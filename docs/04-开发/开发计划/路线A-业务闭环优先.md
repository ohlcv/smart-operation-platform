# 路线 A：业务闭环优先（详细方案）

> 文档版本：v1.0
> 创建日期：2026-07-11
> 文档定位：将"合同→渠道→发票→财务→经营数据"完整业务链 5 个 CRUD 模块从 v1 demo 迁移到当前项目。文件互斥，与路线 B 完全无重叠。

---

## 一、目标与价值

**业务目标**：让合同审批通过后的下游环节（渠道分配、发票开具、财务入账、经营数据登记）全部可在系统内完成。**一条业务链全跑通**。

**演示场景**：业务部门、运营、运维内部演示。

**总工作量**：49h（后端 28h + 前端 21h）

**预计完成**：1.5 周

---

## 二、文件清单（路线 A 独占）

### 2.1 后端文件（22 个新增 / 1 个编辑）

#### channel 渠道管理（11h 后端）

| # | 文件 | 行数 | 工作量 | 内容 |
|---|------|------|--------|------|
| A-2.1.1 | `module_biz/entity/do/channel_do.py` | 60 | 1h | SQLAlchemy 模型，参考 v1 demo `1/backend/app/models/channel.py` (38 行) |
| A-2.1.2 | `module_biz/entity/vo/channel_vo.py` | 120 | 1.5h | Pydantic VO（list/create/update/query）|
| A-2.1.3 | `module_biz/dao/channel_dao.py` | 80 | 1h | CRUD + 分页 |
| A-2.1.4 | `module_biz/service/channel_service.py` | 200 | 4h | 业务逻辑 |
| A-2.1.5 | `module_biz/controller/channel_controller.py` | 100 | 2h | 8 个 endpoint |
| A-2.1.6 | `sql/biz_channel_init.sql` | 50 | 0.5h | 渠道分类字典 + 渠道表 |
| A-2.1.7 | `module_biz/enums.py` | +8 | 0.5h | `ChannelCategoryEnum`（景区门票/酒店数据/综合 OTA/其他）|
| A-2.1.8 | `sql/biz_menus_roles_init.sql` | +20 | 0.5h | 追加 channel 菜单（menu_id=9）+ perms `biz:channel:list/add/edit/delete/import` |

**关键业务规则**：
- 渠道分类：4 类（景区门票/酒店数据/综合 OTA/其他），枚举硬编码在 `module_biz/enums.py`
- 渠道与合同关联：1 个合同可分配到 N 个渠道
- CSV 导入：D09 决策，先做 CSV 兜底
- 资质附件：D12 决策，本地文件系统存储

**Endpoint 清单**：
```
GET    /biz/channel/list                  渠道列表（分页）
GET    /biz/channel/{id}                  渠道详情
POST   /biz/channel                       新建渠道
PUT    /biz/channel?channel_id={id}       编辑渠道
DELETE /biz/channel/{id}                  删除渠道（校验无关联合同）
POST   /biz/channel/import                CSV 导入
GET    /biz/channel/export                导出 CSV
GET    /biz/channel/category-options      渠道分类下拉选项
```

#### invoice 发票管理（9h 后端）

| # | 文件 | 行数 | 工作量 |
|---|------|------|--------|
| A-2.1.9 | `module_biz/entity/do/invoice_do.py` | 70 | 1h |
| A-2.1.10 | `module_biz/entity/vo/invoice_vo.py` | 130 | 1.5h |
| A-2.1.11 | `module_biz/dao/invoice_dao.py` | 100 | 1h |
| A-2.1.12 | `module_biz/service/invoice_service.py` | 250 | 4h |
| A-2.1.13 | `module_biz/controller/invoice_controller.py` | 100 | 2h |
| A-2.1.14 | `sql/biz_invoice_init.sql` | 60 | 0.5h |
| A-2.1.15 | `module_biz/enums.py` | +6 | 0.5h（`InvoiceStatusEnum`：待开/已开/已作废）|
| A-2.1.16 | `sql/biz_menus_roles_init.sql` | +20 | 0.5h（menu_id=10）|

