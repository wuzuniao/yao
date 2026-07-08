<template>
  <view class="record-page">
    <NoticeButton :has-notification="hasNotification" />

    <view class="record-page__main">
      <view class="record-page__calendar">
        <view class="record-page__calendar-header">
          <view class="record-page__calendar-arrow-btn" @click="handlePrevMonth">
            <view class="record-page__calendar-arrow record-page__calendar-arrow--left"></view>
          </view>
          <view class="record-page__calendar-title-group">
            <picker mode="selector" :range="years" :value="yearIndex" @change="handleYearChange">
              <view class="record-page__calendar-title-picker">
                <text class="record-page__calendar-year">{{ currentYear }}年</text>
              </view>
            </picker>
            <picker mode="selector" :range="months" :value="monthIndex" @change="handleMonthChange">
              <view class="record-page__calendar-title-picker">
                <text class="record-page__calendar-month">{{ currentMonth }}月</text>
              </view>
            </picker>
          </view>
          <view class="record-page__calendar-arrow-btn" @click="handleNextMonth">
            <view class="record-page__calendar-arrow record-page__calendar-arrow--right"></view>
          </view>
        </view>

        <view class="record-page__calendar-weekdays">
          <text class="record-page__calendar-weekday">日</text>
          <text class="record-page__calendar-weekday">一</text>
          <text class="record-page__calendar-weekday">二</text>
          <text class="record-page__calendar-weekday">三</text>
          <text class="record-page__calendar-weekday">四</text>
          <text class="record-page__calendar-weekday">五</text>
          <text class="record-page__calendar-weekday">六</text>
        </view>

        <view class="record-page__calendar-grid">
          <view
            v-for="(day, index) in calendarDays"
            :key="index"
            class="record-page__calendar-cell"
            @click="handleSelectDay(day)"
          >
            <template v-if="day">
              <view
                v-if="day.isToday"
                class="record-page__calendar-today"
                :class="{ 'record-page__calendar-today--active': day.isSelected }"
              >
                <text class="record-page__calendar-day-num record-page__calendar-day-num--selected">{{ day.date }}</text>
              </view>
              <view
                v-else-if="day.isSelected"
                class="record-page__calendar-selected"
              >
                <text class="record-page__calendar-day-num record-page__calendar-day-num--selected">{{ day.date }}</text>
              </view>
              <text
                v-else
                class="record-page__calendar-day-num"
              >{{ day.date }}</text>
              <view v-if="day.checked" class="record-page__calendar-dot"></view>
            </template>
          </view>
        </view>
      </view>

      <!-- 当天打卡详情卡片（点击有打卡记录的日期时显示） -->
      <view v-if="selectedDayDetail" class="record-page__list">
        <view class="record-page__list-header">
          <image class="record-page__list-icon" :src="jiluXqIcon" mode="aspectFit" />
          <text class="record-page__list-title">{{ selectedDateText }}</text>
        </view>

        <!-- 加载中状态：异步查询数据库时显示视觉反馈 -->
        <view v-if="isLoadingDay" class="record-page__list-loading">
          <text class="record-page__list-loading-text">加载中...</text>
        </view>
        <!-- 加载失败状态：点击重试重新发起查询 -->
        <view v-else-if="hasLoadError" class="record-page__list-error" @click="retryLoadDay">
          <text class="record-page__list-error-text">加载失败，点击重试</text>
        </view>
        <!-- 有数据：列出当天所有打卡记录 -->
        <view v-else-if="dayRecords.length > 0" class="record-page__list-items">
          <view
            v-for="(item, index) in dayRecords"
            :key="index"
            class="record-page__list-item"
            :class="{ 'record-page__list-item--bordered': index < dayRecords.length - 1 }"
          >
            <view class="record-page__list-item-marker">
              <view
                class="record-page__list-item-dot"
                :class="{ 'record-page__list-item-dot--completed': item.checked }"
              ></view>
            </view>
            <view class="record-page__list-item-content">
              <view class="record-page__list-item-time-row">
                <text class="record-page__list-item-time">{{ item.notification_time }}</text>
                <text v-if="item.checked && item.actual_time" class="record-page__list-item-actual-time">→ {{ formatActualTime(item.actual_time) }}</text>
              </view>
              <text class="record-page__list-item-name">{{ item.plan_name }}</text>
              <text v-if="item.plan_remark" class="record-page__list-item-remark">{{ item.plan_remark }}</text>
            </view>
            <image
              v-if="item.checked"
              class="record-page__list-item-check"
              :src="jiluWcIcon"
              mode="aspectFit"
            />
          </view>
        </view>
        <!-- 无数据 -->
        <view v-else class="record-page__list-empty">
          <text class="record-page__list-empty-text">当天暂无打卡记录</text>
        </view>
      </view>
    </view>

    <BottomNav active="record" />
  </view>
