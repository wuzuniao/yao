import { request } from '../request'

/**
 * 创建打卡记录
 * @param {Object} param0 打卡数据
 * @param {number} param0.user_id 用户ID
 * @param {number} param0.plan_id 计划ID
 * @param {number} param0.plan_time_id 通知时间点ID
 * @param {string} param0.actual_time 实际打卡时间（ISO 格式字符串）
 */
export function createCheckin({ user_id, plan_id, plan_time_id, actual_time }) {
  return request({
    url: '/api/v1/checkins',
    method: 'POST',
    data: { user_id, plan_id, plan_time_id, actual_time }
  })
}

/**
 * 查询用户今日所有打卡记录
 * @param {number} user_id 用户ID
 */
export function listTodayCheckins(user_id) {
  return request({
    url: `/api/v1/checkins/${user_id}/today`,
    method: 'GET'
  })
}

/**
 * 查询用户今日某计划的打卡记录
 * @param {number} user_id 用户ID
 * @param {number} plan_id 计划ID
 */
export function listTodayCheckinsByPlan(user_id, plan_id) {
  return request({
    url: `/api/v1/checkins/${user_id}/today/${plan_id}`,
    method: 'GET'
  })
}

/**
 * 查询用户某月有打卡记录的日期列表
 * @param {number} user_id 用户ID
 * @param {number} year 年份
 * @param {number} month 月份（1-12）
 */
export function listMonthCheckins(user_id, year, month) {
  return request({
    url: `/api/v1/checkins/${user_id}/month`,
    method: 'GET',
    data: { year, month }
  })
}

/**
 * 查询用户某天的打卡详情（含计划提醒时间）
 * @param {number} user_id 用户ID
 * @param {string} date 日期，格式 YYYY-MM-DD
 */
export function listDayCheckins(user_id, date) {
  return request({
    url: `/api/v1/checkins/${user_id}/day`,
    method: 'GET',
    data: { date }
  })
}
