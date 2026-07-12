# ORM 与 alembic 迁移脱节问题（缺列 1054）

**日期**：2026-07-12
**类型**：开发流程 / alembic 同步机制
**影响**：后端启动失败 `(1054, "Unknown column '...' in 'field list'")`，应用无法启动
**根因**：改了 ORM 模型（`entity/do/*.py`），但 alembic baseline 迁移（`0001_baseline_sys_ruoyi.py`）没同步补列；alembic 是 schema 唯一权威源。

---

## 1. 问题现象

启动后端时报错：

```
sqlalchemy.exc.OperationalError: (asyncmy.errors.OperationalError)
(1054, "Unknown column 'sys_job.job_executor' in 'field list'")

[SQL: SELECT DISTINCT sys_job.job_id, ..., sys_job.job_executor, ...
FROM sys_job WHERE sys_job.status = %s]
[parameters: ('0',)]
Application startup failed. Exiting.
```

或：

```
(1054, "Unknown column 'sys_menu.query' in 'field list'")
```

**共同特征**：
- 报错列在 ORM 模型里**声明了**（`module_xxx/entity/do/*.py`）
- 报错列在 alembic baseline 迁移里**没创建**（`alembic/versions/0001_baseline_sys_ruoyi.py` 或 `0002_baseline_biz.py`）
- 启动时第一个 `SELECT` 表的请求（登录查菜单、定时任务加载等）就崩

---

## 2. 根因：两套「schema 真相」

项目里 schema 同时被两处定义，必须保持一致：

| 真相源 | 文件 | 作用 |
|---|---|---|
| **运行时 ORM 模型** | `module_admin/entity/do/*.py`<br>`module_biz/entity/do/*.py` | 后端运行时查询用的字段映射 |
| **迁移脚本** | `alembic/versions/0001_baseline_sys_ruoyi.py`<br>`alembic/versions/0002_baseline_biz.py` | 数据库表结构由它创建/演进 |

**alembic 是数据库 schema 的唯一权威源**——ORM 只是查询/写入时使用的字段映射。但 ORM 加列和迁移加列是两个**独立**的人工动作，迟早会漏。

v4.0 已删除 `Base.metadata.create_all` 兜底，ORM 与 DB schema 演进**只走 Alembic**。改 ORM 后必须跑 `alembic revision --autogenerate`，否则启动时 `alembic upgrade head` 不会帮你补列，会直接报 1054。

历史上发生过：
- `sys_user.pwd_update_date` / `sys_user.signature` 已补（v2.9 后）
- `sys_role.menu_check_strictly` / `sys_role.dept_check_strictly` 已补
- `sys_job.job_executor` / `job_args` / `job_kwargs` 已补（2026-07-12）
- `sys_job_log.job_executor` / `job_args` / `job_kwargs` / `job_trigger` 已补（2026-07-12）
- `sys_menu.query` / `route_name` 已补（2026-07-12）

---

## 3. 改动正确姿势（写新迁移而非改 baseline）

### ❌ 反模式：直接改 `0001_baseline_sys_ruoyi.py`

- 已有数据库的 alembic 已经记到 `0001` 这个 revision，不会再跑 baseline
- 改动 baseline 只对**全新库**（`docker compose down -v` 后）有效
- baseline 改多了团队协作时容易冲突

### ✅ 正解：写新迁移用 `op.add_column`

```python
# alembic/versions/0005_add_job_executor.py
"""add job_executor / job_args / job_kwargs to sys_job

Revision ID: 0005_add_job_executor
Revises: 0004_seed_biz
Create Date: 2026-07-12 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_add_job_executor'
down_revision = '0004_seed_biz'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sys_job',
        sa.Column('job_executor', sa.String(64), server_default='default', nullable=True, comment='任务执行器'))
    op.add_column('sys_job',
        sa.Column('job_args', sa.String(255), server_default='', nullable=True, comment='位置参数'))
    op.add_column('sys_job',
        sa.Column('job_kwargs', sa.String(255), server_default='', nullable=True, comment='关键字参数'))


def downgrade() -> None:
    op.drop_column('sys_job', 'job_kwargs')
    op.drop_column('sys_job', 'job_args')
    op.drop_column('sys_job', 'job_executor')
```

