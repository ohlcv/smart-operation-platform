# 架构决策记录（ADR）

> 文档版本：v1.5  
> 编写日期：2026-07-12  
> 文档定位：记录项目关键架构决策、业务决策及其 rationale；作为后续开发、评审、新人 onboarding 的依据。

---

## 一、决策清单

| 序号 | 决策项 | 决策内容 | 状态 |
|------|--------|----------|------|
| D01 | 审批链级数 | 7 级业务审批链 + 隐藏超级管理员 | ✅ 已确认 |
| D02 | 超级管理员角色 | admin 为隐藏系统角色，不纳入 7 级审批链 | ✅ 已确认 |
| D03 | 审批链状态语义 | `rejected` = 已驳回待修改，可重新提交；不是草稿，不是终止态 | ✅ 已确认 |
| D04 | 合同编号生成方式 | 当前阶段采用手动输入；自动生成为后续优化项 | ✅ 已确认 |
| D05 | 经营数据与合同数据关系 | 当前阶段保持手工录入，不与合同自动汇总 | ✅ 已确认 |
| D06 | 合同甲乙方定义 | `party_a` = 甲方（客户），`party_b` = 乙方（本司） | ✅ 已确认 |
| D07 | 用户表角色模型 | `approval_role`（审批角色）与 `rbac_role_id`（RBAC 角色）分离 | ✅ 已确认 |
| D08 | 审批流实现方式 | 基于 v1 Demo 移植 + 融合 RuoYi 权限体系 | ✅ 已确认 |
| D09 | OTA 对接方式 | 先做 CSV 导入兜底，API 对接作为第二阶段 | ✅ 已确认 |
| D10 | 银行对账方式 | 手工 CSV 导入，不做直连银行 API | ✅ 已确认 |
| D11 | 发票系统对接 | 台账管理，不做真实开票对接 | ✅ 已确认 |
| D12 | 文件存储方式 | 本地文件系统，后期可升级 OSS | ✅ 已确认 |
| D13 | AI 能力选型 | 规则引擎保底 + 大模型可选 | ✅ 已确认 |
| D14 | 小程序技术栈 | 微信小程序 | ✅ 已确认 |
| D15 | 数据库选型 | MySQL 8.0 | ✅ 已确认 |
| D23 | 前端登录页文件组织 | 科技风登录页用 `login/index.vue` 目录结构，替换 RuoYi 原生 `login.vue` 单文件 | ✅ 已确认 |
| D24 | API 字段命名一致性 | JSON 请求/响应字段一律 camelCase，全站强约束；Python 用 snake_case 由 Pydantic `alias_generator=to_camel` 自动序列化 | ✅ 已确认 |
| D25 | 前端样式主题适配规范 | 所有 `.vue` 页面/组件的样式中，色值（背景/文字/边框）必须通过 Element Plus CSS 变量（`var(--el-*)`）引用；禁止硬编码 EP 调色板色值；`html.dark` 切换时自动跟随；业务语义色（警告/金额/驳回等）允许硬编码但需显式注明 | ✅ 已确认 |
| D26 | 注解层 PEP 563 forward ref 兼容性 | 凡通过 `inspect.signature(func).parameters` 解析参数类型注解的工具函数（@Log、参数名提取等），必须用 `typing.get_type_hints(func)` 解析 forward ref 后再做类型匹配；controller 启用 `from __future__ import annotations` 时注解会是字符串，原生比较会失败 | ✅ 已确认 |
| D27 | 前端顶级路由必须 redirect + 侧边栏绝对路径短路 | 顶层父路由（含 `/biz`、`/dashboard` 等独立顶级路由）必须配置 `redirect` 到第一个子路由；侧边栏 `SidebarItem.resolvePath` 必须短路以 `/` 开头的 routePath，避免与空 basePath 拼出 `//xxx` | ✅ 已确认 |
| D28 | 路线 C 仪表盘升级范围 | Pydantic 模型统一采用别名显式声明（`Field(alias='xx', serialization_alias='xx')`）优先于 `alias_generator=to_camel`，避免纯数字+字母连写的边界 case 把字段转成「首字母大写」；具体场景：`trend_7d` → 显式 alias `trend7d` | ✅ 已确认 |
| D29 | 仪表盘双形态（v3.9 双路由共用 + 浏览器真全屏，v3.10 CSS 修正 Chrome 横向滚动 / sidebar 遮挡） | v3.8 嵌入 Layout + URL query `?fullscreen=1` 切换 CSS 形态，但实测发现"应用层切 CSS ≠ 浏览器真全屏"，用户期望"全屏模式 = 真·浏览器全屏 + 去掉 Layout"。**v3.9 修订为双路由共用同一 dashboard.vue**：(1) router 保留 `/dashboard` (Layout 嵌) + 新增 `/dashboard/screen` (顶级，不嵌 Layout，`hidden:true` 菜单不显示)；(2) dashboard.vue 加 `isScreenRoute = computed(() => route.name === 'BizDashboardScreen')` 判形态；(3) 模板 `:class="{ 'is-fullscreen': isScreenRoute }"`，按钮文字 `{{ isScreenRoute ? '退出全屏' : '全屏模式' }}`；(4) `toggleFullscreen()` 默认态 → `router.push('/dashboard/screen')` + `document.documentElement.requestFullscreen()`（50ms 延迟等路由切换），大屏态 → `exitFullscreen()` + `router.push('/dashboard')`；(5) 听 `fullscreenchange` / `webkitfullscreenchange` 事件，浏览器 Esc 退出全屏时自动 `router.push('/dashboard')` 回默认；(6) onMounted 判断 `isScreenRoute && !getFullscreenElement()` 自动补一次 requestFullscreen（处理直链 / 刷新 / 浏览器后退场景）；(7) CSS 双形态：`.ds` 默认嵌 Layout（负 margin 拉满左右，无 100vh）+ `.ds.is-fullscreen` 真大屏（min-height: 100vh + margin: 0）。**v3.10 CSS 修正**：v3.9 `.ds` 用 `margin: 0 calc(50% - 50vw)` 强行溢出到 100vw，**Chrome 出现 body 横向滚动条 + 暗色背景左边被 sidebar 盖住**（Safari 行为不一致掩盖问题）；改 `.ds` 为 `width: 100%; margin: 0`，暗色背景只到 Layout 主区边界，跟其他业务页一致，不被 sidebar 遮挡，无横向溢出。**回退 v3.8**：去掉 URL query `?fullscreen=1` 持久化；去掉 fullscreen ref/computed（改用 isScreenRoute） | ✅ 已确认 |
| D31 | 仪表盘改名为仪表盘（v3.6） | 「仪表盘」产品名沿用自 v1.0 demo；v3.6 收敛为顶级路由 `/dashboard` 后页面已无「仪表盘」实体氛围，且与 dashboard.vue 文件名一致性更强，故用户视角统一改名「仪表盘」：(1) `sys_menu.menu_id=13.menu_name='仪表盘'→'仪表盘'`；(2) router meta title + dashboard.vue 顶部中文标题「数据仪表盘」→「数据仪表盘」；(3) 后端 FastAPI tag 改「业务管理-仪表盘」+ Pydantic/DAO/Service docstring 头部加「原仪表盘」回溯注释；(4) API 设计文档第十三章标题「仪表盘模块」→「仪表盘模块」；(5) **未改**：URL 路径 `/biz/dashboard/overview` 仍保留（前端 api/biz/dashboard.js 沿用），`dashboard_*.py` Python 文件名（重命名影响类名 import 全网扫描），历史 ADR 标题 D28/D29/路线 B-C 开发计划保留原标题（历史快照不改） | ✅ 已确认 |
| D30 | DAO filter 参数显式签名 | service 层用 `asyncio.gather(*DAO_calls)` 并发调用时，DAO 签名必须显式接收 filter 参数（如 `province: str = ''`），而非用 `**kwargs` 兜底；好处：① 静态层 inspect.signature 一眼看出哪些 DAO 支持哪些维度过滤；② 漏接参数时直接 TypeError 而非静默忽略；③ `if province:` 分支条件清晰可读；本规则在 `dashboard_dao.trend_7d` 漏接 province 事故中确立（v3.5） | ✅ 已确认 |

