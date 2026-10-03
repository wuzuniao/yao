import { request } from '../request'
import { AUTH_BASE_URL } from '../../config/env'

/**
 * 公告接口（直连 auth 统一认证服务；公告管理迁移 auth，2026-10-02）
 * --------------------------------------------------------------------------
 * - 已读状态存 auth 库，按 (公告, 用户, 项目) 维度分别维护（user_id 取令牌 sub）
 * - 项目归属由 JWT azp 判定，前端无需传 client_id
 * - baseUrl 用 AUTH_BASE_URL 覆盖默认业务后端地址（request 支持按请求覆盖）
 */

/**
 * 分页查询本项目可见公告（倒序；每条含 is_read，data 附 unread_count / has_more）
 */
export function getAnnouncements(page, pageSize = 20) {
  return request({
    url: `/api/v1/announcements?page=${page}&page_size=${pageSize}`,
    method: 'GET',
    baseUrl: AUTH_BASE_URL
  })
}

/**
 * 查询公告未读数（通知组件查询用）
 */
export function getAnnouncementUnreadCount() {
  return request({
    url: '/api/v1/announcements/unread-count',
    method: 'GET',
    baseUrl: AUTH_BASE_URL
  })
}

/**
 * 标记单条公告已读（幂等）；成功响应 data.unread_count 为最新未读数
 */
export function markAnnouncementRead(id) {
  return request({
    url: `/api/v1/announcements/${id}/read`,
    method: 'POST',
    data: {},
    baseUrl: AUTH_BASE_URL
  })
}

/**
 * 全部已读（当前项目全部未读公告）；成功响应 data.marked 为本次标记条数
 */
export function markAllAnnouncementsRead() {
  return request({
    url: '/api/v1/announcements/read-all',
    method: 'POST',
    data: {},
    baseUrl: AUTH_BASE_URL
  })
}
