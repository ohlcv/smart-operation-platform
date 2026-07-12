# Alembic 迁移目录说明

## MySQL 路线（已跑通）

按顺序：

| 序号 | 文件 | 作用 | down_revision |
|---|---|---|---|
| 0001 | `0001_baseline_sys_ruoyi.py` | 17 张 sys_*（RuoYi 原生） | None |
| 0002 | `0002_baseline_biz.py` | 8 张 biz_*（业务） | 0001 |
| 0003 | `0003_seed_sys.py` | sys_* 字典/角色/菜单 seed | 0002 |
| 0004 | `0004_seed_biz.py` | biz_* 业务 seed（字典 + demo 数据） | 0003 |

Head：`0004_seed_biz`

## PG 兼容预留位（v4.1+ 待办）

迁移里所有 `mysql.DECIMAL/TINYINT/DOUBLE/ENGINE/CHARSET` 已替换为：

| 原 MySQL | 改为 | PG 行为 |
|---|---|---|
| `mysql.DECIMAL(18,2)` | `sa.Numeric(18,2)` | `NUMERIC(18,2)`（同义） |
| `mysql.TINYINT(4)` | `sa.SmallInteger` | `SMALLINT` |
| `mysql.DOUBLE` | `sa.Float(53)` | `DOUBLE PRECISION` |
| `mysql_engine='InnoDB'` 等 | `_mysql_table_kwargs(bind)` helper 内分支控制 | PG 时返回空 dict |

这层抽象在 SQLAlchemy 自带 dialect mapping 上，**PG 上跑 `alembic upgrade head` 不需要修改任何迁移**。但是还需注意：

### 已知 PG 仍需手动处理的事项

1. **JSON 字段**：MySQL `JSON` ↔ PG `JSONB`（性能更好）。SQLAlchemy 的 `JSON` 在 PG 上默认用 `JSON`，需要时手动改 `JSONB`。
2. **Text 大字段**：MySQL `LONGTEXT` ↔ PG `TEXT`。当前代码用 `sa.Text`，OK。
3. **Boolean 转 int**：MySQL 用 `tinyint(1)`/`int`，PG 偏好 `boolean`。当前 `status` 用 `SmallInteger`，无需改。
4. **Server default 引号**：MySQL `server_default='0.00'` PG 也能识别，但 `server_default='1'` PG 期待 `'1'::integer`。SQLAlchemy 自动处理，但某些边角需要 explicit cast。
5. **字符集**：MySQL `utf8mb4` ≠ PG `UTF8`，Postgres `initdb` 时已经决定。
6. **autoincrement**：MySQL `AUTO_INCREMENT` ↔ PG `SERIAL/BIGSERIAL/IDENTITY`。当前 `BigInteger, autoincrement=True` SQLAlchemy 自动处理，PG 用 `nextval('seq')`。

### PG 分支扩展点（如果以后真要分叉）

如果未来 schema 在 MySQL 和 PG 上要演进不一致，可以从 `0004_seed_biz` 分叉：

```python
# alembic/versions/0005_biz_pg_specific.py  (示例，未启用)
revision = '0005_biz_pg_specific'
down_revision = '0004_seed_biz'   # 与 MySQL head 平行
branch_labels = ('pg_branch',)    # 标识分支名
depends_on = None
```

然后 MySQL 后续迁移用 `down_revision = '0004_seed_biz'`。这样 alembic 会存在 **两个 head**，需要手动指定 base 推进：

```bash
alembic upgrade head  # 默认走 MySQL
alembic -x db=pg upgrade pg_branch  # 通过 env 控制走 PG 分支
```

但目前 **不需要**——上面的标准类型替换已足够让 PG 跑通。

## 验证命令

```bash
# MySQL（默认）
cd ruoyi-fastapi-backend
alembic current                  # 应该输出 0004_seed_biz
alembic upgrade head             # 无变更

# PG（需 .env 改 db_type=postgresql 且 alembic.ini 用同步 URL）
PGPASSWORD=root psql -h localhost -p 15432 -U root -d ruoyi-fastapi \
  -c "\dt" | head -30             # 应该看到 25 张表
PGPASSWORD=root psql -h localhost -p 15432 -U root -d ruoyi-fastapi \
  -c "\d biz_contract"            # amount 列应为 numeric(18,2)
```
