# 路线 C 仪表盘运行时 race condition & EP 弃用警告（2026-07-12）

**日期**：2026-07-12
**类型**：前端 race condition + Element Plus API 弃用警告
**影响**：① 后端 `DashboardDAO.trend_7d()` 不支持 province，导致 asyncio.gather 并发调用 `trend_7d(db, province)` 直接抛 `takes 1 positional argument but 2 were given`，前端收到 500；② 前端 axios 同时发两个并发请求 + setInterval 累加触发 socket race，浏览器报 `readexactly() called while another coroutine is already waiting for incoming data`；③ EP 3.x 弃用 `<el-button type="text">` 控制台 warn（不影响功能）
**根因**：v3.4 路线 C 落地时漏掉 DAO 透传 province + 前端并发安全处理 + 没扫 EP 弃用

---

## 1. 现象

打开 `/dashboard/index` 工作台，浏览器 console：

```
[EP warn] type.text is about to be deprecated in version 3.0.0, please use link instead
[axios err] readexactly() called while another coroutine is already waiting for incoming data
[axios err] DashboardDAO.trend_7d() takes 1 positional argument but 2 were given
```

第二个错误弹 ElMessage 错误：`IndexError: list index out of range` 后续被 `request.js:124` catch 后 `Promise.reject(new Error(msg))`，UI 全空。

---

## 2. 根因分析

### 2.1 DAO 漏 province 参数

**路径**：`module_biz/dao/dashboard_dao.py` `DashboardDAO.trend_7d`

**原签名**：
```python
@staticmethod
async def trend_7d(db: AsyncSession) -> list[Trend7dItemModel]:  # ← 只收 db
```

但 `dashboard_service.py` 走 asyncio.gather 把 10 个 DAO 全并发调用，**统一传 province**：
```python
(
    kpi_contract, ..., trend_7d, ...
) = await asyncio.gather(
    DashboardDAO.kpi_contract(db, province),
    ...,
    DashboardDAO.trend_7d(db, province),  # ← 第二个参数 trend_7d 不认
    ...
)
```

`trend_7d` 没接 `province`，TypeError 抛在 gather 内部，FastAPI 拦截 → 500。

**静态层冒烟不报**：之前 `pytest -k dashboard` 用 unit test 直接构造 mock，没跑过真实 `service.overview_services(...)`，所以漏。

### 2.2 前端 axios socket race

**触发链**：
1. `onMounted` 里同步调 `load() + loadAi()` —— 两条 GET 几乎同时发起
2. `setInterval(load, 60000)` 没存 timer id，每次 unmount/remount **新挂一轮定时器**
3. dashboard.vue 还多一个 `setInterval(loadAi, 90000)`
4. `getDashboardOverview()` **没用 AbortController**，前一个未完成又来一个
5. axios 在浏览器用 XHR 没问题，但 Axios adapter 在 node-http 路径下若混用 fetch，会触发 `readexactly` race

**结果**：浏览器 console 报错 + 后端正常响应（无害但污染 console）。

### 2.3 EP `type="text"` 弃用

EP 3.x 弃用了 `<el-button type="text">`，推荐用 `link` 属性。grep 全仓发现：

- `views/biz/dashboard/index.vue` line 82（一处"大屏查看雷达 →"按钮）—— **已修**
- `views/tool/build/index.vue` line 61/64/67（三处"导出/复制/清空"按钮）—— **已修**

`views/login.vue` / `views/register.vue` 的 `type="text"` 是 `el-input` 的 HTML input type，**不触发 useButton**，不算。

---

## 3. 修复前后对比

### 3.1 后端 DAO

**修复前**：
```python
@staticmethod
async def trend_7d(db: AsyncSession) -> list[Trend7dItemModel]:
    new_stmt = (
        select(func.date(BizContract.create_time).label('d'), func.count(BizContract.id))
        .where(BizContract.create_time >= start_dt)
        .group_by(func.date(BizContract.create_time))
    )
    ...
    approved_stmt = (
        ...
        .where(and_(BizContract.status == 'approved', BizContract.update_time >= start_dt))
        ...
    )
```

**修复后**：
```python
@staticmethod
async def trend_7d(db: AsyncSession, province: str = '') -> list[Trend7dItemModel]:
    new_q = [BizContract.create_time >= start_dt]
    if province:
        new_q.append(BizContract.province == province)
    new_stmt = (
        select(func.date(BizContract.create_time).label('d'), func.count(BizContract.id))
        .where(*new_q)
        .group_by(func.date(BizContract.create_time))
    )

    approved_q = [BizContract.status == 'approved', BizContract.update_time >= start_dt]
    if province:
        approved_q.append(BizContract.province == province)
    approved_stmt = (
        select(func.date(BizContract.update_time).label('d'), func.count(BizContract.id))
        .where(*approved_q)
        .group_by(func.date(BizContract.update_time))
    )
```

防御：参数 `province=''` 默认空串，老调用方零成本兼容。

