import { request } from '../request'

/**
 * 查询当前登录用户站内信列表（user_id 由 JWT 提供，分页，含计划名称/备注与未读数量）
 * @param {number} page 页码（从1开始，默认1）
 * @param {number} limit 每页数量（默认20，最大100）
 */
export function listMessages(page = 1, limit = 20) {
  return request({
    url: '/api/v1/notification-logs/list',
    method: 'GET',
    data: { page, limit }
  })
}

/**
 * 标记站内信为已读（user_id 由 JWT 提供，status 2 → 0）
 * @param {Object} param0
 * @param {number} param0.log_id 消息记录ID
 */
export function markMessageRead({ log_id }) {
  return request({
    url: '/api/v1/notification-logs/read',
    method: 'PUT',
    data: { log_id }
  })
}

/**
 * 查询当前登录用户未读站内信数量（user_id 由 JWT 提供，用于通知按钮图标切换）
 */
export function getUnreadCount() {
  return request({
    url: '/api/v1/notification-logs/unread-count',
    method: 'GET'
  })
}
