-- =====================================================================
-- 经营数据初始化脚本（ADR D05：手工录入，不与合同自动汇总）
-- 数据库：MySQL 8.0
-- 创建日期：2026-07-11
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS biz_operation;
CREATE TABLE biz_operation (
  id              BIGINT(20)    NOT NULL AUTO_INCREMENT         COMMENT '记录ID',
  period          VARCHAR(20)   NOT NULL                        COMMENT '周期 key，如 2026-07 / 2026-Q3 / 2026',
  period_type     VARCHAR(20)   NOT NULL                        COMMENT '周期类型 month/quarter/year',
  business_line   VARCHAR(20)   DEFAULT NULL                    COMMENT '业务线 scenic/digital/logistics',
  revenue         DECIMAL(18,2) NOT NULL DEFAULT 0              COMMENT '营收',
  cost            DECIMAL(18,2) NOT NULL DEFAULT 0              COMMENT '成本',
  gross_profit    DECIMAL(18,2) NOT NULL DEFAULT 0              COMMENT '毛利（实时计算冗余）',
  customer_count  INT           NOT NULL DEFAULT 0              COMMENT '客户数',
  contract_count  INT           NOT NULL DEFAULT 0              COMMENT '合同数',
  avg_order_value DECIMAL(18,2) NOT NULL DEFAULT 0              COMMENT '客单价（营收/合同数）',
  remark          TEXT          DEFAULT NULL                    COMMENT '备注',
  created_by      BIGINT(20)    DEFAULT NULL                    COMMENT '创建人 sys_user.user_id',
  created_by_name VARCHAR(64)   DEFAULT NULL                    COMMENT '创建人姓名（冗余）',
  create_time     DATETIME      NOT NULL                        COMMENT '创建时间',
  update_by       VARCHAR(64)   DEFAULT NULL                    COMMENT '更新者',
  update_time     DATETIME      DEFAULT NULL                    COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_period_type_line (period, period_type, business_line),
  KEY idx_period_type (period_type),
  KEY idx_business_line (business_line),
  KEY idx_period (period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='经营数据表';

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 演示数据：2026 年 6/7 月 + 2025 年 7 月（用于同比对比演示）
-- =====================================================================
INSERT INTO biz_operation
(period, period_type, business_line, revenue, cost, gross_profit, customer_count, contract_count, avg_order_value, created_by, created_by_name, create_time, remark)
VALUES
-- 2025-07（去年同期）
('2025-07', 'month', NULL, 3800000.00, 2800000.00, 1000000.00, 25, 8,  475000.00, 1, 'admin', NOW(), '示范数据：去年同期'),
-- 2026-06（上月）
('2026-06', 'month', NULL, 4500000.00, 3200000.00, 1300000.00, 32, 10, 450000.00, 1, 'admin', NOW(), '示范数据：上月'),
-- 2026-07（当月）
('2026-07', 'month', NULL, 5200000.00, 3500000.00, 1700000.00, 35, 12, 433333.33, 1, 'admin', NOW(), '示范数据：当月（含合同 HT-2026-003 已开票）');

-- =====================================================================
-- 验证
-- =====================================================================
SELECT '-- 经营数据表结构 --' AS ' ';
DESC biz_operation;
SELECT '-- 演示数据 --' AS ' ';
SELECT id, period, period_type, revenue, cost, gross_profit, customer_count, contract_count FROM biz_operation ORDER BY period;