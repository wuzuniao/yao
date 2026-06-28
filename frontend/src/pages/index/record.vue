<template>
  <view class="record-page">
    <NoticeButton :has-notification="hasNotification" />

    <view class="record-page__main">
      <view class="record-page__calendar">
        <view class="record-page__calendar-header">
          <view class="record-page__calendar-arrow-btn" @click="handlePrevMonth">
            <view class="record-page__calendar-arrow record-page__calendar-arrow--left"></view>
          </view>
          <text class="record-page__calendar-month">2026年6月</text>
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
              >
                <text class="record-page__calendar-day-num">{{ day.date }}</text>
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

      <view class="record-page__list">
        <view class="record-page__list-header">
          <image class="record-page__list-icon" :src="jiluXqIcon" mode="aspectFit" />
          <text class="record-page__list-title">{{ selectedDate }}</text>
        </view>

        <view class="record-page__list-items">
          <view
            v-for="(item, index) in checkInItems"
            :key="index"
            class="record-page__list-item"
            :class="{ 'record-page__list-item--bordered': index < checkInItems.length - 1 }"
          >
            <view class="record-page__list-item-marker">
              <view
                class="record-page__list-item-dot"
                :class="{ 'record-page__list-item-dot--completed': item.completed }"
              ></view>
            </view>
            <view class="record-page__list-item-content">
              <text class="record-page__list-item-time">{{ item.time }}</text>
              <text class="record-page__list-item-desc">{{ item.desc }}</text>
            </view>
            <image
              v-if="item.completed"
              class="record-page__list-item-check"
              :src="jiluWcIcon"
              mode="aspectFit"
            />
          </view>
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
 *  - 月历：展示当月每日打卡状态（已打卡/未打卡/今日/选中），支持日期选中切换
 *  - 当日明细：列出选中日期的打卡项目（时间 + 备注 + 完成状态图标）
 *  - 底部固定导航栏（BottomNav），当前激活项为"记录"
 */
import { ref } from 'vue'
import NoticeButton from '../../components/NoticeButton.vue'
import BottomNav from '../../components/BottomNav.vue'
import jiluXqIcon from '../../assets/images/jilu_xq.png'
import jiluWcIcon from '../../assets/images/jilu_wc.png'

const hasNotification = false

const checkInItems = ref([
  { time: '09:05', desc: '饭后半小时服用', completed: true },
  { time: '19:30', desc: '睡前服用', completed: false }
])

const calendarDays = ref([
  null,
  { date: 1, isToday: false, isSelected: false, checked: false },
  { date: 2, isToday: false, isSelected: false, checked: false },
  { date: 3, isToday: false, isSelected: false, checked: true },
  { date: 4, isToday: false, isSelected: false, checked: false },
  { date: 5, isToday: false, isSelected: false, checked: true },
  { date: 6, isToday: false, isSelected: false, checked: false },
  { date: 7, isToday: false, isSelected: false, checked: false },
  { date: 8, isToday: false, isSelected: false, checked: true },
  { date: 9, isToday: false, isSelected: false, checked: false },
  { date: 10, isToday: false, isSelected: false, checked: true },
  { date: 11, isToday: false, isSelected: false, checked: false },
  { date: 12, isToday: false, isSelected: false, checked: true },
  { date: 13, isToday: false, isSelected: false, checked: false },
  { date: 14, isToday: false, isSelected: false, checked: false },
  { date: 15, isToday: true, isSelected: false, checked: true },
  { date: 16, isToday: false, isSelected: true, checked: false },
  { date: 17, isToday: false, isSelected: false, checked: false },
  { date: 18, isToday: false, isSelected: false, checked: false },
  { date: 19, isToday: false, isSelected: false, checked: false },
  { date: 20, isToday: false, isSelected: false, checked: false },
  { date: 21, isToday: false, isSelected: false, checked: false },
  { date: 22, isToday: false, isSelected: false, checked: false },
  { date: 23, isToday: false, isSelected: false, checked: false },
  { date: 24, isToday: false, isSelected: false, checked: false },
  { date: 25, isToday: false, isSelected: false, checked: false },
  { date: 26, isToday: false, isSelected: false, checked: false },
  { date: 27, isToday: false, isSelected: false, checked: false },
  { date: 28, isToday: false, isSelected: false, checked: false },
  { date: 29, isToday: false, isSelected: false, checked: false },
  { date: 30, isToday: false, isSelected: false, checked: false },
  null,
  null,
  null,
  null
])

function handlePrevMonth() {
  uni.showToast({ title: '上一月', icon: 'none' })
}

// 当前选中日期文本：与日历 isSelected 状态联动，初始匹配 calendarDays 中 isSelected=true 的 16 日
const selectedDate = ref('6月16日')

/**
 * 日历单元格点击选中处理
 * - day 为 null（月首尾占位空格）直接返回，不处理
 * - 清除所有日期的 isSelected，将点击日期置为选中
 * - 同步更新列表标题为"6月{date}日"
 */
function handleSelectDay(day) {
  if (!day) return
  calendarDays.value.forEach((d) => {
    if (d) d.isSelected = false
  })
  day.isSelected = true
  selectedDate.value = `6月${day.date}日`
}

function handleNextMonth() {
  uni.showToast({ title: '下一月', icon: 'none' })
}
</script>

<style lang="scss">
.record-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
  padding-bottom: 177px;
}

.record-page__main {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 100px 24px 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.record-page__calendar {
  width: 100%;
  padding: 24px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-page__calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 36px;
}

.record-page__calendar-arrow-btn {
  width: 23.4px;
  height: 36px;
  padding: 8px 8px 16px;
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

.record-page__calendar-month {
  color: #0e0f0c;
  font-size: 24px;
  line-height: 32px;
  font-weight: 600;
  text-align: center;
}

.record-page__calendar-weekdays {
  display: flex;
  padding-top: 8px;
}

.record-page__calendar-weekday {
  width: 42px;
  text-align: center;
  color: #454745;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
}

.record-page__calendar-grid {
  display: flex;
  flex-wrap: wrap;
}

.record-page__calendar-cell {
  width: 42px;
  height: 52px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.record-page__calendar-day-num {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
  text-align: center;
}

.record-page__calendar-day-num--selected {
  color: #225100;
}

.record-page__calendar-today {
  width: 36px;
  height: 36px;
  border-radius: 9999px;
  box-shadow: inset 0 0 0 2px #2f6c00;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__calendar-selected {
  width: 36px;
  height: 36px;
  border-radius: 9999px;
  background: #e2f6d5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__calendar-dot {
  position: absolute;
  bottom: 8px;
  width: 4px;
  height: 4px;
  border-radius: 9999px;
  background: #2ead4b;
}

.record-page__list {
  width: 100%;
  padding: 24px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.record-page__list-header {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 24px;
}

.record-page__list-icon {
  width: 18px;
  height: 20px;
  display: block;
}

.record-page__list-title {
  color: #0e0f0c;
  font-size: 18px;
  line-height: 24px;
  font-weight: 600;
}

.record-page__list-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-page__list-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-height: 52px;
}

.record-page__list-item--bordered {
  padding-bottom: 12px;
  border-bottom: 1px solid #e8ebe6;
}

.record-page__list-item-marker {
  width: 8px;
  height: 16px;
  padding-top: 8px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-page__list-item-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #dadada;
}

.record-page__list-item-dot--completed {
  background: #2ead4b;
}

.record-page__list-item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.record-page__list-item-time {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

.record-page__list-item-desc {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}

.record-page__list-item-check {
  width: 20px;
  height: 20px;
  display: block;
  margin-top: 2px;
}
</style>
