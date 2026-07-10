<template>
  <div class="app-container">
    <div class="biz-placeholder">
      <h2>审批记录</h2>
      <p>待我审批、已审批、审批历史</p>
      <!-- TODO: 实现审批管理页面 -->
    </div>
  </div>
</template>

<script setup name="BizApprovalIndex">
// TODO: 接入审批列表、审批通过/驳回功能
</script>

<style scoped>
.biz-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #909399;
}
.biz-placeholder h2 {
  margin-bottom: 8px;
  color: #303133;
}
</style>
