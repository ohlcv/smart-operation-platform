<template>
  <div class="invoice" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="card-header"><span>发票管理</span></div>
      </template>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索发票号 / 合同号 / 购方" clearable class="search-input" @keyup.enter="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="statusFilter" placeholder="状态" clearable class="filter-select">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-select v-model="typeFilter" placeholder="类型" clearable class="filter-select">
          <el-option v-for="o in typeOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <div class="toolbar-right">
          <el-button v-hasPermi="['invoice:add']" type="primary" :icon="Plus" @click="openCreate">新建发票</el-button>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </div>

      <el-table :data="list" border stripe>
        <el-table-column prop="invoiceNo" label="发票号" width="130" />
        <el-table-column prop="contractNo" label="合同号" width="130" />
        <el-table-column prop="partyName" label="购方" min-width="180" show-overflow-tooltip />
        <el-table-column label="类型" width="130" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.invoiceTypeLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额(元)" width="140" align="right">
          <template #default="{ row }">{{ Number(row.amount || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="税额" width="110" align="right">
          <template #default="{ row }">{{ Number(row.taxAmount || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="STATUS_META[row.status]?.type">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开票日期" width="120" align="center">
          <template #default="{ row }">{{ row.issueDate || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link :icon="View" @click="openView(row)">详情</el-button>
            <el-button
              v-if="row.status === 'pending'"
              v-hasPermi="['invoice:edit']"
              size="small" type="primary" link :icon="Edit" @click="openEdit(row)"
            >编辑</el-button>
            <el-button
              v-if="row.status === 'pending'"
              v-hasPermi="['invoice:issue']"
              size="small" type="success" link @click="onIssue(row)"
            >标记已开</el-button>
            <el-button
              v-if="row.status === 'issued'"
              v-hasPermi="['invoice:void']"
              size="small" type="warning" link @click="onVoid(row)"
            >作废</el-button>
            <el-button
              v-if="row.status === 'pending'"
              v-hasPermi="['invoice:delete']"
              size="small" type="danger" link :icon="Delete" @click="onDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
        <template #empty>暂无发票数据</template>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pageNum"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="load"
          @size-change="load"
        />
      </div>
    </el-card>

    <!-- 新建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑发票' : '新建发票'" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="发票号" prop="invoiceNo">
              <el-input v-model="form.invoiceNo" :disabled="isEdit" placeholder="留空自动生成 FP-NNN" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联合同ID" prop="contractId">
              <el-input-number v-model="form.contractId" :min="1" :disabled="isEdit" style="width: 100%" />
              <span class="muted hint">合同必须为「已通过」状态</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="发票类型" prop="invoiceType">
              <el-select v-model="form.invoiceType" placeholder="请选择" style="width: 100%">
                <el-option v-for="o in typeOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="购方名称" prop="partyName">
              <el-input v-model="form.partyName" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="购方税号"><el-input v-model="form.partyTaxNo" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="申请日期">
              <el-date-picker v-model="form.applyDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="开票金额" prop="amount">
              <el-input-number v-model="form.amount" :min="0" :step="100" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率" prop="taxRate">
              <el-input-number v-model="form.taxRate" :min="0" :max="1" :step="0.01" :precision="4" style="width: 100%" />
              <span class="muted hint">0-1（如 0.13 表示13%）</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情 -->
    <el-drawer v-model="viewVisible" title="发票详情" size="500px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="发票号">{{ current.invoiceNo }}</el-descriptions-item>
        <el-descriptions-item label="合同号">{{ current.contractNo }}</el-descriptions-item>
        <el-descriptions-item label="发票类型">{{ current.invoiceTypeLabel }}</el-descriptions-item>
        <el-descriptions-item label="购方名称">{{ current.partyName }}</el-descriptions-item>
        <el-descriptions-item label="购方税号">{{ current.partyTaxNo || '—' }}</el-descriptions-item>
        <el-descriptions-item label="开票金额">¥ {{ Number(current.amount || 0).toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="税率">{{ (Number(current.taxRate) * 100).toFixed(2) }}%</el-descriptions-item>
        <el-descriptions-item label="税额">¥ {{ Number(current.taxAmount || 0).toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="STATUS_META[current.status]?.type">{{ current.statusLabel }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="申请日期">{{ current.applyDate || '—' }}</el-descriptions-item>
        <el-descriptions-item label="开票日期">{{ current.issueDate || '—' }}</el-descriptions-item>
        <el-descriptions-item label="作废原因">{{ current.voidReason || '—' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ current.remark || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ current.createdByName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(current.createTime) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <!-- 作废对话框 -->
    <el-dialog v-model="voidVisible" title="作废发票" width="500px">
      <el-form label-width="80px">
        <el-form-item label="作废原因" required>
          <el-input v-model="voidReason" type="textarea" :rows="3" placeholder="请输入作废原因（必填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="voidVisible = false">取消</el-button>
        <el-button type="warning" :loading="voiding" @click="confirmVoid">确认作废</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="BizInvoiceIndex">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh, View, Edit, Delete } from '@element-plus/icons-vue'
import {
  listInvoices, createInvoice, updateInvoice, deleteInvoice,
  issueInvoice, voidInvoice, getInvoiceOptions
} from '@/api/biz/invoice'

const STATUS_META = {
  pending: { type: 'info', label: '待开' },
  issued: { type: 'success', label: '已开' },
  void: { type: 'danger', label: '已作废' }
}

const loading = ref(false)
const list = ref([])
const keyword = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const statusOptions = ref([])
const typeOptions = ref([])

async function load() {
  loading.value = true
  try {
    const res = await listInvoices({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      keyword: keyword.value || undefined,
      status: statusFilter.value || undefined,
      invoiceType: typeFilter.value || undefined
    })
    list.value = res?.rows ?? []
    total.value = res?.total ?? 0
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const res = await getInvoiceOptions()
    statusOptions.value = res?.data?.statuses ?? []
    typeOptions.value = res?.data?.types ?? []
  } catch {}
}

const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref()
const emptyForm = () => ({
  invoiceNo: '',
  contractId: undefined,
  invoiceType: 'specialized',
  partyName: '',
  partyTaxNo: '',
  amount: 0,
  taxRate: 0.13,
  applyDate: '',
  remark: ''
})
const form = reactive(emptyForm())
const rules = {
  contractId: [{ required: true, message: '请输入关联合同ID', trigger: 'blur' }],
  invoiceType: [{ required: true, message: '请选择发票类型', trigger: 'change' }],
  partyName: [{ required: true, message: '请输入购方名称', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入开票金额', trigger: 'blur' }],
  taxRate: [{ required: true, message: '请输入税率', trigger: 'blur' }]
}

function openCreate() {
  isEdit.value = false; editingId.value = null
  Object.assign(form, emptyForm())
  formRef.value?.clearValidate?.()
  dialogVisible.value = true
}
function openEdit(row) {
  isEdit.value = true; editingId.value = row.id
  Object.assign(form, {
    invoiceNo: row.invoiceNo,
    contractId: row.contractId,
    invoiceType: row.invoiceType,
    partyName: row.partyName,
    partyTaxNo: row.partyTaxNo,
    amount: Number(row.amount),
    taxRate: Number(row.taxRate),
    applyDate: row.applyDate || '',
    remark: row.remark || ''
  })
  formRef.value?.clearValidate?.()
  dialogVisible.value = true
}
async function onSave() {
  try { await formRef.value?.validate() } catch { return }
  saving.value = true
  try {
    if (isEdit.value) {
      const { invoiceNo, contractId, ...rest } = form
      await updateInvoice(editingId.value, rest)
      ElMessage.success('修改成功')
    } else {
      await createInvoice({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false; load()
  } catch {} finally { saving.value = false }
}

async function onIssue(row) {
  try {
    await ElMessageBox.confirm(`将发票 ${row.invoiceNo} 标记为已开？`, '开票确认', { type: 'success' })
  } catch { return }
  try {
    const today = new Date().toISOString().slice(0, 10)
    await issueInvoice(row.id, today)
    ElMessage.success('已标记为已开')
    load()
  } catch {}
}

const voidVisible = ref(false)
const voidReason = ref('')
const voiding = ref(false)
const voidTarget = ref(null)
function onVoid(row) {
  voidTarget.value = row
  voidReason.value = ''
  voidVisible.value = true
}
async function confirmVoid() {
  if (!voidReason.value.trim()) {
    ElMessage.warning('请输入作废原因')
    return
  }
  voiding.value = true
  try {
    await voidInvoice(voidTarget.value.id, voidReason.value.trim())
    ElMessage.success('已作废')
    voidVisible.value = false
    load()
  } catch {} finally { voiding.value = false }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除发票「${row.invoiceNo}」吗？`, '删除确认', { type: 'warning' })
  } catch { return }
  try {
    await deleteInvoice(row.id)
    ElMessage.success('删除成功')
    load()
  } catch {}
}

const viewVisible = ref(false)
const current = ref(null)
function openView(row) { current.value = row; viewVisible.value = true }

function formatDate(t) {
  if (!t) return '—'
  const d = new Date(t)
  if (Number.isNaN(d.getTime())) return String(t)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  loadOptions()
  load()
})
</script>

<style scoped lang="scss">
.card-header { display: flex; justify-content: space-between; align-items: center; }
.toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.search-input { max-width: 320px; }
.filter-select { width: 160px; }
.toolbar-right { margin-left: auto; display: flex; gap: 8px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
.muted { color: var(--el-text-color-placeholder); }
.hint { font-size: 12px; margin-left: 8px; }
</style>
