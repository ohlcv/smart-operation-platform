# 路线 B：大屏可视化优先（详细方案）

> 文档版本：v1.0
> 创建日期：2026-07-11
> 文档定位：以"战略驾驶舱"为核心，3 个可视化通用组件 + 1 个聚合大屏页面 + dashboard + profile + system，**视觉冲击力拉满**。文件互斥，与路线 A 完全无重叠。

---

## 一、目标与价值

**业务目标**：让项目在打开的瞬间就有"产品感"——中国地图 + 数字翻牌 + ECharts 图表 + 暗色科技风背景。**适合给领导/客户演示**。

**演示场景**：领导、外部客户、外部访客。

**总工作量**：50h（后端 6h + 前端 44h）

**预计完成**：1 周

---

## 二、文件清单（路线 B 独占）

### 2.1 后端文件（3 个新增）

#### cockpit 战略驾驶舱（6h 后端）

| # | 文件 | 行数 | 工作量 | 内容 |
|---|------|------|--------|------|
| B-2.1.1 | `module_biz/dao/cockpit_dao.py` | 200 | 2h | 6 个聚合查询（读已完成模块的表） |
| B-2.1.2 | `module_biz/service/cockpit_service.py` | 250 | 3h | 业务聚合 + 简单缓存（60s） |
| B-2.1.3 | `module_biz/controller/cockpit_controller.py` | 80 | 1h | 1 个 endpoint |

**数据源（只读，不写）**：
- `biz_contract` 表 → 合同总数、各状态分布、7 日趋势、本月新增
- `biz_customer` 表 → 客户总数、Top10 客户
- `biz_approval` 表 → 审批中数量、最近审批流
- `module_admin.sys_user` 表 → 用户总数
- 路线 A 完成的 channel/invoice/finance/operation 表（如果已完成）

**Endpoint 清单**：
```
GET /biz/cockpit/overview    返回完整驾驶舱数据
GET /biz/cockpit/realtime    SSE 实时推送（可选，2.0 再做）
```

**返回数据结构**：
```json
{
  "kpi": {
    "contractTotal": 1234,
    "contractPending": 23,
    "contractApproved": 1156,
    "customerTotal": 89,
    "channelTotal": 12,
    "monthRevenue": 5678901.23
  },
  "trend7d": [
    { "date": "2026-07-05", "newContracts": 5, "approved": 3 },
    ...
  ],
  "statusDistribution": [
    { "status": "draft", "count": 12 },
    { "status": "pending", "count": 23 },
    { "status": "approved", "count": 1156 },
    { "status": "rejected", "count": 43 }
  ],
  "topCustomers": [
    { "customerId": 1, "customerName": "山东出版集团", "contractCount": 8, "totalAmount": 1234567.89 },
    ...
  ],
  "recentApprovals": [
    { "contractId": 100, "contractNo": "HT-2026-001", "step": 3, "approverName": "张三", "time": "2026-07-11 14:23:00" },
    ...
  ]
}
```

### 2.2 前端通用组件（3 个新增）

| # | 文件 | 行数 | 工作量 | 来源 |
|---|------|------|--------|------|
| B-2.2.1 | `src/components/Biz/BaseChart.vue` | 200 | 4h | 新建（ECharts 通用封装） |
| B-2.2.2 | `src/components/Biz/CountTo.vue` | 80 | 1.5h | 从 v1 demo `1/frontend/src/components/screen/CountTo.vue` (62 行) 迁移 + 增强 |
| B-2.2.3 | `src/components/Biz/ScreenMap.vue` | 150 | 3h | 从 v1 demo `1/frontend/src/components/screen/ScreenMap.vue` (124 行) 迁移 |

#### BaseChart.vue（4h）

**用途**：ECharts 通用封装，支持 4 种图表类型。