**优势**：
- 已运行过的库和未运行的库都受同一份迁移管
- 团队 pull 后 `alembic upgrade head` 即可生效
- 回退有 `downgrade()` 兜底

### 最高效：用 autogenerate 自动生成

项目 `alembic.ini` + `alembic/env.py` 已配好 `compare_type=True / compare_server_default=True`，可以直接：

```bash
cd ruoyi-fastapi-backend
alembic -c alembic.ini revision --autogenerate -m "add job_executor to sys_job"
alembic -c alembic.ini upgrade head
```

alembic 会**对比 ORM metadata 和当前数据库 schema**，自动检测出缺的列并生成 `op.add_column`。详见 `alembic/README.md` 第 48-67 行「加新字段的标准流程」。

---

## 4. 为什么「改 alembic 要重建 Docker 镜像」是 docker 模式的正确行为

**这是 docker 模式本身的特性，不是 bug**。看 `ruoyi-fastapi-backend/Dockerfile.my`：

```dockerfile
FROM python:3.10
WORKDIR /app
COPY . .                                              # ← alembic 文件在这里 COPY 进镜像
RUN pip install --no-cache-dir -r requirements.txt ...
CMD ["ruoyi", "app", "run", "--env=dockermy"]
```

容器运行时 alembic 文件是「只读快照」，跟 ORM 一起作为 build 产物打包。所以 docker 模式下：

```
你改了 alembic/versions/0005_xxx.py
   ↓
./start-dev.sh --docker
   ↓
docker compose up -d --build
   ↓  (按构建上下文 hash 判断)
若代码改了 → rebuild backend 镜像（重新 COPY . . → 新 alembic 文件进镜像）
   ↓
容器启动 → server.py:run_alembic_upgrade() 跑 alembic upgrade head
   ↓
数据库 schema 就地更新
```

### docker 模式 vs 本地模式：哪种开发更快？

| 模式 | 改 ORM/alembic 后 | 启动时间 | 适用场景 |
|---|---|---|---|
| **本地模式**（默认） | 保存文件，uvicorn --reload 即时生效 | < 1 秒 | 日常开发、频繁改字段 |
| **Docker 模式**（`--docker`） | 跑 `./start-dev.sh --docker`，自动 rebuild + 重启容器 | 3-15 秒 | 模拟生产、交付前自测、生产部署 |
| **生产**（`docker-compose.server.yml`） | 重新 `docker compose up -d --build` 后 push 镜像 | 几分钟 | 真实生产环境 |

**好消息**：`./start-dev.sh --docker` 已经写好自动 rebuild 逻辑（`start-dev.sh:435-449`）：

```bash
# docker compose build 自带 hash 缓存：
#   - 未改代码 → 复用本地镜像（≈up -d，秒级）
#   - 改了代码 → 自动 rebuild（不需要手动 build --no-cache）
if ! docker compose -f "$DOCKER_COMPOSE_FILE" up -d --build 2>&1 | tee "$up_log"; then
```

所以你**只需要再跑一次 `./start-dev.sh --docker`** 即可，不需要手动 `build --no-cache`、不需要手动 `down`。

### 镜像 rebuild 边界

| 文件改动 | 本地模式 | Docker 模式 |
|---|---|---|
| `alembic/versions/*.py` | 保存即生效（reload） | 需 `./start-dev.sh --docker` 自动 rebuild |
| `module_*/entity/do/*.py` 等业务代码 | 保存即生效（reload） | 需 `./start-dev.sh --docker` 自动 rebuild |
| `requirements.txt` 加新 Python 包 | `pip install -r requirements.txt` | rebuild（pip install 阶段） |
| `Dockerfile.my` 改 FROM/CMD | — | rebuild |
| `docker-compose.my.yml` | — | `docker compose up -d`（不需要 rebuild 镜像） |
| `mysql-conf/charset.cnf` | — | 不需要（volume 挂载，热生效） |

**MySQL 容器本身永远不重建**——它是官方 `mysql:8.0` 镜像，数据存在命名 volume `ruoyi-local-mysql-data` 里。

### 重建 MySQL 数据（清库重跑 alembic + init SQL）

这是另一个动作，**不是 rebuild 镜像**，是清数据让 alembic 重新建表：

