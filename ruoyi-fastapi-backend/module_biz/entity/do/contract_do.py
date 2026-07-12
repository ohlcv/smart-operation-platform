"""合同主表 ORM（数据库设计文档 §4.1）。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, BigInteger, Column, Date, DateTime, Integer, Numeric, String, Text

from config.database import Base


class BizContract(Base):
    """合同主表 biz_contract"""

    __tablename__ = 'biz_contract'
    __table_args__ = {'comment': '合同主表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='合同ID')
    contract_no = Column(String(50), nullable=False, unique=True, comment='合同编号（手动输入，唯一）')
    title = Column(String(200), nullable=False, comment='合同名称')
    contract_type = Column(String(20), nullable=False, comment='payment / business')
    party_a = Column(String(200), nullable=False, comment='甲方（客户）')
    party_b = Column(String(200), nullable=False, comment='乙方（本司）')
    amount = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'), comment='合同金额（元）')
    amount_in_words = Column(String(100), nullable=True, comment='金额大写')
    sign_date = Column(Date, nullable=True, comment='签订日期')
    department = Column(String(100), nullable=True, comment='申请部门')
    business_type = Column(String(50), nullable=True, comment='业务类型')
    customer_id = Column(BigInteger, nullable=True, comment='关联客户ID biz_customer.id')
    customer_name = Column(String(200), nullable=True, comment='冗余客户名称（便于列表展示）')
    province = Column(String(40), nullable=True, comment='客户省份（v3.3 路线 C 省份联动，冗余便于聚合查询）')
    remark = Column(Text, nullable=True, comment='合同备注')
    attachments = Column(JSON, nullable=True, comment='附件列表 [{name,url}]')
    status = Column(String(20), nullable=False, default='draft', comment='draft/pending/approved/rejected')
    current_step = Column(Integer, nullable=False, default=0, comment='当前审批步骤 0-6')
    current_role = Column(String(50), nullable=True, comment='当前待审角色 role_key（冗余便于展示）')
    reject_count = Column(Integer, nullable=False, default=0, comment='累计驳回次数')
    created_by = Column(BigInteger, nullable=False, comment='创建人 sys_user.user_id')
    created_by_name = Column(String(50), nullable=True, comment='创建人姓名（冗余）')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}