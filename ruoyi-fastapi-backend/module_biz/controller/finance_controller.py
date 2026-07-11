"""财务管理 controller（路径前缀 /biz/finance）。"""
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
from module_biz.entity.vo.finance_vo import (
    BankStatementImportModel,
    FinanceCreateModel,
    FinanceQueryModel,
    FinanceUpdateModel,
)
from module_biz.service.finance_service import FinanceService
from utils.response_util import ResponseUtil

finance_controller = APIRouterPro(
    prefix='/biz/finance', order_num=24, tags=['业务管理-财务管理'], dependencies=[PreAuthDependency()]
)


@finance_controller.get(
    '/list',
    summary='财务流水列表',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('finance:list')],
)
async def get_finance_list(
    request: Request,
    query: Annotated[FinanceQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await FinanceService.list_services(query_db, query, current_user)
    return ResponseUtil.success(
        msg='查询成功',
        rows=result['rows'],
        dict_content={
            'pageNum': result['page_num'],
            'pageSize': result['page_size'],
            'total': result['total'],
        },
    )


@finance_controller.get(
    '/{entry_id:int}',
    summary='财务流水详情',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('finance:list')],
)
async def get_finance_detail(
    request: Request,
    entry_id: Annotated[int, Path(description='流水ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await FinanceService.detail_services(query_db, entry_id, current_user)
    return ResponseUtil.success(data=data)


@finance_controller.post(
    '',
    summary='新建流水',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('finance:add')],
)
@ValidateFields(validate_model='create_services')
@Log(title='财务管理', business_type=BusinessType.INSERT)
async def add_finance(
    request: Request,
    payload: FinanceCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    new_id = await FinanceService.create_services(query_db, payload, current_user)
    return ResponseUtil.success(msg='新增成功', data={'id': new_id})


@finance_controller.put(
    '',
    summary='编辑流水',
    description='仅未对账的流水可编辑',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('finance:edit')],
)
@Log(title='财务管理', business_type=BusinessType.UPDATE)
async def update_finance(
    request: Request,
    payload: FinanceUpdateModel,
    entry_id: Annotated[int, Query(description='流水ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await FinanceService.update_services(query_db, entry_id, payload, current_user)
    return ResponseUtil.success(msg='修改成功')


@finance_controller.delete(
    '/{entry_id:int}',
    summary='删除流水',
    description='仅未对账的流水可删',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('finance:delete')],
)
@Log(title='财务管理', business_type=BusinessType.DELETE)
async def delete_finance(
    request: Request,
    entry_id: Annotated[int, Path(description='流水ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    deleted = await FinanceService.delete_services(query_db, entry_id, current_user)
    return ResponseUtil.success(msg=f'删除成功 {deleted} 条')


@finance_controller.post(
    '/clear/{entry_id}',
    summary='标记对账',
    description='cleared 0→1',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('finance:edit')],
)
@Log(title='财务管理', business_type=BusinessType.UPDATE)
async def clear_finance(
    request: Request,
    entry_id: Annotated[int, Path(description='流水ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await FinanceService.clear_services(query_db, entry_id, current_user)
    return ResponseUtil.success(msg='已标记为已对账')


@finance_controller.get(
    '/summary',
    summary='按月汇总',
    description='按周期汇总应收/应付/已对账/未对账',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('finance:list')],
)
async def get_finance_summary(
    request: Request,
    period: Annotated[str, Query(description='YYYY-MM', pattern=r'^\d{4}-\d{2}$')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await FinanceService.summary_services(query_db, period, current_user)
    return ResponseUtil.success(data=data)


@finance_controller.post(
    '/import-bank',
    summary='银行对账单 CSV 导入',
    description='手工导入对账单到 biz_bank_statement',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('finance:import')],
)
@Log(title='财务管理', business_type=BusinessType.IMPORT)
async def import_bank_statement(
    request: Request,
    payload: BankStatementImportModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await FinanceService.import_bank_statement_services(query_db, payload, current_user)
    return ResponseUtil.success(
        msg=f'导入完成：批次 {result["batch_no"]}，成功 {result["success"]} 条',
        data=result,
    )


@finance_controller.get(
    '/options',
    summary='下拉选项',
    description='返回流水类型/方向选项',
    response_model=DataResponseModel,
)
async def get_finance_options(
    request: Request,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await FinanceService.options_services(current_user)
    return ResponseUtil.success(data=data)