```bash
docker compose -f docker-compose.my.yml down -v   # 删 volume（数据没了）
./start-dev.sh --docker                             # 触发 initdb + alembic 重跑
```

适用场景：baseline 改了 + 想从空库重新建表（开发期偶尔做，不在常规流程里）。

### 生产部署建议（你提到生产也用 backend 镜像）

1. **CI 里构建一次镜像推到镜像仓库**（不要在生产服务器现场 build）：
   ```bash
   docker build -f ruoyi-fastapi-backend/Dockerfile.my \
     -t your-registry/ruoyi-backend:$(git rev-parse --short HEAD) \
     ruoyi-fastapi-backend
   docker push your-registry/ruoyi-backend:$(git rev-parse --short HEAD)
   ```

2. **生产服务器只 pull 不 build**：
   ```bash
   docker pull your-registry/ruoyi-backend:latest
   docker compose -f docker-compose.server.yml up -d
   ```

3. **改 ORM/alembic 的标准流程**：
   ```
   开发者改 ORM → 写 alembic 迁移 → 提交 PR
   CI: lint + 测试 + docker build + push 镜像
   生产: pull 新镜像 → 重启 backend 容器 → alembic upgrade head 自动跑
   ```

4. **永远不要在生产跑「代码生成器 `tool/gen`」**——它直接 DDL 不写迁移，下次别人 alembic 会冲突

---

## 5. 前端「工具 / 代码生成」与 alembic 的边界

项目里有两套「改数据库」的入口，**用途完全不同**：

| 入口 | 用途 | 是否写 alembic |
|---|---|---|
| 开发者改 ORM + 写 alembic 迁移 | 改 `sys_*` / `biz_*` 等核心模块 | ✅ 必须写迁移并 commit |
| 前端「工具 / 代码生成」页 `tool/gen/createTable` | 给业务用户快速建新业务表（dev 工具） | ❌ 不写迁移（运行时 DDL） |

### 它们的关系

- **代码生成器**走 `module_generator/service/gen_service.py:create_table_services`，用 `sqlglot_parse` 解析用户粘贴的 SQL 后直接执行 DDL
- 这套机制**不产生 alembic 迁移文件**——数据库里有这张表，但仓库里没记录
- 因此**只能用于开发/演示环境**，生产环境要么禁用、要么把生成的表手工迁移到 alembic

### 当前的保护

`middlewares/demo_mode_middleware.py` 拦截了 `system/* / monitor/* / ai/*`，但**没拦 `tool/gen`**。建议：

- 生产部署时把代码生成器整体下线（前端菜单 `system/gen` 不挂权限 / 后端不挂 router）
- 或者在 `intercept_url_list` 里追加 `'tool/gen'`

---

## 6. 防再犯的 3 个机制（任选其一）

| 机制 | 实施成本 | 防护效果 |
|---|---|---|
| **autogenerate 一键脚本**（`make db-new`） | 低 | 改 ORM 后必须跑一次 |
| **pre-commit 钩子** `alembic check` | 中 | commit 时自动检测 ORM/迁移不一致 |
| **后端启动期 ORM↔DB 自检** | 中 | 启动时反射 DB schema 对比 ORM metadata |

### 推荐：先做「autogenerate 脚本」

`Makefile` 或 `start-dev.sh` 里加：

```bash
# 一键：ORM 改完后生成迁移 + 升级
db-new:
	cd ruoyi-fastapi-backend && \
	  source venv/bin/activate && \
	  alembic -c alembic.ini revision --autogenerate -m "$(MSG)" && \
	  alembic -c alembic.ini upgrade head
```

用法：

```bash
make db-new MSG="add job_executor to sys_job"
```

## 7. 相关文件清单

- `alembic/env.py` — `compare_type=True / compare_server_default=True / include_name` 配好
- `alembic/README.md` — 加新字段/新表的标准流程（行 48-102）
- `alembic/versions/README.md` — MySQL / PG 兼容性说明
- `module_admin/entity/do/*.py` — ORM 模型
- `module_biz/entity/do/*.py` — 业务 ORM 模型
- `module_generator/service/gen_service.py:199` — 代码生成器 create_table
- `middlewares/demo_mode_middleware.py` — 演示模式拦截清单（建议补 `tool/gen`）

## 8. 历史案例