</template>

<script setup>
/**
 * 打卡记录页（record.vue）
 * --------------------------------------------------------------------------
 * 功能：展示用户当月打卡日历与当日打卡明细
 *  - 顶部通知按钮（NoticeButton）
 *  - 月历：
 *    - 年份选择器（picker，默认当前年份）
 *    - 月份选择器（picker，默认当前月份）
 *    - 动态生成当月日期（含月初前空格占位）
 *    - 已打卡日期下方显示小绿点
 *    - 点击日期选中，点击有打卡记录的日期显示详情卡片
 *  - 当日明细：列出当天所有进行中计划的提醒时间及打卡状态
 *    - 页面加载时（onShow）自动查询并展示当天打卡详情（仅当已登录且查看当前月份时）
 *    - 其他日期需用户点击日期单元格才触发查询
 *    - 加载中显示"加载中..."，加载失败显示"加载失败，点击重试"
 *    - 已打卡：绿点 + 提醒时间 + 实际打卡时间（→ HH:MM，绿色小字） + 计划名称/备注 + jilu_wc.png 图标
 *    - 未打卡：灰点 + 提醒时间 + 计划名称/备注（无图标）
 *  - 底部固定导航栏（BottomNav），当前激活项为"记录"
 */
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import NoticeButton from '../../components/NoticeButton.vue'
import BottomNav from '../../components/BottomNav.vue'
import { useUserStore } from '../../store/modules/user'
import { listMonthCheckins, listDayCheckins } from '../../api/modules/checkin'
import jiluXqIcon from '../../assets/images/jilu_xq.png'
import jiluWcIcon from '../../assets/images/jilu_wc.png'
import { useShare } from '../../composables/useShare'

useShare({ title: '用药记录' })

const hasNotification = false
const userStore = useUserStore()

// 当前显示的年份和月份（默认当前）
const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth() + 1)

// 年份选择器数据（2020-2040，共21年）
const years = ref([...Array(21)].map((_, i) => 2020 + i))
const yearIndex = computed(() => years.value.indexOf(currentYear.value))

// 月份选择器数据（1-12）
const months = ref([...Array(12)].map((_, i) => i + 1))
const monthIndex = computed(() => months.value.indexOf(currentMonth.value))

// 当月有打卡记录的日期列表（从数据库加载）
const checkedDays = ref([])
// 当前选中的日期（day of month）
const selectedDay = ref(null)
// 当天打卡详情记录列表
const dayRecords = ref([])
// 是否正在加载当日打卡详情（加载中显示"加载中..."反馈）
const isLoadingDay = ref(false)
// 当日打卡详情加载是否失败（失败时显示"加载失败，点击重试"）
const hasLoadError = ref(false)

// 是否显示详情卡片（选中日期后显示）
const selectedDayDetail = computed(() => selectedDay.value !== null)

// 选中日期的标题文本
const selectedDateText = computed(() => {
  if (selectedDay.value === null) return ''
  return `${currentMonth.value}月${selectedDay.value}日`
})