**关键业务规则**（D11 已确认）：
- 发票与合同 **1:1 关联**（合同 ID + 发票号唯一约束）
- 状态流转：`pending`（待开）→ `issued`（已开）→ `void`（已作废）
- **不做真实开票对接**，仅台账管理
- 开票日期不可早于合同签订日期
- 金额不可超过合同金额

**Endpoint 清单**：
```
GET    /biz/invoice/list                  发票列表
GET    /biz/invoice/{id}                  发票详情
POST   /biz/invoice                       新建发票（关联合同）
PUT    /biz/invoice?invoice_id={id}       编辑发票
DELETE /biz/invoice/{id}                  删除发票（仅 pending 状态）
PUT    /biz/invoice/issue/{id}            标记为已开票
PUT    /biz/invoice/void/{id}             作废发票
```

#### finance 财务管理（12h 后端）

| # | 文件 | 行数 | 工作量 |
|---|------|------|--------|
| A-2.1.17 | `module_biz/entity/do/finance_do.py` | 80 | 1h |
| A-2.1.18 | `module_biz/entity/vo/finance_vo.py` | 150 | 2h |
| A-2.1.19 | `module_biz/dao/finance_dao.py` | 120 | 1.5h |
| A-2.1.20 | `module_biz/service/finance_service.py` | 280 | 5h |
| A-2.1.21 | `module_biz/controller/finance_controller.py` | 120 | 2h |
| A-2.1.22 | `sql/biz_finance_init.sql` | 70 | 0.5h |

**关键业务规则**（D10 已确认）：
- 应付/应收台账（payable/receivable）
- 银行对账单 **手工 CSV 导入**，不做银行 API 直连
- 与发票 ID 关联（一条发票对应一条入账记录）
- 月末自动结转（脚本触发）

**Endpoint 清单**：
```
GET    /biz/finance/list                  财务台账列表
GET    /biz/finance/{id}                  详情
POST   /biz/finance                       新建入账（关联发票）
PUT    /biz/finance?finance_id={id}       编辑
DELETE /biz/finance/{id}                  删除
POST   /biz/finance/import-bank           银行对账单 CSV 导入
GET    /biz/finance/summary               财务汇总（按月）
```

#### operation 经营数据（11h 后端）

| # | 文件 | 行数 | 工作量 |
|---|------|------|--------|
| A-2.1.23 | `module_biz/entity/do/operation_do.py` | 80 | 1h |
| A-2.1.24 | `module_biz/entity/vo/operation_vo.py` | 140 | 1.5h |
| A-2.1.25 | `module_biz/dao/operation_dao.py` | 100 | 1h |
| A-2.1.26 | `module_biz/service/operation_service.py` | 260 | 4.5h |
| A-2.1.27 | `module_biz/controller/operation_controller.py` | 110 | 2h |
| A-2.1.28 | `sql/biz_operation_init.sql` | 60 | 0.5h |
| A-2.1.29 | `module_biz/enums.py` | +8 | 0.5h（`OperationPeriodEnum`：月报/季报/年报）|

**关键业务规则**（D05 已确认）：
- **当前阶段手工录入**，不与合同自动汇总
- 经营指标：营收、成本、毛利、客单价、客户数、合同数
- 周期：月报/季报/年报
- 同比/环比自动计算（不存数据库，实时计算）

**Endpoint 清单**：
```
GET    /biz/operation/list                经营数据列表
GET    /biz/operation/{id}                详情
POST   /biz/operation                     新建
PUT    /biz/operation?operation_id={id}   编辑
DELETE /biz/operation/{id}                删除
GET    /biz/operation/comparison          同比环比对比
```

### 2.2 前端文件（10 个新增 / 1 个编辑）

