<template>
  <div ref="chartRef" class="base-chart" :style="{ width, height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import {
  BarChart,
  LineChart,
  PieChart,
  RadarChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DatasetComponent,
  TransformComponent,
  GeoComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart, LineChart, PieChart, RadarChart,
  TitleComponent, TooltipComponent, GridComponent, LegendComponent,
  DatasetComponent, TransformComponent, GeoComponent,
  CanvasRenderer
])

const props = defineProps({
  type: { type: String, default: 'bar' }, // bar / line / pie / radar
  data: { type: [Array, Object], default: () => [] },
  categories: { type: Array, default: () => [] },
  option: { type: Object, default: () => ({}) },
  title: { type: String, default: '' },
  width: { type: String, default: '100%' },
  height: { type: String, default: '280px' },
  loading: { type: Boolean, default: false }
})

const chartRef = ref(null)
let chartInstance = null

const TECH_COLORS = ['#00f2ff', '#00d4ff', '#0099ff', '#7c4dff', '#ff4081', '#ff9c00', '#36cfc9']
const AXIS_LINE_COLOR = '#4a6584'
const AXIS_LABEL_COLOR = '#a0c4ff'
const SPLIT_LINE_COLOR = 'rgba(74, 101, 132, 0.2)'

function buildOption() {
  const baseTitle = props.title
    ? { title: { text: props.title, left: 'left', textStyle: { color: '#fff', fontSize: 14 } } }
    : {}

  if (props.type === 'bar') {
    return {
      ...baseTitle,
      grid: { left: 50, right: 20, top: props.title ? 40 : 20, bottom: 40 },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,30,80,0.9)', borderColor: '#00f2ff', textStyle: { color: '#fff' } },
      xAxis: {
        type: 'category', data: props.categories,
        axisLine: { lineStyle: { color: AXIS_LINE_COLOR } },
        axisLabel: { color: AXIS_LABEL_COLOR, rotate: props.categories.length > 6 ? 30 : 0 }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: AXIS_LINE_COLOR } },
        axisLabel: { color: AXIS_LABEL_COLOR },
        splitLine: { lineStyle: { color: SPLIT_LINE_COLOR } }
      },
      series: [{
        type: 'bar', data: props.data, barMaxWidth: 30,
        itemStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: '#00f2ff' }, { offset: 1, color: '#0099ff' }]
          },
          borderRadius: [4, 4, 0, 0]
        }
      }]
    }
  }

  if (props.type === 'line') {
    return {
      ...baseTitle,
      grid: { left: 50, right: 20, top: props.title ? 40 : 20, bottom: 40 },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,30,80,0.9)', borderColor: '#00f2ff', textStyle: { color: '#fff' } },
      xAxis: {
        type: 'category', data: props.categories,
        axisLine: { lineStyle: { color: AXIS_LINE_COLOR } },
        axisLabel: { color: AXIS_LABEL_COLOR }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: AXIS_LINE_COLOR } },
        axisLabel: { color: AXIS_LABEL_COLOR },
        splitLine: { lineStyle: { color: SPLIT_LINE_COLOR } }
      },
      series: [{
        type: 'line', data: props.data, smooth: true, symbolSize: 6,
        lineStyle: { color: '#00f2ff', width: 2 },
        itemStyle: { color: '#00f2ff' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(0,242,255,0.4)' }, { offset: 1, color: 'rgba(0,242,255,0)' }]
          }
        }
      }]
    }
  }

  if (props.type === 'pie') {
    const seriesData = (props.data || []).map((d, i) => ({
      name: d.label || d.name || (props.categories[i] || ''),
      value: d.value !== undefined ? d.value : d
    }))
    return {
      ...baseTitle,
      tooltip: { trigger: 'item', backgroundColor: 'rgba(0,30,80,0.9)', borderColor: '#00f2ff', textStyle: { color: '#fff' }, formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: AXIS_LABEL_COLOR } },
      series: [{
        type: 'pie', radius: ['45%', '70%'], center: ['38%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: { borderColor: '#0a1a3a', borderWidth: 2 },
        label: { color: AXIS_LABEL_COLOR, formatter: '{b}\n{d}%' },
        data: seriesData
      }],
      color: TECH_COLORS
    }
  }

  if (props.type === 'radar') {
    return {
      ...baseTitle,
      tooltip: { backgroundColor: 'rgba(0,30,80,0.9)', borderColor: '#00f2ff', textStyle: { color: '#fff' } },
      radar: { indicator: props.categories, axisName: { color: AXIS_LABEL_COLOR }, splitLine: { lineStyle: { color: SPLIT_LINE_COLOR } } },
      series: [{ type: 'radar', data: [{ value: props.data, name: '' }], lineStyle: { color: '#00f2ff' }, areaStyle: { color: 'rgba(0,242,255,0.3)' } }]
    }
  }

  return {}
}

function render() {
  if (!chartInstance) return
  const opt = buildOption()
  chartInstance.setOption({ ...opt, ...props.option }, true)
}

function init() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value, null, { renderer: 'canvas' })
  render()
}

function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  nextTick(init)
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

watch(() => [props.data, props.categories, props.option, props.type], () => render(), { deep: true })
watch(() => props.loading, (v) => {
  if (chartInstance) v ? chartInstance.showLoading() : chartInstance.hideLoading()
})
</script>

<style scoped>
.base-chart {
  width: 100%;
}
</style>