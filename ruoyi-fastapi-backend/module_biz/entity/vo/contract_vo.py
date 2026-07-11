"""合同 Pydantic 模型。

遵循 docs/04-开发/ARD/ADR-架构决策记录.md D24：API 字段命名一致性。
JSON 字段一律 camelCase，通过 Pydantic `alias_generator=to_camel` 自动序列化。
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ContractBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class ContractQueryModel(ContractBaseModel):
    """合同查询条件"""

    page_num: int = Field(default=1, ge=1, description='页码')
    page_size: int = Field(default=10, ge=1, le=200, description='每页条数')
    contract_no: str | None = Field(default=None, description='合同编号（模糊）')
    title: str | None = Field(default=None, description='合同名称（模糊）')
    contract_type: str | None = Field(default=None, description='payment / business')
    status: str | None = Field(default=None, description='draft/pending/approved/rejected')
    current_step: int | None = Field(default=None, ge=0, le=6, description='当前审批步骤')
    customer_id: int | None = Field(default=None, description='客户ID')
    begin_time: str | None = Field(default=None, description='创建开始时间 YYYY-MM-DD')
    end_time: str | None = Field(default=None, description='创建结束时间')
    keyword: str | None = Field(default=None, description='通用关键字（搜索合同编号/名称/客户/乙方）')


class ContractCreateModel(ContractBaseModel):
    """新建合同请求体"""

    contract_no: str = Field(..., min_length=1, max_length=50, description='合同编号（手动输入）')
    title: str = Field(..., min_length=1, max_length=200, description='合同名称')
    contract_type: str = Field(..., description='payment / business')
    party_a: str = Field(..., min_length=1, max_length=200, description='甲方（客户）')
    party_b: str = Field(..., min_length=1, max_length=200, description='乙方（本司）')
    amount: Decimal = Field(..., ge=0, description='合同金额')
    sign_date: date | None = Field(default=None, description='签订日期')
    department: str | None = Field(default=None, max_length=100, description='申请部门')
    business_type: str | None = Field(default=None, max_length=50, description='业务类型')
    customer_id: int | None = Field(default=None, description='客户ID')
    customer_name: str | None = Field(default=None, description='客户名称（冗余）')
    remark: str | None = Field(default=None, description='备注')
    attachments: list[dict[str, Any]] | None = Field(default=None, description='附件 [{name,url}]')


class ContractUpdateModel(ContractBaseModel):
    """编辑合同请求体"""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    contract_type: str | None = Field(default=None)
    party_a: str | None = Field(default=None)
    party_b: str | None = Field(default=None)
    amount: Decimal | None = Field(default=None, ge=0)
    sign_date: date | None = Field(default=None)
    department: str | None = Field(default=None)
    business_type: str | None = Field(default=None)
    customer_id: int | None = Field(default=None)
    customer_name: str | None = Field(default=None)
    remark: str | None = Field(default=None)
    attachments: list[dict[str, Any]] | None = Field(default=None)


class ContractResponseModel(ContractBaseModel):
    """合同响应模型（列表/详情共用）

    包含给前端的 *label 字段，由 service 层填充，避免前端再查字典。
    """

    id: int
    contract_no: str
    title: str
    contract_type: str
    contract_type_label: str | None = None
    party_a: str
    party_b: str
    amount: Decimal
    amount_in_words: str | None = None
    sign_date: date | None = None
    department: str | None = None
    business_type: str | None = None
    customer_id: int | None = None
    customer_name: str | None = None
    remark: str | None = None
    attachments: list[dict[str, Any]] | None = None
    status: str
    status_label: str | None = None
    current_step: int
    current_role: str | None = None
    current_role_label: str | None = None
    reject_count: int
    created_by: int
    created_by_name: str | None = None
    create_time: datetime
    update_time: datetime | None = None


class ContractCheckNoModel(ContractBaseModel):
    contract_no: str = Field(..., min_length=1, max_length=50)