| # | 文件 | 行数 | 工作量 | 来源 |
|---|------|------|--------|------|
| A-2.2.1 | `src/api/biz/channel.js` | 70 | 0.5h | 新建 |
| A-2.2.2 | `src/views/biz/channel/index.vue` | 376 | 4.5h | v1 demo `1/frontend/src/views/channel/` 迁移 |
| A-2.2.3 | `src/api/biz/invoice.js` | 70 | 0.5h | 新建 |
| A-2.2.4 | `src/views/biz/invoice/index.vue` | 322 | 4h | v1 demo `1/frontend/src/views/invoice/` 迁移 |
| A-2.2.5 | `src/api/biz/finance.js` | 80 | 0.5h | 新建 |
| A-2.2.6 | `src/views/biz/finance/index.vue` | 380 | 5h | 新建（v1 demo 无 finance 独立模块） |
| A-2.2.7 | `src/api/biz/operation.js` | 70 | 0.5h | 新建 |
| A-2.2.8 | `src/views/biz/operation/index.vue` | 338 | 6h | v1 demo `1/frontend/src/views/operation/` 迁移 |

**前端共用改动**：
| A-2.2.9 | `src/router/index.js` | +12 | 0.5h | 追加 4 个子路由（channel/invoice/finance/operation） |
| A-2.2.10 | `src/views/index.vue`（或 dashboard.vue） | +10 | 0h | 顶部导航/面包屑显示 |

### 2.3 数据库 SQL（4 个新增 / 1 个编辑）

| # | 文件 | 工作量 |
|---|------|--------|
| A-2.3.1 | `sql/biz_channel_init.sql` | 0.5h（与 A-2.1.6 合并计算） |
| A-2.3.2 | `sql/biz_invoice_init.sql` | 0.5h |
| A-2.3.3 | `sql/biz_finance_init.sql` | 0.5h |
| A-2.3.4 | `sql/biz_operation_init.sql` | 0.5h |
| A-2.3.5 | `sql/biz_menus_roles_init.sql` | +1h（追加 4 个菜单 + 角色关联） |

---

## 三、关键业务逻辑详解

### 3.1 channel 渠道管理

#### 数据库表设计

```sql
CREATE TABLE biz_channel (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '渠道ID',
  channel_code VARCHAR(50) NOT NULL UNIQUE COMMENT '渠道编码',
  channel_name VARCHAR(100) NOT NULL COMMENT '渠道名称',
  category VARCHAR(20) NOT NULL COMMENT '渠道分类（景区门票/酒店数据/综合OTA/其他）',
  contact_name VARCHAR(50) COMMENT '联系人',
  contact_phone VARCHAR(20) COMMENT '联系电话',
  commission_rate DECIMAL(5,4) DEFAULT 0 COMMENT '佣金比例（0-1）',
  status CHAR(1) DEFAULT '0' COMMENT '状态（0正常 1停用）',
  remark VARCHAR(500) COMMENT '备注',
  contract_ids VARCHAR(500) COMMENT '关联合同ID列表（JSON数组）',
  attachments JSON COMMENT '资质附件（JSON数组）',
  created_by BIGINT COMMENT '创建人ID',
  created_by_name VARCHAR(64) COMMENT '创建人姓名',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_by VARCHAR(64) COMMENT '更新人',
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_category (category),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='渠道管理表';
```

#### CSV 导入格式（D09）

```csv
渠道编码,渠道名称,分类,联系人,电话,佣金比例,备注
QD-001,同程旅行,综合OTA,张三,13800138000,0.0500,长期合作
JD-002,景区直营,景区门票,李四,13900139000,0.0000,直签
```

### 3.2 invoice 发票管理

#### 数据库表设计

```sql
CREATE TABLE biz_invoice (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  invoice_no VARCHAR(50) NOT NULL UNIQUE COMMENT '发票号',
  contract_id BIGINT NOT NULL COMMENT '关联合同ID',
  invoice_type VARCHAR(20) NOT NULL COMMENT '发票类型（增值税专用/普通/电子）',
  amount DECIMAL(18,2) NOT NULL COMMENT '开票金额',
  tax_rate DECIMAL(5,4) NOT NULL COMMENT '税率',
  tax_amount DECIMAL(18,2) NOT NULL COMMENT '税额',
  party_name VARCHAR(100) NOT NULL COMMENT '购方名称',
  party_tax_no VARCHAR(50) COMMENT '购方税号',
  status VARCHAR(20) DEFAULT 'pending' COMMENT '状态（pending/issued/void）',
  apply_date DATE COMMENT '申请日期',
  issue_date DATE COMMENT '开票日期',
  void_reason VARCHAR(500) COMMENT '作废原因',
  remark VARCHAR(500),
  created_by BIGINT,
  created_by_name VARCHAR(64),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_by VARCHAR(64),
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_contract_id (contract_id),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票管理表';
```

