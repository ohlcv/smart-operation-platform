import request from '@/utils/request'

/**
 * 发票管理 API
 * 路径 /biz/invoice
 * 字段命名遵循 ADR D24
 */

export function listInvoices(params) {
  return request({ url: '/biz/invoice/list', method: 'get', params })
}

export function getInvoice(id) {
  return request({ url: `/biz/invoice/${id}`, method: 'get' })
}

export function createInvoice(data) {
  return request({ url: '/biz/invoice', method: 'post', data })
}

export function updateInvoice(id, data) {
  return request({ url: `/biz/invoice?invoice_id=${id}`, method: 'put', data })
}

export function deleteInvoice(id) {
  return request({ url: `/biz/invoice/${id}`, method: 'delete' })
}

export function issueInvoice(id, issueDate) {
  const params = issueDate ? { issueDate } : {}
  return request({ url: `/biz/invoice/issue/${id}`, method: 'post', params })
}

export function voidInvoice(id, reason) {
  return request({ url: `/biz/invoice/void/${id}`, method: 'post', data: { reason } })
}

export function getInvoiceOptions() {
  return request({ url: '/biz/invoice/options', method: 'get' })
}
