"""seed sys data：sys_dept / sys_user / sys_role / sys_menu / sys_dict_*

Revision ID: 0003_seed_sys
Revises: 0002_baseline_biz
Create Date: 2026-07-12 18:30:00.000000

v4.0 重构：
- 把原 sql/ruoyi-fastapi.sql 的 sys_dict_* 种子数据 + sql/approval_init.sql 的
  sys_user / sys_role 种子数据合并到此
- 使用 INSERT IGNORE 保持幂等（重复执行不报错）
- 7 个审批测试用户的 bcrypt hash 与原 SQL 一致
"""
from __future__ import annotations

from alembic import op

revision = '0003_seed_sys'
down_revision = '0002_baseline_biz'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== sys_dept（年糕集团 9 个部门） ==============
    op.execute("""
        INSERT IGNORE INTO sys_dept (dept_id, parent_id, ancestors, dept_name, order_num, leader, phone, email, status, del_flag, create_by, create_time, update_by, update_time)
        VALUES
        (100, 0,   '0',         '集团总公司',   0, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (101, 100, '0,100',     '深圳分公司', 1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (102, 100, '0,100',     '长沙分公司', 2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (103, 101, '0,100,101', '研发部门',   1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (104, 101, '0,100,101', '市场部门',   2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (105, 101, '0,100,101', '测试部门',   3, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (106, 101, '0,100,101', '财务部门',   4, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (107, 101, '0,100,101', '运维部门',   5, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (108, 102, '0,100,102', '市场部门',   1, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL),
        (109, 102, '0,100,102', '财务部门',   2, '年糕', '15888888888', 'niangao@qq.com', '0', '0', 'admin', NOW(), '', NULL);
    """)

    # ============== sys_role（admin + common + 7 个审批角色） ==============
    # 注意：D02 role_sort 规范：admin=0（隐藏超管）、common=99（非审批 sentinel）、3-9=7级审批链
    op.execute("""
        INSERT IGNORE INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
        VALUES
        (1,  '超级管理员',   'admin',                0,  1, 1, 1, '0', '0', 'admin', NOW(), '隐藏超管（role_sort=0）'),
        (2,  '普通角色',     'common',              99,  5, 1, 1, '0', '0', 'admin', NOW(), '非审批 sentinel（role_sort=99）'),
        (3,  '业务经办',     'business_handler',    1,  5, 1, 1, '0', '0', 'admin', NOW(), 'Step 0：业务经办提交'),
        (4,  '业务复核',     'business_reviewer',   2,  4, 1, 1, '0', '0', 'admin', NOW(), 'Step 1：业务复核'),
        (5,  '风控审核',     'risk_auditor',        3,  1, 1, 1, '0', '0', 'admin', NOW(), 'Step 2：风控审核'),
        (6,  '财务经办',     'finance_handler',     4,  1, 1, 1, '0', '0', 'admin', NOW(), 'Step 3：财务经办'),
        (7,  '财务复核',     'finance_reviewer',    5,  1, 1, 1, '0', '0', 'admin', NOW(), 'Step 4：财务复核'),
        (8,  '供管公司负责人', 'scm_director',        6,  1, 1, 1, '0', '0', 'admin', NOW(), 'Step 5：供管公司负责人'),
        (9,  '投资公司负责人', 'invest_director',     7,  1, 1, 1, '0', '0', 'admin', NOW(), 'Step 6：投资公司负责人（终审）');
    """)

    # ============== sys_user（admin 默认密码 admin123，7 测试用户密码 123456） ==============
    # admin 的 bcrypt hash 是 RuoYi 默认的 admin123 哈希
    op.execute("""
        INSERT IGNORE INTO sys_user
          (user_id, dept_id, user_name, nick_name, user_type, email, phonenumber, sex, avatar, password,
           status, del_flag, login_ip, login_date, pwd_update_date, create_by, create_time, update_by, update_time, remark)
        VALUES
          (1, 103, 'admin', '超级管理员', '00', 'niangao@qq.com', '15888888888', '1', '',
           '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
           '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, '系统内置超级管理员'),
          (101, 103, 'biz_handler',  '业务经办',     '00', 'biz_handler@demo.com',  '13900000101', '1', '',
           '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
           '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 0 测试账号 / 密码 123456'),
          (102, 103, 'biz_reviewer', '业务复核',     '00', 'biz_reviewer@demo.com', '13900000102', '1', '',
           '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
           '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 1 测试账号 / 密码 123456'),
          (103, 103, 'risk_auditor', '风控审核',     '00', 'risk_auditor@demo.com', '13900000103', '1', '',
           '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
           '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 2 测试账号 / 密码 123456'),
          (104, 103, 'finance_h',    '财务经办',     '00', 'finance_h@demo.com',    '13900000104', '1', '',
           '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
           '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 3 测试账号 / 密码 123456'),
          (105, 103, 'finance_r',    '财务复核',     '00', 'finance_r@demo.com',    '13900000105', '1', '',
           '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
           '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 4 测试账号 / 密码 123456'),
          (106, 103, 'scm_director', '供管负责人',   '00', 'scm_director@demo.com', '13900000106', '1', '',
           '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
           '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 5 测试账号 / 密码 123456'),
          (107, 103, 'invest_d',     '投资负责人',   '00', 'invest_d@demo.com',     '13900000107', '1', '',
           '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
           '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 6 测试账号 / 密码 123456');
    """)

    # ============== sys_user_role：admin 同时是 7 个审批角色（便于自己提交审批） ==============
    op.execute("""
        INSERT IGNORE INTO sys_user_role (user_id, role_id) VALUES
          (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9),
          (101, 3), (102, 4), (103, 5), (104, 6), (105, 7), (106, 8), (107, 9);
    """)

    # ============== sys_menu（RuoYi 原生 + 业务 5 个菜单 + 仪表盘） ==============
    # 1=系统管理目录  2=系统监控  3=系统工具  4=若依官网(外链)  5=业务管理目录
    # 6=合同管理  7=客户管理  8=审批中心  12=渠道管理  13=仪表盘  14=发票管理  15=财务管理  16=经营数据
    op.execute("""
        INSERT IGNORE INTO sys_menu
          (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
        VALUES
          (1, '系统管理', 0, 1, 'system', NULL, 1, 0, 'M', '0', '0', '', 'system', 'admin', NOW(), '系统管理目录'),
          (2, '系统监控', 0, 2, 'monitor', NULL, 1, 0, 'M', '0', '0', '', 'monitor', 'admin', NOW(), '系统监控目录'),
          (3, '系统工具', 0, 3, 'tool', NULL, 1, 0, 'M', '0', '0', '', 'tool', 'admin', NOW(), '系统工具目录'),
          (4, '若依官网', 0, 4, 'https://ruoyi.vip', NULL, 0, 0, 'M', '0', '0', '', 'guide', 'admin', NOW(), '外链'),
          (5, '业务管理', 0, 5, 'biz', NULL, 1, 0, 'M', '0', '0', 'biz:view', 'shopping', 'admin', NOW(), '业务管理目录'),
          (6, '合同管理', 5, 1, 'biz/contract', 'biz/contract/index', 1, 0, 'C', '0', '0', 'contract:list,contract:add,contract:edit,contract:delete,contract:submit', 'list', 'admin', NOW(), '合同管理'),
          (7, '客户管理', 5, 2, 'biz/customer', 'biz/customer/index', 1, 0, 'C', '0', '0', 'customer:list,customer:add,customer:edit,customer:delete', 'peoples', 'admin', NOW(), '客户管理'),
          (8, '审批中心', 5, 3, 'biz/approval', 'biz/approval/index', 1, 0, 'C', '0', '0', 'approval:list,approval:approve,approval:reject', 'checkbox', 'admin', NOW(), '7 级审批链路'),
          (12, '渠道管理', 5, 9, 'biz/channel', 'biz/channel/index', 1, 0, 'C', '0', '0', 'channel:list,channel:add,channel:edit,channel:delete,channel:import', 'link', 'admin', NOW(), '路线A'),
          (13, '仪表盘', 0, 13, '/dashboard', 'cockpit/dashboard', 1, 0, 'C', '0', '0', 'biz:dashboard:view', 'dashboard', 'admin', NOW(), 'v3.6 嵌入 Layout'),
          (14, '发票管理', 5, 10, 'biz/invoice', 'biz/invoice/index', 1, 0, 'C', '0', '0', 'invoice:list,invoice:add,invoice:edit,invoice:delete,invoice:issue,invoice:void', 'pdf', 'admin', NOW(), '路线A'),
          (15, '财务管理', 5, 11, 'biz/finance', 'biz/finance/index', 1, 0, 'C', '0', '0', 'finance:list,finance:add,finance:edit,finance:delete,finance:import', 'money', 'admin', NOW(), '路线A'),
          (16, '经营数据', 5, 12, 'biz/operation', 'biz/operation/index', 1, 0, 'C', '0', '0', 'operation:list,operation:add,operation:edit,operation:delete,operation:comparison', 'chart', 'admin', NOW(), '路线A');
    """)

    # ============== sys_role_menu：admin 挂全部 + 7 业务角色挂业务菜单 ==============
    op.execute("""
        INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
        SELECT 1, menu_id FROM sys_menu WHERE status = '0';
    """)
    op.execute("""
        INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
          (3, 5), (3, 6), (3, 7), (3, 8), (3, 12), (3, 14), (3, 15), (3, 16), (3, 13),
          (4, 5), (4, 6), (4, 7), (4, 8), (4, 12), (4, 14), (4, 15), (4, 16), (4, 13),
          (5, 5), (5, 6), (5, 7), (5, 8), (5, 12), (5, 14), (5, 15), (5, 16), (5, 13),
          (6, 5), (6, 6), (6, 7), (6, 8), (6, 12), (6, 14), (6, 15), (6, 16), (6, 13),
          (7, 5), (7, 6), (7, 7), (7, 8), (7, 12), (7, 14), (7, 15), (7, 16), (7, 13),
          (8, 5), (8, 6), (8, 7), (8, 8), (8, 12), (8, 14), (8, 15), (8, 16), (8, 13),
          (9, 5), (9, 6), (9, 7), (9, 8), (9, 12), (9, 14), (9, 15), (9, 16), (9, 13);
    """)
    # common（role_id=2）也挂业务菜单，便于日常使用
    op.execute("""
        INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
          (2, 5), (2, 6), (2, 7), (2, 8), (2, 12), (2, 14), (2, 15), (2, 16), (2, 13);
    """)

    # ============== sys_dict_type（RuoYi 原生 + 业务字典） ==============
    op.execute("""
        INSERT IGNORE INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, remark)
        VALUES
          (1, '用户性别', 'sys_user_sex', '0', 'admin', NOW(), '用户性别列表'),
          (2, '菜单状态', 'sys_show_hide', '0', 'admin', NOW(), '菜单状态列表'),
          (3, '系统开关', 'sys_normal_disable', '0', 'admin', NOW(), '系统开关列表'),
          (4, '任务状态', 'sys_job_status', '0', 'admin', NOW(), '任务状态列表'),
          (5, '任务分组', 'sys_job_group', '0', 'admin', NOW(), '任务分组列表'),
          (6, '任务执行器', 'sys_job_executor', '0', 'admin', NOW(), '任务执行器列表'),
          (7, '系统是否', 'sys_yes_no', '0', 'admin', NOW(), '系统是否列表'),
          (8, '通知类型', 'sys_notice_type', '0', 'admin', NOW(), '通知类型列表'),
          (9, '通知状态', 'sys_notice_status', '0', 'admin', NOW(), '通知状态列表'),
          (10, '操作类型', 'sys_oper_type', '0', 'admin', NOW(), '操作类型列表'),
          (11, '系统状态', 'sys_common_status', '0', 'admin', NOW(), '登录状态列表'),
          (12, 'AI模型提供商', 'ai_provider_type', '0', 'admin', NOW(), 'AI模型提供商列表'),
          (100, '合同类型', 'contract_type', '0', 'admin', NOW(), '合同单据类型'),
          (101, '业务线', 'business_line', '0', 'admin', NOW(), '经营数据业务线'),
          (102, '渠道类型', 'channel_type', '0', 'admin', NOW(), 'OTA 渠道类型'),
          (103, '客户类型', 'customer_type', '0', 'admin', NOW(), '客户档案分类');
    """)

    # ============== sys_dict_data（精简常用值，AI 模型列表此处不重复，与 ruoyi-fastapi.sql 保持一致可在后续补丁追加） ==============
    op.execute("""
        INSERT IGNORE INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
        VALUES
          (1, 1, '男', '0', 'sys_user_sex', '', '', 'Y', '0', 'admin', NOW(), '性别男'),
          (2, 2, '女', '1', 'sys_user_sex', '', '', 'N', '0', 'admin', NOW(), '性别女'),
          (3, 3, '未知', '2', 'sys_user_sex', '', '', 'N', '0', 'admin', NOW(), '性别未知'),
          (4, 1, '显示', '0', 'sys_show_hide', '', 'primary', 'Y', '0', 'admin', NOW(), '显示菜单'),
          (5, 2, '隐藏', '1', 'sys_show_hide', '', 'danger', 'N', '0', 'admin', NOW(), '隐藏菜单'),
          (6, 1, '正常', '0', 'sys_normal_disable', '', 'primary', 'Y', '0', 'admin', NOW(), '正常状态'),
          (7, 2, '停用', '1', 'sys_normal_disable', '', 'danger', 'N', '0', 'admin', NOW(), '停用状态'),
          (8, 1, '正常', '0', 'sys_job_status', '', 'primary', 'Y', '0', 'admin', NOW(), '正常状态'),
          (9, 2, '暂停', '1', 'sys_job_status', '', 'danger', 'N', '0', 'admin', NOW(), '停用状态'),
          (15, 1, '是', 'Y', 'sys_yes_no', '', 'primary', 'Y', '0', 'admin', NOW(), '系统默认是'),
          (16, 2, '否', 'N', 'sys_yes_no', '', 'danger', 'N', '0', 'admin', NOW(), '系统默认否'),
          (17, 1, '通知', '1', 'sys_notice_type', '', 'warning', 'Y', '0', 'admin', NOW(), '通知'),
          (18, 2, '公告', '2', 'sys_notice_type', '', 'success', 'N', '0', 'admin', NOW(), '公告'),
          (19, 1, '正常', '0', 'sys_notice_status', '', 'primary', 'Y', '0', 'admin', NOW(), '正常状态'),
          (20, 2, '关闭', '1', 'sys_notice_status', '', 'danger', 'N', '0', 'admin', NOW(), '关闭状态'),
          (21, 99, '其他', '0', 'sys_oper_type', '', 'info', 'N', '0', 'admin', NOW(), '其他操作'),
          (22, 1, '新增', '1', 'sys_oper_type', '', 'info', 'N', '0', 'admin', NOW(), '新增操作'),
          (23, 2, '修改', '2', 'sys_oper_type', '', 'info', 'N', '0', 'admin', NOW(), '修改操作'),
          (24, 3, '删除', '3', 'sys_oper_type', '', 'danger', 'N', '0', 'admin', NOW(), '删除操作'),
          (25, 4, '授权', '4', 'sys_oper_type', '', 'primary', 'N', '0', 'admin', NOW(), '授权操作'),
          (26, 5, '导出', '5', 'sys_oper_type', '', 'warning', 'N', '0', 'admin', NOW(), '导出操作'),
          (27, 6, '导入', '6', 'sys_oper_type', '', 'warning', 'N', '0', 'admin', NOW(), '导入操作'),
          (28, 7, '强退', '7', 'sys_oper_type', '', 'danger', 'N', '0', 'admin', NOW(), '强退操作'),
          (29, 8, '生成代码', '8', 'sys_oper_type', '', 'warning', 'N', '0', 'admin', NOW(), '生成操作'),
          (30, 9, '清空数据', '9', 'sys_oper_type', '', 'danger', 'N', '0', 'admin', NOW(), '清空操作'),
          (31, 1, '成功', '0', 'sys_common_status', '', 'primary', 'N', '0', 'admin', NOW(), '正常状态'),
          (32, 2, '失败', '1', 'sys_common_status', '', 'danger', 'N', '0', 'admin', NOW(), '停用状态'),
          -- contract_type
          (100, 1, '业务付款审批单', 'payment', 'contract_type', '', '', 'N', '0', 'admin', NOW(), '含付款审批的合同'),
          (101, 2, '业务审批单', 'business', 'contract_type', '', '', 'Y', '0', 'admin', NOW(), '普通业务审批'),
          -- business_line
          (102, 1, '景区发行', 'scenic', 'business_line', '', '', 'N', '0', 'admin', NOW(), '景区相关业务'),
          (103, 2, '数字出版', 'digital', 'business_line', '', '', 'N', '0', 'admin', NOW(), '数字内容业务'),
          (104, 3, '物流仓储', 'logistics', 'business_line', '', '', 'N', '0', 'admin', NOW(), '物流仓储业务'),
          -- channel_type
          (105, 1, '美团到综', 'meituan', 'channel_type', '', '', 'N', '0', 'admin', NOW(), '美团综合业务'),
          (106, 2, '抖音生活服务', 'douyin', 'channel_type', '', '', 'N', '0', 'admin', NOW(), '抖音本地生活'),
          (107, 3, '携程商旅', 'ctrip', 'channel_type', '', '', 'N', '0', 'admin', NOW(), '携程商旅'),
          (108, 4, '同程旅行', 'tongcheng', 'channel_type', '', '', 'N', '0', 'admin', NOW(), '同程旅行'),
          -- customer_type
          (109, 1, '景区', 'scenic', 'customer_type', '', '', 'N', '0', 'admin', NOW(), '景区客户'),
          (110, 2, '酒店', 'hotel', 'customer_type', '', '', 'N', '0', 'admin', NOW(), '酒店客户'),
          (111, 3, '旅行社', 'agency', 'customer_type', '', '', 'N', '0', 'admin', NOW(), '旅行社客户'),
          (112, 4, '出版社', 'publish', 'customer_type', '', '', 'N', '0', 'admin', NOW(), '出版社客户');
    """)


def downgrade() -> None:
    # seed 不支持完全 downgrade（会丢 admin / 业务字典）；这里只清非核心数据
    op.execute("DELETE FROM sys_dict_data WHERE dict_code >= 100;")
    op.execute("DELETE FROM sys_dict_type WHERE dict_id >= 100;")
    op.execute("DELETE FROM sys_role_menu WHERE role_id IN (3, 4, 5, 6, 7, 8, 9);")
    op.execute("DELETE FROM sys_user_role WHERE user_id IN (101, 102, 103, 104, 105, 106, 107);")
    op.execute("DELETE FROM sys_user WHERE user_id IN (101, 102, 103, 104, 105, 106, 107);")
    op.execute("DELETE FROM sys_role WHERE role_id IN (3, 4, 5, 6, 7, 8, 9);")
    op.execute("DELETE FROM sys_menu WHERE menu_id IN (5, 6, 7, 8, 12, 13, 14, 15, 16);")