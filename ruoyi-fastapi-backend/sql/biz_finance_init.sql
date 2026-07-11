-- =====================================================================
-- 财务管理初始化脚本（ADR D10：手工 CSV 导入，不直连银行 API）
-- 数据库：MySQL 8.0
-- 创建日期：2026-07-11
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS biz_finance_entry;
CREATE TABLE biz_finance_entry (
  id                BIGINT(20)    NOT NULL AUTO_INCREMENT       COMMENT '流水ID',
  entry_no          VARCHAR(50)   NOT NULL                      COMMENT '流水号 FN-NNN（唯一）',
  entry_type        VARCHAR(20)   NOT NULL                      COMMENT '类型：payable=应付 / receivable=应收',
  direction         VARCHAR(10)   NOT NULL DEFAULT 'out'         COMMENT '收支方向：out=支出 / in=收入',
  invoice_id        BIGINT(20)    DEFAULT NULL                  COMMENT '关联发票ID biz_invoice.id（可空）',
  invoice_no        VARCHAR(50)   DEFAULT NULL                  COMMENT '冗余发票号',
  contract_id       BIGINT(20)    DEFAULT NULL                  COMMENT '关联合同ID biz_contract.id',
  contract_no       VARCHAR(50)   DEFAULT NULL                  COMMENT '冗余合同号',
  party_name        VARCHAR(200)  DEFAULT NULL                  COMMENT '对手方名称',
  amount            DECIMAL(18,2) NOT NULL DEFAULT 0            COMMENT '金额',
  account           VARCHAR(50)   DEFAULT NULL                  COMMENT '银行账号',
  account_name      VARCHAR(100)  DEFAULT NULL                  COMMENT '账户名',
  bank_name         VARCHAR(100)  DEFAULT NULL                  COMMENT '开户行',
  transaction_date  DATE          DEFAULT NULL                  COMMENT '交易日期',
  cleared           TINYINT(4)    NOT NULL DEFAULT 0            COMMENT '对账状态：0=未对账 1=已对账',
  cleared_time      DATETIME      DEFAULT NULL                  COMMENT '对账时间',
  remark            TEXT          DEFAULT NULL                  COMMENT '备注',
  created_by        BIGINT(20)    DEFAULT NULL                  COMMENT '创建人 sys_user.user_id',
  created_by_name   VARCHAR(64)   DEFAULT NULL                  COMMENT '创建人姓名（冗余）',
  create_time       DATETIME      NOT NULL                      COMMENT '创建时间',
  update_by         VARCHAR(64)   DEFAULT NULL                  COMMENT '更新者',
  update_time       DATETIME      DEFAULT NULL                  COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_entry_no (entry_no),
  KEY idx_entry_type (entry_type),
  KEY idx_cleared (cleared),
  KEY idx_transaction_date (transaction_date),
  KEY idx_invoice_id (invoice_id),
  KEY idx_contract_id (contract_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务流水台账';

DROP TABLE IF EXISTS biz_bank_statement;
CREATE TABLE biz_bank_statement (
  id                    BIGINT(20)    NOT NULL AUTO_INCREMENT       COMMENT '对账单ID',
  batch_no              VARCHAR(50)   NOT NULL                      COMMENT '导入批次号 BS-YYYYMMDDHHMMSS',
  transaction_date      DATE          NOT NULL                      COMMENT '交易日期',
  account               VARCHAR(50)   NOT NULL                      COMMENT '银行账号',
  amount                DECIMAL(18,2) NOT NULL DEFAULT 0            COMMENT '金额',
  direction             VARCHAR(10)   NOT NULL DEFAULT 'in'         COMMENT 'in=收入 / out=支出',
  counterparty          VARCHAR(100)  DEFAULT NULL                  COMMENT '交易对手',
  counterparty_account  VARCHAR(50)   DEFAULT NULL                  COMMENT '对手账号',
  summary               VARCHAR(200)  DEFAULT NULL                  COMMENT '摘要',
  matched               TINYINT(4)    NOT NULL DEFAULT 0            COMMENT '是否已匹配 0=否 1=是',
  matched_entry_id      BIGINT(20)    DEFAULT NULL                  COMMENT '匹配的财务流水ID',
  import_time           DATETIME      NOT NULL                      COMMENT '导入时间',
  imported_by           BIGINT(20)    DEFAULT NULL                  COMMENT '导入人 sys_user.user_id',
  PRIMARY KEY (id),
  KEY idx_batch_no (batch_no),
  KEY idx_transaction_date (transaction_date),
  KEY idx_matched (matched),
  KEY idx_account (account)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='银行对账单导入表';

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 演示数据：发票 FP-0001 (HT-2026-003) 的应收入账
-- =====================================================================
INSERT INTO biz_finance_entry
(entry_no, entry_type, direction, invoice_id, invoice_no, contract_id, contract_no, party_name, amount, account, account_name, bank_name, transaction_date, cleared, created_by, created_by_name, create_time, remark)
VALUES
('FN-0001', 'receivable', 'in', 1, 'FP-0001', 3, 'HT-2026-003', '泰山景区管委会', 1200000.00, '6225880123456789', '山东出版供应链管理公司', '工商银行济南分行', '2026-07-11', 0, 1, 'admin', NOW(), '示范应收：与发票 FP-0001 关联');

-- =====================================================================
-- 验证
-- =====================================================================
SELECT '-- 财务流水表结构 --' AS ' ';
DESC biz_finance_entry;
SELECT '-- 对账单表结构 --' AS ' ';
DESC biz_bank_statement;
SELECT '-- 演示流水 --' AS ' ';
SELECT id, entry_no, entry_type, amount, cleared FROM biz_finance_entry;