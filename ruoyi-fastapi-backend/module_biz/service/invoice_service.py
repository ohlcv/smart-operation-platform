"""发票 Service 层（遵循 ADR D24）。

业务规则（ADR D11）：
- 1:1 关联合同（合同 ID 唯一）
- 状态机：pending → issued → void
- 仅 pending 可编辑/删除
- 开票金额 ≤ 合同金额
- issue_date ≥ apply_date
- 不做真实开票对接，仅台账管理
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.contract_dao import ContractDAO
from module_biz.dao.invoice_dao import InvoiceDAO
from module_biz.entity.do.contract_do import BizContract
from module_biz.entity.do.invoice_do import BizInvoice
from module_biz.entity.vo.invoice_vo import (
    InvoiceCreateModel,
    InvoiceQueryModel,
    InvoiceResponseModel,
    InvoiceStatusOptionModel,
    InvoiceUpdateModel,
    InvoiceVoidModel,
)
from module_biz.enums import InvoiceStatusEnum


VALID_INVOICE_TYPES = {'specialized', 'general', 'electronic'}

INVOICE_TYPE_LABELS = {
    'specialized': '增值税专用发票',
    'general': '普通发票',
    'electronic': '电子发票',
}


def _user_id(current_user: CurrentUserModel) -> int:
    if not current_user or not current_user.user:
        raise ServiceException(message='未识别当前用户')
    return current_user.user.user_id


def _user_name(current_user: CurrentUserModel) -> str | None:
    if current_user and current_user.user:
        return current_user.user.user_name or current_user.user.nick_name
    return None


def _validate_invoice_type(t: str) -> str:
    if t not in VALID_INVOICE_TYPES:
        raise ServiceException(message=f'发票类型 "{t}" 非法', data='400')
    return t


async def _next_invoice_no(db: AsyncSession) -> str:
    """生成下一个发票号 FP-NNN。"""
    seq = await InvoiceDAO.get_max_invoice_seq(db)
    return f'FP-{seq + 1:04d}'


def _calc_tax(amount: Decimal, tax_rate: Decimal) -> tuple[Decimal, Decimal]:
    """根据含税金额和税率计算税额与不含税金额。

    返回 (tax_amount, untaxed_amount)。
    默认按价外税计算（不含税 = 金额 / (1 + 税率)）。
    """
    if not tax_rate or tax_rate == 0:
        return Decimal('0.00'), amount
    untaxed = (amount / (Decimal('1') + tax_rate)).quantize(Decimal('0.01'))
    tax = (amount - untaxed).quantize(Decimal('0.01'))
    return tax, untaxed


def _to_response(inv: BizInvoice) -> InvoiceResponseModel:
    return InvoiceResponseModel(
        id=inv.id,
        invoice_no=inv.invoice_no,
        contract_id=inv.contract_id,
        contract_no=inv.contract_no,
        invoice_type=inv.invoice_type,
        invoice_type_label=INVOICE_TYPE_LABELS.get(inv.invoice_type, inv.invoice_type),
        amount=inv.amount,
        tax_rate=inv.tax_rate,
        tax_amount=inv.tax_amount,
        party_name=inv.party_name,
        party_tax_no=inv.party_tax_no,
        status=inv.status,
        status_label=InvoiceStatusEnum.label(inv.status),
        apply_date=inv.apply_date,
        issue_date=inv.issue_date,
        void_reason=inv.void_reason,
        remark=inv.remark,
        created_by=inv.created_by,
        created_by_name=inv.created_by_name,
        create_time=inv.create_time,
        update_time=inv.update_time,
    )


class InvoiceService:
    @staticmethod
    async def list_services(
        db: AsyncSession,
        query: InvoiceQueryModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        rows, total = await InvoiceDAO.list_page(
            db,
            keyword=query.keyword,
            status=query.status,
            invoice_type=query.invoice_type,
            contract_id=query.contract_id,
            begin_date=None,
            end_date=None,
            page_num=query.page_num,
            page_size=query.page_size,
        )
        return {
            'rows': [_to_response(inv).model_dump(by_alias=True) for inv in rows],
            'total': total,
            'page_num': query.page_num,
            'page_size': query.page_size,
        }

    @staticmethod
    async def detail_services(db: AsyncSession, invoice_id: int, current_user: CurrentUserModel) -> dict[str, Any]:
        inv = await InvoiceDAO.get_by_id(db, invoice_id)
        if not inv:
            raise ServiceException(message=f'发票ID {invoice_id} 不存在', data='404')
        return _to_response(inv).model_dump(by_alias=True)

    @staticmethod
    async def create_services(
        db: AsyncSession,
        payload: InvoiceCreateModel,
        current_user: CurrentUserModel,
    ) -> int:
        _validate_invoice_type(payload.invoice_type)

        # 校验合同存在 + 已审批通过（不可给草稿/驳回合同开发票）
        contract = await ContractDAO.get_by_id(db, payload.contract_id)
        if not contract:
            raise ServiceException(message=f'合同ID {payload.contract_id} 不存在', data='404')
        if contract.status != 'approved':
            raise ServiceException(
                message=f'合同 "{contract.contract_no}" 当前状态为「{contract.status}」，仅审批通过的合同可开发票',
                data='409',
            )

        # 1:1 校验：同一合同不能重复开票
        existed_by_contract = await InvoiceDAO.get_by_contract_id(db, payload.contract_id)
        if existed_by_contract:
            raise ServiceException(
                message=f'合同 "{contract.contract_no}" 已存在发票 {existed_by_contract.invoice_no}，1:1 不可重复',
                data='409',
            )

        # 金额校验：开票金额 ≤ 合同金额
        if payload.amount is not None and contract.amount is not None:
            if payload.amount > contract.amount:
                raise ServiceException(
                    message=f'开票金额 {payload.amount} 不能超过合同金额 {contract.amount}',
                    data='400',
                )

        # 发票号（自动生成或校验）
        inv_no = (payload.invoice_no or '').strip() or await _next_invoice_no(db)
        existed_by_no = await InvoiceDAO.get_by_invoice_no(db, inv_no)
        if existed_by_no:
            raise ServiceException(message=f'发票号 {inv_no} 已存在', data='409')

        tax_amount, _ = _calc_tax(payload.amount, payload.tax_rate)

        uid = _user_id(current_user)
        u_name = _user_name(current_user)
        inv = BizInvoice(
            invoice_no=inv_no,
            contract_id=payload.contract_id,
            contract_no=contract.contract_no,
            invoice_type=payload.invoice_type,
            amount=payload.amount,
            tax_rate=payload.tax_rate,
            tax_amount=tax_amount,
            party_name=payload.party_name,
            party_tax_no=payload.party_tax_no,
            status=InvoiceStatusEnum.PENDING.value,
            apply_date=payload.apply_date,
            issue_date=None,
            remark=payload.remark,
            created_by=uid,
            created_by_name=u_name,
            create_time=datetime.now(),
        )
        new_id = await InvoiceDAO.insert(db, inv)
        await db.commit()
        return new_id

    @staticmethod
    async def update_services(
        db: AsyncSession,
        invoice_id: int,
        payload: InvoiceUpdateModel,
        current_user: CurrentUserModel,
    ) -> None:
        inv = await InvoiceDAO.get_by_id(db, invoice_id)
        if not inv:
            raise ServiceException(message=f'发票ID {invoice_id} 不存在', data='404')
        if inv.status != InvoiceStatusEnum.PENDING.value:
            raise ServiceException(
                message=f'发票当前状态为「{InvoiceStatusEnum.label(inv.status)}」，不可编辑（仅待开发票可编辑）',
                data='409',
            )

        fields = payload.model_dump(exclude_unset=True, exclude_none=False)
        fields.pop('id', None)
        if 'invoice_type' in fields:
            _validate_invoice_type(fields['invoice_type'])

        if 'amount' in fields or 'tax_rate' in fields:
            new_amount = fields.get('amount', inv.amount)
            new_rate = fields.get('tax_rate', inv.tax_rate)
            new_tax, _ = _calc_tax(new_amount, new_rate)
            fields['tax_amount'] = new_tax

        if not fields:
            return

        fields['update_by'] = _user_name(current_user) or ''
        await InvoiceDAO.update_by_id(db, invoice_id, fields)
        await db.commit()

    @staticmethod
    async def delete_services(
        db: AsyncSession,
        invoice_id: int,
        current_user: CurrentUserModel,
    ) -> int:
        inv = await InvoiceDAO.get_by_id(db, invoice_id)
        if not inv:
            raise ServiceException(message=f'发票ID {invoice_id} 不存在', data='404')
        if inv.status != InvoiceStatusEnum.PENDING.value:
            raise ServiceException(
                message=f'发票当前状态为「{InvoiceStatusEnum.label(inv.status)}」，不可删除（仅待开发票可删）',
                data='409',
            )
        deleted = await InvoiceDAO.delete_by_id(db, invoice_id)
        await db.commit()
        return deleted

    @staticmethod
    async def issue_services(
        db: AsyncSession,
        invoice_id: int,
        current_user: CurrentUserModel,
        issue_date: Any = None,
    ) -> dict[str, Any]:
        """标记为已开票（pending → issued）。"""
        inv = await InvoiceDAO.get_by_id(db, invoice_id)
        if not inv:
            raise ServiceException(message=f'发票ID {invoice_id} 不存在', data='404')
        if inv.status != InvoiceStatusEnum.PENDING.value:
            raise ServiceException(
                message=f'仅待开发票可标记为已开，当前状态「{InvoiceStatusEnum.label(inv.status)}」',
                data='409',
            )
        # 开票日期校验
        effective_issue_date = issue_date or datetime.now().date()
        if inv.apply_date and effective_issue_date < inv.apply_date:
            raise ServiceException(message='开票日期不能早于申请日期', data='400')

        await InvoiceDAO.update_by_id(
            db,
            invoice_id,
            {
                'status': InvoiceStatusEnum.ISSUED.value,
                'issue_date': effective_issue_date,
                'update_by': _user_name(current_user) or '',
            },
        )
        await db.commit()
        new = await InvoiceDAO.get_by_id(db, invoice_id)
        return _to_response(new).model_dump(by_alias=True)

    @staticmethod
    async def void_services(
        db: AsyncSession,
        invoice_id: int,
        payload: InvoiceVoidModel,
        current_user: CurrentUserModel,
    ) -> None:
        """作废发票（仅 issued 可作废）。"""
        inv = await InvoiceDAO.get_by_id(db, invoice_id)
        if not inv:
            raise ServiceException(message=f'发票ID {invoice_id} 不存在', data='404')
        if inv.status == InvoiceStatusEnum.VOID.value:
            raise ServiceException(message='发票已作废', data='409')
        if inv.status == InvoiceStatusEnum.PENDING.value:
            raise ServiceException(
                message='待开发票请直接删除，无需作废',
                data='409',
            )

        await InvoiceDAO.update_by_id(
            db,
            invoice_id,
            {
                'status': InvoiceStatusEnum.VOID.value,
                'void_reason': payload.reason,
                'update_by': _user_name(current_user) or '',
            },
        )
        await db.commit()

    @staticmethod
    async def options_services(current_user: CurrentUserModel) -> dict[str, list[dict[str, str]]]:
        """下拉选项（状态/类型）。"""
        statuses = [
            InvoiceStatusOptionModel(value=e.value, label=e.label(e.value)).model_dump(by_alias=True)
            for e in InvoiceStatusEnum
        ]
        types = [
            InvoiceStatusOptionModel(value=k, label=v).model_dump(by_alias=True)
            for k, v in INVOICE_TYPE_LABELS.items()
        ]
        return {'statuses': statuses, 'types': types}
