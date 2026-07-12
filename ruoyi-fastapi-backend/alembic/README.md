# Alembic 数据库迁移

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│  MySQL 容器启动（仅首次 / 删卷重建）                          │
│  └─ /docker-entrypoint-initdb.d/00-bootstrap.sql            │
│     └─ CREATE DATABASE IF NOT EXISTS ruoyi-fastapi          │
├─────────────────────────────────────────────────────────────┤
│  Backend 启动                                                 │
│  └─ server.py:run_alembic_upgrade()                         │
│     └─ alembic upgrade head                                 │
│        ├─ 0001_baseline_all   sys + biz 全套表结构           │
│        └─ 0002_seed_all       sys + biz 全部种子数据         │
└─────────────────────────────────────────────────────────────┘
```

## 迁移文件清单

`alembic/versions/` 下只有 **2 个** 迁移文件，按顺序执行：

| 序号 | 文件 | 作用 | down_revision | 行数 |
|---|---|---|---|---|
| 0001 | `0001_baseline_all.py` | 建 sys_*（17 张）+ biz_*（8 张）共 25 张表 | None | 646 |
| 0002 | `0002_seed_all.py` | 灌入全部种子数据（admin/角色/菜单/字典/8 业务表 demo） | 0001 | 420 |

**Head**：`0002_seed_all`

### 0001_baseline_all 涵盖的 25 张表

**sys_*（17 张 RuoYi 原生表）**

| 表 | 说明 |
|---|---|
| `sys_dept` | 部门表 |
| `sys_user` | 用户表（含 v2.9 signature 电子签名字段） |
| `sys_user_role` / `sys_user_post` | 用户-角色 / 用户-岗位 关联表 |
| `sys_role` / `sys_role_dept` / `sys_role_menu` | 角色 + 关联表 |
| `sys_menu` | 菜单权限表 |
| `sys_post` | 岗位表 |
| `sys_dict_type` / `sys_dict_data` | 字典主表 |
| `sys_config` | 参数配置表 |
| `sys_notice` | 通知公告表 |
| `sys_job` / `sys_job_log` | 定时任务 + 日志 |
| `sys_logininfor` / `sys_oper_log` | 登录 / 操作日志 |

**biz_*（8 张业务表）**

| 表 | 说明 |
|---|---|
| `biz_customer` | 客户档案（含 v3.3 province） |
| `biz_contract` | 合同主表（含 v3.3 province） |
| `biz_approval` | 审批记录表 |
| `biz_channel` | 渠道主表（含 v3.3 province/city/lng/lat） |
| `biz_invoice` | 发票主表 |
| `biz_finance_entry` | 财务流水台账 |
| `biz_bank_statement` | 银行对账单导入 |
| `biz_operation` | 经营数据表 |

### 0002_seed_all 涵盖的种子数据

| 类别 | 内容 |
|---|---|
| sys_dept | 10 个部门（集团 + 深圳/长沙分公司 + 5 个直属部门 + 2 个长沙部门） |
| sys_role | 9 个角色（admin 隐藏超管 + common 普通 + 7 个审批角色） |
| sys_user | 8 个用户（admin + 7 个审批测试账号，默认密码 admin123 / 123456） |
| sys_user_role | admin 绑定 8 个角色（含 `(1,1)`，确保 super admin 权限） |
| sys_menu | 16 个菜单（系统/监控/工具/官网/业务目录 + 5 个业务菜单 + 仪表盘） |
| sys_role_menu | 角色菜单权限映射 |
| sys_config | 8 条默认参数配置（修复验证码开关失效） |
| sys_dict_type / sys_dict_data | 12 类字典 + 数据项（含 4 类业务字典） |
| biz_customer / contract / channel / invoice / finance / operation | 5 客户 + 3 合同 + 4 渠道 + 1 发票 + 1 流水 + 3 期经营数据 |

> **所有 INSERT 都用 `INSERT IGNORE`，重复执行不报错。**

---

## 快速命令

```bash
cd ruoyi-fastapi-backend

# 查看当前数据库版本
alembic -c alembic.ini current

# 查看所有迁移历史
alembic -c alembic.ini history

# 查看未执行的迁移
alembic -c alembic.ini history --indicate-current

# 应用所有未执行的迁移
alembic -c alembic.ini upgrade head

# 回退一个版本
alembic -c alembic.ini downgrade -1

# 回退到指定版本
alembic -c alembic.ini downgrade 0001_baseline_all

# 自动生成新迁移（基于 ORM diff）
alembic -c alembic.ini revision --autogenerate -m "add xxx_field to biz_yyy"
```

---

## 加新字段的标准流程

```bash
# 1) 改 ORM 模型
vim module_biz/entity/do/xxx_do.py
#   + sa.Column('new_field', sa.String(50), nullable=True, comment='新字段')

# 2) 自动生成迁移（文件名形如 2026_07_12_1830-7e9c4f2a1b3d_add_new_field.py）
alembic -c alembic.ini revision --autogenerate -m "add new_field to biz_xxx"

# 3) 检查生成的迁移文件
vim alembic/versions/2026_07_12_1830-7e9c4f2a1b3d_add_new_field.py
# 重点检查：op.add_column / op.create_index / 数据迁移（如有）是否正确

# 4) 本地验证
alembic -c alembic.ini upgrade head

# 5) 启动 backend 时会自动 upgrade head，无需手动
```

> ⚠️ **autogenerate 不会检测**：
> - 表/列重命名（会生成 drop + create）
> - 枚举值变更
> - server_default 的变化（需配合 `compare_server_default=True`，已在 env.py 启用）
>
> 复杂变更请手写迁移。

---

## 加新表的标准流程

同上。`alembic revision --autogenerate` 会自动检测到新表并生成 `op.create_table`。

新表的 seed 数据可以写在**同一个迁移**里：

```python
def upgrade():
    op.create_table('biz_xxx', ...)
    op.execute("INSERT IGNORE INTO biz_xxx (...) VALUES (...);")
