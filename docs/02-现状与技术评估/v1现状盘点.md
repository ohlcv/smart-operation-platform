# v1 Demo 目录结构清单

**文档版本**：V1.1  
**编写日期**：2026-07-10  
**对应目录**：`1/`  
**说明**：本清单基于 `1/` 现有代码实际实现整理，排除依赖文件、日志文件、缓存文件、构建产物及系统文件；目录结构与文件说明尽量贴合当前实现现状。

---

## 一、整体目录结构

```
1/
├── .claude/
│   └── settings.local.json
├── README.md
├── init.sql
├── start.bat
├── stop.bat
├── backend/
│   ├── .env
│   ├── .gitignore
│   ├── README.md
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── auth.py
│   │   │           ├── channel.py
│   │   │           ├── contract.py
│   │   │           ├── customer.py
│   │   │           ├── health.py
│   │   │           ├── invoice.py
│   │   │           ├── operation.py
│   │   │           └── user.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── enums.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── init_db.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── approval.py
│   │   │   ├── channel.py
│   │   │   ├── contract.py
│   │   │   ├── customer.py
│   │   │   ├── invoice.py
│   │   │   ├── operation.py
│   │   │   └── user.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── approval.py
│   │       ├── auth.py
│   │       ├── channel.py
│   │       ├── common.py
│   │       ├── contract.py
│   │       ├── customer.py
│   │       ├── invoice.py
│   │       ├── operation.py
│   │       └── user.py
│   └── migrations/
│       ├── 20260701_phase1_2_upgrade.sql
│       └── 20260701_phase3.sql
├── deploy/
│   ├── nginx.conf
│   └── sd-scm-backend.service
└── frontend/
    ├── .gitignore
    ├── README.md
    ├── index.html
    ├── package.json
    ├── .env.development
    ├── .env.production
    ├── vite.config.js
    └── src/
        ├── App.vue
        ├── main.js
        ├── permission.js
        ├── api/
        │   ├── auth.js
        │   ├── channel.js
        │   ├── contract.js
        │   ├── customer.js
        │   ├── invoice.js
        │   ├── operation.js
        │   ├── request.js
        │   ├── system.js
        │   └── user.js
        ├── components/
        │   ├── AiBrainPanel.vue
        │   ├── BaseChart.vue
        │   ├── ChinaMapChart.vue
        │   ├── ContractDetailDrawer.vue
        │   └── screen/
        │       ├── CountTo.vue
        │       ├── DataScreen.vue
        │       └── ScreenMap.vue
        ├── constants/
        │   └── business.js
        ├── layout/
        │   └── index.vue
        ├── router/
        │   └── index.js
        ├── store/
        │   └── user.js
        ├── styles/
        │   └── index.scss
        ├── utils/
        │   └── rmb.js
        └── views/
            ├── approval/
            │   └── index.vue
            ├── channel/
            │   └── index.vue
            ├── contract/
            │   └── index.vue
            ├── customer/
            │   └── index.vue
            ├── dashboard/
            │   └── index.vue
            ├── error/
            │   └── 404.vue
            ├── invoice/
            │   └── index.vue
            ├── login/
            │   └── index.vue
            ├── operation/
            │   └── index.vue
            ├── profile/
            │   └── index.vue
            ├── screen/
            │   └── index.vue
            └── system/
                └── users.vue
```

---

## 二、根目录与通用配置

| 路径 | 类型 | 说明 |
|------|------|------|
| `.claude/settings.local.json` | 配置 | Claude/Cursor 本地设置，非业务代码 |
| `README.md` | 文档 | 项目总览、本地运行指南、生产部署说明 |
| `init.sql` | 数据库 | MySQL 初始化脚本：建库、建表、种子账号、演示数据 |
| `start.bat` | 脚本 | Windows 一键启动前后端 |
| `stop.bat` | 脚本 | Windows 一键停止前后端 |

> 说明：当前 `1/` 是可直接运行的 v1 Demo，包含后端 FastAPI、前端 Vue 3 和数据库初始化脚本。

---

## 三、后端（Backend）

### 3.1 项目级文件

| 路径 | 类型 | 说明 |
|------|------|------|
| `backend/.env` | 配置 | 数据库连接、JWT 密钥、DEBUG、CORS |
| `backend/.gitignore` | 配置 | 忽略规则 |
| `backend/README.md` | 文档 | 后端说明、角色权限、主要接口 |
| `backend/requirements.txt` | 依赖 | Python 依赖清单，不含锁文件 |
| `backend/migrations/` | 数据库 | 阶段 SQL 升级脚本 |

### 3.2 应用入口与核心配置

| 路径 | 说明 |
|------|------|
| `backend/app/__init__.py` | 应用包初始化 |
| `backend/app/main.py` | FastAPI 入口，挂载 `/api/v1` 路由，支持 CORS 和 Swagger `/docs` |

### 3.3 核心模块（core）

| 路径 | 说明 |
|------|------|
| `backend/app/core/__init__.py` | 核心包初始化 |
| `backend/app/core/config.py` | 全局配置：项目名、数据库地址、JWT、CORS |
| `backend/app/core/enums.py` | 业务枚举：7 级角色、审批链、合同/发票状态、渠道类别 |
| `backend/app/core/security.py` | 密码哈希 bcrypt、JWT 生成/校验 |

> 当前实现：7 级审批角色为固定顺序链，尚未支持动态流程配置。

### 3.4 数据库层（db）

