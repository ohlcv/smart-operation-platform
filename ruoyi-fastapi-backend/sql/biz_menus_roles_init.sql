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
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

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