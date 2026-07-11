"""财务 Pydantic 模型（遵循 ADR D24）。"""
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


class FinanceQueryModel(_Base):
    """财务流水查询"""

    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=200)
    keyword: str | None = Field(default=None, description='流水号/发票号/合同号/对手方模糊')
    entry_type: str | None = Field(default=None, description='payable/receivable')
    cleared: int | None = Field(default=None, description='0=未对账 1=已对账')
    invoice_id: int | None = Field(default=None)
    begin_date: str | None = Field(default=None)
    end_date: str | None = Field(default=None)


class FinanceCreateModel(_Base):
    """新建财务流水"""

    entry_no: str | None = Field(default=None, max_length=50, description='流水号，留空自动生成 FN-NNN')
    entry_type: str = Field(..., description='payable/receivable')
    direction: str = Field(default='out', description='out/in')
    invoice_id: int | None = Field(default=None)
    invoice_no: str | None = Field(default=None, max_length=50)
    contract_id: int | None = Field(default=None)
    contract_no: str | None = Field(default=None, max_length=50)
    party_name: str | None = Field(default=None, max_length=200)
    amount: Decimal = Field(..., ge=0)
    account: str | None = Field(default=None, max_length=50)
    account_name: str | None = Field(default=None, max_length=100)
    bank_name: str | None = Field(default=None, max_length=100)
    transaction_date: date | None = Field(default=None)
    remark: str | None = Field(default=None, max_length=500)


class FinanceUpdateModel(_Base):
    """编辑财务流水"""

    party_name: str | None = Field(default=None, max_length=200)
    amount: Decimal | None = Field(default=None, ge=0)
    account: str | None = Field(default=None)
    account_name: str | None = Field(default=None)
    bank_name: str | None = Field(default=None)
    transaction_date: date | None = Field(default=None)
    remark: str | None = Field(default=None)


class FinanceResponseModel(_Base):
    """财务流水响应"""

    id: int
    entry_no: str
    entry_type: str
    entry_type_label: str | None = None
    direction: str
    direction_label: str | None = None
    invoice_id: int | None = None
    invoice_no: str | None = None
    contract_id: int | None = None
    contract_no: str | None = None
    party_name: str | None = None
    amount: Decimal
    account: str | None = None
    account_name: str | None = None
    bank_name: str | None = None
    transaction_date: date | None = None
    cleared: int
    cleared_time: datetime | None = None
    remark: str | None = None
    created_by: int | None = None
    created_by_name: str | None = None
    create_time: datetime
    update_time: datetime | None = None


class FinanceClearModel(_Base):
    """标记对账"""

    entry_id: int = Field(..., description='财务流水ID')


class BankStatementImportItem(_Base):
    """银行对账单导入一行"""

    transaction_date: date
    account: str = Field(..., max_length=50)
    amount: Decimal = Field(..., ge=0)
    direction: str = Field(default='in')
    counterparty: str | None = Field(default=None, max_length=100)
    counterparty_account: str | None = Field(default=None, max_length=50)
    summary: str | None = Field(default=None, max_length=200)


class BankStatementImportModel(_Base):
    """银行对账单导入请求"""

    items: list[BankStatementImportItem] = Field(..., min_length=1)


class FinanceSummaryResponseModel(_Base):
    """财务汇总（按月）"""

    period: str
    receivable_total: Decimal
    payable_total: Decimal
    cleared_total: Decimal
    uncleared_total: Decimal


class FinanceTypeOptionModel(_Base):
    """类型/方向下拉"""

    value: str
    label: str