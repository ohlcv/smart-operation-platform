<template>
  <div class="operation" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="card-header"><span>经营数据</span></div>
      </template>

      <div class="toolbar">
        <el-input v-model="periodFilter" placeholder="周期，如 2026-07" clearable class="search-input" @keyup.enter="load" />
        <el-select v-model="periodTypeFilter" placeholder="周期类型" clearable class="filter-select">
          <el-option v-for="o in periodTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-select v-model="businessLineFilter" placeholder="业务线" clearable class="filter-select">
          <el-option v-for="o in businessLineOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <div class="toolbar-right">
          <el-button v-hasPermi="['operation:comparison']" type="success" :icon="DataLine" @click="openComparison">同比环比</el-button>
          <el-button v-hasPermi="['operation:add']" type="primary" :icon="Plus" @click="openCreate">新建</el-button>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </div>

      <el-table :data="list" border stripe>
        <el-table-column prop="period" label="周期" width="100" />
        <el-table-column label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.periodTypeLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="业务线" width="100" align="center">
          <template #default="{ row }">
            <span>{{ row.businessLineLabel || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="营收(元)" width="140" align="right">
          <template #default="{ row }">{{ Number(row.revenue || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="成本" width="120" align="right">
          <template #default="{ row }">{{ Number(row.cost || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="毛利" width="130" align="right">
          <template #default="{ row }">
            <span :class="row.grossProfit >= 0 ? 'profit' : 'loss'">{{ Number(row.grossProfit || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="customerCount" label="客户数" width="80" align="right" />
        <el-table-column prop="contractCount" label="合同数" width="80" align="right" />
        <el-table-column label="客单价" width="130" align="right">
          <template #default="{ row }">{{ Number(row.avgOrderValue || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link :icon="View" @click="openView(row)">详情</el-button>
            <el-button v-hasPermi="['operation:edit']" size="small" type="primary" link :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button v-hasPermi="['operation:delete']" size="small" type="danger" link :icon="Delete" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>暂无经营数据</template>
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑经营数据' : '新建经营数据'" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="周期" prop="period">
              <el-input v-model="form.period" :disabled="isEdit" placeholder="2026-07" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="类型" prop="periodType">
              <el-select v-model="form.periodType" :disabled="isEdit" style="width: 100%">
                <el-option v-for="o in periodTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="业务线">
              <el-select v-model="form.businessLine" :disabled="isEdit" clearable style="width: 100%">
                <el-option v-for="o in businessLineOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="营收(元)" prop="revenue">
              <el-input-number v-model="form.revenue" :min="0" :step="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="成本" prop="cost">
              <el-input-number v-model="form.cost" :min="0" :step="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="客户数"><el-input-number v-model="form.customerCount" :min="0" style="width: 100%" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同数"><el-input-number v-model="form.contractCount" :min="0" style="width: 100%" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            毛利 = 营收 - 成本；客单价 = 营收 ÷ 合同数（自动计算）
          </template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情 -->
    <el-drawer v-model="viewVisible" title="经营数据详情" size="500px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="周期">{{ current.period }}（{{ current.periodTypeLabel }}）</el-descriptions-item>
        <el-descriptions-item label="业务线">{{ current.businessLineLabel || '—' }}</el-descriptions-item>
        <el-descriptions-item label="营收">¥ {{ Number(current.revenue || 0).toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="成本">¥ {{ Number(current.cost || 0).toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="毛利">
          <span :class="current.grossProfit >= 0 ? 'profit' : 'loss'">¥ {{ Number(current.grossProfit || 0).toLocaleString() }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="客户数">{{ current.customerCount }}</el-descriptions-item>
        <el-descriptions-item label="合同数">{{ current.contractCount }}</el-descriptions-item>
        <el-descriptions-item label="客单价">¥ {{ Number(current.avgOrderValue || 0).toLocaleString() }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ current.remark || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ current.createdByName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(current.createTime) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <!-- 同比环比 -->
    <el-dialog v-model="comparisonVisible" title="同比环比对比" width="800px" destroy-on-close>
      <el-form label-width="100px" :inline="true">
        <el-form-item label="对比周期">
          <el-input v-model="cmpPeriod" placeholder="2026-07" />
        </el-form-item>
        <el-form-item label="业务线">
          <el-select v-model="cmpLine" clearable placeholder="全部" style="width: 180px">
            <el-option v-for="o in businessLineOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadComparison">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table v-if="cmpItems.length" :data="cmpItems" border stripe style="margin-top: 16px">
        <el-table-column prop="label" label="指标" width="100" />
        <el-table-column label="当期" width="140" align="right">
          <template #default="{ row }">{{ Number(row.current || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="环比上期" width="140" align="right">
          <template #default="{ row }">{{ Number(row.previous || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="环比变化" width="160" align="right">
          <template #default="{ row }">
            <span :class="row.momChange >= 0 ? 'profit' : 'loss'">
              {{ row.momChange >= 0 ? '+' : '' }}{{ Number(row.momChange || 0).toLocaleString() }}
              （{{ row.momRate >= 0 ? '+' : '' }}{{ row.momRate.toFixed(2) }}%）
            </span>
          </template>
        </el-table-column>
        <el-table-column label="同比去年同期" width="160" align="right">
          <template #default="{ row }">
            <span :class="row.yoyChange >= 0 ? 'profit' : 'loss'">
              {{ row.yoyChange >= 0 ? '+' : '' }}{{ Number(row.yoyChange || 0).toLocaleString() }}
              （{{ row.yoyRate >= 0 ? '+' : '' }}{{ row.yoyRate.toFixed(2) }}%）
            </span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else-if="cmpLoaded" description="暂无对比数据" />
    </el-dialog>
  </div>
</template>

<script setup name="BizOperationIndex">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh, View, Edit, Delete, DataLine } from '@element-plus/icons-vue'
import {
  listOperations, createOperation, updateOperation, deleteOperation,
  getOperationComparison, getOperationOptions
} from '@/api/biz/operation'

const loading = ref(false)
const list = ref([])
const periodFilter = ref('')
const periodTypeFilter = ref('')
const businessLineFilter = ref('')
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const periodTypeOptions = ref([])
const businessLineOptions = ref([])

async function load() {
  loading.value = true
  try {
    const res = await listOperations({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      period: periodFilter.value || undefined,
      periodType: periodTypeFilter.value || undefined,
      businessLine: businessLineFilter.value || undefined
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
    const res = await getOperationOptions()
    periodTypeOptions.value = res?.data?.periodTypes ?? []
    businessLineOptions.value = res?.data?.businessLines ?? []
  } catch {}
}

const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref()
const emptyForm = () => ({
  period: '',
  periodType: 'month',
  businessLine: '',
  revenue: 0,
  cost: 0,
  customerCount: 0,
  contractCount: 0,
  remark: ''
})
const form = reactive(emptyForm())
const rules = {
  period: [{ required: true, message: '请输入周期', trigger: 'blur' }],
  periodType: [{ required: true, message: '请选择类型', trigger: 'change' }]
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
    period: row.period,
    periodType: row.periodType,
    businessLine: row.businessLine || '',
    revenue: Number(row.revenue),
    cost: Number(row.cost),
    customerCount: row.customerCount,
    contractCount: row.contractCount,
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
      const { period, periodType, businessLine, ...rest } = form
      await updateOperation(editingId.value, rest)
      ElMessage.success('修改成功')
    } else {
      await createOperation({ ...form, businessLine: form.businessLine || null })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false; load()
  } catch {} finally { saving.value = false }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除周期「${row.period}」的经营数据吗？`, '删除确认', { type: 'warning' })
  } catch { return }
  try {
    await deleteOperation(row.id)
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

// 同比环比
const comparisonVisible = ref(false)
const cmpPeriod = ref('2026-07')
const cmpLine = ref('')
const cmpItems = ref([])
const cmpLoaded = ref(false)

function openComparison() {
  comparisonVisible.value = true
  cmpItems.value = []
  cmpLoaded.value = false
  loadComparison()
}

async function loadComparison() {
  if (!cmpPeriod.value.trim()) {
    ElMessage.warning('请输入对比周期')
    return
  }
  try {
    const res = await getOperationComparison({
      period: cmpPeriod.value.trim(),
      businessLine: cmpLine.value || undefined
    })
    cmpItems.value = res?.data?.items ?? []
    cmpLoaded.value = true
  } catch (e) {
    cmpItems.value = []
    cmpLoaded.value = true
  }
}

onMounted(() => {
  loadOptions()
  load()
})
</script>

<style scoped lang="scss">
.card-header { display: flex; justify-content: space-between; align-items: center; }
.toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.search-input { max-width: 200px; }
.filter-select { width: 140px; }
.toolbar-right { margin-left: auto; display: flex; gap: 8px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
.profit { color: var(--el-color-success); }
.loss { color: var(--el-color-danger); }
</style>