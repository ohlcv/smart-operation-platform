"""业务枚举定义

按 docs/04-开发/ARD/ADR-架构决策记录.md v1.1 的核心决策实现：
- D01：7 级业务审批链（business_handler → ... → invest_director）
- D02：admin 为隐藏超管，role_sort=0 不在审批链中
- D03：状态语义 draft / pending / approved / rejected
- D06：party_a=甲方(客户) party_b=乙方(本司)
"""
from __future__ import annotations

from enum import Enum


class ApprovalStepEnum(int, Enum):
    """7 级业务审批链步骤（0-6）。role_sort 与本枚举一一对应，便于跨表定位当前审批角色。

    流转规则：提交时 → step 0；Step 0 审批通过 → step 1；以此类推；step 6 通过 → approved。
    驳回时 → status=rejected；重新提交 → status=pending, step 重置为 0，保留历史。
    """

    STEP_0_BUSINESS_HANDLER = 0   # 业务经办提交（提交即视为完成 Step 0）
    STEP_1_BUSINESS_REVIEWER = 1  # 业务复核
    STEP_2_RISK_AUDITOR = 2       # 风控审核
    STEP_3_FINANCE_HANDLER = 3    # 财务经办
    STEP_4_FINANCE_REVIEWER = 4   # 财务复核
    STEP_5_SCM_DIRECTOR = 5       # 供管公司负责人
    STEP_6_INVEST_DIRECTOR = 6    # 投资公司负责人（终审）

    @classmethod
    def role_key(cls, step: int) -> str | None:
        """根据 step 返回对应审批角色 role_key。"""
        mapping = {
            cls.STEP_0_BUSINESS_HANDLER.value: 'business_handler',
            cls.STEP_1_BUSINESS_REVIEWER.value: 'business_reviewer',
            cls.STEP_2_RISK_AUDITOR.value: 'risk_auditor',
            cls.STEP_3_FINANCE_HANDLER.value: 'finance_handler',
            cls.STEP_4_FINANCE_REVIEWER.value: 'finance_reviewer',
            cls.STEP_5_SCM_DIRECTOR.value: 'scm_director',
            cls.STEP_6_INVEST_DIRECTOR.value: 'invest_director',
        }
        return mapping.get(step)

    @classmethod
    def label(cls, step: int) -> str:
        """中文标签，供前端 current_role_label 使用。"""
        mapping = {
            cls.STEP_0_BUSINESS_HANDLER.value: '业务经办',
            cls.STEP_1_BUSINESS_REVIEWER.value: '业务复核',
            cls.STEP_2_RISK_AUDITOR.value: '风控审核',
            cls.STEP_3_FINANCE_HANDLER.value: '财务经办',
            cls.STEP_4_FINANCE_REVIEWER.value: '财务复核',
            cls.STEP_5_SCM_DIRECTOR.value: '供管公司负责人',
            cls.STEP_6_INVEST_DIRECTOR.value: '投资公司负责人',
        }
        return mapping.get(step, '')


class ContractStatusEnum(str, Enum):
    """合同状态机。语义严格遵循 ADR D03。"""

    DRAFT = 'draft'           # 草稿（未提交，可编辑可删除）
    PENDING = 'pending'       # 审批中（不可编辑，超管可介入）
    APPROVED = 'approved'     # 已通过（终态）
    REJECTED = 'rejected'     # 已驳回待修改（可重新提交，保留审批历史）

    @classmethod
    def label(cls, status: str) -> str:
        mapping = {
            cls.DRAFT.value: '草稿',
            cls.PENDING.value: '审批中',
            cls.APPROVED.value: '已通过',
            cls.REJECTED.value: '已驳回待修改',
        }
        return mapping.get(status, status)


class ContractTypeEnum(str, Enum):
    """合同类型（参考设计文档 §5.2 sys_dict.contract_type）。"""

    PAYMENT = 'payment'    # 业务付款审批单
    BUSINESS = 'business'  # 业务审批单

    @classmethod
    def label(cls, t: str) -> str:
        return {'payment': '业务付款审批单', 'business': '业务审批单'}.get(t, t)


class CustomerTypeEnum(str, Enum):
    """客户类型（参考设计文档 §4.3）。"""

    SCENIC = 'scenic'    # 景区
    HOTEL = 'hotel'      # 酒店
    AGENCY = 'agency'    # 旅行社
    PUBLISH = 'publish'  # 出版社

    @classmethod
    def label(cls, t: str) -> str:
        return {
            'scenic': '景区',
            'hotel': '酒店',
            'agency': '旅行社',
            'publish': '出版社',
        }.get(t, t)


class ApprovalActionEnum(str, Enum):
    """审批动作（一期仅 approve / reject，参考设计文档 §4.2）。"""

    APPROVE = 'approve'
    REJECT = 'reject'