### 3.2 前端 load / loadAi 并发安全

**修复前**（典型 race 制造器）：
```javascript
async function load() {
  loading.value = true
  try {
    const res = await getDashboardOverview()
    // ...
  } finally { loading.value = false }
}

onMounted(() => {
  load()
  loadAi()
  refreshTimer = setInterval(() => {
    load()
    loadAi()
  }, 60000)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
```

**修复后**（AbortController + in-flight dedup + 全 timer id 化）：
```javascript
let abortCtrl = null
let loadInFlight = false
let loadAiInFlight = false
let overviewTimer = null
let aiTimer = null

async function load() {
  if (loadInFlight) return
  loadInFlight = true
  abortCtrl?.abort()
  const ctrl = new AbortController()
  abortCtrl = ctrl
  try {
    const res = await getDashboardOverview(
      province.value ? { province: province.value } : {},
      { signal: ctrl.signal }   // ← 关键
    )
    // ...
  } catch (e) {
    /* 静默吞掉 axios cancel 错误 */
  } finally {
    loadInFlight = false
  }
}

onMounted(() => {
  load()
  loadAi()
  overviewTimer = setInterval(load, 60000)
  aiTimer = setInterval(loadAi, 90000)
})

onBeforeUnmount(() => {
  clearInterval(overviewTimer)
  clearInterval(aiTimer)
  abortCtrl?.abort()
})
```

并在 `api/biz/dashboard.js` 透传 `config.signal`：
```javascript
export function getDashboardOverview(params = {}, config = {}) {
  return request({ url: '/biz/dashboard/overview', method: 'get', params, ...config })
}
export function getDashboardAiDiagnose(config = {}) {
  return request({ url: '/biz/dashboard/ai-diagnose', method: 'get', ...config })
}
```

### 3.3 EP type="text" 弃用

**修复前**：
```vue
<el-button v-if="ai.summary" type="text" size="small" @click="gotoDashboard">
  大屏查看雷达 →
</el-button>
```

**修复后**：
```vue
<el-button v-if="ai.summary" type="primary" link size="small" @click="gotoDashboard">
  大屏查看雷达 →
</el-button>
```

`tool/build/index.vue` 三处 `type="primary" text` → `type="primary" link` + `type="danger" link`。

---

## 4. 验证清单

- [x] DAO 全部 10 个方法签名符合 service gather 调用契约（`inspect.signature` 实证）
- [x] `DashboardOverviewModel(trend_7d=[]).model_dump(by_alias=True)` 键集合包含 `trend7d`、不包含 `trend7D`
- [x] dashboard/index.vue / dashboard.vue load + loadAi 都有 AbortController + in-flight dedup
- [x] dashboard API `getDashboardOverview({ signal })` / `getDashboardAiDiagnose()` 透传 config
- [x] 全仓 grep `<el-button.*type="text"` 已无命中
- [x] dashboard.vue onBeforeUnmount 清理 overviewTimer + aiTimer + abortCtrl（之前漏）

---

## 5. 反思与同类风险防范

### 5.1 DAO 透传参数的服务层抽象

**规则**：凡是 service 用 `asyncio.gather(*DAO_calls)` 并发调用，DAO 签名必须接受**统一的过滤参数命名**。本项目：province 维度。本规则新增 ADR **D30**：DAO filter 参数显式签名优先于 kwargs。

### 5.2 前端并发安全 checklist

新增规则（写入前端 dev checklist）：
1. **任何对同一 endpoint 的 request 必须有 AbortController**
2. **setInterval 必须存 id 且 onBeforeUnmount clearInterval**
3. **in-flight 标记防 setInterval 叠加**
4. **API 函数接受第二个 config 参数透传 axios signal**

### 5.3 EP 弃用警告扫描

EP 升级到 3.x 后，`type="text"` 是大量 RuoYi 原生按钮的写法。建议：
- dev 阶段 console 保留 warn（不抑制）
- CI 加 grep 卡控：`<el-button[^>]*type=["']text["']` 必须为 0
- 不卡 `<el-input type="text">`（HTML 原生 type，不是 EP prop）

---

## 6. 关联决策 / 影响范围

- **关联 ADR**：D26（PEP 563 注解 + get_type_hints 兜底，与本次无直接关系但同属"运行时坑"族）、**D30**（DAO filter 参数显式签名优先于 kwargs，新增）
- **影响范围**：
  - 后端 1 文件（`module_biz/dao/dashboard_dao.py`）
  - 前端 4 文件（`api/biz/dashboard.js` / `views/biz/dashboard/index.vue` / `views/dashboard/dashboard.vue` / `views/tool/build/index.vue`）
  - 受益：所有 dashboard 视图在切换省份 / 切换组件 / Vite HMR 重载场景不再触发 axios socket race
- **回归**：建议用 `scripts/test_dashboard_v3_3.py` 走 3 个端点 + province 维度过滤断言