// 动态生成日历日期（含月初前空格占位）
const calendarDays = computed(() => {
  const firstDayOfWeek = new Date(currentYear.value, currentMonth.value - 1, 1).getDay()  // 0=周日
  const daysInMonth = new Date(currentYear.value, currentMonth.value, 0).getDate()
  const today = new Date()
  const isCurrentMonthToday =
    today.getFullYear() === currentYear.value && today.getMonth() + 1 === currentMonth.value
  const todayDate = today.getDate()

  const days = []
  // 月初前的空格占位
  for (let i = 0; i < firstDayOfWeek; i++) {
    days.push(null)
  }
  // 当月日期
  for (let d = 1; d <= daysInMonth; d++) {
    days.push({
      date: d,
      isToday: isCurrentMonthToday && d === todayDate,
      isSelected: d === selectedDay.value,
      checked: checkedDays.value.includes(d),
    })
  }
  return days
})

// ===== 数据加载 =====

// 加载当月打卡记录（获取有打卡的日期列表）
async function loadMonthCheckins() {
  if (!userStore.userInfo) {
    checkedDays.value = []
    return
  }
  try {
    const res = await listMonthCheckins(currentYear.value, currentMonth.value)
    if (res.code === 0 && res.data) {
      checkedDays.value = res.data.checked_days || []
    }
  } catch (e) {
    console.warn('加载月度打卡记录失败', e)
    checkedDays.value = []
  }
}

// 加载某天的打卡详情（含加载状态与错误处理，异步不阻塞界面）
async function loadDayCheckins(day) {
  if (!userStore.userInfo) return
  const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  isLoadingDay.value = true
  hasLoadError.value = false
  try {
    const res = await listDayCheckins(dateStr)
    if (res.code === 0 && res.data) {
      dayRecords.value = res.data
    } else {
      dayRecords.value = []
    }
  } catch (e) {
    // 数据库连接或查询异常：记录日志并标记失败状态，界面显示重试入口
    console.warn('加载当日打卡详情失败', e)
    dayRecords.value = []
    hasLoadError.value = true
  } finally {
    isLoadingDay.value = false
  }
}

// 重试加载当日打卡详情（加载失败时用户点击重试触发）
function retryLoadDay() {
  if (selectedDay.value !== null) {
    loadDayCheckins(selectedDay.value)
  }
}

// ===== 工具函数 =====

// 格式化实际打卡时间（ISO 字符串 → HH:MM）
// 后端返回上海时间字符串（如 "2026-07-02T14:30:00"），直接提取 HH:MM 部分
// 避免使用 new Date() 产生时区转换
function formatActualTime(isoStr) {
  if (!isoStr) return ''
  const match = isoStr.match(/T(\d{2}:\d{2})/)
  return match ? match[1] : ''
}

// ===== 事件处理 =====

// 年份选择
function handleYearChange(e) {
  const idx = e.detail.value
  currentYear.value = years.value[idx]
  selectedDay.value = null
  dayRecords.value = []
  loadMonthCheckins()
}

// 月份选择
function handleMonthChange(e) {
  const idx = e.detail.value
  currentMonth.value = months.value[idx]
  selectedDay.value = null
  dayRecords.value = []
  loadMonthCheckins()
}

// 上一月
function handlePrevMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value -= 1
  } else {
    currentMonth.value -= 1
  }
  selectedDay.value = null
  dayRecords.value = []
  loadMonthCheckins()
}

// 下一月
function handleNextMonth() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value += 1
  } else {
    currentMonth.value += 1
  }
  selectedDay.value = null
  dayRecords.value = []
  loadMonthCheckins()
}

// 点击日期：选中并加载当天详情
function handleSelectDay(day) {
  if (!day) return
  selectedDay.value = day.date
  loadDayCheckins(day.date)
}

// ===== 生命周期 =====

onShow(() => {
  loadMonthCheckins()
  // 页面加载时自动查询并展示当天打卡详情（仅当已登录且查看当前月份时）
  // 其他日期需用户点击日期单元格才触发查询
  if (userStore.userInfo) {
    const today = new Date()
    if (currentYear.value === today.getFullYear() && currentMonth.value === today.getMonth() + 1) {
      selectedDay.value = today.getDate()
      loadDayCheckins(today.getDate())
    }
  }
})
</script>

