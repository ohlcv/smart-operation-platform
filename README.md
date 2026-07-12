# 智能运营平台 / Smart Operation Platform

> 基于 [RuoYi-Vue3-FastAPI](https://github.com/insistence/RuoYi-Vue3-FastAPI) v1.9.0 fork 后深度定制的企业运营管理系统  
> 面向合同 / 客户 / 渠道 / 发票 / 财务 / 经营 / 审批 / 仪表盘一体化业务闭环

[![项目版本](https://img.shields.io/badge/version-v3.12-brightgreen.svg)](docs/04-开发/开发进度台账.md)
[![前端](https://img.shields.io/badge/Vue-3.4-42b883.svg)](ruoyi-fastapi-frontend)
[![Element Plus](https://img.shields.io/badge/Element%20Plus-2.13-409eff.svg)](https://element-plus.org/)
[![后端](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](ruoyi-fastapi-backend)
[![Python](https://img.shields.io/badge/Python-≥3.10-3776ab.svg)](https://www.python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8-4479A1.svg)](https://www.mysql.com)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[English](./README_EN.md) | 中文（本文件）

## 📌 项目简介

「智能运营平台」以 RuoYi-Vue3-FastAPI 为 base，经历 3 代演进：

| 阶段 | 状态 | 关键事件 |
|------|------|---------|
| v1 demo | 已完成 | 上游框架 demo1 接入，跑通登录/菜单/权限骨架 |
| v2 框架深化 | 已完成 | DB Schema 同步、RuoYi 业务模块 vs 自研业务模块解耦 |
| v3 业务闭环 | **当前 (v3.12)** | 8 大业务模块 CRUD + 7 级审批链 + 仪表盘大屏双形态 + AI 大脑 |

**当前业务模块清单（v3.12）**

| 模块 | 路由前缀 | 权限标识 | 关键能力 |
|------|---------|---------|---------|
| 🏠 首页 | `/index` | 无需权限 | 4 KPI + 待我审批表 + 最近合同表 + 8 业务快速导航 + 我的工作台 |
| 📊 仪表盘（含大屏） | `/dashboard` | `biz:dashboard:view` | 9 KPI 卡 + 7 日合同趋势 + 营收月度 YTD + 中国地图 + 状态分布 + Top10 + 审批跑马灯 + AI 风险诊断 + 浏览器真全屏 |
| ✅ 审批中心 | `/biz/approval` | `biz:approval:view` | 待我审批 / 我已审批 / 我提交的 / 5 级审批链 + 电子签名快照 |
| 📄 合同管理 | `/biz/contract` | `biz:contract:view` | 合同 CRUD + 状态机（draft/pending/approved/rejected）+ 合同号唯一性校验 |
| 👥 客户档案 | `/biz/customer` | `biz:customer:view` | 客户主数据 + 来源渠道关联 + 合同数聚合 |
| 🔗 渠道管理 | `/biz/channel` | `biz:channel:view` | 渠道主数据 + 区域分布 |
| 🧾 发票管理 | `/biz/invoice` | `biz:invoice:view` | 发票登记 + 状态跟踪 + 与合同金额联动 |
| 💰 财务管理 | `/biz/finance` | `biz:finance:view` | 收入/支出流水 + 应收应付 |
| 📈 经营数据 | `/biz/operation` | `biz:operation:view` | 月/季/年营收/毛利/订单数手工录入 |

**管理后台（沿用 RuoYi module_admin）**：用户、角色、菜单、部门、岗位、字典、参数、通知公告、操作日志、登录日志、在线用户、定时任务、服务监控、缓存监控、代码生成、AI 模型与对话。

## 🏗️ 技术栈

### 前端（`ruoyi-fastapi-frontend/`）

- **核心**：Vue 3.4 + Vite 5 + Pinia + Vue Router 4
- **UI 库**：**Element Plus 2.13**（v3.11 起全栈统一，移除 Ant Design Vue）
- **可视化**：ECharts 5（仪表盘大屏，含中国省份地图）
- **图标**：`@element-plus/icons-vue`
- **HTTP**：Axios（`src/utils/request.js` 包装 + JWT 拦截 + 错误码统一处理）
- **样式**：SCSS + CSS 变量（`var(--el-*)`）— 暗色模式自动跟随 `html.dark`

### 后端（`ruoyi-fastapi-backend/`）

- **核心**：FastAPI 0.115 + Pydantic 2.x（异步 ORM 全面化）
- **ORM**：SQLAlchemy 2.0 `AsyncSession` + asyncmy（MySQL）/ asyncpg（PG）
- **DB**：MySQL 8 / PostgreSQL 15 二选一
- **缓存 / Session**：Redis 7（JWT 黑名单 + 字典 + 业务缓存）
- **认证**：JWT (PyJWT) + OAuth2 多终端认证，单点登录开关
- **数据库迁移**：Alembic
- **CLI**：Typer（`ruoyi app run --env=dev` 启动）
- **传输层加解密**：RSA + AES 混合（白名单机制）

### 基础设施

- **容器编排**：Docker Compose（`docker-compose.my.yml` MySQL 版 / `docker-compose.pg.yml` PG 版）
- **高性能 ASGI**：uvloop + httptools
- **CI**：预留 GitHub Actions（含 RuoYi Playwright Tests badge）

## 🚀 快速开始

### 一键启动（推荐）

> 前置：Docker Desktop / Colima / OrbStack 已运行

```bash
# 本地前后端 + Docker MySQL/Redis（推荐开发模式）
./start-dev.sh

# 全容器模式（接近生产）
./start-dev.sh --docker

# 停止所有进程
./stop-dev.sh
```

启动脚本自动完成：
1. 启 / 重启 MySQL、Redis、Adminer 容器
2. 跑 SQL 初始化（基础 + 业务 + 菜单权限）
3. 启后端（uvicorn，热重载）
4. 启前端（vite，HMR）

### 启动后访问入口

| 入口 | URL | 说明 |
|------|-----|------|
| 前端 | http://localhost | 通过 vite dev server（默认 80 端口）+ nginx proxy |
| 后端 API | http://localhost:9099 | 直接访问 uvicorn |
| API 文档（Swagger UI） | http://localhost:9099/docs | 在线测试所有接口 |
| ReDoc | http://localhost:9099/redoc | 静态文档 |
| Adminer | http://localhost:8080 | 数据库可视化 |
| RedisInsight（可选） | http://localhost:8001 | Redis 可视化 |

> 后端端口由 `ruoyi-fastapi-backend/.env.dev` 的 `APP_PORT` 控制（默认 9099）。

### 手动分模块启动（高级）

```bash
# 后端
cd ruoyi-fastapi-backend
pip3 install -r requirements.txt
python -m alembic upgrade head  # 或直接用 sql/*.sql 初始化
ruoyi app run --env=dev

# 前端
cd ruoyi-fastapi-frontend
npm install --registry=https://registry.npmmirror.com
npm run dev
```

### Docker Compose（生产 / 演示）

```bash
docker compose -f docker-compose.my.yml up -d --build   # MySQL 版本
docker compose -f docker-compose.pg.yml up -d --build   # PostgreSQL 版本
```

> ⚠️ 默认未做数据卷持久化配置，请自行在 `docker-compose.*.yml` 顶部添加 `volumes` 段。

> 💡 **改代码后再次跑 `./start-dev.sh --docker` 即可**：脚本内部使用 `up -d --build`，Docker 会按构建上下文（源码 + Dockerfile）hash 判断是否需要 rebuild —— 代码没变就秒级复用镜像，变了的镜像才真 rebuild。强制全量重建：`docker compose -f docker-compose.my.yml build --no-cache`。

## 📂 顶层目录

```
smart-operation-platform/
├── ruoyi-fastapi-backend/         FastAPI 后端
│   ├── module_admin/              系统管理（用户/角色/菜单/部门/字典/参数/通知）
│   ├── module_biz/                业务模块（合同/审批/客户/渠道/发票/财务/经营/OTA）
│   ├── module_ai/                 AI 大脑（仪表盘 AI 风险诊断）
│   ├── module_generator/          代码生成器
│   ├── module_task/               APScheduler 定时任务
│   ├── common/                    公共层（异常/中间件/工具/枚举/Pydantic）
│   ├── config/                    配置加载（pydantic-settings）
│   ├── sql/                       数据库脚本 + 业务初始化
│   ├── docs/                      后端补充文档（传输加密/CLI/pytest）
│   └── app.py                     ASGI 入口
├── ruoyi-fastapi-frontend/        Vue 3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── dashboard/         仪表盘（v3.9 双形态：Layout 嵌 + 真全屏）
│   │   │   ├── biz/               8 大业务模块
│   │   │   ├── index/             首页（v3.11 完全重写）
│   │   │   ├── system/ monitor/ tool/  系统管理/监控/工具
│   │   │   └── login.vue register.vue
│   │   ├── api/biz/               业务 API 封装（dumb HTTP layer）
│   │   ├── components/            业务组件（BaseChart / BasePagination / ...）
│   │   ├── layout/                Layout 框架（顶栏/侧栏/Tags View/AppMain）
│   │   ├── router/                路由 + 权限 + 标题栏
│   │   ├── store/                 Pinia store
│   │   ├── utils/                 request/auth/validate
│   │   └── styles/                全局样式 + 暗色变量
│   └── public/
├── ruoyi-fastapi-app/             移动端（v3.4 起低优先级，框架保留）
├── ruoyi-fastapi-test/            E2E 套件（Playwright + pytest，v3 扩展中）
├── docs/                          项目文档
│   ├── 01-需求/                   PRD / SRS
│   ├── 02-现状与技术评估/         v1 → v3 历史快照
│   ├── 03-设计/                   概要设计 / API / 数据库 / UI 规格
│   └── 04-开发/                   ADR / 台账 / 开发计划 / DEBUG
├── scripts/                       调试 / 修复 / 验证脚本
├── mysql-conf/                    MySQL 配置（my.cnf）
├── logs/                          运行日志（运行时生成）
├── docker-compose.my.yml          Docker Compose（MySQL 版）
├── docker-compose.pg.yml          Docker Compose（PG 版）
├── start-dev.sh / stop-dev.sh     启停脚本
└── CHANGELOG.md                   上游 RuoYi 框架历史变更日志（保留）
```

## 🔐 默认账号

| 角色 | 账号 | 密码 | 创建方式 |
|------|------|------|----------|
| 超级管理员 | `admin` | `admin123` | `sql/ruoyi-fastapi.sql` 基础脚本内置 |
| 业务经办 | `biz_h_001` | `biz_h_001@123` | `sql/authorization_init.sql` |
| 业务复核 | `biz_r_001` | `biz_r_001@123` | 同上 |
| 风控审核 | `risk_001` | `risk_001@123` | 同上 |
| 财务经办 | `fin_h_001` | `fin_h_001@123` | 同上 |
| 财务复核 | `fin_r_001` | `fin_r_001@123` | 同上 |
| 供管负责人 | `scm_d_001` | `scm_d_001@123` | 同上 |
| 投资负责人 | `inv_d_001` | `inv_d_001@123` | 同上 |

> ⚠️ 业务初始化脚本在 `sql/` 子目录，详见各 `.sql` 文件头部注释。

## 📐 设计原则（ADR 摘录）

完整 ADR 见 [`docs/04-开发/ARD/ADR-架构决策记录.md`](docs/04-开发/ARD/ADR-架构决策记录.md)。当前已确认 D01~D32，部分摘录：

| ID | 决策 | 落地 |
|----|------|------|
| D03 | 合同状态机 4 态（draft/pending/approved/rejected） | `module_biz/enums.py ContractStatusEnum` |
| D05 | `biz_operation` 不加 province/cost 列（手工录入数据，不污染 ERP） | DAO 退化为 `biz_contract.amount` |
| D24 | 全站 JSON 字段 camelCase（Pydantic `to_camel`） | 全文生效 |
| D25 | 暗色模式自动跟随 `html.dark`，EP 调色板走 `var(--el-*)` | 前端 styles + 全业务页 |
| D27 | 7 级审批链（业务经办→复核→风控→财务→总经理）+ 角色中文 label 映射 | 审批中心 v3 落地 |
| D28 | Pydantic 别名显式声明（`Field(alias='xx', serialization_alias='xx')`）优先于 `alias_generator` | `trend7d` 别名修复（D28 案例） |
| D29 | 仪表盘双形态（`/dashboard` 嵌 Layout + `/dashboard/screen` 真全屏） | dashboard.vue v3.9 落地，v3.10 CSS 修正 |
| D30 | DAO filter 参数显式签名（`province: str = ''`，**禁止 `**kwargs` 兜底**） | `trend_revenue` 联动修复（D30 案例） |
| D31 | Element Plus icon 全栈统一替代 Ant Design Vue | v3.11 首页/业务页全部迁移 |
| D32 | 「数据仪表盘」命名统一（v3.6 起，菜单/路由/标签/cache key） | 已生效 |

## 📚 文档体系

| 类别 | 文档 |
|------|------|
| **架构决策** | [ADR-架构决策记录.md](docs/04-开发/ARD/ADR-架构决策记录.md)（D01~D32） |
| **开发台账** | [开发进度台账.md](docs/04-开发/开发进度台账.md)（v3.0 → v3.12 阶段全记录） |
| **变更记录** | [docs/CHANGELOG.md](docs/CHANGELOG.md)（v3.x 项目自身变更） |
| **API 设计** | [API设计文档.md](docs/03-设计/API设计文档.md) |
| **数据库设计** | [数据库设计.md](docs/03-设计/数据库设计.md) |
| **权限模型** | [权限模型设计.md](docs/03-设计/权限模型设计.md) |
| **UI 规格** | [UI视觉还原规格书.md](docs/03-设计/UI视觉还原规格书.md) |
| **PRD** | [PRD-产品需求文档.md](docs/01-需求/PRD-产品需求文档.md) |
| **SRS** | [SRS-需求规格说明书.md](docs/01-需求/SRS-需求规格说明书.md) |
| **开发计划** | [路线 A 业务闭环优先](docs/04-开发/开发计划/路线A-业务闭环优先.md) / [路线 B 大屏可视化](docs/04-开发/开发计划/路线B-大屏可视化优先.md) / [路线 C 战略驾驶舱](docs/04-开发/开发计划/路线C-战略驾驶舱升级.md) |
| **DEBUG 笔记** | [docs/04-开发/DEBUG/](docs/04-开发/DEBUG) 9 篇实战文档（dashboard race / 暗色硬编码 / SQL init 顺序 / 双重 UTF-8 / Swagger UI 异常 / ...） |

## 🧪 调试工具

### 脚本（`scripts/`）

| 脚本 | 用途 |
|------|------|
| `debug_dashboard.py` | 仪表盘渲染调试（KPI 字段 / trend_7d / AI 诊断） |
| `test_dashboard_v3_3.py` | 仪表盘 v3.3/v3.11 回归（9 KPI 字段 / 省份过滤 / trend_revenue 联动） |
| `test_options_live.py` | 经营数据下拉选项接口冒烟测试 |
| `inspect_options.py` | 下拉选项结构动态探查 |
| `fix_double_utf8.py` | 双重 UTF-8 编码后置修复（生产数据清洗） |
| `repro_422.py` | 422 参数错误现场复现 |

## 🔧 故障排查

| 现象 | 排查方向 |
|------|---------|
| `start-dev.sh` 启动失败 | 看 `logs/error.log`；Docker `docker ps` 看 mysql/redis 状态 |
| 前端 80 端口被占 | `lsof -i :80` 找占用进程；或改 `ruoyi-fastapi-frontend/.env.development` 中端口 |
| 后端 `9099` 端口冲突 | 改 `ruoyi-fastapi-backend/.env.dev` 的 `APP_PORT` |
| 仪表盘 KPI 全 0 | 检查 `biz_operation` 表数据；省份模式看 `biz_contract` |
| 审批流程卡住 | 看 `biz_approval.current_step` 与 `biz_approval_history` |
| 菜单图标随机回退 | 见 DEBUG [sql-dml-menu-icon-persistence](docs/04-开发/DEBUG/sql-dml-menu-icon-persistence-2026-07-12.md) |
| 暗色模式色彩断裂 | 排查硬编码颜色（`hex` / `rgba(...)`）；走 EP 调色板 `var(--el-*)` |

## 🤝 贡献

本项目面向内/外企业级业务系统。贡献前请阅读：
- [ADR](docs/04-开发/ARD/ADR-架构决策记录.md) 了解设计约束
- [开发计划](docs/04-开发/开发计划/00-并行开发路线总览.md) 了解路线 A/B/C 选择
- [DEBUG](docs/04-开发/DEBUG/) 历史案例，避免重复踩坑

提交约定：
- 一个 commit 只做一件事
- commit message 形如 `feat(scope): 主题 (ADR D## / v#.#)`，附 `Co-authored-by: Cursor <cursoragent@cursor.com>`（如适用）
- 改动 → test → commit → push（不直接 push main，请走 PR；小改可直推）

## 📜 License

本项目基于 [MIT License](LICENSE) 开源（继承自上游 RuoYi-Vue3-FastAPI）。

## 🙏 致谢

- 上游框架：[RuoYi-Vue3-FastAPI](https://github.com/insistence/RuoYi-Vue3-FastAPI)（本项目 fork 自 v1.9.0）
- 原作者：[insistence2022](https://gitee.com/insistence2022/)
- 前端基于：[RuoYi-Vue3](https://github.com/yangzongzhuan/RuoYi-Vue3) 修改

---

> 📌 **项目当前状态**：v3.12（8 业务闭环 + 仪表盘大屏双形态 + AI 大脑 + 全栈暗色适配）  
> 上次大决策：**D29 v3.10**（CSS 修正 Chrome 横向滚动 + sidebar 遮挡）  
> 下一次计划：v3.13 — `biz_operation` 加 province/cost 列统一营收/毛利口径；后端 11 KPI 字段全部上卡 + KPI 路由联动
