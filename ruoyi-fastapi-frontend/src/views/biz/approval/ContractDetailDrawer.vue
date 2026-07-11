<!--
  合同详情抽屉（v2.9 补）
  ---
  功能：
  1. 合同基础字段（与 v1 demo ContractDetailDrawer 一致）
  2. 7 级审批流转进度条（el-steps）
  3. 审批时间轴（el-timeline，含电子签名）
  4. 打印审批单（@media print 模式）

  数据源：/biz/contract/{id} + /biz/approval/history/{id}
  常量：  src/constants/business.js
-->
<template>
  <el-drawer
    :model-value="modelValue"
    size="820px"
    direction="rtl"
    destroy-on-close
    @update:model-value="(v) => $emit('update:modelValue', v)"
  >
    <template #header>
      <div class="drawer-header">
        <span class="title">合同详情</span>
        <el-tag v-if="contract" :type="STATUS_META[contract.status]?.type || 'info'" size="small">
          {{ STATUS_META[contract.status]?.text || contract.status }}
        </el-tag>
        <el-tag v-if="contract" effect="plain" size="small">
          {{ contract.contractTypeLabel || contract.contractType }}
        </el-tag>
      </div>
    </template>

    <div v-loading="loading" v-if="contract">
      <div class="toolbar">
        <span class="flex-1"></span>
        <el-button type="primary" :icon="Printer" size="small" @click="doPrint">生成并打印审批单</el-button>
      </div>

      <!-- 基础字段 -->
      <el-descriptions :column="2" border class="mb">
        <el-descriptions-item label="合同编号">{{ contract.contractNo }}</el-descriptions-item>
        <el-descriptions-item label="单据类型">{{ contract.contractTypeLabel }}</el-descriptions-item>
        <el-descriptions-item label="合同名称" :span="2">{{ contract.title }}</el-descriptions-item>
        <el-descriptions-item label="申请部门">{{ contract.department || '—' }}</el-descriptions-item>
        <el-descriptions-item label="业务类型">{{ contract.businessType || '—' }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ contract.customerName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="乙方">{{ contract.partyB || '—' }}</el-descriptions-item>
        <el-descriptions-item label="金额(小写)">¥ {{ formatAmount(contract.amount) }}</el-descriptions-item>
        <el-descriptions-item label="金额(大写)">{{ rmb }}</el-descriptions-item>
        <el-descriptions-item label="签订日期">{{ contract.signDate || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ contract.createdByName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="当前环节">
          <el-tag v-if="contract.status === 'pending'" type="warning" size="small">
            Step {{ contract.currentStep }} · {{ contract.currentRoleLabel || roleAtStep(contract.currentStep) }}
          </el-tag>
          <span v-else>—</span>
        </el-descriptions-item>
        <el-descriptions-item label="驳回次数" :span="2">
          <el-tag v-if="contract.rejectCount > 0" type="danger" size="small">{{ contract.rejectCount }}</el-tag>
          <span v-else>0</span>
        </el-descriptions-item>
        <el-descriptions-item v-if="contract.attachments && contract.attachments.length" label="附件" :span="2">
          <div v-for="(att, i) in contract.attachments" :key="i" class="att-link">
            <el-link :href="att.url" target="_blank" type="primary">
              <el-icon><Document /></el-icon> {{ att.name }}
            </el-link>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ contract.remark || '无' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 7 级流转进度条 -->
      <h4 class="section-title"><el-icon><Guide /></el-icon> 审批流转进度（7 级）</h4>
      <el-steps
        :active="stepsActive"
        align-center
        :process-status="processStatus"
        finish-status="success"
        class="chain-steps"
      >
        <el-step v-for="(r, i) in APPROVAL_CHAIN" :key="r" :title="roleLabel(r)" />
      </el-steps>

      <!-- 合规审计日志（时间轴 + 电子签名） -->
      <h4 class="section-title"><el-icon><Clock /></el-icon> 合规审计日志</h4>
      <el-timeline class="flow-timeline">
        <el-timeline-item
          v-for="item in approvals"
          :key="item.id"
          :type="item.action === 'reject' ? 'danger' : 'success'"
          :timestamp="formatTime(item.approvalTime)"
          size="large"
          placement="top"
        >
          <div class="flow-node">
            <div class="flow-node-main">
              <span class="flow-step">Step {{ item.step }}</span>
              <span class="flow-role">{{ item.stepLabel }}</span>
              <el-tag :type="item.action === 'reject' ? 'danger' : 'success'" size="small" effect="plain">
                {{ item.actionLabel }}
              </el-tag>
              <span class="flow-approver">{{ item.approverName || '系统' }}</span>
              <span class="flow-role-key">({{ item.approverRole }})</span>
            </div>
            <div v-if="item.comment" class="flow-comment">意见：{{ item.comment }}</div>
            <div v-if="item.rejectReason" class="flow-reject">驳回原因：{{ item.rejectReason }}</div>
            <img v-if="item.signatureSnapshot" :src="item.signatureSnapshot" class="flow-sig" alt="电子签名" />
          </div>
        </el-timeline-item>
        <el-empty v-if="!approvals.length" :image-size="60" description="暂无审批流转记录" />
      </el-timeline>
    </div>

    <el-empty v-else-if="!loading" description="未找到合同数据" />
  </el-drawer>

  <!-- 打印区：审批单 A4 -->
  <teleport to="body">
    <div class="approval-print-root" v-if="contract">
      <div class="print-sheet">
        <div class="print-title">山东出版供应链管理有限公司</div>
        <div class="print-subtitle">{{ contract.contractTypeLabel }}</div>
        <table class="print-table">
          <tbody>
            <tr>
              <th>申请部门</th>
              <td>{{ contract.department || '—' }}</td>
              <th>业务类型</th>
              <td>{{ contract.businessType || '—' }}</td>
            </tr>
            <tr>
              <th>客户名称</th>
              <td>{{ contract.customerName || contract.partyB || '—' }}</td>
              <th>合同编号</th>
              <td>{{ contract.contractNo }}</td>
            </tr>
            <tr>
              <th>合同名称</th>
              <td colspan="3">{{ contract.title }}</td>
            </tr>
            <tr>
              <th>金额(小写)</th>
              <td>¥ {{ formatAmount(contract.amount) }}</td>
              <th>金额(大写)</th>
              <td>{{ rmb }}</td>
            </tr>
            <tr>
              <th>备注</th>
              <td colspan="3" class="print-remark">{{ contract.remark || '无' }}</td>
            </tr>
          </tbody>
        </table>

        <div class="print-sign-title">审批流转与签章</div>
        <table class="print-table print-sign-table">
          <thead>
            <tr>
              <th>审批环节</th>
              <th>审批人</th>
              <th>意见</th>
              <th>签章</th>
              <th>日期</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in approvals" :key="'p' + a.id">
              <td>{{ a.stepLabel }}</td>
              <td>{{ a.approverName }}</td>
              <td>{{ a.action === 'reject' ? '驳回：' + (a.rejectReason || a.comment) : (a.comment || '同意') }}</td>
              <td class="print-sig-cell">
                <img v-if="a.signatureSnapshot" :src="a.signatureSnapshot" class="print-sig" alt="" />
              </td>
              <td>{{ formatDate(a.approvalTime) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="print-footer">
          打印时间：{{ nowText }}　本单据由业务平台自动生成，签章为电子签名。
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Printer, Clock, Guide, Document } from '@element-plus/icons-vue'
import { getContract } from '@/api/biz/contract'
import { getApprovalHistory } from '@/api/biz/approval'
import { APPROVAL_CHAIN, STATUS_META, roleLabel } from '@/constants/business'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  contractId: { type: [Number, String], default: null }
})
defineEmits(['update:modelValue'])

const loading = ref(false)
const contract = ref(null)
const approvals = ref([])
const nowText = ref('')

const CHINESE_DIGITS = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
const CHINESE_UNITS = ['', '拾', '佰', '仟']
const BIG_UNITS = ['', '万', '亿', '兆']

const rmb = computed(() => {
  if (!contract.value || contract.value.amount === null || contract.value.amount === undefined) return ''
  return digitToRMB(Number(contract.value.amount))
})

function formatAmount(v) {
  if (v === null || v === undefined) return '0.00'
  const n = Number(v)
  return isNaN(n) ? '0.00' : n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatTime(t) {
  if (!t) return ''
  return String(t).replace('T', ' ').slice(0, 19)
}
function formatDate(t) {
  if (!t) return ''
  return String(t).slice(0, 10)
}

/**
 * 把数字金额转中文大写（如 ¥1000.50 → 壹仟元伍角整）。
 * 与 v1 demo 行为一致，覆盖小写万元场景。
 */
function digitToRMB(num) {
  if (num === null || num === undefined || isNaN(num)) return ''
  const n = Math.abs(Number(num))
  if (n === 0) return '零元整'
  const yuan = Math.floor(n)
  const jiao = Math.floor((n - yuan) * 10)
  const fen = Math.round(((n - yuan) * 100) - jiao * 10)
  function sectionToChinese(val) {
    if (val === 0) return ''
    let out = ''
    let zeroFlag = false
    const digits = String(val).split('').map(Number)
    for (let i = 0; i < digits.length; i++) {
      const d = digits[i]
      const u = CHINESE_UNITS[digits.length - 1 - i]
      if (d === 0) {
        if (!zeroFlag && i !== digits.length - 1) out += '零'
        zeroFlag = true
      } else {
        out += CHINESE_DIGITS[d] + u
        zeroFlag = false
      }
    }
    return out
  }
  function splitYuan(v) {
    const arr = []
    let x = v
    while (x > 0) {
      arr.unshift(x % 10000)
      x = Math.floor(x / 10000)
    }
    return arr
  }
  let yStr = ''
  const sections = splitYuan(yuan)
  for (let i = 0; i < sections.length; i++) {
    yStr += sectionToChinese(sections[i]) + BIG_UNITS[sections.length - 1 - i]
  }
  let result = yStr + '元'
  if (jiao === 0 && fen === 0) {
    result += '整'
  } else {
    if (jiao > 0) result += CHINESE_DIGITS[jiao] + '角'
    else result += '零'
    if (fen > 0) result += CHINESE_DIGITS[fen] + '分'
  }
  return result
}

/**
 * 计算 el-steps 当前高亮位置：
 *  - status=approved → 全亮（n）
 *  - status=draft    → 0
 *  - 其余（pending / rejected）→ current_step
 */
const stepsActive = computed(() => {
  const c = contract.value
  if (!c) return 0
  if (c.status === 'approved') return APPROVAL_CHAIN.length
  if (c.status === 'draft') return 0
  return c.currentStep || 0
})

const processStatus = computed(() =>
  contract.value?.status === 'rejected' ? 'error' : 'process'
)

/**
 * 给一个 step 编号返回角色名（业务实现是 +1 偏置：role=APPROVAL_CHAIN[step]）。
 */
function roleAtStep(step) {
  return roleLabel(APPROVAL_CHAIN[step] || '')
}

async function load() {
  if (!props.contractId) return
  loading.value = true
  try {
    const [cRes, hRes] = await Promise.all([
      getContract(props.contractId),
      getApprovalHistory(props.contractId)
    ])
    // RuoYi response: { code: 200, data: {...} }
    contract.value = cRes?.data || cRes
    // /biz/approval/history 返回 { contract, items }（已经包在 data 里）
    const h = hRes?.data || hRes
    approvals.value = h?.items || []
  } catch (e) {
    console.error('ContractDetailDrawer.load error', e)
  } finally {
    loading.value = false
  }
}

function doPrint() {
  nowText.value = new Date().toLocaleString('zh-CN')
  nextTick(() => window.print())
}

watch(
  () => [props.modelValue, props.contractId],
  ([visible]) => {
    if (visible && props.contractId) load()
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
.drawer-header {
  display: flex;
  align-items: center;
  gap: 8px;

  .title {
    margin-right: 8px;
    font-size: 17px;
    font-weight: 600;
  }
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.flex-1 { flex: 1; }
.mb { margin-bottom: 8px; }

.att-link {
  display: inline-block;
  margin-right: 12px;
  margin-bottom: 4px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 22px 0 14px;
  font-size: 15px;
  font-weight: 600;

  .el-icon {
    color: var(--el-color-primary, #409eff);
  }
}

.chain-steps {
  margin-bottom: 8px;
  :deep(.el-step__title) {
    font-size: 12px;
  }
}

.flow-timeline {
  padding-left: 4px;
}

.flow-node-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.flow-step {
  display: inline-block;
  padding: 2px 8px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
}
.flow-role { font-weight: 600; }
.flow-approver { color: #606266; font-size: 13px; }
.flow-role-key { color: #909399; font-size: 12px; }
.flow-comment {
  margin-top: 4px;
  color: #606266;
  font-size: 13px;
}
.flow-reject {
  margin-top: 4px;
  color: #f56c6c;
  font-size: 13px;
}
.flow-sig {
  margin-top: 6px;
  height: 44px;
  display: block;
  filter: drop-shadow(0 0 0.5px rgba(0, 0, 0, 0.2));
}
</style>

<!-- 全局打印样式（@media print）-->
<style lang="scss">
.approval-print-root {
  display: none;
}

@media print {
  body * {
    visibility: hidden !important;
  }
  .approval-print-root {
    display: block !important;
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
  }
  .approval-print-root,
  .approval-print-root * {
    visibility: visible !important;
  }
  @page {
    size: A4;
    margin: 16mm;
  }
}

.print-sheet {
  width: 100%;
  color: #000;
  font-family: 'SimSun', 'Songti SC', serif;
}
.print-title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
}
.print-subtitle {
  text-align: center;
  font-size: 18px;
  margin: 6px 0 18px;
}
.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.print-table th,
.print-table td {
  border: 1px solid #000;
  padding: 8px 10px;
  text-align: left;
  vertical-align: middle;
}
.print-table th {
  background: #f2f2f2;
  width: 110px;
  white-space: nowrap;
}
.print-remark {
  min-height: 48px;
}
.print-sign-title {
  margin: 18px 0 8px;
  font-size: 15px;
  font-weight: 700;
}
.print-sign-table th {
  text-align: center;
  width: auto;
}
.print-sign-table td {
  text-align: center;
}
.print-sig-cell {
  height: 46px;
}
.print-sig {
  height: 40px;
}
.print-footer {
  margin-top: 16px;
  font-size: 12px;
  color: #333;
}
</style>