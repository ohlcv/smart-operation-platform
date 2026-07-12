<template>
  <div class="screen-map">
    <div v-if="loading" class="map-overlay">地图加载中...</div>
    <div v-if="fallback" class="map-fallback">
      地图资源离线，散点视图暂不可用（其余大屏功能正常）
    </div>
    <div ref="chartRef" class="map-canvas" :style="{ height }"></div>
  </div>
</template>

<script setup>
/**
 * 仪表盘地图组件（v3.3 路线 C 升级：省份联动 + 真实坐标 + 中枢高亮）
 *
 * 特性：
 * - demo1 同款：effectScatter 节点 + lines 物流飞线 + 中枢高亮（hub 默认北京）
 * - province-click 事件：点击省份时 emit 给父组件做 KPI 联动
 * - hub 可配置（demo1 默认「山东省」，本项目统一改「北京」作为集团总部所在地）
 *
 * 与 /biz/dashboard/overview 的 channel_locations 数据契约：
 *   { channelId, channelName, lng, lat, contractCount, city }
 */
import { ref, shallowRef, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  height: { type: String, default: '500px' },
  hub: { type: String, default: '北京' }
})
const emit = defineEmits(['province-click'])

const chartRef = ref(null)
const chart = shallowRef(null)
const loading = ref(false)
const fallback = ref(false)

// 省份近似经纬度（demo1 GEO 表扩展，覆盖本项目演示数据）
const GEO = {
  '北京': [116.40, 39.90], '上海': [121.47, 31.23], '天津': [117.20, 39.13],
  '重庆': [106.55, 29.56], '广东': [113.27, 23.13], '广州': [113.27, 23.13],
  '深圳': [114.06, 22.54], '浙江': [120.15, 30.27], '杭州': [120.15, 30.27],
  '江苏': [118.79, 32.06], '南京': [118.79, 32.06], '苏州': [120.62, 31.32],
  '山东': [117.00, 36.65], '济南': [117.00, 36.65], '青岛': [120.38, 36.07],
  '四川': [104.06, 30.67], '成都': [104.06, 30.67], '湖北': [114.30, 30.59],
  '武汉': [114.30, 30.59], '陕西': [108.94, 34.34], '西安': [108.94, 34.34],
  '河南': [113.65, 34.76], '郑州': [113.65, 34.76], '福建': [119.30, 26.08],
  '厦门': [118.10, 24.49], '辽宁': [123.43, 41.80], '大连': [121.62, 38.92],
  '河北': [114.50, 38.05], '石家庄': [114.50, 38.05], '湖南': [112.98, 28.11],
  '广西': [108.33, 22.84], '云南': [102.71, 25.04], '贵州': [106.71, 26.57]
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
  const max = Math.max(1, ...(props.data || []).map((d) => Number(d.contractCount || 1)))

  // 节点散点（按渠道坐标）
  const scatter = (props.data || [])
    .filter((d) => d.lng && d.lat)
    .map((d) => ({
      name: d.channelName,
      value: [d.lng, d.lat, d.contractCount || 1],
      city: d.city,
      province: d.province || d.city
    }))

  // 物流飞线（hub → 各渠道）
  const hubCoord = GEO[props.hub] || GEO['北京']
  const lines = scatter
    .filter((s) => GEO[s.province])
    .map((s) => ({
      coords: [hubCoord, [s.value[0], s.value[1]]],
      val: s.value[2]
    }))

  // 省份级聚合（用于点击省份触发联动）
  const provinceAgg = new Map()
  scatter.forEach((s) => {
    const p = s.province
    if (!p || !GEO[p]) return
    if (!provinceAgg.has(p)) {
      provinceAgg.set(p, { name: p, value: 0, count: 0 })
    }
    provinceAgg.get(p).value += s.value[2] || 1
    provinceAgg.get(p).count += 1
  })
  const provinceData = Array.from(provinceAgg.values())

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 30, 80, 0.9)',
      borderColor: '#00f2ff',
      textStyle: { color: '#fff' },
      formatter: (p) => {
        if (p.seriesType === 'effectScatter' && Array.isArray(p.value)) {
          return `${p.name}<br/>合同数: ${p.value[2] || 0}<br/>城市: ${p.data.city || ''}`
        }
        return `${p.name}<br/>合同数: ${p.value || 0}`
      }
    },
    visualMap: provinceData.length
      ? {
          show: true,
          min: 0,
          max: Math.max(...provinceData.map((d) => d.value), 1),
          left: 16,
          bottom: 16,
          calculable: true,
          inRange: { color: ['#1c3a66', '#1f6fbb', '#00d4ff', '#00f2ff'] },
          text: ['高', '低'],
          textStyle: { color: '#a0c4ff' }
        }
      : undefined,
    geo: {
      map: 'china',
      roam: false,
      zoom: 1.2,
      label: { show: false },
      itemStyle: {
        areaColor: 'rgba(0, 30, 80, 0.4)',
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
    series: [
      // 省份着色（基于聚合数据）
      {
        name: '省份分布',
        type: 'map',
        map: 'china',
        geoIndex: 0,
        data: provinceData
      },
      // 物流飞线
      {
        name: '物流飞线',
        type: 'lines',
        coordinateSystem: 'geo',
        zlevel: 2,
        effect: { show: true, period: 5, trailLength: 0.55, symbol: 'arrow', symbolSize: 6, color: '#39c5ff' },
        lineStyle: { color: '#00f2ff', width: 1.2, opacity: 0.55, curveness: 0.25 },
        data: lines
      },
      // 渠道节点
      {
        name: '渠道节点',
        type: 'effectScatter',
        coordinateSystem: 'geo',
        zlevel: 3,
        rippleEffect: { brushType: 'stroke', scale: 4 },
        symbolSize: (val) => Math.max(8, Math.min((val[2] || 1) * 4, 30)),
        itemStyle: { color: '#ff4081', shadowBlur: 10, shadowColor: '#ff4081' },
        label: { show: true, color: '#fff', formatter: '{b}', position: 'top' },
        data: scatter
      },
      // 中枢高亮（hub）
      {
        name: '中枢',
        type: 'effectScatter',
        coordinateSystem: 'geo',
        zlevel: 4,
        rippleEffect: { brushType: 'stroke', scale: 6 },
        symbolSize: 16,
        itemStyle: { color: '#ffd34e', shadowBlur: 16, shadowColor: '#ffd34e' },
        data: [{ name: props.hub, value: [...hubCoord, max] }]
      }
    ]
  }
}

async function render() {
  if (!chart.value) return
  const hasMap = await ensureMap()
  fallback.value = !hasMap
  if (!hasMap) {
    chart.value.clear()
    return
  }
  chart.value.setOption(buildOption(), true)

  // 省份点击 → emit
  chart.value.off('click')
  chart.value.on('click', (p) => {
    if (p.name && GEO[p.name] && p.name !== props.hub) {
      emit('province-click', p.name)
    }
  })
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
</style>