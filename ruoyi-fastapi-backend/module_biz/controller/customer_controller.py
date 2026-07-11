"""客户管理 controller"""
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
from module_biz.entity.vo.customer_vo import (
    CustomerCreateModel,
    CustomerQueryModel,
    CustomerUpdateModel,
)
from module_biz.service.customer_service import CustomerService
from utils.log_util import logger
from utils.response_util import ResponseUtil

customer_controller = APIRouterPro(
    prefix='/biz/customer', order_num=21, tags=['业务管理-客户管理'], dependencies=[PreAuthDependency()]
)


@customer_controller.get(
    '/list',
    summary='获取客户列表',
    description='分页查询客户列表',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('customer:list')],
)
async def get_customer_list(
    request: Request,
    query: Annotated[CustomerQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await CustomerService.list_services(query_db, query, current_user)
    return ResponseUtil.success(
        msg='查询成功',
        rows=result['rows'],
        dict_content={
            'pageNum': result['page_num'],
            'pageSize': result['page_size'],
            'total': result['total'],
        },
    )


@customer_controller.get(
    '/{customer_id}',
    summary='客户详情',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('customer:list')],
)
async def get_customer_detail(
    request: Request,
    customer_id: Annotated[int, Path(description='客户ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await CustomerService.detail_services(query_db, customer_id, current_user)
    return ResponseUtil.success(data=data)


@customer_controller.post(
    '',
    summary='新建客户',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('customer:add')],
)
@ValidateFields(validate_model='create_services')
@Log(title='客户管理', business_type=BusinessType.INSERT)
async def add_customer(
    request: Request,
    payload: CustomerCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    new_id = await CustomerService.create_services(query_db, payload, current_user)
    logger.info(f'新建客户 id={new_id}')
    return ResponseUtil.success(msg='新增成功', data={'id': new_id})


@customer_controller.put(
    '',
    summary='编辑客户',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('customer:edit')],
)
@Log(title='客户管理', business_type=BusinessType.UPDATE)
async def update_customer(
    request: Request,
    payload: CustomerUpdateModel,
    customer_id: Annotated[int, Query(description='客户ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await CustomerService.update_services(query_db, customer_id, payload, current_user)
    return ResponseUtil.success(msg='修改成功')


@customer_controller.delete(
    '/{customer_ids}',
    summary='删除客户',
    description='逗号分隔多个 ID',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('customer:delete')],
)
@Log(title='客户管理', business_type=BusinessType.DELETE)
async def delete_customer(
    request: Request,
    customer_ids: Annotated[str, Path(description='客户ID，逗号分隔')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    ids = [int(x) for x in customer_ids.split(',') if x.strip().isdigit()]
    deleted = await CustomerService.delete_services(query_db, ids, current_user)
    return ResponseUtil.success(msg=f'删除成功 {deleted} 条')