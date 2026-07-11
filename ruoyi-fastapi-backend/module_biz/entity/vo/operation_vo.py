"""经营数据 Pydantic 模型（遵循 ADR D24）。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Base(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class OperationQueryModel(_Base):
    """经营数据查询"""

    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=200)
    period_type: str | None = Field(default=None, description='month/quarter/year')
    business_line: str | None = Field(default=None)
    period: str | None = Field(default=None, description='精确匹配周期')


class OperationCreateModel(_Base):
    """新建经营数据"""

    period: str = Field(..., min_length=4, max_length=20, description='如 2026-07')
    period_type: str = Field(..., description='month/quarter/year')
    business_line: str | None = Field(default=None)
    revenue: Decimal = Field(default=Decimal('0.00'), ge=0)
    cost: Decimal = Field(default=Decimal('0.00'), ge=0)
    customer_count: int = Field(default=0, ge=0)
    contract_count: int = Field(default=0, ge=0)
    remark: str | None = Field(default=None, max_length=500)


class OperationUpdateModel(_Base):
    """编辑经营数据"""

    revenue: Decimal | None = Field(default=None, ge=0)
    cost: Decimal | None = Field(default=None, ge=0)
    customer_count: int | None = Field(default=None, ge=0)
    contract_count: int | None = Field(default=None, ge=0)
    remark: str | None = Field(default=None)


class OperationResponseModel(_Base):
    """经营数据响应"""

    id: int
    period: str
    period_type: str
    period_type_label: str | None = None
    business_line: str | None = None
    business_line_label: str | None = None
    revenue: Decimal
    cost: Decimal
    gross_profit: Decimal
    customer_count: int
    contract_count: int
    avg_order_value: Decimal
    remark: str | None = None
    created_by: int | None = None
    created_by_name: str | None = None
    create_time: datetime
    update_time: datetime | None = None


class OperationComparisonQueryModel(_Base):
    """同比环比查询"""

    period: str = Field(..., min_length=4, max_length=20, description='如 2026-07')
    business_line: str | None = None


class OperationComparisonItemModel(_Base):
    """对比项"""

    metric: str
    label: str
    current: Decimal
    previous: Decimal
    yoy_change: Decimal  # 同比变化（绝对值）
    yoy_rate: float      # 同比变化率（百分比）
    mom_change: Decimal  # 环比变化
    mom_rate: float


class OperationComparisonResponseModel(_Base):
    """同比环比响应"""

    period: str
    period_type: str
    business_line: str | None = None
    items: list[OperationComparisonItemModel]


class OperationTypeOptionModel(_Base):
    """下拉选项"""

    value: str
    label: str