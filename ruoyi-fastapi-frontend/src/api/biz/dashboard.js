import request from '@/utils/request'

/**
 * 仪表盘 API
 * 路径：
 *   GET /biz/dashboard/overview       仪表盘总览（支持 province 查询参数）
 *   GET /biz/dashboard/ai-diagnose    AI 智能大脑
 *
 * 字段命名遵循 ADR D24：JSON 一律 camelCase
 */
export function getDashboardOverview(params = {}, config = {}) {
  return request({ url: '/biz/dashboard/overview', method: 'get', params, ...config })
}

export function getDashboardAiDiagnose(config = {}) {
  return request({ url: '/biz/dashboard/ai-diagnose', method: 'get', ...config })
}