# SQL 初始化脚本与运行时 DB 修改的持久化原则（2026-07-12）

**日期**：2026-07-12
**类型**：运维规范 / 数据一致性
**影响**：菜单图标、路径、parent_id 等字段被 API 运行时修改后，删卷重建容器时全部回退；SQL 脚本中存在脏数据（基础脚本与业务脚本图标不一致）
**根因**：运行时 API 修改 DB，未同步写回 SQL 脚本；SQL 脚本间存在 icon 脏数据

---

## 1. 问题现象

### 1.1 图标重启后消失

执行 `./stop-dev.sh && ./start-dev.sh`（删卷重建容器）后：
- 业务管理图标从 `shopping` 回退为 `chart`
- 合同管理图标从 `list` 回退为 `document`
- 仪表盘路径从 `cockpit/dashboard` 回退为 `dashboard/dashboard`
- 渠道管理跑到业务管理外面（parent_id=0 而非 5）

### 1.2 menu_id=8 争用导致审批中心消失

`biz_menus_roles_init.sql`（脚本03）和 `approval_init.sql`（脚本05）都使用 `INSERT IGNORE INTO sys_menu ... menu_id=8`，但含义不同：
- 脚本03：`menu_id=8` = 渠道管理（parent_id=0，顶级）
- 脚本05：`menu_id=8` = 审批中心（parent_id=5，业务管理子菜单）

两处 INSERT IGNORE 竞争同一主键，MySQL 执行顺序由 docker-entrypoint-initdb.d 文件名字母序决定：
- `03-biz-menus-roles.sql` 先跑 → menu_id=8 = 渠道管理（parent_id=0）
- `05-approval-init.sql` 后跑 → INSERT IGNORE 跳过（menu_id=8 已存在）
- **结果**：审批中心没有插入，渠道管理跑到外面

---

## 2. 根因分析

### 2.1 错误的修改路径

```
错误路径：
1. 通过前端菜单管理 UI → API → 修改 sys_menu.icon
2. 期望改完就生效
3. ./stop-dev.sh && ./start-dev.sh
4. 删卷 → MySQL 数据全清
5. docker-entrypoint-initdb.d 按顺序重跑 SQL 脚本
6. SQL 里是老图标 → 覆盖了 API 修改 → 图标回退
```

```
正确路径（唯一）：
1. 直接修改 SQL 脚本中的图标值
2. ./stop-dev.sh && ./start-dev.sh
3. 删卷重建
4. SQL 里是新图标 → 正确生效
```

### 2.2 SQL 脚本间 icon 脏数据

`ruoyi-fastapi.sql`（基础脚本，行166-167）：
```sql
-- 旧值（脏数据）
insert into sys_menu values('5', '业务管理', ..., 'chart',      ...);  -- ← 应为 shopping
insert into sys_menu values('6', '合同管理', ..., 'document',   ...);  -- ← 应为 list
```

`biz_menus_roles_init.sql`（业务脚本）虽然有 UPDATE 修正，但基础脚本的脏数据先执行：

| 脚本 | 业务管理 icon | 合同管理 icon |
|---|---|---|
| `ruoyi-fastapi.sql`（基础，先跑） | `chart` | `document` |
| `biz_menus_roles_init.sql`（业务，后跑） | `shopping`（UPDATE 修正） | `list`（UPDATE 修正） |

UPDATE 确实会覆盖基础 INSERT，但这种「先写脏数据再 UPDATE 修正」的模式本身是脆弱的——只要漏写一条 UPDATE，脏数据就会进入 DB。

### 2.3 INSERT IGNORE + DELETE 模式的幂等性陷阱

旧版 `biz_menus_roles_init.sql` 使用「DELETE 后重新 INSERT」修正菜单：

```sql
-- 旧模式（有危险）
DELETE FROM sys_role_menu WHERE menu_id BETWEEN 9 AND 11;  -- ← 误伤：历史库中可能这些 ID 有其他含义
DELETE FROM sys_menu WHERE menu_id BETWEEN 9 AND 11;
INSERT IGNORE INTO sys_menu (menu_id, ...) VALUES (12, '渠道管理', 0, ...);  -- ← 旧 parent_id=0 又写进去了
```

此模式的三个问题：
1. **DELETE 破坏历史数据**：历史库中 menu_id=9-11 可能有其他含义，DELETE 会删除 sys_role_menu 中的合法映射
2. **INSERT IGNORE 无法修正已存在的行**：如果 menu_id=12 已存在（哪怕字段错误），INSERT IGNORE 跳过，不会修正
3. **DELETE 9-11 漏了 8**：menu_id=8 被两处脚本争用，但 DELETE 9-11 范围不包括 8，遗留脏数据

---

## 3. 修复方案

### 3.1 图标持久化：只改 SQL，不改 API

**原则**：`sys_menu.icon` 的唯一修改入口是 SQL 初始化脚本。

运维流程：
```
1. 修改 SQL 脚本中的 icon 字段
2. ./stop-dev.sh && ./start-dev.sh
3. 验证生效
```

