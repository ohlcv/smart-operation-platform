"""发票主表 ORM（数据库设计文档 §4.7 草拟）。

ADR D11：台账管理，不做真实开票对接。
1:1 关联合同（contract_id + invoice_no 唯一）。
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, BigInteger, Column, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.mysql import DECIMAL

from config.database import Base


class BizInvoice(Base):
    """发票主表 biz_invoice"""

    __tablename__ = 'biz_invoice'
    __table_args__ = {'comment': '发票主表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='发票ID')
    invoice_no = Column(String(50), nullable=False, unique=True, comment='发票号（唯一）')
    contract_id = Column(BigInteger, nullable=False, comment='关联合同ID biz_contract.id')
    contract_no = Column(String(50), nullable=True, comment='冗余合同编号（便于展示）')
    invoice_type = Column(String(20), nullable=False, comment='发票类型：specialized=增值税专用 / general=普通 / electronic=电子')
    amount = Column(DECIMAL(18, 2), nullable=False, default=Decimal('0.00'), comment='开票金额（含税）')
    tax_rate = Column(DECIMAL(5, 4), nullable=False, default=Decimal('0.0000'), comment='税率（0-1）')
    tax_amount = Column(DECIMAL(18, 2), nullable=False, default=Decimal('0.00'), comment='税额')
    party_name = Column(String(200), nullable=False, comment='购方名称（抬头）')
    party_tax_no = Column(String(50), nullable=True, comment='购方税号')
    status = Column(String(20), nullable=False, default='pending', comment='状态：pending/issued/void')
    apply_date = Column(Date, nullable=True, comment='申请日期')
    issue_date = Column(Date, nullable=True, comment='开票日期')
    void_reason = Column(String(500), nullable=True, comment='作废原因')
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(BigInteger, nullable=True, comment='创建人 sys_user.user_id')
    created_by_name = Column(String(64), nullable=True, comment='创建人姓名（冗余）')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
