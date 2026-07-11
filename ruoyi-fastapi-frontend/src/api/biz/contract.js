import request from '@/utils/request'

export function listContracts(params) {
  return request({ url: '/biz/contracts', method: 'get', params })
}

export function getContract(id) {
  return request({ url: `/biz/contracts/${id}`, method: 'get' })
}

export function createContract(data) {
  return request({ url: '/biz/contracts', method: 'post', data })
}

export function updateContract(id, data) {
  return request({ url: `/biz/contracts/${id}`, method: 'put', data })
}

export function deleteContract(id) {
  return request({ url: `/biz/contracts/${id}`, method: 'delete' })
}

export function submitContract(id) {
  return request({ url: `/biz/contracts/${id}/submit`, method: 'post' })
}
