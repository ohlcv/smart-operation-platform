"""seed all data：sys_* + biz_* 全部种子数据（v4.0 合并版）

Revision ID: 0002_seed_all
Revises: 0001_baseline_all
Create Date: 2026-07-12 22:30:00.000000

v4.0 重构：把原 0003_seed_sys + 0004_seed_biz + 0005_seed_sys_config 合并为一个 seed
- 使用 INSERT IGNORE 保持幂等（重复执行不报错）
- 7 个审批测试用户的 bcrypt hash 与原 SQL 一致
- admin 同时绑定 8 个角色（隐藏超管 role_id=1 + 7 个审批角色）确保 super admin 权限生效
- sys_config 8 条默认配置（修复验证码开关失效问题）

注意：admin 绑 (1,1) 是关键，原 0003 漏了这一行导致 super admin 分支不生效
"""
from __future__ import annotations

from alembic import op


revision = '0002_seed_all'
down_revision = '0001_baseline_all'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================
    # Part 1: sys_* 种子数据（部门 / 角色 / 用户 / 权限 / 菜单 / 字典 / 配置）
    # ============================================================

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
    # D02 role_sort 规范：admin=0（隐藏超管）、common=99（非审批 sentinel）、3-9=7级审批链
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

    # ============== sys_user_role：admin = 隐藏超管(1) + 7 个审批角色 ==============
    # 关键：必须包含 (1, 1)，否则 get_info 不走 super admin 分支，权限全空
    op.execute("""
        INSERT IGNORE INTO sys_user_role (user_id, role_id) VALUES
          (1, 1), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9),
          (101, 3), (102, 4), (103, 5), (104, 6), (105, 7), (106, 8), (107, 9);
    """)

    # ============== sys_menu（RuoYi 原生 + 业务 5 个菜单 + 仪表盘） ==============
    # 一级目录：1=系统管理  2=系统监控  3=系统工具  5=业务管理  13=仪表盘
    # 业务子菜单：6=合同  7=客户  8=审批中心  12=渠道  14=发票  15=财务  16=经营数据
    # 补全菜单树：100-120（系统管理/监控/工具 二级）+ 500-501（日志管理三级）+ 1000-1064（按钮）
    # 注意：原 menu_id=4「若依官网」已移除（若依官网不再外链）
    op.execute("""
        INSERT IGNORE INTO sys_menu
          (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
        VALUES
          (1, '系统管理', 0, 1, 'system', NULL, 1, 0, 'M', '0', '0', '', 'system', 'admin', NOW(), '系统管理目录'),
          (2, '系统监控', 0, 2, 'monitor', NULL, 1, 0, 'M', '0', '0', '', 'monitor', 'admin', NOW(), '系统监控目录'),
          (3, '系统工具', 0, 3, 'tool', NULL, 1, 0, 'M', '0', '0', '', 'tool', 'admin', NOW(), '系统工具目录'),
          (5, '业务管理', 0, 4, 'biz', NULL, 1, 0, 'M', '0', '0', 'biz:view', 'shopping', 'admin', NOW(), '业务管理目录'),
          (6, '合同管理', 5, 1, 'biz/contract', 'biz/contract/index', 1, 0, 'C', '0', '0', 'contract:list,contract:add,contract:edit,contract:delete,contract:submit', 'list', 'admin', NOW(), '合同管理'),
          (7, '客户管理', 5, 2, 'biz/customer', 'biz/customer/index', 1, 0, 'C', '0', '0', 'customer:list,customer:add,customer:edit,customer:delete', 'peoples', 'admin', NOW(), '客户管理'),
          (8, '审批中心', 5, 3, 'biz/approval', 'biz/approval/index', 1, 0, 'C', '0', '0', 'approval:list,approval:approve,approval:reject', 'checkbox', 'admin', NOW(), '7 级审批链路'),
          (12, '渠道管理', 5, 9, 'biz/channel', 'biz/channel/index', 1, 0, 'C', '0', '0', 'channel:list,channel:add,channel:edit,channel:delete,channel:import', 'link', 'admin', NOW(), '路线A'),
          (13, '仪表盘', 0, 13, '/dashboard', 'cockpit/dashboard', 1, 0, 'C', '0', '0', 'biz:dashboard:view', 'dashboard', 'admin', NOW(), 'v3.6 嵌入 Layout'),
          (14, '发票管理', 5, 10, 'biz/invoice', 'biz/invoice/index', 1, 0, 'C', '0', '0', 'invoice:list,invoice:add,invoice:edit,invoice:delete,invoice:issue,invoice:void', 'pdf', 'admin', NOW(), '路线A'),
          (15, '财务管理', 5, 11, 'biz/finance', 'biz/finance/index', 1, 0, 'C', '0', '0', 'finance:list,finance:add,finance:edit,finance:delete,finance:import', 'money', 'admin', NOW(), '路线A'),
          (16, '经营数据', 5, 12, 'biz/operation', 'biz/operation/index', 1, 0, 'C', '0', '0', 'operation:list,operation:add,operation:edit,operation:delete,operation:comparison', 'chart', 'admin', NOW(), '路线A'),
          /* 系统管理 二级菜单 */
          (100, '用户管理', 1, 1, 'user',       'system/user/index',      1, 0, 'C', '0', '0', 'system:user:list',       'user',       'admin', NOW(), '用户管理菜单'),
          (101, '角色管理', 1, 2, 'role',       'system/role/index',      1, 0, 'C', '0', '0', 'system:role:list',       'peoples',    'admin', NOW(), '角色管理菜单'),
          (102, '菜单管理', 1, 3, 'menu',       'system/menu/index',      1, 0, 'C', '0', '0', 'system:menu:list',       'tree-table', 'admin', NOW(), '菜单管理菜单'),
          (103, '部门管理', 1, 4, 'dept',       'system/dept/index',      1, 0, 'C', '0', '0', 'system:dept:list',       'tree',       'admin', NOW(), '部门管理菜单'),
          (104, '岗位管理', 1, 5, 'post',       'system/post/index',      1, 0, 'C', '0', '0', 'system:post:list',       'post',       'admin', NOW(), '岗位管理菜单'),
          (105, '字典管理', 1, 6, 'dict',       'system/dict/index',      1, 0, 'C', '0', '0', 'system:dict:list',       'dict',       'admin', NOW(), '字典管理菜单'),
          (106, '参数设置', 1, 7, 'config',     'system/config/index',    1, 0, 'C', '0', '0', 'system:config:list',     'edit',       'admin', NOW(), '参数设置菜单'),
          (107, '通知公告', 1, 8, 'notice',     'system/notice/index',    1, 0, 'C', '0', '0', 'system:notice:list',     'message',    'admin', NOW(), '通知公告菜单'),
          (108, '日志管理', 1, 9, 'log',        NULL,                      1, 0, 'M', '0', '0', '',                       'log',        'admin', NOW(), '日志管理目录'),
          /* 系统监控 二级菜单 */
          (109, '在线用户', 2, 1, 'online',          'monitor/online/index',          1, 0, 'C', '0', '0', 'monitor:online:list',          'online',     'admin', NOW(), '在线用户菜单'),
          (110, '定时任务', 2, 2, 'job',             'monitor/job/index',             1, 0, 'C', '0', '0', 'monitor:job:list',             'job',        'admin', NOW(), '定时任务菜单'),
          (111, '数据监控', 2, 3, 'druid',           'monitor/druid/index',           1, 0, 'C', '0', '0', 'monitor:druid:list',           'druid',      'admin', NOW(), '数据监控菜单'),
          (112, '服务监控', 2, 4, 'server',          'monitor/server/index',          1, 0, 'C', '0', '0', 'monitor:server:list',          'server',     'admin', NOW(), '服务监控菜单'),
          (113, '缓存监控', 2, 5, 'cache',           'monitor/cache/index',           1, 0, 'C', '0', '0', 'monitor:cache:list',           'redis',      'admin', NOW(), '缓存监控菜单'),
          (114, '缓存列表', 2, 6, 'cacheList',       'monitor/cache/list',            1, 0, 'C', '0', '0', 'monitor:cache:list',           'redis-list', 'admin', NOW(), '缓存列表菜单'),
          (120, '传输加密', 2, 7, 'transportCrypto', 'monitor/transportCrypto/index', 1, 0, 'C', '0', '0', 'monitor:transportCrypto:list', 'chart',      'admin', NOW(), '传输加密监控菜单'),
          /* 系统工具 二级菜单 */
          (115, '表单构建', 3, 1, 'build',   'tool/build/index',   1, 0, 'C', '0', '0', 'tool:build:list',   'build',   'admin', NOW(), '表单构建菜单'),
          (116, '代码生成', 3, 2, 'gen',     'tool/gen/index',     1, 0, 'C', '0', '0', 'tool:gen:list',     'code',    'admin', NOW(), '代码生成菜单'),
          (117, '系统接口', 3, 3, 'swagger', 'tool/swagger/index', 1, 0, 'C', '0', '0', 'tool:swagger:list', 'swagger', 'admin', NOW(), '系统接口菜单'),
          /* 日志管理 三级菜单 */
          (500, '操作日志', 108, 1, 'operlog',    'monitor/operlog/index',    1, 0, 'C', '0', '0', 'monitor:operlog:list',    'form',       'admin', NOW(), '操作日志菜单'),
          (501, '登录日志', 108, 2, 'logininfor', 'monitor/logininfor/index', 1, 0, 'C', '0', '0', 'monitor:logininfor:list', 'logininfor', 'admin', NOW(), '登录日志菜单'),
          /* 用户管理按钮 */
          (1000, '用户查询', 100, 1, '', '', 1, 0, 'F', '0', '0', 'system:user:query', '#', 'admin', NOW(), ''),
          (1001, '用户新增', 100, 2, '', '', 1, 0, 'F', '0', '0', 'system:user:add', '#', 'admin', NOW(), ''),
          (1002, '用户修改', 100, 3, '', '', 1, 0, 'F', '0', '0', 'system:user:edit', '#', 'admin', NOW(), ''),
          (1003, '用户删除', 100, 4, '', '', 1, 0, 'F', '0', '0', 'system:user:remove', '#', 'admin', NOW(), ''),
          (1004, '用户导出', 100, 5, '', '', 1, 0, 'F', '0', '0', 'system:user:export', '#', 'admin', NOW(), ''),
          (1005, '用户导入', 100, 6, '', '', 1, 0, 'F', '0', '0', 'system:user:import', '#', 'admin', NOW(), ''),
          (1006, '重置密码', 100, 7, '', '', 1, 0, 'F', '0', '0', 'system:user:resetPwd', '#', 'admin', NOW(), ''),
          /* 角色管理按钮 */
          (1007, '角色查询', 101, 1, '', '', 1, 0, 'F', '0', '0', 'system:role:query', '#', 'admin', NOW(), ''),
          (1008, '角色新增', 101, 2, '', '', 1, 0, 'F', '0', '0', 'system:role:add', '#', 'admin', NOW(), ''),
          (1009, '角色修改', 101, 3, '', '', 1, 0, 'F', '0', '0', 'system:role:edit', '#', 'admin', NOW(), ''),
          (1010, '角色删除', 101, 4, '', '', 1, 0, 'F', '0', '0', 'system:role:remove', '#', 'admin', NOW(), ''),
          (1011, '角色导出', 101, 5, '', '', 1, 0, 'F', '0', '0', 'system:role:export', '#', 'admin', NOW(), ''),
          /* 菜单管理按钮 */
          (1012, '菜单查询', 102, 1, '', '', 1, 0, 'F', '0', '0', 'system:menu:query', '#', 'admin', NOW(), ''),
          (1013, '菜单新增', 102, 2, '', '', 1, 0, 'F', '0', '0', 'system:menu:add', '#', 'admin', NOW(), ''),
          (1014, '菜单修改', 102, 3, '', '', 1, 0, 'F', '0', '0', 'system:menu:edit', '#', 'admin', NOW(), ''),
          (1015, '菜单删除', 102, 4, '', '', 1, 0, 'F', '0', '0', 'system:menu:remove', '#', 'admin', NOW(), ''),
          /* 部门管理按钮 */
          (1016, '部门查询', 103, 1, '', '', 1, 0, 'F', '0', '0', 'system:dept:query', '#', 'admin', NOW(), ''),
          (1017, '部门新增', 103, 2, '', '', 1, 0, 'F', '0', '0', 'system:dept:add', '#', 'admin', NOW(), ''),
          (1018, '部门修改', 103, 3, '', '', 1, 0, 'F', '0', '0', 'system:dept:edit', '#', 'admin', NOW(), ''),
          (1019, '部门删除', 103, 4, '', '', 1, 0, 'F', '0', '0', 'system:dept:remove', '#', 'admin', NOW(), ''),
          /* 岗位管理按钮 */
          (1020, '岗位查询', 104, 1, '', '', 1, 0, 'F', '0', '0', 'system:post:query', '#', 'admin', NOW(), ''),
          (1021, '岗位新增', 104, 2, '', '', 1, 0, 'F', '0', '0', 'system:post:add', '#', 'admin', NOW(), ''),
          (1022, '岗位修改', 104, 3, '', '', 1, 0, 'F', '0', '0', 'system:post:edit', '#', 'admin', NOW(), ''),
          (1023, '岗位删除', 104, 4, '', '', 1, 0, 'F', '0', '0', 'system:post:remove', '#', 'admin', NOW(), ''),
          (1024, '岗位导出', 104, 5, '', '', 1, 0, 'F', '0', '0', 'system:post:export', '#', 'admin', NOW(), ''),
          /* 字典管理按钮 */
          (1025, '字典查询', 105, 1, '', '', 1, 0, 'F', '0', '0', 'system:dict:query', '#', 'admin', NOW(), ''),
          (1026, '字典新增', 105, 2, '', '', 1, 0, 'F', '0', '0', 'system:dict:add', '#', 'admin', NOW(), ''),
          (1027, '字典修改', 105, 3, '', '', 1, 0, 'F', '0', '0', 'system:dict:edit', '#', 'admin', NOW(), ''),
          (1028, '字典删除', 105, 4, '', '', 1, 0, 'F', '0', '0', 'system:dict:remove', '#', 'admin', NOW(), ''),
          (1029, '字典导出', 105, 5, '', '', 1, 0, 'F', '0', '0', 'system:dict:export', '#', 'admin', NOW(), ''),
          /* 参数设置按钮 */
          (1030, '参数查询', 106, 1, '', '', 1, 0, 'F', '0', '0', 'system:config:query', '#', 'admin', NOW(), ''),
          (1031, '参数新增', 106, 2, '', '', 1, 0, 'F', '0', '0', 'system:config:add', '#', 'admin', NOW(), ''),
          (1032, '参数修改', 106, 3, '', '', 1, 0, 'F', '0', '0', 'system:config:edit', '#', 'admin', NOW(), ''),
          (1033, '参数删除', 106, 4, '', '', 1, 0, 'F', '0', '0', 'system:config:remove', '#', 'admin', NOW(), ''),
          (1034, '参数导出', 106, 5, '', '', 1, 0, 'F', '0', '0', 'system:config:export', '#', 'admin', NOW(), ''),
          /* 通知公告按钮 */
          (1035, '公告查询', 107, 1, '', '', 1, 0, 'F', '0', '0', 'system:notice:query', '#', 'admin', NOW(), ''),
          (1036, '公告新增', 107, 2, '', '', 1, 0, 'F', '0', '0', 'system:notice:add', '#', 'admin', NOW(), ''),
          (1037, '公告修改', 107, 3, '', '', 1, 0, 'F', '0', '0', 'system:notice:edit', '#', 'admin', NOW(), ''),
          (1038, '公告删除', 107, 4, '', '', 1, 0, 'F', '0', '0', 'system:notice:remove', '#', 'admin', NOW(), ''),
          /* 操作日志按钮 */
          (1039, '操作查询', 500, 1, '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:query', '#', 'admin', NOW(), ''),
          (1040, '操作删除', 500, 2, '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:remove', '#', 'admin', NOW(), ''),
          (1041, '日志导出', 500, 3, '', '', 1, 0, 'F', '0', '0', 'monitor:operlog:export', '#', 'admin', NOW(), ''),
          /* 登录日志按钮 */
          (1042, '登录查询', 501, 1, '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:query', '#', 'admin', NOW(), ''),
          (1043, '登录删除', 501, 2, '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:remove', '#', 'admin', NOW(), ''),
          (1044, '日志导出', 501, 3, '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:export', '#', 'admin', NOW(), ''),
          (1045, '账户解锁', 501, 4, '', '', 1, 0, 'F', '0', '0', 'monitor:logininfor:unlock', '#', 'admin', NOW(), ''),
          /* 在线用户按钮 */
          (1046, '在线查询', 109, 1, '', '', 1, 0, 'F', '0', '0', 'monitor:online:query', '#', 'admin', NOW(), ''),
          (1047, '批量强退', 109, 2, '', '', 1, 0, 'F', '0', '0', 'monitor:online:batchLogout', '#', 'admin', NOW(), ''),
          (1048, '单条强退', 109, 3, '', '', 1, 0, 'F', '0', '0', 'monitor:online:forceLogout', '#', 'admin', NOW(), ''),
          /* 定时任务按钮 */
          (1049, '任务查询', 110, 1, '', '', 1, 0, 'F', '0', '0', 'monitor:job:query', '#', 'admin', NOW(), ''),
          (1050, '任务新增', 110, 2, '', '', 1, 0, 'F', '0', '0', 'monitor:job:add', '#', 'admin', NOW(), ''),
          (1051, '任务修改', 110, 3, '', '', 1, 0, 'F', '0', '0', 'monitor:job:edit', '#', 'admin', NOW(), ''),
          (1052, '任务删除', 110, 4, '', '', 1, 0, 'F', '0', '0', 'monitor:job:remove', '#', 'admin', NOW(), ''),
          (1053, '状态修改', 110, 5, '', '', 1, 0, 'F', '0', '0', 'monitor:job:changeStatus', '#', 'admin', NOW(), ''),
          (1054, '任务导出', 110, 6, '', '', 1, 0, 'F', '0', '0', 'monitor:job:export', '#', 'admin', NOW(), ''),
          /* 代码生成按钮 */
          (1055, '生成查询', 116, 1, '', '', 1, 0, 'F', '0', '0', 'tool:gen:query', '#', 'admin', NOW(), ''),
          (1056, '生成修改', 116, 2, '', '', 1, 0, 'F', '0', '0', 'tool:gen:edit', '#', 'admin', NOW(), ''),
          (1057, '生成删除', 116, 3, '', '', 1, 0, 'F', '0', '0', 'tool:gen:remove', '#', 'admin', NOW(), ''),
          (1058, '导入代码', 116, 4, '', '', 1, 0, 'F', '0', '0', 'tool:gen:import', '#', 'admin', NOW(), ''),
          (1059, '预览代码', 116, 5, '', '', 1, 0, 'F', '0', '0', 'tool:gen:preview', '#', 'admin', NOW(), ''),
          (1060, '生成代码', 116, 6, '', '', 1, 0, 'F', '0', '0', 'tool:gen:code',    '#', 'admin', NOW(), '');
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

    # ============== sys_config（RuoYi 8 条默认配置，修复验证码开关失效） ==============
    # 原 0003 漏了 sys_config 的种子数据，导致 init_cache_sys_config_services 把空表
    # 灌进 Redis，登录接口读 captcha_enabled=None → None == 'true' 为 False → 跳过验证码
    op.execute("""
        INSERT IGNORE INTO sys_config (config_id, config_name, config_key, config_value, config_type, create_by, create_time, update_by, update_time, remark)
        VALUES
          (1, '主框架页-默认皮肤样式名称',         'sys.index.skinName',              'skin-blue',     'Y', 'admin', NOW(), '', NULL, '蓝色 skin-blue、绿色 skin-green、紫色 skin-purple、红色 skin-red、黄色 skin-yellow'),
          (2, '用户管理-账号初始密码',             'sys.user.initPassword',           '123456',        'Y', 'admin', NOW(), '', NULL, '初始化密码 123456'),
          (3, '主框架页-侧边栏主题',               'sys.index.sideTheme',             'theme-dark',    'Y', 'admin', NOW(), '', NULL, '深色主题theme-dark，浅色主题theme-light'),
          (4, '账号自助-验证码开关',               'sys.account.captchaEnabled',      'true',          'Y', 'admin', NOW(), '', NULL, '是否开启验证码功能（true开启，false关闭）'),
          (5, '账号自助-是否开启用户注册功能',     'sys.account.registerUser',        'false',         'Y', 'admin', NOW(), '', NULL, '是否开启注册用户功能（true开启，false关闭）'),
          (6, '用户登录-黑名单列表',               'sys.login.blackIPList',           '',              'Y', 'admin', NOW(), '', NULL, '设置登录IP黑名单限制，多个匹配项以;分隔，支持匹配（*通配、网段）'),
          (7, '用户管理-初始密码修改策略',         'sys.account.initPasswordModify',  '1',             'Y', 'admin', NOW(), '', NULL, '0：初始密码修改策略关闭，没有任何提示，1：提醒用户，如果未修改初始密码，则在登录时就会提醒修改密码对话框'),
          (8, '用户管理-账号密码更新周期',         'sys.account.passwordValidateDays','0',             'Y', 'admin', NOW(), '', NULL, '密码更新周期（填写数字，数据初始化值为0不限制，若修改必须为大于0小于365的正整数），如果超过这个周期登录系统时，则在登录时就会提醒修改密码对话框');
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

    # ============== sys_dict_data（精简常用值） ==============
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
          /* contract_type */
          (100, 1, '业务付款审批单', 'payment', 'contract_type', '', '', 'N', '0', 'admin', NOW(), '含付款审批的合同'),
          (101, 2, '业务审批单', 'business', 'contract_type', '', '', 'Y', '0', 'admin', NOW(), '普通业务审批'),
          /* business_line */
          (102, 1, '景区发行', 'scenic', 'business_line', '', '', 'N', '0', 'admin', NOW(), '景区相关业务'),
          (103, 2, '数字出版', 'digital', 'business_line', '', '', 'N', '0', 'admin', NOW(), '数字内容业务'),
          (104, 3, '物流仓储', 'logistics', 'business_line', '', '', 'N', '0', 'admin', NOW(), '物流仓储业务'),
          /* channel_type */
          (105, 1, '美团到综', 'meituan', 'channel_type', '', '', 'N', '0', 'admin', NOW(), '美团综合业务'),
          (106, 2, '抖音生活服务', 'douyin', 'channel_type', '', '', 'N', '0', 'admin', NOW(), '抖音本地生活'),
          (107, 3, '携程商旅', 'ctrip', 'channel_type', '', '', 'N', '0', 'admin', NOW(), '携程商旅'),
          (108, 4, '同程旅行', 'tongcheng', 'channel_type', '', '', 'N', '0', 'admin', NOW(), '同程旅行'),
          /* customer_type */
          (109, 1, '景区', 'scenic', 'customer_type', '', '', 'N', '0', 'admin', NOW(), '景区客户'),
          (110, 2, '酒店', 'hotel', 'customer_type', '', '', 'N', '0', 'admin', NOW(), '酒店客户'),
          (111, 3, '旅行社', 'agency', 'customer_type', '', '', 'N', '0', 'admin', NOW(), '旅行社客户'),
          (112, 4, '出版社', 'publish', 'customer_type', '', '', 'N', '0', 'admin', NOW(), '出版社客户');
    """)

    # ============================================================
    # Part 2: biz_* 业务种子数据
    # ============================================================

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

    # PLACEHOLDER_AI_MENU
    op.execute("""
        INSERT IGNORE INTO sys_menu
          (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
        VALUES
          (130, 'AI 管理', 0, 14, 'ai', NULL, 1, 0, 'M', '0', '0', '', 'magic-stick', 'admin', NOW(), 'AI 管理目录'),
          (131, 'AI 模型', 130, 1, 'ai/model', 'ai/model/index', 1, 0, 'C', '0', '0', 'ai:model:list', 'model', 'admin', NOW(), 'AI 模型菜单'),
          (132, 'AI 对话', 130, 2, 'ai/chat', 'ai/chat/index', 1, 0, 'C', '0', '0', '', 'chat', 'admin', NOW(), 'AI 对话菜单');
    """)

    # AI 模型 按钮 5 个
    op.execute("""
        INSERT IGNORE INTO sys_menu
          (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
        VALUES
          (2000, '模型查询', 131, 1, '', '', 1, 0, 'F', '0', '0', 'ai:model:query',  '#', 'admin', NOW(), ''),
          (2001, '模型新增', 131, 2, '', '', 1, 0, 'F', '0', '0', 'ai:model:add',    '#', 'admin', NOW(), ''),
          (2002, '模型修改', 131, 3, '', '', 1, 0, 'F', '0', '0', 'ai:model:edit',   '#', 'admin', NOW(), ''),
          (2003, '模型删除', 131, 4, '', '', 1, 0, 'F', '0', '0', 'ai:model:remove', '#', 'admin', NOW(), ''),
          (2004, '模型导出', 131, 5, '', '', 1, 0, 'F', '0', '0', 'ai:model:export', '#', 'admin', NOW(), '');
    """)

    # AI 菜单权限分配（admin 全 8 项；其他角色仅目录+菜单+查询按钮）
    op.execute("""
        INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
          (1, 130), (1, 131), (1, 132),
          (1, 2000), (1, 2001), (1, 2002), (1, 2003), (1, 2004),
          (2, 130), (2, 131), (2, 132), (2, 2000),
          (3, 130), (3, 131), (3, 132), (3, 2000),
          (4, 130), (4, 131), (4, 132), (4, 2000),
          (5, 130), (5, 131), (5, 132), (5, 2000),
          (6, 130), (6, 131), (6, 132), (6, 2000),
          (7, 130), (7, 131), (7, 132), (7, 2000),
          (8, 130), (8, 131), (8, 132), (8, 2000),
          (9, 130), (9, 131), (9, 132), (9, 2000);
    """)


def downgrade() -> None:
    """downgrade：清空种子数据（按依赖反向）"""
    # biz 业务数据（按依赖反向：operation → finance → invoice → channel → contract → customer）
    op.execute("DELETE FROM biz_operation;")
    op.execute("DELETE FROM biz_finance_entry;")
    op.execute("DELETE FROM biz_invoice;")
    op.execute("DELETE FROM biz_channel;")
    op.execute("DELETE FROM biz_contract;")
    op.execute("DELETE FROM biz_customer;")
    # sys 业务字典（dict_code >= 100）
    op.execute("DELETE FROM sys_dict_data WHERE dict_code >= 100;")
    op.execute("DELETE FROM sys_dict_type WHERE dict_id >= 100;")
    # sys config
    op.execute("DELETE FROM sys_config;")
    # sys 角色菜单（先清关联，再清角色）
    op.execute("DELETE FROM sys_role_menu WHERE menu_id IN (130, 131, 132, 2000, 2001, 2002, 2003, 2004);")
    op.execute("DELETE FROM sys_menu WHERE menu_id IN (130, 131, 132, 2000, 2001, 2002, 2003, 2004);")
    op.execute("DELETE FROM sys_role_menu;")
    op.execute("DELETE FROM sys_user_role WHERE user_id IN (101, 102, 103, 104, 105, 106, 107);")
    op.execute("DELETE FROM sys_user_role WHERE user_id = 1;")
    op.execute("DELETE FROM sys_user WHERE user_id IN (101, 102, 103, 104, 105, 106, 107);")
    op.execute("DELETE FROM sys_role WHERE role_id IN (3, 4, 5, 6, 7, 8, 9);")
    op.execute("DELETE FROM sys_menu WHERE menu_id IN (5, 6, 7, 8, 12, 13, 14, 15, 16);")
    op.execute("DELETE FROM sys_dept WHERE dept_id >= 100;")
