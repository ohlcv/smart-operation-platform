# 文档变更记录

所有项目文档的版本变更历史。

---

## 2026-07-11 — v3.0 API 字段命名一致性重构（ADR D24 落地）

### 重大变更

**全站 JSON 字段统一 camelCase**（ADR D24）。`module_biz` 业务模块原本走 snake_case JSON（`contract_no` / `customer_name` / `current_role_label` 等），与 `module_admin`（RuoYi 原生 camelCase）不一致；本次重构统一为 camelCase，删除前后端混用的隐患。

### 代码变更

**后端**
- `module_biz/entity/vo/contract_vo.py`：`ContractBaseModel` 启用 `alias_generator=to_camel` + `populate_by_name=True`；移除 snake_case 偏离说明
- `module_biz/entity/vo/customer_vo.py`：`_Base` 启用 `alias_generator=to_camel` + `populate_by_name=True`
- `module_biz/entity/do/customer_do.py`：新增 `customer_code` 列（VARCHAR(50) UNIQUE，业务编号 KH-NNN）
- `module_biz/dao/customer_dao.py`：新增 `get_by_customer_code`、`get_max_customer_seq` 方法；list_page 关键字搜索支持 customer_code
- `module_biz/service/customer_service.py`：重写以支持 `customer_code` 自动生成与冲突校验
- `sql/biz_init.sql`：`biz_customer` 表新增 `customer_code` 列 + UNIQUE 索引；演示数据回填 `KH-001~KH-005`

**前端**
- `src/views/biz/contract/index.vue`：所有字段重命名为 camelCase（`contractNo` / `contractTypeLabel` / `customerName` / `partyB` / `signDate` / `businessType` / `statusLabel` / `currentRoleLabel`）
- `src/views/biz/customer/index.vue`：所有字段重命名为 camelCase（`customerCode` / `customerName` / `contactName` / `contactPhone` / `qualificationFiles`）；新增 `customerCode` 表单字段（编辑禁用）
- `src/api/biz/contract.js`：Query 参数 camelCase（`contractNo` / `excludeId`）
- `src/components/ContractDetailDrawer.vue`：占位注释列出后续接入的 camelCase 字段清单

### 文档变更

- `04-开发/ARD/ADR-架构决策记录.md` v1.1 → **v1.2**：新增 **D24「API 字段命名一致性」**（决策项 + 完整记录：问题 / 决策 / Rationale / 实现方式 / 字段映射示例 / 影响范围）
- `03-设计/API设计文档.md` §1.4：加强为强约束，标注 ADR D24 引用
- `04-开发/开发进度台账.md` v2.2 → **v2.3**：3.1、3.3、7.5、7.6 状态 🟢；变更记录追加本次重构
- `CHANGELOG.md`（本文件）：追加 v3.0 记录

### 兼容性保障

- `populate_by_name=True` 保留：老客户端若仍发 snake_case 字段，后端能继续接受（自动 fallback）
- `as_query` 装饰器读取 `model_field.alias`：自动接收 camelCase Query 参数（无需前端手工调字段名）
- 数据库列名（snake_case）未改动：与 ORM 100% 对齐，无迁移脚本

### 受影响范围

| 层级 | 改动 | 风险 |
|------|------|------|
| 前端字段引用 | 5 个文件改动 | 🟢 已逐字段核对 |
| 后端序列化 | 2 个 VO 文件 | 🟢 沿用 RuoYi 原生方案 |
| 数据库 schema | 1 个新列 + 唯一索引 | 🟡 新部署执行 `biz_init.sql` 即可 |
| 业务逻辑 | customer_service 加 KH-NNN 自动生成 | 🟢 简单 seq 查询，无并发风险 |
| 文档 | 4 份同步更新 | 🟢 |

---

## 2026-07-10 — v2.3 施工前准备完成

### 代码变更

**后端骨架 — `ruoyi-fastapi-backend/module_biz/`**
- 新建 `module_biz/` 目录及子层 `controller/dao/service/entity/do/entity/vo`
- 创建 `biz_controller.py`：stub 路由 `/biz/health`，遵循 `APIRouterPro` 规范，可被自动扫描注册
- 各子层 `__init__.py` 占位文件

**前端骨架 — `ruoyi-fastapi-frontend/src/views/biz/`**
- 新建 9 个业务子模块目录：`contract/approval/customer/channel/invoice/finance/operation/ota/dashboard`
- 每个子目录含 `index.vue` stub 页面，标注 `<!-- TODO: 实现... -->`

### 文档变更

- `03-设计/API设计文档.md` v1.1：新增三个章节
  - **十一、财务记录模块**（11.1~11.6）：财务记录 CRUD + 银行对账 CSV 导入 + 统计
  - **十二、OTA 数据导入模块**（12.1~12.3）：渠道订单 CSV 导入 + 导入记录查询 + 订单查询
  - **十三、仪表盘模块**（13.1~13.4）：合同统计 + 渠道收入排行 + 经营数据趋势 + 仪表盘首页聚合
  - 章节编号顺延：十一→十四，十二→十五，十三→十六
- `04-开发/开发进度台账.md` v2.1：R3/R4 🔴 风险标注为 ✅ 已解决