| 路径 | 说明 |
|------|------|
| `backend/app/db/__init__.py` | 数据库包初始化 |
| `backend/app/db/base.py` | SQLAlchemy 声明式基类，统一 `created_at` / `updated_at` |
| `backend/app/db/init_db.py` | 初始化数据库：建表 + 写入种子用户、经营数据、客户、渠道、发票 |
| `backend/app/db/session.py` | 引擎与会话管理，依赖注入 `get_db` |

### 3.5 数据模型（models）

| 路径 | 表名 | 说明 |
|------|------|------|
| `backend/app/models/__init__.py` | — | 模型包初始化 |
| `backend/app/models/user.py` | `sys_user` | 用户、组织架构、电子签名资产 |
| `backend/app/models/contract.py` | `biz_contract` | 合同全生命周期 + 审批状态 |
| `backend/app/models/approval.py` | `biz_approval` | 审批记录、审计日志、电子签章快照 |
| `backend/app/models/customer.py` | `biz_customer` | 客户档案主数据 |
| `backend/app/models/channel.py` | `biz_channel` / `biz_channel_data` | 渠道平台卡片与回传表格数据 |
| `backend/app/models/invoice.py` | `biz_invoice` | 发票信息与开票状态 |
| `backend/app/models/operation.py` | `biz_operation_data` | 经营指标，按年月+业务条线存储 |

> 当前实现：渠道密码为演示明文存储；客户附件为 JSON 模拟，未接入对象存储。

### 3.6 数据校验（schemas）

| 路径 | 说明 |
|------|------|
| `backend/app/schemas/__init__.py` | Schema 包初始化 |
| `backend/app/schemas/common.py` | 统一响应结构 `Response[T]` |
| `backend/app/schemas/auth.py` | 登录 Token 结构 |
| `backend/app/schemas/user.py` | 用户输出、签名更新、组织列表精简结构 |
| `backend/app/schemas/contract.py` | 合同创建/更新/输出，含状态标签、当前审批角色 |
| `backend/app/schemas/approval.py` | 审批通过/驳回请求、审批记录输出 |
| `backend/app/schemas/customer.py` | 客户档案创建/更新/输出 |
| `backend/app/schemas/channel.py` | 渠道平台与回传数据结构 |
| `backend/app/schemas/invoice.py` | 发票创建/更新/输出、开票统计结构 |
| `backend/app/schemas/operation.py` | 经营数据输出、看板聚合结构 |

### 3.7 API 层（api）

#### 3.7.1 依赖与路由

| 路径 | 说明 |
|------|------|
| `backend/app/api/__init__.py` | API 包初始化 |
| `backend/app/api/deps.py` | 认证依赖 `get_current_user`，角色依赖 `require_roles` |
| `backend/app/api/v1/__init__.py` | v1 API 初始化 |
| `backend/app/api/v1/router.py` | v1 路由汇总 |
| `backend/app/api/v1/endpoints/__init__.py` | 端点包初始化 |

#### 3.7.2 业务端点

| 路径 | 路由前缀 | 说明 | 当前实现状态 |
|------|----------|------|--------------|
| `backend/app/api/v1/endpoints/health.py` | `/health` | 健康检查 | ✅ 已实现 |
| `backend/app/api/v1/endpoints/auth.py` | `/auth` | 登录、当前用户 | ✅ 已实现 |
| `backend/app/api/v1/endpoints/user.py` | `/users` | 当前用户资料、更新本人签名、人员列表 | ⚠️ 仅列表与签名维护，无完整用户 CRUD |
| `backend/app/api/v1/endpoints/contract.py` | `/contracts` | 合同 CRUD、提交审批、逐级通过、驳回、审批记录 | ✅ 已实现 7 级审批流 |
| `backend/app/api/v1/endpoints/operation.py` | `/operation` | 经营数据看板、明细列表、录入、AI 诊断 | ✅ 已实现规则化 AI 诊断 |
| `backend/app/api/v1/endpoints/customer.py` | `/customers` | 客户档案 CRUD | ✅ 已实现 |
| `backend/app/api/v1/endpoints/channel.py` | `/channels` | 渠道 CRUD、回传数据读取/导入 | ✅ 已实现基础渠道台账 |
| `backend/app/api/v1/endpoints/invoice.py` | `/invoices` | 发票 CRUD、开票统计 | ✅ 已实现基础发票台账 |

> 当前实现说明：
> - 合同审批为固定 7 级链，不支持自定义流程、加签、转办、会签。
> - 经营数据与合同数据相互独立，经营看板不自动汇总合同金额。
> - 发票目前是台账级管理，未接入税务系统或真实开票流程。

### 3.8 数据库迁移（migrations）

| 路径 | 说明 |
|------|------|
| `backend/migrations/20260701_phase1_2_upgrade.sql` | 第一阶段/第二阶段升级脚本 |
| `backend/migrations/20260701_phase3.sql` | 第三阶段升级脚本 |

---

## 四、部署配置（deploy）

| 路径 | 说明 |
|------|------|
| `deploy/nginx.conf` | Nginx 配置：静态资源 + `/api` 反向代理到后端 |
| `deploy/sd-scm-backend.service` | Systemd 服务：后端守护进程配置 |

> 当前实现：生产环境为 Nginx + Uvicorn + MySQL 单体部署，无容器化编排文件位于 `1/` 内。

---

## 五、前端（Frontend）

### 5.1 项目级文件

