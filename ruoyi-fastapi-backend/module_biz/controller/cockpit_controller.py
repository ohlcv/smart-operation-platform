"""战略驾驶舱 controller。

GET /biz/cockpit/overview — 单端点，60s 缓存，返回驾驶舱全量数据。

权限注解：`biz:cockpit:view`（menu_id=13 的 perms 已在 SQL 挂载）。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.service.cockpit_service import CockpitService
from utils.response_util import ResponseUtil


cockpit_controller = APIRouterPro(
    prefix='/biz/cockpit',
    order_num=30,
    tags=['业务管理-战略驾驶舱'],
    dependencies=[PreAuthDependency()],
)


@cockpit_controller.get(
    '/overview',
    summary='获取驾驶舱总览数据',
    description=(
        '聚合返回 6 个 KPI + 7 日趋势 + 状态分布 + Top10 客户 + '
        '最近审批流 + 渠道地图分布。后端 60s 内存缓存。'
    ),
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('biz:cockpit:view')],
)
async def get_cockpit_overview(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    data = await CockpitService.overview_services(query_db, current_user)
    return ResponseUtil.success(data=data, msg='查询成功')