<style lang="scss">
/* ==========================================================================
 * 响应式单位说明（px → rpx 转换）
 * --------------------------------------------------------------------------
 * 基准：375px 设计稿，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * 转 rpx：width/height/padding/margin/gap/font-size/line-height/border-radius/定位偏移
 * 保留 px：1px 边框、box-shadow 偏移/模糊、9999px、百分比、vh、z-index
 * 平板/折叠屏断点：≥768px 锁定关键尺寸为 px，避免 rpx 过度放大
 * ========================================================================== */
.record-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
  /* padding-bottom 120px：BottomNav 高86px + bottom15px = 101px，留19px余量确保内容不被遮挡 */
  padding-bottom: 240rpx;
}

.record-page__main {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 210rpx 48rpx 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
}

.record-page__calendar {
  width: 100%;
  padding: 48rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.record-page__calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72rpx;
}

.record-page__calendar-arrow-btn {
  width: 46.8rpx;
  height: 72rpx;
  padding: 16rpx 16rpx 32rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__calendar-arrow {
  width: 0;
  height: 0;
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
}

.record-page__calendar-arrow--left {
  border-right: 7.4px solid #0e0f0c;
}

.record-page__calendar-arrow--right {
  border-left: 7.4px solid #0e0f0c;
}

/* 年月选择器标题组 */
.record-page__calendar-title-group {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.record-page__calendar-title-picker {
  display: flex;
  align-items: center;
}

.record-page__calendar-year {
  color: #0e0f0c;
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 600;
  text-align: center;
}

.record-page__calendar-month {
  color: #0e0f0c;
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 600;
  text-align: center;
}

.record-page__calendar-weekdays {
  /* CSS Grid 7列等宽，列宽自适应卡片宽度，杜绝固定宽度导致的换行错位 */
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding-top: 16rpx;
}

.record-page__calendar-weekday {
  text-align: center;
  color: #454745;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

.record-page__calendar-grid {
  /* CSS Grid 7列等宽，与星期标题列宽严格对齐，任何机型都不会错位 */
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.record-page__calendar-cell {
  height: 104rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.record-page__calendar-day-num {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
  text-align: center;
}

.record-page__calendar-day-num--selected {
  color: #225100;
}

.record-page__calendar-today {
  width: 72rpx;
  height: 72rpx;
  border-radius: 9999px;
  /* 绿色内边框始终区分"今天"；浅绿色背景仅在 today 被选中时通过 --active 修饰符叠加 */
  box-shadow: inset 0 0 0 2px #2f6c00;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 修饰符：今天被选中时叠加浅绿色背景，与其他日期选中态视觉一致 */
.record-page__calendar-today--active {
  background: #e2f6d5;
}

.record-page__calendar-selected {
  width: 72rpx;
  height: 72rpx;
  border-radius: 9999px;
  background: #e2f6d5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__calendar-dot {
  position: absolute;
  bottom: 16rpx;
  width: 8rpx;
  height: 8rpx;
  border-radius: 9999px;
  background: #2ead4b;
}

/* ===== 当天打卡详情卡片 ===== */
.record-page__list {
  width: 100%;
  padding: 48rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.record-page__list-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  height: 48rpx;
}

.record-page__list-icon {
  width: 36rpx;
  height: 40rpx;
  display: block;
}

.record-page__list-title {
  color: #0e0f0c;
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
}

.record-page__list-items {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.record-page__list-item {
  display: flex;
  align-items: flex-start;
  gap: 24rpx;
  min-height: 104rpx;
}

.record-page__list-item--bordered {
  padding-bottom: 24rpx;
  border-bottom: 1px solid #e8ebe6;
}

.record-page__list-item-marker {
  width: 16rpx;
  height: 32rpx;
  padding-top: 16rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__list-item-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 9999px;
  background: #dadada;
}

.record-page__list-item-dot--completed {
  background: #2ead4b;
}

.record-page__list-item-content {
  flex: 1;
  /* min-width:0 允许 flex 子项收缩，使文本截断生效 */
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.record-page__list-item-time-row {
  display: flex;
  align-items: baseline;
  gap: 16rpx;
}

.record-page__list-item-time {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

.record-page__list-item-actual-time {
  color: #2ead4b;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.record-page__list-item-name {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-page__list-item-remark {
  color: #454745;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-page__list-item-check {
  width: 40rpx;
  height: 40rpx;
  display: block;
  margin-top: 4rpx;
}

.record-page__list-empty {
  padding: 32rpx 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__list-empty-text {
  color: #888888;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.record-page__list-loading {
  padding: 32rpx 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__list-loading-text {
  color: #888888;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.record-page__list-error {
  padding: 32rpx 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__list-error-text {
  color: #e8553a;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 * 规则：将本页面主要容器的宽度、卡片宽度、按钮尺寸锁定为设计稿原 px 值
 */
@media screen and (min-width: 768px) {
  /* 主容器内边距与间距 */
  .record-page {
    padding-bottom: 120px;
  }
  .record-page__main {
    padding: 105px 24px 0;
    gap: 32px;
  }
  /* 日历卡片 */
  .record-page__calendar {
    padding: 24px;
    border-radius: 12px;
    gap: 8px;
  }
  .record-page__calendar-header {
    height: 36px;
  }
  .record-page__calendar-arrow-btn {
    width: 23.4px;
    height: 36px;
    padding: 8px 8px 16px;
  }
  .record-page__calendar-title-group {
    gap: 4px;
  }
  .record-page__calendar-year {
    font-size: 24px;
    line-height: 32px;
  }
  .record-page__calendar-month {
    font-size: 24px;
    line-height: 32px;
  }
  .record-page__calendar-weekdays {
    padding-top: 8px;
  }
  .record-page__calendar-weekday {
    font-size: 12px;
    line-height: 16px;
  }
  .record-page__calendar-cell {
    height: 52px;
  }
  .record-page__calendar-day-num {
    font-size: 16px;
    line-height: 24px;
  }
  .record-page__calendar-today {
    width: 36px;
    height: 36px;
  }
  .record-page__calendar-selected {
    width: 36px;
    height: 36px;
  }
  .record-page__calendar-dot {
    bottom: 8px;
    width: 4px;
    height: 4px;
  }
  /* 当天打卡详情卡片 */
  .record-page__list {
    padding: 24px;
    border-radius: 12px;
    gap: 16px;
  }
  .record-page__list-header {
    gap: 8px;
    height: 24px;
  }
  .record-page__list-icon {
    width: 18px;
    height: 20px;
  }
  .record-page__list-title {
    font-size: 18px;
    line-height: 24px;
  }
  .record-page__list-items {
    gap: 12px;
  }
  .record-page__list-item {
    gap: 12px;
    min-height: 52px;
  }
  .record-page__list-item--bordered {
    padding-bottom: 12px;
  }
  .record-page__list-item-marker {
    width: 8px;
    height: 16px;
    padding-top: 8px;
  }
  .record-page__list-item-dot {
    width: 8px;
    height: 8px;
  }
  .record-page__list-item-content {
    gap: 4px;
  }
  .record-page__list-item-time-row {
    gap: 8px;
  }
  .record-page__list-item-time {
    font-size: 16px;
    line-height: 24px;
  }
  .record-page__list-item-actual-time {
    font-size: 14px;
    line-height: 20px;
  }
  .record-page__list-item-name {
    font-size: 16px;
    line-height: 24px;
  }
  .record-page__list-item-remark {
    font-size: 14px;
    line-height: 20px;
  }
  .record-page__list-item-check {
    width: 20px;
    height: 20px;
    margin-top: 2px;
  }
  .record-page__list-empty {
    padding: 16px 0;
  }
  .record-page__list-empty-text {
    font-size: 14px;
    line-height: 20px;
  }
  .record-page__list-loading {
    padding: 16px 0;
  }
  .record-page__list-loading-text {
    font-size: 14px;
    line-height: 20px;
  }
  .record-page__list-error {
    padding: 16px 0;
  }
  .record-page__list-error-text {
    font-size: 14px;
    line-height: 20px;
  }
}
</style>
