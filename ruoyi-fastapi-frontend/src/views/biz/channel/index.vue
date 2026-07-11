<template>
  <div class="channel" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="card-header"><span>渠道管理</span></div>
      </template>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索渠道编码 / 名称 / 联系人" clearable class="search-input">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="categoryFilter" placeholder="分类筛选" clearable class="category-select">
          <el-option v-for="o in categoryOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <div class="toolbar-right">
          <el-button v-hasPermi="['channel:add']" type="primary" :icon="Plus" @click="openCreate">
            新建渠道
          </el-button>
          <el-button v-hasPermi="['channel:import']" :icon="UploadFilled" @click="openImport">导入</el-button>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </div>

      <el-table :data="filtered" border stripe>
        <el-table-column prop="channelCode" label="编码" width="110" />
        <el-table-column prop="channelName" label="渠道名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="分类" width="130" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.categoryLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contactName" label="联系人" width="110" />
        <el-table-column prop="contactPhone" label="电话" width="130" />
        <el-table-column label="佣金比例" width="100" align="right">
          <template #default="{ row }">
            <span v-if="row.commissionRate !== null && row.commissionRate !== undefined">
              {{ (Number(row.commissionRate) * 100).toFixed(2) }}%
            </span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="关联合同" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.contractIds && row.contractIds.length" type="success" size="small">
              {{ row.contractIds.length }} 个
            </el-tag>
            <span v-else class="muted">无</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              :disabled="!hasEditPerm"
              @change="onStatusChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center">
          <template #default="{ row }">
            <el-button size="small" link :icon="View" @click="openView(row)">详情</el-button>
            <el-button v-hasPermi="['channel:edit']" size="small" type="primary" link :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button v-hasPermi="['channel:delete']" size="small" type="danger" link :icon="Delete" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>暂无渠道数据</template>
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

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑渠道' : '新建渠道'" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="渠道编码" prop="channelCode">
              <el-input v-model="form.channelCode" :disabled="isEdit" placeholder="留空自动生成 QD-NNN" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="渠道名称" prop="channelName">
              <el-input v-model="form.channelName" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="渠道分类" prop="category">
              <el-select v-model="form.category" placeholder="请选择" style="width: 100%">
                <el-option v-for="o in categoryOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="平台地址">
              <el-input v-model="form.platformUrl" placeholder="https://" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="联系人"><el-input v-model="form.contactName" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话"><el-input v-model="form.contactPhone" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="联系邮箱"><el-input v-model="form.contactEmail" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佣金比例">
              <el-input-number v-model="form.commissionRate" :min="0" :max="1" :step="0.001" :precision="4" style="width: 100%" />
              <span class="muted hint">0-1 之间（如 0.05 表示 5%）</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="渠道说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="viewVisible" title="渠道详情" size="500px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="编码">{{ current.channelCode }}</el-descriptions-item>
        <el-descriptions-item label="渠道名称">{{ current.channelName }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ current.categoryLabel }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ current.contactName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ current.contactPhone || '—' }}</el-descriptions-item>
        <el-descriptions-item label="联系邮箱">{{ current.contactEmail || '—' }}</el-descriptions-item>
        <el-descriptions-item label="平台地址">
          <a v-if="current.platformUrl" :href="current.platformUrl" target="_blank">{{ current.platformUrl }}</a>
          <span v-else>—</span>
        </el-descriptions-item>
        <el-descriptions-item label="佣金比例">
          <span v-if="current.commissionRate !== null">{{ (Number(current.commissionRate) * 100).toFixed(2) }}%</span>
          <span v-else>—</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="current.status === 1 ? 'success' : 'info'" size="small">
            {{ current.status === 1 ? '启用' : '停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="说明">{{ current.description || '—' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ current.remark || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ current.createdByName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(current.createTime) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <!-- CSV 导入对话框 -->
    <el-dialog v-model="importVisible" title="批量导入渠道" width="640px" destroy-on-close>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
        <template #title>
          模板：渠道编码,渠道名称,分类,联系人,电话,佣金比例,备注<br />
          分类必须是：meituan / douyin / ctrip / tongcheng
        </template>
      </el-alert>
      <el-input
        v-model="csvText"
        type="textarea"
        :rows="10"
        placeholder="QD-005,小红书种草,tongcheng,张三,13800001234,0.0500,演示渠道"
      />
      <template #footer>
        <el-checkbox v-model="skipDuplicates">跳过重复编码</el-checkbox>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="onImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="BizChannelIndex">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh, View, Edit, Delete, UploadFilled } from '@element-plus/icons-vue'
import {
  listChannels, createChannel, updateChannel, deleteChannel,
  getChannelCategoryOptions, importChannels
} from '@/api/biz/channel'

const loading = ref(false)
const list = ref([])
const keyword = ref('')
const categoryFilter = ref('')
const categoryOptions = ref([])
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const hasEditPerm = ref(true)  // 简化为 true，实际由 v-hasPermi 控制按钮可见性

const filtered = computed(() => {
  return list.value // 后端已过滤，这里仅做 keyword 二次搜索兜底
})

async function load() {
  loading.value = true
  try {
    const res = await listChannels({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      keyword: keyword.value || undefined,
      category: categoryFilter.value || undefined
    })
    list.value = res?.rows ?? []
    total.value = res?.total ?? 0
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function loadCategoryOptions() {
  try {
    const res = await getChannelCategoryOptions()
    categoryOptions.value = res?.rows ?? []
  } catch {
    categoryOptions.value = [
      { value: 'meituan', label: '美团到综' },
      { value: 'douyin', label: '抖音生活服务' },
      { value: 'ctrip', label: '携程商旅' },
      { value: 'tongcheng', label: '同程旅行' }
    ]
  }
}

const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref()
const emptyForm = () => ({
  channelCode: '', channelName: '', category: '',
  contactName: '', contactPhone: '', contactEmail: '',
  platformUrl: '', commissionRate: 0,
  description: '', remark: ''
})
const form = reactive(emptyForm())
const rules = {
  channelName: [{ required: true, message: '请输入渠道名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择渠道分类', trigger: 'change' }]
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
    channelCode: row.channelCode,
    channelName: row.channelName,
    category: row.category,
    contactName: row.contactName || '',
    contactPhone: row.contactPhone || '',
    contactEmail: row.contactEmail || '',
    platformUrl: row.platformUrl || '',
    commissionRate: row.commissionRate ?? 0,
    description: row.description || '',
    remark: row.remark || ''
  })
  formRef.value?.clearValidate?.()
  dialogVisible.value = true
}
async function onSave() {
  try {
    await formRef.value?.validate()
  } catch { return }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateChannel(editingId.value, { ...form })
      ElMessage.success('修改成功')
    } else {
      await createChannel({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    load()
  } catch {
    // request interceptor 已处理
  } finally {
    saving.value = false
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除渠道「${row.channelName}」吗？${row.contractIds?.length ? '（该渠道已关联合同）' : ''}`,
      '删除确认', { type: 'warning' }
    )
  } catch { return }
  try {
    await deleteChannel(row.id)
    ElMessage.success('删除成功')
    load()
  } catch {}
}

async function onStatusChange(row) {
  try {
    await updateChannel(row.id, { status: row.status })
    ElMessage.success(row.status === 1 ? '已启用' : '已停用')
  } catch {
    row.status = row.status === 1 ? 0 : 1  // 回滚
  }
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
const skipDuplicates = ref(true)

function openImport() {
  csvText.value = 'QD-101,示例渠道A,meituan,张三,13800000001,0.0500,演示\nQD-102,示例渠道B,douyin,李四,13800000002,0.0600,演示'
  skipDuplicates.value = true
  importVisible.value = true
}

function parseCsv(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim() && !l.startsWith('#'))
  return lines.map(line => {
    const [channelCode, channelName, category, contactName, contactPhone, commissionRate, remark] =
      line.split(',').map(s => s.trim())
    return { channelCode, channelName, category, contactName, contactPhone, commissionRate, remark }
  }).filter(it => it.channelName && it.category)
}

async function onImport() {
  const items = parseCsv(csvText.value)
  if (!items.length) {
    ElMessage.warning('没有可导入的记录（请检查格式：编码,名称,分类,联系人,电话,佣金,备注）')
    return
  }
  importing.value = true
  try {
    const res = await importChannels({ items, skipDuplicates: skipDuplicates.value })
    const d = res?.data ?? {}
    ElMessage.success(
      `导入完成：成功 ${d.success ?? 0} 条，跳过 ${d.skipped ?? 0} 条，失败 ${(d.errors ?? []).length} 条`
    )
    importVisible.value = false
    load()
  } catch {
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  loadCategoryOptions()
  load()
})
</script>

<style scoped lang="scss">
.card-header { display: flex; justify-content: space-between; align-items: center; }
.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.search-input { max-width: 320px; }
.category-select { width: 180px; }
.toolbar-right { margin-left: auto; display: flex; gap: 8px; }
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.muted { color: var(--el-text-color-placeholder); }
.hint { font-size: 12px; margin-left: 8px; }
</style>
