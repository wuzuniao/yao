import { request } from '../request'
import { AUTH_BASE_URL, AUTH_CLIENT_ID } from '../../config/env'

/**
 * 用户模块接口（全部直连 auth 统一认证服务，不经 yao 后端转发）
 * - baseUrl 固定为 AUTH_BASE_URL（开发 http://localhost:10000 / 生产 https://auth.wuzuniao.com）
 * - 登录类请求携带 client_id（auth 服务 oauth_clients 表注册的本应用公共 client）
 * - 登录/注册/重置密码/绑定邮箱成功响应的 data 含 OIDC 令牌三件套：
 *   access_token / refresh_token / expires_in / token_type
 */

/**
 * 发送注册验证码
 * @param {string} email 收件人邮箱（用户注册表单填写的电子邮箱）
 */
export function sendRegisterCode(email) {
  return request({
    url: '/api/v1/users/send-code',
    method: 'POST',
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
    data: { username, password, email, code, client_id: AUTH_CLIENT_ID }
  })
}

/**
 * 用户登录
 * @param {Object} param0 登录表单数据
 * @param {string} param0.username 用户名或邮箱
 * @param {string} param0.password 密码
 */
export function loginUser({ username, password, device_id }) {
  return request({
    url: '/api/v1/users/login',
    method: 'POST',
    baseUrl: AUTH_BASE_URL,
    data: { username, password, device_id, client_id: AUTH_CLIENT_ID }
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
    baseUrl: AUTH_BASE_URL,
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
export function resetPassword({ email, code, new_password, device_id }) {
  return request({
    url: '/api/v1/users/reset-password',
    method: 'POST',
    baseUrl: AUTH_BASE_URL,
    data: { email, code, new_password, device_id, client_id: AUTH_CLIENT_ID }
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
    data: { code, client_id: AUTH_CLIENT_ID },
    timeout: 10000
  })
}

/**
 * 绑定微信到当前登录用户
 * @param {string} code wx.login() 获取的临时登录凭证
 * @description 供已注册但未微信登录的用户，在通知页主动绑定微信以接收订阅消息
 */
export function bindWechat(code) {
  return request({
    url: '/api/v1/users/bind-wechat',
    method: 'POST',
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
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
    baseUrl: AUTH_BASE_URL,
    data: { new_password }
  })
}

/**
 * 绑定邮箱（user_id 由 JWT 提供，用于无邮箱用户首次绑定邮箱；
 * 若邮箱已存在会触发账号合并，成功响应含新令牌三件套）
 * @param {Object} param0 绑定邮箱数据
 * @param {string} param0.new_email 新邮箱地址
 * @param {string} param0.new_code 新邮箱验证码
 */
export function bindEmail({ new_email, new_code }) {
  return request({
    url: '/api/v1/users/bind-email',
    method: 'PUT',
    baseUrl: AUTH_BASE_URL,
    data: { new_email, new_code, client_id: AUTH_CLIENT_ID }
  })
}

/**
 * 获取当前登录用户信息（user_id 由 JWT 提供，用于验证账号是否存在及刷新状态）
 */
export function getUserInfo() {
  return request({
    url: '/api/v1/users/info',
    method: 'GET',
    baseUrl: AUTH_BASE_URL
  })
}

/**
 * 刷新访问令牌（静默续期，不要求重新登录）
 * 经 auth 服务标准 OIDC 令牌端点（POST /oauth/token 的 refresh_token grant，轮换制：
 * 每次刷新换新 refresh_token 并撤销旧的，新旧令牌均本地更新）
 * 注意：响应为令牌三件套原始结构（access_token/refresh_token/expires_in/token_type），
 * 非 {code,msg,data} 业务格式
 * @param {Object} param0 续期参数
 * @param {string} [param0.device_id] 设备标识，传入后 auth 同步顺延生物识别凭证有效期
 */
export function refreshToken({ device_id } = {}) {
  const data = {
    grant_type: 'refresh_token',
    refresh_token: uni.getStorageSync('refreshToken') || '',
    client_id: AUTH_CLIENT_ID
  }
  if (device_id) data.device_id = device_id
  return request({
    url: '/oauth/token',
    method: 'POST',
    baseUrl: AUTH_BASE_URL,
    // 刷新请求自身带跳过 401 静默重试标记（防递归），失败由调用方处理
    skipAuthRefresh: true,
    data
  })
}

/**
 * 生物识别（指纹）登录
 * @param {Object} param0 指纹登录参数
 * @param {string} param0.token 本地存储的生物识别凭证
 * @param {string} param0.device_id 设备标识（与凭证绑定）
 */
export function biometricLogin({ token, device_id }) {
  return request({
    url: '/api/v1/users/biometric-login',
    method: 'POST',
    baseUrl: AUTH_BASE_URL,
    data: { token, device_id, client_id: AUTH_CLIENT_ID },
    timeout: 10000
  })
}

/**
 * 撤销当前设备生物识别登录凭证（关闭指纹登录时调用）
 * @param {Object} param0 撤销参数
 * @param {string} param0.device_id 设备标识（与凭证绑定）
 */
export function revokeBiometric({ device_id }) {
  return request({
    url: '/api/v1/users/biometric-revoke',
    method: 'POST',
    baseUrl: AUTH_BASE_URL,
    data: { device_id }
  })
}

/**
 * 退出登录（撤销全部令牌；前端需同步清除本地 accessToken/refreshToken/userInfo）
 */
export function logout() {
  return request({
    url: '/api/v1/users/logout',
    method: 'POST',
    baseUrl: AUTH_BASE_URL,
    data: {}
  })
}
