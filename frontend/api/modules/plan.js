import { request } from '../request'

/**
 * 查询当前登录用户的所有计划（user_id 由 JWT 提供）
 */
export function listPlans() {
  return request({
    url: '/api/v1/plans/list',
    method: 'GET'
  })
}

/**
 * 创建计划（user_id 由 JWT 提供，含通知时间点和关联渠道）
 * @param {Object} param0 计划数据
 * @param {string} param0.name 计划名称
 * @param {string} param0.remark 备注
 * @param {string} param0.start_date 开始日期（YYYY-MM-DD）
 * @param {string} param0.end_date 结束日期（YYYY-MM-DD）
 * @param {string[]} param0.notification_times 通知时间点数组（HH:MM 格式）
 * @param {number[]} param0.channel_ids 关联的通知渠道ID数组
 * @param {number} param0.status 任务状态：1-进行中，2-暂停，0-已结束（默认1）
 * @param {number} param0.priority 优先级：0-7，数字越小优先级越高（默认3）
 */
export function createPlan({ name, remark, start_date, end_date, notification_times, channel_ids, status = 1, priority = 3 }) {
  return request({
    url: '/api/v1/plans',
    method: 'POST',
    data: { name, remark, start_date, end_date, notification_times, channel_ids, status, priority }
  })
}

/**
 * 删除计划（user_id 由 JWT 提供）
 * @param {number} plan_id 计划ID
 */
export function deletePlan(plan_id) {
  return request({
    url: `/api/v1/plans/${plan_id}`,
    method: 'DELETE'
  })
}

/**
 * 更新计划（user_id 由 JWT 提供，含通知时间点和关联渠道）
 * @param {number} plan_id 计划ID
 * @param {Object} param0 计划数据
 * @param {string} param0.name 计划名称
 * @param {string} param0.remark 备注
 * @param {string} param0.start_date 开始日期（YYYY-MM-DD）
 * @param {string} param0.end_date 结束日期（YYYY-MM-DD）
 * @param {string[]} param0.notification_times 通知时间点数组（HH:MM 格式）
 * @param {number[]} param0.channel_ids 关联的通知渠道ID数组
 * @param {number} param0.status 任务状态：1-进行中，2-暂停，0-已结束
 * @param {number} param0.priority 优先级：0-7，数字越小优先级越高
 */
export function updatePlan(plan_id, { name, remark, start_date, end_date, notification_times, channel_ids, status, priority }) {
  return request({
    url: `/api/v1/plans/${plan_id}`,
    method: 'PUT',
    data: { name, remark, start_date, end_date, notification_times, channel_ids, status, priority }
  })
}
