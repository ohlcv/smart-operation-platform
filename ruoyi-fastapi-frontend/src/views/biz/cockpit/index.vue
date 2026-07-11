<template>
  <div class="cockpit-workbench" v-loading="loading">
    <!-- 顶部条 -->
    <div class="workbench-header">
      <div>
        <h2 class="header-title">战略驾驶舱</h2>
        <p class="header-sub">
          业务全景 · 实时洞察 · 智能决策
          <span v-if="generatedAt" class="generated-at">数据生成时间：{{ generatedAt }}</span>
        </p>
      </div>
      <div class="header-actions">
        <el-button type="primary" size="large" :icon="FullScreen" @click="gotoDashboard">
          进入大屏
        </el-button>
        <el-button :icon="Refresh" size="large" @click="load" :loading="loading">
          刷新
        </el-button>
      </div>
    </div>

    <!-- 6 个 KPI -->
    <el-row :gutter="12" class="kpi-row">
      <el-col v-for="kpi in kpiList" :key="kpi.key" :xs="12" :sm="8" :md="4">
        <div class="kpi-card" :class="{ clickable: kpi.link }" @click="kpi.link && $router.push(kpi.link)">
          <div class="kpi-label">{{ kpi.label }}</div>
          <CountTo
            :target="kpi.value"
            :prefix="kpi.prefix || ''"
            :suffix="kpi.suffix || ''"
            :decimals="kpi.decimals || 0"
            :duration="1500"
          />
          <div v-if="kpi.hint" class="kpi-hint">{{ kpi.hint }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 4 个图表 + AI 提示 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :xs="24" :md="14">
        <div class="chart-card">
          <div class="chart-card__title">7 日合同趋势</div>
          <BaseChart
            type="line"
            :categories="trend7dDates"
            :data="trend7dNew"
            height="280px"
          />
        </div>
      </el-col>
      <el-col :xs="24" :md="10">
        <div class="chart-card">
          <div class="chart-card__title">合同状态分布</div>
          <BaseChart
            type="pie"
            :data="statusDistribution"
            height="280px"
          />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="12" class="chart-row">
      <el-col :xs="24" :md="12">
        <div class="chart-card">
          <div class="chart-card__title">Top10 客户（按合同金额）</div>
          <BaseChart
            type="bar"
            :categories="topCustomersNames"
            :data="topCustomersAmount"
            height="280px"
          />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="chart-card">
          <div class="chart-card__title">
            AI 智能大脑
            <el-button
              v-if="ai.summary"
              type="text"
              size="small"
              @click="gotoDashboard"
            >
              大屏查看雷达 →
            </el-button>
          </div>
          <div v-if="ai.summary" class="ai-card">
            <div class="ai-summary">{{ ai.summary }}</div>
            <div v-if="ai.risks?.length" class="ai-risks">
              <div v-for="(r, i) in ai.risks" :key="i" class="ai-risk-item" :class="`level-${r.level}`">
                <el-tag size="small" :type="r.level === 'high' ? 'danger' : r.level === 'medium' ? 'warning' : 'info'">
                  {{ r.level === 'high' ? '高' : r.level === 'medium' ? '中' : '低' }}风险
                </el-tag>
                <strong>{{ r.title }}</strong>
                <span class="ai-risk-detail">{{ r.detail }}</span>
              </div>
            </div>
            <div v-if="ai.suggestions?.length" class="ai-suggestions">
              <div v-for="(s, i) in ai.suggestions" :key="i" class="ai-suggestion-item">
                <el-tag size="small" type="success">建议</el-tag>
                <strong>{{ s.title }}</strong>
                <span class="ai-suggestion-detail">{{ s.detail }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="AI 诊断中…" />
        </div>
      </el-col>
    </el-row>

    <!-- 底部：渠道地图 + 最近审批 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :xs="24" :md="14">
        <div class="chart-card">
          <div class="chart-card__title">
            渠道全国分布
            <span class="chart-card__subtitle">点击地图省份可联动 KPI（大屏体验更佳）</span>
          </div>
          <ScreenMap :data="channelLocations" height="380px" />
        </div>
      </el-col>
      <el-col :xs="24" :md="10">
        <div class="chart-card">
          <div class="chart-card__title">最近审批动态</div>
          <el-scrollbar v-if="recentApprovals.length" class="approval-list">
            <el-timeline>
              <el-timeline-item
                v-for="apv in recentApprovals"
                :key="apv.contractId"
                :timestamp="apv.updatedAt"
                placement="top"
                color="#00f2ff"
              >
                <div class="approval-item">
                  <span class="approval-no">{{ apv.contractNo }}</span>
                  <el-tag size="small" type="info" effect="plain" class="approval-step">
                    Step {{ apv.step }} · {{ apv.stepLabel }}
                  </el-tag>
                  <span class="approval-title">{{ apv.title || '—' }}</span>
                  <span class="approval-approver" v-if="apv.approverName">
                    等待：{{ apv.approverName }}
                  </span>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-scrollbar>
          <el-empty v-else description="暂无审批动态" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="BizCockpitWorkbench">
/**
 * 战略驾驶舱 - 工作台入口（v3.3 路线 C）
 *
 * 形态：普通业务页（嵌入 Layout 内），快速一览 + AI 卡片提示
 * 大屏入口：右上角「进入大屏」按钮 → /cockpit/dashboard
 *
 * v3.3 改进：
 * - 集成 AI 大脑精简摘要卡片（高/中/低风险 + 建议）
 * - KPI 卡片可点击跳转对应业务页（v3.3 P2 #12）
 * - 保留地图但弱化（让大屏去玩）
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Refresh, FullScreen } from '@element-plus/icons-vue'
import { getCockpitOverview, getCockpitAiDiagnose } from '@/api/biz/cockpit'
import CountTo from '@/components/Biz/CountTo.vue'
import BaseChart from '@/components/Biz/BaseChart.vue'
import ScreenMap from '@/components/Biz/ScreenMap.vue'

const loading = ref(false)
const generatedAt = ref('')

const kpiList = ref([])
const trend7dDates = ref([])
const trend7dNew = ref([])
const statusDistribution = ref([])
const channelLocations = ref([])
const topCustomersNames = ref([])
const topCustomersAmount = ref([])
const recentApprovals = ref([])

const ai = ref({ summary: '', risks: [], suggestions: [] })

function gotoDashboard() {
  window.open('/cockpit/dashboard', '_blank')
}

function buildKpiList(kpi) {
  if (!kpi) return []
  return [
    {
      key: 'contractTotal',
      label: '合同总数',
      value: kpi.contractTotal || 0,
      link: '/biz/contract'
    },
    {
      key: 'contractPending',
      label: '审批中',
      value: kpi.contractPending || 0,
      hint: '点击进入审批中心',
      link: '/biz/approval'
    },
    {
      key: 'contractApproved',
      label: '已通过',
      value: kpi.contractApproved || 0
    },
    {
      key: 'customerTotal',
      label: '客户数',
      value: kpi.customerTotal || 0,
      link: '/biz/customer'
    },
    {
      key: 'channelTotal',
      label: '渠道数',
      value: kpi.channelTotal || 0,
      link: '/biz/channel'
    },
    {
      key: 'monthAmount',
      label: '本月合同金额',
      value: Number(kpi.contractMonthAmount || 0),
      prefix: '¥',
      decimals: 0,
      hint: `本月新增 ${kpi.contractMonthNew || 0} 单`
    }
  ]
}

async function load() {
  loading.value = true
  try {
    const res = await getCockpitOverview()
    const data = res?.data || res || {}
    const kpi = data.kpi || {}
    kpiList.value = buildKpiList(kpi)

    trend7dDates.value = (data.trend7d || []).map((t) => (t.date || t.day || '').slice(5))
    trend7dNew.value = (data.trend7d || []).map((t) => t.newContracts || 0)

    statusDistribution.value = (data.statusDistribution || []).map((s) => ({
      name: s.label,
      label: s.label,
      value: s.count
    }))

    channelLocations.value = data.channelLocations || []

    topCustomersNames.value = (data.topCustomers || []).map((c) => c.customerName)
    topCustomersAmount.value = (data.topCustomers || []).map((c) =>
      Number(c.totalAmount || 0)
    )

    recentApprovals.value = data.recentApprovals || []
    generatedAt.value = data.generatedAt || ''
  } finally {
    loading.value = false
  }
}

async function loadAi() {
  try {
    const res = await getCockpitAiDiagnose()
    ai.value = res?.data || res || {}
  } catch (e) {
    /* 静默 */
  }
}