---

## 2026-07-10 — v2.3 骨架搭建 + API 文档补全

### 代码改动

- `ruoyi-fastapi-backend/module_biz/`：新建完整业务模块骨架，包含 `controller/dao/service/entity/do&vo` 目录、`__init__.py`、`biz_controller.py` stub（`/biz/health` 健康检查，被 APIRouterPro 自动扫描注册）
- `ruoyi-fastapi-frontend/src/views/biz/`：新建 9 个业务子模块目录 `contract/approval/customer/channel/invoice/finance/operation/ota/dashboard`，每个含 `index.vue` stub

### 文档修订

- `04-开发/开发进度台账.md` v2.0 → v2.1：R3/R4 风险标记为 ✅ 已解决
- `03-设计/API设计文档.md` v1.0 → v1.1：新增第十一/十二/十三章（财务记录 6 个 API / OTA 导入 3 个 API / 仪表盘 4 个 API），章节编号顺延（通用接口→十四，权限标识→十五，对应关系→十六）

---

## 2026-07-10 — v2.2 台账精细化 + ADR D23 登录页决策

### 新增文档/决策

- `02-现状与技术评估/ADR-架构决策记录.md` 新增 **D23**：前端登录页采用 `src/views/login/index.vue` 目录结构，删除 RuoYi 原生单文件 `login.vue`，路由引用改为 `import('@/views/login/index.vue')`；见 ADR §2 D23

### 文档修订

- `04-开发/开发进度台账.md` v1.0 → v2.0：从模块级细化到**文件级**，79 个目标文件逐一追踪；新增目标路径树（后端/前端/v1 demo 三份）、跨模块文件清单（9 个共用关键文件）、文件级里程碑验收条件表；台账 v1.0 R1 风险已解决
- `03-设计/demo模块迁移重构.md`：修正 3 处"替换 RuoYi login.vue"含糊表述，明确为"删除单文件 + 新建 login/ 目录"（与 ADR D23 对齐）
- `02-现状与技术评估/ADR-架构决策记录.md` v1.0 → v1.1：新增 D23 及影响矩阵条目

---

## 2026-07-10 — v2.1 新增开发台账

### 新增文档

- `04-开发/开发进度台账.md` — 模块进度追踪、里程碑管理、工时统计、风险登记，基于概要设计文档 v3.0 模块清单和 RuoYi 重构方案 v1.0 工时估算

### 文档修订

- `03-设计/概要设计文档.md` v3.0 → v3.1：修复 13 处设计一致性问题（详见本文档 v2.1 修订说明）

---

## 2026-07-10 — v2.0 文档体系重构

### 重大变更

**文档目录重组**
- 原有5份文档重新分类到标准SDLC目录结构
- 新增 `01-需求/`、`03-设计/`、`04-开发/`、`05-测试/`、`06-部署与交付/` 等目录

### 文档迁移记录

| 原位置 | 新位置 | 动作 |
|--------|--------|------|
| `需求规格说明书.md` | `01-需求/SRS-需求规格说明书.md` | 重命名+修复矛盾 |
| `需求分析文档.md` | `02-现状与技术评估/v1现状盘点.md` | 重命名 |
| `问题诊断与解决方案.md` | `02-现状与技术评估/技术债务清单.md` | 重命名+修复矛盾 |
| `重构可行性分析报告.md` | `02-现状与技术评估/RuoYi重构可行性报告.md` | 重命名 |
| `7级审批流与科技感UI重构方案.md` | `03-设计/核心模块迁移分析.md` | 重命名 |

### 矛盾修复记录

| 问题 | 修复方案 |
|------|----------|
| 数据库选型不一致（SQLite/PostgreSQL vs MySQL） | 统一为 MySQL 8.0 |
| 代码文件数不一致（98 vs 80） | 统一为约 80 个 |
| 工时估算不一致 | 统一各文档工时数字 |
| 验收清单编号重复（63-65） | 重新编号（74-80） |
| 需求规格说明书范围过宽 | 新增范围说明章节 |

### 新增文档

- `docs/README.md` - 文档地图和阅读指南
- `docs/CHANGELOG.md` - 变更记录

---

## 2026-07-09 — v1.2 需求分析修订

### 修订内容
- AI诊断描述修正：规则引擎（基于真实数据）非纯Mock
- 审批单打印状态更正：已实现
- 用户管理CRUD状态更正：仅列表查看
- 新增审批流增强需求（撤回/转交/加签/会签）
- 数据总需求从35增至42个，工时从70h增至97h

---

## 2026-07-09 — v1.1 问题诊断修订

### 修订内容
- 数据库选型从"SQLite/PostgreSQL"更正为"MySQL 8.0"
- 代码文件数从"98个"更正为"约80个"
- P1工时从"14小时"调整为"10小时"
- 总工时从"29-32小时"调整为"25-28小时"

---

## 2026-07-09 — v1.0 初始版本

### 新增文档
- 需求分析文档 v1.0
- 问题诊断与解决方案 v1.0
- 重构可行性分析报告 v1.0
- 7级审批流与科技感UI重构方案 v1.0
- 需求规格说明书 v1.0

---

*格式说明：使用 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 约定*
