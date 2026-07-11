"""客户档案 ORM（数据库设计文档 §4.3）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, String
from sqlalchemy.dialects.mysql import TINYINT

from config.database import Base


class BizCustomer(Base):
    """客户档案表 biz_customer

    主键统一为 id（与 RuoYi 原生 sys_user.user_id 命名不一致，是有意为之的差异化设计，
    参考 docs/04-开发/开发进度台账.md §2.1）。
    """

    __tablename__ = 'biz_customer'
    __table_args__ = {'comment': '客户档案表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='客户ID')
    customer_code = Column(String(50), nullable=True, unique=True, comment='业务编号 KH-NNN，customer_code 唯一键')
    customer_name = Column(String(200), nullable=False, comment='客户名称（公司全称）')
    customer_type = Column(String(20), nullable=True, comment='客户类型：scenic/hotel/agency/publish')
    contact_name = Column(String(50), nullable=True, comment='联系人')
    contact_phone = Column(String(20), nullable=True, comment='联系电话')
    contact_email = Column(String(100), nullable=True, comment='邮箱')
    address = Column(String(300), nullable=True, comment='地址')
    business_license = Column(String(200), nullable=True, comment='营业执照编号')
    tax_no = Column(String(50), nullable=True, comment='纳税人识别号')
    qualification_files = Column(JSON, nullable=True, comment='资质文件列表 [{name,url}]')
    level = Column(String(10), nullable=True, comment='客户等级 A/B/C')
    tags = Column(JSON, nullable=True, comment='标签 ["景区","文旅"]')
    status = Column(TINYINT(4), nullable=False, default=1, comment='状态 0=停用 1=启用')
    created_by = Column(BigInteger, nullable=True, comment='创建人 sys_user.user_id')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')
    remark = Column(String(500), nullable=True, comment='备注')

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}