| 路径 | 说明 |
|------|------|
| `frontend/.gitignore` | 忽略规则 |
| `frontend/README.md` | 前端说明、权限与路由拦截 |
| `frontend/index.html` | HTML 入口 |
| `frontend/package.json` | 依赖清单，无 lock 文件 |
| `frontend/.env.development` | 开发环境 API 地址 |
| `frontend/.env.production` | 生产环境 API 地址 |
| `frontend/vite.config.js` | Vite 配置：路径别名 `/api` 代理、Element Plus 按需自动导入 |

### 5.2 应用入口

| 路径 | 说明 |
|------|------|
| `frontend/src/App.vue` | 根组件，仅渲染 `<router-view />` |
| `frontend/src/main.js` | 创建 Vue 应用，注册 Element Plus、路由、Pinia、暗色主题 |
| `frontend/src/permission.js` | 全局路由守卫：登录态校验、角色拦截、401 跳转 |

### 5.3 请求层（api）

| 路径 | 说明 |
|------|------|
| `frontend/src/api/request.js` | axios 实例：统一附加 token、统一处理后端 `{code,message,data}` |
| `frontend/src/api/auth.js` | 登录、获取当前用户 |
| `frontend/src/api/contract.js` | 合同列表/详情/CRUD、提交/审批/驳回、审批记录 |
| `frontend/src/api/operation.js` | 看板聚合、经营数据明细、AI 诊断 |
| `frontend/src/api/customer.js` | 客户档案 CRUD |
| `frontend/src/api/channel.js` | 渠道列表、回传数据读取、导入覆盖 |
| `frontend/src/api/invoice.js` | 发票列表/统计/CRUD |
| `frontend/src/api/system.js` | 健康检查 |
| `frontend/src/api/user.js` | 当前用户资料、更新签名、人员列表 |

### 5.4 常量与工具

| 路径 | 说明 |
|------|------|
| `frontend/src/constants/business.js` | 7 级角色、审批链、合同类型/状态、发票状态、渠道类别 |
| `frontend/src/utils/rmb.js` | 人民币金额转中文大写，用于审批单打印 |

### 5.5 布局与路由

| 路径 | 说明 |
|------|------|
| `frontend/src/layout/index.vue` | 主框架：侧边栏动态菜单、顶栏用户信息、下拉退出/个人设置 |
| `frontend/src/router/index.js` | 路由配置：登录、大屏、首页、经营数据、合同、审批、客户、渠道、发票、组织架构、个人中心、404 |

### 5.6 状态管理

| 路径 | 说明 |
|------|------|
| `frontend/src/store/user.js` | Pinia：token、role、userInfo、登录/登出、角色判断 |

### 5.7 样式

| 路径 | 说明 |
|------|------|
| `frontend/src/styles/index.scss` | 全站暗色科技风主题：覆盖 Element Plus 变量、卡片/表格/按钮/滚动条样式 |

### 5.8 公共组件（components）

| 路径 | 说明 |
|------|------|
| `frontend/src/components/AiBrainPanel.vue` | AI 智能脑图面板 |
| `frontend/src/components/BaseChart.vue` | ECharts 通用封装 |
| `frontend/src/components/ChinaMapChart.vue` | 中国地图图表 |
| `frontend/src/components/ContractDetailDrawer.vue` | 合同详情抽屉 |
| `frontend/src/components/screen/CountTo.vue` | 数字滚动组件 |
| `frontend/src/components/screen/DataScreen.vue` | 数据大屏组件 |
| `frontend/src/components/screen/ScreenMap.vue` | 大屏地图组件 |

### 5.9 页面视图（views）

| 路径 | 说明 |
|------|------|
| `frontend/src/views/login/index.vue` | 登录页 |
| `frontend/src/views/dashboard/index.vue` | 首页数据看板 |
| `frontend/src/views/operation/index.vue` | 经营数据可视化 |
| `frontend/src/views/contract/index.vue` | 合同管理：列表、新增、编辑、删除、提交、审批、驳回 |
| `frontend/src/views/approval/index.vue` | 审批中心：待我审批列表 |
| `frontend/src/views/customer/index.vue` | 客户档案管理 |
| `frontend/src/views/channel/index.vue` | 渠道集成：平台卡片与回传数据编辑 |
| `frontend/src/views/invoice/index.vue` | 发票管理：台账与统计 |
| `frontend/src/views/system/users.vue` | 组织架构/人员列表：查看与签名状态 |
| `frontend/src/views/profile/index.vue` | 个人中心：上传/更新本人签名 |
| `frontend/src/views/screen/index.vue` | 数据投放大屏 |
| `frontend/src/views/error/404.vue` | 404 页面 |

> 当前实现说明：
> - 前端已实现角色级菜单过滤和页面访问拦截。
> - 合同、审批、渠道、客户、发票均有完整前端交互页面。
> - 用户管理页面仅做人员列表与签名状态查看，未做账号新增/编辑/禁用等完整管理。

---

## 六、技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 ORM | SQLAlchemy 2.0 |
| 数据库 | MySQL 8.0 |
| 前端框架 | Vue 3 |
| UI 组件库 | Element Plus |
| 构建工具 | Vite |
| 状态管理 | Pinia |
| 图表库 | ECharts |
| 部署 | Nginx + Systemd + Uvicorn |

---

## 六、数据模型

> 以下模型均来自 `1/backend/app/models` 与 `1/backend/app/schemas`，是当前 v1 的全部数据契约。
> 表名以 `biz_` 开头为业务表，以 `sys_` 开头为系统表。

