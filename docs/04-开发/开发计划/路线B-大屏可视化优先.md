# 路线 B 大屏可视化优先（v3.0 完成报告）

> 文档版本：v2.0（完成报告）
> 原始创建：2026-07-11 23:00（按"待开发"假设撰写）
> 现实更新：2026-07-12 00:15（按 commit `d8dd5bc` 实际成果重写）
> 文档定位：路线 B 「仪表盘大屏」+ 「可视化通用组件」**真实交付清单**。

---

## 一、交付概要

| 维度 | 数据 |
|------|------|
| Commit hash | `d8dd5bc` |
| Commit 标题 | `feat(module_biz): 仪表盘大屏（路线 B）` |
| 新增文件 | **后端 4 + 前端 5 = 9 个**（含 route_sql/无 SQL/无主题样式覆写） |
| 菜单 | menu_id=13（仪表盘），路径 `/dashboard/index`，**顶级路由不是 /biz/dashboard** |
| 工作量 | 1 个会话内完成 |

---

## 二、与初始假设关键差异（务必看）

| 维度 | 初始假设 | 现实 |
|------|---------|------|
| **dashboard 路由位置** | `/biz/dashboard` | **`/dashboard/index`**（顶级路由，与其他 7 个 /biz/* 不同） |
| **dashboard 路由** | 需新建覆盖 RuoYi 原生 | **未改**，沿用 RuoYi 原生 `dashboard/index.vue` 17KB |
| **profile 路由** | 需新建 | **未改**，RuoYi 原生 `system/user/profile/*` 已存在并增强 signature 画板 |
| **system/user 路由** | 需新建 | **未改**，RuoYi 原生 `system/user/index.vue` 在用 |
| **可视化组件路径** | `components/Biz/{BaseChart,CountTo,ScreenMap}.vue` | **完全一致** ✅ |
| **dashboard 后端 do/vo** | 路线 B 不需要 | **vo 存在**（dashboard_vo.py），do **不存在**（聚合查询不写库）|
| **数据源** | 读已完成的合同/审批/客户表 | 一致，并且额外读路线 A 的 channel/invoice/finance/operation 表做 KPI |
| **科技蓝主题样式** | 路线 B 要做 | **未做**（用户明确「先不要管科技风主题样式覆写」） |

---

## 三、详细交付清单

### 3.1 后端（4 文件）

| 文件 | 行数 | 内容 |
|------|------|------|
| `module_biz/controller/dashboard_controller.py` | **1690 字节** | 1 个聚合 endpoint：`GET /biz/dashboard/overview` |
| `module_biz/service/dashboard_service.py` | **4038 字节** | 业务聚合 + 简单缓存（60s TTL） |
| `module_biz/dao/dashboard_dao.py` | **13471 字节** | **最大文件**：6 个聚合查询（合同总数/状态分布/7 日趋势/Top10 客户/审批流/营收） |
| `module_biz/entity/vo/dashboard_vo.py` | **5617 字节** | Pydantic VO：KPI / Trend7D / StatusDist / TopCustomer / RecentApproval |
| `module_biz/entity/do/dashboard_do.py` | ❌ **不存在** | 聚合查询不写库，不需要 ORM 模型 |

**自动注册**：与路线 A 一致，由 `common/router.py auto_register_routers` 自动扫描 controller/ 注册。

### 3.2 前端可视化通用组件（3 文件）

| 组件 | 行数 | 来源 | 关键能力 |
|------|------|------|---------|
| `src/components/Biz/BaseChart.vue` | **183** | 原创 | ECharts 通用封装，支持 bar/line/pie/radar 4 种图表类型 |
| `src/components/Biz/CountTo.vue` | **77** | 参考 v1 demo 1/frontend/src/components/screen/CountTo.vue (62 行) | 数字翻牌动画（requestAnimationFrame + easeOutCubic） |
| `src/components/Biz/ScreenMap.vue` | **210** | 参考 v1 demo 1/frontend/src/components/screen/ScreenMap.vue | 中国地图 + 涟漪散点（effectScatter + ECharts.registerMap） |

**被引用**：
- `src/views/biz/dashboard/index.vue` 一次性 import 了 3 个组件（`grep import '@/components/Biz' src/` 唯一引用方）

**中国地图 JSON**：
- 路线 B 没引入 `src/assets/map/china.json` 物理文件，但代码里有 ECharts 内置 `china` 注册。**这点待 E2E 启动时验证**（如果没有 china.json，可能 runtime 报错）。

### 3.3 仪表盘主页（1 文件）

| 文件 | 行数 | 内容 |
|------|------|------|
| `src/views/biz/dashboard/index.vue` | **331** | 暗色科技风大屏页面 |
| `src/api/biz/dashboard.js` | **320 字节** | 1 个 API 函数 `getDashboardOverview` |

**页面布局**（与 v1 demo 的 `DataScreen.vue` 326 行属同一风格）：
- 顶部：6 个 KPI 数字翻牌（合同总数 / 审批中 / 已通过 / 客户数 / 渠道数 / 本月营收）
- 第 2 行：7 日趋势（line）+ 合同状态分布（pie）
- 中部：中国地图（screen-map）
- 底部：Top10 客户（bar）+ 最近审批流（el-timeline）

**主题色**：暗色 `background: #0a1a3a`，卡片 `rgba(0, 30, 80, 0.6)`，边框 `#00f2ff`，数字翻牌渐变 `linear-gradient(180deg, #fff 0%, #00f2ff 100%)`。

### 3.4 路由（1 个）

```javascript
// src/router/index.js
{
  path: '/dashboard',                  // 顶级路由，不在 /biz 下
  component: Layout,
  permissions: ['biz:dashboard:view'],
  children: [{
    path: 'index',
    component: () => import('@/views/biz/dashboard/index.vue'),
    name: 'BizDashboard',
    meta: { title: '仪表盘', icon: 'pie-chart', noCache: false }
  }]
}
```

### 3.5 dashboard / profile / system（**未动**）

| 项目 | 状态 |
|------|------|
| `src/views/dashboard/index.vue` | RuoYi 原生 17KB，沿用 |
| `src/views/system/user/profile/*` | RuoYi 原生，v2.9 阶段增强了 signature 画板 |
| `src/views/system/user/index.vue` | RuoYi 原生，沿用 |

---

## 四、菜单 SQL（共用文件的一部分）

`sql/biz_menus_roles_init.sql` § 路线 B 段（commit `8eab8f0` 之后但路线 B commit `d8dd5bc` 之前已经写好菜单）：

```sql
-- 路线 B：仪表盘菜单（menu_id=13，v3.6 改名，原「仪表盘」+ 路径 dashboard 化）
-- 注：以下 SQL 仅保留作为历史样例（叙述路线 B v3.0 当时实现），实际部署请用：
--   ruoyi-fastapi-backend/sql/biz_menus_roles_init.sql
INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES (13, '仪表盘', 0, 13, '/dashboard', 'dashboard/dashboard', 1, 0, 'C', '0', '0', 'biz:dashboard:view', 'pie-chart', 'admin', NOW(), 'v3.6 改名 + 路径 dashboard 化');
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 13);
```

**注意**（v3.6 改名后）：
- `menu_name='仪表盘'`（v3.6 前是「仪表盘」）
- `path='/dashboard'`（v3.6 前是 `dashboard`，顶级而非 `/biz/*`）
- `component='dashboard/dashboard'`（v3.6 前是 `biz/dashboard/index`）
- `perms='biz:dashboard:view'` 保留（避免破坏角色权限矩阵；perm 标识符在历史里就叫这个）

---

## 五、关键风险 / 注意事项

### 5.1 中国地图 JSON 来源未明

代码里 `echarts.registerMap('china', chinaMapJson)` 需要 `chinaMapJson`：

- v1 demo 是否有 `1/frontend/src/assets/map/china.json` 200KB JSON？需要查
- 如果没有，可能 runtime 报错：地图显示不出来但其他 5 个 KPI 都正常
- 备选方案：从 `https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json` 下载

### 5.2 dashboard/profile/system 三个原生页面与业务页视觉风格不一致

- RuoYi 原生 dashboard 17KB 是经典 Element Plus 后台风格
- 业务页（approval/contract/customer/4-CRUD/dashboard）都已经在 v2.9 / v3.0 做了暗色模式适配（D25）
- **视觉一致性缺口**：用户登录后从 `/index` 跳 `/dashboard`（RuoYi 风），点「业务管理」跳 `/biz/approval`（暗色风），**反差明显**

### 5.3 主题样式覆写未做

- 用户明确「先不要管科技风主题样式覆写」
- 这意味着 dashboard 这套暗色科技风**只活在自己页面内**，没有全局 `--el-*` 变量覆写
- 一旦未来要求全站切换，dashboard 会和全站主流视觉脱节

---

## 六、关联文档

- [路线总览（v3.0/v3.1 完成报告）](./00-并行开发路线总览.md)
- [路线 A 完成报告](./路线A-业务闭环优先.md)
- [开发进度台账 v2.9 / v3.0 条目](../../开发进度台账.md)
- [ADR D13 / D25](../../ARD/ADR-架构决策记录.md)
- 原始「操作手册」草稿（归档作参考）：[操作手册-双窗口并行.md](./操作手册-双窗口并行.md)