---

## 二、详细决策记录

### D01：审批链级数

**问题**：文档中曾出现"8 级审批链"和"7 级审批链"两种表述，导致开发边界不清晰。

**决策**：
- **7 级业务审批链**：业务经办 → 业务复核 → 风控审核 → 财务经办 → 财务复核 → 供管公司负责人 → 投资公司负责人
- **隐藏超级管理员**：admin 角色，不在审批链中，但拥有 bypass 权限

**Rationale**：
- 业务审批链是固定流程，必须明确级数，否则开发时无法确定步骤和状态流转
- 超级管理员是系统角色，不是业务角色，不应纳入审批链计数

---

### D02：超级管理员角色

**问题**：admin 角色是否属于 7 级审批链之一？

**决策**：admin 为隐藏超级管理员，不纳入 7 级审批链。

**Rationale**：
- 超级管理员拥有 bypass 权限，可审批任意环节，与普通审批角色在权限模型上完全不同
- 若将 admin 纳入审批链，会导致审批逻辑复杂化（需要判断"当前步骤是否为 admin"）
- 隐藏 admin 可避免业务人员误操作，仅在系统维护或紧急审批场景下使用

**实现方式**：
- `sys_user.is_superuser = True` 时，跳过审批角色校验
- 前端菜单权限：admin 可见全部菜单，但不显示在审批角色列表中

**约束补充（2026-07-11）**：`sys_role.role_sort` 取值规范 —— `0` = 隐藏超管（admin）、`1-7` = 7 级业务审批链（与 step 一一对应）、`>7` 或 `NULL` = 非审批业务角色（如 `common`，约定用 `99`）。任何审批人匹配逻辑必须先排除 `role_sort NOT IN (1..7)`，再判断 `role_sort == current_step + 1`。

**冲突历史**：RuoYi 原生 `ruoyi-fastapi.sql` 第 126 行默认 admin `role_sort=1`、common `role_sort=2`，分别与 `business_handler`（sort=1）、`business_reviewer`（sort=2）冲突，导致任何拥有 admin 或 common 角色的用户在「待我审批」判断时会被误识别为业务经办/复核。已在 `biz_menus_roles_init.sql` §0 节修正（admin→0、common→99），同步更新本决策的取值规范条款。

---

### D03：审批链状态语义

**问题**：合同驳回后，`rejected` 状态的确切语义是什么？是否可重新提交？

**决策**：
- `rejected` 语义固定为：**已驳回待修改**
- 驳回后合同回到 `rejected` 状态，业务经办可修改后重新提交
- `rejected` 不是草稿（`draft`），不是终止态

**Rationale**：
- 草稿（`draft`）表示未提交，`rejected` 表示已提交但被驳回，两者在业务语义上不同
- 保留审批记录是审计要求，不能回到草稿态（否则审批历史会丢失）
- 固定语义后，前端状态流转逻辑清晰：`rejected` → 编辑 → 提交 → `pending`

**状态流转图**：

```
draft ──提交──► pending ──审批通过──► approved
  │              │
  │              └──审批驳回──► rejected ──重新提交──► pending
  │
  └──删除──► (deleted)
```

---

### D04：合同编号生成方式

**问题**：合同编号是手动输入还是自动生成？

**决策**：当前阶段采用**手动输入**，自动生成为后续优化项（P1 优先级）。

**Rationale**：
- 手动输入可快速上线，无需额外开发编号生成规则
- 自动生成需要定义规则（年月日+序号、业务类型前缀等），需要甲方确认
- 当前 v1 Demo 也是手动输入，可快速迁移

**后续优化**：
- 定义编号规则（如：`HT-2026-001`）
- 考虑并发场景下的序号唯一性
- 支持按业务类型前缀（如：`BW-` 业务审批单，`FK-` 付款审批单）

---

### D05：经营数据与合同数据关系

**问题**：经营数据是手工录入还是与合同自动汇总？

**决策**：当前阶段保持**手工录入**，不与合同自动汇总。

**Rationale**：
- 自动汇总需要复杂的 ETL 逻辑，且经营数据维度（年月+业务线）与合同数据不完全匹配
- 手工录入可快速上线，且更灵活（可调整数据）
- v1 Demo 也是手工录入，可快速迁移

**后续优化**：
- 合同审批通过后，自动生成经营数据记录（需要定义映射规则）
- 支持从发票、渠道数据自动聚合

---

### D06：合同甲乙方定义

