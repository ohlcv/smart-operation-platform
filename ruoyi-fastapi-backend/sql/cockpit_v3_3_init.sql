-- =====================================================================
-- 战略驾驶舱 v3.3 路线 C 增量脚本：渠道表加位置字段 + 合同表加 province
-- 文档依据：docs/04-开发/ARD/ADR-架构决策记录.md 路线 C-2
-- 维护原则：
--   1. 所有 ALTER 加 IF NOT EXISTS（v2.6 反思）
--   2. UPDATE 用 ON DUPLICATE KEY UPDATE 兼容已删卷重建场景
--   3. 演示数据回填 4 个渠道的真实坐标（与产品 demo1 一致：北京/上海/广州/杭州）
-- =====================================================================

SET NAMES utf8mb4;

-- 1) biz_channel 加位置字段（v3.3）
ALTER TABLE biz_channel
  ADD COLUMN IF NOT EXISTS province VARCHAR(40)  DEFAULT NULL COMMENT '省份（v3.3 路线 C 地图联动）' AFTER commission_rate,
  ADD COLUMN IF NOT EXISTS city     VARCHAR(40)  DEFAULT NULL COMMENT '城市（v3.3 路线 C 地图联动）' AFTER province,
  ADD COLUMN IF NOT EXISTS lng      DOUBLE       DEFAULT NULL COMMENT '经度（v3.3 路线 C）' AFTER city,
  ADD COLUMN IF NOT EXISTS lat      DOUBLE       DEFAULT NULL COMMENT '纬度（v3.3 路线 C）' AFTER lng;

-- 2) biz_contract 加 province 字段（省份联动筛选）
ALTER TABLE biz_contract
  ADD COLUMN IF NOT EXISTS province VARCHAR(40) DEFAULT NULL COMMENT '客户省份（v3.3 路线 C 省份联动）' AFTER customer_name;

-- 3) biz_customer 加 province 字段（合同表 province 派生源）
ALTER TABLE biz_customer
  ADD COLUMN IF NOT EXISTS province VARCHAR(40) DEFAULT NULL COMMENT '省份（v3.3 路线 C）' AFTER address;

-- 4) 演示数据回填（4 个渠道按平台总部所在地给真实坐标）
UPDATE biz_channel SET province = '北京', city = '北京', lng = 116.40, lat = 39.90 WHERE channel_code = 'QD-001' AND lng IS NULL;
UPDATE biz_channel SET province = '北京', city = '北京', lng = 116.40, lat = 39.90 WHERE channel_code = 'QD-002' AND lng IS NULL;
UPDATE biz_channel SET province = '上海', city = '上海', lng = 121.47, lat = 31.23 WHERE channel_code = 'QD-003' AND lng IS NULL;
UPDATE biz_channel SET province = '江苏', city = '苏州', lng = 120.62, lat = 31.32 WHERE channel_code = 'QD-004' AND lng IS NULL;

-- 5) 演示数据：5 个客户指定 province（与种子数据 ID 对应，省份联动基础数据）
UPDATE biz_customer SET province = '山东'  WHERE id = 1 AND province IS NULL;
UPDATE biz_customer SET province = '浙江'  WHERE id = 2 AND province IS NULL;
UPDATE biz_customer SET province = '广东'  WHERE id = 3 AND province IS NULL;
UPDATE biz_customer SET province = '北京'  WHERE id = 4 AND province IS NULL;
UPDATE biz_customer SET province = '四川'  WHERE id = 5 AND province IS NULL;

-- 6) 合同表 province 由客户派生
UPDATE biz_contract c
JOIN biz_customer cu ON cu.id = c.customer_id
SET c.province = cu.province
WHERE c.province IS NULL AND cu.province IS NOT NULL;

-- 5) 验证
SELECT '-- 渠道表位置字段 --' AS ' ';
SELECT channel_code, channel_name, province, city, lng, lat FROM biz_channel;

SELECT '-- 合同 province 字段 --' AS ' ';
SELECT COUNT(*) AS contract_with_province FROM biz_contract WHERE province IS NOT NULL;