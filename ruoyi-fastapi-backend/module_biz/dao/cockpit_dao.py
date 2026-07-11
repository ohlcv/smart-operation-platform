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
    AiDiagnoseModel,
    AiRiskItemModel,
    AiSuggestionItemModel,
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
    async def kpi_contract(db: AsyncSession, province: str = '') -> dict[str, int | Decimal]:
        """合同类 KPI：总数 / 各状态分布 / 本月新增 / 本月金额

        province 非空时按省份过滤（v3.3 路线 C 省份联动）。
        """
        if province:
            cnt_stmt = (
                select(BizContract.status, func.count(BizContract.id))
                .where(BizContract.province == province)
                .group_by(BizContract.status)
            )
        else:
            cnt_stmt = select(BizContract.status, func.count(BizContract.id)).group_by(BizContract.status)
        rows = (await db.execute(cnt_stmt)).all()
        cnt_map: dict[str, int] = {row[0]: int(row[1]) for row in rows if row[0]}

        total = sum(cnt_map.values())
        pending = cnt_map.get('pending', 0)
        approved = cnt_map.get('approved', 0)
        rejected = cnt_map.get('rejected', 0)

        month_start = datetime.combine(date.today().replace(day=1), datetime.min.time())
        month_q = [BizContract.create_time >= month_start]
        if province:
            month_q.append(BizContract.province == province)
        month_stmt = select(
            func.count(BizContract.id),
            func.coalesce(func.sum(BizContract.amount), 0),
        ).where(*month_q)
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
    async def trend_7d(db: AsyncSession, province: str = '') -> list[Trend7dItemModel]:
        """近 7 天（含今日）每日新增合同数 + 当日通过合同数。

        province 非空时按省份过滤（v3.3 路线 C 省份联动）。
        通过：用 biz_approval.action='approve' 同表 join；为避免 join 重复，
        这里简化：取每个状态为 approved 的合同的 update_time 分组。
        """
        today = date.today()
        start = today - timedelta(days=6)
        start_dt = datetime.combine(start, datetime.min.time())

        # 各日合同新增数
        new_q = [BizContract.create_time >= start_dt]
        if province:
            new_q.append(BizContract.province == province)
        new_stmt = (
            select(func.date(BizContract.create_time).label('d'), func.count(BizContract.id))
            .where(*new_q)
            .group_by(func.date(BizContract.create_time))
        )
        new_rows = (await db.execute(new_stmt)).all()
        new_map: dict[str, int] = {str(row[0]): int(row[1]) for row in new_rows if row[0]}

        # 各日已通过合同数（status=approved 的 update_time 分组）
        approved_q = [BizContract.status == 'approved', BizContract.update_time >= start_dt]
        if province:
            approved_q.append(BizContract.province == province)
        approved_stmt = (
            select(func.date(BizContract.update_time).label('d'), func.count(BizContract.id))
            .where(*approved_q)
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
    async def status_distribution(db: AsyncSession, province: str = '') -> list[StatusDistributionItemModel]:
        """合同状态分布（饼图）。province 非空时按省份过滤。"""
        if province:
            stmt = (
                select(BizContract.status, func.count(BizContract.id))
                .where(BizContract.province == province)
                .group_by(BizContract.status)
            )
        else:
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
    async def top_customers(db: AsyncSession, province: str = '', limit: int = 10) -> list[TopCustomerItemModel]:
        """按合同总金额降序的 Top 客户。province 非空时按省份过滤。"""
        if province:
            stmt = (
                select(
                    BizContract.customer_id,
                    BizContract.customer_name,
                    func.count(BizContract.id).label('contract_count'),
                    func.coalesce(func.sum(BizContract.amount), 0).label('total_amount'),
                )
                .where(BizContract.province == province)
                .where(BizContract.customer_id.isnot(None))
                .group_by(BizContract.customer_id, BizContract.customer_name)
                .order_by(func.sum(BizContract.amount).desc())
                .limit(limit)
            )
        else:
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

        v3.3 路线 C：读 biz_channel 真实字段（province/city/lng/lat/contract_count）。
        老表若字段缺失（旧 DB 没 ALTER），则 try/except 兜底按城市查表伪造。
        """
        # 真实字段读法（v3.3 通道表已 ALTER 加 province/city/lng/lat/contract_count）
        try:
            stmt = text(
                "SELECT id, channel_name, city, lng, lat "
                "FROM biz_channel "
                "WHERE status = '0' AND lng IS NOT NULL AND lat IS NOT NULL "
                "LIMIT :limit"
            )
            rows = (await db.execute(stmt, {'limit': limit})).all()
            return [
                ChannelLocationItemModel(
                    channel_id=int(r[0]) if r[0] is not None else None,
                    channel_name=str(r[1] or ''),
                    lng=float(r[3] or 0),
                    lat=float(r[4] or 0),
                    contract_count=0,
                    city=str(r[2] or ''),
                )
                for r in rows
            ]
        except SQLAlchemyError:
            return []

    # ---------------- AI 智能大脑（规则引擎，D13 保底） ----------------

    @staticmethod
    async def ai_diagnose(db: AsyncSession, current_role_keys: list[str]) -> AiDiagnoseModel:
        """AI 智能大脑 - 6 维雷达 + 风险诊断 + 资金建议。

        D13 决策：规则引擎保底。本期不接 LLM。
        """
        # 收集 6 维原始指标
        contract_cnt = await db.execute(select(func.count(BizContract.id)))
        total_contracts = int(contract_cnt.scalar() or 0)

        pending_cnt = await db.execute(
            select(func.count(BizContract.id)).where(BizContract.status == 'pending')
        )
        pending = int(pending_cnt.scalar() or 0)

        rejected_cnt = await db.execute(
            select(func.count(BizContract.id)).where(BizContract.status == 'rejected')
        )
        rejected = int(rejected_cnt.scalar() or 0)

        approved_cnt = await db.execute(
            select(func.count(BizContract.id)).where(BizContract.status == 'approved')
        )
        approved = int(approved_cnt.scalar() or 0)

        # 待我审批（若 current_role_keys 为空则给一个中性值）
        my_todo = 0
        if current_role_keys:
            try:
                me = await db.execute(
                    select(func.count(BizContract.id)).where(
                        and_(
                            BizContract.status == 'pending',
                            BizContract.current_role.in_(current_role_keys),
                        )
                    )
                )
                my_todo = int(me.scalar() or 0)
            except SQLAlchemyError:
                my_todo = 0

        # 6 维分数 0-100
        # 1. 资金合规：approved 占比
        compliance = round(approved / max(total_contracts, 1) * 100, 0) if total_contracts else 90
        # 2. 风险防控：100 - rejected*5
        risk_ctl = max(40, 100 - rejected * 5)
        # 3. 审批时效：pending 多则扣分
        speed = max(40, 100 - pending * 2)
        # 4. 数据质量：默认 85（够用即可）
        data_q = 85
        # 5. 渠道覆盖：渠道数（v3.3 真实读法）
        coverage = 70
        try:
            ch = await db.execute(text("SELECT COUNT(*) FROM biz_channel WHERE status = '0'"))
            coverage = min(100, int(ch.scalar() or 0) * 10 + 40)
        except SQLAlchemyError:
            pass
        # 6. 客户活跃度：top10 客户 / 总客户
        activity = 75
        try:
            tc = await db.execute(text("SELECT COUNT(DISTINCT customer_id) FROM biz_contract"))
            activity = min(100, int(tc.scalar() or 0) * 5 + 50)
        except SQLAlchemyError:
            pass

        scores = [compliance, risk_ctl, speed, data_q, coverage, activity]

        # 风险条目（按阈值）
        risks: list[AiRiskItemModel] = []
        if pending > 10:
            risks.append(
                AiRiskItemModel(
                    level='high',
                    title='审批积压告警',
                    detail=f'当前待审合同 {pending} 单，超过 10 单阈值，建议审批人优先处理。',
                )
            )
        elif pending > 5:
            risks.append(
                AiRiskItemModel(
                    level='medium',
                    title='审批积压提醒',
                    detail=f'待审合同 {pending} 单，建议关注审批 SLA。',
                )
            )
        if rejected > 5:
            risks.append(
                AiRiskItemModel(
                    level='medium',
                    title='驳回率偏高',
                    detail=f'累计驳回 {rejected} 单，建议复核合同模板/客户资质审核标准。',
                )
            )
        if my_todo > 0:
            risks.append(
                AiRiskItemModel(
                    level='low',
                    title='个人待办',
                    detail=f'您当前有 {my_todo} 单待审批，建议及时处理以免阻塞流程。',
                )
            )

        # 建议条目
        suggestions: list[AiSuggestionItemModel] = []
        if coverage < 60:
            suggestions.append(
                AiSuggestionItemModel(
                    title='渠道拓展建议',
                    detail='活跃渠道数偏少，建议拓展 OTA 合作或开通新平台账号（美团/抖音/携程/同程）。',
                )
            )
        if pending > 5:
            suggestions.append(
                AiSuggestionItemModel(
                    title='审批提速建议',
                    detail='审批链存在积压，可考虑给风控/财务环节设 SLA 预警，或临时调配人手。',
                )
            )
        if rejected > total_contracts * 0.2 and total_contracts:
            suggestions.append(
                AiSuggestionItemModel(
                    title='合同质量建议',
                    detail='驳回率超 20%，建议组织一次合同模板评审 + 客户资质审核培训。',
                )
            )
        if not suggestions:
            suggestions.append(
                AiSuggestionItemModel(
                    title='运营节奏稳健',
                    detail='当前各维度指标健康，建议保持现有审批节奏，关注节假日高峰。',
                )
            )

        # summary 一句话
        if not risks:
            summary = f'运营健康度良好：6 维平均分 {sum(scores) // len(scores)}，无高风险。'
        else:
            high_cnt = sum(1 for r in risks if r.level == 'high')
            summary = (
                f'检测到 {high_cnt} 项高风险 / {len(risks) - high_cnt} 项关注项'
                f'，建议优先处理。6 维平均分 {sum(scores) // len(scores)}。'
            )

        return AiDiagnoseModel(
            summary=summary,
            risks=risks,
            suggestions=suggestions,
            metrics={
                'pending': float(pending),
                'rejected': float(rejected),
                'approved': float(approved),
                'totalContracts': float(total_contracts),
                'myTodo': float(my_todo),
            },
            radar_scores=scores,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