**问题**：`party_a` 和 `party_b` 哪个是本司，哪个是客户？

**决策**：
- `party_a` = **甲方（客户）**
- `party_b` = **乙方（本司）**

**Rationale**：
- 数据库设计已按此定义，且与 v1 Demo 的实际填法一致
- 中国合同法惯例：甲方通常为委托方/客户，乙方为提供服务方/本司
- 前端表单字段名保持 `party_a`、`party_b`，但在界面上显示为"甲方（客户）"、"乙方（本司）"

---

### D07：用户表角色模型

**问题**：v1 Demo 的 `sys_user.role` 是单角色字段，同时承担审批角色和菜单权限角色；是否分离？

**决策**：**分离审批角色与 RBAC 角色**。

**Rationale**：
- 审批角色（7 级）是固定业务链，用于判断"谁能审批"
- RBAC 角色是菜单/按钮权限，用于判断"谁能看什么"
- 两者解耦后，可灵活调整菜单权限，不影响审批流
- 例如：业务经办可以分配"财务管理"菜单权限，但仍然是业务经办审批角色

**实现方式**：
- `sys_user.approval_role`：审批角色（`business_handler` 等）
- `sys_user.rbac_role_id`：RBAC 角色 ID（关联 `sys_role` 表）
- `sys_user.is_superuser`：超级管理员标识

---

### D08：审批流实现方式

**问题**：审批流是基于 RuoYi Flowable，还是基于 v1 Demo 移植？

**决策**：基于 **v1 Demo 移植 + 融合 RuoYi 权限体系**。

**Rationale**：
- RuoYi FastAPI 版本没有成熟的 Flowable 审批流模块
- v1 Demo 已有完整的 7 级审批流实现，可直接移植
- 融合 RuoYi 权限体系后，可复用 RuoYi 的用户、角色、菜单管理

**技术路线**：
- 后端：移植 v1 的 `contract.py` endpoint，适配 RuoYi 的认证和权限依赖
- 前端：移植 v1 的合同页、审批页、详情抽屉
- 审批链角色映射到 RuoYi 的 `sys_role` 表

---

### D09：OTA 对接方式

**问题**：OTA 平台（美团/抖音）对接，是 API 对接还是 CSV 导入？

**决策**：**先做 CSV 导入兜底，API 对接作为第二阶段**。

**Rationale**：
- OTA 平台接口申请周期长，且需要甲方配合申请资质
- CSV 导入可快速上线，满足基本业务需求
- API 对接需要额外开发定时任务、错误处理、数据清洗等

---

### D10：银行对账方式

**问题**：银行对账是直连银行 API 还是 CSV 导入？

**决策**：**手工 CSV 导入，不做直连银行 API**。

**Rationale**：
- 甲方无银行对公账户 API 对接资质
- 银行 API 对接涉及金融合规问题，需要额外审批
- CSV 导入可满足当前业务需求

---

### D11：发票系统对接

**问题**：发票系统是台账管理还是对接税务系统？

**决策**：**台账管理，不做真实开票对接**。

**Rationale**：
- 对接税务系统（金税四期）需要额外资质和开发成本
- 台账管理可满足当前业务需求（记录发票信息、统计）
- 长期可升级对接全电发票系统

---

### D12：文件存储方式

**问题**：文件存储是本地文件系统还是 OSS？

**决策**：**本地文件系统，后期可升级 OSS**。

**Rationale**：
- 本地文件系统部署简单，无需额外配置
- 后期可无缝升级到阿里云 OSS 或 MinIO

---

### D13：AI 能力选型

**问题**：AI 能力是规则引擎还是大模型？

**决策**：**规则引擎保底 + 大模型可选**。

**Rationale**：
- 规则引擎稳定、成本低、可解释性强，适合风险识别等确定性场景
- 大模型成本高、不可控，适合对话、投前分析等开放式场景
- 当前阶段先实现规则引擎，大模型作为可选项

---

### D14：小程序技术栈

**问题**：移动审批是微信小程序还是 H5？

**决策**：**微信小程序**。

**Rationale**：
- 审批场景适合小程序（即用即走、消息推送、手写签名）
- H5 在微信中体验不如小程序
- 与 Web 端共用后端 API，仅前端不同

---

### D15：数据库选型

**问题**：数据库是 MySQL 还是 PostgreSQL？

**决策**：**MySQL 8.0**。

**Rationale**：
- RuoYi 对 MySQL 支持更好，文档和社区资源更丰富
- 甲方现有系统多用 MySQL，运维成本低
- 项目初期无需 PostgreSQL 的高级特性

---

### D23：前端登录页文件组织

**问题**：RuoYi 前端登录页是单文件 `src/views/login.vue`，v1 Demo 登录页是目录 `src/views/login/index.vue`；科技风登录页迁移后应采用哪种组织方式？

**决策**：**采用目录结构 `src/views/login/index.vue`，替换 RuoYi 原生单文件 `login.vue`**。

**Rationale**：
- v1 Demo 所有页面均采用「目录 + index.vue」风格（`contract/`、`approval/`、`screen/` 等），登录页保持一致有利于代码库风格统一，降低迁移后维护复杂度
- RuoYi 原生系统页面（`views/system/`、`views/monitor/`）采用目录风格，登录页改用目录后与 RuoYi 业务模块风格对齐
- 目录结构为后续登录相关子组件（`components/LoginForm.vue`、`components/RegisterDialog.vue`）留出扩展空间
- v1 Demo 的登录页代码行数仅 170 行，单文件体积小，目录开销可忽略

**实现方式**：
1. 删除 RuoYi 原生 `src/views/login.vue`
2. 新建目录 `src/views/login/`，放入 `index.vue`
3. 在 `src/router/index.js` 中将路由引用从 `import('@/views/login.vue')` 改为 `import('@/views/login/index.vue')`
4. v1 Demo 登录页中引用的图片/样式资源需同步迁移到 `src/assets/` 下

**状态流转**：🔴 已决策，待实施

---

## 三、决策影响矩阵

