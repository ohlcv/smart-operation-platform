<template>
  <div class="screen-map">
    <div v-if="loading" class="map-overlay">地图加载中...</div>
    <div v-if="fallback" class="map-fallback">地图资源离线，显示散点列表（坐标视图可用）</div>
    <div ref="chartRef" class="map-canvas" :style="{ height }"></div>
    <div v-if="points && points.length" class="map-points-list">
      <div class="points-title">渠道分布（数据点）</div>
      <div class="points-grid">
        <div v-for="p in points" :key="p.channelId || p.channelName" class="points-item">
          <span class="points-name">{{ p.channelName }}</span>
          <span class="points-city">{{ p.city || '—' }}</span>
          <span class="points-count">{{ p.contractCount }} 单</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  height: { type: String, default: '500px' }
})

const chartRef = ref(null)
const chart = shallowRef(null)
const loading = ref(false)
const fallback = ref(false)

const points = props.data

const GEO = {
  '北京': [116.40, 39.90], '上海': [121.47, 31.23], '广州': [113.27, 23.13],
  '深圳': [114.06, 22.54], '杭州': [120.15, 30.27], '成都': [104.06, 30.67],
  '南京': [118.79, 32.06], '武汉': [114.30, 30.59], '西安': [108.94, 34.34],
  '重庆': [106.55, 29.56], '青岛': [120.38, 36.07], '苏州': [120.62, 31.32],
  '济南': [117.00, 36.65], '郑州': [113.65, 34.76]
}

async function ensureMap() {
  if (echarts.getMap('china')) return true
  loading.value = true
  try {
    const resp = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
    if (!resp.ok) throw new Error('fetch failed')
    const json = await resp.json()
    echarts.registerMap('china', json)
    return true
  } catch (e) {
    return false
  } finally {
    loading.value = false
  }
}

function buildOption() {
  const scatter = (props.data || [])
    .filter((d) => GEO[d.city || d.channelName])
    .map((d) => ({
      name: d.channelName,
      value: [...(GEO[d.city || d.channelName] || [0, 0]), d.contractCount || 1]
    }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0,30,80,0.9)',
      borderColor: '#00f2ff',
      textStyle: { color: '#fff' },
      formatter: (p) => `${p.name}<br/>合同数: ${p.value[2] || 0}`
    },
    geo: {
      map: 'china',
      roam: false,
      zoom: 1.2,
      label: { show: false },
      itemStyle: {
        areaColor: 'rgba(0, 50, 100, 0.3)',
        borderColor: '#00f2ff',
        borderWidth: 1,
        shadowColor: 'rgba(0, 242, 255, 0.5)',
        shadowBlur: 10
      },
      emphasis: {
        itemStyle: { areaColor: '#0099ff' },
        label: { show: true, color: '#fff' }
      }
    },
    series: [{
      type: 'effectScatter',
      coordinateSystem: 'geo',
      data: scatter,
      showEffectOn: 'render',
      rippleEffect: { brushType: 'stroke', scale: 4 },
      symbolSize: (val) => Math.max(8, Math.min((val[2] || 1) * 4, 30)),
      itemStyle: {
        color: '#ff4081',
        shadowBlur: 10,
        shadowColor: '#ff4081'
      },
      label: { show: true, color: '#fff', formatter: '{b}', position: 'top' }
    }]
  }
}

async function render() {
  if (!chart.value) return
  const hasMap = await ensureMap()
  if (!hasMap) {
    fallback.value = true
  }
  chart.value.setOption(buildOption(), true)
}

async function init() {
  if (!chartRef.value) return
  chart.value = echarts.init(chartRef.value, null, { renderer: 'canvas' })
  await render()
}

function handleResize() {
  chart.value?.resize()
}

onMounted(() => {
  nextTick(init)
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart.value?.dispose()
  chart.value = null
})

watch(() => props.data, () => render(), { deep: true })
</script>

<style scoped>
.screen-map {
  position: relative;
  width: 100%;
}

.map-canvas {
  width: 100%;
  background: rgba(0, 20, 60, 0.4);
  border-radius: 4px;
}

.map-overlay,
.map-fallback {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  color: #00f2ff;
  background: rgba(0, 30, 80, 0.8);
  padding: 12px 24px;
  border-radius: 4px;
  border: 1px solid #00f2ff;
  z-index: 2;
}

.map-points-list {
  margin-top: 16px;
  padding: 12px;
  background: rgba(0, 30, 80, 0.4);
  border-radius: 4px;
  border: 1px solid rgba(0, 242, 255, 0.3);
}

.points-title {
  color: #a0c4ff;
  font-size: 13px;
  margin-bottom: 8px;
}

.points-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.points-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px;
  background: rgba(0, 50, 100, 0.5);
  border-radius: 4px;
  font-size: 12px;
}

.points-name {
  color: #fff;
  font-weight: 600;
}

.points-city {
  color: #a0c4ff;
  margin-left: 8px;
}

.points-count {
  color: #00f2ff;
  margin-left: 8px;
}
</style>