-- =====================================================================
-- 仪表盘 v3.3 路线 C 增量脚本：渠道表加位置字段 + 合同表加 province
-- 文档依据：docs/04-开发/ARD/ADR-架构决策记录.md 路线 C-2
--
-- v3.7 修复：MySQL 8 不支持 `ADD COLUMN IF NOT EXISTS`（MariaDB 才支持），
-- 改用 INFORMATION_SCHEMA.COLUMNS 条件判断 + PREPARE/EXECUTE 动态 SQL。
-- 兼容：MySQL 5.7 / 8.0 / MariaDB
--
-- 维护原则：
--   1. ALTER 用动态 SQL 模拟 IF NOT EXISTS（v2.6 + v3.7 反思）
--   2. UPDATE 用 ON DUPLICATE KEY UPDATE 兼容已删卷重建场景
--   3. 演示数据回填 4 个渠道的真实坐标（与产品 demo1 一致：北京/上海/广州/杭州）
-- =====================================================================

SET NAMES utf8mb4;

-- 0) 业务表存在性前置检查（v3.7.1 反思：原版探测仅查 COLUMNS，对不存在的表
--   返回 0 行（COUNT=0），@sql 被赋值为 ALTER TABLE biz_channel ...，
--   PREPARE 时报 1146 整段挂掉。改为开篇先判断核心业务表是否存在，
--   不存在则跳过整段 ALTER/UPDATE，避免噪声）。
SET @has_biz_channel := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_channel'
);
SET @has_biz_contract := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_contract'
);
SET @has_biz_customer := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_customer'
);

SELECT IF(@has_biz_channel > 0, 'biz_channel 已存在，继续', 'biz_channel 不存在，跳过 v3.3 增量') AS step0_biz_channel,
       IF(@has_biz_contract > 0, 'biz_contract 已存在，继续', 'biz_contract 不存在，跳过')      AS step0_biz_contract,
       IF(@has_biz_customer > 0, 'biz_customer 已存在，继续', 'biz_customer 不存在，跳过')      AS step0_biz_customer;

-- 1) biz_channel 加位置字段（v3.3）
-- v3.7.1 修复：探测条件由「列不存在」改为「表存在 AND 列不存在」，
--   避免不存在的表触发 ALTER 1146 整段挂掉。
-- province
SET @col_exists := IF(@has_biz_channel = 0, 1,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_channel' AND COLUMN_NAME = 'province'));
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE biz_channel ADD COLUMN province VARCHAR(40) DEFAULT NULL COMMENT ''省份（v3.3 路线 C 地图联动）'' AFTER commission_rate',
  'SELECT ''biz_channel.province 跳过（表不存在或列已存在）'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
-- city
SET @col_exists := IF(@has_biz_channel = 0, 1,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_channel' AND COLUMN_NAME = 'city'));
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE biz_channel ADD COLUMN city VARCHAR(40) DEFAULT NULL COMMENT ''城市（v3.3 路线 C 地图联动）'' AFTER province',
  'SELECT ''biz_channel.city 跳过（表不存在或列已存在）'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
-- lng
SET @col_exists := IF(@has_biz_channel = 0, 1,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_channel' AND COLUMN_NAME = 'lng'));
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE biz_channel ADD COLUMN lng DOUBLE DEFAULT NULL COMMENT ''经度（v3.3 路线 C）'' AFTER city',
  'SELECT ''biz_channel.lng 跳过（表不存在或列已存在）'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
-- lat
SET @col_exists := IF(@has_biz_channel = 0, 1,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_channel' AND COLUMN_NAME = 'lat'));
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE biz_channel ADD COLUMN lat DOUBLE DEFAULT NULL COMMENT ''纬度（v3.3 路线 C）'' AFTER lng',
  'SELECT ''biz_channel.lat 跳过（表不存在或列已存在）'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) biz_contract 加 province 字段（省份联动筛选）
SET @col_exists := IF(@has_biz_contract = 0, 1,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_contract' AND COLUMN_NAME = 'province'));
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE biz_contract ADD COLUMN province VARCHAR(40) DEFAULT NULL COMMENT ''客户省份（v3.3 路线 C 省份联动）'' AFTER customer_name',
  'SELECT ''biz_contract.province 跳过（表不存在或列已存在）'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3) biz_customer 加 province 字段（合同表 province 派生源）
SET @col_exists := IF(@has_biz_customer = 0, 1,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'biz_customer' AND COLUMN_NAME = 'province'));
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE biz_customer ADD COLUMN province VARCHAR(40) DEFAULT NULL COMMENT ''省份（v3.3 路线 C）'' AFTER address',
  'SELECT ''biz_customer.province 跳过（表不存在或列已存在）'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4) 演示数据回填（4 个渠道按平台总部所在地给真实坐标）
--    加 IF(@has_biz_channel=0, ...) 守护，表不存在时直接 SELECT 跳过。
SET @sql := IF(@has_biz_channel = 0,
  'SELECT ''biz_channel 不存在，跳过演示数据回填'' AS msg',
  'UPDATE biz_channel SET province = ''北京'', city = ''北京'', lng = 116.40, lat = 39.90 WHERE channel_code = ''QD-001'' AND lng IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_biz_channel = 0,
  'SELECT ''skip'' AS msg',
  'UPDATE biz_channel SET province = ''北京'', city = ''北京'', lng = 116.40, lat = 39.90 WHERE channel_code = ''QD-002'' AND lng IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_biz_channel = 0,
  'SELECT ''skip'' AS msg',
  'UPDATE biz_channel SET province = ''上海'', city = ''上海'', lng = 121.47, lat = 31.23 WHERE channel_code = ''QD-003'' AND lng IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_biz_channel = 0,
  'SELECT ''skip'' AS msg',
  'UPDATE biz_channel SET province = ''江苏'', city = ''苏州'', lng = 120.62, lat = 31.32 WHERE channel_code = ''QD-004'' AND lng IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 5) 演示数据：5 个客户指定 province（与种子数据 ID 对应，省份联动基础数据）
SET @sql := IF(@has_biz_customer = 0,
  'SELECT ''biz_customer 不存在，跳过客户省份回填'' AS msg',
  'UPDATE biz_customer SET province = ''山东''  WHERE id = 1 AND province IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_biz_customer = 0,
  'SELECT ''skip'' AS msg',
  'UPDATE biz_customer SET province = ''浙江''  WHERE id = 2 AND province IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_biz_customer = 0,
  'SELECT ''skip'' AS msg',
  'UPDATE biz_customer SET province = ''广东''  WHERE id = 3 AND province IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_biz_customer = 0,
  'SELECT ''skip'' AS msg',
  'UPDATE biz_customer SET province = ''北京''  WHERE id = 4 AND province IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_biz_customer = 0,
  'SELECT ''skip'' AS msg',
  'UPDATE biz_customer SET province = ''四川''  WHERE id = 5 AND province IS NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 6) 合同表 province 由客户派生（双表守护）
SET @sql := IF(@has_biz_contract = 0 OR @has_biz_customer = 0,
  'SELECT ''biz_contract/biz_customer 不存在，跳过派生'' AS msg',
  'UPDATE biz_contract c JOIN biz_customer cu ON cu.id = c.customer_id SET c.province = cu.province WHERE c.province IS NULL AND cu.province IS NOT NULL');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 7) 验证
SELECT '-- 渠道表位置字段 --' AS ' ';
SELECT channel_code, channel_name, province, city, lng, lat FROM biz_channel;

SELECT '-- 合同 province 字段 --' AS ' ';
SELECT COUNT(*) AS contract_with_province FROM biz_contract WHERE province IS NOT NULL;