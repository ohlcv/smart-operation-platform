<template>
  <div class="customer" v-loading="loading">
    <el-card shadow="never">
      <template #header><div class="card-header"><span>客户档案管理</span></div></template>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索客户名称 / ID / 联系人" clearable class="search-input">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <div>
          <el-button type="primary" :icon="Plus" @click="openCreate">新建客户</el-button>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </div>

      <el-table :data="filtered" border stripe>
        <el-table-column prop="customerCode" label="客户ID" width="120" />
        <el-table-column prop="customerName" label="客户名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="contactName" label="联系人" width="110" />
        <el-table-column prop="contactPhone" label="电话" width="150" />
        <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
        <el-table-column label="准入资料" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.qualificationFiles?.length" type="success" size="small" effect="plain">
              {{ row.qualificationFiles.length }} 个附件
            </el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button size="small" link :icon="View" @click="openView(row)">查看</el-button>
            <el-button size="small" type="primary" link :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" link :icon="Delete" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>暂无客户数据</template>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑客户' : '新建客户'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="客户ID" prop="customerCode">
          <el-input v-model="form.customerCode" :disabled="isEdit" placeholder="留空自动生成 KH-NNN" />
        </el-form-item>
        <el-form-item label="客户名称" prop="customerName"><el-input v-model="form.customerName" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="联系人"><el-input v-model="form.contactName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="电话"><el-input v-model="form.contactPhone" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="准入资料">
          <div class="files">
            <el-tag
              v-for="(f, i) in form.qualificationFiles"
              :key="i"
              closable
              @close="form.qualificationFiles.splice(i, 1)"
              class="file-tag"
            >
              <el-icon><Document /></el-icon> {{ f.name }}
            </el-tag>
          </div>
          <el-upload action="#" :auto-upload="false" :show-file-list="false" :on-change="onFileChange">
            <el-button size="small" :icon="UploadFilled">上传准入资料（演示）</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="viewVisible" title="客户详情" size="520px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="客户ID">{{ current.customerCode }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ current.customerName }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ current.contactName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ current.contactPhone || '—' }}</el-descriptions-item>
        <el-descriptions-item label="地址">{{ current.address || '—' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ current.remark || '无' }}</el-descriptions-item>
        <el-descriptions-item label="准入资料附件">
          <div v-if="current.qualificationFiles?.length">
            <div v-for="(f, i) in current.qualificationFiles" :key="i" class="file-line">
              <el-icon><Document /></el-icon> {{ f.name }}
              <el-button size="small" link type="primary" @click="ElMessage.info('演示附件，暂不支持预览下载')">查看</el-button>
            </div>
          </div>
          <span v-else class="muted">无</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup name="BizCustomerIndex">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh, View, Edit, Delete, Document, UploadFilled } from '@element-plus/icons-vue'
import { listCustomers, createCustomer, updateCustomer, deleteCustomer } from '@/api/biz/customer'

const loading = ref(false)
const list = ref([])
const keyword = ref('')
const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return list.value
  return list.value.filter((c) =>
    [c.customerName, c.customerCode, c.contactName].filter(Boolean).some((v) => String(v).toLowerCase().includes(kw))
  )
})

async function load() {
  loading.value = true
  try {
    list.value = await listCustomers()
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref()
const emptyForm = () => ({
  customerCode: '', customerName: '', contactName: '', contactPhone: '', address: '',
  qualificationFiles: [], remark: ''
})
const form = reactive(emptyForm())
const rules = {
  customerCode: [{ required: false, message: '客户业务编号可留空自动生成', trigger: 'blur' }],
  customerName: [{ required: true, message: '请输入客户名称', trigger: 'blur' }]
}
function openCreate() {
  isEdit.value = false; editingId.value = null
  Object.assign(form, emptyForm()); formRef.value?.clearValidate?.(); dialogVisible.value = true
}
function openEdit(row) {
  isEdit.value = true; editingId.value = row.id
  Object.assign(form, {
    customerCode: row.customerCode, customerName: row.customerName, contactName: row.contactName, contactPhone: row.contactPhone,
    address: row.address, qualificationFiles: [...(row.qualificationFiles || [])], remark: row.remark
  })
  formRef.value?.clearValidate?.(); dialogVisible.value = true
}
function onFileChange(file) {
  form.qualificationFiles.push({ name: file.name, url: '' })
  ElMessage.success(`已添加附件：${file.name}（演示）`)
}
async function onSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      const { customerCode, ...rest } = form
      await updateCustomer(editingId.value, { ...rest })
      ElMessage.success('修改成功')
    } else {
      await createCustomer({ ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false; load()
  } catch {
    // error already handled by request
  } finally { saving.value = false }
}
async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除客户「${row.customerName}」吗？`, '删除确认', { type: 'warning' })
  } catch { return }
  await deleteCustomer(row.id); ElMessage.success('删除成功'); load()
}

const viewVisible = ref(false)
const current = ref(null)
function openView(row) { current.value = row; viewVisible.value = true }

onMounted(load)
</script>

<style scoped lang="scss">
.card-header { display: flex; justify-content: space-between; align-items: center; }
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; gap: 12px; }
.search-input { max-width: 320px; }
.muted { color: #c0c4cc; }
.files { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.file-tag { display: inline-flex; align-items: center; gap: 4px; }
.file-line { display: flex; align-items: center; gap: 6px; padding: 3px 0; }
</style>
