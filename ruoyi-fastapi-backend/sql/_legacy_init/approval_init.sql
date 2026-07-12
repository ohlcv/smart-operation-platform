-- =====================================================================
-- 审批链路初始化脚本（v2.8）
-- 文档依据：docs/03-设计/数据库设计.md §3.2 + §四 §4.2
--          docs/03-设计/权限模型设计.md §三 §3.2-§3.5
--          docs/04-开发/ARD/ADR-架构决策记录.md D02（role_sort 规范）
-- 数据库：MySQL 8.0
-- 创建日期：2026-07-11
-- 维护原则：
--   1. 本脚本是增量脚本，幂等（重复执行不报错）
--   2. 必须在 biz_menus_roles_init.sql 之后执行（依赖 §0/§2 已有的 7 级审批角色）
--   3. 字段全部 IF NOT EXISTS / INSERT IGNORE，不会破坏已有数据
-- 4. 7 个测试用户密码均为 `123456`（bcrypt 哈希值用 SQL 默认 admin 同款便于验证）
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- 0. sys_user 补 signature 字段（数据库设计 §3.2 line 174）
--    用于电子签名审批快照（biz_approval.signature_snapshot 来源）
-- =====================================================================
-- v3.7.2 修复：原版用 ADD COLUMN IF NOT EXISTS 仅 MySQL 8.0.29+ 支持，
--   低于该版本（如 8.0.23 / 8.0.27 等）会报 1064 语法错，
--   且本项目 docker run 拉的是 mysql:8.0 浮动 tag，版本不可控。
--   改用 INFORMATION_SCHEMA 探测 + PREPARE/EXECUTE 动态 SQL，
--   兼容 MySQL 5.7 / 8.0 全版本，幂等（再跑不挂）。
SET @sig_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sys_user' AND COLUMN_NAME = 'signature'
);
SET @sql := IF(@sig_exists = 0,
  'ALTER TABLE sys_user ADD COLUMN signature VARCHAR(500) DEFAULT NULL COMMENT ''电子签名 base64 data URI''',
  'SELECT ''sys_user.signature 已存在，跳过'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- =====================================================================
-- 1. 审批中心菜单 + perms（数据库设计 §四 §4.2）
--    parent_id=5（业务管理目录），menu_id=8 占位
--    perms：approval:list / approval:approve / approval:reject
-- =====================================================================
INSERT IGNORE INTO sys_menu
  (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
  (8, '审批中心', 5, 1, 'biz/approval', 'biz/approval/index', 1, 0, 'C', '0', '0',
   'approval:list,approval:approve,approval:reject', '#', 'admin', NOW(), '7 级审批链路');

-- 父菜单补 perms（如未补）
UPDATE sys_menu SET perms = 'biz:view' WHERE menu_id = 5 AND (perms IS NULL OR perms = '');

-- =====================================================================
-- 2. 7 个审批角色挂审批菜单（role_id=3..9 都要有 menu_id=8）
--    业务经办（3）只查；其余审批角色有 approve / reject
-- =====================================================================
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
VALUES
  (3, 8),  -- 业务经办
  (4, 8),  -- 业务复核
  (5, 8),  -- 风控审核
  (6, 8),  -- 财务经办
  (7, 8),  -- 财务复核
  (8, 8),  -- 供管公司负责人
  (9, 8);  -- 投资公司负责人

-- 业务经办角色额外补合同菜单（否则看不到自己提交的合同）
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
VALUES
  (3, 6),  -- 业务经办 可见合同管理
  (4, 6),  -- 业务复核 可见合同管理
  (5, 6),  -- 风控审核 可见合同管理
  (6, 6),  -- 财务经办 可见合同管理
  (7, 6),  -- 财务复核 可见合同管理
  (8, 6),  -- 供管公司负责人 可见合同管理
  (9, 6);  -- 投资公司负责人 可见合同管理

-- =====================================================================
-- 3. 7 个测试用户（一个角色一个用户，便于独立测审批）
--    密码统一 `123456`（bcrypt hash 与 admin 同款）
-- =====================================================================
INSERT IGNORE INTO sys_user
  (user_id, dept_id, user_name, nick_name, user_type, email, phonenumber, sex, avatar, password,
   status, del_flag, login_ip, login_date, pwd_update_date, create_by, create_time, update_by, update_time, remark)
VALUES
  (101, 103, 'biz_handler',   '业务经办',     '00', 'biz_handler@demo.com',   '13900000101', '1', '',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
   '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 0 测试账号 / 密码 123456'),
  (102, 103, 'biz_reviewer',  '业务复核',     '00', 'biz_reviewer@demo.com',  '13900000102', '1', '',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
   '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 1 测试账号 / 密码 123456'),
  (103, 103, 'risk_auditor',  '风控审核',     '00', 'risk_auditor@demo.com',  '13900000103', '1', '',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
   '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 2 测试账号 / 密码 123456'),
  (104, 103, 'finance_h',     '财务经办',     '00', 'finance_h@demo.com',     '13900000104', '1', '',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
   '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 3 测试账号 / 密码 123456'),
  (105, 103, 'finance_r',     '财务复核',     '00', 'finance_r@demo.com',     '13900000105', '1', '',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
   '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 4 测试账号 / 密码 123456'),
  (106, 103, 'scm_director',  '供管负责人',   '00', 'scm_director@demo.com',  '13900000106', '1', '',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
   '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 5 测试账号 / 密码 123456'),
  (107, 103, 'invest_d',      '投资负责人',   '00', 'invest_d@demo.com',      '13900000107', '1', '',
   '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
   '0', '0', '', NOW(), NOW(), 'admin', NOW(), '', NULL, 'Step 6 测试账号 / 密码 123456');

-- 7 个测试用户绑定 7 个审批角色（一个用户一个角色，便于精确测试）
INSERT IGNORE INTO sys_user_role (user_id, role_id)
VALUES
  (101, 3),  -- 业务经办
  (102, 4),  -- 业务复核
  (103, 5),  -- 风控审核
  (104, 6),  -- 财务经办
  (105, 7),  -- 财务复核
  (106, 8),  -- 供管负责人
  (107, 9);  -- 投资负责人

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 验收（执行完后查看）
-- =====================================================================
SELECT '-- sys_user 新增 7 行 --' AS ' ';
SELECT user_id, user_name, nick_name, email FROM sys_user WHERE user_id BETWEEN 101 AND 107 ORDER BY user_id;
SELECT '-- sys_user_role 7 个测试用户绑定 --' AS ' ';
SELECT ur.user_id, u.user_name, ur.role_id, r.role_key, r.role_sort
FROM sys_user_role ur
JOIN sys_user u ON u.user_id = ur.user_id
JOIN sys_role r ON r.role_id = ur.role_id
WHERE ur.user_id BETWEEN 101 AND 107
ORDER BY ur.user_id;
SELECT '-- 审批菜单 --' AS ' ';
SELECT menu_id, menu_name, parent_id, path, perms FROM sys_menu WHERE menu_id = 8;
SELECT '-- 7 个审批角色挂审批菜单 --' AS ' ';
SELECT rm.role_id, r.role_name, r.role_key, COUNT(*) AS menu_cnt
FROM sys_role_menu rm
JOIN sys_role r ON r.role_id = rm.role_id
WHERE rm.role_id BETWEEN 3 AND 9
GROUP BY rm.role_id, r.role_name, r.role_key
ORDER BY rm.role_id;
SELECT '-- signature 字段已添加 --' AS ' ';
SHOW COLUMNS FROM sys_user LIKE 'signature';