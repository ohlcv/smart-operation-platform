<template>
  <span ref="elRef" class="count-to" :class="{ 'count-to--gradient': gradient }">{{ displayValue }}</span>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  target: { type: Number, default: 0 },
  duration: { type: Number, default: 1500 },
  decimals: { type: Number, default: 0 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  separator: { type: String, default: ',' },
  gradient: { type: Boolean, default: true }
})

const displayValue = ref(formatNumber(0))
let rafId = null

function formatNumber(n) {
  const fixed = Number(n).toFixed(props.decimals)
  const [intPart, decPart] = fixed.split('.')
  const formatted = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, props.separator)
  return props.prefix + (decPart ? formatted + '.' + decPart : formatted) + props.suffix
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
}

function animate() {
  if (rafId) cancelAnimationFrame(rafId)
  const from = 0
  const to = Number(props.target) || 0
  if (to === 0) {
    displayValue.value = formatNumber(0)
    return
  }
  const start = performance.now()
  function step(now) {
    const elapsed = now - start
    const progress = Math.min(elapsed / props.duration, 1)
    const current = from + (to - from) * easeOutCubic(progress)
    displayValue.value = formatNumber(current)
    if (progress < 1) {
      rafId = requestAnimationFrame(step)
    } else {
      displayValue.value = formatNumber(to)
      rafId = null
    }
  }
  rafId = requestAnimationFrame(step)
}

onMounted(() => animate())

watch(() => props.target, () => animate())
</script>

<style scoped>
.count-to {
  display: inline-block;
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  color: #00f2ff;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.count-to--gradient {
  background: linear-gradient(180deg, #ffffff 0%, #00f2ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}
</style>