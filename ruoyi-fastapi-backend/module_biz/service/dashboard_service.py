"""仪表盘 Service 层。

按 docs/04-开发/开发计划/仪表盘开发计划.md §2.1 实现。

聚合 6 个数据源：
- 合同 KPI / 7 日趋势 / 状态分布 / Top10 客户
- 客户总数
- 审批动态
- 渠道地图分布
- 待办审批（按当前用户角色）

v3.3 路线 C 升级：
- overview 加 province 参数支持省份联动
- DAO 改 asyncio.gather 并发（9 SQL → 单次延迟 < 200ms）
- 新增 ai_diagnose 入口（AI 智能大脑）

缓存策略：60s 内存缓存（避免高频访问打 DB），多用户场景下数据相差不大。
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.dashboard_dao import DashboardDAO
from module_biz.entity.vo.dashboard_vo import AiDiagnoseModel, DashboardOverviewModel


# 简单的模块级缓存（线程安全的 dict + 时间戳）
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SECONDS = 60


def _cache_get(key: str) -> dict[str, Any] | None:
    """取缓存。返回 None 表示缓存已失效。"""
    if key not in _CACHE:
        return None
    cached_at, data = _CACHE[key]
    if time.time() - cached_at > _CACHE_TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return data


def _cache_set(key: str, data: dict[str, Any]) -> None:
    _CACHE[key] = (time.time(), data)


def _current_user_role_keys(current_user: CurrentUserModel | None) -> list[str]:
    """提取当前用户的角色 key 列表（如 ['business_handler', 'admin']）。

    用于计算「待我审批」KPI。
    """
    if not current_user or not current_user.user:
        return []
    role_keys: list[str] = []
    if current_user.roles:
        for role in current_user.roles:
            key = (
                role.get('role_key') if isinstance(role, dict)
                else getattr(role, 'role_key', None)
            )
            if key and key not in role_keys:
                role_keys.append(key)
    return role_keys


class DashboardService:
    @staticmethod
    async def overview_services(
        db: AsyncSession,
        current_user: CurrentUserModel | None,
        province: str = '',
    ) -> dict[str, Any]:
        """GET /biz/dashboard/overview 主入口（v3.6 URL 迁到 /biz/dashboard/）。

        60s 缓存：相同 province + user_id 60s 内返回同一份数据。
        v3.3：DAO 改 asyncio.gather 并发，9 个 SQL 并发执行。
        """
        uid = (current_user.user.user_id if current_user and current_user.user else 0)
        cache_key = f"dashboard_overview_{uid}_{province or 'national'}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        role_keys = _current_user_role_keys(current_user)

        # 11 个 DAO 调用并发执行（v3.12 加 kpi_operation）
        (
            kpi_contract,
            kpi_customer,
            kpi_channel,
            kpi_invoice,
            kpi_approval,
            kpi_operation,
            trend_7d,
            revenue_trend,
            status_distribution,
            top_customers,
            recent_approvals,
            channel_locations,
        ) = await asyncio.gather(
            DashboardDAO.kpi_contract(db, province),
            DashboardDAO.kpi_customer(db),
            DashboardDAO.kpi_channel(db),
            DashboardDAO.kpi_invoice_pending(db),
            DashboardDAO.kpi_approval_pending(db, role_keys),
            DashboardDAO.kpi_operation(db, province),  # v3.12：SRS B1-01 核心财务指标（营收/毛利/订单数）
            DashboardDAO.trend_7d(db, province),
            DashboardDAO.trend_revenue(db, province),  # v3.11：省份联动（contract.amount 按月聚合）
            DashboardDAO.status_distribution(db, province),
            DashboardDAO.top_customers(db, province),
            DashboardDAO.recent_approvals(db),
            DashboardDAO.channel_locations(db),
        )

        kpi_payload = {
            **kpi_contract,
            'customerTotal': kpi_customer,
            'channelTotal': kpi_channel,
            'invoicePending': kpi_invoice,
            'approvalPending': kpi_approval,
            **kpi_operation,  # v3.12：operationRevenue/operationGrossProfit/operationContractCount
        }

        overview = DashboardOverviewModel(
            kpi=kpi_payload,  # type: ignore[arg-type]
            trend_7d=trend_7d,
            revenue_trend=revenue_trend,
            status_distribution=status_distribution,
            top_customers=top_customers,
            recent_approvals=recent_approvals,
            channel_locations=channel_locations,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            province=province,
        )

        result = overview.model_dump(by_alias=True, mode='json')
        _cache_set(cache_key, result)
        return result

    @staticmethod
    async def ai_diagnose_services(
        db: AsyncSession,
        current_user: CurrentUserModel | None,
    ) -> dict[str, Any]:
        """GET /biz/dashboard/ai-diagnose 主入口（v3.6 URL 迁到 /biz/dashboard/）。

        AI 智能大脑：6 维雷达 + 风险诊断 + 资金建议。
        30s 缓存（数据时效更敏感）。
        """
        uid = (current_user.user.user_id if current_user and current_user.user else 0)
        cache_key = f"dashboard_ai_diagnose_{uid}"
        cached = _cache_get(cache_key)
        if cached is not None and time.time() - _CACHE[cache_key][0] < 30:
            return cached

        role_keys = _current_user_role_keys(current_user)
        result = await DashboardDAO.ai_diagnose(db, role_keys)
        _cache_set(cache_key, result.model_dump(by_alias=True, mode='json'))
        return result.model_dump(by_alias=True, mode='json')