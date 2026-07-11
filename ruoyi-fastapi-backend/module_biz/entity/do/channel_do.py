"""渠道主表 ORM（数据库设计文档 §4.6 草拟）。

渠道分类严格遵循 sys_dict_data dict_type='channel_type' 已登记的 4 个 value：
- meituan: 美团到综
- douyin: 抖音生活服务
- ctrip: 携程商旅
- tongcheng: 同程旅行
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.mysql import DECIMAL, DOUBLE

from config.database import Base


class BizChannel(Base):
    """渠道主表 biz_channel"""

    __tablename__ = 'biz_channel'
    __table_args__ = {'comment': '渠道主表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='渠道ID')
    channel_code = Column(String(50), nullable=False, unique=True, comment='渠道编码 QD-NNN')
    channel_name = Column(String(100), nullable=False, comment='渠道名称')
    category = Column(String(20), nullable=False, comment='渠道分类：meituan/douyin/ctrip/tongcheng')
    contact_name = Column(String(50), nullable=True, comment='联系人')
    contact_phone = Column(String(20), nullable=True, comment='联系电话')
    contact_email = Column(String(100), nullable=True, comment='联系邮箱')
    platform_url = Column(String(255), nullable=True, comment='平台地址')
    account = Column(String(128), nullable=True, comment='登录账号（演示用）')
    password = Column(String(128), nullable=True, comment='登录密码（演示用，明文不加密）')
    commission_rate = Column(DECIMAL(5, 4), nullable=True, comment='佣金比例（0-1）')
    # v3.3 路线 C：地图定位字段
    province = Column(String(40), nullable=True, comment='省份（v3.3 路线 C 地图联动）')
    city = Column(String(40), nullable=True, comment='城市（v3.3 路线 C 地图联动）')
    lng = Column(DOUBLE, nullable=True, comment='经度（v3.3 路线 C）')
    lat = Column(DOUBLE, nullable=True, comment='纬度（v3.3 路线 C）')
    status = Column(Integer, nullable=False, default=1, comment='状态 0=停用 1=启用')
    sort_order = Column(Integer, nullable=False, default=0, comment='排序值，越大越靠前')
    description = Column(Text, nullable=True, comment='渠道说明')
    attachments = Column(JSON, nullable=True, comment='资质附件 [{name,url}]')
    contract_ids = Column(JSON, nullable=True, comment='关联合同ID列表 [id]（冗余便于展示）')
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(BigInteger, nullable=True, comment='创建人 sys_user.user_id')
    created_by_name = Column(String(64), nullable=True, comment='创建人姓名（冗余）')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
