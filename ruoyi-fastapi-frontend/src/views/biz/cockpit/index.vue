<template>
  <div class="cockpit" v-loading="loading">
    <!-- 顶部 KPI 6 个数字翻牌 -->
    <el-row :gutter="12" class="kpi-row">
      <el-col v-for="kpi in kpiList" :key="kpi.key" :xs="12" :sm="8" :md="4">
        <div class="kpi-card">
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

    <!-- 第 2 行：7 日趋势 + 状态分布 -->
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

    <!-- 第 3 行：中国地图 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :span="24">
        <div class="chart-card">
          <div class="chart-card__title">
            渠道全国分布
            <span class="chart-card__subtitle">路线 A 完成 channel 表后填充</span>
          </div>
          <ScreenMap :data="channelLocations" height="500px" />
        </div>
      </el-col>
    </el-row>

    <!-- 第 4 行：Top10 客户 + 最近审批 -->
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

    <!-- 底部：数据生成时间 + 手动刷新 -->
    <div class="cockpit-footer">
      <span class="generated-at" v-if="generatedAt">
        数据生成时间：{{ generatedAt }}
      </span>
      <el-button :icon="Refresh" size="small" @click="load" :loading="loading">
        手动刷新
      </el-button>
    </div>
  </div>
</template>

<script setup name="BizCockpitIndex">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getCockpitOverview } from '@/api/biz/cockpit'
import CountTo from '@/components/Biz/CountTo.vue'
import BaseChart from '@/components/Biz/BaseChart.vue'
import ScreenMap from '@/components/Biz/ScreenMap.vue'

const loading = ref(false)
const generatedAt = ref('')

const kpiList = ref([])
const trend7dDates = ref([])
const trend7dNew = ref([])
const trend7dApproved = ref([])
const statusDistribution = ref([])
const channelLocations = ref([])
const topCustomersNames = ref([])
const topCustomersAmount = ref([])
const recentApprovals = ref([])

let refreshTimer = null

function buildKpiList(kpi) {
  if (!kpi) return []
  return [
    { key: 'contractTotal', label: '合同总数', value: kpi.contractTotal || 0 },
    { key: 'contractPending', label: '审批中', value: kpi.contractPending || 0 },
    { key: 'contractApproved', label: '已通过', value: kpi.contractApproved || 0 },
    { key: 'customerTotal', label: '客户数', value: kpi.customerTotal || 0 },
    { key: 'channelTotal', label: '渠道数', value: kpi.channelTotal || 0, hint: '路线 A 完成' },
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
    // RuoYi 标准响应：{ code, msg, data }
    const data = res?.data || res || {}
    const kpi = data.kpi || {}
    kpiList.value = buildKpiList(kpi)

    trend7dDates.value = (data.trend7d || []).map((t) => t.date || t.day)
    trend7dNew.value = (data.trend7d || []).map((t) => t.newContracts || 0)
    trend7dApproved.value = (data.trend7d || []).map((t) => t.approvedContracts || 0)

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

onMounted(() => {
  load()
  // 60s 自动刷新
  refreshTimer = setInterval(load, 60000)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped lang="scss">
.cockpit {
  min-height: calc(100vh - 120px);
  background: linear-gradient(135deg, #0a1a3a 0%, #051b3a 100%);
  padding: 16px;
  color: #fff;
  border-radius: 4px;
}

.kpi-row {
  margin-bottom: 12px;
}

.kpi-card {
  background: rgba(0, 30, 80, 0.6);
  border: 1px solid rgba(0, 242, 255, 0.5);
  border-radius: 4px;
  padding: 16px 12px;
  text-align: center;
  margin-bottom: 12px;
  box-shadow: 0 0 12px rgba(0, 242, 255, 0.15);
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 0 20px rgba(0, 242, 255, 0.4);
    transform: translateY(-2px);
  }
}

.kpi-label {
  font-size: 13px;
  color: #a0c4ff;
  margin-bottom: 6px;
}

.kpi-hint {
  margin-top: 4px;
  font-size: 11px;
  color: #7090c0;
}

.chart-row {
  margin-bottom: 12px;
}

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
}

.chart-card__subtitle {
  margin-left: 8px;
  font-size: 12px;
  color: #7090c0;
  font-weight: normal;
}

.approval-list {
  height: 260px;
}

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

.approval-title {
  color: #fff;
}

.approval-approver {
  color: #ff9c00;
  font-size: 12px;
  margin-left: auto;
}

.cockpit-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-top: 8px;
  background: rgba(0, 30, 80, 0.3);
  border-radius: 4px;
}

.generated-at {
  font-size: 12px;
  color: #7090c0;
}

// 响应式：小屏（< 768px）禁用
@media (max-width: 768px) {
  .cockpit::before {
    content: '驾驶舱大屏建议在桌面端访问';
    display: block;
    background: rgba(255, 156, 0, 0.2);
    color: #ff9c00;
    padding: 8px;
    margin-bottom: 12px;
    border-radius: 4px;
    text-align: center;
    font-size: 13px;
  }
}
</style>