# MySQL Docker init.sql 自动初始化机制 & 业务 SQL 漏挂问题

**日期**：2026-07-11
**类型**：基础设施配置缺陷
**影响**：容器首次启动后 biz 模块无种子数据、菜单/角色/字典全部缺失
**根因**：`start-dev.sh` 只挂载了 `ruoyi-fastapi.sql`，漏挂 `biz_init.sql` 和 `biz_menus_roles_init.sql`

---

## 1. 问题现象

容器启动后，前端访问 `/biz/contract` 和 `/biz/customer` 出现 404 或空白，数据库检查发现：

```
biz_customer    → 0 行（应该有 5 行种子数据）
biz_contract    → 0 行（应该有 3 行种子数据）
sys_menu        → path='contract'（应为 'biz/contract'）
sys_role        → 只有 admin/common，缺 7 个业务审批角色
sys_dict_data   → 缺 contract_type / business_line / customer_type / channel_type
```

## 2. 根因：MySQL 镜像的 entrypoint 机制

MySQL 官方镜像有一个特殊目录：`/docker-entrypoint-initdb.d/`

**行为规则**：

```
容器首次启动 + 数据卷为空
  → 扫描 /docker-entrypoint-initdb.d/
  → 按文件名字母顺序执行所有 .sql / .sh / .sql.gz 文件
  → 之后不再执行（卷已有数据则跳过）

容器重启 / rm 后再 up
  → 数据卷不为空
  → 什么都不做，跳过所有 init 脚本
```

**因此**：

| 触发时机 | init 脚本会跑吗 |
|---|---|
| 容器首次启动（卷为空） | ✅ 按字母序执行 |
| `docker compose restart` | ❌ 跳过 |
| `docker rm` 再 `docker run`（不删卷） | ❌ 跳过 |
| `docker rm -v`（删卷）再启动 | ✅ 重新执行 |

## 3. 原 start-dev.sh 配置（错误）

```bash
# start-dev.sh 旧版 MySQL 挂载
docker run \
  -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql:/docker-entrypoint-initdb.d/ruoyi-fastapi.sql \
  # 只挂了 1 个 SQL，biz 相关全漏
```

**后果**：biz 三张表由 ORM `Base.metadata.create_all()` 自动建了表结构，但：

- ❌ 无种子数据（INSERT 脚本未执行）
- ❌ 无菜单/角色/字典（business SQL 脚本未执行）

## 4. 修复后的 start-dev.sh 配置

```bash
# start-dev.sh 新版（2026-07-11 修复）
docker run \
  -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql:/docker-entrypoint-initdb.d/01-ruoyi-fastapi.sql \
  -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/biz_init.sql:/docker-entrypoint-initdb.d/02-biz-init.sql \
  -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/biz_menus_roles_init.sql:/docker-entrypoint-initdb.d/03-biz-menus-roles.sql \
  -v $PROJECT_ROOT/mysql-conf/charset.cnf:/etc/mysql/conf.d/charset.cnf:ro
```

**执行顺序**（字母序）：

```
01-ruoyi-fastapi.sql        → RuoYi 基础数据（25 张系统表，sys_user/sys_role/sys_menu 等）
02-biz-init.sql             → biz_customer / biz_contract / biz_approval 建表 + 种子数据
03-biz-menus-roles.sql      → 菜单路径修正 + 7 级审批角色 + admin 全菜单授权 + 4 类业务字典
```

## 5. 各 SQL 文件职责

| 文件 | 作用 | 重跑安全性 |
|---|---|---|
| `ruoyi-fastapi.sql` | RuoYi 框架主初始化 | 首次启动专用，不支持二次执行 |
| `biz_init.sql` | biz 业务表建表 + 种子数据 | 有 CREATE TABLE 无 IF NOT EXISTS，**二次执行会报错**（需删卷） |
| `biz_menus_roles_init.sql` | 菜单 + 角色 + 字典 | 有 INSERT IGNORE，**二次执行安全**（重复键跳过） |

### biz_init.sql 的安全隐患

```sql
-- 当前写法（不安全）
CREATE TABLE biz_customer (...);           -- 无 IF NOT EXISTS
INSERT INTO biz_customer (...) VALUES (...);  -- 会重复插入

-- 建议改为（已记录待修）
CREATE TABLE IF NOT EXISTS biz_customer (...);
INSERT INTO biz_customer (...) VALUES (...) ON DUPLICATE KEY UPDATE id=id;
```

**现状处理**：由于 MySQL entrypoint 只在卷为空时执行一次，这个问题已被机制规避，但建议加上 IF NOT EXISTS 以防手动重跑脚本。

## 6. 手动补救步骤（当前已运行的容器）

```bash
# 如果当前容器是在修复 start-dev.sh 之前启动的（SQL 未自动跑）
# 需要手动执行以下脚本：

# Step 1: 重建 biz 表 + 种子数据
docker exec -i ruoyi-mysql mysql -uroot -proot ruoyi-fastapi \
  < sql/biz_init.sql

# Step 2: 业务菜单 + 角色 + 字典
docker exec -i ruoyi-mysql mysql -uroot -proot ruoyi-fastapi \
  < sql/biz_menus_roles_init.sql

# 验证
docker exec ruoyi-mysql mysql -uroot -proot -t -e "
  SELECT COUNT(*) FROM biz_customer;          -- 应为 5
  SELECT COUNT(*) FROM biz_contract;         -- 应为 3
  SELECT COUNT(*) FROM sys_role_menu WHERE role_id=1;  -- 应为 95（admin 全菜单）
  SELECT COUNT(*) FROM sys_dict_type WHERE dict_id >= 100;  -- 应为 4
"
```

## 7. 正确的开发工作流

```
开发阶段改 SQL（schema / 种子 / 菜单 / 角色）
  ↓
docker compose down -v     ← 必须删卷才能重跑 init
  ↓
docker compose up -d
  ↓
✅ 3 个 SQL 自动按顺序执行，环境完整
```

**不要**：
- 只 `docker compose restart` → init SQL 不重跑，改的不生效
- 只 `docker rm` 不 `-v` → 卷还在，什么都不会变

## 8. 生产环境注意

生产环境如果用 Docker 部署，同样需要确保 `docker-compose.yml` 或启动脚本挂载了这 3 个 SQL（顺序不能乱）。生产环境通常**不会删卷重建**（会丢数据），所以：

- 首次部署时 3 个 SQL 会自动跑完 ✅
- 后续改 SQL 需要手动执行或写 migration 脚本
- 不要把 `biz_init.sql` 的 INSERT 放在有持久数据的库里跑，会重复插入

---

**关联文件**：
- `start-dev.sh` — MySQL 容器启动配置（挂载 3 个 init SQL）
- `ruoyi-fastapi-backend/sql/biz_init.sql` — biz 业务表 + 种子数据
- `ruoyi-fastapi-backend/sql/biz_menus_roles_init.sql` — 菜单 + 角色 + 字典
- `docs/04-开发/开发进度台账.md` — 记录在 v2.6
