<template>
  <div class="home">
    <!-- ===== 顶部欢迎卡片 ===== -->
    <el-card class="welcome-card" shadow="never">
      <div class="welcome-inner">
        <div class="left">
          <el-avatar :size="64" :src="avatar" />
          <div class="info">
            <div class="greeting">
              {{ greeting }}，{{ nickName || name }}
              <span class="sig">「{{ signature || '专注智能运营每一天' }}」</span>
            </div>
            <div class="role-line">
              <el-tag
                v-for="r in visibleRoles"
                :key="r"
                size="small"
                type="primary"
                effect="plain"
                class="mr-1"
              >
                {{ roleLabel(r) }}
              </el-tag>
              <span class="meta">{{ today }} {{ weekday }} · 智能运营平台 v{{ appVersion }}</span>
            </div>
          </div>
        </div>

        <div class="right">
          <div class="kpi-cell" @click="$router.push('/biz/contract')">
            <div class="kpi-label">合同总数</div>
            <div class="kpi-value">{{ kpi.contractTotal ?? '--' }}</div>
            <div class="kpi-sub">本月新增 {{ kpi.contractMonthNew ?? 0 }}</div>
          </div>
          <div class="kpi-cell" @click="$router.push('/biz/approval')">
            <div class="kpi-label">待我审批</div>
            <div class="kpi-value text-warning">{{ kpi.approvalPending ?? '--' }}</div>
            <div class="kpi-sub">审批中 {{ kpi.contractPending ?? 0 }}</div>
          </div>
          <div class="kpi-cell" @click="$router.push('/biz/customer')">
            <div class="kpi-label">客户总数</div>
            <div class="kpi-value">{{ kpi.customerTotal ?? '--' }}</div>
            <div class="kpi-sub">渠道 {{ kpi.channelTotal ?? 0 }}</div>
          </div>
          <div class="kpi-cell" @click="$router.push('/biz/finance')">
            <div class="kpi-label">本月合同金额</div>
            <div class="kpi-value text-success">
              ¥{{ formatMoney(kpi.contractMonthAmount) }}
            </div>
            <div class="kpi-sub">已通过 {{ kpi.contractApproved ?? 0 }} 笔</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- ===== 主体两栏 ===== -->
    <el-row :gutter="16" class="mt-3">
      <!-- 左主区 16 列 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="16" :xl="16">
        <!-- 待我审批 -->
        <el-card class="box-card" shadow="never" v-loading="loadingApproval">
          <template #header>
            <div class="card-header">
              <span class="title">
                <el-icon><Bell /></el-icon>
                待我审批
                <el-badge
                  v-if="pendingList.length > 0"
                  :value="pendingList.length"
                  class="ml-1"
                  type="warning"
                />
              </span>
              <el-link
                type="primary"
                :underline="false"
                @click="$router.push('/biz/approval')"
              >前往审批中心 →</el-link>
            </div>
          </template>
          <el-table
            v-if="pendingList.length > 0"
            :data="pendingList"
            stripe
            size="default"
            :row-style="{ cursor: 'pointer' }"
            @row-click="goApproval"
          >
            <el-table-column prop="contractNo" label="合同编号" width="170" />
            <el-table-column prop="title" label="合同标题" show-overflow-tooltip min-width="160" />
            <el-table-column prop="currentStep" label="节点" width="80" align="center">
              <template #default="{ row }">
                <el-tag size="small" effect="plain">第 {{ row.currentStep }} 级</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="submitUserName" label="提交人" width="100" show-overflow-tooltip />
            <el-table-column prop="submitTime" label="提交时间" width="160" />
            <el-table-column prop="amount" label="金额" width="120" align="right">
              <template #default="{ row }">
                <span class="money">¥{{ formatMoney(row.amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center" fixed="right">
              <template #default="{ row }">
                <el-link type="primary" :underline="false" @click.stop="goApproval(row)">
                  审批
                </el-link>
              </template>
            </el-table-column>
          </el-table>
          <el-empty
            v-else-if="!loadingApproval"
            description="暂无待审批合同"
            :image-size="80"
          />
        </el-card>

        <!-- 最近合同 -->
        <el-card class="box-card mt-3" shadow="never" v-loading="loadingContract">
          <template #header>
            <div class="card-header">
              <span class="title">
                <el-icon><Document /></el-icon>
                最近合同
              </span>
              <el-link
                type="primary"
                :underline="false"
                @click="$router.push('/biz/contract')"
              >前往合同管理 →</el-link>
            </div>
          </template>
          <el-table
            v-if="recentContracts.length > 0"
            :data="recentContracts"
            stripe
            size="default"
          >
            <el-table-column prop="contractNo" label="合同编号" width="170" />
            <el-table-column prop="title" label="合同标题" show-overflow-tooltip min-width="160" />
            <el-table-column prop="customerName" label="客户" width="120" show-overflow-tooltip />
            <el-table-column prop="amount" label="金额" width="120" align="right">
              <template #default="{ row }">
                <span class="money">¥{{ formatMoney(row.amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="statusType(row.status)">
                  {{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="创建时间" width="160" />
          </el-table>
          <el-empty
            v-else-if="!loadingContract"
            description="暂无合同数据"
            :image-size="80"
          />
        </el-card>
      </el-col>

      <!-- 右栏 8 列 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="8" :xl="8">
        <!-- 快速导航 -->
        <el-card class="box-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="title">
                <el-icon><Grid /></el-icon>
                快速导航
              </span>
            </div>
          </template>
          <div class="quick-grid">
            <div
              v-for="item in quickEntries"
              :key="item.path"
              class="quick-cell"
              @click="$router.push(item.path)"
            >
              <div class="quick-icon" :style="{ background: item.bg }">
                <el-icon :size="20" color="#fff">
                  <component :is="item.icon" />
                </el-icon>
              </div>
              <div class="quick-label">{{ item.title }}</div>
            </div>
          </div>
        </el-card>

        <!-- 我的工作台 -->
        <el-card class="box-card mt-3" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="title">
                <el-icon><DataAnalysis /></el-icon>
                我的工作台
              </span>
            </div>
          </template>

          <!-- 待我处理 -->
          <div class="ws-section">
            <div class="ws-section-label">待我处理</div>
            <div class="ws-grid">
              <div class="ws-cell" @click="$router.push('/biz/approval')">
                <div class="ws-num text-warning">{{ kpi.approvalPending ?? '--' }}</div>
                <div class="ws-name">待我审批</div>
              </div>
              <div class="ws-cell" @click="$router.push('/biz/contract')">
                <div class="ws-num">{{ kpi.contractTotal ?? '--' }}</div>
                <div class="ws-name">合同总数</div>
              </div>
              <div class="ws-cell" @click="$router.push('/biz/customer')">
                <div class="ws-num">{{ kpi.customerTotal ?? '--' }}</div>
                <div class="ws-name">客户总数</div>
              </div>
            </div>
          </div>

          <!-- 本月业务动态 -->
          <div class="ws-section">
            <div class="ws-section-label">本月业务动态</div>
            <ul class="ws-list">
              <li>
                <span class="ws-list-label">本月新增合同</span>
                <span class="ws-list-value">{{ kpi.contractMonthNew ?? 0 }} 笔</span>
              </li>
              <li>
                <span class="ws-list-label">审批中</span>
                <span class="ws-list-value text-warning">{{ kpi.contractPending ?? 0 }} 笔</span>
              </li>
              <li>
                <span class="ws-list-label">已通过</span>
                <span class="ws-list-value text-success">{{ kpi.contractApproved ?? 0 }} 笔</span>
              </li>
              <li>
                <span class="ws-list-label">已驳回</span>
                <span class="ws-list-value text-danger">{{ kpi.contractRejected ?? 0 }} 笔</span>
              </li>
              <li>
                <span class="ws-list-label">本月合同金额</span>
                <span class="ws-list-value text-success">¥{{ formatMoney(kpi.contractMonthAmount) }}</span>
              </li>
            </ul>
          </div>

          <!-- 快捷操作 -->
          <div class="ws-section">
            <div class="ws-section-label">快捷操作</div>
            <div class="ws-actions">
              <el-button type="primary" plain size="small" @click="$router.push('/biz/contract')">
                <el-icon><Plus /></el-icon>
                新建合同
              </el-button>
              <el-button type="success" plain size="small" @click="$router.push('/biz/customer')">
                <el-icon><Plus /></el-icon>
                新增客户
              </el-button>
              <el-button type="warning" plain size="small" @click="$router.push('/biz/channel')">
                <el-icon><Plus /></el-icon>
                新增渠道
              </el-button>
              <el-button size="small" @click="$router.push('/biz/operation')">
                <el-icon><Plus /></el-icon>
                录入经营
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import {
  Bell, Document, Grid, DataAnalysis,
  PieChart, Check, User, Share, Tickets, Wallet, Plus,
} from '@element-plus/icons-vue'
import useUserStore from '@/store/modules/user'
import { getDashboardOverview } from '@/api/biz/dashboard'
import { listApprovals } from '@/api/biz/approval'
import { listContracts } from '@/api/biz/contract'

defineOptions({
  name: 'Index',
})

const router = useRouter()
const userStore = useUserStore()
const { avatar, name, nickName, signature, roles: userRoles } = storeToRefs(userStore)

const visibleRoles = computed(() => (userRoles.value || []).slice(0, 3))

// ====== 时间 / 问候 ======
const today = computed(() => {
  const d = new Date()
  const pad = (n) => (n < 10 ? '0' + n : '' + n)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
})

const weekday = computed(() => {
  const cn = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return cn[new Date().getDay()]
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '凌晨好'
  if (h < 9) return '早安'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  if (h < 22) return '晚上好'
  return '夜深了'
})

// ====== 角色 ======
function roleLabel(roleKey) {
  const map = {
    admin: '超级管理员',
    common: '普通用户',
    biz_handler: '业务经办',
    biz_reviewer: '业务复核',
    risk_auditor: '风控审核',
    finance_h: '财务经办',
    finance_r: '财务复核',
    scm_director: '供管负责人',
    invest_d: '投资负责人',
  }
  return map[roleKey] || roleKey
}

// 项目当前版本（顶部欢迎卡片展示，与开发台账对齐）
const appVersion = '3.10'

// ====== 顶部 4 个 KPI（从 dashboard.kpi 取） ======
const kpi = ref({
  contractTotal: 0,
  contractMonthNew: 0,
  contractPending: 0,
  contractApproved: 0,
  contractRejected: 0,
  contractMonthAmount: 0,
  customerTotal: 0,
  channelTotal: 0,
  invoicePending: 0,
  approvalPending: 0,
})

async function loadKpi() {
  try {
    const res = await getDashboardOverview()
    const data = res?.data ?? res
    if (data?.kpi) {
      kpi.value = {
        ...kpi.value,
        contractTotal: data.kpi.contractTotal ?? 0,
        contractMonthNew: data.kpi.contractMonthNew ?? 0,
        contractPending: data.kpi.contractPending ?? 0,
        contractApproved: data.kpi.contractApproved ?? 0,
        contractRejected: data.kpi.contractRejected ?? 0,
        contractMonthAmount: data.kpi.contractMonthAmount ?? 0,
        customerTotal: data.kpi.customerTotal ?? 0,
        channelTotal: data.kpi.channelTotal ?? 0,
        invoicePending: data.kpi.invoicePending ?? 0,
        approvalPending: data.kpi.approvalPending ?? 0,
      }
    }
  } catch (e) {
    console.warn('[Index] loadKpi failed:', e)
  }
}

// ====== 待我审批 ======
const pendingList = ref([])
const loadingApproval = ref(false)
async function loadPending() {
  loadingApproval.value = true
  try {
    const res = await listApprovals({ scope: 'pending', pageNum: 1, pageSize: 5 })
    const data = res?.data ?? res
    pendingList.value = data?.rows ?? data?.items ?? []
  } catch (e) {
    console.warn('[Index] loadPending failed:', e)
    pendingList.value = []
  } finally {
    loadingApproval.value = false
  }
}

// ====== 最近合同 ======
const recentContracts = ref([])
const loadingContract = ref(false)
async function loadRecentContracts() {
  loadingContract.value = true
  try {
    const res = await listContracts({ pageNum: 1, pageSize: 5, orderBy: 'createTime', orderDirection: 'desc' })
    const data = res?.data ?? res
    recentContracts.value = data?.rows ?? data?.items ?? []
  } catch (e) {
    console.warn('[Index] loadRecentContracts failed:', e)
    recentContracts.value = []
  } finally {
    loadingContract.value = false
  }
}

// ====== 快速导航 ======
const quickEntries = [
  { title: '仪表盘', path: '/dashboard', icon: PieChart, bg: 'linear-gradient(135deg, #409eff, #2c7be5)' },
  { title: '审批中心', path: '/biz/approval', icon: Check, bg: 'linear-gradient(135deg, #67c23a, #3eaa10)' },
  { title: '合同管理', path: '/biz/contract', icon: Document, bg: 'linear-gradient(135deg, #909399, #606266)' },
  { title: '客户档案', path: '/biz/customer', icon: User, bg: 'linear-gradient(135deg, #e6a23c, #c97c1f)' },
  { title: '渠道管理', path: '/biz/channel', icon: Share, bg: 'linear-gradient(135deg, #f56c6c, #d14545)' },
  { title: '发票管理', path: '/biz/invoice', icon: Tickets, bg: 'linear-gradient(135deg, #9b59b6, #7d3cab)' },
  { title: '财务流水', path: '/biz/finance', icon: Wallet, bg: 'linear-gradient(135deg, #1abc9c, #16a085)' },
  { title: '经营数据', path: '/biz/operation', icon: DataAnalysis, bg: 'linear-gradient(135deg, #ff7e67, #e85d4d)' },
]

// ====== 跳转 ======
function goApproval(row) {
  router.push({ path: '/biz/approval', query: { contractId: row.contractId || row.id } })
}

// ====== 工具 ======
function formatMoney(v) {
  if (v == null || v === '') return '0.00'
  const n = Number(v)
  if (Number.isNaN(n)) return '0.00'
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const STATUS_MAP = {
  draft: { label: '草稿', type: 'info' },
  pending: { label: '审批中', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}
function statusLabel(s) {
  return STATUS_MAP[s]?.label || s || '-'
}
function statusType(s) {
  return STATUS_MAP[s]?.type || 'info'
}

// ====== 生命周期 ======
onMounted(() => {
  loadKpi()
  loadPending()
  loadRecentContracts()
})
</script>

<style scoped lang="scss">
.home {
  padding: 0;
}

/* ====== 顶部欢迎卡片 ====== */
.welcome-card {
  background: linear-gradient(
    135deg,
    var(--el-color-primary-light-7) 0%,
    var(--el-color-primary-light-9) 100%
  );
  border: 1px solid var(--el-color-primary-light-5);

  :deep(.el-card__body) {
    padding: 20px 24px;
  }
}

html.dark .welcome-card {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--el-color-primary) 22%, var(--el-bg-color)) 0%,
    var(--el-bg-color) 100%
  );
  border: 1px solid var(--el-color-primary-dark-2);
}

.welcome-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;

  .left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex: 1 1 320px;
    min-width: 280px;

    .info {
      display: flex;
      flex-direction: column;
      gap: 6px;

      .greeting {
        font-size: 20px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        line-height: 28px;

        .sig {
          margin-left: 8px;
          font-size: 13px;
          font-weight: 400;
          color: var(--el-text-color-secondary);
          font-style: italic;
        }
      }

      .role-line {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 4px;

        .meta {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }

  .right {
    display: flex;
    align-items: stretch;
    gap: 0;

    .kpi-cell {
      cursor: pointer;
      padding: 4px 20px;
      min-width: 120px;
      border-right: 1px dashed var(--el-color-primary-light-5);
      transition: all 0.2s ease;

      &:last-child {
        border-right: none;
      }

      &:hover {
        transform: translateY(-1px);
      }

      .kpi-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        line-height: 20px;
      }

      .kpi-value {
        font-size: 26px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        line-height: 36px;
        margin-top: 2px;

        &.text-warning {
          color: var(--el-color-warning);
        }

        &.text-success {
          color: var(--el-color-success);
        }
      }

      .kpi-sub {
        font-size: 11px;
        color: var(--el-text-color-placeholder);
        line-height: 16px;
        margin-top: 2px;
      }
    }
  }
}

/* ====== 通用卡片 ====== */
.box-card {
  :deep(.el-card__header) {
    padding: 12px 20px;
    background: var(--el-fill-color-blank);
  }

  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 15px;
    font-weight: 600;
    color: var(--el-text-color-primary);

    .el-icon {
      color: var(--el-color-primary);
    }
  }
}

.money {
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-weight: 500;
  color: var(--el-color-success);
}

/* ====== 快速导航 ====== */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;

  .quick-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 14px 4px;
    cursor: pointer;
    border-radius: 8px;
    background: var(--el-fill-color-light);
    transition: all 0.2s ease;

    &:hover {
      transform: translateY(-2px);
      background: var(--el-fill-color);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    html.dark &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }

    .quick-icon {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    }

    .quick-label {
      font-size: 12px;
      color: var(--el-text-color-regular);
      line-height: 16px;
    }
  }
}

@media (max-width: 1200px) {
  .quick-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* ====== 我的工作台 ====== */
.ws-section {
  padding: 12px 0;

  & + .ws-section {
    border-top: 1px dashed var(--el-border-color-lighter);
  }

  .ws-section-label {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    line-height: 20px;
    margin-bottom: 10px;
    font-weight: 500;
    letter-spacing: 0.5px;
  }
}

.ws-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;

  .ws-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 12px 4px;
    cursor: pointer;
    border-radius: 6px;
    background: var(--el-fill-color-light);
    transition: all 0.2s ease;

    &:hover {
      transform: translateY(-1px);
      background: var(--el-fill-color);
    }

    .ws-num {
      font-size: 22px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      line-height: 28px;

      &.text-warning {
        color: var(--el-color-warning);
      }
    }

    .ws-name {
      font-size: 11px;
      color: var(--el-text-color-secondary);
      line-height: 16px;
    }
  }
}

.ws-list {
  margin: 0;
  padding: 0;
  list-style: none;

  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    font-size: 13px;
    color: var(--el-text-color-regular);

    .ws-list-label {
      color: var(--el-text-color-secondary);
    }

    .ws-list-value {
      font-weight: 500;
      color: var(--el-text-color-primary);

      &.text-warning {
        color: var(--el-color-warning);
      }

      &.text-success {
        color: var(--el-color-success);
      }

      &.text-danger {
        color: var(--el-color-danger);
      }
    }
  }
}

.ws-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;

  .el-button {
    width: 100%;
    margin-left: 0;
  }
}

/* ====== 响应式 ====== */
@media (max-width: 992px) {
  .welcome-inner {
    flex-direction: column;
    align-items: flex-start;

    .right {
      width: 100%;
      justify-content: space-between;

      .kpi-cell {
        flex: 1;
        padding: 4px 8px;
        border-right: 1px dashed var(--el-color-primary-light-5);

        .kpi-value {
          font-size: 22px;
        }
      }
    }
  }
}
</style>