| 决策 | 影响模块 | 影响范围 | 是否需要重构 |
|------|----------|----------|--------------|
| D01 | 审批流、权限模型 | 全系统 | 否 |
| D02 | 用户管理、审批流 | 用户模块、审批流 | 否 |
| D03 | 合同管理、审批流 | 合同状态流转 | 否 |
| D04 | 合同管理 | 合同创建 | 否（当前手动） |
| D05 | 经营数据、战略总览 | 数据聚合 | 否（当前手工） |
| D06 | 合同管理、数据库设计 | 合同表字段 | 否 |
| D07 | 用户管理、权限模型 | 用户表设计 | 是（已设计） |
| D08 | 审批流、前后端 | 全系统 | 否 |
| D09 | 渠道管理 | 渠道模块 | 否 |
| D10 | 财务管理 | 财务模块 | 否 |
| D11 | 发票管理 | 发票模块 | 否 |
| D12 | 客户管理、合同管理 | 文件存储 | 否 |
| D13 | AI 模块 | AI 诊断、对话 | 否 |
| D14 | 小程序 | 移动端 | 否 |
| D15 | 数据库 | 全系统 | 否 |
| D23 | 前端登录页 | 路由、前端构建 | 否（仅文件重组） |

---

## 四、后续需确认的决策

以下决策尚未最终确定，需要在项目启动会或甲方评审会中确认：

| 序号 | 决策项 | 待确认内容 | 建议确认时间 |
|------|--------|----------|----------|
| D16 | 审批流程配置 | 是否支持可视化配置（不同业务类型走不同审批链） | 需求评审会 |
| D17 | 合同编号规则 | 自动生成规则（格式、前缀、序号规则） | 需求评审会 |
| D18 | 经营数据关联 | 后期是否自动汇总合同金额到经营数据 | 阶段三评审会 |
| D19 | OTA API 对接 | 美团/抖音 API 对接时间和资源投入 | 阶段二评审会 |
| D20 | 大模型选型 | 是否引入大模型，选择哪家厂商 | 阶段四评审会 |
| D21 | 第三方数据接口 | 是否采购企查查/天眼查类 API | 需求评审会 |
| D22 | 数据迁移范围 | 是否需要导入历史业务/财务数据 | 项目启动会 |

---

## 五、决策变更记录

| 日期 | 决策编号 | 变更内容 | 变更原因 | 变更人 |
|------|----------|----------|----------|--------|
| 2026-07-10 | D01 | 从"8 级审批链"改为"7 级审批链 + 隐藏 admin" | 文档打架，概念混淆 | 产品/技术 |
| 2026-07-10 | D03 | 明确 `rejected` 语义为"已驳回待修改" | 状态流转不清晰 | 产品 |
| 2026-07-10 | D04 | 合同编号先手动输入，自动生成为后续优化 | 快速上线 | 产品 |
| 2026-07-10 | D05 | 经营数据保持手工录入，不与合同自动汇总 | 简化一期开发 | 产品 |
| 2026-07-10 | D06 | 明确 `party_a` = 甲方（客户），`party_b` = 乙方（本司） | 字段语义不清晰 | 产品 |
| 2026-07-10 | D23 | 新增决策：前端登录页采用 `login/index.vue` 目录结构，替换 RuoYi 原生 `login.vue` 单文件 | 消除登录页迁移方案歧义，统一 v1 Demo 页面目录风格 | 产品/技术 |

---

## 六、ADR 使用指南

### 什么时候写 ADR？

- 遇到多个可行技术方案，需要做取舍时
- 业务规则不明确，需要定义清晰语义时
- 架构决策影响多个模块时
- 需求变更导致技术方案需要调整时

### ADR 格式说明

```
## 一、决策清单
所有决策的快速索引，方便查阅。

## 二、详细决策记录
每个决策的详细记录，包括：
- 问题：要解决什么问题
- 决策：最终决定是什么
- Rationale：为什么做这个决策
- 实现方式：如何在技术层面落地

## 三、决策影响矩阵
评估每个决策对系统的影响范围，帮助技术负责人评估风险和重构成本。

## 四、后续需确认的决策
记录尚未最终确定的决策，避免遗漏。

## 五、决策变更记录
记录决策的变更历史，便于追溯。
```

---

### D24：API 字段命名一致性

**问题**：项目存在两套 JSON 字段命名风格：`module_admin`（RuoYi 原生）使用 camelCase（`alias_generator=to_camel`），`module_biz` 业务模块（合同/客户）使用 snake_case。两套并存造成 API 风格不一致、前端页面混用（`system/*` 用 camelCase、`biz/*` 用 snake_case），且与 API 设计文档 §1.4 的 camelCase 强约束不一致。

**决策**：
- JSON 请求/响应字段**全站统一 camelCase**，Python 层使用 snake_case
- 后端统一通过 Pydantic `alias_generator=to_camel` + `populate_by_name=True` 自动序列化
- 数据库层保持 snake_case 不变
- URL 路径保持 kebab-case 不变
- `as_query` 装饰器读取 `model_field.alias`，自动接收 camelCase Query 参数

**Rationale**：
- 与 RuoYi 原版（yangzongzhuan/RuoYi-FastAPI CamelModel）约定一致
- 业界主流（71% 公开 REST API 使用 camelCase）
- JS/TS 前端无需 `humps` 转换层，符合 JS 属性访问习惯
- Google API 规范（AIP-140）、JSON:API 规范均推荐 camelCase
- `populate_by_name=True` 保留可同时接受 snake_case 输入，兼容老客户端

**实现方式**：
| 层级 | 命名 | 工具 |
|------|------|------|
| URL 路径 | kebab-case | 静态 |
| JSON 请求/响应 | **camelCase** | Pydantic `alias_generator=to_camel` |
| Python 类属性 | snake_case | 代码风格（PEP 8）|
| 数据库字段 | snake_case | ORM/SQL |

**字段映射示例**：
| Python（snake）| JSON（camel）|
|---|---|
| `contract_no` | `contractNo` |
| `current_role_label` | `currentRoleLabel` |
| `customer_name` | `customerName` |
| `qualification_files` | `qualificationFiles` |
| `page_num` / `page_size` | `pageNum` / `pageSize` |

**影响范围**：
- 后端：`module_biz/entity/vo/{contract,customer}_vo.py` 启用 `alias_generator=to_camel`
- 前端：`src/views/biz/{contract,customer}/` 页面字段重命名
- 前端：`src/api/biz/contract.js` Query 参数 camelCase
- 数据库：未改动（snake_case 保持）

**关联决策**：D06（甲乙方字段名 `party_a`/`party_b` 仍按 Python 层 snake_case，JSON 层自动 `partyA`/`partyB`）。

