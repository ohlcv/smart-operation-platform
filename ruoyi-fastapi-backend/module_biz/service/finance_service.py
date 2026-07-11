"""财务 Service 层（遵循 ADR D24）。

业务规则（ADR D10）：
- 手工 CSV 导入，不直连银行 API
- 流水 1:1 关联发票（可空）
- 状态：cleared 0=未对账 1=已对账
- 银行对账单导入后可手动 match 到财务流水
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.finance_dao import FinanceDAO
from module_biz.dao.invoice_dao import InvoiceDAO
from module_biz.entity.do.finance_do import BizBankStatement, BizFinanceEntry
from module_biz.entity.vo.finance_vo import (
    BankStatementImportModel,
    FinanceCreateModel,
    FinanceQueryModel,
    FinanceResponseModel,
    FinanceSummaryResponseModel,
    FinanceTypeOptionModel,
    FinanceUpdateModel,
)
from module_biz.enums import FinanceEntryTypeEnum


VALID_TYPES = {e.value for e in FinanceEntryTypeEnum}
TYPE_LABELS = {e.value: e.label(e.value) for e in FinanceEntryTypeEnum}

DIRECTION_LABELS = {'in': '收入', 'out': '支出'}
VALID_DIRECTIONS = set(DIRECTION_LABELS.keys())


def _user_id(current_user: CurrentUserModel) -> int:
    if not current_user or not current_user.user:
        raise ServiceException(message='未识别当前用户')
    return current_user.user.user_id


def _user_name(current_user: CurrentUserModel) -> str | None:
    if current_user and current_user.user:
        return current_user.user.user_name or current_user.user.nick_name
    return None


async def _next_entry_no(db: AsyncSession) -> str:
    seq = await FinanceDAO.get_max_entry_seq(db)
    return f'FN-{seq + 1:04d}'


def _validate_entry_type(t: str) -> str:
    if t not in VALID_TYPES:
        raise ServiceException(message=f'流水类型 "{t}" 非法', data='400')
    return t


def _validate_direction(d: str) -> str:
    if d not in VALID_DIRECTIONS:
        raise ServiceException(message=f'收支方向 "{d}" 非法', data='400')
    return d


def _to_response(e: BizFinanceEntry) -> FinanceResponseModel:
    return FinanceResponseModel(
        id=e.id,
        entry_no=e.entry_no,
        entry_type=e.entry_type,
        entry_type_label=TYPE_LABELS.get(e.entry_type, e.entry_type),
        direction=e.direction,
        direction_label=DIRECTION_LABELS.get(e.direction, e.direction),
        invoice_id=e.invoice_id,
        invoice_no=e.invoice_no,
        contract_id=e.contract_id,
        contract_no=e.contract_no,
        party_name=e.party_name,
        amount=e.amount,
        account=e.account,
        account_name=e.account_name,
        bank_name=e.bank_name,
        transaction_date=e.transaction_date,
        cleared=e.cleared,
        cleared_time=e.cleared_time,
        remark=e.remark,
        created_by=e.created_by,
        created_by_name=e.created_by_name,
        create_time=e.create_time,
        update_time=e.update_time,
    )


class FinanceService:
    @staticmethod
    async def list_services(
        db: AsyncSession,
        query: FinanceQueryModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        rows, total = await FinanceDAO.list_entry_page(
            db,
            keyword=query.keyword,
            entry_type=query.entry_type,
            cleared=query.cleared,
            invoice_id=query.invoice_id,
            begin_date=None,
            end_date=None,
            page_num=query.page_num,
            page_size=query.page_size,
        )
        return {
            'rows': [_to_response(e).model_dump(by_alias=True) for e in rows],
            'total': total,
            'page_num': query.page_num,
            'page_size': query.page_size,
        }

    @staticmethod
    async def detail_services(db: AsyncSession, entry_id: int, current_user: CurrentUserModel) -> dict[str, Any]:
        e = await FinanceDAO.get_entry_by_id(db, entry_id)
        if not e:
            raise ServiceException(message=f'财务流水ID {entry_id} 不存在', data='404')
        return _to_response(e).model_dump(by_alias=True)

    @staticmethod
    async def create_services(
        db: AsyncSession,
        payload: FinanceCreateModel,
        current_user: CurrentUserModel,
    ) -> int:
        _validate_entry_type(payload.entry_type)
        _validate_direction(payload.direction)

        # 若关联发票，校验发票存在
        if payload.invoice_id is not None:
            inv = await InvoiceDAO.get_by_id(db, payload.invoice_id)
            if not inv:
                raise ServiceException(message=f'关联的发票ID {payload.invoice_id} 不存在', data='404')

        entry_no = (payload.entry_no or '').strip() or await _next_entry_no(db)
        existed = await FinanceDAO.get_entry_by_no(db, entry_no)
        if existed:
            raise ServiceException(message=f'流水号 {entry_no} 已存在', data='409')

        e = BizFinanceEntry(
            entry_no=entry_no,
            entry_type=payload.entry_type,
            direction=payload.direction,
            invoice_id=payload.invoice_id,
            invoice_no=payload.invoice_no,
            contract_id=payload.contract_id,
            contract_no=payload.contract_no,
            party_name=payload.party_name,
            amount=payload.amount,
            account=payload.account,
            account_name=payload.account_name,
            bank_name=payload.bank_name,
            transaction_date=payload.transaction_date,
            cleared=0,
            remark=payload.remark,
            created_by=_user_id(current_user),
            created_by_name=_user_name(current_user),
            create_time=datetime.now(),
        )
        new_id = await FinanceDAO.insert_entry(db, e)
        await db.commit()
        return new_id

    @staticmethod
    async def update_services(
        db: AsyncSession,
        entry_id: int,
        payload: FinanceUpdateModel,
        current_user: CurrentUserModel,
    ) -> None:
        e = await FinanceDAO.get_entry_by_id(db, entry_id)
        if not e:
            raise ServiceException(message=f'财务流水ID {entry_id} 不存在', data='404')
        if e.cleared == 1:
            raise ServiceException(message='已对账的流水不可编辑，请先撤销对账', data='409')

        fields = payload.model_dump(exclude_unset=True, exclude_none=False)
        fields.pop('id', None)
        if not fields:
            return
        fields['update_by'] = _user_name(current_user) or ''
        await FinanceDAO.update_entry_by_id(db, entry_id, fields)
        await db.commit()

    @staticmethod
    async def delete_services(
        db: AsyncSession,
        entry_id: int,
        current_user: CurrentUserModel,
    ) -> int:
        e = await FinanceDAO.get_entry_by_id(db, entry_id)
        if not e:
            raise ServiceException(message=f'财务流水ID {entry_id} 不存在', data='404')
        if e.cleared == 1:
            raise ServiceException(message='已对账的流水不可删除', data='409')
        deleted = await FinanceDAO.delete_entry_by_id(db, entry_id)
        await db.commit()
        return deleted

    @staticmethod
    async def clear_services(
        db: AsyncSession,
        entry_id: int,
        current_user: CurrentUserModel,
    ) -> None:
        """标记对账（仅校验存在性，不强制关联对账单）。"""
        e = await FinanceDAO.get_entry_by_id(db, entry_id)
        if not e:
            raise ServiceException(message=f'财务流水ID {entry_id} 不存在', data='404')
        if e.cleared == 1:
            raise ServiceException(message='该流水已对账，无需重复操作', data='409')
        await FinanceDAO.update_entry_by_id(
            db,
            entry_id,
            {
                'cleared': 1,
                'cleared_time': datetime.now(),
                'update_by': _user_name(current_user) or '',
            },
        )
        await db.commit()

    @staticmethod
    async def summary_services(
        db: AsyncSession,
        period: str,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        data = await FinanceDAO.summary_by_period(db, period)
        return FinanceSummaryResponseModel(
            period=period,
            **data,
        ).model_dump(by_alias=True)

    @staticmethod
    async def import_bank_statement_services(
        db: AsyncSession,
        payload: BankStatementImportModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """CSV 导入银行对账单（ADR D10：手工导入）。"""
        from datetime import datetime as dt
        batch_no = f'BS-{dt.now().strftime("%Y%m%d%H%M%S")}'
        uid = _user_id(current_user)
        success = 0
        errors: list[dict[str, Any]] = []

        for idx, item in enumerate(payload.items, start=1):
            try:
                _validate_direction(item.direction)
                s = BizBankStatement(
                    batch_no=batch_no,
                    transaction_date=item.transaction_date,
                    account=item.account,
                    amount=item.amount,
                    direction=item.direction,
                    counterparty=item.counterparty,
                    counterparty_account=item.counterparty_account,
                    summary=item.summary,
                    matched=0,
                    import_time=dt.now(),
                    imported_by=uid,
                )
                await FinanceDAO.insert_statement(db, s)
                success += 1
            except Exception as e:  # noqa: BLE001
                errors.append({'row': idx, 'error': str(e)})

        await db.commit()
        return {
            'batch_no': batch_no,
            'success': success,
            'errors': errors,
            'total': len(payload.items),
        }

    @staticmethod
    async def options_services(current_user: CurrentUserModel) -> dict[str, list[dict[str, str]]]:
        types = [
            FinanceTypeOptionModel(value=k, label=v).model_dump(by_alias=True)
            for k, v in TYPE_LABELS.items()
        ]
        dirs = [
            FinanceTypeOptionModel(value=k, label=v).model_dump(by_alias=True)
            for k, v in DIRECTION_LABELS.items()
        ]
        return {'types': types, 'directions': dirs}