"""渠道管理 controller（路径前缀 /biz/channel）。

严格遵循 docs/03-设计/API设计文档.md §五 + ADR D24：
- 路径 /biz/channel
- JSON 字段一律 camelCase
- 权限注解：biz:channel:list / add / edit / delete / import
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
from module_biz.entity.vo.channel_vo import (
    ChannelCategoryOptionModel,
    ChannelCreateModel,
    ChannelImportModel,
    ChannelQueryModel,
    ChannelUpdateModel,
)
from module_biz.service.channel_service import ChannelService
from utils.response_util import ResponseUtil

channel_controller = APIRouterPro(
    prefix='/biz/channel', order_num=22, tags=['业务管理-渠道管理'], dependencies=[PreAuthDependency()]
)


@channel_controller.get(
    '/list',
    summary='获取渠道列表',
    description='分页查询渠道列表，支持关键字/分类/状态过滤',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('channel:list')],
)
async def get_channel_list(
    request: Request,
    query: Annotated[ChannelQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await ChannelService.list_services(query_db, query, current_user)
    return ResponseUtil.success(
        msg='查询成功',
        rows=result['rows'],
        dict_content={
            'pageNum': result['page_num'],
            'pageSize': result['page_size'],
            'total': result['total'],
        },
    )


@channel_controller.get(
    '/{channel_id}',
    summary='获取渠道详情',
    description='按 ID 获取渠道完整信息',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('channel:list')],
)
async def get_channel_detail(
    request: Request,
    channel_id: Annotated[int, Path(description='渠道ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await ChannelService.detail_services(query_db, channel_id, current_user)
    return ResponseUtil.success(data=data)


@channel_controller.post(
    '',
    summary='新建渠道',
    description='新建渠道（启用状态）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('channel:add')],
)
@ValidateFields(validate_model='create_services')
@Log(title='渠道管理', business_type=BusinessType.INSERT)
async def add_channel(
    request: Request,
    payload: ChannelCreateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    new_id = await ChannelService.create_services(query_db, payload, current_user)
    return ResponseUtil.success(msg='新增成功', data={'id': new_id})


@channel_controller.put(
    '',
    summary='编辑渠道',
    description='编辑渠道信息',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('channel:edit')],
)
@Log(title='渠道管理', business_type=BusinessType.UPDATE)
async def update_channel(
    request: Request,
    payload: ChannelUpdateModel,
    channel_id: Annotated[int, Query(description='渠道ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    await ChannelService.update_services(query_db, channel_id, payload, current_user)
    return ResponseUtil.success(msg='修改成功')


@channel_controller.delete(
    '/{channel_ids}',
    summary='删除渠道',
    description='批量删除渠道（逗号分隔），有合同关联的渠道拒绝删除',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('channel:delete')],
)
@Log(title='渠道管理', business_type=BusinessType.DELETE)
async def delete_channel(
    request: Request,
    channel_ids: Annotated[str, Path(description='渠道ID，逗号分隔')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    ids = [int(x) for x in channel_ids.split(',') if x.strip().isdigit()]
    deleted = await ChannelService.delete_services(query_db, ids, current_user)
    return ResponseUtil.success(msg=f'删除成功 {deleted} 条')


@channel_controller.get(
    '/category-options',
    summary='渠道分类下拉选项',
    description='返回渠道分类枚举（前端下拉）',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('channel:list')],
)
async def get_channel_category_options(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    options = await ChannelService.category_options_services(query_db, current_user)
    return ResponseUtil.success(rows=options, msg='查询成功')


@channel_controller.post(
    '/import',
    summary='CSV 批量导入渠道',
    description='按行导入渠道；遇到编码冲突默认跳过，可选报错',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('channel:import')],
)
@Log(title='渠道管理', business_type=BusinessType.IMPORT)
async def import_channels(
    request: Request,
    payload: ChannelImportModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await ChannelService.import_services(query_db, payload, current_user)
    return ResponseUtil.success(
        msg=f'导入完成：成功 {result["success"]} 条，跳过 {result["skipped"]} 条，失败 {len(result["errors"])} 条',
        data=result,
    )