### 6.1 用户与组织

**表名**：`sys_user`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `username` | str(64) | 登录账号，唯一 |
| `full_name` | str(64) | 姓名 |
| `hashed_password` | str(128) | 密码哈希 |
| `role` | enum | 7 级角色 |
| `department` | str(64) | 所属部门 |
| `signature` | text | 电子签名（data-URI 或路径） |
| `is_active` | bool | 是否启用 |
| `is_superuser` | bool | 是否超级管理员 |

**关联 Schema**：
- `UserCreate`：创建用户，含明文密码
- `UserOut` / `UserBrief`：输出模型，含 `role_label`、`has_signature`
- `SignatureUpdate`：更新签名

### 6.2 客户档案

**表名**：`biz_customer`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `customer_code` | str(64) | 客户 ID/编码，唯一 |
| `name` | str(200) | 客户名称 |
| `address` | str(255) | 地址 |
| `contact` | str(64) | 联系人 |
| `phone` | str(32) | 电话 |
| `admission_files` | JSON | 准入资料附件 `[{name, url}]` |
| `remark` | text | 备注 |

**关联 Schema**：
- `FileRef`：附件引用 `{name, url}`
- `CustomerCreate` / `CustomerUpdate` / `CustomerOut`

### 6.3 渠道平台

**表名**：`biz_channel`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `name` | str(100) | 平台名称 |
| `category` | str(16) | 类别：`ticket`/`hotel`/`ota`/`other` |
| `url` | str(255) | 平台地址 |
| `account` | str(128) | 登录账号（Mock） |
| `password` | str(128) | 登录密码（Mock，演示明文） |
| `logo` | str(16) | 图标 emoji |
| `description` | text | 平台说明 |
| `sort_order` | int | 排序 |

**关联表**：`biz_channel_data`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `channel_id` | int | 关联渠道，唯一 |
| `columns` | JSON | 表头列 `[]` |
| `rows` | JSON | 数据行 `[[...]]` |

**关联 Schema**：
- `ChannelCreate` / `ChannelUpdate` / `ChannelOut`
- `ChannelDataIn` / `ChannelDataOut`

### 6.4 合同

**表名**：`biz_contract`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `contract_no` | str(64) | 合同编号，唯一 |
| `title` | str(200) | 合同名称 |
| `party_a` | str(200) | 甲方 |
| `party_b` | str(200) | 乙方 |
| `amount` | numeric(18,2) | 合同金额 |
| `sign_date` | date | 签订日期 |
| `remark` | text | 备注 |
| `contract_type` | enum | 单据类型：`payment`/`business` |
| `department` | str(64) | 申请部门 |
| `customer_name` | str(200) | 客户名称 |
| `business_type` | str(64) | 业务类型 |
| `status` | enum | 状态：`draft`/`pending`/`approved`/`rejected` |
| `current_step` | int | 当前待审批步序（0-6） |
| `created_by` | int | 创建人（业务经办） |

**关联 Schema**：
- `ContractCreate`：创建合同，必填 `contract_no`、`title`
- `ContractUpdate`：更新合同，仅草稿/驳回态可改
- `ContractOut`：输出模型，含 `status_label`、`contract_type_label`、`current_role_label`

### 6.5 审批记录

**表名**：`biz_approval`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `contract_id` | int | 关联合同 |
| `approver_id` | int | 审批人 |
| `step` | int | 审批步序（0-6） |
| `approver_role` | str(32) | 审批人当时的角色值 |
| `action` | enum | 动作：`approve`/`reject` |
| `comment` | text | 审批意见/驳回原因 |
| `signature_snapshot` | text | 电子签名快照 |

**关联 Schema**：
- `ApproveRequest`：通过请求，`comment` 可选
- `RejectRequest`：驳回请求，`comment` 必填
- `ApprovalOut`：输出模型，含 `role_label`

### 6.6 发票

**表名**：`biz_invoice`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `invoice_title` | str(200) | 发票抬头 |
| `tax_no` | str(64) | 纳税人识别号 |
| `invoice_type` | str(32) | 发票类型，默认增值税专用发票 |
| `amount` | numeric(18,2) | 开票金额 |
| `status` | enum | 状态：`pending`/`issued`/`void` |
| `customer_name` | str(200) | 客户名称 |
| `contract_no` | str(64) | 关联合同编号 |
| `issued_date` | date | 开票日期 |
| `remark` | text | 备注 |

**关联 Schema**：
- `InvoiceCreate` / `InvoiceUpdate` / `InvoiceOut`
- `InvoiceStats`：统计模型 `{total, pending, issued, void, issued_amount, pending_amount}`

### 6.7 经营数据

**表名**：`biz_operation_data`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `year` | int | 年份 |
| `month` | int | 月份 1-12 |
| `business_line` | str(64) | 业务条线，如图书发行/数字出版/物流仓储 |
| `revenue` | numeric(18,2) | 营收 |
| `cost` | numeric(18,2) | 成本 |
| `profit` | numeric(18,2) | 利润 |
| `order_count` | int | 订单数 |

**唯一约束**：`(year, month, business_line)`

**关联 Schema**：
- `OperationDataCreate` / `OperationDataOut`
- `DashboardData`：看板聚合 `{kpi, trend, line_share}`
- `KpiSummary`：`{total_revenue, total_cost, total_profit, total_orders}`
- `TrendPoint`：`{month, revenue, profit}`
- `LineShare`：`{business_line, revenue}`

