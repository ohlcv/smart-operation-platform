import request from '@/utils/request'

export function listCustomers(params) {
  return request({ url: '/biz/customers', method: 'get', params })
}

export function getCustomer(id) {
  return request({ url: `/biz/customers/${id}`, method: 'get' })
}

export function createCustomer(data) {
  return request({ url: '/biz/customers', method: 'post', data })
}

export function updateCustomer(id, data) {
  return request({ url: `/biz/customers/${id}`, method: 'put', data })
}

export function deleteCustomer(id) {
  return request({ url: `/biz/customers/${id}`, method: 'delete' })
}
