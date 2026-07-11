"""审批中心 controller。
路径前缀 /biz/approval，遵循 docs/03-设计/API设计文档.md §六。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.entity.vo.approval_vo import (
    ApprovalActionModel,
    PendingQueryModel,
)
from module_biz.service.approval_service import ApprovalService
from utils.log_util import logger
from utils.response_util import ResponseUtil

approval_controller = APIRouterPro(
    prefix='/biz/approval', order_num=22, tags=['业务管理-审批中心'], dependencies=[PreAuthDependency()]
)


@approval_controller.get(
    '/list',
    summary='审批列表（待我审批/我已审批/我提交的）',
    description='scope: pending=待我审批 / processed=我已审批 / submitted=我提交的',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('approval:list')],
)
async def get_approval_list(
    request: Request,
    query: Annotated[PendingQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await ApprovalService.pending_list_services(query_db, query, current_user)
    return ResponseUtil.success(
        msg='查询成功',
        rows=result['rows'],
        dict_content={
            'pageNum': result['page_num'],
            'pageSize': result['page_size'],
            'total': result['total'],
            'scope': result['scope'],
        },
    )


@approval_controller.get(
    '/history/{contract_id}',
    summary='审批历史',
    description='返回合同的全量审批历史记录，按时间正序',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('approval:list')],
)
async def get_approval_history(
    request: Request,
    contract_id: Annotated[int, Path(description='合同ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await ApprovalService.history_services(query_db, contract_id, current_user)
    return ResponseUtil.success(data=result)


@approval_controller.post(
    '/approve/{contract_id}',
    summary='审批通过',
    description='当前步骤审批人调用；推进 current_step，超管可审批任意 step',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('approval:approve')],
)
@Log(title='审批中心', business_type=BusinessType.UPDATE)
async def approve_contract(
    request: Request,
    contract_id: Annotated[int, Path(description='合同ID')],
    payload: ApprovalActionModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await ApprovalService.approve_services(query_db, contract_id, payload, current_user)
    logger.info(f'审批通过 contract_id={contract_id} approver={current_user.user.user_name}')
    return ResponseUtil.success(msg=data['msg'], data=data)


@approval_controller.post(
    '/reject/{contract_id}',
    summary='审批驳回',
    description='当前步骤审批人调用；status→rejected（可重新提交，ADR D03）',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('approval:reject')],
)
@Log(title='审批中心', business_type=BusinessType.UPDATE)
async def reject_contract(
    request: Request,
    contract_id: Annotated[int, Path(description='合同ID')],
    payload: ApprovalActionModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await ApprovalService.reject_services(query_db, contract_id, payload, current_user)
    logger.info(f'审批驳回 contract_id={contract_id} approver={current_user.user.user_name}')
    return ResponseUtil.success(msg=data['msg'], data=data)