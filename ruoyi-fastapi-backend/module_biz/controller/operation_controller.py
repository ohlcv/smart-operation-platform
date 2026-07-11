"""经营数据 controller（路径前缀 /biz/operation）。"""
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
from module_biz.entity.vo.operation_vo import (
    OperationComparisonQueryModel,
    OperationCreateModel,
    OperationQueryModel,
    OperationUpdateModel,
)
from module_biz.service.operation_service import OperationService
from utils.response_util import ResponseUtil

operation_controller = APIRouterPro(
    prefix='/biz/operation', order_num=25, tags=['业务管理-经营数据'], dependencies=[PreAuthDependency()]
)


@operation_controller.get(
    '/list',
    summary='经营数据列表',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('operation:list')],
)
async def get_operation_list(
    request: Request,
    query: Annotated[OperationQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await OperationService.list_services(query_db, query, current_user)
    return ResponseUtil.success(
        msg='查询成功',
        rows=result['rows'],
        dict_content={
            'pageNum': result['page_num'],
            'pageSize': result['page_size'],
            'total': result['total'],
        },
    )


@operation_controller.get(
    '/{op_id}',
    summary='经营数据详情',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('operation:list')],
)
async def get_operation_detail(
    request: Request,
    op_id: Annotated[int, Path(description='经营数据ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await OperationService.detail_services(query_db, op_id, current_user)
    return ResponseUtil.success(data=data)


@operation_controller.post(
    '',
    summary='新建经营数据',
    description='(period, period_type, business_line) 唯一',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('operation:add')],
)
@ValidateFields(validate_model='create_services')
@Log(title='经营数据', business_type=BusinessType.INSERT)
async def add_operation(
    request: Request,
    payload: OperationCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    new_id = await OperationService.create_services(query_db, payload, current_user)
    return ResponseUtil.success(msg='新增成功', data={'id': new_id})


@operation_controller.put(
    '',
    summary='编辑经营数据',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('operation:edit')],
)
@Log(title='经营数据', business_type=BusinessType.UPDATE)
async def update_operation(
    request: Request,
    payload: OperationUpdateModel,
    op_id: Annotated[int, Query(description='经营数据ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await OperationService.update_services(query_db, op_id, payload, current_user)
    return ResponseUtil.success(msg='修改成功')


@operation_controller.delete(
    '/{op_id}',
    summary='删除经营数据',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('operation:delete')],
)
@Log(title='经营数据', business_type=BusinessType.DELETE)
async def delete_operation(
    request: Request,
    op_id: Annotated[int, Path(description='经营数据ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    deleted = await OperationService.delete_services(query_db, op_id, current_user)
    return ResponseUtil.success(msg=f'删除成功 {deleted} 条')


@operation_controller.get(
    '/comparison',
    summary='同比环比对比',
    description='根据 period 自动算上期和去年同期',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('operation:comparison')],
)
async def get_operation_comparison(
    request: Request,
    query: Annotated[OperationComparisonQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await OperationService.comparison_services(query_db, query, current_user)
    return ResponseUtil.success(data=data)


@operation_controller.get(
    '/options',
    summary='下拉选项',
    response_model=DataResponseModel,
)
async def get_operation_options(
    request: Request,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await OperationService.options_services(current_user)
    return ResponseUtil.success(data=data)