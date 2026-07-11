-- =====================================================================
-- 渠道管理初始化脚本
-- 文档依据：docs/03-设计/数据库设计.md v3.0 §4.6（草拟）
-- 数据库：MySQL 8.0
-- 创建日期：2026-07-11
-- 维护原则：
--   1. 渠道分类严格遵循 sys_dict_data dict_type='channel_type' 已登记的 4 个 value
--   2. 删除拦截：contract_ids 非空禁止删除（Service 层校验）
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS biz_channel;
CREATE TABLE biz_channel (
  id                BIGINT(20)    NOT NULL AUTO_INCREMENT           COMMENT '渠道ID',
  channel_code      VARCHAR(50)   NOT NULL                          COMMENT '渠道编码 QD-NNN（唯一）',
  channel_name      VARCHAR(100)  NOT NULL                          COMMENT '渠道名称',
  category          VARCHAR(20)   NOT NULL                          COMMENT '渠道分类：meituan/douyin/ctrip/tongcheng',
  contact_name      VARCHAR(50)   DEFAULT NULL                      COMMENT '联系人',
  contact_phone     VARCHAR(20)   DEFAULT NULL                      COMMENT '联系电话',
  contact_email     VARCHAR(100)  DEFAULT NULL                      COMMENT '联系邮箱',
  platform_url      VARCHAR(255)  DEFAULT NULL                      COMMENT '平台地址',
  account           VARCHAR(128)  DEFAULT NULL                      COMMENT '登录账号（演示用）',
  password          VARCHAR(128)  DEFAULT NULL                      COMMENT '登录密码（演示用，明文不加密）',
  commission_rate   DECIMAL(5,4)  DEFAULT NULL                      COMMENT '佣金比例（0-1）',
  status            TINYINT(4)    NOT NULL DEFAULT 1                COMMENT '状态：0=停用 1=启用',
  sort_order        INT           NOT NULL DEFAULT 0                COMMENT '排序值，越大越靠前',
  description       TEXT          DEFAULT NULL                      COMMENT '渠道说明',
  attachments       JSON          DEFAULT NULL                      COMMENT '资质附件 [{name,url}]',
  contract_ids      JSON          DEFAULT NULL                      COMMENT '关联合同ID列表（冗余便于展示）',
  remark            TEXT          DEFAULT NULL                      COMMENT '备注',
  created_by        BIGINT(20)    DEFAULT NULL                      COMMENT '创建人 sys_user.user_id',
  created_by_name   VARCHAR(64)   DEFAULT NULL                      COMMENT '创建人姓名（冗余）',
  create_time       DATETIME      NOT NULL                          COMMENT '创建时间',
  update_by         VARCHAR(64)   DEFAULT NULL                      COMMENT '更新者',
  update_time       DATETIME      DEFAULT NULL                      COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_channel_code (channel_code),
  KEY idx_category (category),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='渠道主表';

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 演示数据（与字典对齐）
-- =====================================================================
INSERT INTO biz_channel
(channel_code, channel_name, category, contact_name, contact_phone, platform_url, account, password, commission_rate, description, created_by, created_by_name, create_time, remark)
VALUES
('QD-001', '美团到综（景区合作）',   'meituan',   '美团商务',  '400-009-9888',  'https://www.meituan.com',   'meituan_biz_01', 'demo_pwd', 0.0500, '美团综合业务：景区门票/酒店/餐饮', 1, 'admin', NOW(), '示范渠道：美团到综'),
('QD-002', '抖音生活服务',           'douyin',    '抖音商务',  '400-822-2288',  'https://www.douyin.com',    'dy_biz_01',      'demo_pwd', 0.0600, '抖音本地生活服务',              1, 'admin', NOW(), '示范渠道：抖音生活'),
('QD-003', '携程商旅',               'ctrip',     '携程商务',  '400-819-9999',  'https://www.ctrip.com',     'ctrip_biz_01',   'demo_pwd', 0.0450, '携程商旅业务',                  1, 'admin', NOW(), '示范渠道：携程商旅'),
('QD-004', '同程旅行（OTA 直连）',   'tongcheng', '同程商务',  '400-100-7777',  'https://www.ly.com',        'tongcheng_biz',  'demo_pwd', 0.0480, '同程旅行 OTA 直连',            1, 'admin', NOW(), '示范渠道：同程旅行');

-- =====================================================================
-- 验证
-- =====================================================================
SELECT '-- 渠道表结构 --' AS ' ';
DESC biz_channel;
SELECT '-- 演示渠道 --' AS ' ';
SELECT id, channel_code, channel_name, category, contact_name, status FROM biz_channel ORDER BY id;
