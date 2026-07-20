import { request } from '../request'

/**
 * 查询全部公告（仅管理员）
 */
export function getAnnouncements() {
  return request({
    url: '/api/v1/announcements',
    method: 'GET'
  })
}

/**
 * 查询最近 7 天内发布的公告（普通用户），按创建时间倒序
 */
export function getRecentAnnouncements() {
  return request({
    url: '/api/v1/announcements/recent',
    method: 'GET'
  })
}

/**
 * 发布公告（仅管理员）
 * @param {Object} param0 公告数据
 * @param {string} param0.title 公告标题
 * @param {string} param0.content 公告内容
 */
export function publishAnnouncement({ title, content }) {
  return request({
    url: '/api/v1/announcements',
    method: 'POST',
    data: { title, content }
  })
}

/**
 * 更新公告（仅管理员）
 * @param {number} id 公告ID
 * @param {Object} param0 公告数据
 * @param {string} param0.title 公告标题
 * @param {string} param0.content 公告内容
 */
export function updateAnnouncement(id, { title, content }) {
  return request({
    url: `/api/v1/announcements/${id}`,
    method: 'PUT',
    data: { title, content }
  })
}

/**
 * 删除公告（仅管理员）
 * @param {number} id 公告ID
 */
export function deleteAnnouncement(id) {
  return request({
    url: `/api/v1/announcements/${id}`,
    method: 'DELETE'
  })
}
