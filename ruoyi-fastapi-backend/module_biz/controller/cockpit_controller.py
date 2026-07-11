"""战略驾驶舱 controller。

端点：
- GET /biz/cockpit/overview      单端点，60s 缓存，返回驾驶舱全量数据
- GET /biz/cockpit/ai-diagnose   AI 智能大脑（v3.3 新增）

权限注解：`biz:cockpit:view`（menu_id=13 的 perms 已在 SQL 挂载）。
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
        'v3.3：可选 province 参数支持省份联动（点地图省份过滤 KPI/趋势/Top10/状态分布）。'
    ),
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('biz:cockpit:view')],
)
async def get_cockpit_overview(
    request: Request,
    province: Annotated[str, Query(description='省份过滤（如「山东省」），空=全国')] = '',
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,  # type: ignore[assignment]
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()] = None,  # type: ignore[assignment]
) -> Response:
    data = await CockpitService.overview_services(query_db, current_user, province=province)
    return ResponseUtil.success(data=data, msg='查询成功')


@cockpit_controller.get(
    '/ai-diagnose',
    summary='AI 智能大脑 - 风险诊断',
    description=(
        '6 维雷达图（资金合规/风险防控/审批时效/数据质量/渠道覆盖/客户活跃）'
        '+ 风险条目 + 资金/运营建议。D13 规则引擎保底。'
    ),
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('biz:cockpit:view')],
)
async def get_cockpit_ai_diagnose(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()] = None,  # type: ignore[assignment]
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()] = None,  # type: ignore[assignment]
) -> Response:
    data = await CockpitService.ai_diagnose_services(query_db, current_user)
    return ResponseUtil.success(data=data, msg='AI 诊断完成')