### 6.8 核心枚举

**文件**：`app/core/enums.py`

| 枚举 | 值 | 说明 |
|------|------|------|
| `Role` | `business_handler` / `business_reviewer` / `risk_auditor` / `finance_handler` / `finance_reviewer` / `scm_director` / `invest_director` | 7 级角色 |
| `ContractStatus` | `draft` / `pending` / `approved` / `rejected` | 合同状态 |
| `ContractType` | `payment` / `business` | 单据类型 |
| `ApprovalAction` | `approve` / `reject` | 审批动作 |
| `InvoiceStatus` | `pending` / `issued` / `void` | 发票状态 |

**核心常量**：
- `APPROVAL_CHAIN`：7 级审批链顺序列表
- `ROLE_LABELS`：角色中文映射
- `CONTRACT_STATUS_LABELS` / `CONTRACT_TYPE_LABELS` / `INVOICE_STATUS_LABELS`：枚举标签映射
- `CHANNEL_CATEGORY_LABELS`：渠道类别中文映射
- `FINANCE_ROLES` / `DIRECTOR_ROLES`：常用角色分组

### 6.9 通用响应模型

**文件**：`app/schemas/common.py`

| 模型 | 说明 |
|------|------|
| `Response[T]` | 统一响应结构 `{code, message, data}` |
| `Response.ok(data)` | 成功响应 |
| `Response.fail(message)` | 失败响应 |

---

## 七、当前实现限制与备注

| 维度 | 现状 |
|------|------|
| 审批流程 | 固定 7 级链，无自定义流程、加签、转办、会签 |
| 渠道对接 | 仅基础台账与回传表格 JSON，未接入真实 OTA/抖音 API |
| 财务管理 | 仅发票台账，无银行对账、真实开票/税务对接 |
| 经营数据 | 与合同数据独立，看板不自动汇总合同金额 |
| 用户管理 | 前端仅列表，后端无完整账号 CRUD |
| AI 能力 | 后端为规则诊断与建议，未接入大模型 |
| 小程序端 | 无 |
| 数据安全 | 渠道账号密码演示明文，生产需加密/密钥托管 |
| 部署方式 | 单体应用，无 Kubernetes/容器编排文件位于 `1/` 内 |

---

## 八、业务域与核心流程

### 8.1 业务模块总览

当前 v1 Demo 覆盖 6 大业务域，各域实现深度不同：

| 业务域 | 核心对象 | 实现深度 | 说明 |
|--------|----------|----------|------|
| 合同与审批 | 合同、审批记录 | 闭环 | 从创建到 7 级审批流、驳回、打印审批单 |
| 客户管理 | 客户档案 | 台账级 | 基础 CRUD + 准入资料模拟 |
| 渠道集成 | 渠道平台、回传数据 | 台账级 | 平台卡片 + 表格数据导入/编辑 |
| 发票管理 | 发票台账 | 台账级 | CRUD + 开票统计，未对接税务系统 |
| 经营数据 | 经营指标 | 录入级 | 按月/条线手工录入，前端可视化看板 |
| 组织与权限 | 用户、角色 | 基础级 | 7 级角色、路由拦截、签名管理 |

> 当前定位：v1 为“可演示的供应链业务平台原型”，重点展示合同审批流与数据可视化，非生产级财务系统。

### 8.2 核心业务流程

#### 8.2.1 合同审批流程（核心流程）

```
业务经办创建草稿
    ↓
提交审批（自动完成第 0 级，附加电子签名）
    ↓
进入 7 级审批链：
  1. 业务复核 → 2. 风控审核 → 3. 财务经办 → 4. 财务复核 → 5. 供管公司负责人 → 6. 投资公司负责人
    ↓
任一级可驳回（原因必填）→ 合同回到草稿状态，由业务经办修改后重新提交
    ↓
末级通过 → 合同状态变为「已通过」，流程结束
```

**关键规则：**
- 仅当前 `current_step` 对应角色的用户可操作，超管可介入
- 通过时自动附加审批人电子签名快照，形成审计时间轴
- 驳回后保留审批记录，合同回到 `rejected` 状态
- 草稿/驳回态可编辑、删除；审批中不可修改

#### 8.2.2 客户管理流程

```
新建客户（客户ID唯一）→ 录入档案/准入资料 → 查看/编辑/删除
```

**关键规则：**
- 客户编码唯一，不可重复
- 准入资料为前端模拟上传，未接入对象存储
- 全角色可查看，无字段级权限差异

#### 8.2.3 渠道集成流程

```
平台卡片配置（账号/密码/类别）→ 回传数据导入（CSV 或示例数据）→ 表格内联编辑 → 保存
```

**关键规则：**
- 账号密码为演示明文存储，仅用于前端复制打开平台
- 回传数据为 JSON 二维表格，导入后进入可修改模式
- 未对接真实 OTA/抖音 API，为模拟数据集成

#### 8.2.4 发票管理流程

```
新建发票（关联合同编号）→ 台账维护 → 确认开票 → 状态变更 → 统计看板更新
```

**关键规则：**
- 发票状态：待开票 → 已开票 / 已作废
- 开票金额不校验合同总额，为独立台账
- 未对接税务系统或银行流水

#### 8.2.5 经营数据流程

```
手工录入（年月 + 业务条线）→ 前端看板聚合 → AI 规则诊断
```

