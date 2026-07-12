-- =====================================================================
-- 发票管理初始化脚本
-- 文档依据：docs/03-开发/开发计划/路线A-业务闭环优先.md §3.2（数据库表设计）
-- 数据库：MySQL 8.0
-- 创建日期：2026-07-11
-- 维护原则：
--   1. 1:1 关联合同（contract_id + invoice_no 唯一）
--   2. 状态机：pending → issued → void
--   3. ADR D11：台账管理，不做真实开票对接
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS biz_invoice;
CREATE TABLE biz_invoice (
  id                BIGINT(20)    NOT NULL AUTO_INCREMENT          COMMENT '发票ID',
  invoice_no        VARCHAR(50)   NOT NULL                         COMMENT '发票号 FP-NNN（唯一）',
  contract_id       BIGINT(20)    NOT NULL                         COMMENT '关联合同ID biz_contract.id（1:1）',
  contract_no       VARCHAR(50)   DEFAULT NULL                     COMMENT '冗余合同编号（便于展示）',
  invoice_type      VARCHAR(20)   NOT NULL                         COMMENT '发票类型：specialized=增值税专用/general=普通/electronic=电子',
  amount            DECIMAL(18,2) NOT NULL DEFAULT 0               COMMENT '开票金额（含税）',
  tax_rate          DECIMAL(5,4)  NOT NULL DEFAULT 0.1300         COMMENT '税率（0-1，默认13%）',
  tax_amount        DECIMAL(18,2) NOT NULL DEFAULT 0               COMMENT '税额',
  party_name        VARCHAR(200)  NOT NULL                         COMMENT '购方名称（抬头）',
  party_tax_no      VARCHAR(50)   DEFAULT NULL                     COMMENT '购方税号',
  status            VARCHAR(20)   NOT NULL DEFAULT 'pending'        COMMENT '状态：pending=待开 / issued=已开 / void=已作废',
  apply_date        DATE          DEFAULT NULL                     COMMENT '申请日期',
  issue_date        DATE          DEFAULT NULL                     COMMENT '开票日期',
  void_reason       VARCHAR(500)  DEFAULT NULL                     COMMENT '作废原因（action=void 时必填）',
  remark            TEXT          DEFAULT NULL                     COMMENT '备注',
  created_by        BIGINT(20)    DEFAULT NULL                     COMMENT '创建人 sys_user.user_id',
  created_by_name   VARCHAR(64)   DEFAULT NULL                     COMMENT '创建人姓名（冗余）',
  create_time       DATETIME      NOT NULL                         COMMENT '创建时间',
  update_by         VARCHAR(64)   DEFAULT NULL                     COMMENT '更新者',
  update_time       DATETIME      DEFAULT NULL                     COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_invoice_no (invoice_no),
  UNIQUE KEY uk_contract_id (contract_id),
  KEY idx_status (status),
  KEY idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票主表';

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 演示数据：给已审批通过的合同 HT-2026-003 开一张已开票发票
-- =====================================================================
INSERT INTO biz_invoice
(invoice_no, contract_id, contract_no, invoice_type, amount, tax_rate, tax_amount, party_name, party_tax_no, status, apply_date, issue_date, created_by, created_by_name, create_time, remark)
VALUES
('FP-0001', 3, 'HT-2026-003', 'specialized', 1200000.00, 0.1300, 138053.10, '泰山景区管委会', '91910000123456789X', 'issued', '2026-07-10', '2026-07-11', 1, 'admin', NOW(), '示范发票：与示范合同 HT-2026-003 关联');

-- =====================================================================
-- 验证
-- =====================================================================
SELECT '-- 发票表结构 --' AS ' ';
DESC biz_invoice;
SELECT '-- 演示发票 --' AS ' ';
SELECT id, invoice_no, contract_no, amount, status, issue_date FROM biz_invoice;
