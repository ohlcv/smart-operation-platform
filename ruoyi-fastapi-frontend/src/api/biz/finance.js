import request from '@/utils/request'

/**
 * 财务管理 API
 * 路径 /biz/finance
 * 字段命名遵循 ADR D24
 */

export function listFinances(params) {
  return request({ url: '/biz/finance/list', method: 'get', params })
}

export function getFinance(id) {
  return request({ url: `/biz/finance/${id}`, method: 'get' })
}

export function createFinance(data) {
  return request({ url: '/biz/finance', method: 'post', data })
}

export function updateFinance(id, data) {
  return request({ url: `/biz/finance?entry_id=${id}`, method: 'put', data })
}

export function deleteFinance(id) {
  return request({ url: `/biz/finance/${id}`, method: 'delete' })
}

export function clearFinance(id) {
  return request({ url: `/biz/finance/clear/${id}`, method: 'post' })
}

export function getFinanceSummary(period) {
  return request({ url: '/biz/finance/summary', method: 'get', params: { period } })
}

export function importBankStatement(data) {
  return request({ url: '/biz/finance/import-bank', method: 'post', data })
}

export function getFinanceOptions() {
  return request({ url: '/biz/finance/options', method: 'get' })
}