**关键规则：**
- 经营数据与合同数据独立，不自动汇总
- 业务条线示例：图书发行、数字出版、物流仓储
- AI 诊断为规则化分析，非大模型推理

---

## 九、角色与业务权限

### 9.1 角色清单

| 角色值 | 中文名 | 部门 | 业务定位 |
|--------|--------|------|----------|
| `business_handler` | 业务经办 | 业务部 | 合同源头录入与提交 |
| `business_reviewer` | 业务复核 | 业务部 | 第一级审批 |
| `risk_auditor` | 风控审核 | 风控合规部 | 第二级审批 |
| `finance_handler` | 财务经办 | 财务部 | 第三级审批 |
| `finance_reviewer` | 财务复核 | 财务部 | 第四级审批 |
| `scm_director` | 供管公司负责人 | 供管公司 | 第五级审批 |
| `invest_director` | 投资公司负责人 | 投资公司 | 第六级审批（末级） |

### 9.2 页面访问权限

| 页面 | 路由 | 可见角色 | 说明 |
|------|------|----------|------|
| 登录 | `/login` | 全部 | 公开页面 |
| 首页看板 | `/dashboard` | 全部 | 基础数据概览 |
| 经营数据 | `/operation` | 风控、财务、负责人 | 需特定角色进入 |
| 合同管理 | `/contract` | 全部 | 页面内按角色控制操作按钮 |
| 审批中心 | `/approval` | 6 级审批角色 | 仅显示当前待办 |
| 客户档案 | `/customer` | 全部 | 基础台账 |
| 渠道集成 | `/channel` | 全部 | 平台卡片与回传数据 |
| 发票管理 | `/invoice` | 财务、负责人 | 开票台账 |
| 组织架构 | `/org` | 公司负责人 | 人员与签名查看 |
| 数据大屏 | `/screen` | 全部 | 公开演示页面 |
| 个人中心 | `/profile` | 全部 | 通过顶部下拉进入 |

### 9.3 操作权限控制

| 操作 | 允许角色 | 当前实现 |
|------|----------|----------|
| 创建合同 | 业务经办 | 仅业务经办可见「新建合同」按钮 |
| 编辑/删除合同 | 业务经办 | 仅草稿/驳回态可操作，且仅本人创建 |
| 提交审批 | 业务经办 | 仅草稿/驳回态可提交 |
| 审批通过/驳回 | 当前环节角色 | 后端强制校验角色，前端仅显示待办 |
| 开票 | 财务/负责人 | 无额外限制 |
| 用户管理 | 负责人 | 前端仅查看，无编辑权限 |

> 当前实现：权限控制以页面级和按钮级为主，无字段级权限。

---

## 十、核心业务规则

### 10.1 合同业务规则

| 规则项 | 现状 |
|--------|------|
| 合同编号 | 唯一，前端输入后不可修改（编辑态禁用） |
| 合同类型 | 二选一：业务付款审批单 / 业务审批单 |
| 甲方 | 默认固定为「山东出版供应链管理公司」 |
| 金额 | 最小 0，步进 10000 元 |
| 状态流转 | 草稿 → 审批中 → 已通过 / 已驳回 |
| 审批触发 | 业务经办点击「提交审批」后自动进入 7 级链 |
| 驳回处理 | 合同回到 `rejected` 状态，业务经办可修改后重新提交 |
| 打印 | 详情页支持生成并打印审批单，含签章区域 |

### 10.2 审批业务规则

| 规则项 | 现状 |
|--------|------|
| 审批链顺序 | 固定 7 级：业务经办 → 业务复核 → 风控审核 → 财务经办 → 财务复核 → 供管公司负责人 → 投资公司负责人 |
| 审批人确定 | 按 `current_step` 映射角色，后端强制校验 |
| 超管权限 | 超管可绕过角色限制，审批任意合同 |
| 电子签章 | 通过时自动附加当前审批人签名快照 |
| 驳回要求 | 驳回时意见必填 |
| 通过意见 | 通过时意见可选 |
| 审计日志 | 全部审批记录永久保存，时间轴展示 |

### 10.3 客户业务规则

| 规则项 | 现状 |
|--------|------|
| 客户编码 | 唯一标识，编辑时不可修改 |
| 准入资料 | 前端模拟上传，存 JSON 数组 `[{name, url}]` |
| 附件预览 | 暂不支持真实预览/下载，演示用途 |

### 10.4 渠道业务规则

| 规则项 | 现状 |
|--------|------|
| 平台类别 | 景区门票 / 酒店数据 / 综合 OTA / 其他平台 |
| 账号密码 | 演示明文存储，用于前端复制登录 |
| 回传数据 | 支持 CSV 导入或填充示例数据，导入后可内联编辑 |
| 数据存储 | JSON 格式，列 + 行二维结构 |

### 10.5 发票业务规则

| 规则项 | 现状 |
|--------|------|
| 发票状态 | 待开票 → 已开票 / 已作废 |
| 关联合同 | 可填写合同编号，但不强制校验 |
| 开票操作 | 前端点击「确认开票」后状态变为已开票，自动填入当天日期 |
| 统计 | 实时统计总数、待开票、已开票、已开票金额 |

### 10.6 经营数据规则

| 规则项 | 现状 |
|--------|------|
| 数据维度 | 年月 + 业务条线，唯一约束 |
| 业务条线 | 示例：图书发行、数字出版、物流仓储 |
| 指标 | 营收、成本、利润、订单数 |
| 数据来源 | 手工录入，不与合同/发票自动关联 |
| AI 诊断 | 规则化分析，基于利润率、闲置资金、待开票、审批中等指标 |