---

### D25：前端样式主题适配规范

**问题**：业务页（`biz/*`）的 `<style scoped>` 中大量硬编码 Element Plus 调色板色值（如 `#fafbfc / #f5f7fa / #909399 / #ecf5ff / #409eff` 等），在浅色模式下视觉正常，但切换到暗色模式（`html.dark`）后，这些区块底色不跟随主题，呈现「白色块漂浮在暗色页面」的视觉割裂（详见 `DEBUG/approval-dark-mode-hardcoded-colors-2026-07-11.md`）。

**决策**：

- 所有 `.vue` 页面/组件的样式中，**色值（背景/文字/边框）必须通过 Element Plus CSS 变量引用**
- 允许使用的变量形式：`var(--el-fill-color-blank)` / `var(--el-text-color-primary)` / `var(--el-border-color-lighter)` / `var(--el-color-primary-light-9)` 等 EP 全局变量
- **禁止硬编码 EP 调色板色值**（`#[0-9a-fA-F]{3,6}`），包括但不限于：`#fafbfc / #f5f7fa / #ecf5ff / #409eff / #e6a23c / #a8abb2 / #c0c4cc / #909399 / #606266 / #e4e7ed`
- `html.dark` 切换时，Element Plus `dark/css-vars.css` 自动切换所有 `--el-*` 变量，无需额外 JS 逻辑
- **业务语义色允许硬编码**：警告/金额高亮/驳回原因等有明确业务含义的红色（`#f56c6c`）等硬编码值允许保留，但须在同文件注释说明原因

**允许硬编码的例外色清单**（当前已知，后续补充）：

| 色值 | 语义 | 使用场景 | 所在文件 |
|------|------|----------|----------|
| `#f56c6c` | 警告/错误/金额高亮/驳回原因 | `.tab-badge`、`.amount-text`、`.history-item-reject` | `approval/index.vue` |

**Rationale**：

- 项目暗色主题机制已完善（`@vueuse/core useDark()` → `html.classList.add('dark')` → EP `dark/css-vars.css` 切换变量），业务页只需正确引用变量即可自动适配
- `dashboard/index.vue` 等已正确示范，biz/* 页开发时未遵循同一规范
- 台账 §五「前端 Page (.vue)」验收标准原只有「v-permission + 三态」，缺失「主题适配」维度，导致开发时无约束

**变量速查对照**（浅色/暗色切换时 EP 自动映射）：

| 用途 | 推荐变量 | 浅色典型值 | 暗色典型值 |
|------|----------|------------|------------|
| 页面/卡片底色 | `--el-fill-color-blank` | `#ffffff` | `#1d1e1f` |
| 次级区块底色 | `--el-fill-color-light` | `#f5f7fa` | `#262727` |
| 主要文字 | `--el-text-color-primary` | `#303133` | `#e8e8e8` |
| 次要文字 | `--el-text-color-secondary` | `#909399` | `#a3a6ad` |
| 常规文字 | `--el-text-color-regular` | `#606266` | `#c0c4cc` |
| 占位/禁用文字 | `--el-text-color-placeholder` | `#a8abb2` | `#8d9095` |
| 边框 | `--el-border-color` | `#e4e7ed` | `#4a4a4a` |
| 浅边框 | `--el-border-color-lighter` | `#ebeef5` | `#363637` |
| 主色浅底（标签等） | `--el-color-primary-light-9` | `#ecf5ff` | `#1e1e2e` |
| 主色文字 | `--el-color-primary` | `#409eff` | 跟随主题色 |
| 警告色 | `--el-color-warning` | `#e6a23c` | `#cf9236` |

**验收检查项**（每次业务页提交前执行）：

```bash
# 1. 扫描 .vue 文件中是否还有写死 EP 调色板色值
rg -n '#[0-9a-fA-F]{3,6}' src/views/biz/**/*.vue \
  | grep -vE 'f56c6c'  # f56c6c 是业务语义色保留

