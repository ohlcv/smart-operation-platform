"""baseline biz schema（业务 8 张表）

Revision ID: 0002_baseline_biz
Revises: 0001_baseline_sys_ruoyi
Create Date: 2026-07-12 18:30:00.000000

v4.0 重构：
- 把原 sql/biz_*.sql 的业务表结构（不含数据）迁移到 Alembic
- 字段与各 biz_*_do.py ORM 1:1 对齐
- 包括 v3.3 路线 C 的 province/city/lng/lat 列（dashboard_v3_3_init.sql 已合并到此处）
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = '0002_baseline_biz'
down_revision = '0001_baseline_sys_ruoyi'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== biz_customer（ADR D24 含 customer_code） ==============
    op.create_table(
        'biz_customer',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='客户ID'),
        sa.Column('customer_code', sa.String(50), nullable=True, comment='业务编号 KH-NNN（唯一键）'),
        sa.Column('customer_name', sa.String(200), nullable=False, comment='客户名称（公司全称）'),
        sa.Column('customer_type', sa.String(20), nullable=True, comment='客户类型 scenic/hotel/agency/publish'),
        sa.Column('contact_name', sa.String(50), nullable=True, comment='联系人'),
        sa.Column('contact_phone', sa.String(20), nullable=True, comment='联系电话'),
        sa.Column('contact_email', sa.String(100), nullable=True, comment='邮箱'),
        sa.Column('address', sa.String(300), nullable=True, comment='地址'),
        sa.Column('province', sa.String(40), nullable=True, comment='省份（v3.3 路线 C）'),
        sa.Column('business_license', sa.String(200), nullable=True, comment='营业执照编号'),
        sa.Column('tax_no', sa.String(50), nullable=True, comment='纳税人识别号'),
        sa.Column('qualification_files', sa.JSON, nullable=True, comment='资质文件列表 [{name,url}]'),
        sa.Column('level', sa.String(10), nullable=True, comment='客户等级 A/B/C'),
        sa.Column('tags', sa.JSON, nullable=True, comment='标签 ["景区","文旅"]'),
        sa.Column('status', mysql.TINYINT(4), nullable=False, server_default='1', comment='状态 0=停用 1=启用'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_code', name='uk_customer_code'),
        mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci',
        comment='客户档案表',
    )
    op.create_index('idx_customer_type', 'biz_customer', ['customer_type'])
    op.create_index('idx_level', 'biz_customer', ['level'])
    op.create_index('idx_status', 'biz_customer', ['status'])

    # ============== biz_contract（含 province v3.3 路线 C） ==============
    op.create_table(
        'biz_contract',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='合同ID'),
        sa.Column('contract_no', sa.String(50), nullable=False, comment='合同编号（唯一）'),
        sa.Column('title', sa.String(200), nullable=False, comment='合同名称'),
        sa.Column('contract_type', sa.String(20), nullable=False, comment='payment / business'),
        sa.Column('party_a', sa.String(200), nullable=False, comment='甲方（客户）'),
        sa.Column('party_b', sa.String(200), nullable=False, comment='乙方（本司）'),
        sa.Column('amount', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='合同金额（元）'),
        sa.Column('amount_in_words', sa.String(100), nullable=True, comment='金额大写'),
        sa.Column('sign_date', sa.Date, nullable=True, comment='签订日期'),
        sa.Column('department', sa.String(100), nullable=True, comment='申请部门'),
        sa.Column('business_type', sa.String(50), nullable=True, comment='业务类型'),
        sa.Column('customer_id', sa.BigInteger, nullable=True, comment='关联客户ID biz_customer.id'),
        sa.Column('customer_name', sa.String(200), nullable=True, comment='冗余客户名称'),
        sa.Column('province', sa.String(40), nullable=True, comment='客户省份（v3.3 路线 C 冗余）'),
        sa.Column('remark', sa.Text, nullable=True, comment='合同备注'),
        sa.Column('attachments', sa.JSON, nullable=True, comment='附件列表 [{name,url}]'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft', comment='draft/pending/approved/rejected'),
        sa.Column('current_step', sa.Integer, nullable=False, server_default='0', comment='当前审批步骤 0-6'),
        sa.Column('current_role', sa.String(50), nullable=True, comment='当前待审角色 role_key'),
        sa.Column('reject_count', sa.Integer, nullable=False, server_default='0', comment='累计驳回次数'),
        sa.Column('created_by', sa.BigInteger, nullable=False, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(50), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_no', name='uk_contract_no'),
        mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci',
        comment='合同主表',
    )
    op.create_index('idx_status', 'biz_contract', ['status'])
    op.create_index('idx_current_step', 'biz_contract', ['current_step'])
    op.create_index('idx_created_by', 'biz_contract', ['created_by'])
    op.create_index('idx_create_time', 'biz_contract', ['create_time'])
    op.create_index('idx_customer_id', 'biz_contract', ['customer_id'])

    # ============== biz_approval ==============
    op.create_table(
        'biz_approval',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='审批记录ID'),
        sa.Column('contract_id', sa.BigInteger, nullable=False, comment='关联合同ID biz_contract.id'),
        sa.Column('approver_id', sa.BigInteger, nullable=True, comment='审批人 sys_user.user_id'),
        sa.Column('approver_name', sa.String(50), nullable=True, comment='审批人姓名（冗余）'),
        sa.Column('step', sa.Integer, nullable=False, comment='审批步骤 0-6'),
        sa.Column('approver_role', sa.String(50), nullable=False, comment='审批时角色标识'),
        sa.Column('action', sa.String(20), nullable=False, comment='approve=通过 / reject=驳回'),
        sa.Column('comment', sa.Text, nullable=True, comment='审批意见'),
        sa.Column('reject_reason', sa.Text, nullable=True, comment='驳回原因'),
        sa.Column('signature_snapshot', sa.Text, nullable=True, comment='签名快照 base64 data URI'),
        sa.Column('approval_ip', sa.String(50), nullable=True, comment='审批操作 IP'),
        sa.Column('approval_time', sa.DateTime, nullable=False, comment='审批时间'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='记录创建时间'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci',
        comment='审批记录表',
    )
    op.create_index('idx_contract_id', 'biz_approval', ['contract_id'])
    op.create_index('idx_approver_id', 'biz_approval', ['approver_id'])
    op.create_index('idx_step', 'biz_approval', ['step'])
    op.create_index('idx_approval_time', 'biz_approval', ['approval_time'])

    # ============== biz_channel（含 v3.3 路线 C province/city/lng/lat） ==============
    op.create_table(
        'biz_channel',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='渠道ID'),
        sa.Column('channel_code', sa.String(50), nullable=False, comment='渠道编码 QD-NNN'),
        sa.Column('channel_name', sa.String(100), nullable=False, comment='渠道名称'),
        sa.Column('category', sa.String(20), nullable=False, comment='渠道分类 meituan/douyin/ctrip/tongcheng'),
        sa.Column('contact_name', sa.String(50), nullable=True, comment='联系人'),
        sa.Column('contact_phone', sa.String(20), nullable=True, comment='联系电话'),
        sa.Column('contact_email', sa.String(100), nullable=True, comment='联系邮箱'),
        sa.Column('platform_url', sa.String(255), nullable=True, comment='平台地址'),
        sa.Column('account', sa.String(128), nullable=True, comment='登录账号（演示用）'),
        sa.Column('password', sa.String(128), nullable=True, comment='登录密码（演示用，明文不加密）'),
        sa.Column('commission_rate', mysql.DECIMAL(5, 4), nullable=True, comment='佣金比例（0-1）'),
        sa.Column('province', sa.String(40), nullable=True, comment='省份（v3.3 路线 C）'),
        sa.Column('city', sa.String(40), nullable=True, comment='城市（v3.3 路线 C）'),
        sa.Column('lng', mysql.DOUBLE, nullable=True, comment='经度（v3.3 路线 C）'),
        sa.Column('lat', mysql.DOUBLE, nullable=True, comment='纬度（v3.3 路线 C）'),
        sa.Column('status', sa.Integer, nullable=False, server_default='1', comment='状态 0=停用 1=启用'),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0', comment='排序值'),
        sa.Column('description', sa.Text, nullable=True, comment='渠道说明'),
        sa.Column('attachments', sa.JSON, nullable=True, comment='资质附件 [{name,url}]'),
        sa.Column('contract_ids', sa.JSON, nullable=True, comment='关联合同ID列表（冗余便于展示）'),
        sa.Column('remark', sa.Text, nullable=True, comment='备注'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(64), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('channel_code', name='uk_channel_code'),
        mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci',
        comment='渠道主表',
    )
    op.create_index('idx_category', 'biz_channel', ['category'])
    op.create_index('idx_status', 'biz_channel', ['status'])

    # ============== biz_invoice ==============
    op.create_table(
        'biz_invoice',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='发票ID'),
        sa.Column('invoice_no', sa.String(50), nullable=False, comment='发票号（唯一）'),
        sa.Column('contract_id', sa.BigInteger, nullable=False, comment='关联合同ID biz_contract.id（1:1）'),
        sa.Column('contract_no', sa.String(50), nullable=True, comment='冗余合同编号（便于展示）'),
        sa.Column('invoice_type', sa.String(20), nullable=False, comment='specialized/general/electronic'),
        sa.Column('amount', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='开票金额（含税）'),
        sa.Column('tax_rate', mysql.DECIMAL(5, 4), nullable=False, server_default='0.0000', comment='税率'),
        sa.Column('tax_amount', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='税额'),
        sa.Column('party_name', sa.String(200), nullable=False, comment='购方名称（抬头）'),
        sa.Column('party_tax_no', sa.String(50), nullable=True, comment='购方税号'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='pending/issued/void'),
        sa.Column('apply_date', sa.Date, nullable=True, comment='申请日期'),
        sa.Column('issue_date', sa.Date, nullable=True, comment='开票日期'),
        sa.Column('void_reason', sa.String(500), nullable=True, comment='作废原因'),
        sa.Column('remark', sa.Text, nullable=True, comment='备注'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(64), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_no', name='uk_invoice_no'),
        sa.UniqueConstraint('contract_id', name='uk_contract_id'),
        mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci',
        comment='发票主表',
    )
    op.create_index('idx_invoice_status', 'biz_invoice', ['status'])
    op.create_index('idx_invoice_create_time', 'biz_invoice', ['create_time'])

    # ============== biz_finance_entry ==============
    op.create_table(
        'biz_finance_entry',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='流水ID'),
        sa.Column('entry_no', sa.String(50), nullable=False, comment='流水号 FN-NNN'),
        sa.Column('entry_type', sa.String(20), nullable=False, comment='payable/receivable'),
        sa.Column('direction', sa.String(10), nullable=False, server_default='out', comment='out/in'),
        sa.Column('invoice_id', sa.BigInteger, nullable=True, comment='关联发票ID biz_invoice.id'),
        sa.Column('invoice_no', sa.String(50), nullable=True, comment='冗余发票号'),
        sa.Column('contract_id', sa.BigInteger, nullable=True, comment='关联合同ID biz_contract.id'),
        sa.Column('contract_no', sa.String(50), nullable=True, comment='冗余合同号'),
        sa.Column('party_name', sa.String(200), nullable=True, comment='对手方名称'),
        sa.Column('amount', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='金额'),
        sa.Column('account', sa.String(50), nullable=True, comment='银行账号'),
        sa.Column('account_name', sa.String(100), nullable=True, comment='账户名'),
        sa.Column('bank_name', sa.String(100), nullable=True, comment='开户行'),
        sa.Column('transaction_date', sa.Date, nullable=True, comment='交易日期'),
        sa.Column('cleared', sa.Integer, nullable=False, server_default='0', comment='是否已对账'),
        sa.Column('cleared_time', sa.DateTime, nullable=True, comment='对账时间'),
        sa.Column('remark', sa.Text, nullable=True, comment='备注'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(64), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_no', name='uk_entry_no'),
        mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci',
        comment='财务流水台账',
    )
    op.create_index('idx_entry_type', 'biz_finance_entry', ['entry_type'])
    op.create_index('idx_cleared', 'biz_finance_entry', ['cleared'])
    op.create_index('idx_transaction_date', 'biz_finance_entry', ['transaction_date'])
    op.create_index('idx_invoice_id', 'biz_finance_entry', ['invoice_id'])
    op.create_index('idx_contract_id', 'biz_finance_entry', ['contract_id'])

    # ============== biz_bank_statement ==============
    op.create_table(
        'biz_bank_statement',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='对账单ID'),
        sa.Column('batch_no', sa.String(50), nullable=False, comment='导入批次号 BS-YYYYMMDDHHMMSS'),
        sa.Column('transaction_date', sa.Date, nullable=False, comment='交易日期'),
        sa.Column('account', sa.String(50), nullable=False, comment='银行账号'),
        sa.Column('amount', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='金额'),
        sa.Column('direction', sa.String(10), nullable=False, server_default='in', comment='in/out'),
        sa.Column('counterparty', sa.String(100), nullable=True, comment='交易对手'),
        sa.Column('counterparty_account', sa.String(50), nullable=True, comment='对手账号'),
        sa.Column('summary', sa.String(200), nullable=True, comment='摘要'),
        sa.Column('matched', sa.Integer, nullable=False, server_default='0', comment='是否已匹配'),
        sa.Column('matched_entry_id', sa.BigInteger, nullable=True, comment='匹配的财务流水ID'),
        sa.Column('import_time', sa.DateTime, nullable=False, comment='导入时间'),
        sa.Column('imported_by', sa.BigInteger, nullable=True, comment='导入人 sys_user.user_id'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci',
        comment='银行对账单导入表',
    )
    op.create_index('idx_batch_no', 'biz_bank_statement', ['batch_no'])
    op.create_index('idx_statement_transaction_date', 'biz_bank_statement', ['transaction_date'])
    op.create_index('idx_matched', 'biz_bank_statement', ['matched'])
    op.create_index('idx_account', 'biz_bank_statement', ['account'])

    # ============== biz_operation ==============
    op.create_table(
        'biz_operation',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='记录ID'),
        sa.Column('period', sa.String(20), nullable=False, comment='周期 key 2026-07/2026-Q3/2026'),
        sa.Column('period_type', sa.String(20), nullable=False, comment='month/quarter/year'),
        sa.Column('business_line', sa.String(20), nullable=True, comment='scenic/digital/logistics'),
        sa.Column('revenue', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='营收'),
        sa.Column('cost', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='成本'),
        sa.Column('gross_profit', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='毛利（实时计算冗余）'),
        sa.Column('customer_count', sa.Integer, nullable=False, server_default='0', comment='客户数'),
        sa.Column('contract_count', sa.Integer, nullable=False, server_default='0', comment='合同数'),
        sa.Column('avg_order_value', mysql.DECIMAL(18, 2), nullable=False, server_default='0.00', comment='客单价'),
        sa.Column('remark', sa.Text, nullable=True, comment='备注'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(64), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period', 'period_type', 'business_line', name='uk_period_type_line'),
        mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci',
        comment='经营数据表',
    )
    op.create_index('idx_op_period_type', 'biz_operation', ['period_type'])
    op.create_index('idx_op_business_line', 'biz_operation', ['business_line'])
    op.create_index('idx_op_period', 'biz_operation', ['period'])


def downgrade() -> None:
    op.drop_table('biz_operation')
    op.drop_table('biz_bank_statement')
    op.drop_table('biz_finance_entry')
    op.drop_table('biz_invoice')
    op.drop_table('biz_channel')
    op.drop_table('biz_approval')
    op.drop_table('biz_contract')
    op.drop_table('biz_customer')