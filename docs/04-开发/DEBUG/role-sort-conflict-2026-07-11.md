# sys_role.role_sort 冲突：admin / common 与 7 级审批链角色 sort 重复

**日期**：2026-07-11
**类型**：数据建模 ADR 违规 / 审批链前置依赖
**影响**：任何拥有 admin 或 common 角色的用户会被误识别为业务经办/复核
**根因**：RuoYi 原生 init 把 admin/common sort 都设成了 1/2，与本项目 7 级审批链角色 sort 区间冲突

---

## 1. 现象

执行「审批链路 / 待我审批」SQL 时（如 pending-list 设计逻辑）：

```sql
-- 设计文档 §5.1 期望的查询（伪 SQL）
SELECT DISTINCT c.*
FROM biz_contract c
JOIN sys_user_role ur ON ur.user_id = :current_user_id
JOIN sys_role r ON r.role_id = ur.role_id
WHERE c.status = 'pending'
  AND c.current_step + 1 = r.role_sort  -- 关键判断
```

实测：`current_user=admin（user_id=1）` 时，admin 用户**同时拥有 8 个角色**（admin + 7 级业务审批角色），按 `role_sort=1` 会**误判为业务经办**（sort=1）→ 任何 admin 用户提交合同后立刻被自己识别为「待我审批」。

`current_user=niangao（user_id=2）` 时，niangao 只有 `common` 角色（sort=2）→ 会被**误判为业务复核**（sort=2）。

## 2. 修复前后对比

### 修复前（违规）

| role_id | role_name | role_key | role_sort | 设计要求 |
|---|---|---|---|---|
| 1 | 超级管理员 | admin | **1** | **0**（隐藏超管）|
| 2 | 普通角色 | common | **2** | **>7 或 NULL**（非审批角色）|
| 3 | 业务经办 | business_handler | 1 | 1 |
| 4 | 业务复核 | business_reviewer | 2 | 2 |

### 修复后（合规）

| role_id | role_name | role_key | role_sort |
|---|---|---|---|
| 1 | 超级管理员 | admin | **0** |
| 3 | 业务经办 | business_handler | 1 |
| 4 | 业务复核 | business_reviewer | 2 |
| 5 | 风控审核 | risk_auditor | 3 |
| 6 | 财务经办 | finance_handler | 4 |
| 7 | 财务复核 | finance_reviewer | 5 |
| 8 | 供管公司负责人 | scm_director | 6 |
| 9 | 投资公司负责人 | invest_director | 7 |
| 2 | 普通角色 | common | **99** |

## 3. 根因分析

### 3.1 RuoYi 原生 init（sql/ruoyi-fastapi.sql:126）

```sql
insert into sys_role values('1', '超级管理员',  'admin',  1, ...);  -- 默认 sort=1
insert into sys_role values('2', '普通角色',    'common', 2, ...);  -- 默认 sort=2
```

RuoYi 用 `role_sort` 表达「显示顺序」，所以默认 sort=1/2 没问题。但**本项目把 `role_sort` 复用为「审批链位置」**（参考设计文档 §3.3 与 ADR D02），导致 RuoYi 默认值与本项目语义冲突。

### 3.2 biz_menus_roles_init.sql 注释 vs 实际

```sql
-- 注释（第 32 行）：
-- 注意：admin 已存在（role_id=1），role_sort=0 标记为隐藏超管
-- 实际：脚本里没有任何 UPDATE sys_role SET role_sort = 0 WHERE role_id = 1
```

脚本作者意识到了问题，写在注释里，但**没真的写 SQL**。属于典型的「注释与代码不一致」遗留 bug。

## 4. 修复执行

### 4.1 立刻修当前运行的 DB

```bash
docker exec ruoyi-mysql mysql -uroot -proot -e "
USE ruoyi-fastapi;
UPDATE sys_role SET role_sort = 0  WHERE role_id = 1;
UPDATE sys_role SET role_sort = 99 WHERE role_id = 2;
"
```

实测返回：

```
role_id  role_name    role_sort
1        超级管理员   0
3        业务经办     1
4        业务复核     2
...（按设计文档 §5.1 顺序）
2        普通角色     99
```

### 4.2 同步更新 SQL 脚本（biz_menus_roles_init.sql §0 节）

新增节：

```sql
-- =====================================================================
-- 0. 修正 admin / common 的 role_sort（修复 ADR D02 违规）
-- =====================================================================
UPDATE sys_role SET role_sort = 0  WHERE role_id = 1;
UPDATE sys_role SET role_sort = 99 WHERE role_id = 2;
```

这样下次 `docker compose down -v && up` 重建容器时，新的 SQL 挂载会自动跑这条 UPDATE。

### 4.3 同步更新 ADR D02 约束补充段

D02「实现方式」后追加：

> **约束补充（2026-07-11）**：`sys_role.role_sort` 取值规范 —— `0` = 隐藏超管、`1-7` = 7 级业务审批链、`>7` 或 `NULL` = 非审批角色（约定用 `99`）。任何审批人匹配逻辑必须先排除 `role_sort NOT IN (1..7)`，再判断 `role_sort == current_step + 1`。

## 5. 为什么当前应用层没暴露 bug

- `contract_service.submit_services` 推进 step 时不查 role_sort，只看 `current_step` 数值
- `/biz/approval/*` 接口（pending-list / approve / reject / history）**还没建**（台账 §3.1 编号 2.3 / 2.6）
- 当前 admin 的 `user_id=1` 硬编码绕过（`UserModel.check_admin` 走 `user_id == 1`），所以前端 `isSuperuser` 标志不依赖 role_sort

**但**一旦开始实现 pending-list，会**立刻踩坑** —— admin 用户提交合同后立刻在「待我审批」看到自己提交的合同，体验和权限模型严重不符。

## 6. 验收 / 复现命令

```bash
# 验收当前状态
docker exec ruoyi-mysql mysql -uroot -proot -t -e "
USE ruoyi-fastapi;
SELECT role_id, role_name, role_key, role_sort
FROM sys_role
ORDER BY role_sort, role_id;
"

# 期望：admin=0、common=99、其余 1-7 严格按设计顺序，无重复 sort
```

## 7. 后续启示

- **D24 类全局约定落地时，必须把 SQL init 脚本也同步改**：本次是 ADR D02 落地不彻底，下次做 ADR D03（rejected 状态语义）扩展时也要检查 SQL 与 Python 同步
- **不要把 RuoYi 的「显示顺序」字段（role_sort）复用为业务语义字段**，会与 RuoYi 默认值冲突；或者复用时必须显式修正默认值
- **审批人匹配逻辑的安全约束**：必须 `role_sort IN (1..7)` 先过滤，再判断 == current_step+1；admin 走 bypass 分支独立处理

---

**关联文件**：
- `ruoyi-fastapi-backend/sql/biz_menus_roles_init.sql` — §0 节修复
- `ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql:126` — RuoYi 原生 admin 默认 sort=1（root cause）
- `docs/04-开发/ARD/ADR-架构决策记录.md` — D02「约束补充」段
- `docs/04-开发/开发进度台账.md` — v2.7 变更记录