# 2. 手动：切到暗色模式，逐区块目视检查是否跟随主题
#    关注：搜索区容器 / 表单背景 / 操作摘要块 / 步骤标签 / 签名图边框
```

**关联决策**：D23（前端登录页文件组织）、D24（API 字段命名一致性）。

**关联 DEBUG**：`DEBUG/approval-dark-mode-hardcoded-colors-2026-07-11.md`（2026-07-11 审批中心暗色适配修复记录，含 3 个文件 12 处替换明细）。

---

### D26：注解层 PEP 563 forward ref 兼容性

**问题**：所有 controller（`module_biz/controller/*.py`）都启用了 `from __future__ import annotations`（PEP 563）。这把所有参数类型注解变成字符串（如 `request: Request` 在 inspect 里看到的是 `'Request'` 字符串），导致依赖 `inspect.signature(func).parameters` 解析参数类型的工具函数失效。

实测症状：`common/annotation/log_annotation.py` 的 `get_function_parameters_name_by_type(func, Request)` 在所有 `@Log` 装饰的接口上拿到空列表 `[]`，下一行 `request_name_list[0]` 直接 `IndexError: list index out of range`。**所有 `@Log` 装饰的接口都受影响**——不只是 DELETE，GET/POST/PUT 等只要走 `@Log` 就崩。HTTP 实测表现为 `code=500 msg="list index out of range"`。

**决策**：

- 凡通过 `inspect.signature(func).parameters` 解析参数类型注解的工具函数（`@Log`、参数名提取、依赖注入元编程等），必须用 `typing.get_type_hints(func)` 先解析 forward ref，**再做**类型匹配
- 解析失败时 fallback 到 `param.annotation` 字符串（不引入新崩溃，但等于原行为——属极端场景，实际未复现）
- 适用工具：`common/annotation/log_annotation.py` 的 `get_function_parameters_name_by_type`

**Rationale**：

- `from __future__ import annotations` 在本项目是 PEP 563 标准做法，前向兼容 Python 3.14，对 controller 代码可读性提升显著，不能撤
- 注解层是公共基础，被 `@Log` 这类装饰器隐式依赖；放弃 forward ref 等于放弃 `from __future__ import annotations`，代价过大
- 解析失败时静默 fallback（`get_type_hints` 抛异常 → 退回原路径）保证工具函数不会因某个极端注解而崩；真出问题时表现为"日志少了 request 信息"而非整个接口 500

**示例（修复后）**：

```python
# ruoyi-fastapi-backend/common/annotation/log_annotation.py
def get_function_parameters_name_by_type(func: Callable, param_type: Any) -> list:
    try:
        resolved_hints = get_type_hints(func)  # PEP 563 兼容：先解析 forward ref
    except Exception:
        resolved_hints = {}
    parameters_name_list = []
    for name, param in inspect.signature(func).parameters.items():
        annotation = resolved_hints.get(name, param.annotation)  # 优先用解析后的
        if annotation == param_type or (
            hasattr(annotation, '__class__')
            and annotation.__class__.__name__ == '_AnnotatedAlias'
            and annotation.__origin__ == param_type
        ):
            parameters_name_list.append(name)
    return parameters_name_list
```

**影响范围**：

- 修改：`common/annotation/log_annotation.py` 一处
- 受益：所有 `@Log` 装饰的接口（路由 49 条中绝大多数），不仅是 DELETE 路径
- 不需修改：controller 侧（保留 `from __future__ import annotations`）

**关联 DEBUG**：`DEBUG/log-annotation-future-annotations-2026-07-12.md`。

---

### D27：前端顶级路由必须 redirect + 侧边栏绝对路径短路

**问题**：vue-router 警告 `Location "//dashboard" resolved to "//dashboard". A resolved location cannot start with multiple slashes.` 在切换仪表盘菜单时反复触发。两个独立 bug 叠加：

1. **`/dashboard` 顶级路由没设 `redirect`**：访问根路径 `/dashboard` 会 404（其他顶级路由如 `/biz` 都设了 `redirect: '/biz/approval'`）。子路由 `path: 'index'` 拼出来是 `/dashboard/index`，但用户点菜单走的是 `/dashboard` 父路径。
2. **`SidebarItem.vue` 的 `resolvePath(routePath)` 拼接 bug**：
   ```js
   // 旧实现（line 79-91）
   function resolvePath(routePath, routeQuery) {
     if (isExternal(routePath)) return routePath
     if (isExternal(props.basePath)) return props.basePath
     // basePath 是父路由传下来的；顶级父路由的 basePath 是空串 ''
     return getNormalPath(props.basePath + '/' + routePath)  // '' + '/' + '/dashboard' = '//dashboard' 💥
   }
   ```
   当 `routePath` 本身已是绝对路径（以 `/` 开头，如顶级父路由 `/dashboard` 自身），`basePath=''` 时拼接会得到 `//dashboard`。

**决策**：

- **规则 1**：所有顶层父路由（含 `/biz`、`/dashboard` 等独立顶级路由）**必须**配置 `redirect: '/<first-child>'` 指向第一个子路由
- **规则 2**：`SidebarItem.vue` 的 `resolvePath` 必须短路以 `/` 开头的 `routePath`，避免与空 `basePath` 拼出 `//xxx`

**Rationale**：

- vue-router 设计上要求 path 单一 `/` 开头；双 `/` 路径在不同浏览器/代理下行为不一致（部分会被吞掉，部分会重定向到根），必须在源头避免
- 顶级父路由无 redirect 时用户直接访问 `/dashboard` 会撞到空 Layout 组件；统一 redirect 是约定俗成的 vue-element-admin 模板风格
- 侧边栏短路修复是**通用性修复**——任何顶级父路由（不只是 dashboard）都会遇到同类问题；不改就埋雷

**修复（侧边栏）**：

```vue
<!-- ruoyi-fastapi-frontend/src/layout/components/Sidebar/SidebarItem.vue -->
<script setup>
function resolvePath(routePath, routeQuery) {
  if (isExternal(routePath)) return routePath
  if (isExternal(props.basePath)) return props.basePath
  // 绝对路径直接返回，避免 basePath='' + '/'+ '/dashboard' 拼出 '//dashboard'
  if (routePath.startsWith('/')) {
    return getNormalPath(routePath)
  }
  if (routeQuery) {
    let query = JSON.parse(routeQuery);
    return { path: getNormalPath(props.basePath + '/' + routePath), query: query }
  }
  return getNormalPath(props.basePath + '/' + routePath)
}
</script>
```

**修复（dashboard 路由）**：

```js
// ruoyi-fastapi-frontend/src/router/index.js
{
  path: '/dashboard',
  component: Layout,
  redirect: '/dashboard/index',  // 补：与 /biz 的 redirect 风格一致
  permissions: ['biz:dashboard:view'],
  children: [
    { path: 'index', component: () => import('@/views/biz/dashboard/index.vue'), name: 'BizDashboard', meta: { title: '仪表盘', icon: 'pie-chart', noCache: false } }
  ]
}
```

**修复（dashboard 路由）**：

```js
// ruoyi-fastapi-frontend/src/router/index.js
{
  path: '/dashboard',
  component: Layout,
  redirect: '/dashboard/index',
  permissions: ['biz:dashboard:view'],
  children: [
    {
      path: 'index',
      component: () => import('@/views/biz/dashboard/index.vue'),
      name: 'BizDashboard',
      meta: { title: '仪表盘', icon: 'pie-chart', noCache: false }
    }
  ]
}
```

**影响范围**：

- 修改：`src/router/index.js`（dashboard 父路由补 redirect）、`src/layout/components/Sidebar/SidebarItem.vue`（resolvePath 短路）
- 受益：所有顶级父路由（不只 dashboard），未来新增 `/xxx` 顶级路由也不会再触发 `//xxx` 警告

---

### D28：路线 C 仪表盘升级 - Pydantic 别名显式声明（避坑 `trend7d`）

**问题**：路线 C 重构 dashboard 时，Pydantic `DashboardOverviewModel.trend_7d: list[Trend7dItemModel]` 由 `alias_generator=to_camel` 自动转 camelCase，实测**得到的字段名是 `trend7D`** 而不是预期的 `trend7d`：

```python
>>> from pydantic.alias_generators import to_camel
>>> to_camel('trend_7d')
'trend7D'  # 数字当词边界，首字母大写
```

前端 `dashboard.vue` 写死读 `data.trend7d`，后端返回 `trend7D`，整个趋势图**静默不显示**（`forEach` 不报错但空数组）。

**决策**：

- 所有 Pydantic 模型若字段名包含「数字+字母连写」边界（`trend_7d`、`level_3_id` 等），**必须**用 `Field(alias='xx', serialization_alias='xx')` 显式声明，**优先于** `alias_generator=to_camel`
- 普通字段（纯字母）继续走 `to_camel`，无需手写 alias
- 影响本项目唯一已知案例：`DashboardOverviewModel.trend_7d` → 显式 `alias='trend7d', serialization_alias='trend7d'`

**Rationale**：

- `to_camel` 的算法是「下划线 → 驼峰 + 每个词首字母大写」，不区分字母和数字；`trend_7d` 被解析成 `[trend][7][d]` 三个词，组合时 `d` 单独被首字母大写成 `D`
- 这是 Pydantic 的设计行为，不是 bug；社区已有同名 issue
- 显式 alias 比回避命名（`trend_sevenday`）更语义化，且不影响 `from_attributes` 模式（Python 侧仍按 `trend_7d` 访问）
- 一处显式声明闭环；未来新增字段名前先问一句「是不是数字+字母连写」即可

**修复**：

```python
# ruoyi-fastapi-backend/module_biz/entity/vo/dashboard_vo.py
class DashboardOverviewModel(DashboardBaseModel):
    kpi: DashboardKpiModel = Field(default_factory=DashboardKpiModel)
    trend_7d: list[Trend7dItemModel] = Field(
        default_factory=list,
        alias='trend7d',                      # ← 关键
        serialization_alias='trend7d',         # ← 关键（dump by_alias 用）
    )
    # 其他字段继续走 alias_generator=to_camel
```

验证：

```python
>>> DashboardOverviewModel(trend_7d=[]).model_dump(by_alias=True, mode='json').keys()
dict_keys(['channelLocations', 'generatedAt', 'kpi', 'province', 'recentApprovals',
           'statusDistribution', 'topCustomers', 'trend7d'])  # ✓ trend7d
```

**影响范围**：

- 当前唯一影响：`DashboardOverviewModel.trend_7d` 一处
- 项目其他 Pydantic 模型扫一遍，凡含「`_数字字母`」边界（如 `step_3`、`level_2_score`）走同样规则

**关联 DEBUG**：`DEBUG/trend7d-to-camel-2026-07-12.md`。

---

### D29：仪表盘大屏形态（v3.9 双路由共用 + 浏览器真全屏）

**演进时间线**：
- v3.4：三形态（工作台 / 大屏 / 全屏投放），3 个独立路由
- v3.5：收敛为单形态 `/dashboard/dashboard` 真·大屏（顶级路由）
- v3.6：扁平化为顶级路由 `/dashboard`（不嵌 Layout）
- v3.8：反向——嵌 Layout + URL query `?fullscreen=1` 切 CSS 形态
- **v3.9（本变更）**：双路由共用同一 dashboard.vue + 浏览器 Fullscreen API

**v3.8 → v3.9 反向变更原因**（用户实测反馈 v3.8 仍不达预期）：

1. **应用层 CSS 切 ≠ 浏览器真全屏**：v3.8 的 `?fullscreen=1` 只让仪表盘暗色区占 100vh，但 Layout 框架（菜单/顶栏/Tags View）依然显示 = 不是用户期望的"真大屏"
2. **按钮文字与视觉状态反了**：v3.8 默认嵌 Layout 时按钮写"全屏模式"（OK），但**点击后进入 100vh 状态时按钮写"退出全屏"**——用户期望"全屏模式"按钮在点击后**真去全屏（隐藏 Layout）**，而不是只 CSS 撑高

**决策**（v3.9）：

1. **router 双路由共用 dashboard.vue**：
   ```
   // 路由 1：默认嵌 Layout（菜单可见）
   {
     path: '/dashboard',
     component: Layout,
     redirect: '/dashboard/index',
     permissions: ['biz:dashboard:view'],
     meta: { title: '仪表盘', icon: 'dashboard' },
     children: [{
       path: 'index',
       component: () => import('@/views/dashboard/dashboard.vue'),
       name: 'BizDashboard',
       meta: { title: '仪表盘', icon: 'dashboard', activeMenu: '/dashboard' }
     }]
   }

   // 路由 2：真·大屏（顶级，不嵌 Layout，菜单 hidden）
   {
     path: '/dashboard/screen',
     component: () => import('@/views/dashboard/dashboard.vue'),
     name: 'BizDashboardScreen',
     permissions: ['biz:dashboard:view'],
     meta: { title: '仪表盘 · 大屏', hidden: true, activeMenu: '/dashboard' }
   }
   ```

2. **dashboard.vue 形态判定**：`isScreenRoute = computed(() => route.name === 'BizDashboardScreen')`
   - `:class="{ 'is-fullscreen': isScreenRoute }"` 控制 CSS
   - 按钮文字：`{{ isScreenRoute ? '退出全屏' : '全屏模式' }}`

3. **`toggleFullscreen()` 联动路由 + Fullscreen API**：
   - 默认态（isScreenRoute=false）→ `router.push('/dashboard/screen')`（50ms 后等路由切换完）→ `document.documentElement.requestFullscreen()`
   - 大屏态（isScreenRoute=true）→ `exitFullscreen()` + `router.push('/dashboard')`

4. **fullscreenchange 事件双向同步**：浏览器 Esc / 系统切走全屏时，`isScreenRoute=true` 且 `document.fullscreenElement` 为 null → 自动 `router.push('/dashboard')` 回默认

5. **onMounted 直链场景兜底**：刷新 / 直链 `/dashboard/screen` 时，如果浏览器不在全屏状态，**自动补一次 `requestFullscreen`**（80ms 延迟）

6. **CSS 双形态**（与 v3.8 同）：
   - `.ds`（默认嵌 Layout）：去掉 `min-height: 100vh`，负 margin `calc(50% - 50vw)` 拉满左右
   - `.ds.is-fullscreen`（真大屏）：`min-height: 100vh` + `margin: 0` 占满整页

**Rationale**：

- 形态判定用 `route.name` 比 URL query 更直接：刷新 / 直链 / 后退都能精准还原形态
- 双路由共用同一文件，避免代码重复（CSS class 由 isScreenRoute 切换）
- Fullscreen API + 路由切换双联动：浏览器全屏状态 / 应用路由状态 / CSS 形态三者一致
- fullscreenchange 监听保证浏览器原生退出（Esc）能自动回默认路由，按钮文字不会卡在"退出全屏"

**v3.10 CSS 修正**（Chrome 横向滚动 / sidebar 遮挡）：

- **回归问题**：v3.8/v3.9 `.ds` 用 `margin: 0 calc(50% - 50vw)` 强行让暗色背景延伸到 100vw。Chrome 严格按 CSS spec 出现 body 横向滚动条 + 暗色背景左边被 sidebar 盖住；Safari 对 `100vw` 溢出行为不一致，暂时掩盖问题。
- **修复**：v3.10 `.ds` 改成 `width: 100%; margin: 0; padding: 14px 20px` —— 暗色背景只到 Layout 主区边界，跟其他业务页行为一致，不被 sidebar 遮挡，没有横向溢出。
- **代价**：嵌入 Layout 形态下暗色背景不再贯穿屏幕边缘；想要"暗色背景贯穿全屏"必须切到真·大屏形态 `/dashboard/screen`（top level + `.ds.is-fullscreen` CSS `min-height: 100vh + margin: 0`）。

**架构图**（v3.9）：

```
侧边栏菜单「仪表盘」 → /dashboard → redirect /dashboard/index
   ↓                              (默认嵌 Layout，仪表盘完整显示)
   Layout (navbar / Tags View / sidebar)
   ↓
   /dashboard/index → dashboard.vue
                          ├─ isScreenRoute = false
                          ├─ .ds class（嵌 Layout，负 margin 拉满）
                          └─ 按钮「全屏模式」

点击「全屏模式」 → router.push('/dashboard/screen')
                       + requestFullscreen()
                       ↓
                /dashboard/screen → dashboard.vue (顶级，不嵌 Layout)
                          ├─ isScreenRoute = true
                          ├─ .ds.is-fullscreen class（100vh + margin: 0）
                          ├─ 浏览器真全屏（隐藏 chrome）
                          └─ 按钮「退出全屏」

按 Esc 或点「退出全屏」 → exitFullscreen() + router.push('/dashboard')
                       → 回到默认嵌 Layout 形态
```

**后端 province 数据链**（不变）：

```
biz_customer.province (RED 增列)
   ↓ 派生
biz_contract.province (RED 增列，由 dashboard_v3_3_init.sql 的 UPDATE 一次性回填)
   ↓ 过滤
```

### D30：DAO filter 参数显式签名（避坑 `**kwargs`）

**问题**：v3.4 路线 C 落地时，service 层 `dashboard_service.py` 用 `asyncio.gather(*DAO_calls)` 把 10 个 DAO 统一并发调用：

```python
(
    kpi_contract, ..., trend_7d, ...
) = await asyncio.gather(
    DashboardDAO.kpi_contract(db, province),
    ...,
    DashboardDAO.trend_7d(db, province),  # ← trend_7d 漏接 province
    ...
)
```

`DashboardDAO.trend_7d(db)` 原签名只收 `db`，service 强行传第二个位置参数 → TypeError `takes 1 positional argument but 2 were given` → 500 抛出。

**根因**：v3.4 给 4 个 DAO（kpi_contract / status_distribution / top_customers / channel_locations）加了 `province` 过滤，唯独 `trend_7d` 漏；原因是 v3.4 静态层冒烟用 `pytest -k dashboard` mock 调 DAO，没走真实 service.overview_services(...)，漏掉了并发调用契约。

**决策**：凡是 service 用 `asyncio.gather(*DAO_calls)` 并发调用，DAO 签名必须**显式接收 filter 参数**（如 `province: str = ''`），**禁止用 `**kwargs` 兜底**。

**Rationale**：

- **静态可校验**：`inspect.signature(DashboardDAO.trend_7d).parameters` 一眼看出支持哪些维度过滤；CI 可加 `pytest` 断言「所有 DAO 在 gather 调用里传的参数都在签名里」
- **漏接即崩**：DAO 漏接参数 → TypeError 立即在 gather 抛出，定位 0 成本；用 `**kwargs` 兜底 → 静默忽略，过滤失效、用户看不到数据但页面不崩（最差形态）
- **条件过滤清晰**：`if province: q.append(...)` 比 `if 'province' in kwargs and kwargs['province']:` 短 70%，IDE 跳定义也准
- **配合 D24（API camelCase）**：filter 维度命名（如 `province`）前端 service 一处定义、后端 DAO 多处透传，命名一致性 + 显式签名 = 双保险

**修复**：

```python
# module_biz/dao/dashboard_dao.py（v3.5）
@staticmethod
async def trend_7d(db: AsyncSession, province: str = '') -> list[Trend7dItemModel]:
    today = date.today()
    start = today - timedelta(days=6)
    start_dt = datetime.combine(start, datetime.min.time())

    new_q = [BizContract.create_time >= start_dt]
    if province:
        new_q.append(BizContract.province == province)
    new_stmt = (
        select(func.date(BizContract.create_time).label('d'), func.count(BizContract.id))
        .where(*new_q)
        .group_by(func.date(BizContract.create_time))
    )

    approved_q = [BizContract.status == 'approved', BizContract.update_time >= start_dt]
    if province:
        approved_q.append(BizContract.province == province)
    approved_stmt = (
        select(func.date(BizContract.update_time).label('d'), func.count(BizContract.id))
        .where(*approved_q)
        .group_by(func.date(BizContract.update_time))
    )
    ...
```

防御：参数 `province=''` 默认空串，老调用方零成本兼容，新调用方显式声明可读。

**静态校验示例**：

```python
import inspect
from module_biz.dao.dashboard_dao import DashboardDAO
for m in ['kpi_contract', 'trend_7d', 'status_distribution', 'top_customers']:
    sig = inspect.signature(getattr(DashboardDAO, m))
    assert 'province' in sig.parameters, f'{m} 漏接 province，违反 D30'
```

**影响范围**：

- 本项目唯一受影响：`DashboardDAO.trend_7d` 一处
- 项目所有 DAO 已扫一遍（kpi_* / *_distribution / *_locations / *_pending），除 `trend_7d` 外全部已正确支持 `province`，无其它漏接
- 未来新增 DAO filter 维度（如 `period`、`category`）按 D30 显式签名

**关联 DEBUG**：`DEBUG/dashboard-runtime-race-2026-07-12.md`。

---

*文档结束*
