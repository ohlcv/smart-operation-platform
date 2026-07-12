<template>
  <div class="app-container">
    <!-- 顶部筛选 -->
    <el-form
      :model="queryParams"
      ref="queryRef"
      :inline="true"
      label-width="68px"
      class="search-form"
    >
      <el-form-item label="合同编号" prop="contractNo">
        <el-input
          v-model="queryParams.contractNo"
          placeholder="请输入合同编号"
          clearable
          size="small"
          style="width: 180px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="合同名称" prop="title">
        <el-input
          v-model="queryParams.title"
          placeholder="请输入合同名称"
          clearable
          size="small"
          style="width: 180px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="关键字" prop="keyword">
        <el-input
          v-model="queryParams.keyword"
          placeholder="编号/名称/客户/乙方"
          clearable
          size="small"
          style="width: 180px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" size="small" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" size="small" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="approval-tabs">
      <el-tab-pane name="pending">
        <template #label>
          <span class="tab-label">
            待我审批
            <span v-if="pendingTotal > 0" class="tab-badge">{{ pendingTotal }}</span>
          </span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="我已审批" name="processed"></el-tab-pane>
      <el-tab-pane label="我提交的" name="submitted"></el-tab-pane>
    </el-tabs>

    <!-- 表格 -->
    <el-table
      v-loading="loading"
      :data="dataList"
      border
      stripe
      height="calc(100vh - 360px)"
    >
      <el-table-column label="合同编号" prop="contractNo" width="180" fixed="left" />
      <el-table-column label="合同名称" prop="title" min-width="200" show-overflow-tooltip />
      <el-table-column label="类型" prop="contractTypeLabel" width="120" align="center">
        <template #default="scope">
          <el-tag :type="scope.row.contractType === 'payment' ? 'warning' : 'success'" size="small">
            {{ scope.row.contractTypeLabel }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="甲方" prop="partyA" width="160" show-overflow-tooltip />
      <el-table-column label="乙方" prop="partyB" width="160" show-overflow-tooltip />
      <el-table-column label="金额(元)" prop="amount" width="140" align="right">
        <template #default="scope">
          <span class="amount-text">¥ {{ formatAmount(scope.row.amount) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="客户" prop="customerName" width="140" show-overflow-tooltip />
      <el-table-column label="状态" prop="statusLabel" width="100" align="center">
        <template #default="scope">
          <el-tag :type="statusTagType(scope.row.status)" size="small">
            {{ scope.row.statusLabel }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="当前步骤" prop="currentRoleLabel" width="120" align="center">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 'pending'" type="info" size="small">
            Step {{ scope.row.currentStep }} · {{ scope.row.currentRoleLabel }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="驳回次数" prop="rejectCount" width="80" align="center" />
      <el-table-column label="创建人" prop="createdByName" width="100" align="center" />
      <el-table-column label="创建时间" prop="createTime" width="160" align="center">
        <template #default="scope">
          <span class="time-text">{{ formatTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <!-- 我已审批 tab 额外列 -->
      <el-table-column
        v-if="activeTab === 'processed'"
        label="我的动作"
        prop="myActionLabel"
        width="100"
        align="center"
      >
        <template #default="scope">
          <el-tag :type="scope.row.myAction === 'approve' ? 'success' : 'danger'" size="small">
            {{ scope.row.myActionLabel }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        v-if="activeTab === 'processed'"
        label="我的意见"
        prop="myComment"
        min-width="160"
        show-overflow-tooltip
      />
      <!-- 操作 -->
      <el-table-column label="操作" width="240" fixed="right" align="center">
        <template #default="scope">
          <el-button
            type="primary"
            link
            size="small"
            icon="View"
            @click="openDetail(scope.row)"
          >
            查看详情
          </el-button>
          <template v-if="activeTab === 'pending' && scope.row.canApprove">
            <el-button
              type="success"
              link
              size="small"
              icon="Check"
              @click="openActionDialog(scope.row, 'approve')"
            >
              通过
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              icon="Close"
              @click="openActionDialog(scope.row, 'reject')"
            >
              驳回
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="queryParams.pageNum"
        v-model:page-size="queryParams.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleQuery"
        @current-change="handleQuery"
      />
    </div>

    <!-- 审批操作弹窗 -->
    <el-dialog
      v-model="actionDialog.visible"
      :title="actionDialog.action === 'approve' ? '审批通过' : '审批驳回'"
      width="560px"
      append-to-body
      destroy-on-close
    >
      <div v-if="actionDialog.row" class="action-summary">
        <div><strong>合同编号：</strong>{{ actionDialog.row.contractNo }}</div>
        <div><strong>合同名称：</strong>{{ actionDialog.row.title }}</div>
        <div><strong>当前步骤：</strong>Step {{ actionDialog.row.currentStep }} · {{ actionDialog.row.currentRoleLabel }}</div>
      </div>
      <el-form ref="actionFormRef" :model="actionDialog.form" :rules="actionDialog.rules" label-width="100px">
        <el-form-item label="审批意见" prop="comment">
          <el-input
            v-model="actionDialog.form.comment"
            type="textarea"
            :rows="3"
            placeholder="选填，记录您的审批意见"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item v-if="actionDialog.action === 'reject'" label="驳回原因" prop="rejectReason">
          <el-input
            v-model="actionDialog.form.rejectReason"
            type="textarea"
            :rows="3"
            placeholder="必填，明确告知驳回原因（创建人修改后重新提交）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-alert
          v-if="actionDialog.action === 'approve'"
          type="success"
          :closable="false"
          show-icon
        >
          <template #title>
            通过后将自动推进到下一审批环节
          </template>
        </el-alert>
        <el-alert
          v-else
          type="warning"
          :closable="false"
          show-icon
          style="margin-top: 4px"
        >
          <template #title>
            驳回后合同状态变为「已驳回待修改」，创建人可修改后重新提交（ADR D03）
          </template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="actionDialog.visible = false">取消</el-button>
        <el-button
          :type="actionDialog.action === 'approve' ? 'success' : 'danger'"
          :loading="actionDialog.loading"
          @click="submitAction"
        >
          确认{{ actionDialog.action === 'approve' ? '通过' : '驳回' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 合同详情抽屉（含 7 级进度条 + 时间轴 + 打印审批单） -->
    <ContractDetailDrawer
      v-model="detailDrawer.visible"
      :contract-id="detailDrawer.contractId"
    />
  </div>
</template>

<script setup name="BizApprovalIndex">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listApprovals,
  approveContract,
  rejectContract
} from '@/api/biz/approval'
import ContractDetailDrawer from './ContractDetailDrawer.vue'

const loading = ref(false)
const dataList = ref([])
const total = ref(0)
const pendingTotal = ref(0)
const activeTab = ref('pending')

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  contractNo: '',
  title: '',
  keyword: '',
  scope: 'pending'
})

const statusTagType = (status) => {
  const map = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const formatAmount = (val) => {
  if (val === null || val === undefined) return '0.00'
  const n = Number(val)
  return isNaN(n) ? '0.00' : n.toFixed(2)
}

const formatTime = (val) => {
  if (!val) return '-'
  return String(val).replace('T', ' ').slice(0, 19)
}

async function fetchList() {
  loading.value = true
  try {
    const res = await listApprovals({
      ...queryParams,
      scope: activeTab.value
    })
    dataList.value = res.rows || []
    total.value = res.total || 0
    // 同时拉一份待我审批总数用于 tab badge
    if (activeTab.value !== 'pending') {
      const pendingRes = await listApprovals({ scope: 'pending', pageNum: 1, pageSize: 1 })
      pendingTotal.value = pendingRes.total || 0
    } else {
      pendingTotal.value = total.value
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('加载审批列表失败')
  } finally {
    loading.value = false
  }
}

function handleQuery() {
  queryParams.pageNum = 1
  fetchList()
}

function resetQuery() {
  queryParams.contractNo = ''
  queryParams.title = ''
  queryParams.keyword = ''
  handleQuery()
}

function handleTabChange(tab) {
  queryParams.pageNum = 1
  queryParams.status = ''
  fetchList()
}

// 审批操作弹窗
const actionFormRef = ref()
const actionDialog = reactive({
  visible: false,
  action: 'approve',
  row: null,
  loading: false,
  form: { comment: '', rejectReason: '' },
  rules: {
    rejectReason: [
      {
        required: true,
        message: '驳回必须填写驳回原因',
        trigger: 'blur'
      }
    ]
  }
})

function openActionDialog(row, action) {
  actionDialog.row = row
  actionDialog.action = action
  actionDialog.form = { comment: '', rejectReason: '' }
  actionDialog.visible = true
}

async function submitAction() {
  await actionFormRef.value.validate()
  actionDialog.loading = true
  try {
    const data = {
      action: actionDialog.action,
      comment: actionDialog.form.comment || ''
    }
    if (actionDialog.action === 'reject') {
      data.rejectReason = actionDialog.form.rejectReason
    }
    const fn = actionDialog.action === 'approve' ? approveContract : rejectContract
    const res = await fn(actionDialog.row.id, data)
    ElMessage.success(res.msg || '操作成功')
    actionDialog.visible = false
    fetchList()
  } catch (e) {
    console.error(e)
    if (e !== 'cancel') {
      const msg = (e && e.response && e.response.data && e.response.data.msg) || '操作失败'
      ElMessage.error(msg)
    }
  } finally {
    actionDialog.loading = false
  }
}

// 合同详情抽屉（v2.9）：合同信息 + 7 级进度条 + 时间轴 + 打印审批单
const detailDrawer = reactive({
  visible: false,
  contractId: null
})

function openDetail(row) {
  detailDrawer.contractId = row.id
  detailDrawer.visible = true
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.search-form {
  background: var(--el-fill-color-blank);
  padding: 16px;
  border-radius: 4px;
  margin-bottom: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.approval-tabs {
  margin-bottom: 8px;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.tab-badge {
  display: inline-block;
  margin-left: 4px;
  padding: 0 6px;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  font-size: 12px;
  border-radius: 9px;
  background: #e6a23c;
  color: #fff;
  text-align: center;
  vertical-align: middle;
  box-shadow: 0 0 6px rgba(230, 162, 60, 0.55);
}

.amount-text {
  font-weight: 600;
  color: #f56c6c;
}

.time-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.action-summary {
  background: var(--el-fill-color-light);
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--el-text-color-regular);
}

.history-header {
  background: var(--el-fill-color-light);
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--el-text-color-regular);
}

.history-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.step-tag {
  display: inline-block;
  padding: 2px 8px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
}

.approver {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.role {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.history-item-comment,
.history-item-reject {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
  padding-left: 8px;
}

.history-item-reject {
  color: #f56c6c;
}

.history-item-sig {
  margin-top: 8px;
  padding-left: 8px;
}

.sig-img {
  max-height: 60px;
  max-width: 200px;
  border: 1px solid var(--el-border-color);
  border-radius: 3px;
  background: var(--el-fill-color-blank);
}
</style>