"""审批 Pydantic 模型。
文档依据：
- API 设计文档 §六 审批中心（6.1 待我审批 / 6.2 审批通过 / 6.3 审批驳回 / 6.4 审批历史）
- 权限模型设计.md §三（role_sort 匹配）
- ADR D02 / D24（camelCase + role_sort 规范）
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApprovalBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class PendingQueryModel(ApprovalBaseModel):
    """待我审批 / 我已审批查询条件"""

    page_num: int = Field(default=1, ge=1, description='页码')
    page_size: int = Field(default=10, ge=1, le=200, description='每页条数')
    contract_no: str | None = Field(default=None, description='合同编号（模糊）')
    title: str | None = Field(default=None, description='合同名称（模糊）')
    contract_type: str | None = Field(default=None, description='payment / business')
    current_step: int | None = Field(default=None, ge=1, le=6, description='当前审批步骤（1-6，待我审批时一般是 current_user 当前 step）')
    begin_time: str | None = Field(default=None, description='创建开始时间 YYYY-MM-DD')
    end_time: str | None = Field(default=None, description='创建结束时间')
    keyword: str | None = Field(default=None, description='通用关键字（合同编号/名称/客户/乙方）')
    # tab 区分「待我审批」(pending) / 「我已审批」(processed)
    scope: str = Field(default='pending', description='pending=待我审批 / processed=我已审批 / submitted=我提交的')


class ApprovalActionModel(ApprovalBaseModel):
    """审批通过 / 驳回请求体"""

    action: str = Field(..., description='approve / reject')
    comment: str | None = Field(default=None, max_length=1000, description='审批意见（通过时可选，驳回时建议填）')
    reject_reason: str | None = Field(default=None, max_length=1000, description='驳回原因（reject 时必填）')


class ApprovalHistoryItemModel(ApprovalBaseModel):
    """审批历史单条记录"""

    id: int
    contract_id: int
    contract_no: str | None = None
    contract_title: str | None = None
    approver_id: int | None = None
    approver_name: str | None = None
    step: int
    step_label: str | None = None
    approver_role: str
    action: str
    action_label: str | None = None
    comment: str | None = None
    reject_reason: str | None = None
    signature_snapshot: str | None = None
    approval_time: datetime


class PendingContractItemModel(ApprovalBaseModel):
    """待我审批列表单条合同记录（复用 contract 字段 + 当前角色标识）"""

    id: int
    contract_no: str
    title: str
    contract_type: str
    contract_type_label: str | None = None
    party_a: str
    party_b: str
    amount: float
    customer_name: str | None = None
    status: str
    status_label: str | None = None
    current_step: int
    current_role: str | None = None
    current_role_label: str | None = None
    reject_count: int
    created_by: int
    created_by_name: str | None = None
    create_time: datetime
    # 审批权限判断结果（前端展示按钮用）
    can_approve: bool = False
    # 当前用户若已审批过：是否「已通过」/「已驳回」
    my_action: str | None = None
    my_action_label: str | None = None
    my_comment: str | None = None
    my_approval_time: datetime | None = None