### 3.3 finance 财务管理

```sql
CREATE TABLE biz_finance_entry (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  entry_no VARCHAR(50) NOT NULL UNIQUE COMMENT '流水号',
  entry_type VARCHAR(20) NOT NULL COMMENT '类型（payable/receivable）',
  invoice_id BIGINT COMMENT '关联发票ID',
  contract_id BIGINT COMMENT '关联合同ID',
  amount DECIMAL(18,2) NOT NULL COMMENT '金额',
  account VARCHAR(50) COMMENT '银行账号',
  account_name VARCHAR(100) COMMENT '账户名',
  transaction_date DATE COMMENT '交易日期',
  cleared TINYINT DEFAULT 0 COMMENT '是否已对账（0否 1是）',
  remark VARCHAR(500),
  created_by BIGINT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_entry_type (entry_type),
  INDEX idx_cleared (cleared),
  INDEX idx_transaction_date (transaction_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务台账表';

CREATE TABLE biz_bank_statement (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  batch_no VARCHAR(50) NOT NULL COMMENT '导入批次号',
  transaction_date DATE NOT NULL,
  account VARCHAR(50) NOT NULL,
  amount DECIMAL(18,2) NOT NULL,
  counterparty VARCHAR(100) COMMENT '交易对手',
  remark VARCHAR(200),
  matched TINYINT DEFAULT 0 COMMENT '是否已匹配财务流水',
  matched_entry_id BIGINT COMMENT '匹配的财务流水ID',
  import_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  imported_by BIGINT,
  INDEX idx_batch_no (batch_no),
  INDEX idx_transaction_date (transaction_date),
  INDEX idx_matched (matched)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='银行对账单导入表';
```

### 3.4 operation 经营数据

```sql
CREATE TABLE biz_operation (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  period VARCHAR(20) NOT NULL COMMENT '周期（如 2026-07 / 2026-Q3 / 2026）',
  period_type VARCHAR(20) NOT NULL COMMENT '周期类型（month/quarter/year）',
  revenue DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '营收',
  cost DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '成本',
  gross_profit DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '毛利',
  customer_count INT DEFAULT 0 COMMENT '客户数',
  contract_count INT DEFAULT 0 COMMENT '合同数',
  avg_order_value DECIMAL(18,2) DEFAULT 0 COMMENT '客单价',
  remark VARCHAR(500),
  created_by BIGINT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_period_type (period, period_type),
  INDEX idx_period_type (period_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='经营数据表';
```

---

## 四、菜单与权限分配

### 4.1 menu_id 分配（与路线 B 互斥）

```
menu_id=9   渠道管理     path=biz/channel    icon=share
menu_id=10  发票管理     path=biz/invoice    icon=ticket
menu_id=11  财务管理     path=biz/finance    icon=money
menu_id=12  经营数据     path=biz/operation  icon=data-line
```

### 4.2 perms 分配

```
biz:channel:list    biz:channel:add    biz:channel:edit    biz:channel:delete    biz:channel:import
biz:invoice:list    biz:invoice:add    biz:invoice:edit    biz:invoice:delete    biz:invoice:issue    biz:invoice:void
biz:finance:list    biz:finance:add    biz:finance:edit    biz:finance:delete    biz:finance:import
biz:operation:list  biz:operation:add  biz:operation:edit  biz:operation:delete  biz:operation:comparison
```

### 4.3 角色挂菜单

- admin（role_id=1，role_sort=0）：挂全部菜单 + 全部权限
- 业务经办（uid=101）：挂 channel 列表
- 财务经办/复核（uid=104/105）：挂 invoice + finance 全部权限
- 供管负责人（uid=106）：挂 channel 全部权限

---

## 五、端到端验收清单

