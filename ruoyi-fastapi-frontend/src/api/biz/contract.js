import request from '@/utils/request'

/**
 * 合同管理 API
 * 路径严格遵循 docs/03-设计/API设计文档.md §五（/biz/contract，不是 /biz/contracts）
 * 字段命名遵循 docs/04-开发/ARD/ADR-架构决策记录.md D24：JSON 一律 camelCase
 * 列表接口返回 RuoYi 标准分页响应 { code, msg, rows, total, pageNum, pageSize }，
 * 调用方需取 res.rows。
 */
export function listContracts(params) {
  return request({ url: '/biz/contract/list', method: 'get', params })
}

export function listMyContracts(params) {
  return request({ url: '/biz/contract/my-list', method: 'get', params })
}

export function getContract(id) {
  return request({ url: `/biz/contract/${id}`, method: 'get' })
}

export function createContract(data) {
  return request({ url: '/biz/contract', method: 'post', data })
}

export function updateContract(id, data) {
  // 后端约定：用 ?contract_id=ID 的 query 形式传递 ID（与 RuoYi 一致）
  return request({ url: `/biz/contract?contract_id=${id}`, method: 'put', data })
}

export function deleteContract(id) {
  return request({ url: `/biz/contract/${id}`, method: 'delete' })
}

export function submitContract(id) {
  return request({ url: `/biz/contract/submit/${id}`, method: 'post' })
}

export function checkContractNo(contractNo, excludeId) {
  return request({ url: '/biz/contract/check-no', method: 'get', params: { contractNo, excludeId } })
}