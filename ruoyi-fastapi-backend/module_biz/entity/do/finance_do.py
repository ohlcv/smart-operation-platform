"""财务台账 ORM（ADR D10：手工 CSV 导入，不直连银行 API）。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, BigInteger, Column, Date, DateTime, Integer, Numeric, String, Text

from config.database import Base


class BizFinanceEntry(Base):
    """财务流水台账表 biz_finance_entry"""

    __tablename__ = 'biz_finance_entry'
    __table_args__ = {'comment': '财务流水台账'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='流水ID')
    entry_no = Column(String(50), nullable=False, unique=True, comment='流水号 FN-NNN')
    entry_type = Column(String(20), nullable=False, comment='类型：payable/receivable')
    invoice_id = Column(BigInteger, nullable=True, comment='关联发票ID biz_invoice.id')
    invoice_no = Column(String(50), nullable=True, comment='冗余发票号')
    contract_id = Column(BigInteger, nullable=True, comment='关联合同ID biz_contract.id')
    contract_no = Column(String(50), nullable=True, comment='冗余合同号')
    party_name = Column(String(200), nullable=True, comment='对手方名称')
    amount = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'), comment='金额')
    account = Column(String(50), nullable=True, comment='银行账号')
    account_name = Column(String(100), nullable=True, comment='账户名')
    bank_name = Column(String(100), nullable=True, comment='开户行')
    transaction_date = Column(Date, nullable=True, comment='交易日期')
    cleared = Column(Integer, nullable=False, default=0, comment='是否已对账 0=否 1=是')
    cleared_time = Column(DateTime, nullable=True, comment='对账时间')
    direction = Column(String(10), nullable=False, default='out', comment='出/入账方向 out=出 in=入')
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(BigInteger, nullable=True, comment='创建人 sys_user.user_id')
    created_by_name = Column(String(64), nullable=True, comment='创建人姓名（冗余）')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class BizBankStatement(Base):
    """银行对账单导入表"""

    __tablename__ = 'biz_bank_statement'
    __table_args__ = {'comment': '银行对账单导入'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True)
    batch_no = Column(String(50), nullable=False, comment='导入批次号')
    transaction_date = Column(Date, nullable=False, comment='交易日期')
    account = Column(String(50), nullable=False, comment='银行账号')
    amount = Column(Numeric(18, 2), nullable=False, comment='金额')
    direction = Column(String(10), nullable=False, default='in', comment='in=收入/out=支出')
    counterparty = Column(String(100), nullable=True, comment='交易对手')
    counterparty_account = Column(String(50), nullable=True, comment='对手账号')
    summary = Column(String(200), nullable=True, comment='摘要')
    matched = Column(Integer, nullable=False, default=0, comment='是否已匹配 0=否 1=是')
    matched_entry_id = Column(BigInteger, nullable=True, comment='匹配的财务流水ID')
    import_time = Column(DateTime, nullable=False, default=datetime.now, comment='导入时间')
    imported_by = Column(BigInteger, nullable=True, comment='导入人 sys_user.user_id')

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
