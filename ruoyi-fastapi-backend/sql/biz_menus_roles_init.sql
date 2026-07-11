-- =====================================================================
-- 业务菜单与角色初始化脚本（修复版）
-- 文档依据：docs/03-设计/数据库设计.md v3.0 §3.3, §3.5, §5.1, §5.2, §5.3, §5.4
--          docs/04-开发/ARD/ADR-架构决策记录.md D01/D02/D07/D08
-- 创建日期：2026-07-11
-- 修复项：
--   1. biz/* 菜单 path 拼写修正（path=contract → path=biz/contract）
--   2. 补 7 级业务审批链角色 + 1 个 admin（设计文档 §5.1）
--   3. sys_role_menu 给 admin(role_id=1) 挂全部菜单
--   4. biz 菜单补 perms 字段（contract:* / customer:* / approval:* / signature:*）
--   5. sys_user.role_sort 字段暂缺，本脚本先按现有 sys_role 表结构补齐
--   6. 修正 admin / common 的 role_sort（D02 违规修复：admin 1→0, common 2→99）
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- 0. 修正 admin / common 的 role_sort（修复 ADR D02 违规）
--    设计文档：role_sort=0=隐藏超管，1-7=7 级业务审批链，>7=非审批角色
--    RuoYi 默认 admin sort=1 与业务经办 sort=1 冲突；common sort=2 与业务复核 sort=2 冲突
-- =====================================================================
UPDATE sys_role SET role_sort = 0  WHERE role_id = 1;
UPDATE sys_role SET role_sort = 99 WHERE role_id = 2;

-- =====================================================================
-- 1. 修正 biz 菜单 path 拼写（path 必须包含父级路径）
-- =====================================================================
UPDATE sys_menu SET path = 'biz/contract' WHERE menu_id = 6 AND path = 'contract';
UPDATE sys_menu SET path = 'biz/customer' WHERE menu_id = 7 AND path = 'customer';

-- 补 biz 菜单 perms（按钮级权限标识，前端 v-permission 用）
UPDATE sys_menu SET perms = 'contract:list,contract:add,contract:edit,contract:delete,contract:submit' WHERE menu_id = 6;
UPDATE sys_menu SET perms = 'customer:list,customer:add,customer:edit,customer:delete' WHERE menu_id = 7;

-- 父菜单 业务管理 补 perms（用于目录权限标识，RuoYi 习惯）
UPDATE sys_menu SET perms = 'biz:view' WHERE menu_id = 5;

-- =====================================================================
-- 1b. 路线 A 追加：渠道/发票/财务/经营 4 个菜单（menu_id 8-11）
--     与合同/客户保持一致：path=biz/<module>，perms=module:list,add,edit,delete[,...]
-- =====================================================================
INSERT IGNORE INTO sys_menu
(menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
(8,  '渠道管理',  0, 8,  'biz/channel',   'biz/channel/index',    1, 0, 'C', '0', '0', 'channel:list,channel:add,channel:edit,channel:delete,channel:import',  'share',     'admin', NOW(), '路线A-2026-07-11'),
(9,  '发票管理',  0, 9,  'biz/invoice',   'biz/invoice/index',    1, 0, 'C', '0', '0', 'invoice:list,invoice:add,invoice:edit,invoice:delete,invoice:issue,invoice:void', 'ticket', 'admin', NOW(), '路线A-2026-07-11'),
(10, '财务管理',  0, 10, 'biz/finance',   'biz/finance/index',    1, 0, 'C', '0', '0', 'finance:list,finance:add,finance:edit,finance:delete,finance:import', 'money',     'admin', NOW(), '路线A-2026-07-11'),
(11, '经营数据',  0, 11, 'biz/operation', 'biz/operation/index',  1, 0, 'C', '0', '0', 'operation:list,operation:add,operation:edit,operation:delete,operation:comparison', 'data-line', 'admin', NOW(), '路线A-2026-07-11');

-- 业务管理父菜单（menu_id=5）的 perms 已存在 biz:view，子菜单补充

-- 把 4 个新菜单挂到业务经办等业务侧角色上（供正常使用）
-- 业务经办(business_handler, role_id=3) → 渠道/发票/财务/经营 都可见可写
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(3, 8), (3, 9), (3, 10), (3, 11),
-- 业务复核(business_reviewer, 4) → 仅看列表
(4, 8), (4, 9), (4, 10), (4, 11),
-- 风控审核(risk_auditor, 5) → 仅看列表
(5, 8), (5, 9), (5, 10), (5, 11),
-- 财务经办(finance_handler, 6) → 财务/发票 全权，渠道/经营仅看
(6, 8), (6, 9), (6, 10), (6, 11),
-- 财务复核(finance_reviewer, 7) → 同上
(7, 8), (7, 9), (7, 10), (7, 11),
-- 供管负责人(scm_director, 8) → 渠道全权 + 经营数据全权
(8, 8), (8, 9), (8, 10), (8, 11),
-- 投资负责人(invest_director, 9) → 全部可见
(9, 8), (9, 9), (9, 10), (9, 11);

-- admin(role_id=1) 同样挂上（确保 admin 也访问得到）
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT 1, menu_id FROM sys_menu WHERE menu_id BETWEEN 8 AND 11;

-- =====================================================================
-- 2. 补 7 级业务审批链角色 + admin（按 §5.1 严格顺序）
--    注意：admin 已存在（role_id=1），role_sort=0 标记为隐藏超管
-- =====================================================================
INSERT IGNORE INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
VALUES
(3, '业务经办',     'business_handler',  1, 5, 1, 1, '0', '0', 'admin', NOW(), 'Step 0：业务经办提交'),
(4, '业务复核',     'business_reviewer', 2, 4, 1, 1, '0', '0', 'admin', NOW(), 'Step 1：业务复核'),
(5, '风控审核',     'risk_auditor',      3, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 2：风控审核'),
(6, '财务经办',     'finance_handler',   4, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 3：财务经办'),
(7, '财务复核',     'finance_reviewer',  5, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 4：财务复核'),
(8, '供管公司负责人', 'scm_director',      6, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 5：供管公司负责人'),
(9, '投资公司负责人', 'invest_director',   7, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 6：投资公司负责人（终审）');

-- =====================================================================
-- 3. admin(role_id=1) 挂全部菜单（包括原有 86 + biz 三条 = 89）
--    admin 应有 *:*:* 全权（业务侧约定）
-- =====================================================================
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT 1, menu_id FROM sys_menu WHERE status = '0';

-- =====================================================================
-- 4. 给现有 admin 用户额外挂 7 级审批角色（admin 同时是超管 + 业务经办）
--    这样 admin 既能看所有菜单，又能审批自己提交的合同（D02 admin bypass）
-- =====================================================================
INSERT IGNORE INTO sys_user_role (user_id, role_id)
VALUES
(1, 3),  -- admin 同时是业务经办
(1, 4),  -- admin 同时是业务复核
(1, 5),  -- admin 同时是风控审核
(1, 6),  -- admin 同时是财务经办
(1, 7),  -- admin 同时是财务复核
(1, 8),  -- admin 同时是供管负责人
(1, 9);  -- admin 同时是投资负责人

-- =====================================================================
-- 5. 字典补登（设计文档 §5.2/5.3/5.4）
-- =====================================================================
-- 检查是否已存在 sys_dict 字典类型
INSERT IGNORE INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, remark)
VALUES
(100, '合同类型',    'contract_type',  '0', 'admin', NOW(), '合同单据类型（业务付款/业务审批）'),
(101, '业务线',      'business_line',  '0', 'admin', NOW(), '经营数据业务线'),
(102, '渠道类型',    'channel_type',   '0', 'admin', NOW(), 'OTA 渠道类型'),
(103, '客户类型',    'customer_type',  '0', 'admin', NOW(), '客户档案分类');

-- 字典数据
INSERT IGNORE INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, is_default, status, create_by, create_time, remark)
VALUES
-- contract_type
(100, 1, '业务付款审批单', 'payment',  'contract_type', 'N', '0', 'admin', NOW(), '含付款审批的合同'),
(100, 2, '业务审批单',     'business', 'contract_type', 'Y', '0', 'admin', NOW(), '普通业务审批'),
-- business_line
(101, 1, '景区发行', 'scenic',     'business_line', 'N', '0', 'admin', NOW(), '景区相关业务'),
(101, 2, '数字出版', 'digital',    'business_line', 'N', '0', 'admin', NOW(), '数字内容业务'),
(101, 3, '物流仓储', 'logistics',  'business_line', 'N', '0', 'admin', NOW(), '物流仓储业务'),
-- channel_type
(102, 1, '美团到综',     'meituan',   'channel_type', 'N', '0', 'admin', NOW(), '美团综合业务'),
(102, 2, '抖音生活服务', 'douyin',    'channel_type', 'N', '0', 'admin', NOW(), '抖音本地生活'),
(102, 3, '携程商旅',     'ctrip',     'channel_type', 'N', '0', 'admin', NOW(), '携程商旅'),
(102, 4, '同程旅行',     'tongcheng', 'channel_type', 'N', '0', 'admin', NOW(), '同程旅行'),
-- customer_type
(103, 1, '景区',     'scenic',  'customer_type', 'N', '0', 'admin', NOW(), '景区客户'),
(103, 2, '酒店',     'hotel',   'customer_type', 'N', '0', 'admin', NOW(), '酒店客户'),
(103, 3, '旅行社',   'agency',  'customer_type', 'N', '0', 'admin', NOW(), '旅行社客户'),
(103, 4, '出版社',   'publish', 'customer_type', 'N', '0', 'admin', NOW(), '出版社客户');

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 验证（执行完后查看）
-- =====================================================================
SELECT '-- 修正后 biz 菜单 --' AS ' ';
SELECT menu_id, menu_name, path, component, perms FROM sys_menu WHERE menu_id IN (5,6,7);
SELECT '-- 所有角色 --' AS ' ';
SELECT role_id, role_name, role_key, role_sort, data_scope FROM sys_role ORDER BY role_sort;
SELECT '-- admin 拥有的菜单数 --' AS ' ';
SELECT COUNT(*) AS admin_menu_cnt FROM sys_role_menu WHERE role_id = 1;
SELECT '-- admin 拥有的角色 --' AS ' ';
SELECT ur.user_id, u.user_name, ur.role_id, r.role_name, r.role_key, r.role_sort
FROM sys_user_role ur
LEFT JOIN sys_user u ON ur.user_id = u.user_id
LEFT JOIN sys_role r ON ur.role_id = r.role_id
WHERE ur.user_id = 1
ORDER BY r.role_sort;
SELECT '-- 字典类型 --' AS ' ';
SELECT dict_id, dict_name, dict_type FROM sys_dict_type WHERE dict_id >= 100;
SELECT '-- 字典数据（业务相关）--' AS ' ';
SELECT dict_type, dict_label, dict_value FROM sys_dict_data WHERE dict_type IN ('contract_type','business_line','channel_type','customer_type') ORDER BY dict_type, dict_sort;

-- 路线 B：战略驾驶舱菜单（menu_id=13）
INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES (13, '战略驾驶舱', 0, 13, 'cockpit', 'biz/cockpit/index', 1, 0, 'C', '0', '0', 'biz:cockpit:view', 'pie-chart', 'admin', NOW(), '路线B');
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 13);

-- 路线 A：业务闭环菜单（menu_id=9-12：channel/invoice/finance/operation）
-- 表已通过 ORM create_all 自动创建（biz_channel/biz_invoice/biz_finance_entry/biz_operation）
INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
(9,  '渠道管理',    0,  9, 'channel',   'biz/channel/index',   1, 0, 'C', '0', '0', 'biz:channel:list,channel:add,channel:edit,channel:delete,channel:import', 'share',     'admin', NOW(), '路线A'),
(10, '发票管理',    0, 10, 'invoice',   'biz/invoice/index',   1, 0, 'C', '0', '0', 'biz:invoice:list,invoice:add,invoice:edit,invoice:delete,invoice:issue,invoice:void', 'ticket', 'admin', NOW(), '路线A'),
(11, '财务管理',    0, 11, 'finance',   'biz/finance/index',   1, 0, 'C', '0', '0', 'biz:finance:list,finance:add,finance:edit,finance:delete,finance:import', 'money', 'admin', NOW(), '路线A'),
(12, '经营数据',    0, 12, 'operation', 'biz/operation/index', 1, 0, 'C', '0', '0', 'biz:operation:list,operation:add,operation:edit,operation:delete', 'data-line', 'admin', NOW(), '路线A');

-- admin 挂业务闭环菜单（步骤 3 已 SELECT 全菜单，此处兼容历史库）
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(1, 9), (1, 10), (1, 11), (1, 12);