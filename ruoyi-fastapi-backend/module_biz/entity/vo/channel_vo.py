"""渠道 Pydantic 模型（遵循 ADR D24：JSON 字段统一 camelCase）。"""
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


class ChannelQueryModel(_Base):
    """渠道查询条件"""

    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=200)
    keyword: str | None = Field(default=None, description='渠道编码/名称/联系人模糊')
    category: str | None = Field(default=None, description='meituan/douyin/ctrip/tongcheng')
    status: int | None = Field(default=None, description='0=停用 1=启用')


class ChannelCreateModel(_Base):
    """新建渠道请求体"""

    channel_code: str | None = Field(default=None, max_length=50, description='渠道编码 QD-NNN，留空自动生成')
    channel_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., description='meituan/douyin/ctrip/tongcheng')
    contact_name: str | None = Field(default=None, max_length=50)
    contact_phone: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(default=None, max_length=100)
    platform_url: str | None = Field(default=None, max_length=255)
    account: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, max_length=128)
    commission_rate: Decimal | None = Field(default=None, ge=0, le=1, description='0-1')
    sort_order: int = Field(default=0)
    description: str | None = None
    attachments: list[dict[str, Any]] | None = None
    remark: str | None = Field(default=None, max_length=500)


class ChannelUpdateModel(_Base):
    """编辑渠道请求体"""

    channel_name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None)
    contact_name: str | None = Field(default=None)
    contact_phone: str | None = Field(default=None)
    contact_email: str | None = Field(default=None)
    platform_url: str | None = Field(default=None)
    account: str | None = Field(default=None)
    password: str | None = Field(default=None)
    commission_rate: Decimal | None = Field(default=None, ge=0, le=1)
    sort_order: int | None = Field(default=None)
    description: str | None = None
    attachments: list[dict[str, Any]] | None = None
    status: int | None = Field(default=None)
    remark: str | None = Field(default=None)


class ChannelResponseModel(_Base):
    """渠道响应模型"""

    id: int
    channel_code: str
    channel_name: str
    category: str
    category_label: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    platform_url: str | None = None
    account: str | None = None
    commission_rate: Decimal | None = None
    sort_order: int = 0
    description: str | None = None
    attachments: list[dict[str, Any]] | None = None
    contract_ids: list[int] | None = None
    status: int
    created_by: int | None = None
    created_by_name: str | None = None
    create_time: datetime
    update_time: datetime | None = None
    remark: str | None = None


class ChannelCategoryOptionModel(_Base):
    """渠道分类下拉选项"""

    value: str
    label: str


class ChannelImportItemModel(_Base):
    """CSV 导入单行"""

    channel_code: str = Field(..., max_length=50)
    channel_name: str = Field(..., max_length=100)
    category: str
    contact_name: str | None = None
    contact_phone: str | None = None
    commission_rate: Decimal | None = None
    remark: str | None = None


class ChannelImportModel(_Base):
    """CSV 导入请求"""

    items: list[ChannelImportItemModel] = Field(..., min_length=1)
    skip_duplicates: bool = Field(default=True, description='遇到重复编码是否跳过')
