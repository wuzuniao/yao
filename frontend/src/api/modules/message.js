import { request } from '../request'

/**
 * 查询用户站内信列表（分页，含计划名称/备注与未读数量）
 * @param {number} user_id 用户ID
 * @param {number} page 页码（从1开始，默认1）
 * @param {number} limit 每页数量（默认20，最大100）
 */
export function listMessages(user_id, page = 1, limit = 20) {
  return request({
    url: `/api/v1/notification-logs/${user_id}/list`,
    method: 'GET',
    data: { page, limit }
  })
}

/**
 * 标记站内信为已读（status 2 → 0）
 * @param {Object} param0
 * @param {number} param0.log_id 消息记录ID
 * @param {number} param0.user_id 用户ID
 */
export function markMessageRead({ log_id, user_id }) {
  return request({
    url: '/api/v1/notification-logs/read',
    method: 'PUT',
    data: { log_id, user_id }
  })
}

/**
 * 查询用户未读站内信数量（用于通知按钮图标切换）
 * @param {number} user_id 用户ID
 */
export function getUnreadCount(user_id) {
  return request({
    url: `/api/v1/notification-logs/${user_id}/unread-count`,
    method: 'GET'
  })
}
