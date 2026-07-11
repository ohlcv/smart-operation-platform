"""战略驾驶舱 Service 层。

按 docs/04-开发/开发计划/路线B-大屏可视化优先.md §2.1 实现。

聚合 6 个数据源：
- 合同 KPI / 7 日趋势 / 状态分布 / Top10 客户
- 客户总数
- 审批动态
- 渠道地图分布
- 待办审批（按当前用户角色）

缓存策略：60s 内存缓存（避免高频访问打 DB），多用户场景下数据相差不大。
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.cockpit_dao import CockpitDAO
from module_biz.entity.vo.cockpit_vo import CockpitOverviewModel


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


class CockpitService:
    @staticmethod
    async def overview_services(db: AsyncSession, current_user: CurrentUserModel | None) -> dict[str, Any]:
        """GET /biz/cockpit/overview 主入口。

        60s 缓存：相同用户两次访问 60s 内返回同一份数据。
        cache key = user_id || '_' || epoch_bucket(60s)
        """
        uid = (current_user.user.user_id if current_user and current_user.user else 0)
        cache_key = f"cockpit_overview_{uid}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        # 6 个 KPI
        kpi_contract = await CockpitDAO.kpi_contract(db)
        kpi_customer = await CockpitDAO.kpi_customer(db)
        kpi_channel = await CockpitDAO.kpi_channel(db)
        kpi_invoice = await CockpitDAO.kpi_invoice_pending(db)
        role_keys = _current_user_role_keys(current_user)
        kpi_approval = await CockpitDAO.kpi_approval_pending(db, role_keys)

        kpi_payload = {
            **kpi_contract,
            'customerTotal': kpi_customer,
            'channelTotal': kpi_channel,
            'invoicePending': kpi_invoice,
            'approvalPending': kpi_approval,
        }

        # 7 个并发查询（先后顺序无关，但为简洁起见顺序执行）
        trend_7d = await CockpitDAO.trend_7d(db)
        status_distribution = await CockpitDAO.status_distribution(db)
        top_customers = await CockpitDAO.top_customers(db)
        recent_approvals = await CockpitDAO.recent_approvals(db)
        channel_locations = await CockpitDAO.channel_locations(db)

        overview = CockpitOverviewModel(
            kpi=kpi_payload,  # type: ignore[arg-type]
            trend_7d=trend_7d,
            status_distribution=status_distribution,
            top_customers=top_customers,
            recent_approvals=recent_approvals,
            channel_locations=channel_locations,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )

        result = overview.model_dump(by_alias=True, mode='json')
        _cache_set(cache_key, result)
        return result
