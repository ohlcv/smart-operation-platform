-- =====================================================================
-- 业务模块初始化脚本
-- 文档依据：docs/03-设计/数据库设计.md v3.0 §四
-- 数据库：MySQL 8.0
-- 创建日期：2026-07-11
-- 维护原则：
--   1. 所有建表与设计文档一一对应；字段含义、长度、约束与设计文档保持一致
--   2. 主键统一使用 id（与设计文档 §四保持一致；与 RuoYi 原生 sys_user.user_id 不同，这是有意为之的差异化设计）
--   3. 时间戳统一 created_at / updated_at（设计文档 §1.2 命名规范）
--   4. 业务表前缀统一 biz_（设计文档 §1.1）
--   5. 不可在本文件中修改 RuoYi 原生表（sys_* / log_*）
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- 一、客户档案表 biz_customer（设计文档 §4.3）
-- =====================================================================
DROP TABLE IF EXISTS biz_customer;
CREATE TABLE biz_customer (
  id                  BIGINT(20)      NOT NULL AUTO_INCREMENT       COMMENT '客户ID',
  customer_code       VARCHAR(50)     DEFAULT NULL                   COMMENT '业务编号 KH-NNN，唯一键（ADR D24 客户业务标识）',
  customer_name       VARCHAR(200)    NOT NULL                       COMMENT '客户名称（公司全称）',
  customer_type       VARCHAR(20)     DEFAULT NULL                   COMMENT '客户类型：scenic=景区 / hotel=酒店 / agency=旅行社 / publish=出版社',
  contact_name        VARCHAR(50)     DEFAULT NULL                   COMMENT '联系人',
  contact_phone       VARCHAR(20)     DEFAULT NULL                   COMMENT '联系电话',
  contact_email       VARCHAR(100)    DEFAULT NULL                   COMMENT '邮箱',
  address             VARCHAR(300)    DEFAULT NULL                   COMMENT '地址',
  business_license    VARCHAR(200)    DEFAULT NULL                   COMMENT '营业执照编号',
  tax_no              VARCHAR(50)     DEFAULT NULL                   COMMENT '纳税人识别号',
  qualification_files JSON            DEFAULT NULL                   COMMENT '资质文件列表：[{name,url}]',
  level               VARCHAR(10)     DEFAULT NULL                   COMMENT '客户等级：A / B / C',
  tags                JSON            DEFAULT NULL                   COMMENT '标签：["景区","文旅"]',
  status              TINYINT(4)      NOT NULL DEFAULT 1             COMMENT '状态：0=停用 1=启用',
  created_by          BIGINT(20)      DEFAULT NULL                   COMMENT '创建人(sys_user.user_id)',
  create_time         DATETIME        NOT NULL                       COMMENT '创建时间',
  update_by           VARCHAR(64)     DEFAULT NULL                   COMMENT '更新者',
  update_time         DATETIME        DEFAULT NULL                   COMMENT '更新时间',
  remark              VARCHAR(500)    DEFAULT NULL                   COMMENT '备注',
  PRIMARY KEY (id),
  UNIQUE KEY uk_customer_code (customer_code),
  KEY idx_customer_type (customer_type),
  KEY idx_level (level),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户档案表';

-- =====================================================================
-- 二、合同主表 biz_contract（设计文档 §4.1）
-- =====================================================================
DROP TABLE IF EXISTS biz_contract;
CREATE TABLE biz_contract (
  id                  BIGINT(20)      NOT NULL AUTO_INCREMENT       COMMENT '合同ID',
  contract_no         VARCHAR(50)     NOT NULL                       COMMENT '合同编号（手动输入，唯一）',
  title               VARCHAR(200)    NOT NULL                       COMMENT '合同名称',
  contract_type       VARCHAR(20)     NOT NULL                       COMMENT '合同类型：payment=业务付款审批单 / business=业务审批单',
  party_a             VARCHAR(200)    NOT NULL                       COMMENT '甲方（客户）',
  party_b             VARCHAR(200)    NOT NULL                       COMMENT '乙方（本司）',
  amount              DECIMAL(18,2)   NOT NULL DEFAULT 0             COMMENT '合同金额（元）',
  amount_in_words     VARCHAR(100)    DEFAULT NULL                   COMMENT '金额大写',
  sign_date           DATE            DEFAULT NULL                   COMMENT '签订日期',
  department          VARCHAR(100)    DEFAULT NULL                   COMMENT '申请部门',
  business_type       VARCHAR(50)     DEFAULT NULL                   COMMENT '业务类型（如：景区门票、文创产品等）',
  customer_id         BIGINT(20)      DEFAULT NULL                   COMMENT '关联客户ID(biz_customer.id)',
  customer_name       VARCHAR(200)    DEFAULT NULL                   COMMENT '冗余客户名称（便于列表展示）',
  remark              TEXT            DEFAULT NULL                   COMMENT '合同备注',
  attachments         JSON            DEFAULT NULL                   COMMENT '附件列表：[{name,url}]',
  status              VARCHAR(20)     NOT NULL DEFAULT 'draft'       COMMENT '状态：draft=草稿 pending=审批中 approved=已通过 rejected=已驳回待修改',
  current_step        INT             NOT NULL DEFAULT 0             COMMENT '当前审批步骤（0-6）',
  current_role        VARCHAR(50)     DEFAULT NULL                   COMMENT '当前待审角色role_key（冗余便于展示）',
  reject_count        INT             NOT NULL DEFAULT 0             COMMENT '累计驳回次数',
  created_by          BIGINT(20)      NOT NULL                       COMMENT '创建人(sys_user.user_id)',
  created_by_name     VARCHAR(50)     DEFAULT NULL                   COMMENT '创建人姓名（冗余）',
  create_time         DATETIME        NOT NULL                       COMMENT '创建时间',
  update_by           VARCHAR(64)     DEFAULT NULL                   COMMENT '更新者',
  update_time         DATETIME        DEFAULT NULL                   COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_contract_no (contract_no),
  KEY idx_status (status),
  KEY idx_current_step (current_step),
  KEY idx_created_by (created_by),
  KEY idx_create_time (create_time),
  KEY idx_customer_id (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同主表';

-- =====================================================================
-- 三、审批记录表 biz_approval（设计文档 §4.2）
-- =====================================================================
DROP TABLE IF EXISTS biz_approval;
CREATE TABLE biz_approval (
  id                  BIGINT(20)      NOT NULL AUTO_INCREMENT       COMMENT '审批记录ID',
  contract_id         BIGINT(20)      NOT NULL                       COMMENT '关联合同ID(biz_contract.id)',
  approver_id         BIGINT(20)      DEFAULT NULL                   COMMENT '审批人(sys_user.user_id)',
  approver_name       VARCHAR(50)     DEFAULT NULL                   COMMENT '审批人姓名（冗余）',
  step                INT             NOT NULL                       COMMENT '审批步骤（0-6），记录历史 step 值',
  approver_role       VARCHAR(50)     NOT NULL                       COMMENT '审批时角色标识(如 business_reviewer)',
  action              VARCHAR(20)     NOT NULL                       COMMENT '审批动作：approve=通过 / reject=驳回',
  comment             TEXT            DEFAULT NULL                   COMMENT '审批意见',
  reject_reason       TEXT            DEFAULT NULL                   COMMENT '驳回原因（action=reject 时必填）',
  signature_snapshot  TEXT            DEFAULT NULL                   COMMENT '审批时电子签名快照(base64 data URI)',
  approval_ip         VARCHAR(50)     DEFAULT NULL                   COMMENT '审批操作 IP',
  approval_time       DATETIME        NOT NULL                       COMMENT '审批时间',
  create_time         DATETIME        NOT NULL                       COMMENT '记录创建时间',
  PRIMARY KEY (id),
  KEY idx_contract_id (contract_id),
  KEY idx_approver_id (approver_id),
  KEY idx_step (step),
  KEY idx_approval_time (approval_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批记录表';

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 四、演示数据（仅 demo 用，生产环境必须清空）
-- =====================================================================
INSERT INTO biz_customer (customer_code, customer_name, customer_type, contact_name, contact_phone, address, level, status, created_by, create_time, remark)
VALUES
('KH-001', '济南新华书店', 'publish', '王经理', '13900000001', '济南市市中区胜利大街56号', 'A', 1, 1, NOW(), '战略合作客户'),
('KH-002', '青岛出版发行集团', 'publish', '李主任', '13900000002', '青岛市市南区香港中路26号', 'A', 1, 1, NOW(), '数字出版核心客户'),
('KH-003', '泰山景区管委会', 'scenic', '张科长', '13900000003', '泰安市岱宗大街', 'A', 1, 1, NOW(), '景区发行重点客户'),
('KH-004', '山东文旅集团', 'agency', '赵总', '13900000004', '济南市经四路', 'B', 1, 1, NOW(), '旅行社渠道'),
('KH-005', '曲阜孔子文化园', 'scenic', '陈馆长', '13900000005', '曲阜市明故城', 'B', 1, 1, NOW(), '景区发行');

INSERT INTO biz_contract
(contract_no, title, contract_type, party_a, party_b, amount, sign_date, department, business_type, customer_id, customer_name, status, current_step, current_role, reject_count, created_by, created_by_name, create_time, remark)
VALUES
('HT-2026-001', '济南新华书店图书采购合同', 'payment', '济南新华书店', '山东出版供应链管理公司', 500000.00, '2026-07-05', '业务部', '景区门票', 1, '济南新华书店', 'pending', 1, 'business_reviewer', 0, 2, '年糕', NOW(), '示范合同：审批中'),
('HT-2026-002', '青岛数字出版合作协议', 'business', '青岛出版发行集团', '山东出版供应链管理公司', 300000.00, '2026-07-08', '数字业务部', '数字出版', 2, '青岛出版发行集团', 'draft', 0, NULL, 0, 2, '年糕', NOW(), '示范合同：草稿'),
('HT-2026-003', '泰山景区票务系统对接', 'business', '泰山景区管委会', '山东出版供应链管理公司', 1200000.00, '2026-07-10', '技术部', '景区门票', 3, '泰山景区管委会', 'approved', 6, 'invest_director', 0, 2, '年糕', NOW(), '示范合同：已通过');