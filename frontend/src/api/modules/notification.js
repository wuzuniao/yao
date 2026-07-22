import { request } from '../request'

/**
 * 查询当前登录用户的所有通知渠道（user_id 由 JWT 提供）
 */
export function listNotificationChannels() {
  return request({
    url: '/api/v1/notification-channels/list',
    method: 'GET'
  })
}

/**
 * 创建邮件通知渠道（user_id 由 JWT 提供）
 * @param {Object} param0 邮件渠道配置
 * @param {string} param0.smtp_host SMTP服务器地址
 * @param {number} param0.smtp_port SMTP服务器端口
 * @param {string} param0.email 发件邮箱地址
 * @param {string} param0.password 客户端专用密码
 * @param {boolean} param0.enabled 是否启用（默认 true）
 */
export function createEmailChannel({ smtp_host, smtp_port, email, password, enabled = true }) {
  return request({
    url: '/api/v1/notification-channels/email',
    method: 'POST',
    data: { smtp_host, smtp_port, email, password, enabled }
  })
}

/**
 * 更新邮件通知渠道配置（user_id 由 JWT 提供）
 * @param {Object} param0 邮件渠道配置
 * @param {number} param0.channel_id 渠道ID
 * @param {string} param0.smtp_host SMTP服务器地址
 * @param {number} param0.smtp_port SMTP服务器端口
 * @param {string} param0.email 发件邮箱地址
 * @param {string} param0.password 客户端专用密码（空字符串表示保留原密码）
 * @param {boolean} param0.enabled 是否启用
 */
export function updateEmailChannel({ channel_id, smtp_host, smtp_port, email, password, enabled = true }) {
  return request({
    url: '/api/v1/notification-channels/email',
    method: 'PUT',
    data: { channel_id, smtp_host, smtp_port, email, password, enabled }
  })
}

/**
 * 删除通知渠道（user_id 由 JWT 提供，站内信不允许删除）
 * @param {Object} param0
 * @param {number} param0.channel_id 渠道ID
 */
export function deleteNotificationChannel({ channel_id }) {
  return request({
    url: '/api/v1/notification-channels',
    method: 'DELETE',
    data: { channel_id }
  })
}

/**
 * 微信订阅消息授权回调：用户每同意一次授权（wx.requestSubscribeMessage 返回 accept）
 * 即 +1 下发额度并启用微信渠道（user_id 由 JWT 提供）
 */
export function grantWechatChannel() {
  return request({
    url: '/api/v1/notification-channels/wechat/grant',
    method: 'POST'
  })
}
