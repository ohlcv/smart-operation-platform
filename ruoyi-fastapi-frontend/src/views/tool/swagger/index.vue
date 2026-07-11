<template>
  <i-frame v-model:src="url"></i-frame>
</template>

<script setup>
import iFrame from '@/components/iFrame'

// 直接走 '/proxy-docs'（不走 '/dev-api' 前缀），原因见
// docs/04-开发/DEBUG/swagger-ui-relative-openapi-yaml-exception-2026-07-11.md：
// 走 '/dev-api/proxy-docs' 时，swagger UI HTML 内的相对路径 '/openapi.json' 会被
// iframe 浏览器解析为 'http://<frontend-host>/openapi.json'（丢失 /dev-api 前缀），
// 走到 Vite SPA fallback 而非后端 → 触发 YAMLException。
// 因此 vite.config.js 中把 '/proxy-docs'、'/openapi.json'、'/proxy-openapi.json'
// 都做了同源代理，这里直接用 '/proxy-docs' 让整条链路走同一套代理规则。
const url = ref('/proxy-docs')
</script>
