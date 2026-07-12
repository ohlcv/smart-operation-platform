"""仪表盘 controller。

端点：
- GET /biz/dashboard/overview      单端点，60s 缓存，返回仪表盘全量数据
- GET /biz/dashboard/ai-diagnose   AI 智能大脑

权限注解：`biz:dashboard:view`（menu_id=13 的 perms 已在 SQL 挂载）。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.service.dashboard_service import DashboardService
from utils.response_util import ResponseUtil


dashboard_controller = APIRouterPro(
    prefix='/biz/dashboard',
    order_num=30,
    tags=['业务管理-仪表盘'],
    dependencies=[PreAuthDependency()],
)


@dashboard_controller.get(
    '/overview',
    summary='获取仪表盘总览数据',
    description=(
        '聚合返回 6 个 KPI + 7 日趋势 + 状态分布 + Top10 客户 + '
        '最近审批流 + 渠道地图分布。后端 60s 内存缓存。'
        '可选 province 参数支持省份联动（点地图省份过滤 KPI/趋势/Top10/状态分布）。'
    ),
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('biz:dashboard:view')],
)
async def get_dashboard_overview(
    request: Request,
    province: Annotated[str, Query(description='省份过滤（如「山东省」），空=全国')] = '',
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,  # type: ignore[assignment]
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()] = None,  # type: ignore[assignment]
) -> Response:
    data = await DashboardService.overview_services(query_db, current_user, province=province)
    return ResponseUtil.success(data=data, msg='查询成功')


@dashboard_controller.get(
    '/ai-diagnose',
    summary='AI 智能大脑 - 风险诊断',
    description=(
        '6 维雷达图（资金合规/风险防控/审批时效/数据质量/渠道覆盖/客户活跃）'
        '+ 风险条目 + 资金/运营建议。规则引擎保底。'
    ),
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('biz:dashboard:view')],
)
async def get_dashboard_ai_diagnose(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,  # type: ignore[assignment]
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()] = None,  # type: ignore[assignment]
) -> Response:
    data = await DashboardService.ai_diagnose_services(query_db, current_user)
    return ResponseUtil.success(data=data, msg='AI 诊断完成')