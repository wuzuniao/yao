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
 * 更新用户签名（user_id 由 JWT 提供，无需前端传递）
 * @param {Object} param0 更新签名数据
 * @param {string} param0.signature 新签名
 */
export function updateSignature({ signature }) {
  return request({
    url: '/api/v1/users/update-signature',
    method: 'PUT',
    data: { signature }
  })
}

/**
 * 修改密码（user_id 由 JWT 提供）
 * @param {Object} param0 修改密码数据
 * @param {string} param0.old_password 旧密码
 * @param {string} param0.new_password 新密码
 */
export function changePassword({ old_password, new_password }) {
  return request({
    url: '/api/v1/users/change-password',
    method: 'PUT',
    data: { old_password, new_password }
  })
}

/**
 * 发送修改邮箱的旧邮箱验证码（user_id 由 JWT 提供）
 */
export function sendChangeEmailOldCode() {
  return request({
    url: '/api/v1/users/send-change-email-old-code',
    method: 'POST',
    data: {}
  })
}

/**
 * 发送修改/绑定邮箱的新邮箱验证码
 * @param {string} new_email 新邮箱地址
 * @param {boolean} allow_existing 是否允许邮箱已存在（绑定邮箱触发账号合并场景传 true）
 */
export function sendChangeEmailNewCode(new_email, allow_existing = false) {
  return request({
    url: '/api/v1/users/send-change-email-new-code',
    method: 'POST',
    data: { new_email, allow_existing }
  })
}

/**
 * 修改邮箱（user_id 由 JWT 提供）
 * @param {Object} param0 修改邮箱数据
 * @param {string} param0.old_code 旧邮箱验证码
 * @param {string} param0.new_email 新邮箱地址
 * @param {string} param0.new_code 新邮箱验证码
 */
export function changeEmail({ old_code, new_email, new_code }) {
  return request({
    url: '/api/v1/users/change-email',
    method: 'PUT',
    data: { old_code, new_email, new_code }
  })
}

/**
 * 更新用户头像（user_id 由 JWT 提供）
 * @param {Object} param0 更新头像数据
 * @param {string} param0.avatar_url 头像地址
 */
export function updateAvatar({ avatar_url }) {
  return request({
    url: '/api/v1/users/update-avatar',
    method: 'PUT',
    data: { avatar_url }
  })
}

/**
 * 计划删除账号（user_id 由 JWT 提供，将 status 置为 0，后台任务在 24 小时后自动清理）
 */
export function scheduleDeletion() {
  return request({
    url: '/api/v1/users/schedule-deletion',
    method: 'POST',
    data: {}
  })
}

/**
 * 取消账号删除计划（user_id 由 JWT 提供，将 status 恢复为 1）
 */
export function cancelDeletion() {
  return request({
    url: '/api/v1/users/cancel-deletion',
    method: 'POST',
    data: {}
  })
}

/**
 * 微信一键登录
 * @param {string} code wx.login() 获取的临时登录凭证
 */
export function wechatLogin(code) {
  return request({
    url: '/api/v1/users/wechat-login',
    method: 'POST',
    data: { code },
    timeout: 10000
  })
}

/**
 * 更新用户名（user_id 由 JWT 提供，含唯一性校验）
 * @param {Object} param0 更新用户名数据
 * @param {string} param0.new_username 新用户名
 */
export function updateUsername({ new_username }) {
  return request({
    url: '/api/v1/users/update-username',
    method: 'PUT',
    data: { new_username }
  })
}

/**
 * 设置密码（user_id 由 JWT 提供，用于无密码用户首次设置密码）
 * @param {Object} param0 设置密码数据
 * @param {string} param0.new_password 新密码
 */
export function setPassword({ new_password }) {
  return request({
    url: '/api/v1/users/set-password',
    method: 'PUT',
    data: { new_password }
  })
}

/**
 * 绑定邮箱（user_id 由 JWT 提供，用于无邮箱用户首次绑定邮箱）
 * @param {Object} param0 绑定邮箱数据
 * @param {string} param0.new_email 新邮箱地址
 * @param {string} param0.new_code 新邮箱验证码
 */
export function bindEmail({ new_email, new_code }) {
  return request({
    url: '/api/v1/users/bind-email',
    method: 'PUT',
    data: { new_email, new_code }
  })
}

/**
 * 获取当前登录用户信息（user_id 由 JWT 提供，用于验证账号是否存在及刷新状态）
 */
export function getUserInfo() {
  return request({
    url: '/api/v1/users/info',
    method: 'GET'
  })
}