```vue
<template>
  <div ref="chartRef" class="base-chart" :style="{ width, height }"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // 图表类型：bar/line/pie/radar
  type: { type: String, default: 'bar' },
  // 数据
  data: { type: Array, required: true },
  // X 轴类目（柱状/折线）
  categories: { type: Array, default: () => [] },
  // 配置
  option: { type: Object, default: () => ({}) },
  width: { type: String, default: '100%' },
  height: { type: String, default: '300px' }
})

const chartRef = ref(null)
let chartInstance = null

function init() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  render()
}

function render() {
  if (!chartInstance) return
  const baseOption = buildOption()
  chartInstance.setOption({ ...baseOption, ...props.option }, true)
}

function buildOption() {
  // 根据 type 返回对应基础配置
  // 全部使用科技风主题色（暗色背景）
  const techColors = ['#00f2ff', '#00d4ff', '#0099ff', '#7c4dff', '#ff4081']
  switch (props.type) {
    case 'bar':
      return {
        grid: { left: 40, right: 20, top: 30, bottom: 30 },
        xAxis: { type: 'category', data: props.categories, axisLine: { lineStyle: { color: '#4a6584' } }, axisLabel: { color: '#a0c4ff' } },
        yAxis: { type: 'value', axisLine: { lineStyle: { color: '#4a6584' } }, axisLabel: { color: '#a0c4ff' }, splitLine: { lineStyle: { color: 'rgba(74, 101, 132, 0.2)' } } },
        series: [{ type: 'bar', data: props.data, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#00f2ff' }, { offset: 1, color: '#0099ff' }] } } }]
      }
    case 'line':
      return { /* 折线配置 */ }
    case 'pie':
      return { /* 饼图配置 */ }
    case 'radar':
      return { /* 雷达配置 */ }
  }
}

onMounted(() => nextTick(init))
onUnmounted(() => chartInstance?.dispose())
window.addEventListener('resize', () => chartInstance?.resize())
</script>

<style scoped>
.base-chart { width: 100%; height: 300px; }
</style>
```

#### CountTo.vue（1.5h）

**用途**：数字翻牌动画，从 0 滚动到目标值。

```vue
<template>
  <span ref="elRef" class="count-to">{{ displayValue }}</span>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  // 目标值
  target: { type: Number, required: true },
  // 动画时长（ms）
  duration: { type: Number, default: 1500 },
  // 小数位数
  decimals: { type: Number, default: 0 },
  // 前缀
  prefix: { type: String, default: '' },
  // 后缀
  suffix: { type: String, default: '' },
  // 分隔符（千分位）
  separator: { type: String, default: ',' }
})

const displayValue = ref(formatNumber(0))

function formatNumber(n) {
  return props.prefix + n.toFixed(props.decimals).replace(/\B(?=(\d{3})+(?!\d))/g, props.separator) + props.suffix
}

function animate() {
  const start = performance.now()
  const from = 0
  const to = props.target
  function step(now) {
    const elapsed = now - start
    const progress = Math.min(elapsed / props.duration, 1)
    // easeOutCubic
    const eased = 1 - Math.pow(1 - progress, 3)
    const current = from + (to - from) * eased
    displayValue.value = formatNumber(current)
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

watch(() => props.target, () => animate(), { immediate: true })
</script>

<style scoped>
.count-to {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(180deg, #fff 0%, #00f2ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
```

#### ScreenMap.vue（3h）

**用途**：中国地图 + 闪烁热力点。

```vue
<template>
  <div ref="mapRef" class="screen-map"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
// 引入中国地图 JSON（v1 demo 已打包好）
import chinaMapJson from '@/assets/map/china.json'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const mapRef = ref(null)
let chartInstance = null

function init() {
  echarts.registerMap('china', chinaMapJson)
  chartInstance = echarts.init(mapRef.value)
  render()
}

function render() {
  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item' },
    geo: {
      map: 'china',
      roam: false,
      zoom: 1.2,
      label: { show: false },
      itemStyle: {
        areaColor: 'rgba(0, 50, 100, 0.3)',
        borderColor: '#00f2ff',
        borderWidth: 1,
        shadowColor: 'rgba(0, 242, 255, 0.5)',
        shadowBlur: 10
      },
      emphasis: {
        itemStyle: { areaColor: '#0099ff' },
        label: { show: true, color: '#fff' }
      }
    },
    series: [
      // 散点 + 涟漪动画
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: props.data.map(d => ({ name: d.name, value: [d.lng, d.lat, d.value] })),
        showEffectOn: 'render',
        rippleEffect: { brushType: 'stroke', scale: 4 },
        symbolSize: val => Math.max(8, Math.min(val[2] / 100, 30)),
        itemStyle: { color: '#ff4081', shadowBlur: 10, shadowColor: '#ff4081' },
        label: { show: true, color: '#fff', formatter: '{b}' }
      }
    ]
  }, true)
}

onMounted(() => nextTick(init))
onUnmounted(() => chartInstance?.dispose())
</script>

<style scoped>
.screen-map {
  width: 100%;
  height: 500px;
}
</style>
```

