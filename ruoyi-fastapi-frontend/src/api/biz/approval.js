import request from '@/utils/request'

/**
 * 审批中心 API
 * 路径严格遵循 docs/03-设计/API设计文档.md §六
 * 字段命名遵循 ADR D24：JSON 一律 camelCase
 */

/**
 * 获取审批列表
 * @param {Object} params - { scope: 'pending'|'processed'|'submitted', pageNum, pageSize, contractNo, title, currentStep, keyword, ... }
 */
export function listApprovals(params) {
  return request({ url: '/biz/approval/list', method: 'get', params })
}

/**
 * 获取合同审批历史
 * @param {number} contractId
 */
export function getApprovalHistory(contractId) {
  return request({ url: `/biz/approval/history/${contractId}`, method: 'get' })
}

/**
 * 审批通过
 * @param {number} contractId
 * @param {Object} data - { action: 'approve', comment: '审批意见（可选）' }
 */
export function approveContract(contractId, data) {
  return request({ url: `/biz/approval/approve/${contractId}`, method: 'post', data })
}

/**
 * 审批驳回
 * @param {number} contractId
 * @param {Object} data - { action: 'reject', comment: '审批意见', rejectReason: '驳回原因' }
 */
export function rejectContract(contractId, data) {
  return request({ url: `/biz/approval/reject/${contractId}`, method: 'post', data })
}