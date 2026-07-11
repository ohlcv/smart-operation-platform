"""合同管理 controller

路径前缀 /biz/contract，严格遵循 docs/03-设计/API设计文档.md §五。
注意：与前端 api/biz/contract.js 当前使用的 /biz/contracts（复数）不一致；
实际部署前需统一，详见 docs/04-开发/开发进度台账.md 1.6 节点。
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
from module_biz.entity.vo.contract_vo import (
    ContractCheckNoModel,
    ContractCreateModel,
    ContractQueryModel,
    ContractUpdateModel,
)
from module_biz.service.contract_service import ContractService
from utils.log_util import logger
from utils.response_util import ResponseUtil

contract_controller = APIRouterPro(
    prefix='/biz/contract', order_num=20, tags=['业务管理-合同管理'], dependencies=[PreAuthDependency()]
)


@contract_controller.get(
    '/list',
    summary='获取合同列表',
    description='分页查询合同列表，支持按编号/名称/状态/步骤过滤',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('contract:list')],
)
async def get_contract_list(
    request: Request,
    query: Annotated[ContractQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await ContractService.list_services(query_db, query, current_user)
    return ResponseUtil.success(
        msg='查询成功',
        rows=result['rows'],
        dict_content={
            'pageNum': result['page_num'],
            'pageSize': result['page_size'],
            'total': result['total'],
        },
    )


@contract_controller.get(
    '/my-list',
    summary='我的合同',
    description='当前用户作为创建人的合同列表',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('contract:list')],
)
async def get_my_contracts(
    request: Request,
    query: Annotated[ContractQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await ContractService.my_list_services(query_db, query, current_user)
    return ResponseUtil.success(
        msg='查询成功',
        rows=result['rows'],
        dict_content={
            'pageNum': result['page_num'],
            'pageSize': result['page_size'],
            'total': result['total'],
        },
    )


@contract_controller.get(
    '/{contract_id}',
    summary='获取合同详情',
    description='按 ID 获取合同完整信息',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('contract:list')],
)
async def get_contract_detail(
    request: Request,
    contract_id: Annotated[int, Path(description='合同ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await ContractService.detail_services(query_db, contract_id, current_user)
    return ResponseUtil.success(data=data)


@contract_controller.post(
    '',
    summary='新建合同',
    description='新建合同（草稿状态）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('contract:add')],
)
@ValidateFields(validate_model='create_services')
@Log(title='合同管理', business_type=BusinessType.INSERT)
async def add_contract(
    request: Request,
    payload: ContractCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    new_id = await ContractService.create_services(query_db, payload, current_user)
    logger.info(f'新建合同 id={new_id}')
    return ResponseUtil.success(msg='新增成功', data={'id': new_id})


@contract_controller.put(
    '',
    summary='编辑合同',
    description='仅草稿/已驳回状态的合同可编辑，且仅创建人可编辑',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('contract:edit')],
)
@Log(title='合同管理', business_type=BusinessType.UPDATE)
async def update_contract(
    request: Request,
    payload: ContractUpdateModel,
    contract_id: Annotated[int, Query(description='合同ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await ContractService.update_services(query_db, contract_id, payload, current_user)
    return ResponseUtil.success(msg='修改成功')


@contract_controller.delete(
    '/{contract_ids}',
    summary='删除合同',
    description='仅草稿/已驳回状态的合同可删除，逗号分隔多个 ID',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('contract:delete')],
)
@Log(title='合同管理', business_type=BusinessType.DELETE)
async def delete_contract(
    request: Request,
    contract_ids: Annotated[str, Path(description='合同ID，逗号分隔')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    ids = [int(x) for x in contract_ids.split(',') if x.strip().isdigit()]
    deleted = await ContractService.delete_services(query_db, ids, current_user)
    return ResponseUtil.success(msg=f'删除成功 {deleted} 条')


@contract_controller.post(
    '/submit/{contract_id}',
    summary='提交审批',
    description='草稿/已驳回的合同提交进入 7 级审批链',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('contract:submit')],
)
@Log(title='合同管理', business_type=BusinessType.UPDATE)
async def submit_contract(
    request: Request,
    contract_id: Annotated[int, Path(description='合同ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await ContractService.submit_services(query_db, contract_id, current_user)
    return ResponseUtil.success(msg='提交审批成功', data=data)


@contract_controller.get(
    '/check-no',
    summary='合同编号唯一性校验',
    description='新建/编辑前校验编号是否被占用',
    response_model=DataResponseModel,
)
async def check_contract_no(
    request: Request,
    payload: Annotated[ContractCheckNoModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    available = await ContractService.check_no_services(query_db, payload.contract_no)
    return ResponseUtil.success(data=available, msg='编号可用' if available else '编号已被占用')