"""客户 Pydantic 模型（遵循 ADR D24：JSON 字段统一 camelCase）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Base(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class CustomerQueryModel(_Base):
    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=200)
    keyword: str | None = Field(default=None, description='客户名称/联系人模糊')
    customer_type: str | None = Field(default=None)
    level: str | None = Field(default=None)
    status: int | None = Field(default=None, description='0=停用 1=启用')


class CustomerCreateModel(_Base):
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_type: str | None = Field(default=None)
    contact_name: str | None = Field(default=None)
    contact_phone: str | None = Field(default=None)
    contact_email: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=300)
    business_license: str | None = Field(default=None)
    tax_no: str | None = Field(default=None)
    qualification_files: list[dict[str, Any]] | None = Field(default=None)
    level: str | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    status: int = Field(default=1, description='0=停用 1=启用')
    remark: str | None = Field(default=None, max_length=500)
    customer_code: str | None = Field(default=None, max_length=50, description='业务编号 KH-NNN，留空由后端自动生成')


class CustomerUpdateModel(_Base):
    customer_name: str | None = Field(default=None)
    customer_type: str | None = Field(default=None)
    contact_name: str | None = Field(default=None)
    contact_phone: str | None = Field(default=None)
    contact_email: str | None = Field(default=None)
    address: str | None = Field(default=None)
    business_license: str | None = Field(default=None)
    tax_no: str | None = Field(default=None)
    qualification_files: list[dict[str, Any]] | None = Field(default=None)
    level: str | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    status: int | None = Field(default=None)
    remark: str | None = Field(default=None)


class CustomerResponseModel(_Base):
    id: int
    customer_code: str | None = None
    customer_name: str
    customer_type: str | None = None
    customer_type_label: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    address: str | None = None
    business_license: str | None = None
    tax_no: str | None = None
    qualification_files: list[dict[str, Any]] | None = None
    level: str | None = None
    tags: list[str] | None = None
    status: int
    create_time: datetime
    update_time: datetime | None = None
    remark: str | None = None