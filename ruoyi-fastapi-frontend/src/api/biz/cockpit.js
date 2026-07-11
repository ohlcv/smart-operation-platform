import request from '@/utils/request'

/**
 * 战略驾驶舱 API
 * 路径：/biz/cockpit/overview（详见 module_biz/controller/cockpit_controller.py）
 * 字段命名遵循 ADR D24：JSON 一律 camelCase
 */
export function getCockpitOverview() {
  return request({ url: '/biz/cockpit/overview', method: 'get' })
}