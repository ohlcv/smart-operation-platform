<template>
  <!-- v3.6：扁平路由，去掉 ds-full 切换 -->
  <div class="ds">
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
        <!-- v3.5：删除「全屏投放」按钮，仅保留普通布局大屏；真实全屏用浏览器原生 F11 -->
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
          <div class="panel-title">7 日合同趋势</div>
          <BaseChart
            type="line"
            :categories="trendDates"
            :data="trendNew"
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
          <BaseChart
            v-if="ai.radarScores && ai.radarScores.length"
            type="radar"
            :categories="radarIndicators"
            :data="ai.radarScores"
            height="230px"
          />
          <div v-else class="ai-empty">AI 诊断中…</div>

          <div class="ai-typer">
            <span class="ai-tag">AI</span>
            <span class="ai-text">{{ typed }}<span class="caret">▋</span></span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
/**
 * 仪表盘 - 真·大屏（v3.3 路线 C：AI 智能大脑 + 6 KPI + 4 图表 + 中国地图 + 省份联动）
 *
 * 形态：DataScreen 风格（demo1 同款）
 * - 顶部标题栏（中文标题 + 英文副标题 + 在线状态 + 实时时钟）
 * - 三栏分栏：左 26% KPI + 趋势 / 中央 flex:1 地图 / 右 26% 审批跑马灯 + AI 大脑
 * - 省份联动：点击地图省份 → KPI / 趋势 / 状态分布 / Top10 全部按 province 过滤
 * - AI 大脑：6 维雷达 + summary / risks / suggestions 打字机轮播
 *
 * 路由：/dashboard（v3.6 扁平，顶级路由，菜单直达）
 * 全屏：浏览器原生 F11 / 系统快捷键
 * 数据源：
 *   - GET /biz/dashboard/overview[?province=xx]
 *   - GET /biz/dashboard/ai-diagnose
 */
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getDashboardOverview, getDashboardAiDiagnose } from '@/api/biz/dashboard'
import BaseChart from '@/components/Biz/BaseChart.vue'
import CountTo from '@/components/Biz/CountTo.vue'
import ScreenMap from '@/components/Biz/ScreenMap.vue'

// v3.6：扁平路由后无 Layout / 无全屏分支；useRoute / fullscreen ref / props / toggleScreen 已无引用
// 注释保留以备后续真需要时还原

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
const trendDates = computed(() => (overview.value.trend7d || []).map((t) => (t.date || t.day || '').slice(5)))
const trendNew = computed(() => (overview.value.trend7d || []).map((t) => t.newContracts || 0))

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

// AI 雷达 6 维指标（与后端 metrics 顺序对齐）
const radarIndicators = computed(() => [
  { name: '资金合规', max: 100 },
  { name: '风险防控', max: 100 },
  { name: '审批时效', max: 100 },
  { name: '数据质量', max: 100 },
  { name: '渠道覆盖', max: 100 },
  { name: '客户活跃', max: 100 }
])

// AI 打字机
const typed = ref('')
let typerTimer = null
function startTyper() {
  stopTyper()
  let mi = 0
  const typeMsg = () => {
    const msgs = aiMessages.value
    if (!msgs.length) {
      typerTimer = setTimeout(typeMsg, 500)
      return
    }
    const cur = String(msgs[mi % msgs.length] || '')
    let ci = 0
    typed.value = ''
    const step = () => {
      ci++
      typed.value = cur.slice(0, ci)
      if (ci < cur.length) typerTimer = setTimeout(step, 36)
      else typerTimer = setTimeout(() => { mi++; typeMsg() }, 2400)
    }
    step()
  }
  typeMsg()
}
function stopTyper() {
  if (typerTimer) {
    clearTimeout(typerTimer)
    typerTimer = null
  }
}
const aiMessages = computed(() => {
  const arr = []
  if (ai.value.summary) arr.push(ai.value.summary)
  ;(ai.value.risks || []).forEach((r) => {
    arr.push(`【${r.level === 'high' ? '高' : r.level === 'medium' ? '中' : '低'}风险】${r.title}：${r.detail}`)
  })
  ;(ai.value.suggestions || []).forEach((s) => {
    arr.push(`【建议】${s.title}：${s.detail}`)
  })
  return arr
})

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
})

onBeforeUnmount(() => {
  clearInterval(clockTimer)
  clearInterval(overviewTimer)
  clearInterval(aiTimer)
  stopTyper()
  abortCtrl?.abort()
})
</script>


<style scoped lang="scss">
/* demo1 同款：径向渐变 + 玻璃感面板 + 蓝色青光 */
/* v3.6：扁平 /dashboard 路由，不再嵌 Layout，去掉负 margin 与 ds-full 分支 */
.ds {
  background:
    radial-gradient(1200px 600px at 50% -10%, rgba(28, 155, 230, 0.18), transparent 60%),
    radial-gradient(900px 500px at 90% 110%, rgba(45, 225, 194, 0.12), transparent 60%),
    #000a1f;
  color: #cfe6ff;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  box-sizing: border-box;
  margin: 0;
  padding: 14px 20px;
  min-height: 100vh;
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