### 10.7 电子签名规则

| 规则项 | 现状 |
|--------|------|
| 签名形式 | 图片上传（PNG/JPG），建议透明底 |
| 存储方式 | 前端转 data-URI 后存后端 Text 字段 |
| 使用场景 | 审批通过时自动附加到审批单 |
| 生成方式 | 种子数据使用 SVG 生成红色手写体姓名 |

---

## 十一、前端页面与视觉效果

### 11.1 页面清单

| 页面 | 路径 | 主要功能 | 视觉效果 |
|------|------|----------|----------|
| 登录页 | `/login` | 账号密码登录 | 动态网格背景 + 光晕 + 玻璃霓虹卡片 |
| 首页看板 | `/dashboard` | 数据概览入口 | 直接嵌入数据大屏组件 |
| 经营数据 | `/operation` | KPI + 趋势图 + 饼图 + AI 诊断 | 卡片悬停上浮、KPI 点击展开订单抽屉 |
| 合同管理 | `/contract` | 合同 CRUD + 提交审批 | 表格、弹窗表单、详情抽屉、打印审批单 |
| 审批中心 | `/approval` | 待审批列表 + 通过/驳回 | 状态标签、时间轴、电子签章展示 |
| 客户档案 | `/customer` | 客户 CRUD + 详情查看 | 表格、抽屉详情、标签展示附件数量 |
| 渠道集成 | `/channel` | 平台卡片 + 回传数据 | 卡片网格、抽屉表格编辑、CSV 导入 |
| 发票管理 | `/invoice` | 发票 CRUD + 开票统计 | 统计卡、表格、状态标签 |
| 组织架构 | `/org` | 人员列表 + 角色/签名状态 | 表格、信息提示条 |
| 个人中心 | `/profile` | 查看资料 + 上传/更新签名 | 描述列表、签名预览、拖拽上传 |
| 数据大屏 | `/screen` | 全屏数据投映 | 三栏布局、数字滚动、地图飞线、跑马灯、AI 雷达 |

### 11.2 公共组件

| 组件 | 说明 | 视觉效果 |
|------|------|----------|
| `DataScreen` | 数据大屏主组件 | 深色背景 + 玻璃面板 + 渐变标题 + 实时时钟 |
| `AiBrainPanel` | AI 智能分析面板 | 加载旋转、指标卡、风险/建议分栏、打字机效果 |
| `BaseChart` | ECharts 通用封装 | 自适应容器、监听 option 变化重绘 |
| `ChinaMapChart` | 中国地图图表 | 地图 + 下钻条形图降级、省份点击联动 |
| `ContractDetailDrawer` | 合同详情抽屉 | 7 级步骤条、时间轴、签章图片、打印区域 |
| `CountTo` | 数字滚动动画 | easeOutCubic 缓动、千分位格式化 |
| `ScreenMap` | 大屏地图 | 地图 + 物流飞线 + 涟漪节点、省份联动 |

### 11.3 交互与视觉细节

#### 11.3.1 登录页
- **动态背景**：CSS 透视网格 + 径向渐变光晕 + 浮动动画
- **登录卡片**：玻璃拟态效果，半透明背景 + backdrop-filter 模糊 + 霓虹边框
- **品牌区域**：渐变 Logo + 标题文字渐变 + 发光阴影

#### 11.3.2 主框架
- **侧边栏**：深蓝渐变背景 + 渐变 Logo + 菜单悬停高亮 + 激活项左侧光条
- **顶栏**：玻璃质感 + 渐变标题 + 用户信息下拉 + 角色标签
- **主题**：全站暗色科技风，覆盖 Element Plus 变量

#### 11.3.3 经营数据页
- **KPI 卡片**：悬停上浮 + 阴影加深 + 可点击卡片顶部高亮条
- **周期切换**：本月/本季度/本年 + 月份选择器，KPI 和图表联动刷新
- **趋势图**：柱状图（营收）+ 折线图（利润），Y 轴显示「万」
- **饼图**：环形图展示业务条线营收占比，底部图例
- **订单抽屉**：右侧滑出，展示最近订单明细 Mock 数据

#### 11.3.4 合同管理页
- **表格**：斑马纹 + 边框 + 溢出省略 + 状态标签 + 当前环节提示
- **操作按钮**：图标按钮 + 文字按钮，草稿/驳回态显示编辑/提交/删除
- **新建/编辑弹窗**：表单校验 + 拖拽上传附件（演示）
- **详情抽屉**：描述列表 + 7 级步骤条 + 审批时间轴 + 签章图片
- **打印**：`@media print` 全局隐藏系统，仅打印审批单，含表格和签章区

#### 11.3.5 审批中心页
- **列表**：仅显示当前待办，显示当前环节角色标签
- **操作**：查看详情 + 通过/驳回按钮
- **通过弹窗**：成功提示 + 自动附加签名说明
- **驳回弹窗**：原因必填校验 + 危险操作确认

#### 11.3.6 渠道集成页
- **卡片网格**：自适应列数 + 悬停阴影
- **平台信息**：Emoji Logo + 类别标签 + 描述
- **账号密码**：等宽字体 + 一键复制按钮
- **回传数据抽屉**：工具栏 + CSV 导入 + 示例数据填充 + 表格内联编辑 + 保存