```

如果 seed 数据量大（>50 行），建议拆成单独的 `000X_seed_xxx.py` 迁移，down_revision 指向建表迁移。

---

## 数据迁移（已有表的数据回填）

```python
def upgrade():
    # 1) 加列（先 nullable=True）
    op.add_column('biz_xxx', sa.Column('new_field', sa.String(50), nullable=True))

    # 2) 回填数据
    op.execute("UPDATE biz_xxx SET new_field = '默认值' WHERE new_field IS NULL;")

    # 3) 改为 NOT NULL（如果有强制约束）
    op.alter_column('biz_xxx', 'new_field', nullable=False)
```

---

## 文件命名规范

由 `alembic.ini` 的 `file_template` 控制：

```
YYYY_MM_DD_HHMM-<rev>_<slug>.py
例：2026_07_12_1830-7e9c4f2a1b3d_add_signature_field.py
```

- `rev`：alembic 自动生成的 12 位 hex，**不要手工指定**
- `slug`：`-m` 后面的内容，自动转成下划线

---

## env.py 关键配置

```python
# 使用同步驱动（alembic 不能用 asyncmy）
alembic_config.set_main_option('sqlalchemy.url', SYNC_SQLALCHEMY_DATABASE_URL)

# 自动检测类型差异 / server_default 差异
compare_type=True
compare_server_default=True

# 过滤 alembic_version 等元数据表
include_name=lambda name, type_, parent_names: \
    name in target_metadata.tables if type_ == 'table' else True
```

---

## 灾难恢复

```bash
# alembic_version 表错乱（极少见）
docker compose -f docker-compose.my.yml exec ruoyi-mysql mysql -uroot -proot ruoyi-fastapi \
  -e "UPDATE alembic_version SET version_num='0001_baseline_all'"

# 删卷重建（终极方案）
docker compose -f docker-compose.my.yml down -v
docker compose -f docker-compose.my.yml up -d
# backend 启动时自动 alembic upgrade head
```

---

## 不要再做的事

- ❌ 直接改生产数据库
- ❌ 在 `sql/_legacy_init/` 里加新 SQL（该目录已冻结，仅做历史参考）
- ❌ 跳过迁移文件手动 `CREATE TABLE`
- ❌ 改已应用迁移的 revision id（会导致 alembic_version 失同步）
- ❌ 用 `if not exists` 之类的「兜底 SQL」代替迁移

---

## PG 兼容性说明

迁移里所有 `mysql.DECIMAL/TINYINT/DOUBLE/ENGINE/CHARSET` 已替换为：

| 原 MySQL | 改为 | PG 行为 |
|---|---|---|
| `mysql.DECIMAL(18,2)` | `sa.Numeric(18,2)` | `NUMERIC(18,2)` |
| `mysql.TINYINT(4)` | `sa.SmallInteger` | `SMALLINT` |
| `mysql.DOUBLE` | `sa.Float(53)` | `DOUBLE PRECISION` |
| `mysql_engine='InnoDB'` 等 | `_mysql_table_kwargs(bind)` helper 内分支控制 | PG 时返回空 dict |

### 已知 PG 仍需手动处理的事项

1. **JSON 字段**：MySQL `JSON` ↔ PG `JSONB`（性能更好）。SQLAlchemy 的 `JSON` 在 PG 上默认用 `JSON`，需要时手动改 `JSONB`。
2. **Server default 引号**：MySQL `server_default='0.00'` PG 也能识别，但 `server_default='1'` PG 期待 `'1'::integer`。SQLAlchemy 自动处理，但某些边角需要 explicit cast。
3. **字符集**：MySQL `utf8mb4` ≠ PG `UTF8`，Postgres `initdb` 时已经决定。
4. **autoincrement**：MySQL `AUTO_INCREMENT` ↔ PG `SERIAL/BIGSERIAL/IDENTITY`。当前 `BigInteger, autoincrement=True` SQLAlchemy 自动处理，PG 用 `nextval('seq')`。

### PG 分支扩展点（如果以后真要分叉）

```python
# alembic/versions/0003_biz_pg_specific.py  (示例，未启用)
revision = '0003_biz_pg_specific'
down_revision = '0002_seed_all'     # 与 MySQL head 平行
branch_labels = ('pg_branch',)      # 标识分支名
depends_on = None
```

但目前 **不需要**——上面的标准类型替换已足够让 PG 跑通。

---

## 验证命令

```bash
# MySQL（默认）
cd ruoyi-fastapi-backend
alembic -c alembic.ini current                  # 应该输出 0002_seed_all
alembic -c alembic.ini upgrade head             # 无变更

# 查看实际表数
docker compose -f docker-compose.my.yml exec ruoyi-mysql mysql -uroot -proot ruoyi-fastapi \
  -e "SHOW TABLES;" | wc -l                     # 应该 28（含 alembic_version + 25 张业务表 + 2 张额外）

# PG（需 .env 改 db_type=postgresql 且 alembic.ini 用同步 URL）
PGPASSWORD=root psql -h localhost -p 15432 -U root -d ruoyi-fastapi \
  -c "\dt" | head -30                           # 应该看到 25 张表
PGPASSWORD=root psql -h localhost -p 15432 -U root -d ruoyi-fastapi \
  -c "\d biz_contract"                          # amount 列应为 numeric(18,2)
```