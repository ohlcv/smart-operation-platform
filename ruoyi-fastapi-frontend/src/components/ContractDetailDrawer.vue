<template>
  <el-drawer v-model="visible" title="合同详情" size="680px" direction="rtl">
    <el-empty description="合同详情组件，待后端接口实现后接入" />
  </el-drawer>
</template>

<script setup>
/**
 * 合同详情抽屉（占位）
 *
 * 字段命名遵循 ADR D24：后端返回 camelCase。
 * 后续接入 controller 时，按以下字段取数：
 *   id, contractNo, title, contractType, contractTypeLabel, partyA, partyB,
 *   amount, signDate, department, businessType, customerId, customerName,
 *   status, statusLabel, currentStep, currentRole, currentRoleLabel,
 *   rejectCount, createdBy, createdByName, createTime, updateTime, remark, attachments
 */
import { computed } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  contractId: [String, Number]
})
const emit = defineEmits(['update:modelValue'])
const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})
</script>