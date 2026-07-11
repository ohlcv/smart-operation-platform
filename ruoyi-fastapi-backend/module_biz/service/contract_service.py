"""合同 Service 层。

按 docs/04-开发/开发进度台账.md §2.5 contract_service.py 实现。
业务规则严格遵循 docs/04-开发/ARD/ADR-架构决策记录.md v1.1：
- D03：rejected=已驳回待修改，可重新提交
- D04：合同编号手动输入
- D06：party_a=甲方(客户) party_b=乙方(本司)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.approval_dao import ApprovalDAO
from module_biz.dao.contract_dao import ContractDAO
from module_biz.entity.do.approval_do import BizApproval
from module_biz.entity.do.contract_do import BizContract
from module_biz.entity.vo.contract_vo import (
    ContractCreateModel,
    ContractQueryModel,
    ContractResponseModel,
    ContractUpdateModel,
)
from module_biz.enums import (
    ApprovalActionEnum,
    ApprovalStepEnum,
    ContractStatusEnum,
    ContractTypeEnum,
)


def _user_id(current_user: CurrentUserModel) -> int:
    """从 CurrentUserModel 中提取 user_id，统一入口。"""
    if not current_user or not current_user.user:
        raise ServiceException(message='未识别当前用户')
    return current_user.user.user_id


def _user_name(current_user: CurrentUserModel) -> str:
    if current_user and current_user.user:
        return current_user.user.user_name or current_user.user.nick_name or ''
    return ''


def _to_response(c: BizContract) -> ContractResponseModel:
    """DO → 响应 Pydantic 模型，注入 *label 字段。

    严格遵循 ADR D24：返回 Pydantic 模型，由 FastAPI + ResponseUtil 经 model_dump(by_alias=True)
    序列化为 camelCase JSON，禁止返回裸 dict。
    """
    return ContractResponseModel(
        id=c.id,
        contract_no=c.contract_no,
        title=c.title,
        contract_type=c.contract_type,
        contract_type_label=ContractTypeEnum.label(c.contract_type),
        party_a=c.party_a,
        party_b=c.party_b,
        amount=c.amount,
        amount_in_words=c.amount_in_words,
        sign_date=c.sign_date,
        department=c.department,
        business_type=c.business_type,
        customer_id=c.customer_id,
        customer_name=c.customer_name,
        remark=c.remark,
        attachments=c.attachments,
        status=c.status,
        status_label=ContractStatusEnum.label(c.status),
        current_step=c.current_step,
        current_role=c.current_role,
        current_role_label=(
            ApprovalStepEnum.label(c.current_step)
            if c.status == ContractStatusEnum.PENDING.value
            else None
        ),
        reject_count=c.reject_count,
        created_by=c.created_by,
        created_by_name=c.created_by_name,
        create_time=c.create_time,
        update_time=c.update_time,
    )


class ContractService:
    @staticmethod
    async def list_services(
        db: AsyncSession,
        query: ContractQueryModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        rows, total = await ContractDAO.list_page(
            db,
            contract_no=query.contract_no,
            title=query.title,
            contract_type=query.contract_type,
            status=query.status,
            current_step=query.current_step,
            customer_id=query.customer_id,
            keyword=query.keyword,
            page_num=query.page_num,
            page_size=query.page_size,
        )
        return {
            'rows': [_to_response(c).model_dump(by_alias=True) for c in rows],
            'total': total,
            'page_num': query.page_num,
            'page_size': query.page_size,
        }

    @staticmethod
    async def my_list_services(
        db: AsyncSession,
        query: ContractQueryModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        uid = _user_id(current_user)
        rows, total = await ContractDAO.list_page(
            db,
            contract_no=query.contract_no,
            title=query.title,
            contract_type=query.contract_type,
            status=query.status,
            current_step=query.current_step,
            customer_id=query.customer_id,
            keyword=query.keyword,
            created_by=uid,
            page_num=query.page_num,
            page_size=query.page_size,
        )
        return {
            'rows': [_to_response(c).model_dump(by_alias=True) for c in rows],
            'total': total,
            'page_num': query.page_num,
            'page_size': query.page_size,
        }

    @staticmethod
    async def detail_services(db: AsyncSession, contract_id: int, current_user: CurrentUserModel) -> dict[str, Any]:
        c = await ContractDAO.get_by_id(db, contract_id)
        if not c:
            raise ServiceException(message=f'合同ID {contract_id} 不存在', data='404')
        return _to_response(c).model_dump(by_alias=True)

    @staticmethod
    async def create_services(
        db: AsyncSession,
        payload: ContractCreateModel,
        current_user: CurrentUserModel,
    ) -> int:
        existed = await ContractDAO.get_by_contract_no(db, payload.contract_no)
        if existed:
            raise ServiceException(message=f'合同编号 {payload.contract_no} 已存在', data='409')

        uid = _user_id(current_user)
        u_name = _user_name(current_user)
        contract = BizContract(
            contract_no=payload.contract_no,
            title=payload.title,
            contract_type=payload.contract_type,
            party_a=payload.party_a,
            party_b=payload.party_b,
            amount=payload.amount,
            sign_date=payload.sign_date,
            department=payload.department,
            business_type=payload.business_type,
            customer_id=payload.customer_id,
            customer_name=payload.customer_name,
            remark=payload.remark,
            attachments=payload.attachments,
            status=ContractStatusEnum.DRAFT.value,
            current_step=0,
            current_role=None,
            reject_count=0,
            created_by=uid,
            created_by_name=u_name,
            create_time=datetime.now(),
        )
        new_id = await ContractDAO.insert(db, contract)
        await db.commit()
        return new_id

    @staticmethod
    async def update_services(
        db: AsyncSession,
        contract_id: int,
        payload: ContractUpdateModel,
        current_user: CurrentUserModel,
    ) -> None:
        c = await ContractDAO.get_by_id(db, contract_id)
        if not c:
            raise ServiceException(message=f'合同ID {contract_id} 不存在', data='404')
        # 状态机：仅 draft/rejected 可编辑
        if c.status not in (ContractStatusEnum.DRAFT.value, ContractStatusEnum.REJECTED.value):
            raise ServiceException(
                message=f'合同当前状态为 {ContractStatusEnum.label(c.status)}，不可编辑',
                data='409',
            )
        uid = _user_id(current_user)
        if c.created_by != uid:
            raise ServiceException(message='仅创建人可编辑该合同', data='403')

        fields = payload.model_dump(exclude_unset=True, exclude_none=False)
        fields.pop('id', None)
        if not fields:
            return
        fields['update_by'] = _user_name(current_user)
        await ContractDAO.update_by_id(db, contract_id, fields)
        await db.commit()

    @staticmethod
    async def delete_services(
        db: AsyncSession,
        ids: list[int],
        current_user: CurrentUserModel,
    ) -> int:
        if not ids:
            return 0
        uid = _user_id(current_user)
        deleted = 0
        for cid in ids:
            c = await ContractDAO.get_by_id(db, cid)
            if not c:
                continue
            if c.status not in (ContractStatusEnum.DRAFT.value, ContractStatusEnum.REJECTED.value):
                raise ServiceException(
                    message=f'合同 {c.contract_no} 当前状态为 {ContractStatusEnum.label(c.status)}，不可删除',
                    data='409',
                )
            if c.created_by != uid:
                raise ServiceException(message=f'合同 {c.contract_no} 非创建人，无权删除', data='403')
            deleted += await ContractDAO.delete_by_ids(db, [cid])
        await db.commit()
        return deleted

    @staticmethod
    async def submit_services(
        db: AsyncSession,
        contract_id: int,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """提交审批。

        业务规则（docs/03-设计/API设计文档.md §5.7）：
        1. 仅 draft / rejected 状态可提交
        2. 创建人必须为当前用户
        3. 校验必填字段（合同编号、名称、甲乙方、金额）
        4. status → pending, current_step → 1（Step 0 视为业务经办提交即完成）
        5. current_role → business_reviewer（下一步审批角色）
        6. 写一条 approval 记录（step=0, action=approve）
        """
        c = await ContractDAO.get_by_id(db, contract_id)
        if not c:
            raise ServiceException(message=f'合同ID {contract_id} 不存在', data='404')
        if c.status not in (ContractStatusEnum.DRAFT.value, ContractStatusEnum.REJECTED.value):
            raise ServiceException(
                message=f'合同当前状态为 {ContractStatusEnum.label(c.status)}，不可提交',
                data='409',
            )
        uid = _user_id(current_user)
        if c.created_by != uid:
            raise ServiceException(message='仅创建人可提交该合同', data='403')
        # 必填字段校验
        missing = []
        for f in ('contract_no', 'title', 'party_a', 'party_b'):
            if not getattr(c, f):
                missing.append(f)
        if not c.amount or float(c.amount) <= 0:
            missing.append('amount')
        if missing:
            raise ServiceException(message=f'合同信息不完整，缺少字段：{", ".join(missing)}', data='400')

        # 推进状态
        next_step = ApprovalStepEnum.STEP_1_BUSINESS_REVIEWER.value
        next_role = ApprovalStepEnum.role_key(next_step)
        await ContractDAO.update_by_id(
            db,
            contract_id,
            {
                'status': ContractStatusEnum.PENDING.value,
                'current_step': next_step,
                'current_role': next_role,
                'update_by': _user_name(current_user),
            },
        )
        # 写 Step 0 自动审批记录
        u_name = _user_name(current_user)
        approval = BizApproval(
            contract_id=contract_id,
            approver_id=uid,
            approver_name=u_name,
            step=ApprovalStepEnum.STEP_0_BUSINESS_HANDLER.value,
            approver_role=ApprovalStepEnum.role_key(ApprovalStepEnum.STEP_0_BUSINESS_HANDLER.value) or 'business_handler',
            action=ApprovalActionEnum.APPROVE.value,
            comment='业务经办提交',
            approval_time=datetime.now(),
            create_time=datetime.now(),
        )
        await ApprovalDAO.insert(db, approval)
        await db.commit()
        return {'status': ContractStatusEnum.PENDING.value, 'current_step': next_step}

    @staticmethod
    async def check_no_services(
        db: AsyncSession,
        contract_no: str,
        exclude_id: int | None = None,
    ) -> bool:
        """合同编号唯一性校验，存在返回 False（不可用），不存在返回 True（可用）。"""
        existed = await ContractDAO.get_by_contract_no(db, contract_no, exclude_id=exclude_id)
        return existed is None