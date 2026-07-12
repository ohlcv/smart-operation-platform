<template>
  <div class="ds" :class="{ 'is-fullscreen': isScreenRoute }">
    <!-- 顶部标题栏 -->
    <header class="screen-head">
      <div class="head-side left">
        <span class="dot online" />
        系统在线
        <span class="sep">|</span>
        视角：<span class="region-label">{{ regionLabel }}</span>
        <span v-if="province" class="back-region" @click="resetNational">← 返回全国</span>
      </div>
      <h1 class="head-title">
        <span class="title-cn">智能运营平台 · 数据仪表盘</span>
        <span class="title-en">SMART OPERATION PLATFORM · DATA DASHBOARD</span>
      </h1>
      <div class="head-side right">
        <span class="clock">{{ clock }}</span>
        <span class="sep">|</span>
        {{ today }}
        <span class="sep">|</span>
        <el-link
          :underline="false"
          class="fullscreen-toggle"
          @click="toggleFullscreen"
        >
          {{ isScreenRoute ? '退出全屏' : '全屏模式' }}
        </el-link>
      </div>
    </header>

    <div class="screen-body">
      <!-- 左侧：KPI + 趋势 -->
      <section class="col col-left">
        <div class="panel">
          <div class="panel-title">核心经营指标</div>
          <div class="metrics" :key="flipKey">
            <div class="metric" v-for="m in metricCards" :key="m.label">
              <div class="metric-ico">{{ m.ico }}</div>
              <div class="metric-body">
                <div class="metric-label">{{ m.label }}</div>
                <div class="metric-value" :style="{ color: m.color, textShadow: '0 0 12px ' + m.color }">
                  <CountTo :value="m.value" :prefix="m.prefix || ''" :suffix="m.suffix || ''" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="panel grow">
          <div class="panel-title">营收月度趋势 <em>YTD</em></div>
          <BaseChart
            type="area"
            :categories="revenueMonths"
            :data="revenueAmounts"
            height="240px"
          />
        </div>
      </section>

      <!-- 中央：天眼地图 -->
      <section class="col col-center">
        <div class="panel panel-map grow">
          <div class="panel-title center">
            全国业务天眼 · 渠道飞线 <em>点击省份联动两侧数据</em>
          </div>
          <ScreenMap
            :data="channelLocations"
            hub="北京"
            height="660px"
            @province-click="onProvince"
          />
        </div>
      </section>

      <!-- 右侧：审批跑马灯 + AI 大脑 -->
      <section class="col col-right">
        <div class="panel">
          <div class="panel-title">
            7 级审批流 · 实时动态
            <em>{{ recentApprovals.length }} 条 pending</em>
          </div>
          <div class="marquee" @mouseenter="pauseMarquee = true" @mouseleave="pauseMarquee = false">
            <div class="marquee-track" :class="{ paused: pauseMarquee }">
              <div
                v-for="(it, i) in marqueeLoop"
                :key="i"
                class="mq-item"
              >
                <span class="mq-no">{{ it.contractNo }}</span>
                <span class="mq-title">{{ it.title || '—' }}</span>
                <span class="mq-role">{{ it.stepLabel }}</span>
                <span v-if="it.approverName" class="mq-approver">→{{ it.approverName }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="panel grow" :key="'ai' + flipKey">
          <div class="panel-title">
            AI 智能大脑 · 风险雷达
            <em>{{ ai.summary ? '已诊断' : '诊断中…' }}</em>
          </div>

          <!-- 雷达图 + summary（dome 同款 d2de1c2 青色风格） -->
          <BaseChart
            v-if="ai.radarScores && ai.radarScores.length"
            type="radar"
            :categories="radarIndicators"
            :data="ai.radarScores"
            height="220px"
          />
          <div v-else class="ai-empty">AI 诊断中…</div>

          <!-- AI 总览一句话（替代原打字机） -->
          <div v-if="ai.summary" class="ai-summary">
            <span class="ai-tag">AI</span>
            <span class="ai-text">{{ ai.summary }}</span>
          </div>

          <!-- 风险 + 建议 分栏卡片（dome AiBrainPanel.vue 同款双列布局） -->
          <div v-if="ai.risks || ai.suggestions" class="ai-cols">
            <div class="ai-col">
              <div class="col-title">⚠ 业务风险预警</div>
            <div
              v-for="(r, i) in (ai.risks || [])"
              :key="'r' + i"
              class="risk-item"
              :class="'lv-' + r.level"
            >
              <div class="risk-head">
                <span class="risk-tag" :class="'lv-' + r.level">{{ aiLevelLabel(r.level) }}</span>
                <span class="risk-title">{{ r.title }}</span>
              </div>
                <div class="risk-detail">{{ r.detail }}</div>
              </div>
              <div v-if="!(ai.risks && ai.risks.length)" class="ai-empty-mini">✓ 当前无高风险</div>
            </div>
            <div class="ai-col">
              <div class="col-title">💡 运营/资金建议</div>
              <div
                v-for="(s, i) in (ai.suggestions || [])"
                :key="'s' + i"
                class="sug-item"
              >
                <div class="sug-title">{{ i + 1 }}. {{ s.title }}</div>
                <div class="sug-detail">{{ s.detail }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
/**
 * 仪表盘（v3.10 双路由共用 + 修正 Chrome 横向滚动 / sidebar 遮挡）
 *
 * 两种形态：
 * - 默认：路由 `/dashboard` → `/dashboard/index`，嵌 Layout（左侧菜单 + 顶部 navbar + Tags View + 中间区）
 *   头部右侧按钮显示「全屏模式」→ 点击 → push `/dashboard/screen` + requestFullscreen
 *   暗色背景只到 Layout 主区边界（width: 100%），不会被 sidebar 遮挡，没有横向溢出
 * - 真·大屏：路由 `/dashboard/screen`（顶级，不嵌 Layout），浏览器进入 Fullscreen API
 *   头部右侧按钮显示「退出全屏」→ 点击 → router.back + exitFullscreen
 *   暗色背景占满整页（min-height: 100vh + margin: 0）
 *
 * - 路由切换由头部按钮主动触发；浏览器 Esc / fullscreenchange 事件自动同步路由
 * - 同 dashboard.vue 文件两个 route 复用：screen 路由下用 `.ds.is-fullscreen` CSS（min-height: 100vh + margin: 0）
 * - 默认嵌入 Layout 时用 `.ds`（width: 100% + margin: 0 + 无 100vh，v3.10 去掉 v3.8/v3.9 的负 margin hack）
 *
 * 布局：DataScreen 风格（demo1 同款）
 * - 顶部标题栏（中文标题 + 英文副标题 + 在线状态 + 实时时钟 + 全屏切换）
 * - 三栏分栏：左 26% KPI + 趋势 / 中央 flex:1 地图 / 右 26% 审批跑马灯 + AI 大脑
 * - 省份联动：点击地图省份 → KPI / 趋势 / 状态分布 / Top10 全部按 province 过滤
 * - AI 大脑：6 维雷达 + summary / risks / suggestions 打字机轮播
 *
 * 数据源：
 *   - GET /biz/dashboard/overview[?province=xx]
 *   - GET /biz/dashboard/ai-diagnose
 */
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDashboardOverview, getDashboardAiDiagnose } from '@/api/biz/dashboard'
import BaseChart from '@/components/Biz/BaseChart.vue'
import CountTo from '@/components/Biz/CountTo.vue'
import ScreenMap from '@/components/Biz/ScreenMap.vue'

// v3.9：双路由共用 dashboard.vue。判断当前 route.name === 'BizDashboardScreen'
// 即为真·大屏形态；否则为默认嵌 Layout 形态。
const route = useRoute()
const router = useRouter()
const isScreenRoute = computed(() => route.name === 'BizDashboardScreen')

// 浏览器 Fullscreen API 封装
function getFullscreenElement() {
  return document.fullscreenElement || document.webkitFullscreenElement || null
}
function requestFullscreen(el) {
  const fn = el.requestFullscreen || el.webkitRequestFullscreen
  if (fn) return fn.call(el)
  return Promise.reject(new Error('Fullscreen API unsupported'))
}
function exitFullscreen() {
  const fn = document.exitFullscreen || document.webkitExitFullscreen
  if (fn) return fn.call(document)
  return Promise.resolve()
}

async function toggleFullscreen() {
  if (isScreenRoute.value) {
    // 当前在真·大屏：退到默认嵌 Layout 路由 + 退浏览器全屏
    try { await exitFullscreen() } catch (e) { /* ignore */ }
    router.push('/dashboard')
  } else {
    // 当前在默认：跳大屏路由 + 进浏览器全屏
    router.push('/dashboard/screen')
    // 路由切换后等组件挂完再 requestFullscreen
    await new Promise((r) => setTimeout(r, 50))
    try {
      const el = document.documentElement
      await requestFullscreen(el)
    } catch (e) {
      console.warn('requestFullscreen failed:', e)
    }
  }
}

// 监听浏览器全屏变化：用户按 Esc / 系统切走全屏 → 自动回默认路由
function onFullscreenChange() {
  if (!isScreenRoute.value) return
  if (!getFullscreenElement()) {
    // 浏览器全屏状态没了 + 当前在大屏路由 → 跳回默认
    router.push('/dashboard')
  }
}

// ---- 时钟 ----
const clock = ref('')
const today = ref('')
let clockTimer = null
function tickClock() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  clock.value = `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
  today.value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

// v3.5：Esc 全屏退出逻辑删除（已无全屏入口）

// ---- 数据 ----
const chartRef = ref(null)
const overview = ref({
  kpi: {},
  trend7d: [],
  revenueTrend: [],
  statusDistribution: [],
  topCustomers: [],
  recentApprovals: [],
  channelLocations: []
})
const ai = ref({
  summary: '',
  risks: [],
  suggestions: [],
  radarScores: []
})
const generatedAt = ref('')

// ---- 省份联动 ----
const province = ref('')
const flipKey = ref(0)
const regionLabel = computed(() => (province.value ? province.value : '全国'))

function onProvince(name) {
  province.value = name
  flipKey.value++
  load()
}
function resetNational() {
  province.value = ''
  flipKey.value++
  load()
}

// ---- 派生 ----
// 营收月度趋势：YTD，月份 X 轴标签如 "07月"，数据为元
const revenueMonths = computed(() => (overview.value.revenueTrend || []).map((t) => {
  const m = t.month || t.date || ''
  return m ? (m.slice(5) + '月') : ''
}))
const revenueAmounts = computed(() => (overview.value.revenueTrend || []).map((t) => Number(t.revenue || 0)))

const metricCards = computed(() => {
  const k = overview.value.kpi || {}
  return [
    { label: '合同总数', value: k.contractTotal || 0, color: '#2de1c2', ico: '📑', prefix: '' },
    { label: '审批中', value: k.contractPending || 0, color: '#ffd34e', ico: '📝' },
    { label: '已通过', value: k.contractApproved || 0, color: '#39c5ff', ico: '✅' },
    { label: '已驳回', value: k.contractRejected || 0, color: '#ff7ac6', ico: '⛔' },
    {
      label: '本月合同金额(元)',
      value: Number(k.contractMonthAmount || 0),
      color: '#2de1c2',
      ico: '💰',
      prefix: '¥'
    },
    { label: '待我审批', value: k.approvalPending || 0, color: '#ff7ac6', ico: '📌' }
  ]
})

const channelLocations = computed(() => overview.value.channelLocations || [])
const recentApprovals = computed(() => overview.value.recentApprovals || [])

// 跑马灯（demo1 同款：duplicate 一份接尾部实现无缝循环）
const pauseMarquee = ref(false)
const marqueeLoop = computed(() => [
  ...recentApprovals.value,
  ...recentApprovals.value
])

// AI 雷达 6 维指标（与后端 metrics 顺序对齐，v3.10 改 dome 同款 6 维）
const radarIndicators = computed(() => [
  { name: '资金合规', max: 100 },
  { name: '风险防控', max: 100 },
  { name: '盈利能力', max: 100 },
  { name: '审批时效', max: 100 },
  { name: '回款健康', max: 100 },
  { name: '数据质量', max: 100 }
])

// AI 风险等级标签（dome AiBrainPanel.vue lvType 同款：high/medium/low → 高/中/低）
const aiLevelLabel = (lv) => ({
  high: '高风险',
  medium: '中风险',
  low: '低风险'
}[lv] || lv || '提示')

// AI 诊断结果在模板内直接使用 ai.risks / ai.suggestions 渲染分栏
// （替代 v3.9 之前的打字机轮播）

// ---- 数据加载：signal + in-flight dedup ----
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
      { signal: ctrl.signal }
    )
    const data = res?.data || res || {}
    overview.value = data
    generatedAt.value = data.generatedAt || ""
  } catch (e) { /* 静默吞掉 axios cancel */ } finally { loadInFlight = false }
}

async function loadAi() {
  if (loadAiInFlight) return
  loadAiInFlight = true
  try {
    const res = await getDashboardAiDiagnose()
    ai.value = res?.data || res || {}
    startTyper()
  } catch (e) { /* 静默 */ } finally { loadAiInFlight = false }
}

onMounted(() => {
  tickClock()
  clockTimer = setInterval(tickClock, 1000)
  load()
  loadAi()
  overviewTimer = setInterval(load, 60000)
  aiTimer = setInterval(loadAi, 90000)
  // 如果当前路由是大屏路由（直链 / 刷新 / 浏览器后退），自动 requestFullscreen
  if (isScreenRoute.value && !getFullscreenElement()) {
    setTimeout(async () => {
      try {
        const el = document.documentElement
        await requestFullscreen(el)
      } catch (e) { console.warn('auto requestFullscreen failed:', e) }
    }, 80)
  }
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('webkitfullscreenchange', onFullscreenChange)
})

onBeforeUnmount(() => {
  clearInterval(clockTimer)
  clearInterval(overviewTimer)
  clearInterval(aiTimer)
  stopTyper()
  abortCtrl?.abort()
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', onFullscreenChange)
})
</script>


<style scoped lang="scss">
/* demo1 同款：径向渐变 + 玻璃感面板 + 蓝色青光 */
/* v3.10：双路由共用 + 修正 Chrome 横向滚动 / sidebar 遮挡
 * - 默认（嵌 Layout，/dashboard/index）：width: 100% 撑满 AppMain 主区，跟其他业务页一致
 *   ❌ v3.8/v3.9 hack `margin: 0 calc(50% - 50vw)` 让 .ds 强行溢出主区到 100vw，
 *      Chrome 严格按 spec 出现 body 横向滚动条 + 左边被 sidebar 盖住（Safari 行为不一致掩盖问题）
 *   ✅ v3.10 改成 `width: 100%`：暗色背景只到 Layout 主区边界，不会被 sidebar 遮挡，没有横向溢出
 *      「暗色背景贯穿屏幕边缘」只属于真·大屏形态（路由 /dashboard/screen）
 * - 真·大屏（/dashboard/screen，顶级路由）：min-height: 100vh + margin: 0 占满整页
 */
.ds {
  background:
    radial-gradient(1200px 600px at 50% -10%, rgba(28, 155, 230, 0.18), transparent 60%),
    radial-gradient(900px 500px at 90% 110%, rgba(45, 225, 194, 0.12), transparent 60%),
    #000a1f;
  color: #cfe6ff;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  box-sizing: border-box;
  /* v3.10：width: 100% 撑满 AppMain 主区，不溢出、不被 sidebar 遮挡 */
  width: 100%;
  margin: 0;
  padding: 14px 20px;
}

.ds.is-fullscreen {
  /* v3.10：全屏形态仍走 100vh + margin: 0，路由 /dashboard/screen 顶级渲染 */
  margin: 0;
  min-height: 100vh;
}

.fullscreen-toggle {
  cursor: pointer;
  user-select: none;
  font-size: 13px;
  color: #cfe6ff;
}
.fullscreen-toggle:hover {
  color: #2de1c2;
}

/* 头部 */
.screen-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px 14px;
  border-bottom: 1px solid rgba(45, 225, 194, 0.2);
}
.head-title { margin: 0; text-align: center; line-height: 1.2; flex: 1; }
.title-cn {
  display: block;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 3px;
  background: linear-gradient(90deg, #39c5ff, #2de1c2);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 0 24px rgba(45, 225, 194, 0.4);
}
.title-en {
  display: block;
  font-size: 11px;
  letter-spacing: 4px;
  color: #4f7bb0;
  margin-top: 3px;
}
.head-side { font-size: 13px; color: #7fa8d0; min-width: 300px; display: flex; align-items: center; gap: 4px; }
.head-side.right { justify-content: flex-end; }
.region-label { color: #2de1c2; font-weight: 700; }
.back-region {
  cursor: pointer;
  color: #4f7bb0;
  margin-left: 8px;
  text-decoration: underline;
  font-size: 12px;
  &:hover { color: #00f2ff; }
}
.clock { color: #2de1c2; font-weight: 700; font-size: 16px; letter-spacing: 1px; }
.sep { margin: 0 8px; color: #26456f; }
.scr-btn {
  margin-left: 10px;
  background: rgba(28, 155, 230, 0.15);
  border-color: rgba(45, 225, 194, 0.5);
  color: #9fe9ff;
}
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.dot.online { background: #2de1c2; box-shadow: 0 0 8px #2de1c2; animation: pulse 1.6s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.35 } }

/* 三栏 */
.screen-body { display: flex; gap: 16px; margin-top: 14px; }
.col { display: flex; flex-direction: column; gap: 16px; }
.col-left, .col-right { width: 26%; }
.col-center { flex: 1; }
.grow { flex: 1; }

.panel {
  position: relative;
  background: rgba(10, 28, 60, 0.45);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(45, 225, 194, 0.28);
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 0 18px rgba(28, 155, 230, 0.18), inset 0 0 26px rgba(28, 155, 230, 0.06);
}
.panel-map { padding: 8px 10px; }
.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: #eafcff;
  margin-bottom: 12px;
  padding-left: 10px;
  border-left: 3px solid #2de1c2;
  letter-spacing: 1px;
  display: flex;
  align-items: baseline;
  gap: 8px;
  em { font-style: normal; font-size: 12px; color: #4f7bb0; }
  &.center {
    justify-content: center;
    border-left: none;
    padding-left: 0;
  }
}

/* KPI */
.metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  animation: flipIn 0.6s ease;
}
@keyframes flipIn { from { transform: rotateX(90deg); opacity: 0 } to { transform: rotateX(0); opacity: 1 } }
.metric {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(6, 20, 46, 0.6);
  border: 1px solid rgba(28, 155, 230, 0.2);
  border-radius: 8px;
  padding: 12px;
}
.metric-ico { font-size: 24px; }
.metric-label { font-size: 12px; color: #7fa8d0; }
.metric-value {
  font-size: 20px;
  font-weight: 800;
  margin-top: 4px;
  font-variant-numeric: tabular-nums;
}

/* 跑马灯 */
.marquee { height: 168px; overflow: hidden; position: relative; }
.marquee-track {
  display: flex;
  flex-direction: column;
  animation: scrollUp 16s linear infinite;
}
.marquee-track.paused { animation-play-state: paused; }
@keyframes scrollUp { from { transform: translateY(0) } to { transform: translateY(-50%) } }
.mq-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  margin-bottom: 8px;
  background: rgba(6, 20, 46, 0.6);
  border-left: 2px solid #39c5ff;
  border-radius: 6px;
  font-size: 12px;
}
.mq-no { color: #2de1c2; font-family: monospace; flex: 0 0 auto; }
.mq-title {
  flex: 1;
  color: #cfe6ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mq-role {
  flex: 0 0 auto;
  color: #ffd34e;
  background: rgba(255, 211, 78, 0.12);
  padding: 2px 8px;
  border-radius: 10px;
}
.mq-approver { color: #ff9c00; font-size: 11px; }

/* AI 大脑 */
.ai-typer {
  margin-top: 10px;
  min-height: 66px;
  padding: 10px 12px;
  background: rgba(6, 20, 46, 0.6);
  border: 1px solid rgba(45, 225, 194, 0.2);
  border-radius: 8px;
  font-size: 12.5px;
  line-height: 1.7;
  color: #bfe8ff;
}
.ai-tag {
  display: inline-block;
  background: linear-gradient(90deg, #39c5ff, #2de1c2);
  color: #002;
  font-weight: 800;
  border-radius: 4px;
  padding: 0 6px;
  margin-right: 8px;
  font-size: 11px;
}
.ai-empty { padding: 40px; text-align: center; color: #7fa8d0; }
.caret { color: #2de1c2; animation: blink 1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0 } }
</style>