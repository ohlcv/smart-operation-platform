# Alembic 数据库迁移（v4.0）

## 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│  MySQL 容器启动（仅首次 / 删卷重建）                          │
│  └─ /docker-entrypoint-initdb.d/00-bootstrap.sql            │
│     └─ CREATE DATABASE IF NOT EXISTS ruoyi-fastapi          │
├──────────────────────────────────────────────────────────────┤
│  Backend 启动                                                 │
│  └─ server.py:run_alembic_upgrade()                         │
│     └─ alembic upgrade head                                 │
│        ├─ 0001_baseline_sys_ruoyi    RuoYi 原生 sys_*       │
│        ├─ 0002_baseline_biz          业务 8 张表             │
│        ├─ 0003_seed_sys              sys 种子（角色/字典/用户）│
│        └─ 0004_seed_biz              业务种子                │
└──────────────────────────────────────────────────────────────┘
```

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
alembic -c alembic.ini downgrade 0001_baseline_sys_ruoyi

# 自动生成新迁移（基于 ORM diff）
alembic -c alembic.ini revision --autogenerate -m "add xxx_field to biz_yyy"
```

## 加新字段的标准流程

```bash
# 1) 改 ORM
vim module_biz/entity/do/xxx_do.py
#   + sa.Column('new_field', sa.String(50), nullable=True, comment='新字段')

# 2) 自动生成迁移
alembic -c alembic.ini revision --autogenerate -m "add new_field to biz_xxx"

# 3) 检查生成的迁移文件
# vim alembic/versions/2026_07_12_xxxx_add_new_field_to_biz_xxx.py
# 重点检查：op.add_column / op.create_index / 数据迁移（如有）是否正确

# 4) 本地验证
alembic -c alembic.ini upgrade head

# 5) 提交迁移文件（必须）
git add alembic/versions/
git commit -m "feat(db): add new_field to biz_xxx"
```

> ⚠️ **autogenerate 不会检测**：
> - 表/列重命名（会生成 drop + create）
> - 枚举值变更
> - server_default 的变化（需配合 `compare_server_default=True` 已在 env.py 启用）
>
> 复杂变更请手写迁移。

## 加新表的标准流程

同上。`alembic revision --autogenerate` 会自动检测到新表并生成 `op.create_table`。

如果表需要 seed 数据，可以在同一个迁移里：

```python
def upgrade():
    op.create_table('biz_xxx', ...)
    op.execute("INSERT INTO biz_xxx (...) VALUES (...);")
```

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

## 灾难恢复

```bash
# alembic_version 表错乱（极少见）
mysql -uroot -proot ruoyi-fastapi \
  -e "UPDATE alembic_version SET version_num='0001_baseline_sys_ruoyi'"

# 删卷重建（终极方案）
docker compose -f docker-compose.my.yml down -v
docker compose -f docker-compose.my.yml up -d
# backend 启动时自动 alembic upgrade head
```

## 文件命名规范

由 `alembic.ini` 的 `file_template` 控制：

```
YYYY_MM_DD_HHMM-<rev>_<slug>.py
例：2026_07_12_1830-7e9c4f2a1b3d_add_signature_field.py
```

`rev` 是 alembic 自动生成的 12 位 hex（前缀固定，避免冲突），不要手工指定。
`slug` 是你 `-m` 后面写的内容，会自动转成下划线。

## 不要再做的事

- ❌ 直接改生产数据库
- ❌ 在 `sql/_legacy_init/` 里加新 SQL
- ❌ 跳过迁移文件手动 `CREATE TABLE`
- ❌ 把迁移文件的 revision id 改了（会导致 alembic_version 失同步）
- ❌ 用 `if not exists` 之类的「兜底 SQL」代替迁移

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