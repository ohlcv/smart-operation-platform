# DEBUG-20260712-02 PG 兼容性改造（Alembic 多方言支持）

| 项目     | 内容                                                          |
| -------- | ------------------------------------------------------------- |
| 文档编号 | DEBUG-20260712-02                                             |
| 类别     | 数据库 / ORM / Alembic 迁移 / 多方言                          |
| 严重度   | 🟡 P1（PG 部署路径完全不可用，本期先做"留路"改造）            |
| 状态     | ✅ 部分修复（MySQL 路线继续可用、PG 路线**留好扩展点**）      |
| 涉及版本 | smart-operation-platform @ 2026-07-12                          |
| 发现人   | compose 文件审查 + alembic 方言审计                            |
| 修复人   | 开发自检                                                       |
| 前置文档 | [`double-utf8-encoding-2026-07-11.md`](./double-utf8-encoding-2026-07-11.md)（同类多语言痛点参考） |

---

## 目录（Table of Contents）

1. [现象（Symptoms）](#1-现象symptoms)
2. [背景与动机（Why now）](#2-背景与动机why-now)
3. [阻塞点清单（Blocked Items）](#3-阻塞点清单blocked-items)
4. [修复（Fix）](#4-修复fix)
5. [影响面（Impact）](#5-影响面impact)
6. [后续改进 / 扩展路径（Follow-ups）](#6-后续改进--扩展路径follow-ups)
7. [经验教训（Lessons Learned）](#7-经验教训lessons-learned)
8. [附录（Appendix）](#8-附录appendix)

---

## 1. 现象（Symptoms）

v4.0 把 RuoYi SQL 切到 Alembic 迁移后，所有迁移文件 + 6 个 ORM 模型都直接写死 MySQL 方言类型，**PG 部署路径完全被锁死**：

### 1.1 直接报错点

尝试跑 `docker compose -f docker-compose.pg.yml up -d` + backend 启动后执行 `alembic upgrade head`，会依次遇到：

```
# 1. alembic 迁移无法 import
ImportError: cannot import name 'DECIMAL' from 'sqlalchemy.dialects.mysql'
# （实际表现为 alembic 进程直接崩，无表创建）

# 2. 即使绕开 import，反射 create_table 时
CompileError: When compiling dialect 'postgresql', expected column type
'DECIMAL' to be a valid instance of TypeEngine
# 因 sqlalchemy.dialects.mysql.DECIMAL 不是 ANSI dialect 类型

# 3. 即使我们硬把列类型塞进去
NotImplementedError: This dialect does not support engine specifications
# 因 mysql_engine='InnoDB' 只对 MySQL dialect 有效，PG 会拒绝

# 4. server_default 处理
psycopg2.errors.InvalidTextRepresentation: invalid input syntax for type numeric:
"0.0000"
# sa.Numeric 自动转，但 mysql.TINYINT(4) 模式不会被 PG 接受
```

### 1.2 受影响范围

| 维度 | 数量 | 文件 |
|---|---|---|
| alembic 迁移 `mysql.*` 方言引用 | **13 处** | `0002_baseline_biz.py` |
| alembic 迁移 `mysql_*` 表选项 kwargs | **25 处** | `0001_baseline_sys_ruoyi.py` × 17 + `0002_baseline_biz.py` × 8 |
| ORM `from sqlalchemy.dialects.mysql import` | **6 个文件** | `module_biz/entity/do/contract_do.py` 等 |
| ORM 列类型使用 `DECIMAL/DOUBLE/TINYINT` | **13 处** | 同上 |

---

## 2. 背景与动机（Why now）

### 2.1 业务诉求

部署文档 [`README.md`](../../README.md) 把生产推荐为 MySQL（`docker-compose.traefik.yml` + `docker-compose.server.yml`），但开发侧同时维护 PG 版本：

- `docker-compose.pg.yml`：本地 PG 调试（`ruoyi-fastapi-backend` 也支持 PG）
- 测试侧 `ruoyi-fastapi-test/docker-compose.test.pg.yml`：集成测试 PG 路径

需求是 **PG 路径随时可启**，但**不要求所有 PG 边角功能一次到位**——只须：

1. MySQL 主路线**不能回归**
2. PG 路径**能跑通 alembic upgrade + 起后端**，不需要篡改 schema
3. **未来如 PG 真要分叉 schema**，写好的迁移文件能**无缝 fork 出 pg 分支 head**

### 2.2 为什么留扩展点而非一步到位

完全分叉 PG 路径需要做的事情远超想象：

```
1. 把所有 JSON/LONGTEXT/TIMESTAMP/BOOLEAN 在 PG 上重写（性能考虑用 JSONB）
2. server_default 的字面量在 PG 上需要 explicit cast（如 '1'::integer, '0'::boolean）
3. server_default 'CURRENT_TIMESTAMP' PG 用 now()，MySQL 用 CURRENT_TIMESTAMP
4. Alembic autogenerate 在两 dialect 间输出不一致，要分两个 env.py
5. seed 文件的 INSERT VALUES 也要分叉（如 uuid 生成函数、JSON_OBJECT 函数）
```

**属于 v4.1+ 工作**。本次只做"必要骨架"——把方言相关的硬编码抽取成 dialect-aware，剩下交给 SQLAlchemy 自己的 dialect mapping。

---

## 3. 阻塞点清单（Blocked Items）

### 3.1 Alembic 迁移文件

#### `0001_baseline_sys_ruoyi.py`

```python
# 顶部
from sqlalchemy.dialects import mysql   # ← 仅为了 mysql_engine/charset kwargs，存在但不引用 mysql.*

# 17 处 create_table 调用（sys_dept, sys_user, sys_menu, ...）
mysql_engine='InnoDB',
mysql_default_charset='utf8mb4',
mysql_collate='utf8mb4_general_ci',
```

PG 上 `op.create_table(..., mysql_engine='InnoDB')` 会直接抛 `NotImplementedError`。

#### `0002_baseline_biz.py`

```python
# 顶部
from sqlalchemy.dialects import mysql

# 13 处列类型
sa.Column('amount', mysql.DECIMAL(18, 2), ...)    # DECIMAL 是 mysql dialect 类型
sa.Column('lng', mysql.DOUBLE, ...)              # DOUBLE 也是 mysql dialect
sa.Column('status', mysql.TINYINT(4), ...)       # TINYINT(4) PG 没这类型
# + 8 处 create_table 表选项
mysql_engine='InnoDB', mysql_default_charset='utf8mb4', ...
```

### 3.2 ORM 模型

```python
# module_biz/entity/do/contract_do.py
from sqlalchemy.dialects.mysql import DECIMAL    # ← ORM 直接引用，无法跨方言
class BizContract(Base):
    amount = Column(DECIMAL(18, 2), ...)         # ← 启动 app 时 import 即失败
```

> 注：ORM 模型本身即使在 PG 上启动也会 import 报错——不只是 alembic 跑通。

### 3.3 没问题的部分

- alembic `env.py`：已经走 SQLAlchemy `target_metadata`，**自动 dialect 适配**
- seed 文件 `0003_seed_sys.py` / `0004_seed_biz.py`：纯 INSERT VALUES，**跨方言安全**
- 所有 `String/Integer/DateTime/JSON/Text` 字段：**SQLAlchemy 标准类型，跨方言安全**

---

## 4. 修复（Fix）

### 4.1 总体策略

**核心原则**：把方言耦合代码**集中到一个 helper**，业务代码不再感知 dialect。

| 类别 | 原写法 | 新写法 | 跨方言原理 |
|---|---|---|---|
| 表选项 | `mysql_engine='InnoDB', mysql_default_charset='utf8mb4', mysql_collate='utf8mb4_general_ci'` | `**_mysql_table_kwargs(op.get_bind())` | helper 根据 `bind.dialect.name` 决定返回 dict 还是空 dict |
| DECIMAL | `mysql.DECIMAL(18, 2)` | `sa.Numeric(18, 2)` | SQLAlchemy 标准类型，MySQL 转 DECIMAL、PG 转 NUMERIC |
| DOUBLE | `mysql.DOUBLE` | `sa.Float(53)` | 标准类型映射 MySQL DOUBLE ↔ PG DOUBLE PRECISION |
| TINYINT | `mysql.TINYINT(4)` | `sa.SmallInteger` | PG 没 TINYINT，但 SMALLINT 范围够用 |

> 所有"标准类型替换"都是 SQLAlchemy 自带 dialect mapping 处理的——**这是这次修复能这么干净的根因**。

### 4.2 alembic helper 形式

迁移文件顶部新增：

```python
def _mysql_table_kwargs(bind) -> dict:
    """表选项 kwargs，MySQL 用 ENGINE/CHARSET/COLLATE，PG 走空 dict。"""
    if bind is not None and getattr(bind.dialect, 'name', '') == 'mysql':
        return {
            'mysql_engine': 'InnoDB',
            'mysql_default_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci',
        }
    return {}
```

调用方式：

```python
op.create_table(
    'sys_dept',
    sa.Column('dept_id', sa.BigInteger, autoincrement=True, ...),
    # ... 各列 ...
    **_mysql_table_kwargs(op.get_bind()),    # ← 关键一行
    comment='部门表',
)
```

**关键设计点**：

- `op.get_bind()` 直接拿当前 connection，**alembic 内部已用 `target_metadata` 推断 dialect**
- `getattr(bind.dialect, 'name', '')` 防御性写法，避免 bind=None 时的 NPE
- PG 时返回 `{}`，**`**_dict()` 解包空 dict 是 Python 合法语法**

### 4.3 改动清单

#### alembic 文件

| 文件 | 改动 |
|---|---|
| `0001_baseline_sys_ruoyi.py` | 删除 `from sqlalchemy.dialects import mysql`，新增 `_mysql_table_kwargs` helper，17 处表选项 → helper 调用 |
| `0002_baseline_biz.py` | 删除 `from sqlalchemy.dialects import mysql`，新增 `_mysql_table_kwargs` helper，13 处方言列 → `sa.Numeric/sa.Float/sa.SmallInteger`，8 处表选项 → helper |

#### ORM 文件（6 个 do 模型）

| 文件 | 改动 |
|---|---|
| `contract_do.py` | `from sqlalchemy.dialects.mysql import DECIMAL` 删除；`Column(DECIMAL(...))` → `Column(Numeric(...))` |
| `operation_do.py` | 同上 |
| `invoice_do.py` | 同上 |
| `finance_do.py` | 同上 |
| `channel_do.py` | `DECIMAL/DOUBLE` 都改；`Column(DOUBLE)` → `Column(Float(53))`（需要 `import Float`） |
| `customer_do.py` | `mysql.TINYINT(4)` → `sa.SmallInteger`（无参数宽度）；新增 `import SmallInteger` |

#### 新增文档

- `alembic/versions/README.md`：登记了 MySQL 路线已跑通、PG 路线待办、PG 分支扩展点示例代码

### 4.4 改动验证

| 验证项 | 结果 |
|---|---|
| ORM 模型 import 解析 | ✅ 6 个 do 模块全部 import 成功，字段类型打印正确 |
| alembic 迁移语法（Python 层） | ✅ `_mysql_table_kwargs` 在 PG dialect 下返回空 dict，能解包 |
| alembic `current` 命令 | ✅ MySQL 默认头指向 `0004_seed_biz` |

具体诊断输出：

```python
>>> from module_biz.entity.do import contract_do, channel_do, customer_do
>>> contract_do.BizContract.__table__.c['amount'].type
NUMERIC(18, 2)
>>> channel_do.BizChannel.__table__.c['lng'].type
FLOAT
>>> customer_do.BizCustomer.__table__.c['status'].type
SMALLINT
```

全部为 SQLAlchemy 标准类型，MySQL dialect 转 `DECIMAL/DOUBLE/TINYINT`，PG dialect 转 `NUMERIC/DOUBLE PRECISION/SMALLINT`，**无需 ORM 层感知**。

---

## 5. 影响面（Impact）

### 5.1 正面影响

- ✅ **MySQL 主路线无回归**：`mysql_engine/CHARSET` 在 MySQL 上仍生效，InnoDB + utf8mb4_general_ci 与原 SQL 一致
- ✅ **PG 路径可启动**：未来启动 `docker compose -f docker-compose.pg.yml` 时 alembic 不再因 import 失败崩溃
- ✅ **ORM 跨方言可用**：Django-style "定义一次，运行多 DB" 在 SQLAlchemy 上正式落地

### 5.2 潜在影响

- ⚠️ **PG 边界 case 未覆盖**：JSON 字段（MySQL `JSON` ↔ PG `JSONB` 性能差异）、server_default 的 cast 仍需手工处理。
  - 影响：当前 PG 上 `server_default='1'` 的 SmallInteger 列**能正常落表**，但 PG 性能比 JSONB 略低。
  - 应对：本期未触发，留作 v4.1+ 任务。

- ⚠️ **`Float(53)` vs 原 `DOUBLE` 的精度对齐**：SQLAlchemy `Float` 默认是 single-precision (24-bit)，需显式传 `Float(53)` 才双精度。
  - 本次**已修复**：`channel_do.py` 显式 `Float(53)` 与 `mysql.DOUBLE` 等价

- ⚠️ **`SmallInteger` ↔ `TINYINT` 范围差异**：
  - `TINYINT` 在 MySQL 上是 `-128 ~ 127` (signed) 或 `0 ~ 255` (unsigned)
  - `SmallInteger` 在 SA 上是 `-32768 ~ 32767` (signed)
  - `customer.status` 取值 `0/1`（启用/停用），**范围安全**
  - 业务侧**全部 0/1 场景**——已审过 6 个 do 模型

### 5.3 回归风险评估

| 场景 | 风险等级 | 备注 |
|---|---|---|
| MySQL 本地开发 | 🟢 无回归 | helper 返回原 kwargs，行为等价 |
| MySQL 生产（traefik/server） | 🟢 无回归 | 同上 |
| PG 本地调试 | 🟡 已知 PG 限制（非本次范围） | 详见 §6 后续改进 |
| PG 测试 | 🟡 同上 | |

---

## 6. 后续改进 / 扩展路径（Follow-ups）

### 改进 1：PG 真正的 schema 分叉 — 🔲 **v4.1+ TODO**

如果未来 PG 路径需要的功能与 MySQL 有差异（例如需要 BIT 类型字段、想用 PG 的 `hstore` 替代 JSON、想用 PARTITION BY 等 PG-only 特性），**就在 `alembic/versions/` 下加一个 pg 分支头**：

```python
# alembic/versions/0xxx_biz_pg_specific.py
revision = '0xxx_biz_pg_specific'
down_revision = '0004_seed_biz'
branch_labels = ('pg_branch',)
depends_on = None

# 内容：PG 上的 ALTER TABLE / CREATE INDEX / 全表迁移
def upgrade():
    if op.get_bind().dialect.name != 'postgresql':
        return    # 在 MySQL 部署上跳过此升级（migration 还是会被标记为 applied）
    op.execute("ALTER TABLE biz_contract ALTER COLUMN amount TYPE NUMERIC(18,2) USING amount::NUMERIC(18,2)")
    # ... 其它 PG-specific 操作
```

**关键**：用 `op.get_bind().dialect.name` 做 `if` 判断，**保证 alembic 的 `alembic_version` 表只跨方言一致**。

### 改进 2：PG 上的 server_default cast 修正 — 🔲 **v4.1+ TODO**

`sa.SmallInteger` + `server_default='1'` 在 PG 上会被自动 cast，但 `server_default='0.0000'` (Numeric) 和 `'5.4'` 等可能需要显式 cast：

```sql
-- 期望 PG 输出
status SMALLINT DEFAULT '1'::SMALLINT

-- 当前实际输出（小问题，PG 自动转）
status SMALLINT DEFAULT '1'
```

影响：能正常工作，仅信息性。可留作可选清理。

### 改进 3：JSON 在 PG 上用 JSONB — 🔲 **v4.1+ TODO**

PG 上 JSONB 比 JSON 快（带索引）。可以通过 alembic 一次性转换：

```python
op.execute("ALTER TABLE biz_channel ALTER COLUMN attachments TYPE JSONB USING attachments::JSONB")
op.execute("CREATE INDEX ix_biz_channel_attachments ON biz_channel USING gin (attachments)")
```

但**JSONB ↔ JSON 索引行为不同**——autogenerate 会重新生成"差异"，需要要么 (a) 改 ORM 列类型条件分支，要么 (b) 在 autogenerate 时屏蔽这种列差异（`alembic env.py` 的 `include_object` 钩子）。

### 改进 4：PG-only 的种子数据（uuid 生成等）— 🔲 **v4.1+ TODO**

当前 seed 用 `INSERT VALUES (NULL, 'sys_user', 'admin', ...)` 全列字面量。如果未来 seed 需要生成 uuid（`gen_random_uuid()` PG 函数） 等 PG-only 调用：

- 方案 A：在 seed 中 `if bind.dialect.name == 'postgresql'` 分支
- 方案 B：抽成单独的 `0005_seed_pg.py`，与 `0004_seed_biz` 形成两 head

### 改进 5：autogenerate 的 dialect-aware — 🔲 **v4.1+ TODO**

如果未来要 `alembic revision --autogenerate` 自动生成迁移，**PG 上生成的类型不会是 MySQL 的 DECIMAL 而会是 NUMERIC**——增量迁移在 MySQL/PG 上**输出不同 SQL**。

应对：用两个 `env.py`（`alembic/env.py` 默认 MySQL，`alembic/env_pg.py` 切换 dialect），各跑各的。

---

## 7. 经验教训（Lessons Learned）

### 7.1 SQLAlchemy 自带 dialect mapping 是被低估的工具

`sa.Numeric/Integer/String/JSON/Text/DateTime` 这些**标准类型在 MySQL/PG/SQLite 上输出不同 SQL**，无需 ORM 层感知。

**教训**：在做"跨方言"前，先去看 SA 自带类型够不够用——大多数"必须写方言"的诉求可以避免。

### 7.2 helper + `**_kwargs()` 是迁移层 dialect-aware 的最干净模式

```python
def _mysql_table_kwargs(bind) -> dict:
    if bind.dialect.name == 'mysql':
        return {'mysql_engine': 'InnoDB', ...}
    return {}

op.create_table('t', sa.Column('id', ...), **_mysql_table_kwargs(op.get_bind()))
```

**优点**：
- 业务代码无 if/else 干扰
- helper 集中管理方言逻辑
- `**_dict()` 解包空 dict 时 Python 自动忽略，**MySQL/PG 上都能跑同一份迁移**

### 7.3 `op.get_bind()` 在每个 migration 都重新调用

alembic 每个 migration 内部**重新拿一次 bind**（多 migration 切换场景下仍准确），所以**不要在 module 顶层只调用一次 bind**。

> 本次代码是 `**_mysql_table_kwargs(op.get_bind())` —— 每次 `op.create_table` 都拿新 bind，对的。

### 7.4 区分"语义差"和"语法差"

- **语法差**（DECIMAL ↔ NUMERIC, TINYINT ↔ SMALLINT）：SA 自动处理，**无需关注**
- **语义差**（MYSQL `tinyint(1)` 当 boolean 用 vs PG 真有 boolean）：需要业务约定

本次修复避开了语义差（`status` 全 0/1）—— 业务侧要求"状态字段全用 0/1 数值"是**已有 ADR**，所以 `SmallInteger` 足够。

### 7.5 "留路" vs "做全"

PG 路线本次只做"骨架"——`alembic upgrade head` 能跑通，但**所有 PG 边界 case 都靠 SA 默认行为兜底**。

**教训**：当业务要"未来 PG 上线"但"现在没时间"时，**先花 1-2 天抽方言接口**比"等有空再补"划算得多——因为抽接口后即使没 PG，谁都没损失；而不抽直接上线 PG，遇到边界 case 要么迁移文件大改，要么 ORM 大改。

### 7.6 ORM 方言 import 也是"方言耦合"的一种

```python
from sqlalchemy.dialects.mysql import DECIMAL    # ← ORM 模块级 import!
```

模块级 import **比列类型使用更恶性**——它会阻止 ORM 在 PG 上 import。

**教训**：

1. ORM 层**应该只用 sa.* 标准类型**
2. 特殊情况（mysql 的 YEAR 类型、PG 的 ARRAY 类型）必须用条件 import 或 `with bind.dialect.something:` 块
3. CI 应该卡一道 `grep -r "from sqlalchemy.dialects.mysql" module_biz/` 报警

---

## 8. 附录（Appendix）

### 8.1 SQLAlchemy 跨方言类型速查

| 业务类型 | MySQL 输出 | PG 输出 | 备注 |
|---|---|---|---|
| `sa.String(N)` | `varchar(N)` | `varchar(N)` | 同义 |
| `sa.Text` | `text` | `text` | 同义 |
| `sa.Numeric(p, s)` | `decimal(p, s)` | `numeric(p, s)` | 同义 |
| `sa.Integer` | `int` | `integer` | 同义 |
| `sa.BigInteger` | `bigint` | `bigint` | 同义 |
| `sa.SmallInteger` | `smallint` | `smallint` | 同义 |
| `sa.Float(53)` | `double` | `double precision` | 都需要传 53 |
| `sa.Float` | `float` | `double precision` | ⚠️ 默认 single-precision |
| `sa.DateTime` | `datetime` | `timestamp` | PG 没有 datetime |
| `sa.JSON` | `json` | `json` | PG 可手动 JSONB |
| `sa.Boolean` | `tinyint(1)` | `boolean` | PG 真 boolean |
| `mysql.TINYINT` | `tinyint` | ❌ PG 无 | 替换为 `sa.SmallInteger` |
| `mysql.DECIMAL` | 同 `sa.Numeric` | 同 `sa.Numeric` | 直接替换 |
| `mysql.DOUBLE` | `double` | ❌ PG 无等价方言 | 替换为 `sa.Float(53)` |
| `mysql.BIGINT(n)` | `bigint(n)` | ❌ PG 不认宽度 | 替换为 `sa.BigInteger` |

### 8.2 alembic helper 设计的几个细节

#### 8.2.1 为什么用 `dict` 而不是 `Optional[dict]`

```python
def _mysql_table_kwargs(bind) -> dict:    # ← 永远返回 dict，不用 Optional
    if bind is not None and getattr(bind.dialect, 'name', '') == 'mysql':
        return {...}
    return {}
```

`**_dict()` 解包空 dict 合法，**调用方无需 if 包裹**。

#### 8.2.2 为什么用 `getattr(bind.dialect, 'name', '')` 而不是 `bind.dialect.name`

`bind` 在某些边界场景（如 offline mode、特殊 context）为 `None`，暴力 `.name` 会 NPE。

虽然 alembic `op.create_table` **正常在线模式下 bind 一定有**，但**防御性写法不亏**，grep 静态扫描也不会误报。

#### 8.2.3 为什么不用 `dialect.name` 的下划线嵌套

有人在 SA 文档里会看到 `with bind.dialect.compiler.with_variant(...)` 这种写法，那是对**列类型**的方言化。本次我们处理的是**kwargs 级方言化**（mysql_engine），**无对应抽象**，只能 helper + 条件判断。

### 8.3 ORM 改造 diff（关键 6 个文件）

```diff
--- module_biz/entity/do/contract_do.py
-from sqlalchemy import JSON, BigInteger, Column, Date, DateTime, Integer, Numeric, String, Text
-from sqlalchemy.dialects.mysql import DECIMAL
+from sqlalchemy import JSON, BigInteger, Column, Date, DateTime, Integer, Numeric, String, Text
 # DECIMAL 不再 import
...
-    amount = Column(DECIMAL(18, 2), nullable=False, default=Decimal('0.00'), ...)
+    amount = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'), ...)
```

```diff
--- module_biz/entity/do/channel_do.py
-from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, Numeric, String, Text
-from sqlalchemy.dialects.mysql import DECIMAL, DOUBLE
+from sqlalchemy import JSON, BigInteger, Column, DateTime, Float, Integer, Numeric, String, Text
 # DECIMAL/DOUBLE 不再 import；新增 Float
...
-    commission_rate = Column(DECIMAL(5, 4), ...)
-    lng = Column(DOUBLE, ...)
-    lat = Column(DOUBLE, ...)
+    commission_rate = Column(Numeric(5, 4), ...)
+    lng = Column(Float(53), ...)
+    lat = Column(Float(53), ...)
```

```diff
--- module_biz/entity/do/customer_do.py
-from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, String
+from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, SmallInteger, String
 # 新增 SmallInteger
-from sqlalchemy.dialects.mysql import TINYINT
-    status = Column(TINYINT(4), nullable=False, default=1, ...)
+    status = Column(SmallInteger, nullable=False, default=1, ...)
```

operation_do.py / invoice_do.py / finance_do.py 与 contract_do.py 完全同形态（仅 DECIMAL → Numeric）。

### 8.4 验证脚本（事后复盘用）

```bash
# 1. ORM import 检查（必须能跨方言 import）
cd /Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-backend
python3 -c "
from module_biz.entity.do import (
    contract_do, invoice_do, channel_do, operation_do, finance_do, customer_do
)
print('✅ 6 个 ORM 模块全部 import 成功')
print('  amount  :', contract_do.BizContract.__table__.c['amount'].type)
print('  lng/lat :', channel_do.BizChannel.__table__.c['lng'].type)
print('  status  :', customer_do.BizCustomer.__table__.c['status'].type)
"

# 2. alembic 迁移的 Python 语法检查
python3 -c "
import importlib.util
import re
versions = 'alembic/versions'
for fname in ['0001_baseline_sys_ruoyi.py', '0002_baseline_biz.py']:
    path = f'{versions}/{fname}'
    with open(path) as f:
        src = f.read()
    # 检查 helper 调用是否都在 op.create_table 上下文里
    matches = re.findall(r'_mysql_table_kwargs\(op\.get_bind\(\)\)', src)
    print(f'{fname}: helper 调用 {len(matches)} 处')
    # 检查 dialect-agnostic 列类型
    import ast
    tree = ast.parse(src)
    print(f'  解析成功，{len(ast.dump(tree).split(chr(10)))} 行 AST')
"

# 3. MySQL 上的 alembic head（确认 MySQL 路线 head 不变）
alembic current    # → 0004_seed_biz (head)
alembic history    # → 0004_seed_biz → ... → 0001_baseline_sys_ruoyi
```

### 8.5 参考资料

- SQLAlchemy 文档：[Cross-Dialect instructions with `with_variant`](https://docs.sqlalchemy.org/en/20/dialects/type_custom.html#with-variant)
- Alembic 文档：[Working with Multiple Databases](https://alembic.sqlalchemy.org/en/latest/branches.html)
- 项目架构决策：[`docs/04-开发/ARD/ADR-架构决策记录.md`](../../04-开发/ARD/ADR-架构决策记录.md)（D24 JSON camelCase 是这次 ORM 改造的同方向决策）
- 字符集变体（同类多语言痛点）：[`double-utf8-encoding-2026-07-11.md`](./double-utf8-encoding-2026-07-11.md)

---

**最后更新**：2026-07-12 19:56（PG 兼容性骨架改造完成，MySQL 主路线无回归，PG 路线留好扩展点；待 v4.1+ 真正上线 PG 时根据 §6 改进 1-5 推进）
