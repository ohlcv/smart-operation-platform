import request from '@/utils/request'

/**
 * 渠道管理 API
 * 路径严格遵循 docs/03-设计/API设计文档.md §五（/biz/channel）
 * 字段命名遵循 docs/04-开发/ARD/ADR-架构决策记录.md D24：JSON 一律 camelCase
 * 列表接口返回 RuoYi 标准分页响应 { code, msg, rows, total, pageNum, pageSize }，
 * 调用方需取 res.rows。
 */

export function listChannels(params) {
  return request({ url: '/biz/channel/list', method: 'get', params })
}

export function getChannel(id) {
  return request({ url: `/biz/channel/${id}`, method: 'get' })
}

export function createChannel(data) {
  return request({ url: '/biz/channel', method: 'post', data })
}

export function updateChannel(id, data) {
  return request({ url: `/biz/channel?channel_id=${id}`, method: 'put', data })
}

export function deleteChannel(id) {
  return request({ url: `/biz/channel/${id}`, method: 'delete' })
}

export function getChannelCategoryOptions() {
  return request({ url: '/biz/channel/category-options', method: 'get' })
}

export function importChannels(data) {
  return request({ url: '/biz/channel/import', method: 'post', data })
}
