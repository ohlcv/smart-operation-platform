"""发票管理 controller（路径前缀 /biz/invoice）。"""
from __future__ import annotations

from datetime import date as date_t
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
from module_biz.entity.vo.invoice_vo import (
    InvoiceCreateModel,
    InvoiceQueryModel,
    InvoiceUpdateModel,
    InvoiceVoidModel,
)
from module_biz.service.invoice_service import InvoiceService
from utils.response_util import ResponseUtil

invoice_controller = APIRouterPro(
    prefix='/biz/invoice', order_num=23, tags=['业务管理-发票管理'], dependencies=[PreAuthDependency()]
)


@invoice_controller.get(
    '/list',
    summary='发票列表',
    description='分页查询发票（关键字/状态/类型/合同）',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('invoice:list')],
)
async def get_invoice_list(
    request: Request,
    query: Annotated[InvoiceQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await InvoiceService.list_services(query_db, query, current_user)
    return ResponseUtil.success(
        msg='查询成功',
        rows=result['rows'],
        dict_content={
            'pageNum': result['page_num'],
            'pageSize': result['page_size'],
            'total': result['total'],
        },
    )


@invoice_controller.get(
    '/{invoice_id:int}',
    summary='发票详情',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('invoice:list')],
)
async def get_invoice_detail(
    request: Request,
    invoice_id: Annotated[int, Path(description='发票ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await InvoiceService.detail_services(query_db, invoice_id, current_user)
    return ResponseUtil.success(data=data)


@invoice_controller.post(
    '',
    summary='新建发票',
    description='为已审批通过的合同开票，1:1 关联',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('invoice:add')],
)
@ValidateFields(validate_model='create_services')
@Log(title='发票管理', business_type=BusinessType.INSERT)
async def add_invoice(
    request: Request,
    payload: InvoiceCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    new_id = await InvoiceService.create_services(query_db, payload, current_user)
    return ResponseUtil.success(msg='新建成功', data={'id': new_id})


@invoice_controller.put(
    '',
    summary='编辑发票',
    description='仅待开（pending）状态可编辑',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('invoice:edit')],
)
@Log(title='发票管理', business_type=BusinessType.UPDATE)
async def update_invoice(
    request: Request,
    payload: InvoiceUpdateModel,
    invoice_id: Annotated[int, Query(description='发票ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await InvoiceService.update_services(query_db, invoice_id, payload, current_user)
    return ResponseUtil.success(msg='修改成功')


@invoice_controller.delete(
    '/{invoice_id:int}',
    summary='删除发票',
    description='仅待开（pending）状态可删；issued/void 不可删',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('invoice:delete')],
)
@Log(title='发票管理', business_type=BusinessType.DELETE)
async def delete_invoice(
    request: Request,
    invoice_id: Annotated[int, Path(description='发票ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    deleted = await InvoiceService.delete_services(query_db, invoice_id, current_user)
    return ResponseUtil.success(msg=f'删除成功 {deleted} 条')


@invoice_controller.post(
    '/issue/{invoice_id}',
    summary='标记为已开',
    description='pending → issued；可指定开票日期',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('invoice:issue')],
)
@Log(title='发票管理', business_type=BusinessType.UPDATE)
async def issue_invoice(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    invoice_id: Annotated[int, Path(description='发票ID')],
    issue_date: Annotated[str | None, Query(description='开票日期 YYYY-MM-DD')] = None,
) -> Response:
    parsed = date_t.fromisoformat(issue_date) if issue_date else None
    data = await InvoiceService.issue_services(query_db, invoice_id, current_user, parsed)
    return ResponseUtil.success(msg='已标记为已开', data=data)


@invoice_controller.post(
    '/void/{invoice_id}',
    summary='作废发票',
    description='仅已开（issued）发票可作废',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('invoice:void')],
)
@Log(title='发票管理', business_type=BusinessType.UPDATE)
async def void_invoice(
    request: Request,
    invoice_id: Annotated[int, Path(description='发票ID')],
    payload: InvoiceVoidModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await InvoiceService.void_services(query_db, invoice_id, payload, current_user)
    return ResponseUtil.success(msg='已作废')


@invoice_controller.get(
    '/options',
    summary='下拉选项',
    description='返回发票状态/类型选项',
    response_model=DataResponseModel,
)
async def get_invoice_options(
    request: Request,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await InvoiceService.options_services(current_user)
    return ResponseUtil.success(data=data)