### 5.1 单元验收（每个模块独立）

| 模块 | 验收动作 | 预期结果 |
|------|---------|---------|
| channel | 新建渠道 → 列表显示 → 编辑 → 删除 | OK |
| channel | CSV 导入 5 条 | 列表显示 5 条新记录 |
| channel | 删除有合同关联的渠道 | 拒绝删除，提示"请先解除合同关联" |
| invoice | 为已审批通过的合同开发票 | 成功，状态 pending |
| invoice | 开票 → 标记已开 → 作废 | 状态正常流转 |
| invoice | 开票金额超过合同金额 | 拒绝，提示"开票金额不能超过合同金额" |
| finance | 导入银行对账单 CSV | 成功，状态 unmatched |
| finance | 手动新建入账记录，关联发票 | 成功 |
| operation | 新建 2026-07 月报 | 成功，毛利自动计算 |
| operation | 查看同比环比 | 2026-07 vs 2025-07 自动计算 |

### 5.2 业务链端到端验收

```
步骤 1：biz_handler(uid=101) 创建合同 HT-2026-009
步骤 2：业务经办提交 → 7 级审批通过
步骤 3：admin 把 HT-2026-009 分配到「同程旅行」(channel_id=1) + 「景区直营」(channel_id=2)
步骤 4：财务经办(uid=104) 为 HT-2026-009 开票 → 标记已开票
步骤 5：财务经办导入 7 月银行对账单 CSV，匹配入账
步骤 6：管理员登记 2026-07 月报：
   - 营收：包含 HT-2026-009 的开票金额
   - 客户数：1（来自 HT-2026-009 的客户）
   - 合同数：1
步骤 7：查看同比环比：2026-07 vs 2025-07

预期：所有步骤成功，无报错；驾驶舱数据可被路线 B 直接读取
```

### 5.3 性能验收

- 渠道列表 1000 条数据，分页响应 < 500ms
- CSV 导入 1000 条，< 5s
- 发票列表分页 100 条，< 300ms

---

## 六、与路线 B 的边界确认

| 项目 | 路线 A 处理 | 路线 B 处理 |
|------|----------|----------|
| `biz_channel` 表 | A 写 | B 只读（驾驶舱聚合查询）|
| `biz_invoice` 表 | A 写 | B 只读 |
| `biz_finance_entry` 表 | A 写 | B 只读 |
| `biz_operation` 表 | A 写 | B 只读 |
| `src/router/index.js` | A 只追加 channel/invoice/finance/operation 4 行 | B 只追加 cockpit/dashboard/profile/system 4 行 |
| `sql/biz_menus_roles_init.sql` | A 追加 menu_id 9-12 | B 追加 menu_id 13-16 |
| `module_biz/enums.py` | A 追加 4 个 enum | B 不动 |
| `module_biz/__init__.py` | 阶段 0 已注册，路线 A 不动 | 同左 |

---

## 七、风险与回退方案

| 风险 | 触发条件 | 回退方案 |
|------|---------|---------|
| channel CSV 导入性能差 | 1000 条 > 10s | 改为分批 INSERT，每批 100 条 |
| invoice 与合同强约束导致历史数据导入失败 | 老系统发票与合同 1:N | 改为弱关联（允许重复） |
| finance 银行对账单 CSV 格式不统一 | 各银行格式差异大 | 设计灵活解析器，支持字段映射 |
| operation 同比环比计算错误 | 跨年数据 | 加 period 维度校验 |
| 4 个 controller 注册冲突 | 路线 B 抢先注册 | 阶段 0 一次性注册好 |

---

## 八、关联文档

- [并行开发路线总览](./00-并行开发路线总览.md)
- [路线 B 详细方案：大屏可视化优先](./路线B-大屏可视化优先.md)
- 开发进度台账 v2.9 → `docs/04-开发/开发进度台账.md`
- v1 demo 参考源码 → `1/frontend/src/views/{channel,invoice,operation}/`、`1/backend/app/models/{channel,invoice}.py`
- ADR 决策记录 → `docs/04-开发/ARD/ADR-架构决策记录.md` D05/D09/D10/D11