<template>
  <div class="app-container">
    <div class="biz-placeholder">
      <h2>战略驾驶舱</h2>
      <p>经营总览、合同统计、渠道分析</p>
      <!-- TODO: 实现驾驶舱页面（复用 v1 screen 模块） -->
    </div>
  </div>
</template>

<script setup name="BizCockpitIndex">
// TODO: 接入驾驶舱大屏（复用 v1 DataScreen/ScreenMap/BaseChart）
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
