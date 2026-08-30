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
 * 创建计划（user_id 由 JWT 提供，含通知时间点、重复规则、结束方式与关联渠道）
 * @param {Object} param0 计划数据
 * @param {string} param0.name 计划名称
 * @param {string} param0.remark 备注
 * @param {string} param0.start_date 开始日期（YYYY-MM-DD）
 * @param {string|null} param0.end_date 结束日期（YYYY-MM-DD；end_mode=0 必填，1/2 传 null 由后端落哨兵值）
 * @param {Array<{time: string, followup_count: number, followup_interval_min: number}>} param0.notification_times
 *        通知时间点数组：time 为 HH:MM；followup_count 提醒总次数（1/2/3，3=默认三段式）；
 *        followup_interval_min 自定义等间隔分钟（5-60，仅 count=1/2 生效）
 * @param {number} param0.repeat_weekdays 重复星期位掩码：bit0=周一…bit6=周日（127=每天，31=工作日，96=周末）
 * @param {number} param0.end_mode 结束方式：0-按end_date，1-按打卡总次数，2-长期不结束
 * @param {number|null} param0.total_target_count 目标打卡总次数（end_mode=1 时必填，1-9999）
 * @param {number[]} param0.channel_ids 关联的通知渠道ID数组
 * @param {number} param0.status 任务状态：1-进行中，2-暂停，0-已结束（默认1）
 * @param {number} param0.priority 优先级：0-3，数字越小优先级越高（默认3）
 */
export function createPlan({
  name, remark, start_date, end_date,
  notification_times, repeat_weekdays = 127, end_mode = 0, total_target_count = null,
  channel_ids, status = 1, priority = 3
}) {
  return request({
    url: '/api/v1/plans',
    method: 'POST',
    data: {
      name, remark, start_date, end_date,
      notification_times, repeat_weekdays, end_mode, total_target_count,
      channel_ids, status, priority
    }
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
 * 更新计划（user_id 由 JWT 提供，字段同 createPlan）
 * @param {number} plan_id 计划ID
 */
export function updatePlan(plan_id, {
  name, remark, start_date, end_date,
  notification_times, repeat_weekdays = 127, end_mode = 0, total_target_count = null,
  channel_ids, status, priority
}) {
  return request({
    url: `/api/v1/plans/${plan_id}`,
    method: 'PUT',
    data: {
      name, remark, start_date, end_date,
      notification_times, repeat_weekdays, end_mode, total_target_count,
      channel_ids, status, priority
    }
  })
}
