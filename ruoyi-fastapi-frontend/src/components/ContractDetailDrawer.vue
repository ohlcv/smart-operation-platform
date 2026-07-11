<template>
  <el-drawer v-model="visible" title="合同详情" size="680px" direction="rtl">
    <el-empty description="合同详情组件，待后端接口实现后接入" />
  </el-drawer>
</template>

<script setup>
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
