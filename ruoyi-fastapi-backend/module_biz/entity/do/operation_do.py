"""经营数据 ORM（ADR D05：当前阶段手工录入，不与合同自动汇总）。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, Numeric, String, Text

from config.database import Base


class BizOperation(Base):
    """经营数据表 biz_operation"""

    __tablename__ = 'biz_operation'
    __table_args__ = {'comment': '经营数据表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='记录ID')
    period = Column(String(20), nullable=False, comment='周期 key，如 2026-07 / 2026-Q3 / 2026')
    period_type = Column(String(20), nullable=False, comment='周期类型 month/quarter/year')
    business_line = Column(String(20), nullable=True, comment='业务线 scenic/digital/logistics')
    revenue = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'), comment='营收')
    cost = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'), comment='成本')
    gross_profit = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'), comment='毛利（实时计算冗余）')
    customer_count = Column(Integer, nullable=False, default=0, comment='客户数')
    contract_count = Column(Integer, nullable=False, default=0, comment='合同数')
    avg_order_value = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'), comment='客单价')
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(BigInteger, nullable=True, comment='创建人 sys_user.user_id')
    created_by_name = Column(String(64), nullable=True, comment='创建人姓名（冗余）')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}