import request from '@/utils/request'

/**
 * 战略驾驶舱 API
 * 路径：
 *   GET /biz/cockpit/overview       驾驶舱总览（支持 province 查询参数）
 *   GET /biz/cockpit/ai-diagnose    AI 智能大脑
 *
 * 字段命名遵循 ADR D24：JSON 一律 camelCase
 *
 * v3.3 路线 C：
 *   - overview 加 province 参数（点地图省份时过滤 KPI/趋势/Top10/状态分布）
 *   - 新增 aiDiagnose 返回 6 维雷达 + 风险 + 建议
 */
export function getCockpitOverview(params = {}) {
  return request({ url: '/biz/cockpit/overview', method: 'get', params })
}

export function getCockpitAiDiagnose() {
  return request({ url: '/biz/cockpit/ai-diagnose', method: 'get' })
}