**地图 JSON 文件**：
```
src/assets/map/china.json    （约 200KB，从 v1 demo 1/frontend/src/assets/map/ 复制）
```

### 2.3 前端页面（5 个新增 / 1 个编辑）

| # | 文件 | 行数 | 工作量 | 来源 |
|---|------|------|--------|------|
| B-2.3.1 | `src/views/biz/cockpit/index.vue` | 600 | 10.5h | 新建（核心大屏页面） |
| B-2.3.2 | `src/api/biz/cockpit.js` | 60 | 0.5h | 新建 |
| B-2.3.3 | `src/views/dashboard/index.vue` | 250 | 5h | 从 v1 demo `1/frontend/src/views/dashboard/` (314 行) 迁移 |
| B-2.3.4 | `src/views/profile/index.vue` | 200 | 3h | 从 v1 demo `1/frontend/src/views/profile/` 迁移 + 合并我已做的签名画板 |
| B-2.3.5 | `src/views/system/users.vue` | 350 | 6h | 从 v1 demo `1/frontend/src/views/system/users.vue` 风格化覆写 |
| B-2.3.6 | `src/api/biz/system.js` | 80 | 0.5h | 新建（system:user 风格化） |

#### 驾驶舱页面布局（B-2.3.1，10.5h）

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 合同总数  │  │ 审批中    │  │ 已通过    │  │ 客户数    │     │
│  │  1234   │  │   23    │  │  1156   │  │   89    │        │
│  │ CountTo │  │ CountTo  │  │ CountTo  │  │ CountTo │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐                                    │
│  │ 渠道数    │  │ 本月营收  │                                    │
│  │   12    │  │ ¥567万   │                                    │
│  └──────────┘  └──────────┘                                    │
│                                                                │
│  ┌──────────────────────────┐  ┌──────────────────────────┐   │
│  │ 7 日趋势（折线图）         │  │ 合同状态分布（饼图）       │   │
│  │                          │  │                          │   │
│  │   [BaseChart type=line] │  │   [BaseChart type=pie]   │   │
│  │                          │  │                          │   │
│  └──────────────────────────┘  └──────────────────────────┘   │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 中国地图（渠道分布热力）                                    │  │
│  │ [ScreenMap]                                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────┐  ┌──────────────────────────┐   │
│  │ Top10 客户（柱状图）       │  │ 最近审批流（时间轴）       │   │
│  │                          │  │                          │   │
│  │   [BaseChart type=bar]  │  │   [el-timeline]           │   │
│  └──────────────────────────┘  └──────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

**视觉规范**：
- 背景：`#0a1a3a`（深蓝科技底）
- 卡片背景：`rgba(0, 30, 80, 0.6)` 透明玻璃感
- 边框：`#00f2ff`（青色发光）
- 标题：渐变文字 `linear-gradient(180deg, #fff 0%, #00f2ff 100%)`
- 字体：思源黑体 / HarmonyOS Sans

**页面核心代码骨架**（B-2.3.1）：

