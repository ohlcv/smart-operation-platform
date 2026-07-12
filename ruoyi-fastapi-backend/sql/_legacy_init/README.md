# Legacy Init Scripts（已冻结）

⚠️ **本目录的 SQL 文件已不再作为运行时初始化来源**（自 v4.0 起）。

## 为什么冻结？

RuoYi-FastAPI v3.x 阶段使用 `/docker-entrypoint-initdb.d` 挂载 SQL 文件作为
数据库初始化的唯一手段，导致一系列问题：

| 问题 | 影响 |
|------|------|
| initdb 仅在「数据目录为空」时执行一次 | 后续 schema 演进需要写「双轨 IF EXISTS」SQL 兜底 |
| 无法版本化 | 任何字段变更都得手工维护「先后顺序」与「重复执行安全」 |
| 删卷重建 = 数据全没 | 无 down 路径，无法回滚 |
| ORM 与 SQL 双源 | 字段漂移，PR review 需要人肉对齐 |

## v4.0 新架构

```
┌──────────────────────────────────────────────────────────────┐
│ 00-bootstrap.sql    仅 CREATE DATABASE（MySQL initdb 唯一入口）│
├──────────────────────────────────────────────────────────────┤
│ alembic/versions/   所有 schema 演进的唯一权威                │
│                     启动 backend 时自动 upgrade head         │
├──────────────────────────────────────────────────────────────┤
│ 本目录（_legacy_init）                                        │
│                     仅作历史参考，新需求请勿修改这里的文件    │
└──────────────────────────────────────────────────────────────┘
```

## 如何加新字段（新流程）

```bash
# 1) 改 ORM 模型
vim module_biz/entity/do/xxx_do.py

# 2) 自动生成迁移文件
cd ruoyi-fastapi-backend
alembic -c alembic.ini revision --autogenerate -m "add xxx_field to biz_yyy"

# 3) 检查生成的迁移文件，确认无误后提交

# 4) 本地验证
alembic -c alembic.ini upgrade head

# 5) 启动 backend 时自动会 upgrade，无需手动
```

## 如何加新表

同上流程，`alembic revision --autogenerate` 会自动检测并生成 `op.create_table`。

## 如何回滚

```bash
alembic -c alembic.ini downgrade -1   # 回退一个版本
alembic -c alembic.ini history        # 查看历史
```

## 如果 alembic 跑挂怎么办？

极端情况下 alembic 状态错乱（比如手改过表结构），可以：

```bash
# 1) 把 alembic_version 表里记录改成 base 之前（看 history 里最早的 revision id）
mysql -uroot -proot ruoyi-fastapi -e "UPDATE alembic_version SET version_num='<base_revision_id>'"

# 2) 删卷重建（彻底重置）
docker compose down -v && docker compose up -d
```

## 历史文件清单

| 文件 | 原本的作用 | 取代方式 |
|------|-----------|---------|
| `ruoyi-fastapi.sql` | RuoYi 原生 sys_* 全套 + sys_dict 初始化 | `alembic/versions/0001_baseline_sys_ruoyi.py` |
| `ruoyi-fastapi-pg.sql` | PostgreSQL 版本（未启用，仅作参考） | 如需 PG 支持：在 `0001` 写 PG 方言变体或单独维护 `0001_pg_*` |
| `biz_init.sql` | 业务三表 biz_customer/contract/approval + 种子 | `alembic/versions/0002_baseline_biz.py` + `0004_seed_biz.py` |
| `biz_channel_init.sql` | biz_channel + 种子 | `0002_baseline_biz` + `0004_seed_biz` |
| `biz_invoice_init.sql` | biz_invoice + 种子 | `0002_baseline_biz` + `0004_seed_biz` |
| `biz_finance_init.sql` | biz_finance_entry + biz_bank_statement + 种子 | `0002_baseline_biz` + `0004_seed_biz` |
| `biz_operation_init.sql` | biz_operation + 种子 | `0002_baseline_biz` + `0004_seed_biz` |
| `biz_menus_roles_init.sql` | sys_menu/sys_role 修正 + 字典 + 角色挂菜单 | `0003_seed_sys.py`（合并 sys_role_menu / sys_user_role） |
| `dashboard_v3_3_init.sql` | 增量列：biz_channel.province/city/lng/lat + biz_contract.province + biz_customer.province | 已经合并到 `0002_baseline_biz.py` 的 baseline schema |
| `approval_init.sql` | sys_user.signature + 7 测试用户 + 审批菜单 + 角色挂菜单 | 已经合并到 `0003_seed_sys.py`（含 sys_user.signature 列在 `0001` baseline 中） |

## 命名约定

迁移文件命名（alembic.ini 已配置 `file_template`）：

```
YYYY_MM_DD_HHMM-<rev>_<slug>.py
例：2026_07_12_1830-7e9c4f2a1b3d_add_signature_field.py
```

`--autogenerate` 会自动生成 hex revision id，无需手工指定。