# 路线 A 业务闭环优先（v3.0 完成报告）

> 文档版本：v2.0（完成报告）
> 原始创建：2026-07-11 23:00（按"待开发"假设撰写）
> 现实更新：2026-07-12 00:10（按 commit `8eab8f0` 实际成果重写）
> 文档定位：路线 A 「合同→渠道→发票→财务→经营数据」业务闭环的**真实交付清单**。

---

## 一、交付概要

| 维度 | 数据 |
|------|------|
| Commit hash | `8eab8f0` |
| Commit 标题 | `feat(module_biz): 业务闭环 4 模块（路线 A：channel/invoice/finance/operation）` |
| 新增文件 | **35 个**（后端 20 + 前端 8 + SQL 4 + 共用 3）|
| 后端模块 | channel / invoice / finance / operation 4 个完整 CRUD |
| 菜单 | menu_id=12 (channel) / 14 (invoice) / 15 (finance) / 16 (operation) |
| 工作量 | 1 个会话内完成（v3.0 备注：~50 min 实际工时 + 静态层冒烟）|
| 路由新增 | /biz/* 总 49 条新增，路线 A 贡献 29 条 |

---

## 二、详细交付清单（与初始假设对比）

### 2.1 后端（20 文件）

| 模块 | do | vo | dao | service | controller | 行数估算 |
|------|----|----|-----|---------|------------|---------|
| **channel** | ✅ 60 行 (`channel_do.py`) | ✅ 120 行 (`channel_vo.py`) | ✅ 80 行 (`channel_dao.py`) | ✅ 200 行 (`channel_service.py`) | ✅ 100 行 (`channel_controller.py`) | ~9.4KB total |
| **invoice** | ✅ 70 行 (`invoice_do.py`) | ✅ 130 行 (`invoice_vo.py`) | ✅ 100 行 (`invoice_dao.py`) | ✅ 250 行 (`invoice_service.py`) | ✅ 100 行 (`invoice_controller.py`) | ~29KB total |
| **finance** | ✅ 80 行 (`finance_do.py`) | ✅ 150 行 (`finance_vo.py`) | ✅ 120 行 (`finance_dao.py`) | ✅ 280 行 (`finance_service.py`) | ✅ 120 行 (`finance_controller.py`) | ~32KB total |
| **operation** | ✅ 80 行 (`operation_do.py`) | ✅ 140 行 (`operation_vo.py`) | ✅ 100 行 (`operation_dao.py`) | ✅ 260 行 (`operation_service.py`) | ✅ 110 行 (`operation_controller.py`) | ~26KB total |

**自动注册**：`module_biz/__init__.py` 引用了「由 `common/router.py auto_register_routers` 自动扫描 `module_biz/controller/`」机制。所有 controller 类无需手动 import 注册。

### 2.2 SQL 初始化（4 文件）

| 文件 | 表 | 关键设计 |
|------|----|---------|
| `sql/biz_channel_init.sql` | `biz_channel` | 4 渠道分类（meituan/douyin/ctrip/tongcheng 与字典对齐）；单字段多合同 ID 用 JSON 存 |
| `sql/biz_invoice_init.sql` | `biz_invoice` | 1:1 关联合同（合同 ID + 发票号唯一约束）；状态机 pending→issued→void |
| `sql/biz_finance_init.sql` | `biz_finance_entry` + `biz_bank_statement` | 流水台账 + 银行对账单 2 张表分离（按月汇总 + 匹配状态） |
| `sql/biz_operation_init.sql` | `biz_operation` | UNIQUE KEY (period, period_type) 防止月/季/年重报 |

### 2.3 前端（8 文件）

| 模块 | api | view | 行数 |
|------|------|------|------|
| **channel** | `src/api/biz/channel.js` | `src/views/biz/channel/index.vue` | **417 行** |
| **invoice** | `src/api/biz/invoice.js` | `src/views/biz/invoice/index.vue` | **377 行** |
| **finance** | `src/api/biz/finance.js` | `src/views/biz/finance/index.vue` | **394 行** |
| **operation** | `src/api/biz/operation.js` | `src/views/biz/operation/index.vue` | **370 行** |

**前端路由**：在 `/biz` 父路由下追加 4 个子路由（`'channel' / 'invoice' / 'finance' / 'operation'`）。

### 2.4 共用文件编辑（3 文件）

| 文件 | 改动 |
|------|------|
| `src/router/index.js` | `/biz` children 一次性追加 4 个子路由 + 把 v2.9 的 contract/customer 路由补全（这是 v2.9 阶段就做过的，路线 A 重新排版） |
| `module_biz/enums.py` | 追加 5 个 enum：`ChannelCategoryEnum` / `InvoiceStatusEnum` / `FinanceEntryTypeEnum` / `OperationPeriodEnum` / `OperationBusinessLineEnum` |
| `sql/biz_menus_roles_init.sql` | 新增 menu_id=12/14/15/16 4 个菜单 + 7 业务角色挂载（admin 全菜单 + 每个业务角色挂对应业务菜单） |

---

## 三、关键业务规则（实施版）

### 3.1 channel 渠道管理

- **分类枚举**：与字典 `dict_type='channel_type'` 对齐，采用 `meituan/douyin/ctrip/tongcheng`（最初草稿用了 ticket/hotel/ota/other，**已调整以保持与字典一致**）
- **删除约束**：关联合同不允许删除（service 层校验抛 4xx 错）
- **CSV 导入**：依据 D09 决策，先做 CSV 兜底（路径：`POST /biz/channel/import`）
- **状态字段**：`status='0'` 正常 / `'1'` 停用

### 3.2 invoice 发票管理（D11 实现）

- **1:1 关联合同**：DB 层 UNIQUE 约束 `idx_contract_id`，**发票号唯一键**
- **状态机**：
  ```
  pending ──issue──► issued ──void──► void
     │                                 ▲
     └───────────reject─────────────────┘
  ```
- **金额校验**：`amount <= contract.amount`
- **日期校验**：`issue_date >= apply_date`
- **税额自动计算**：价外税（含税金额 → 不含税金额 → 税额）

### 3.3 finance 财务管理（D10 实现）

- **2 张表分离**：
  - `biz_finance_entry` —— 业务台账（应付/应收）
  - `biz_bank_statement` —— 银行对账单导入表
- **对账流程**：导入银行对账单 → 标记 matched → 已对账不可编辑/删除
- **按月汇总**：`GET /biz/finance/summary` 应收/应付/已对账/未对账 4 维度

### 3.4 operation 经营数据（D05 实现）

- **手工录入**：当前阶段与合同**不自动汇总**（D05 决策）
- **毛利 = 营收 - 成本**：实时计算，不存 DB
- **同比环比**：跨年边界处理（2026-01→2025-12、2026-Q1→2025-Q4、2025-09→2024-09 同月、2025-Q3→2024-Q3 同季）

---

## 四、关键 bug 修复与设计调整（v3.0 hotfix）

> 以下是 v3.0 commit message 里记录的"v3.0 hotfix（菜单 SQL）"段，实际是与原路线图最不一致的几点：

1. **menu_id 错位**：早期版本错把 channel/invoice/finance/operation 写成 menu_id 9-11，与审批菜单 menu_id=8 冲突。**已 DELETE 清理 9-11**，改用 **12/14/15/16 让出 13 给路线 B 战略驾驶舱**。
2. **parent_id**：从 `parent_id=0`（顶级）改为 `parent_id=5`（业务管理父菜单），与审批 menu_id=8 风格一致。
3. **path 路径**：必须写**完整路径** `biz/channel`（含父级前缀），与 v2.6 修正后的 contract/customer 风格一致。最初草稿写的是 `channel`，**已修正**。
4. **perms 去掉 `biz:` 前缀**：与 controller `UserInterfaceAuthDependency` 一致，例如 `channel:list` 而不是 `biz:channel:list`。
5. **ChannelCategoryEnum 命名**：草稿 `ticket/hotel/ota/other` → **改为 `meituan/douyin/ctrip/tongcheng`**，与 sys_dict_data dict_type='channel_type' 对齐。

---

## 五、静态层冒烟（已 PASS）

| 检查项 | 通过依据 |
|--------|---------|
| 5 张表 ORM 字段与 SQL 100% 对齐 | DAO 层 SELECT 通过 `column.name` 反射对比无错 |
| Pydantic camelCase 序列化 | 所有 VO 启用 `alias_generator=to_camel` + `model_dump(by_alias=True)` |
| 5 个枚举中文 label | `enum.Enum` 的类属性 `__doc__` 提供 label |
| 同比环比 period 移位 | 2026-01→2025-12（年减 1）、2026-Q1→2025-Q4、2025-09→2024-09（同月减 1 年）|
| 路由注册总数 | FastAPI `/biz/*` 总 49 条，路线 A 贡献 29 条（4 模块合计）|
| 权限注解 | 7 个业务角色已挂对应菜单 + perms |

**运行时端到端**：MySQL+服务启动后端到端验收待后续在 Day 5 末尾执行（详见台账 v2.9 / v3.0）。

---

## 六、剩余 & 后续

| 项目 | 状态 |
|------|------|
| 后端单元测试 | ⏳ 未做（单测 ≥80% 覆盖率要求）|
| E2E Playwright 测试 | ⏳ 未做 |
| 性能压测 | ⏳ 未做（路线 A 验收清单列了 ≤ 500ms/≤ 5s 阈值）|

---

## 七、关联文档

- [路线总览（v3.0/v3.1 完成报告）](./00-并行开发路线总览.md)
- [路线 B 完成报告](./路线B-大屏可视化优先.md)
- [开发进度台账 v2.9 / v3.0 / v3.1 条目](../../开发进度台账.md)
- [ADR D05/D09/D10/D11](../../ARD/ADR-架构决策记录.md)
- 原始「操作手册」草稿（归档作参考）：[操作手册-双窗口并行.md](./操作手册-双窗口并行.md)
