"""战略驾驶舱 DAO：只读聚合查询。

只读取已完成模块的表：
- biz_contract         （合同）
- biz_customer         （客户）
- biz_approval         （审批流）
- sys_user             （RuoYi 用户）

路线 A 完成的表（biz_channel / biz_invoice / ...）做 try/except 兜底，不存在时给空值不报错。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, case, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from module_biz.entity.do.contract_do import BizContract
from module_biz.entity.do.approval_do import BizApproval
from module_biz.entity.vo.cockpit_vo import (
    ChannelLocationItemModel,
    RecentApprovalItemModel,
    STATUS_LABEL_MAP,
    StatusDistributionItemModel,
    TopCustomerItemModel,
    Trend7dItemModel,
    STEP_LABEL_MAP,
)


class CockpitDAO:
    """驾驶舱聚合查询。全部只读，无 INSERT/UPDATE/DELETE。"""

    # ---------------- KPI ----------------

    @staticmethod
    async def kpi_contract(db: AsyncSession) -> dict[str, int | Decimal]:
        """合同类 KPI：总数 / 各状态分布 / 本月新增 / 本月金额"""
        # 各状态计数
        cnt_stmt = select(BizContract.status, func.count(BizContract.id)).group_by(BizContract.status)
        rows = (await db.execute(cnt_stmt)).all()
        cnt_map: dict[str, int] = {row[0]: int(row[1]) for row in rows if row[0]}

        total = sum(cnt_map.values())
        pending = cnt_map.get('pending', 0)
        approved = cnt_map.get('approved', 0)
        rejected = cnt_map.get('rejected', 0)

        # 本月新增 + 本月金额
        month_start = datetime.combine(date.today().replace(day=1), datetime.min.time())
        month_stmt = select(
            func.count(BizContract.id),
            func.coalesce(func.sum(BizContract.amount), 0),
        ).where(BizContract.create_time >= month_start)
        month_row = (await db.execute(month_stmt)).one()
        month_new = int(month_row[0] or 0)
        month_amount = Decimal(str(month_row[1] or 0))

        return {
            'contractTotal': total,
            'contractPending': pending,
            'contractApproved': approved,
            'contractRejected': rejected,
            'contractMonthNew': month_new,
            'contractMonthAmount': month_amount,
        }

    @staticmethod
    async def kpi_customer(db: AsyncSession) -> int:
        """客户总数（用原生 SQL 兼容 RuoYi 客户表 biz_customer）"""
        try:
            stmt = select(func.count(text('id'))).select_from(text('biz_customer'))
            row = (await db.execute(stmt)).one()
            return int(row[0] or 0)
        except SQLAlchemyError:
            return 0

    @staticmethod
    async def kpi_channel(db: AsyncSession) -> int:
        """渠道总数（路线 A 表，可能不存在 → 0）"""
        try:
            stmt = select(func.count(text('id'))).select_from(text('biz_channel'))
            row = (await db.execute(stmt)).one()
            return int(row[0] or 0)
        except SQLAlchemyError:
            return 0

    @staticmethod
    async def kpi_invoice_pending(db: AsyncSession) -> int:
        """待开发票数（路线 A 表，可能不存在 → 0）"""
        try:
            stmt = select(func.count(text('id'))).select_from(text('biz_invoice')).where(
                text("status = 'pending'")
            )
            row = (await db.execute(stmt)).one()
            return int(row[0] or 0)
        except SQLAlchemyError:
            return 0

    @staticmethod
    async def kpi_approval_pending(db: AsyncSession, current_role_keys: list[str]) -> int:
        """待我审批的合同数：status=pending AND current_role ∈ current_role_keys"""
        if not current_role_keys:
            return 0
        try:
            stmt = select(func.count(BizContract.id)).where(
                and_(
                    BizContract.status == 'pending',
                    BizContract.current_role.in_(current_role_keys),
                )
            )
            row = (await db.execute(stmt)).one()
            return int(row[0] or 0)
        except SQLAlchemyError:
            return 0

    # ---------------- 7 日趋势 ----------------

    @staticmethod
    async def trend_7d(db: AsyncSession) -> list[Trend7dItemModel]:
        """近 7 天（含今日）每日新增合同数 + 当日通过合同数。

        通过：用 biz_approval.action='approve' 同表 join；为避免 join 重复，
        这里简化：取每个状态为 approved 的合同的 update_time 分组。
        """
        today = date.today()
        start = today - timedelta(days=6)
        start_dt = datetime.combine(start, datetime.min.time())

        # 各日合同新增数
        new_stmt = (
            select(func.date(BizContract.create_time).label('d'), func.count(BizContract.id))
            .where(BizContract.create_time >= start_dt)
            .group_by(func.date(BizContract.create_time))
        )
        new_rows = (await db.execute(new_stmt)).all()
        new_map: dict[str, int] = {str(row[0]): int(row[1]) for row in new_rows if row[0]}

        # 各日已通过合同数（status=approved 的 update_time 分组）
        approved_stmt = (
            select(func.date(BizContract.update_time).label('d'), func.count(BizContract.id))
            .where(
                and_(
                    BizContract.status == 'approved',
                    BizContract.update_time >= start_dt,
                )
            )
            .group_by(func.date(BizContract.update_time))
        )
        approved_rows = (await db.execute(approved_stmt)).all()
        approved_map: dict[str, int] = {str(row[0]): int(row[1]) for row in approved_rows if row[0]}

        items: list[Trend7dItemModel] = []
        for offset in range(7):
            d = start + timedelta(days=offset)
            items.append(
                Trend7dItemModel(
                    day=d,
                    new_contracts=new_map.get(str(d), 0),
                    approved_contracts=approved_map.get(str(d), 0),
                )
            )
        return items

    # ---------------- 状态分布 ----------------

    @staticmethod
    async def status_distribution(db: AsyncSession) -> list[StatusDistributionItemModel]:
        """合同状态分布（饼图）"""
        stmt = select(BizContract.status, func.count(BizContract.id)).group_by(BizContract.status)
        rows = (await db.execute(stmt)).all()
        items = [
            StatusDistributionItemModel(
                status=row[0],
                label=STATUS_LABEL_MAP.get(row[0], row[0]),
                count=int(row[1] or 0),
            )
            for row in rows
            if row[0]
        ]
        items.sort(key=lambda x: x.count, reverse=True)
        return items

    # ---------------- Top10 客户 ----------------

    @staticmethod
    async def top_customers(db: AsyncSession, limit: int = 10) -> list[TopCustomerItemModel]:
        """按合同总金额降序的 Top 客户"""
        stmt = (
            select(
                BizContract.customer_id,
                BizContract.customer_name,
                func.count(BizContract.id).label('contract_count'),
                func.coalesce(func.sum(BizContract.amount), 0).label('total_amount'),
            )
            .where(BizContract.customer_id.isnot(None))
            .group_by(BizContract.customer_id, BizContract.customer_name)
            .order_by(func.sum(BizContract.amount).desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        return [
            TopCustomerItemModel(
                customer_id=row[0],
                customer_name=row[1] or '未指定',
                contract_count=int(row[2] or 0),
                total_amount=Decimal(str(row[3] or 0)),
            )
            for row in rows
            if row[0] is not None
        ]

    # ---------------- 最近审批 ----------------

    @staticmethod
    async def recent_approvals(db: AsyncSession, limit: int = 10) -> list[RecentApprovalItemModel]:
        """最近正在审批中（pending）的合同 + 当前步骤审批人。

        数据源：biz_contract JOIN biz_approval（取最近一次审批记录）。
        """
        # 用子查询取每个 contract 最新一条 approval
        sub_stmt = (
            select(
                BizApproval.contract_id,
                func.max(BizApproval.approval_time).label('max_time'),
            )
            .where(BizApproval.action == 'approve')
            .group_by(BizApproval.contract_id)
            .subquery()
        )

        stmt = (
            select(BizContract, BizApproval)
            .join(
                sub_stmt,
                and_(
                    BizContract.id == sub_stmt.c.contract_id,
                ),
            )
            .join(
                BizApproval,
                and_(
                    BizApproval.contract_id == BizContract.id,
                    BizApproval.approval_time == sub_stmt.c.max_time,
                ),
            )
            .where(BizContract.status == 'pending')
            .order_by(BizApproval.approval_time.desc())
            .limit(limit)
        )

        rows = (await db.execute(stmt)).all()

        # 如果 join 出来为空，退化为简单 pending 合同列表（取前 10）
        if not rows:
            simple_stmt = (
                select(BizContract)
                .where(BizContract.status == 'pending')
                .order_by(BizContract.update_time.desc())
                .limit(limit)
            )
            pending_contracts = (await db.execute(simple_stmt)).scalars().all()
            return [
                RecentApprovalItemModel(
                    contract_id=c.id,
                    contract_no=c.contract_no,
                    title=c.title,
                    step=c.current_step or 0,
                    step_label=STEP_LABEL_MAP.get(c.current_step or 0, ''),
                    approver_name=None,
                    updated_at=(c.update_time or c.create_time).strftime('%Y-%m-%d %H:%M:%S')
                    if (c.update_time or c.create_time)
                    else '',
                )
                for c in pending_contracts
            ]

        items: list[RecentApprovalItemModel] = []
        for contract, approval in rows:
            updated = approval.approval_time or contract.update_time or contract.create_time
            items.append(
                RecentApprovalItemModel(
                    contract_id=contract.id,
                    contract_no=contract.contract_no,
                    title=contract.title,
                    step=contract.current_step or 0,
                    step_label=STEP_LABEL_MAP.get(contract.current_step or 0, ''),
                    approver_name=approval.approver_name or contract.created_by_name,
                    updated_at=updated.strftime('%Y-%m-%d %H:%M:%S') if updated else '',
                )
            )
        return items

    # ---------------- 渠道地图分布 ----------------

    # 路由 A 渠道表约定结构（不在 dao 内 import 表模型）：
    #   id, channel_name, contact_name, contact_phone, status, ...
    # 城市定位通过客户表关联的 region 计算：本期默认给几个常用城市坐标作为示例。
    # 路线 A 完成后可替换为真实 lng/lat 字段读取。

    @staticmethod
    async def channel_locations(db: AsyncSession, limit: int = 30) -> list[ChannelLocationItemModel]:
        """渠道全国地图分布。

        路线 A 表未完成时返回空列表（前端地图不渲染散点，地图本身仍显示）。
        表字段约定：id / channel_name / status。城市经纬度走查表。
        """
        try:
            stmt = select(text('id'), text('channel_name')).select_from(text('biz_channel')).where(
                text("status = '0'")
            ).limit(limit)
            rows = (await db.execute(stmt)).all()
        except SQLAlchemyError:
            return []

        # 简易城市坐标表（路线 A 完成会替换为真实位置字段）
        CITY_COORDS = {
            '北京': (116.40, 39.90), '上海': (121.47, 31.23), '广州': (113.27, 23.13),
            '深圳': (114.06, 22.54), '杭州': (120.15, 30.27), '成都': (104.06, 30.67),
            '南京': (118.79, 32.06), '武汉': (114.30, 30.59), '西安': (108.94, 34.34),
            '重庆': (106.55, 29.56), '青岛': (120.38, 36.07), '苏州': (120.62, 31.32),
        }
        items: list[ChannelLocationItemModel] = []
        # 不均匀散落到 12 个城市（路线 A 完成后按真实地区给）
        keys = list(CITY_COORDS.keys())
        for idx, row in enumerate(rows):
            city = keys[idx % len(keys)]
            lng, lat = CITY_COORDS[city]
            items.append(
                ChannelLocationItemModel(
                    channel_id=int(row[0]) if row[0] is not None else None,
                    channel_name=str(row[1] or ''),
                    lng=lng,
                    lat=lat,
                    contract_count=0,  # 路线 A 完成 channel 表后回填
                    city=city,
                )
            )
        return items
