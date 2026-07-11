"""审批 Service 层。
文档依据：
- API 设计文档 §六（待我审批 / 审批通过 / 驳回 / 审批历史）
- 权限模型设计.md §三 §3.5（7 级审批链判定流程）
- ADR D02（role_sort 规范：1-7 = 审批链，0=超管，>7=非审批）
- ADR D03（rejected=已驳回待修改，可重新提交）

审批权限判定（参考权限模型设计 §3.5）：
1. 超管（user.admin=True）→ 可审批任意 step
2. 拥有 current_step 对应 role_key 的角色（role_sort = current_step）→ 可审批
3. 同一用户不能在自己提交的合同中担任审批人（边界条件 §9.2）
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, asc, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.approval_dao import ApprovalDAO
from module_biz.dao.contract_dao import ContractDAO
from module_biz.entity.do.approval_do import BizApproval
from module_biz.entity.do.contract_do import BizContract
from module_biz.entity.vo.approval_vo import ApprovalHistoryItemModel
from module_biz.entity.vo.contract_vo import ContractResponseModel
from module_biz.enums import (
    ApprovalActionEnum,
    ApprovalStepEnum,
    ContractStatusEnum,
    ContractTypeEnum,
)


def _user_id(current_user: CurrentUserModel) -> int:
    if not current_user or not current_user.user:
        raise ServiceException(message='未识别当前用户')
    return current_user.user.user_id


def _user_name(current_user: CurrentUserModel) -> str:
    if current_user and current_user.user:
        return current_user.user.user_name or current_user.user.nick_name or ''
    return ''


def _is_admin(current_user: CurrentUserModel) -> bool:
    """判断当前用户是否为超管（user_id==1 或 admin 角色 sort=0）。"""
    if not current_user or not current_user.user:
        return False
    return bool(current_user.user.admin)


async def _user_role_sorts(db: AsyncSession, user_id: int) -> list[int]:
    """返回当前用户所有角色的 role_sort 列表（含 0=admin）。"""
    stmt = text(
        """
        SELECT r.role_sort FROM sys_role r
        JOIN sys_user_role ur ON ur.role_id = r.role_id
        WHERE ur.user_id = :uid
        """
    )
    result = await db.execute(stmt, {'uid': user_id})
    return [int(row[0]) for row in result.fetchall() if row[0] is not None]


async def _user_signature(db: AsyncSession, user_id: int) -> str | None:
    """读取当前用户的电子签名（base64 data URI），用于审批自动签章快照。

    读取时直接从 sys_user.signature 取，避免依赖 Pydantic CurrentUserModel 是否加载此字段。
    """
    stmt = text("SELECT signature FROM sys_user WHERE user_id = :uid")
    result = await db.execute(stmt, {'uid': user_id})
    row = result.fetchone()
    if row and row[0]:
        return row[0]
    return None


async def can_approve(
    db: AsyncSession,
    contract: BizContract,
    current_user: CurrentUserModel,
) -> bool:
    """判断当前用户能否审批给定合同。

    判定规则（权限模型设计 §3.5 + ADR D02）：
    1. 合同必须 status=pending
    2. 超管：直接通过
    3. 普通用户：拥有「当前 step+1 对应」的审批角色（role_sort 1-7 是审批链 1-7）
       这里 role_sort 与 step 是 1:1 + 1 偏置：role_sort=N → step=N-1。
       所以匹配条件是 `role_sort == current_step + 1`。
       业务经办（step=0）创建即视为完成 Step 0 自动审批，不需要找审批人。
    4. 边界条件：同一用户不能在自己提交的合同中担任审批人（权限模型 §9.2）
    """
    if contract.status != ContractStatusEnum.PENDING.value:
        return False
    if _is_admin(current_user):
        return True
    uid = _user_id(current_user)
    if contract.created_by == uid:
        return False
    sorts = await _user_role_sorts(db, uid)
    approval_sorts = {s for s in sorts if 1 <= s <= 7}
    if not approval_sorts:
        return False
    # 匹配条件：role_sort == current_step + 1（D02 role_sort 规范）
    return (contract.current_step + 1) in approval_sorts


def _contract_to_response(c: BizContract) -> ContractResponseModel:
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


async def _my_approval_for(
    db: AsyncSession,
    contract_id: int,
    user_id: int,
) -> BizApproval | None:
    """返回当前用户在该合同上的最后一条审批记录（如有）。"""
    stmt = (
        select(BizApproval)
        .where(
            and_(
                BizApproval.contract_id == contract_id,
                BizApproval.approver_id == user_id,
                BizApproval.step > 0,  # 排除 Step 0 自动审批
            )
        )
        .order_by(desc(BizApproval.approval_time))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _list_pending_for_user(
    db: AsyncSession,
    query,
    current_user: CurrentUserModel,
) -> tuple[list[BizContract], int]:
    """待我审批列表：status=pending 且 role_sort = current_step+1 命中的合同。

    实现：通过 ContractDAO 拉所有 pending 合同，再在 Python 层按 can_approve 过滤。
    命中规则：role_sort = current_step + 1（详见 can_approve）。
    这里故意不在 SQL 层做 role_sort JOIN 过滤，因为审批角色与用户是多对多关系，
    Python 层过滤更直观且开销可接受（pending 合同数据量有限）。
    """
    rows, total = await ContractDAO.list_page(
        db,
        contract_no=query.contract_no,
        title=query.title,
        contract_type=query.contract_type,
        status=ContractStatusEnum.PENDING.value,
        current_step=query.current_step,
        customer_id=None,
        keyword=query.keyword,
        page_num=query.page_num,
        page_size=query.page_size,
    )
    # 过滤出当前用户能审批的合同（role_sort == current_step+1 或 superuser）
    if _is_admin(current_user):
        return rows, total
    uid = _user_id(current_user)
    sorts = await _user_role_sorts(db, uid)
    approval_sorts = {s for s in sorts if 1 <= s <= 7}
    if not approval_sorts:
        return [], 0
    # 过滤：合同在「我」能审批的 step 集合里
    my_steps = {s - 1 for s in approval_sorts}
    filtered = [c for c in rows if c.current_step in my_steps]
    return filtered, len(filtered)


class ApprovalService:
    @staticmethod
    async def pending_list_services(
        db: AsyncSession,
        query,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """待我审批 / 我已审批 / 我提交的（统一一个 list 接口，scope 区分）。"""
        uid = _user_id(current_user)
        scope = query.scope or 'pending'

        if scope == 'submitted':
            # 我创建的合同（含全部状态）
            status_filter = getattr(query, 'status', None)
            rows, total = await ContractDAO.list_page(
                db,
                contract_no=query.contract_no,
                title=query.title,
                contract_type=query.contract_type,
                status=status_filter,
                current_step=query.current_step,
                customer_id=None,
                keyword=query.keyword,
                created_by=uid,
                page_num=query.page_num,
                page_size=query.page_size,
            )
        elif scope == 'processed':
            # 我已审批过：JOIN biz_approvals WHERE approver_id=uid AND step>0
            return await ApprovalService._list_processed_services(db, query, current_user)
        else:
            # pending：当前 step 命中审批角色
            rows, total = await _list_pending_for_user(db, query, current_user)

        out_rows = []
        for c in rows:
            resp = _contract_to_response(c).model_dump(by_alias=True)
            # 待我审批场景补充 can_approve
            if scope == 'pending':
                resp['canApprove'] = await can_approve(db, c, current_user)
                # 当前用户已审批过（驳回后重提场景）
                my = await _my_approval_for(db, c.id, uid)
                if my:
                    resp['myAction'] = my.action
                    resp['myActionLabel'] = '通过' if my.action == ApprovalActionEnum.APPROVE.value else '驳回'
                    resp['myComment'] = my.comment
                    resp['myApprovalTime'] = my.approval_time.isoformat() if my.approval_time else None
            out_rows.append(resp)
        return {
            'rows': out_rows,
            'total': total,
            'page_num': query.page_num,
            'page_size': query.page_size,
            'scope': scope,
        }

    @staticmethod
    async def _list_processed_services(
        db: AsyncSession,
        query,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """我已审批过的合同列表（按 approval 记录 join contract）。"""
        uid = _user_id(current_user)
        # 子查询：取每个合同中当前用户最后一条 step>0 的审批记录的 contract_id
        latest_subq = (
            select(
                BizApproval.contract_id.label('contract_id'),
                func.max(BizApproval.approval_time).label('last_time'),
            )
            .where(and_(BizApproval.approver_id == uid, BizApproval.step > 0))
            .group_by(BizApproval.contract_id)
            .subquery()
        )
        join_stmt = (
            select(BizApproval, BizContract)
            .join(BizContract, BizContract.id == BizApproval.contract_id)
            .join(
                latest_subq,
                and_(
                    latest_subq.c.contract_id == BizApproval.contract_id,
                    latest_subq.c.last_time == BizApproval.approval_time,
                ),
            )
            .where(BizApproval.approver_id == uid)
        )
        # 关键字过滤
        if query.keyword:
            kw = f'%{query.keyword}%'
            join_stmt = join_stmt.where(
                or_(
                    BizContract.contract_no.like(kw),
                    BizContract.title.like(kw),
                    BizContract.customer_name.like(kw),
                    BizContract.party_b.like(kw),
                )
            )
        if query.contract_no:
            join_stmt = join_stmt.where(BizContract.contract_no.like(f'%{query.contract_no}%'))
        if query.title:
            join_stmt = join_stmt.where(BizContract.title.like(f'%{query.title}%'))
        if query.contract_type:
            join_stmt = join_stmt.where(BizContract.contract_type == query.contract_type)
        # query.status 不在 PendingQueryModel 上，用 getattr 兜底（接口允许客户端按 status 过滤）
        status_filter = getattr(query, 'status', None)
        if status_filter:
            join_stmt = join_stmt.where(BizContract.status == status_filter)

        # 总数
        count_stmt = select(func.count()).select_from(join_stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # 分页
        page_num = query.page_num or 1
        page_size = query.page_size or 10
        join_stmt = (
            join_stmt.order_by(desc(BizApproval.approval_time))
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(join_stmt)
        out_rows = []
        for approval, contract in result.all():
            resp = _contract_to_response(contract).model_dump(by_alias=True)
            resp['canApprove'] = False  # 我已审批过不可再审批
            resp['myAction'] = approval.action
            resp['myActionLabel'] = '通过' if approval.action == ApprovalActionEnum.APPROVE.value else '驳回'
            resp['myComment'] = approval.comment
            resp['myApprovalTime'] = approval.approval_time.isoformat() if approval.approval_time else None
            out_rows.append(resp)
        return {
            'rows': out_rows,
            'total': total,
            'page_num': page_num,
            'page_size': page_size,
            'scope': 'processed',
        }

    @staticmethod
    async def history_services(
        db: AsyncSession,
        contract_id: int,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """审批历史（合同详情抽屉用）。"""
        c = await ContractDAO.get_by_id(db, contract_id)
        if not c:
            raise ServiceException(message=f'合同ID {contract_id} 不存在', data='404')
        approvals = await ApprovalDAO.list_by_contract(db, contract_id)
        items: list[ApprovalHistoryItemModel] = []
        for a in approvals:
            items.append(
                ApprovalHistoryItemModel(
                    id=a.id,
                    contract_id=a.contract_id,
                    approver_id=a.approver_id,
                    approver_name=a.approver_name,
                    step=a.step,
                    step_label=ApprovalStepEnum.label(a.step),
                    approver_role=a.approver_role,
                    action=a.action,
                    action_label='通过' if a.action == ApprovalActionEnum.APPROVE.value else '驳回',
                    comment=a.comment,
                    reject_reason=a.reject_reason,
                    signature_snapshot=a.signature_snapshot,
                    approval_time=a.approval_time,
                )
            )
        return {
            'contract': _contract_to_response(c).model_dump(by_alias=True),
            'items': [it.model_dump(by_alias=True) for it in items],
        }

    @staticmethod
    async def approve_services(
        db: AsyncSession,
        contract_id: int,
        payload,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """审批通过。

        流程：
        1. 取合同，校验 status=pending
        2. can_approve 校验
        3. 写入 biz_approval（action=approve, step=current_step）
        4. 推进 current_step：
           - current_step < 6：current_step++, current_role=next role_key
           - current_step = 6：status=approved（终态）
        5. 拒绝自身审批：拒绝（驳回由 reject_services 处理）
        """
        c = await ContractDAO.get_by_id(db, contract_id)
        if not c:
            raise ServiceException(message=f'合同ID {contract_id} 不存在', data='404')
        if not await can_approve(db, c, current_user):
            raise ServiceException(message='您不是当前步骤的审批人，无权审批', data='403')
        if payload.action != ApprovalActionEnum.APPROVE.value:
            raise ServiceException(message='此接口仅处理通过操作', data='400')

        uid = _user_id(current_user)
        u_name = _user_name(current_user)
        # 自动电子签章：从 sys_user.signature 取 base64 data URI 快照（v1 demo 行为）
        sig_snapshot = await _user_signature(db, uid)

        # 写审批记录
        approval = BizApproval(
            contract_id=contract_id,
            approver_id=uid,
            approver_name=u_name,
            step=c.current_step,
            approver_role=c.current_role or ApprovalStepEnum.role_key(c.current_step) or '',
            action=ApprovalActionEnum.APPROVE.value,
            comment=payload.comment,
            signature_snapshot=sig_snapshot,
            approval_time=datetime.now(),
            create_time=datetime.now(),
        )
        await ApprovalDAO.insert(db, approval)

        # 推进 step 或终态
        next_step = c.current_step + 1
        if next_step > ApprovalStepEnum.STEP_6_INVEST_DIRECTOR.value:
            # 终态
            await ContractDAO.update_by_id(
                db,
                contract_id,
                {
                    'status': ContractStatusEnum.APPROVED.value,
                    'current_role': None,
                    'update_by': u_name,
                },
            )
            result_msg = '终审通过，流程结束'
        else:
            next_role = ApprovalStepEnum.role_key(next_step)
            await ContractDAO.update_by_id(
                db,
                contract_id,
                {
                    'current_step': next_step,
                    'current_role': next_role,
                    'update_by': u_name,
                },
            )
            result_msg = f'审批通过，已流转至 {ApprovalStepEnum.label(next_step)}'

        await db.commit()
        return {
            'contractId': contract_id,
            'newStep': next_step if next_step <= 6 else 6,
            'newStatus': ContractStatusEnum.APPROVED.value if next_step > 6 else ContractStatusEnum.PENDING.value,
            'msg': result_msg,
        }

    @staticmethod
    async def reject_services(
        db: AsyncSession,
        contract_id: int,
        payload,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """审批驳回。

        流程：
        1. 取合同，校验 status=pending
        2. can_approve 校验
        3. 校验 reject_reason 必填
        4. 写入 biz_approval（action=reject）
        5. status=rejected（ADR D03：可重新提交，保留历史）
        6. reject_count++
        """
        c = await ContractDAO.get_by_id(db, contract_id)
        if not c:
            raise ServiceException(message=f'合同ID {contract_id} 不存在', data='404')
        if not await can_approve(db, c, current_user):
            raise ServiceException(message='您不是当前步骤的审批人，无权驳回', data='403')
        if payload.action != ApprovalActionEnum.REJECT.value:
            raise ServiceException(message='此接口仅处理驳回操作', data='400')
        reject_reason = payload.reject_reason or payload.comment
        if not reject_reason:
            raise ServiceException(message='驳回必须填写驳回原因', data='400')

        uid = _user_id(current_user)
        u_name = _user_name(current_user)
        approval = BizApproval(
            contract_id=contract_id,
            approver_id=uid,
            approver_name=u_name,
            step=c.current_step,
            approver_role=c.current_role or ApprovalStepEnum.role_key(c.current_step) or '',
            action=ApprovalActionEnum.REJECT.value,
            comment=payload.comment,
            reject_reason=reject_reason,
            approval_time=datetime.now(),
            create_time=datetime.now(),
        )
        await ApprovalDAO.insert(db, approval)
        await ContractDAO.update_by_id(
            db,
            contract_id,
            {
                'status': ContractStatusEnum.REJECTED.value,
                'current_role': None,
                'reject_count': (c.reject_count or 0) + 1,
                'update_by': u_name,
            },
        )
        await db.commit()
        return {
            'contractId': contract_id,
            'newStatus': ContractStatusEnum.REJECTED.value,
            'msg': '已驳回，创建人可修改后重新提交',
        }