#### 11.3.7 数据大屏
- **布局**：左 26% + 中 48% + 右 26% 三栏
- **顶部栏**：实时时钟 + 日期 + 系统在线状态 + 全屏切换
- **左侧面板**：核心指标卡（数字滚动动画）+ 营收月度面积图
- **中间面板**：中国地图 + 省份下钻 + 物流飞线动画 + 涟漪节点
- **右侧面板**：审批流跑马灯（悬停暂停）+ AI 雷达图 + 打字机分析文本
- **交互**：点击省份联动两侧数据，Esc 退出全屏

---

## 十二、业务数据现状

### 12.1 种子数据范围

初始化脚本 `backend/app/db/init_db.py` 会写入以下演示数据：

| 数据域 | 数量 | 说明 |
|--------|------|------|
| 用户账号 | 8 个 | admin + 7 级角色各一，密码统一 `123456` |
| 经营数据 | 18 条 | 2026 年 1-6 月 × 3 条业务线，营收递增模拟 |
| 客户档案 | 3 个 | 济南新华书店、青岛出版发行集团、齐鲁印刷 |
| 渠道平台 | 4 个 | 携程商旅、美团到综、去哪儿网、同程旅行 |
| 发票记录 | 3 条 | 对应 3 个客户，状态混合（已开票/待开票） |

### 12.2 演示账号

| 账号 | 姓名 | 角色 | 部门 | 密码 |
|------|------|------|------|------|
| `admin` | 系统管理员 | 投资公司负责人（超管） | 信息中心 | `123456` |
| `op` | 张经办 | 业务经办 | 业务部 | `123456` |
| `review` | 李复核 | 业务复核 | 业务部 | `123456` |
| `risk` | 王风控 | 风控审核 | 风控合规部 | `123456` |
| `fin` | 赵财办 | 财务经办 | 财务部 | `123456` |
| `finr` | 孙财复 | 财务复核 | 财务部 | `123456` |
| `scm` | 周供管 | 供管公司负责人 | 供管公司 | `123456` |
| `inv` | 吴投资 | 投资公司负责人 | 投资公司 | `123456` |

> 所有账号预置电子签名（SVG 生成红色手写体姓名），审批时可自动签章。

### 12.3 数据边界说明

| 维度 | 现状 |
|------|------|
| 合同数据 | 初始化无种子合同，需手动创建演示 |
| 审批记录 | 随合同流转生成，初始化无历史数据 |
| 渠道数据 | 初始化无回传数据，需手动导入或填充示例 |
| 客户附件 | JSON 模拟，URL 为空，仅展示附件名 |
| 渠道密码 | 明文存储，仅演示用途 |
| 经营数据 | 2026 上半年 Mock 数据，下半年需手动录入 |

---

## 十三、业务已知问题与限制

| 维度 | 现状 | 业务影响 |
|------|------|----------|
| 审批流程 | 固定 7 级链 | 不支持自定义流程、加签、转办、会签 |
| 合同管理 | 无合同编号自动生成 | 需手动输入，存在重复风险 |
| 渠道对接 | 仅 Mock 数据 | 无法自动同步 OTA/抖音真实数据 |
| 财务管理 | 台账级管理 | 无银行对账、税务对接、真实开票 |
| 经营数据 | 与合同独立 | 看板无法自动汇总合同金额，需手工录入 |
| 客户管理 | 附件未落地 | 无法真实预览/下载准入资料 |
| 数据安全 | 渠道密码明文 | 生产环境需加密/密钥托管 |
| AI 能力 | 规则化诊断 | 非真实 AI 推理，结论基于预设规则 |
| 移动端 | 无小程序/响应式 | 仅桌面端可用 |
| 权限控制 | 页面/按钮级 | 无字段级、数据范围级细粒度控制 |

---

## 十四、业务术语与口径

| 术语 | 业务含义 |
|------|----------|
| 业务经办 | 合同创建人，负责录入和提交审批 |
| 业务复核 | 业务部二级审批，确认合同内容准确性 |
| 风控审核 | 风控合规部审批，评估合同风险 |
| 财务经办/复核 | 财务部两级审批，审核金额与付款条件 |
| 供管公司负责人 | 供应链管理公司负责人审批 |
| 投资公司负责人 | 最终审批人，审批通过后合同生效 |
| 审批中 | 合同处于 7 级审批链流转中 |
| 已驳回 | 合同被任一级驳回，回到草稿状态 |
| 已通过 | 合同走完 7 级审批，流程结束 |
| 渠道回传数据 | 外部平台导出的业务数据，经 CSV 导入系统 |
| AI 智能大脑 | 规则化业务诊断，非大模型推理 |

---

## 十五、业务验收范围

| 已验收场景 | 未验证/仅代码实现 |
|------------|------------------|
| 合同创建/编辑/删除 | 合同编号自动生成规则 |
| 7 级审批流通过 | 驳回后重新提交的完整路径 |
| 审批时间轴 + 签章 | 多用户并发审批冲突 |
| 客户档案 CRUD | 客户导入/导出 |
| 渠道卡片 + 回传数据 | 真实 API 对接 |
| 发票台账 + 统计 | 税务系统对接 |
| 经营数据录入 + 看板 | 与合同金额自动汇总 |
| 登录态拦截 | 密码强度/过期策略 |
| 数据大屏展示 | 大屏分辨率适配 |

> 建议下次业务评审重点验证：合同审批全流程、渠道数据导入、经营数据与合同数据关联需求。
