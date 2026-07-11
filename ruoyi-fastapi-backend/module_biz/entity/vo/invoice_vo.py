"""发票 Pydantic 模型（遵循 ADR D24：JSON 字段统一 camelCase）。"""
from __future__ import annotations

from datetime import date, datetime
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


class InvoiceQueryModel(_Base):
    """发票查询条件"""

    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=200)
    keyword: str | None = Field(default=None, description='发票号/合同号/购方名称模糊')
    status: str | None = Field(default=None, description='pending/issued/void')
    invoice_type: str | None = Field(default=None, description='specialized/general/electronic')
    contract_id: int | None = Field(default=None)
    begin_date: str | None = Field(default=None, description='开票开始日期 YYYY-MM-DD')
    end_date: str | None = Field(default=None)


class InvoiceCreateModel(_Base):
    """新建发票"""

    invoice_no: str | None = Field(default=None, max_length=50, description='发票号，留空自动生成 FP-NNN')
    contract_id: int = Field(..., description='关联合同ID')
    contract_no: str | None = Field(default=None, max_length=50)
    invoice_type: str = Field(..., description='specialized/general/electronic')
    amount: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal('0.1300'), ge=0, le=1, description='默认 13%（一般纳税人）')
    party_name: str = Field(..., min_length=1, max_length=200)
    party_tax_no: str | None = Field(default=None, max_length=50)
    apply_date: date | None = Field(default=None)
    remark: str | None = Field(default=None, max_length=500)


class InvoiceUpdateModel(_Base):
    """编辑发票请求（仅 pending 状态可编辑）"""

    invoice_no: str | None = Field(default=None, max_length=50)
    invoice_type: str | None = Field(default=None)
    amount: Decimal | None = Field(default=None, ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=1)
    party_name: str | None = Field(default=None)
    party_tax_no: str | None = Field(default=None)
    apply_date: date | None = Field(default=None)
    issue_date: date | None = Field(default=None)
    remark: str | None = Field(default=None)


class InvoiceResponseModel(_Base):
    """发票响应模型"""

    id: int
    invoice_no: str
    contract_id: int
    contract_no: str | None = None
    invoice_type: str
    invoice_type_label: str | None = None
    amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    party_name: str
    party_tax_no: str | None = None
    status: str
    status_label: str | None = None
    apply_date: date | None = None
    issue_date: date | None = None
    void_reason: str | None = None
    remark: str | None = None
    created_by: int | None = None
    created_by_name: str | None = None
    create_time: datetime
    update_time: datetime | None = None


class InvoiceVoidModel(_Base):
    """作废发票请求"""

    reason: str = Field(..., min_length=1, max_length=500, description='作废原因必填')


class InvoiceStatusOptionModel(_Base):
    """发票状态/类型下拉"""

    value: str
    label: str