| 日期 | 表 | 缺列 | 修复方式 |
|---|---|---|---|
| 2026-07-12 (晚) | sys_oper_log | oper_location | baseline 补列（**AST 比对发现**） |
| 2026-07-12 (晚) | sys_menu | menu_type server_default='' / sys_dict_type.dict_name | baseline 补 server_default |
| 2026-07-12 (晚) | sys_job / sys_job_log | job_name/job_group/job_executor/invoke_target nullable 对齐 | baseline 改 nullable=False |
| 2026-07-12 (早) | sys_job | job_executor / job_args / job_kwargs | baseline 补列（应急） |
| 2026-07-12 (早) | sys_job_log | job_executor / job_args / job_kwargs / job_trigger | baseline 补列（应急） |
| 2026-07-12 (早) | sys_menu | query / route_name | baseline 补列（应急） |
| v2.9 | sys_user | pwd_update_date / signature | baseline 补列 |
| v2.9 | sys_role | menu_check_strictly / dept_check_strictly | baseline 补列 |

## 9. 2026-07-12 补充：AST 自动比对工具

人肉对比 ORM 和 baseline 迁移**容易漏**。第二次又出现 1054（`sys_oper_log.oper_location`）就是因为没机器化检查。

### 自检脚本思路

用 Python AST 解析两个源，做 4 个维度的差集：

```python
# 核心逻辑：tmp_check_schema.py（已用完删除）
import ast, pathlib

# ① 解析 ORM 模型
def collect_orm():
    """从 module_admin/entity/do/*.py + module_biz/entity/do/*.py 提取所有 Column(...) 调用"""
    ...

# ② 解析 alembic baseline
def collect_mig():
    """从 alembic/versions/0001_*.py + 0002_*.py 提取所有 op.create_table 内的 sa.Column(...)"""
    ...

# ③ 对比
#   ①ORM 列缺失于 baseline (会触发 1054)
#   ②baseline 多出但 ORM 没声明的列（孤儿）
#   ③nullable / type / server_default 不一致
#   ④表清单差集 / 列数对比
```

**关键陷阱**：baseline 列是**位置参数** `sa.Column('col_name', sa.Type, ...)`，列名在 `args[0]`；ORM 是 `Column(BigInteger, ...)`，类型在 `args[0]`。脚本要分别处理。

### 替代方案：直接用 alembic 官方 `check`

项目已配 `compare_type=True / compare_server_default=True`（见 `alembic/env.py`），可以直接：

```bash
cd ruoyi-fastapi-backend
alembic -c alembic.ini check
```

这个命令**真连数据库**、对比 ORM metadata，发现差异会报错。这是项目最权威的检测工具，建议改成 git pre-commit 钩子（见下文）。

### 建议：加 pre-commit 钩子防止再犯

新建 `.git/hooks/pre-commit`：

```bash
#!/bin/bash
# 检测 ORM 是否改了但 alembic 没改
cd ruoyi-fastapi-backend

changed_files=$(git diff --cached --name-only)

# 检测 ORM 文件改动
orm_changed=$(echo "$changed_files" | grep -E 'module_(admin|biz)/entity/do/.*\.py' || true)
mig_changed=$(echo "$changed_files" | grep -E 'alembic/versions/.*\.py' || true)

if [ -n "$orm_changed" ] && [ -z "$mig_changed" ]; then
  echo "⚠️  ORM 改动但 alembic 迁移未改动，请确认："
  echo "$orm_changed"
  echo ""
  echo "   - 如果只改字段 nullable/server_default 不需 alembic 改动，可加 --no-verify 跳过"
  echo "   - 如果是新增列 / 改类型，必须写 alembic 迁移："
  echo "       alembic -c alembic.ini revision --autogenerate -m 'describe change'"
  exit 1
fi
```

或者用 `pre-commit` 框架（`.pre-commit-config.yaml`）：

```yaml
repos:
  - repo: local
    hooks:
      - id: alembic-check
        name: alembic check (ORM vs DB)
        entry: bash -c 'cd ruoyi-fastapi-backend && alembic -c alembic.ini check'
        language: system
        pass_filenames: false
        files: 'ruoyi-fastapi-backend/(module_.*/entity/do/.*\.py|alembic/versions/.*\.py)$'
```