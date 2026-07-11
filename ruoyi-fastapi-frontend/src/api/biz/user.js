import request from '@/utils/request'

/**
 * 当前用户 API（个人中心）
 * 路径严格遵循 RuoYi 系统约定：/system/user/profile/*
 */

/** 获取当前用户个人信息（含 signature） */
export function getUserProfile() {
  return request({ url: '/system/user/profile', method: 'get' })
}

/** 上传/更新本人电子签名（base64 data URI，传 null/空串可清除） */
export function updateSignature(signature) {
  return request({
    url: '/system/user/profile/signature',
    method: 'put',
    data: { signature }
  })
}

/** 修改当前用户密码 */
export function updateUserPassword(oldPassword, newPassword) {
  return request({
    url: '/system/user/profile/updatePwd',
    method: 'put',
    params: { oldPassword, newPassword }
  })
}