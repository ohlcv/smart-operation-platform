<template>
  <div class="finance" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="card-header"><span>财务管理</span></div>
      </template>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索流水号 / 发票号 / 合同号 / 对手方" clearable class="search-input" @keyup.enter="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="typeFilter" placeholder="类型" clearable class="filter-select">
          <el-option v-for="o in typeOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-select v-model="clearedFilter" placeholder="对账状态" clearable class="filter-select">
          <el-option :value="0" label="未对账" />
          <el-option :value="1" label="已对账" />
        </el-select>
        <div class="toolbar-right">
          <el-button v-hasPermi="['finance:add']" type="primary" :icon="Plus" @click="openCreate">新建流水</el-button>
          <el-button v-hasPermi="['finance:import']" :icon="UploadFilled" @click="openImport">导入对账单</el-button>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </div>

      <el-table :data="list" border stripe>
        <el-table-column prop="entryNo" label="流水号" width="130" />
        <el-table-column label="类型 / 方向" width="150" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.entryType === 'receivable' ? 'success' : 'warning'" effect="plain">
              {{ row.entryTypeLabel }} · {{ row.directionLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="invoiceNo" label="发票号" width="130" />
        <el-table-column prop="contractNo" label="合同号" width="130" />
        <el-table-column prop="partyName" label="对手方" min-width="180" show-overflow-tooltip />
        <el-table-column label="金额(元)" width="140" align="right">
          <template #default="{ row }">{{ Number(row.amount || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="交易日期" width="120" align="center">
          <template #default="{ row }">{{ row.transactionDate || '—' }}</template>
        </el-table-column>
        <el-table-column label="对账" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.cleared === 1 ? 'success' : 'info'" size="small">
              {{ row.cleared === 1 ? '已对账' : '未对账' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link :icon="View" @click="openView(row)">详情</el-button>
            <el-button
              v-if="row.cleared === 0"
              v-hasPermi="['finance:edit']"
              size="small" type="primary" link :icon="Edit" @click="openEdit(row)"
            >编辑</el-button>
            <el-button
              v-if="row.cleared === 0"
              v-hasPermi="['finance:edit']"
              size="small" type="success" link @click="onClear(row)"
            >标记对账</el-button>
            <el-button
              v-if="row.cleared === 0"
              v-hasPermi="['finance:delete']"
              size="small" type="danger" link :icon="Delete" @click="onDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
        <template #empty>暂无财务流水</template>
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑流水' : '新建流水'" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="流水号" prop="entryNo">
              <el-input v-model="form.entryNo" :disabled="isEdit" placeholder="留空自动生成 FN-NNN" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型" prop="entryType">
              <el-select v-model="form.entryType" placeholder="请选择" style="width: 100%">
                <el-option v-for="o in typeOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="收支方向" prop="direction">
              <el-radio-group v-model="form.direction">
                <el-radio-button value="out">支出</el-radio-button>
                <el-radio-button value="in">收入</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="金额" prop="amount">
              <el-input-number v-model="form.amount" :min="0" :step="100" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="关联发票ID">
              <el-input-number v-model="form.invoiceId" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="对手方名称"><el-input v-model="form.partyName" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="银行账号"><el-input v-model="form.account" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开户行"><el-input v-model="form.bankName" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="账户名"><el-input v-model="form.accountName" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="交易日期">
              <el-date-picker v-model="form.transactionDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
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
    <el-drawer v-model="viewVisible" title="财务流水详情" size="500px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="流水号">{{ current.entryNo }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ current.entryTypeLabel }} · {{ current.directionLabel }}</el-descriptions-item>
        <el-descriptions-item label="关联发票">{{ current.invoiceNo || '—' }}</el-descriptions-item>
        <el-descriptions-item label="关联合同">{{ current.contractNo || '—' }}</el-descriptions-item>
        <el-descriptions-item label="对手方">{{ current.partyName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥ {{ Number(current.amount || 0).toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="银行账号">{{ current.account || '—' }}</el-descriptions-item>
        <el-descriptions-item label="开户行">{{ current.bankName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="账户名">{{ current.accountName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="交易日期">{{ current.transactionDate || '—' }}</el-descriptions-item>
        <el-descriptions-item label="对账状态">
          <el-tag :type="current.cleared === 1 ? 'success' : 'info'">
            {{ current.cleared === 1 ? '已对账' : '未对账' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="对账时间">{{ current.clearedTime || '—' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ current.remark || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ current.createdByName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(current.createTime) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <!-- CSV 导入 -->
    <el-dialog v-model="importVisible" title="银行对账单导入" width="640px" destroy-on-close>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
        <template #title>
          格式：交易日期(YYYY-MM-DD),银行账号,金额,方向(in/out),交易对手,对手账号,摘要<br />
          一行一条记录
        </template>
      </el-alert>
      <el-input
        v-model="csvText"
        type="textarea"
        :rows="10"
        placeholder="2026-07-11,6225880123456789,50000.00,in,某客户公司,,货款"
      />
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="onImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="BizFinanceIndex">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh, View, Edit, Delete, UploadFilled } from '@element-plus/icons-vue'
import {
  listFinances, createFinance, updateFinance, deleteFinance,
  clearFinance, importBankStatement, getFinanceOptions
} from '@/api/biz/finance'

const loading = ref(false)
const list = ref([])
const keyword = ref('')
const typeFilter = ref('')
const clearedFilter = ref('')
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const typeOptions = ref([])

async function load() {
  loading.value = true
  try {
    const res = await listFinances({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      keyword: keyword.value || undefined,
      entryType: typeFilter.value || undefined,
      cleared: clearedFilter.value === '' ? undefined : clearedFilter.value
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
    const res = await getFinanceOptions()
    typeOptions.value = res?.data?.types ?? []
  } catch {}
}

const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref()
const emptyForm = () => ({
  entryNo: '',
  entryType: 'receivable',
  direction: 'in',
  invoiceId: undefined,
  partyName: '',
  amount: 0,
  account: '',
  accountName: '',
  bankName: '',
  transactionDate: '',
  remark: ''
})
const form = reactive(emptyForm())
const rules = {
  entryType: [{ required: true, message: '请选择类型', trigger: 'change' }],
  direction: [{ required: true, message: '请选择方向', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }]
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
    entryNo: row.entryNo,
    entryType: row.entryType,
    direction: row.direction,
    invoiceId: row.invoiceId,
    partyName: row.partyName || '',
    amount: Number(row.amount),
    account: row.account || '',
    accountName: row.accountName || '',
    bankName: row.bankName || '',
    transactionDate: row.transactionDate || '',
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
      const { entryNo, entryType, direction, invoiceId, ...rest } = form
      await updateFinance(editingId.value, rest)
      ElMessage.success('修改成功')
    } else {
      await createFinance({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false; load()
  } catch {} finally { saving.value = false }
}

async function onClear(row) {
  try {
    await ElMessageBox.confirm(`将流水 ${row.entryNo} 标记为已对账？`, '对账确认', { type: 'success' })
  } catch { return }
  try {
    await clearFinance(row.id)
    ElMessage.success('已对账')
    load()
  } catch {}
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除流水「${row.entryNo}」吗？`, '删除确认', { type: 'warning' })
  } catch { return }
  try {
    await deleteFinance(row.id)
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

// CSV 导入
const importVisible = ref(false)
const importing = ref(false)
const csvText = ref('')

function openImport() {
  const today = new Date().toISOString().slice(0, 10)
  csvText.value = `${today},6225880123456789,50000.00,in,某客户公司,1234,货款`
  importVisible.value = true
}

function parseCsv(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim() && !l.startsWith('#'))
  return lines.map(line => {
    const [transactionDate, account, amount, direction, counterparty, counterpartyAccount, summary] =
      line.split(',').map(s => s.trim())
    return { transactionDate, account, amount, direction: direction || 'in', counterparty, counterpartyAccount, summary }
  }).filter(it => it.transactionDate && it.account && it.amount)
}

async function onImport() {
  const items = parseCsv(csvText.value)
  if (!items.length) {
    ElMessage.warning('没有可导入的记录')
    return
  }
  importing.value = true
  try {
    const res = await importBankStatement({ items })
    const d = res?.data ?? {}
    ElMessage.success(`导入完成：批次 ${d.batch_no ?? '-'}，成功 ${d.success ?? 0} 条`)
    importVisible.value = false
  } catch {} finally { importing.value = false }
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
</style>