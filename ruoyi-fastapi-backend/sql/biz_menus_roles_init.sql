-- =====================================================================
-- 业务菜单与角色初始化脚本（v4.0 重构版）
-- 文档依据：docs/03-设计/数据库设计.md v3.0 §3.3, §3.5, §5.1, §5.2, §5.3, §5.4
--          docs/04-开发/ARD/ADR-架构决策记录.md D01/D02/D07/D08
-- 创建日期：2026-07-11
-- 重构日期：2026-07-12
-- 重构说明：
--   1. 彻底消除 menu_id=8 争用：原脚本行46 INSERT menu_id=8（渠道，parent_id=0）与
--      approval_init.sql（menu_id=8 审批中心，parent_id=5）冲突，
--      先跑的行赢，后跑的永远是审批中心，渠道管理丢失。
--      改为 UPDATE 模式：menu_id=12 修正 parent_id、icon、path，不再依赖 DELETE。
--   2. 弃用 DELETE+INSERT：历史库中 DELETE sys_menu 会破坏已挂角色数据，
--      改为 INSERT IGNORE（已存在则跳过）+ 针对性 UPDATE（修正错误字段）。
--   3. 全部图标持久化到 SQL，重启容器不丢失。
--   4. 删除 role_menu SELECT BETWEEN 9-12（误取）→ 修正为 14-16。
-- 维护原则：幂等（重复执行安全），必须在 approval_init.sql 之前执行。
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- 0. 修正 admin / common 的 role_sort（修复 ADR D02 违规）
--    设计文档：role_sort=0=隐藏超管，1-7=7 级业务审批链，>7=非审批角色
-- =====================================================================
UPDATE sys_role SET role_sort = 0  WHERE role_id = 1;
UPDATE sys_role SET role_sort = 99 WHERE role_id = 2;

-- =====================================================================
-- 1. 修正合同/客户 path（含父级 biz/ 前缀）
--    同时修正 合同管理 parent_id=5、icon='list'
--              客户档案  parent_id=5、icon='peoples'（已是）
-- =====================================================================
UPDATE sys_menu SET path = 'biz/contract', parent_id = 5, icon = 'list'
  WHERE menu_id = 6 AND (path != 'biz/contract' OR parent_id != 5 OR icon != 'list');
UPDATE sys_menu SET path = 'biz/customer', parent_id = 5
  WHERE menu_id = 7 AND (path != 'biz/customer' OR parent_id != 5);

-- =====================================================================
-- 2. 修正 业务管理 parent_id=5、icon='shopping'、path='biz'
--    补 perms（目录权限标识）
-- =====================================================================
UPDATE sys_menu SET parent_id = 0, icon = 'shopping', path = 'biz',
  perms = COALESCE(NULLIF(perms, ''), 'biz:view')
  WHERE menu_id = 5 AND menu_type = 'M';

-- =====================================================================
-- 3. 路线 A：4 个子菜单（渠道/发票/财务/经营）
--    menu_id=12 已在 DB 中（approval_init.sql 先 INSERT），用 UPDATE 修正
--    menu_id=14/15/16 INSERT IGNORE 创建
--    icon 全部持久化（重启容器不丢失）
-- =====================================================================

-- 3a) menu_id=12（渠道管理）：修正 parent_id=5、icon='link'、path='biz/channel'、perms
UPDATE sys_menu
   SET parent_id = 5,
       icon = 'link',
       path = 'biz/channel',
       perms = 'channel:list,channel:add,channel:edit,channel:delete,channel:import',
       menu_type = 'C',
       visible = '0',
       status = '0',
       is_frame = 1,
       is_cache = 0,
       order_num = 9,
       component = 'biz/channel/index'
 WHERE menu_id = 12
   AND (parent_id != 5 OR icon != 'link' OR path != 'biz/channel');

