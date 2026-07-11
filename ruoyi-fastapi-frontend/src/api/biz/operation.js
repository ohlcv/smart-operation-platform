import request from '@/utils/request'

/**
 * 经营数据 API
 * 路径 /biz/operation
 * 字段命名遵循 ADR D24
 */

export function listOperations(params) {
  return request({ url: '/biz/operation/list', method: 'get', params })
}

export function getOperation(id) {
  return request({ url: `/biz/operation/${id}`, method: 'get' })
}

export function createOperation(data) {
  return request({ url: '/biz/operation', method: 'post', data })
}

export function updateOperation(id, data) {
  return request({ url: `/biz/operation?op_id=${id}`, method: 'put', data })
}

export function deleteOperation(id) {
  return request({ url: `/biz/operation/${id}`, method: 'delete' })
}

export function getOperationComparison(params) {
  return request({ url: '/biz/operation/comparison', method: 'get', params })
}

export function getOperationOptions() {
  return request({ url: '/biz/operation/options', method: 'get' })
}