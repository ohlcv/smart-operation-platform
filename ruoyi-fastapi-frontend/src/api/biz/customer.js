import request from '@/utils/request'

/**
 * 客户管理 API
 * 路径严格遵循 docs/03-设计/API设计文档.md §七（/biz/customer，不是 /biz/customers）
 * 列表接口返回 RuoYi 标准分页响应 { code, msg, rows, total, pageNum, pageSize }，
 * 调用方需取 res.rows。字段命名遵循 ADR D24（camelCase）。
 */
export function listCustomers(params) {
  return request({ url: '/biz/customer/list', method: 'get', params })
}

export function getCustomer(id) {
  return request({ url: `/biz/customer/${id}`, method: 'get' })
}

export function createCustomer(data) {
  return request({ url: '/biz/customer', method: 'post', data })
}

export function updateCustomer(id, data) {
  // 后端约定：用 ?customer_id=ID 的 query 形式传递 ID（与 RuoYi 一致）
  return request({ url: `/biz/customer?customer_id=${id}`, method: 'put', data })
}

export function deleteCustomer(id) {
  return request({ url: `/biz/customer/${id}`, method: 'delete' })
}