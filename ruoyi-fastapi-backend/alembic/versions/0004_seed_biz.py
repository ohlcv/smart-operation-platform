"""seed biz data：业务 8 张表的种子数据

Revision ID: 0004_seed_biz
Revises: 0003_seed_sys
Create Date: 2026-07-12 18:30:00.000000

v4.0 重构：
- 把原 sql/biz_init.sql / biz_channel_init.sql / biz_invoice_init.sql /
  biz_finance_init.sql / biz_operation_init.sql 的演示数据合并
- 渠道表 province/city/lng/lat 与 v3.3 路线 C 对齐
- 客户表 province 与 v3.3 路线 C 对齐
- 合同表 province 由 customer 派生
"""
from __future__ import annotations

from alembic import op

revision = '0004_seed_biz'
down_revision = '0003_seed_sys'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== biz_customer（5 个客户 + 省份 v3.3 路线 C） ==============
    op.execute("""
        INSERT IGNORE INTO biz_customer
          (id, customer_code, customer_name, customer_type, contact_name, contact_phone, address, province, level, status, created_by, create_time, remark)
        VALUES
          (1, 'KH-001', '济南新华书店',     'publish', '王经理', '13900000001', '济南市市中区胜利大街56号', '山东', 'A', 1, 1, NOW(), '战略合作客户'),
          (2, 'KH-002', '青岛出版发行集团', 'publish', '李主任', '13900000002', '青岛市市南区香港中路26号', '浙江', 'A', 1, 1, NOW(), '数字出版核心客户'),
          (3, 'KH-003', '泰山景区管委会',   'scenic',  '张科长', '13900000003', '泰安市岱宗大街',         '广东', 'A', 1, 1, NOW(), '景区发行重点客户'),
          (4, 'KH-004', '山东文旅集团',     'agency',  '赵总',   '13900000004', '济南市经四路',           '北京', 'B', 1, 1, NOW(), '旅行社渠道'),
          (5, 'KH-005', '曲阜孔子文化园',   'scenic',  '陈馆长', '13900000005', '曲阜市明故城',           '四川', 'B', 1, 1, NOW(), '景区发行');
    """)

    # ============== biz_contract（3 个合同；province 由 customer 派生） ==============
    op.execute("""
        INSERT IGNORE INTO biz_contract
          (id, contract_no, title, contract_type, party_a, party_b, amount, sign_date, department, business_type, customer_id, customer_name, province, status, current_step, current_role, reject_count, created_by, created_by_name, create_time, remark)
        VALUES
          (1, 'HT-2026-001', '济南新华书店图书采购合同', 'payment',  '济南新华书店',     '山东出版供应链管理公司', 500000.00,   '2026-07-05', '业务部',     '景区门票', 1, '济南新华书店',     '山东', 'pending',  1, 'business_reviewer', 0, 2, '年糕', NOW(), '示范合同：审批中'),
          (2, 'HT-2026-002', '青岛数字出版合作协议',     'business', '青岛出版发行集团', '山东出版供应链管理公司', 300000.00,   '2026-07-08', '数字业务部', '数字出版', 2, '青岛出版发行集团', '浙江', 'draft',    0, NULL,                0, 2, '年糕', NOW(), '示范合同：草稿'),
          (3, 'HT-2026-003', '泰山景区票务系统对接',     'business', '泰山景区管委会',   '山东出版供应链管理公司', 1200000.00,  '2026-07-10', '技术部',     '景区门票', 3, '泰山景区管委会',   '广东', 'approved', 6, 'invest_director',    0, 2, '年糕', NOW(), '示范合同：已通过');
    """)

    # ============== biz_channel（4 个渠道 + v3.3 路线 C 位置坐标） ==============
    op.execute("""
        INSERT IGNORE INTO biz_channel
          (id, channel_code, channel_name, category, contact_name, contact_phone, platform_url, account, password, commission_rate, province, city, lng, lat, status, sort_order, description, created_by, created_by_name, create_time, remark)
        VALUES
          (1, 'QD-001', '美团到综（景区合作）',  'meituan',   '美团商务',  '400-009-9888', 'https://www.meituan.com', 'meituan_biz_01', 'demo_pwd', 0.0500, '北京', '北京', 116.40, 39.90, 1, 0, '美团综合业务：景区门票/酒店/餐饮', 1, 'admin', NOW(), '示范渠道：美团到综'),
          (2, 'QD-002', '抖音生活服务',          'douyin',    '抖音商务',  '400-822-2288', 'https://www.douyin.com',  'dy_biz_01',      'demo_pwd', 0.0600, '北京', '北京', 116.40, 39.90, 1, 0, '抖音本地生活服务',               1, 'admin', NOW(), '示范渠道：抖音生活'),
          (3, 'QD-003', '携程商旅',              'ctrip',     '携程商务',  '400-819-9999', 'https://www.ctrip.com',   'ctrip_biz_01',   'demo_pwd', 0.0450, '上海', '上海', 121.47, 31.23, 1, 0, '携程商旅业务',                   1, 'admin', NOW(), '示范渠道：携程商旅'),
          (4, 'QD-004', '同程旅行（OTA 直连）',  'tongcheng', '同程商务',  '400-100-7777', 'https://www.ly.com',      'tongcheng_biz',  'demo_pwd', 0.0480, '江苏', '苏州', 120.62, 31.32, 1, 0, '同程旅行 OTA 直连',             1, 'admin', NOW(), '示范渠道：同程旅行');
    """)

    # ============== biz_invoice（1 张示范发票：与合同 HT-2026-003 1:1 关联） ==============
    op.execute("""
        INSERT IGNORE INTO biz_invoice
          (id, invoice_no, contract_id, contract_no, invoice_type, amount, tax_rate, tax_amount, party_name, party_tax_no, status, apply_date, issue_date, created_by, created_by_name, create_time, remark)
        VALUES
          (1, 'FP-0001', 3, 'HT-2026-003', 'specialized', 1200000.00, 0.1300, 138053.10, '泰山景区管委会', '91910000123456789X', 'issued', '2026-07-10', '2026-07-11', 1, 'admin', NOW(), '示范发票：与 HT-2026-003 关联');
    """)

    # ============== biz_finance_entry（1 条示范流水：与 FP-0001 关联） ==============
    op.execute("""
        INSERT IGNORE INTO biz_finance_entry
          (id, entry_no, entry_type, direction, invoice_id, invoice_no, contract_id, contract_no, party_name, amount, account, account_name, bank_name, transaction_date, cleared, created_by, created_by_name, create_time, remark)
        VALUES
          (1, 'FN-0001', 'receivable', 'in', 1, 'FP-0001', 3, 'HT-2026-003', '泰山景区管委会', 1200000.00, '6225880123456789', '山东出版供应链管理公司', '工商银行济南分行', '2026-07-11', 0, 1, 'admin', NOW(), '示范应收：与 FP-0001 关联');
    """)

    # ============== biz_operation（3 期经营数据：2025-07 / 2026-06 / 2026-07） ==============
    op.execute("""
        INSERT IGNORE INTO biz_operation
          (id, period, period_type, business_line, revenue, cost, gross_profit, customer_count, contract_count, avg_order_value, created_by, created_by_name, create_time, remark)
        VALUES
          (1, '2025-07', 'month', NULL, 3800000.00, 2800000.00, 1000000.00, 25, 8,  475000.00, 1, 'admin', NOW(), '去年同期'),
          (2, '2026-06', 'month', NULL, 4500000.00, 3200000.00, 1300000.00, 32, 10, 450000.00, 1, 'admin', NOW(), '上月'),
          (3, '2026-07', 'month', NULL, 5200000.00, 3500000.00, 1700000.00, 35, 12, 433333.33, 1, 'admin', NOW(), '当月（含 HT-2026-003 已开票）');
    """)


def downgrade() -> None:
    op.execute("DELETE FROM biz_operation;")
    op.execute("DELETE FROM biz_finance_entry;")
    op.execute("DELETE FROM biz_invoice;")
    op.execute("DELETE FROM biz_channel;")
    op.execute("DELETE FROM biz_contract;")
    op.execute("DELETE FROM biz_customer;")