let refreshTimer = null
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
</script>

<style scoped lang="scss">
.cockpit-workbench {
  min-height: calc(100vh - 120px);
  background: linear-gradient(135deg, #0a1a3a 0%, #051b3a 100%);
  padding: 16px;
  color: #fff;
  border-radius: 4px;
}

.workbench-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 242, 255, 0.3);
}
.header-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(90deg, #39c5ff, #2de1c2);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.header-sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: #a0c4ff;
}
.generated-at {
  margin-left: 16px;
  font-size: 12px;
  color: #7090c0;
}
.header-actions { display: flex; gap: 8px; }

.kpi-row { margin-bottom: 12px; }
.kpi-card {
  background: rgba(0, 30, 80, 0.6);
  border: 1px solid rgba(0, 242, 255, 0.5);
  border-radius: 4px;
  padding: 16px 12px;
  text-align: center;
  margin-bottom: 12px;
  box-shadow: 0 0 12px rgba(0, 242, 255, 0.15);
  transition: all 0.3s ease;

  &.clickable { cursor: pointer; }
  &.clickable:hover {
    box-shadow: 0 0 20px rgba(0, 242, 255, 0.4);
    transform: translateY(-2px);
  }
}
.kpi-label { font-size: 13px; color: #a0c4ff; margin-bottom: 6px; }
.kpi-hint { margin-top: 4px; font-size: 11px; color: #7090c0; }

.chart-row { margin-bottom: 12px; }
.chart-card {
  background: rgba(0, 30, 80, 0.6);
  border: 1px solid rgba(0, 242, 255, 0.3);
  border-radius: 4px;
  padding: 12px 16px;
  margin-bottom: 12px;
  min-height: 320px;
}
.chart-card__title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 8px;
  border-left: 3px solid #00f2ff;
  padding-left: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chart-card__subtitle {
  font-size: 12px;
  color: #7090c0;
  font-weight: normal;
}

/* AI 卡片 */
.ai-card {
  padding: 8px 4px;
  max-height: 280px;
  overflow-y: auto;
}
.ai-summary {
  padding: 10px 14px;
  background: rgba(0, 50, 100, 0.4);
  border-left: 3px solid #2de1c2;
  border-radius: 4px;
  font-size: 13px;
  color: #cfe8ff;
  margin-bottom: 10px;
}
.ai-risk-item,
.ai-suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  margin-bottom: 6px;
  background: rgba(6, 20, 46, 0.6);
  border-radius: 4px;
  font-size: 12px;
  flex-wrap: wrap;

  strong { color: #eafcff; margin-right: 4px; }
}
.ai-risk-detail,
.ai-suggestion-detail { color: #a0c4ff; flex: 1; }
.ai-risk-item.level-high { border-left: 2px solid #f56c6c; }
.ai-risk-item.level-medium { border-left: 2px solid #e6a23c; }
.ai-risk-item.level-low { border-left: 2px solid #909399; }

/* 审批时间轴 */
.approval-list { height: 340px; }
.approval-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.approval-no {
  color: #00f2ff;
  font-family: 'Menlo', 'Monaco', monospace;
  font-weight: 600;
}
.approval-step {
  border-color: rgba(0, 242, 255, 0.5);
  color: #a0c4ff;
  background: rgba(0, 30, 80, 0.6);
}
.approval-title { color: #fff; }
.approval-approver {
  color: #ff9c00;
  font-size: 12px;
  margin-left: auto;
}
</style>