"""审批记录 ORM（数据库设计文档 §4.2）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text

from config.database import Base


class BizApproval(Base):
    """审批记录表 biz_approval"""

    __tablename__ = 'biz_approval'
    __table_args__ = {'comment': '审批记录表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='审批记录ID')
    contract_id = Column(BigInteger, nullable=False, comment='关联合同ID biz_contract.id')
    approver_id = Column(BigInteger, nullable=True, comment='审批人 sys_user.user_id')
    approver_name = Column(String(50), nullable=True, comment='审批人姓名（冗余）')
    step = Column(Integer, nullable=False, comment='审批步骤 0-6')
    approver_role = Column(String(50), nullable=False, comment='审批时角色标识')
    action = Column(String(20), nullable=False, comment='approve=通过 / reject=驳回')
    comment = Column(Text, nullable=True, comment='审批意见')
    reject_reason = Column(Text, nullable=True, comment='驳回原因')
    signature_snapshot = Column(Text, nullable=True, comment='签名快照 base64 data URI')
    approval_ip = Column(String(50), nullable=True, comment='审批操作 IP')
    approval_time = Column(DateTime, nullable=False, default=datetime.now, comment='审批时间')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='记录创建时间')

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}