-- 3b) menu_id=14（发票管理）：INSERT IGNORE（已存在则跳过，再执行 UPDATE 修正）
INSERT IGNORE INTO sys_menu
  (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
  (14, '发票管理', 5, 10, 'biz/invoice', 'biz/invoice/index', 1, 0, 'C', '0', '0',
   'invoice:list,invoice:add,invoice:edit,invoice:delete,invoice:issue,invoice:void',
   'pdf', 'admin', NOW(), '路线A');
UPDATE sys_menu
   SET parent_id = 5, icon = 'pdf', path = 'biz/invoice', perms = 'invoice:list,invoice:add,invoice:edit,invoice:delete,invoice:issue,invoice:void',
       order_num = 10, component = 'biz/invoice/index', menu_type = 'C'
 WHERE menu_id = 14;

-- 3c) menu_id=15（财务管理）：INSERT IGNORE + UPDATE
INSERT IGNORE INTO sys_menu
  (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
  (15, '财务管理', 5, 11, 'biz/finance', 'biz/finance/index', 1, 0, 'C', '0', '0',
   'finance:list,finance:add,finance:edit,finance:delete,finance:import',
   'money', 'admin', NOW(), '路线A');
UPDATE sys_menu
   SET parent_id = 5, icon = 'money', path = 'biz/finance', perms = 'finance:list,finance:add,finance:edit,finance:delete,finance:import',
       order_num = 11, component = 'biz/finance/index', menu_type = 'C'
 WHERE menu_id = 15;

-- 3d) menu_id=16（经营数据）：INSERT IGNORE + UPDATE
INSERT IGNORE INTO sys_menu
  (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
  (16, '经营数据', 5, 12, 'biz/operation', 'biz/operation/index', 1, 0, 'C', '0', '0',
   'operation:list,operation:add,operation:edit,operation:delete,operation:comparison',
   'chart', 'admin', NOW(), '路线A');
UPDATE sys_menu
   SET parent_id = 5, icon = 'chart', path = 'biz/operation', perms = 'operation:list,operation:add,operation:edit,operation:delete,operation:comparison',
       order_num = 12, component = 'biz/operation/index', menu_type = 'C'
 WHERE menu_id = 16;

-- =====================================================================
-- 4. 7 个业务审批角色 + admin 全部挂上路线 A 4 个菜单
--    幂等：INSERT IGNORE，已挂则跳过
-- =====================================================================
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
  (1, 12), (1, 14), (1, 15), (1, 16),  -- admin
  (3, 12), (3, 14), (3, 15), (3, 16),  -- 业务经办
  (4, 12), (4, 14), (4, 15), (4, 16),  -- 业务复核
  (5, 12), (5, 14), (5, 15), (5, 16),  -- 风控审核
  (6, 12), (6, 14), (6, 15), (6, 16),  -- 财务经办
  (7, 12), (7, 14), (7, 15), (7, 16),  -- 财务复核
  (8, 12), (8, 14), (8, 15), (8, 16),  -- 供管负责人
  (9, 12), (9, 14), (9, 15), (9, 16); -- 投资负责人

-- =====================================================================
-- 5. 补 7 级业务审批链角色（按 §5.1 严格顺序）
--    admin(role_id=1) 已存在，role_sort=0 标记为隐藏超管
-- =====================================================================
INSERT IGNORE INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
VALUES
  (3,  '业务经办',     'business_handler',   1, 5, 1, 1, '0', '0', 'admin', NOW(), 'Step 0：业务经办提交'),
  (4,  '业务复核',     'business_reviewer',  2, 4, 1, 1, '0', '0', 'admin', NOW(), 'Step 1：业务复核'),
  (5,  '风控审核',     'risk_auditor',       3, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 2：风控审核'),
  (6,  '财务经办',     'finance_handler',    4, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 3：财务经办'),
  (7,  '财务复核',     'finance_reviewer',   5, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 4：财务复核'),
  (8,  '供管公司负责人', 'scm_director',       6, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 5：供管公司负责人'),
  (9,  '投资公司负责人', 'invest_director',    7, 1, 1, 1, '0', '0', 'admin', NOW(), 'Step 6：投资公司负责人（终审）');

-- =====================================================================
-- 6. admin 挂全部菜单（幂等）
-- =====================================================================
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
  SELECT 1, menu_id FROM sys_menu WHERE status = '0' AND del_flag = '0';

-- =====================================================================
-- 7. admin 额外挂 7 级审批角色（admin 同时是超管 + 业务经办，支持自己提交审批）
-- =====================================================================
INSERT IGNORE INTO sys_user_role (user_id, role_id)
  VALUES (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9);

-- =====================================================================
-- 8. 字典补登（设计文档 §5.2/5.3/5.4）
-- =====================================================================
INSERT IGNORE INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, remark)
VALUES
  (100, '合同类型',    'contract_type',  '0', 'admin', NOW(), '合同单据类型（业务付款/业务审批）'),
  (101, '业务线',      'business_line',  '0', 'admin', NOW(), '经营数据业务线'),
  (102, '渠道类型',    'channel_type',   '0', 'admin', NOW(), 'OTA 渠道类型'),
  (103, '客户类型',    'customer_type',  '0', 'admin', NOW(), '客户档案分类');

INSERT IGNORE INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, is_default, status, create_by, create_time, remark)
VALUES
  -- contract_type
  (100, 1, '业务付款审批单', 'payment',  'contract_type', 'N', '0', 'admin', NOW(), '含付款审批的合同'),
  (100, 2, '业务审批单',     'business', 'contract_type', 'Y', '0', 'admin', NOW(), '普通业务审批'),
  -- business_line
  (101, 1, '景区发行', 'scenic',    'business_line', 'N', '0', 'admin', NOW(), '景区相关业务'),
  (101, 2, '数字出版', 'digital',   'business_line', 'N', '0', 'admin', NOW(), '数字内容业务'),
  (101, 3, '物流仓储', 'logistics', 'business_line', 'N', '0', 'admin', NOW(), '物流仓储业务'),
  -- channel_type
  (102, 1, '美团到综',     'meituan',   'channel_type', 'N', '0', 'admin', NOW(), '美团综合业务'),
  (102, 2, '抖音生活服务', 'douyin',    'channel_type', 'N', '0', 'admin', NOW(), '抖音本地生活'),
  (102, 3, '携程商旅',     'ctrip',     'channel_type', 'N', '0', 'admin', NOW(), '携程商旅'),
  (102, 4, '同程旅行',     'tongcheng', 'channel_type', 'N', '0', 'admin', NOW(), '同程旅行'),
  -- customer_type
  (103, 1, '景区',   'scenic',  'customer_type', 'N', '0', 'admin', NOW(), '景区客户'),
  (103, 2, '酒店',   'hotel',   'customer_type', 'N', '0', 'admin', NOW(), '酒店客户'),
  (103, 3, '旅行社', 'agency',  'customer_type', 'N', '0', 'admin', NOW(), '旅行社客户'),
  (103, 4, '出版社', 'publish', 'customer_type', 'N', '0', 'admin', NOW(), '出版社客户');

-- =====================================================================
-- 9. 仪表盘菜单（menu_id=13）
--    icon='dashboard' 持久化，重启容器不丢失
-- =====================================================================
INSERT IGNORE INTO sys_menu
  (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
  (13, '仪表盘', 0, 13, '/dashboard', 'cockpit/dashboard', 1, 0, 'C', '0', '0',
   'biz:dashboard:view', 'dashboard', 'admin', NOW(), '仪表盘顶级路由 /dashboard (v3.6 嵌入 Layout + 支持 ?fullscreen=1 全屏)');
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 13);

-- v3.1 hotfix：顶级菜单 path 必须加前导 '/'（否则 vue-router 匹配失败）
UPDATE sys_menu SET path = '/dashboard'
  WHERE menu_id = 13 AND path NOT LIKE '/%';

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 验证（执行完后查看）
-- =====================================================================
SELECT '-- 业务管理目录及子菜单 --' AS ' ';
SELECT menu_id, menu_name, parent_id, path, icon, perms FROM sys_menu WHERE menu_id IN (5, 6, 7, 12, 14, 15, 16, 13) ORDER BY menu_id;

SELECT '-- 所有角色 --' AS ' ';
SELECT role_id, role_name, role_key, role_sort FROM sys_role ORDER BY role_sort;

SELECT '-- admin 拥有的菜单数 --' AS ' ';
SELECT COUNT(*) AS admin_menu_cnt FROM sys_role_menu WHERE role_id = 1;

SELECT '-- 字典类型 --' AS ' ';
SELECT dict_id, dict_name, dict_type FROM sys_dict_type WHERE dict_id >= 100;

SELECT '-- 路线 A 4 菜单已挂角色的数量 --' AS ' ';
SELECT m.menu_id, m.menu_name,
       COUNT(rm.role_id) AS role_count
  FROM sys_menu m
  LEFT JOIN sys_role_menu rm ON rm.menu_id = m.menu_id
 WHERE m.menu_id IN (12, 14, 15, 16)
 GROUP BY m.menu_id, m.menu_name
 ORDER BY m.menu_id;