```vue
<template>
  <div class="cockpit">
    <!-- 顶部 KPI -->
    <div class="kpi-row">
      <div class="kpi-card" v-for="kpi in kpiList" :key="kpi.key">
        <div class="kpi-label">{{ kpi.label }}</div>
        <CountTo :target="kpi.value" :prefix="kpi.prefix" :decimals="kpi.decimals" />
      </div>
    </div>

    <!-- 中部：趋势 + 状态分布 -->
    <div class="row-2">
      <div class="panel">
        <div class="panel-title">7 日合同趋势</div>
        <BaseChart type="line" :data="trend7dNew" :categories="trend7dDates" height="280px" />
      </div>
      <div class="panel">
        <div class="panel-title">合同状态分布</div>
        <BaseChart type="pie" :data="statusDistribution" height="280px" />
      </div>
    </div>

    <!-- 中国地图 -->
    <div class="panel map-panel">
      <div class="panel-title">渠道全国分布</div>
      <ScreenMap :data="mapData" />
    </div>

    <!-- 底部：Top10 客户 + 最近审批 -->
    <div class="row-2">
      <div class="panel">
        <div class="panel-title">Top10 客户（按合同金额）</div>
        <BaseChart type="bar" :data="topCustomersAmount" :categories="topCustomersNames" height="280px" />
      </div>
      <div class="panel">
        <div class="panel-title">最近审批动态</div>
        <el-timeline>
          <el-timeline-item v-for="apv in recentApprovals" :key="apv.contractId" :timestamp="apv.time">
            <span class="apv-text">
              {{ apv.contractNo }} Step {{ apv.step }} - {{ apv.approverName }}
            </span>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getCockpitOverview } from '@/api/biz/cockpit'
import CountTo from '@/components/Biz/CountTo.vue'
import BaseChart from '@/components/Biz/BaseChart.vue'
import ScreenMap from '@/components/Biz/ScreenMap.vue'

const kpiList = ref([])
const trend7dDates = ref([])
const trend7dNew = ref([])
const statusDistribution = ref([])
const mapData = ref([])
const topCustomersNames = ref([])
const topCustomersAmount = ref([])
const recentApprovals = ref([])

let refreshTimer = null

async function load() {
  const res = await getCockpitOverview()
  const data = res.data
  kpiList.value = [
    { key: 'contractTotal', label: '合同总数', value: data.kpi.contractTotal },
    { key: 'contractPending', label: '审批中', value: data.kpi.contractPending },
    { key: 'contractApproved', label: '已通过', value: data.kpi.contractApproved },
    { key: 'customerTotal', label: '客户数', value: data.kpi.customerTotal },
    { key: 'channelTotal', label: '渠道数', value: data.kpi.channelTotal },
    { key: 'monthRevenue', label: '本月营收', value: data.kpi.monthRevenue, prefix: '¥', decimals: 2 }
  ]
  trend7dDates.value = data.trend7d.map(t => t.date)
  trend7dNew.value = data.trend7d.map(t => t.newContracts)
  statusDistribution.value = data.statusDistribution
  mapData.value = data.channelLocations || []  // 若路线 A 未完成则为空数组
  topCustomersNames.value = data.topCustomers.map(c => c.customerName)
  topCustomersAmount.value = data.topCustomers.map(c => c.totalAmount)
  recentApprovals.value = data.recentApprovals
}

onMounted(() => {
  load()
  // 60s 自动刷新
  refreshTimer = setInterval(load, 60000)
})

onUnmounted(() => clearInterval(refreshTimer))
</script>

<style scoped lang="scss">
.cockpit {
  min-height: 100vh;
  background: #0a1a3a;
  padding: 20px;
  color: #fff;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.kpi-card {
  background: rgba(0, 30, 80, 0.6);
  border: 1px solid #00f2ff;
  border-radius: 4px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 0 20px rgba(0, 242, 255, 0.3);
}

.kpi-label {
  font-size: 14px;
  color: #a0c4ff;
  margin-bottom: 8px;
}

.row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.panel {
  background: rgba(0, 30, 80, 0.6);
  border: 1px solid #00f2ff;
  border-radius: 4px;
  padding: 16px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  background: linear-gradient(180deg, #fff 0%, #00f2ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.map-panel {
  margin-bottom: 20px;
}
</style>
```

### 2.4 资源文件（1 个新增）

| # | 文件 | 大小 | 工作量 | 来源 |
|---|------|------|--------|------|
| B-2.4.1 | `src/assets/map/china.json` | 200KB | 0.5h | 从 v1 demo `1/frontend/src/assets/map/china.json` 复制 |

---

## 三、菜单与路由分配

### 3.1 menu_id 分配（与路线 A 互斥）

```
menu_id=13  战略驾驶舱    path=biz/cockpit     icon=pie-chart
menu_id=14  首页工作台    path=dashboard       icon=dashboard
menu_id=15  个人中心     path=/profile        icon=user
menu_id=16  用户管理     path=system/user     icon=users
```

### 3.2 顶级路由（dashboard 与 profile）

```javascript
// /dashboard 顶级路由
{
  path: '/dashboard',
  component: Layout,
  redirect: '/dashboard/index',
  children: [{
    path: 'index',
    component: () => import('@/views/dashboard/index.vue'),
    name: 'Dashboard',
    meta: { title: '首页', icon: 'dashboard', affix: true }
  }]
}

// /profile 顶级路由（隐藏菜单，顶部头像点击进入）
{
  path: '/profile',
  component: Layout,
  hidden: true,
  children: [{
    path: 'index',
    component: () => import('@/views/profile/index.vue'),
    name: 'Profile',
    meta: { title: '个人中心', icon: 'user' }
  }]
}
```

---

## 四、端到端验收清单

### 4.1 组件级验收