不再通过 API（PUT /system/menu）改菜单配置。如需运行时调优，调完后再把变更同步回 SQL 脚本（作为开发行为，非运维行为）。

### 3.2 修正 SQL 脚本脏数据

直接修改 `ruoyi-fastapi.sql` 中的图标值，而非依赖后续 UPDATE：

```sql
-- ruoyi-fastapi.sql（修正后）
insert into sys_menu values('5', '业务管理', '0', '5', 'biz', null, ...,
    'shopping',   -- ← 直接修正，不再脏
    'admin', sysdate(), ...);
insert into sys_menu values('6', '合同管理', '5',  '1', 'contract', 'biz/contract/index', ...,
    'list',       -- ← 直接修正
    'admin', sysdate(), ...);
```

### 3.3 弃用 DELETE+INSERT，改用 UPDATE 幂等模式

旧版（有危险）：
```sql
DELETE FROM sys_menu WHERE menu_id BETWEEN 9 AND 11;
INSERT IGNORE INTO sys_menu (menu_id, ...) VALUES (12, '渠道管理', 0, ...);  -- parent_id=0 危险
```

新版（幂等安全）：
```sql
-- 只 UPDATE，不 DELETE
UPDATE sys_menu
   SET parent_id = 5,
       icon = 'link',
       path = 'biz/channel',
       perms = 'channel:list,channel:add,channel:edit,channel:delete,channel:import',
       component = 'biz/channel/index'
 WHERE menu_id = 12
   AND (parent_id != 5 OR icon != 'link' OR path != 'biz/channel');
```

### 3.4 消除 menu_id 争用：确认唯一性

所有 SQL 脚本按「占位 + 修正」模式设计：

```
1. approval_init.sql 先 INSERT menu_id=8（审批中心，parent_id=5）← 后跑会覆盖其他脚本的 8
2. biz_menus_roles_init.sql 用 UPDATE 修正 menu_id=12（渠道管理），不再占用 8
```

---

## 4. 修复文件清单

| 文件 | 修复内容 |
|---|---|
| `sql/ruoyi-fastapi.sql` 行166-167 | `chart` → `shopping`；`document` → `list` |
| `sql/biz_menus_roles_init.sql`（全文） | 重构为 UPDATE 幂等模式，消除 menu_id=8 争用，图标全持久化 |
| `sql/biz_menus_roles_init.sql` 行183 | `dashboard/dashboard` → `cockpit/dashboard` |
| `src/router/index.js` | 动态路由图标与 SQL 同步 |
| 运行中 DB（menu_id=13） | component → `cockpit/dashboard` |

---

## 5. 同类风险防范规则

### 规则 1：菜单配置只从 SQL 读取
- **禁止**：通过 API（PUT /system/menu）持久化菜单配置
- **例外**：运行时临时调优（不改 SQL，只临时验证）
- **完成后**：必须把变更同步回 SQL 脚本

### 规则 2：SQL 脚本图标值必须与 router/index.js 一致
- 新增菜单时，同时在三个地方写图标：
  1. `ruoyi-fastapi.sql`（基础 INSERT）
  2. `biz_menus_roles_init.sql`（UPDATE 修正）
  3. `src/router/index.js`（前端 fallback）

### 规则 3：menu_id 唯一性登记
- 所有菜单 ID 在 `docs/03-设计/数据库设计.md` 或 SQL 脚本头部注释登记
- 新增菜单必须申请新的 menu_id，不得复用
- 禁止两个 INSERT 争用同一 menu_id（改用 UPDATE 修正）

### 规则 4：弃用 DELETE+INSERT 修正模式
- 用 `INSERT IGNORE` + 后续 `UPDATE` 替代 `DELETE` + `INSERT`
- DELETE 只用于清理明确的脏数据，不用于「重新创建」

### 规则 5：删卷重建前必须确认 SQL 最新
- `./stop-dev.sh && ./start-dev.sh` 前检查 SQL 脚本是否包含最新变更
- 如果只用 API 改了 DB，必须先把变更写入 SQL，再删卷重建

---

## 6. 当前菜单结构（v4.0）

```
menu_id=5  业务管理   parent_id=0   icon=shopping
  menu_id=6  合同管理   parent_id=5   icon=list
  menu_id=7  客户档案   parent_id=5   icon=peoples
  menu_id=8  审批中心   parent_id=5   icon=clipboard
  menu_id=12 渠道管理   parent_id=5   icon=link
  menu_id=14 发票管理   parent_id=5   icon=pdf
  menu_id=15 财务管理   parent_id=5   icon=money
  menu_id=16 经营数据   parent_id=5   icon=chart
menu_id=13 仪表盘      parent_id=0   icon=dashboard   component=cockpit/dashboard
```

---

## 7. 关联决策

- **ADR D08**：菜单父子关系规范（parent_id=5 为业务管理目录）
- **ADR D01**：权限模型设计
- **ADR D02**：role_sort 规范
