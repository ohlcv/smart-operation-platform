"""仪表盘 Pydantic 模型。

读取已完成模块的 biz_contract / biz_customer / sys_user 等表，聚合出
页面所需的 KPI / 趋势 / 分布 / 排名 / 时间轴等数据。

返回结构遵循 ADR D24：JSON 字段一律 camelCase，Pydantic alias_generator=to_camel。
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DashboardBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class DashboardKpiModel(DashboardBaseModel):
    """仪表盘顶部 6 个 KPI 数字翻牌"""

    contract_total: int = Field(default=0, description='合同总数')
    contract_pending: int = Field(default=0, description='审批中合同数')
    contract_approved: int = Field(default=0, description='已通过合同数')
    contract_rejected: int = Field(default=0, description='已驳回合同数')
    contract_month_new: int = Field(default=0, description='本月新增合同数')
    contract_month_amount: Decimal = Field(default=Decimal('0.00'), description='本月合同总金额（元）')
    customer_total: int = Field(default=0, description='客户总数')
    channel_total: int = Field(default=0, description='渠道总数（D09 读取 channel 表，路线 A 表若不存在则 0）')
    invoice_pending: int = Field(default=0, description='待开发票数（D11 读取 invoice 表）')
    approval_pending: int = Field(default=0, description='待我审批数')


class Trend7dItemModel(DashboardBaseModel):
    """7 日趋势折线图一项"""

    day: date = Field(..., alias='date', description='日期 YYYY-MM-DD，前端 JSON 字段为 date')
    new_contracts: int = Field(default=0, description='当日新增合同数')
    approved_contracts: int = Field(default=0, description='当日通过合同数')

    model_config = ConfigDict(
        alias_generator=None,  # 显式禁用 camelCase，对带 alias 的字段不再二次转换
        from_attributes=True,
        populate_by_name=True,
    )


class RevenueTrendItemModel(DashboardBaseModel):
    """营收月度趋势面积图一项（YTD）"""

    month: date = Field(..., description='月份 1 号 YYYY-MM-DD，前端按 .slice(5) 取 MM')
    revenue: Decimal = Field(default=Decimal('0.00'), description='当月营收总和（元），全业务线合并')


class StatusDistributionItemModel(DashboardBaseModel):
    """合同状态分布饼图一项"""

    status: str = Field(..., description='draft/pending/approved/rejected')
    label: str = Field(..., description='状态中文名')
    count: int = Field(default=0, description='该状态合同数')


class TopCustomerItemModel(DashboardBaseModel):
    """Top10 客户（按合同总金额）一项"""

    customer_id: int | None = Field(default=None, description='客户ID')
    customer_name: str = Field(default='未指定客户', description='客户名称')
    contract_count: int = Field(default=0, description='该客户合同数')
    total_amount: Decimal = Field(default=Decimal('0.00'), description='该客户合同总金额')


class RecentApprovalItemModel(DashboardBaseModel):
    """最近审批流时间轴一项"""

    contract_id: int = Field(..., description='合同ID')
    contract_no: str = Field(..., description='合同编号')
    title: str | None = Field(default=None, description='合同名称')
    step: int = Field(..., description='当前审批步骤 0-6')
    step_label: str = Field(default='', description='当前审批步骤的中文名（业务经办/复核/...）')
    approver_name: str | None = Field(default=None, description='当前待审人姓名')
    updated_at: str = Field(default='', description='最近更新时间 YYYY-MM-DD HH:mm:ss')


class ChannelLocationItemModel(DashboardBaseModel):
    """中国地图渠道分布一项（路线 A 完成 channel 表后才有值）"""

    channel_id: int | None = Field(default=None, description='渠道ID')
    channel_name: str = Field(default='', description='渠道名称')
    lng: float = Field(default=0.0, description='经度')
    lat: float = Field(default=0.0, description='纬度')
    contract_count: int = Field(default=0, description='该渠道关联合同数')
    city: str = Field(default='', description='所在城市')


class DashboardOverviewModel(DashboardBaseModel):
    """仪表盘 GET /biz/dashboard/overview 完整返回结构"""

    kpi: DashboardKpiModel = Field(default_factory=DashboardKpiModel, description='顶部 6 个 KPI')
    trend_7d: list[Trend7dItemModel] = Field(
        default_factory=list,
        alias='trend7d',  # 显式 alias，避免 to_camel 把 "7d" 转成 "7D"
        serialization_alias='trend7d',
        description='7 日合同趋势',
    )
    revenue_trend: list[RevenueTrendItemModel] = Field(
        default_factory=list,
        description='营收月度趋势（YTD，1 月至当前月，未来月份补 0）',
    )
    status_distribution: list[StatusDistributionItemModel] = Field(
        default_factory=list, description='合同状态分布'
    )
    top_customers: list[TopCustomerItemModel] = Field(
        default_factory=list, description='Top10 客户（按合同金额）'
    )
    recent_approvals: list[RecentApprovalItemModel] = Field(
        default_factory=list, description='最近审批动态时间轴'
    )
    channel_locations: list[ChannelLocationItemModel] = Field(
        default_factory=list, description='渠道全国地图分布（路线 A 未完成时为空）'
    )
    generated_at: str = Field(default='', description='数据生成时间 YYYY-MM-DD HH:mm:ss')
    province: str = Field(default='', description='当前查询的省份（全国为空）')


class AiRiskItemModel(DashboardBaseModel):
    """AI 智能大脑 - 风险诊断条目"""

    level: str = Field(..., description='风险等级 high/medium/low')
    title: str = Field(..., description='风险标题')
    detail: str = Field(..., description='风险详细说明')


class AiSuggestionItemModel(DashboardBaseModel):
    """AI 智能大脑 - 资金/运营建议条目"""

    title: str = Field(..., description='建议标题')
    detail: str = Field(..., description='建议详细说明')


class AiDiagnoseModel(DashboardBaseModel):
    """AI 智能大脑 - 风险雷达 + 诊断结论 + 资金建议

    GET /biz/dashboard/ai-diagnose 返回结构（demo1 同款）
    """

    summary: str = Field(default='', description='一段话总结当前运营健康度')
    risks: list[AiRiskItemModel] = Field(default_factory=list, description='风险条目')
    suggestions: list[AiSuggestionItemModel] = Field(default_factory=list, description='运营/资金建议条目')
    metrics: dict[str, float] = Field(default_factory=dict, description='雷达图 6 维原始数值')
    radar_scores: list[int] = Field(default_factory=list, description='雷达图 6 维分数 0-100')
    generated_at: str = Field(default='', description='诊断生成时间')


# 状态码到中文的映射（仪表盘页面饼图直接拿 label 渲染）
STATUS_LABEL_MAP: dict[str, str] = {
    'draft': '草稿',
    'pending': '审批中',
    'approved': '已通过',
    'rejected': '已驳回',
}

# 7 级审批链步骤中文名（D01 决策）
STEP_LABEL_MAP: dict[int, str] = {
    0: '业务经办',
    1: '业务复核',
    2: '风控审核',
    3: '财务经办',
    4: '财务复核',
    5: '供管公司负责人',
    6: '投资公司负责人',
}
