"""add missing tables：gen_table / gen_table_column / ai_models / ai_chat_config

Revision ID: 0003_add_missing_tables
Revises: 0002_seed_all
Create Date: 2026-07-12 23:40:00.000000

说明：
  0001_baseline_all 只建了 sys_* + biz_* 主线表，遗漏了"代码生成器"和"AI 模型"模块的表。
  访问"代码生成"菜单会触发 SELECT gen_table，导致 1146 表不存在。
  本迁移补齐以下 4 张表，结构与 ruoyi-fastapi.sql 保持一致（同时兼容 PG）。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


def _mysql_table_kwargs(bind) -> dict:
    """MySQL 走 ENGINE/CHARSET/COLLATE，PG 走空 dict。"""
    if bind is not None and getattr(bind.dialect, 'name', '') == 'mysql':
        return {
            'mysql_engine': 'InnoDB',
            'mysql_default_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci',
        }
    return {}


revision = '0003_add_missing_tables'
down_revision = '0002_seed_all'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """补建代码生成器 + AI 模型 4 张表"""
    bind = op.get_bind()

    # ============== 代码生成业务表 gen_table ==============
    op.create_table(
        'gen_table',
        sa.Column('table_id', sa.BigInteger, primary_key=True, autoincrement=True, comment='编号'),
        sa.Column('table_name', sa.String(200), nullable=False, server_default='', comment='表名称'),
        sa.Column('table_comment', sa.String(500), nullable=False, server_default='', comment='表描述'),
        sa.Column('sub_table_name', sa.String(64), nullable=True, comment='关联子表的表名'),
        sa.Column('sub_table_fk_name', sa.String(64), nullable=True, comment='子表关联的外键名'),
        sa.Column('class_name', sa.String(100), nullable=False, server_default='', comment='实体类名称'),
        sa.Column('tpl_category', sa.String(200), nullable=False, server_default='crud', comment='使用的模板（crud单表操作 tree树表操作）'),
        sa.Column('tpl_web_type', sa.String(30), nullable=False, server_default='', comment='前端模板类型（element-ui模版 element-plus模版）'),
        sa.Column('package_name', sa.String(100), nullable=True, comment='生成包路径'),
        sa.Column('module_name', sa.String(30), nullable=True, comment='生成模块名'),
        sa.Column('business_name', sa.String(30), nullable=True, comment='生成业务名'),
        sa.Column('function_name', sa.String(50), nullable=True, comment='生成功能名'),
        sa.Column('function_author', sa.String(50), nullable=True, comment='生成功能作者'),
        sa.Column('gen_type', sa.String(1), nullable=False, server_default='0', comment='生成代码方式（0