| 组件 | 验收动作 | 预期结果 |
|------|---------|---------|
| CountTo | 传入 target=1234 | 数字从 0 在 1.5s 内平滑滚动到 1,234 |
| CountTo | 传入 target=5678901.23, decimals=2 | 显示 ¥5,678,901.23 |
| BaseChart | type=bar, data=[10,20,30] | 显示柱状图，渐变青色 |
| BaseChart | type=line, data=[5,10,15] | 显示折线图，平滑曲线 |
| BaseChart | type=pie, data=[{name,value}] | 显示饼图，5 色科技风 |
| ScreenMap | 传入 5 个城市数据 | 中国地图显示，散点 + 涟漪动画 |

### 4.2 驾驶舱页面验收

- **加载**：访问 `/biz/cockpit`，6 个数字翻牌从 0 滚动到目标值
- **图表**：4 个 ECharts 图表正常渲染
- **地图**：中国地图显示，散点涟漪动画流畅
- **时间轴**：最近 10 条审批动态按时间倒序
- **自动刷新**：每 60s 自动重新拉取数据
- **响应式**：1440px / 1920px / 4K 三种分辨率自适应

### 4.3 dashboard / profile / system 验收

- **dashboard**：登录后跳 `/dashboard`，看到工作台（待办/常用功能/最近合同/系统通知 4 个区块）
- **profile**：头像下拉 → 个人中心 → 修改昵称 → 修改密码 → **绘制签名** → 保存 → 刷新页面签名仍存在
- **system/user**：用户列表 + 新建 + 编辑 + 删除 + 重置密码

### 4.4 视觉验收

- 浏览器全屏 1920×1080，驾驶舱占满屏幕
- 所有色值在切换 `html.dark` 后跟随，无白色块漂浮
- 移动端（768px 以下）显示「请在桌面端访问」提示

---

## 五、与路线 A 的边界确认

| 项目 | 路线 A 处理 | 路线 B 处理 |
|------|----------|----------|
| `biz_channel` 表 | A 写 | B **只读**（驾驶舱聚合查询） |
| `biz_invoice` 表 | A 写 | B **只读** |
| `biz_finance_entry` 表 | A 写 | B **只读** |
| `biz_operation` 表 | A 写 | B **只读** |
| `biz_contract` 表 | 已完成 | B **只读** |
| `biz_approval` 表 | 已完成 | B **只读** |
| `sys_user` 表 | 不动 | B 只读 |
| `src/router/index.js` | A 追加 channel/invoice/finance/operation 4 行 | B 追加 cockpit/dashboard/profile/system 4 行 |
| `sql/biz_menus_roles_init.sql` | A 追加 menu_id 9-12 | B 追加 menu_id 13-16 |

---

## 六、风险与回退方案

| 风险 | 触发条件 | 回退方案 |
|------|---------|---------|
| ECharts 性能差 | 4K 分辨率掉帧 | 关闭涟漪动画、降低 DPI |
| 中国地图 JSON 加载慢 | 首屏 > 3s | 改为按需 import + loading 占位 |
| 数字翻牌抖动 | 频繁刷新 | 改用 transform 优化 |
| cockpit 依赖路线 A 表未完成 | A 未启动 | B 用空数组兜底，地图不显示散点 |
| dashboard 替换 RuoYi 默认首页后用户不适应 | 习惯原首页 | 保留原 RuoYi 首页作为 fallback 链接 |
| profile 修改密码接口与 RuoYi 原生冲突 | 重复实现 | 检查是否已存在，合并 |
| 系统管理页面权限不足 | 普通用户可见 | 加 v-permission 控制 |

---

## 七、ECharts 安装与依赖

### 7.1 安装命令

```bash
cd ruoyi-fastapi-frontend
npm install echarts@^5.4.0 --save
```

### 7.2 package.json 改动

```json
{
  "dependencies": {
    "echarts": "^5.4.0"
  }
}
```

### 7.3 中国地图 JSON

```
src/assets/map/china.json    （从 v1 demo 复制，~200KB）
```

如果 v1 demo 没有，从 https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json 下载。

---

## 八、关联文档

- [并行开发路线总览](./00-并行开发路线总览.md)
- [路线 A 详细方案：业务闭环优先](./路线A-业务闭环优先.md)
- 开发进度台账 v2.9 → `docs/04-开发/开发进度台账.md`
- v1 demo 参考源码 → `1/frontend/src/components/screen/`、`1/frontend/src/views/dashboard/`、`1/frontend/src/views/profile/`、`1/frontend/src/views/system/users.vue`
- ADR 决策记录 → `docs/04-开发/ARD/ADR-架构决策记录.md` D13