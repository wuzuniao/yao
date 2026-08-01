import { request } from '../request'

/**
 * 创建打卡记录（user_id 由 JWT 提供）
 * @param {Object} param0 打卡数据
 * @param {number} param0.plan_id 计划ID
 * @param {number} param0.plan_time_id 通知时间点ID
 * @param {string} param0.actual_time 实际打卡时间（ISO 格式字符串）
 */
export function createCheckin({ plan_id, plan_time_id, actual_time }) {
  return request({
    url: '/api/v1/checkins',
    method: 'POST',
    data: { plan_id, plan_time_id, actual_time }
  })
}

/**
 * 查询当前登录用户今日所有打卡记录（user_id 由 JWT 提供）
 */
export function listTodayCheckins() {
  return request({
    url: '/api/v1/checkins/today',
    method: 'GET'
  })
}

/**
 * 查询当前登录用户今日某计划的打卡记录（user_id 由 JWT 提供）
 * @param {number} plan_id 计划ID
 */
export function listTodayCheckinsByPlan(plan_id) {
  return request({
    url: `/api/v1/checkins/today/${plan_id}`,
    method: 'GET'
  })
}

/**
 * 查询当前登录用户某月有打卡记录的日期列表（user_id 由 JWT 提供）
 * @param {number} year 年份
 * @param {number} month 月份（1-12）
 */
export function listMonthCheckins(year, month) {
  return request({
    url: '/api/v1/checkins/month',
    method: 'GET',
    data: { year, month }
  })
}

/**
 * 查询当前登录用户某天的打卡详情（user_id 由 JWT 提供，含计划提醒时间）
 * @param {string} date 日期，格式 YYYY-MM-DD
 */
export function listDayCheckins(date) {
  return request({
    url: '/api/v1/checkins/day',
    method: 'GET',
    data: { date }
  })
}
