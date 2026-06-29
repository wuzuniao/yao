import { request } from '../request'

/**
 * 发送注册验证码
 * @param {string} email 收件人邮箱（用户注册表单填写的电子邮箱）
 */
export function sendRegisterCode(email) {
  return request({
    url: '/api/v1/users/send-code',
    method: 'POST',
    data: { email }
  })
}

/**
 * 用户注册
 * @param {Object} param0 注册表单数据
 * @param {string} param0.username 用户名
 * @param {string} param0.password 密码
 * @param {string} param0.email 电子邮箱
 * @param {string} param0.code 验证码
 */
export function registerUser({ username, password, email, code }) {
  return request({
    url: '/api/v1/users/register',
    method: 'POST',
    data: { username, password, email, code }
  })
}

/**
 * 用户登录
 * @param {Object} param0 登录表单数据
 * @param {string} param0.username 用户名或邮箱
 * @param {string} param0.password 密码
 */
export function loginUser({ username, password }) {
  return request({
    url: '/api/v1/users/login',
    method: 'POST',
    data: { username, password }
  })
}

/**
 * 发送密码找回验证码
 * @param {string} email 收件人邮箱
 */
export function sendResetCode(email) {
  return request({
    url: '/api/v1/users/send-reset-code',
    method: 'POST',
    data: { email }
  })
}

/**
 * 重置密码
 * @param {Object} param0 重置密码表单数据
 * @param {string} param0.email 邮箱
 * @param {string} param0.code 验证码
 * @param {string} param0.new_password 新密码
 */
export function resetPassword({ email, code, new_password }) {
  return request({
    url: '/api/v1/users/reset-password',
    method: 'POST',
    data: { email, code, new_password }
  })
}

/**
 * 更新用户签名
 * @param {Object} param0 更新签名数据
 * @param {number} param0.user_id 用户ID
 * @param {string} param0.signature 新签名
 */
export function updateSignature({ user_id, signature }) {
  return request({
    url: '/api/v1/users/update-signature',
    method: 'PUT',
    data: { user_id, signature }
  })
}

/**
 * 修改密码
 * @param {Object} param0 修改密码数据
 * @param {number} param0.user_id 用户ID
 * @param {string} param0.old_password 旧密码
 * @param {string} param0.new_password 新密码
 */
export function changePassword({ user_id, old_password, new_password }) {
  return request({
    url: '/api/v1/users/change-password',
    method: 'PUT',
    data: { user_id, old_password, new_password }
  })
}

/**
 * 发送修改邮箱的旧邮箱验证码
 * @param {number} user_id 用户ID
 */
export function sendChangeEmailOldCode(user_id) {
  return request({
    url: '/api/v1/users/send-change-email-old-code',
    method: 'POST',
    data: { user_id }
  })
}

/**
 * 发送修改邮箱的新邮箱验证码
 * @param {string} new_email 新邮箱地址
 */
export function sendChangeEmailNewCode(new_email) {
  return request({
    url: '/api/v1/users/send-change-email-new-code',
    method: 'POST',
    data: { new_email }
  })
}

/**
 * 修改邮箱
 * @param {Object} param0 修改邮箱数据
 * @param {number} param0.user_id 用户ID
 * @param {string} param0.old_code 旧邮箱验证码
 * @param {string} param0.new_email 新邮箱地址
 * @param {string} param0.new_code 新邮箱验证码
 */
export function changeEmail({ user_id, old_code, new_email, new_code }) {
  return request({
    url: '/api/v1/users/change-email',
    method: 'PUT',
    data: { user_id, old_code, new_email, new_code }
  })
}
