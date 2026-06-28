<template>
  <view class="plan-page">
    <NoticeButton :has-notification="hasNotification" />

    <view class="plan-page__main">
      <!-- 页面标题区 -->
      <view class="plan-page__header">
        <text class="plan-page__title">制定计划</text>
        <text class="plan-page__desc">合理规划您的用药与健康提醒，助您养成良好{{'\n'}}的生活习惯。</text>
      </view>

      <!-- 已有计划列表 -->
      <view class="plan-page__list">
        <!-- 计划卡片 1：激活态（左侧绿色色条） -->
        <view class="plan-page__card plan-page__card--active">
          <view class="plan-page__card-stripe plan-page__card-stripe--active"></view>
          <view class="plan-page__card-body">
            <view class="plan-page__card-head">
              <view class="plan-page__card-title-group">
                <text class="plan-page__card-title">按时吃药</text>
                <text class="plan-page__card-subtitle">降压药 - 每日</text>
              </view>
              <view class="plan-page__card-menu" @click="handleMenu">
                <view class="plan-page__dot"></view>
                <view class="plan-page__dot"></view>
                <view class="plan-page__dot"></view>
              </view>
            </view>
            <view class="plan-page__card-pills">
              <view class="plan-page__pill">08:00</view>
              <view class="plan-page__pill">20:00</view>
            </view>
          </view>
        </view>

        <!-- 计划卡片 2：未激活态（左侧灰色色条） -->
        <view class="plan-page__card">
          <view class="plan-page__card-stripe"></view>
          <view class="plan-page__card-body">
            <view class="plan-page__card-head">
              <view class="plan-page__card-title-group">
                <text class="plan-page__card-title">测量血压</text>
                <text class="plan-page__card-subtitle">早晚各一次</text>
              </view>
              <view class="plan-page__card-menu" @click="handleMenu">
                <view class="plan-page__dot"></view>
                <view class="plan-page__dot"></view>
                <view class="plan-page__dot"></view>
              </view>
            </view>
            <view class="plan-page__card-pills">
              <view class="plan-page__pill">07:30</view>
              <view class="plan-page__pill">21:00</view>
            </view>
          </view>
        </view>

        <!-- 新建计划入口卡（点击后切换为"新建计划详情"表单卡） -->
        <view class="plan-page__new-entry" v-if="!showForm" @click="handleNewEntry">
          <image class="plan-page__new-entry-icon" :src="jiaJihuaIcon" mode="aspectFit" />
          <text class="plan-page__new-entry-text">新建计划</text>
        </view>
      </view>

      <!-- 新建计划详情表单卡（默认隐藏，点击"新建计划"后显示，淡入过渡） -->
      <view class="plan-page__form-wrap" v-if="showForm">
        <view class="plan-page__form plan-page__form--fade-in">
          <text class="plan-page__form-heading">新建计划详情</text>

          <!-- 计划名称 -->
          <view class="plan-page__field">
            <text class="plan-page__label">计划名称</text>
            <input
              class="plan-page__input"
              placeholder="例如：按时吃药"
              placeholder-class="plan-page__placeholder"
              :placeholder-style="phStyle('name')"
              @focus="onFocus('name')"
              @blur="onBlur"
            />
          </view>

          <!-- 备注说明 -->
          <view class="plan-page__field">
            <text class="plan-page__label">备注说明</text>
            <textarea
              class="plan-page__textarea"
              placeholder="例如：饭后半小时服用"
              placeholder-class="plan-page__placeholder"
              :placeholder-style="phStyle('remark')"
              @focus="onFocus('remark')"
              @blur="onBlur"
            />
          </view>

          <!-- 日期范围 -->
          <view class="plan-page__field">
            <text class="plan-page__label">日期范围</text>
            <view class="plan-page__date-row">
              <input
                class="plan-page__date-input"
                placeholder="选择开始日期"
                placeholder-class="plan-page__placeholder"
                :placeholder-style="phStyle('dateStart')"
                @focus="onFocus('dateStart')"
                @blur="onBlur"
              />
              <view class="plan-page__arrow"></view>
              <input
                class="plan-page__date-input"
                placeholder="选择结束日期"
                placeholder-class="plan-page__placeholder"
                :placeholder-style="phStyle('dateEnd')"
                @focus="onFocus('dateEnd')"
                @blur="onBlur"
              />
            </view>
          </view>

          <!-- 提醒时间 -->
          <view class="plan-page__field">
            <view class="plan-page__time-label-row">
              <text class="plan-page__label">提醒时间</text>
              <view class="plan-page__add-time" @click="handleAddTime">
                <image class="plan-page__add-time-icon" :src="jiaShijianIcon" mode="aspectFit" />
                <text class="plan-page__add-time-text">添加时间</text>
              </view>
            </view>
            <view class="plan-page__time-row">
              <input
                class="plan-page__time-input"
                placeholder="选择时间"
                placeholder-class="plan-page__placeholder"
                :placeholder-style="phStyle('time0Start')"
                @focus="onFocus('time0Start')"
                @blur="onBlur"
              />
              <text class="plan-page__time-dash">-</text>
              <input
                class="plan-page__time-input"
                placeholder="选择时间"
                placeholder-class="plan-page__placeholder"
                :placeholder-style="phStyle('time0End')"
                @focus="onFocus('time0End')"
                @blur="onBlur"
              />
              <view class="plan-page__time-delete" @click="handleDeleteTime(0)">
                <image class="plan-page__time-delete-icon" :src="shanchuIcon" mode="aspectFit" />
              </view>
            </view>
            <view class="plan-page__time-row">
              <input
                class="plan-page__time-input"
                placeholder="选择时间"
                placeholder-class="plan-page__placeholder"
                :placeholder-style="phStyle('time1Start')"
                @focus="onFocus('time1Start')"
                @blur="onBlur"
              />
              <text class="plan-page__time-dash">-</text>
              <input
                class="plan-page__time-input"
                placeholder="选择时间"
                placeholder-class="plan-page__placeholder"
                :placeholder-style="phStyle('time1End')"
                @focus="onFocus('time1End')"
                @blur="onBlur"
              />
              <view class="plan-page__time-delete" @click="handleDeleteTime(1)">
                <image class="plan-page__time-delete-icon" :src="shanchuIcon" mode="aspectFit" />
              </view>
            </view>
          </view>

          <!-- 通知方式 -->
          <view class="plan-page__field">
            <text class="plan-page__label">通知方式</text>
            <view class="plan-page__notify-row">
              <view class="plan-page__notify-item" @click="toggleNotify('znx')">
                <view class="plan-page__checkbox" :class="{ 'plan-page__checkbox--checked': notify.znx }">
                  <view v-if="notify.znx" class="plan-page__checkmark"></view>
                </view>
                <text class="plan-page__notify-text">站内信</text>
              </view>
              <view class="plan-page__notify-item" @click="toggleNotify('yx')">
                <view class="plan-page__checkbox" :class="{ 'plan-page__checkbox--checked': notify.yx }">
                  <view v-if="notify.yx" class="plan-page__checkmark"></view>
                </view>
                <text class="plan-page__notify-text">邮件</text>
              </view>
            </view>
          </view>

          <!-- 保存按钮 -->
          <view class="plan-page__save" @click="handleSave">
            <image class="plan-page__save-icon" :src="baocunJihuaIcon" mode="aspectFit" />
            <text class="plan-page__save-text">保存计划</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 制定计划页（plan.vue）
 * --------------------------------------------------------------------------
 * 功能：用药 / 健康提醒计划的制定与管理
 *  - 已有计划列表：展示激活态（绿色色条）与未激活态（灰色色条）计划卡片
 *  - 卡片切换：默认显示"新建计划"入口卡，点击后淡入切换为"新建计划详情"表单卡
 *  - 表单字段：计划名称、备注说明、日期范围、提醒时间（支持多时间段增删）、通知方式（站内信/邮件）
 *  - 保存计划：提交表单（当前为占位 toast，待接入后端 API）
 * 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
 */
import { reactive, ref } from 'vue'
import NoticeButton from '../../components/NoticeButton.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import jiaJihuaIcon from '../../assets/images/jia_jihua.png'
import jiaShijianIcon from '../../assets/images/jia_shijian.png'
import shanchuIcon from '../../assets/images/shanchu.png'
import baocunJihuaIcon from '../../assets/images/baocun_jihua.png'

// 设计稿顶栏铃铛为绿色无红点态
const hasNotification = false

// 通知方式复选状态：站内信默认选中、邮件默认未选（对照设计稿）
const notify = reactive({ znx: true, yx: false })

// 卡片切换：默认显示"新建计划"入口卡，点击后切换为"新建计划详情"表单卡
const showForm = ref(false)

// 输入框 placeholder 聚焦交互：聚焦变浅灰 #c0c0c0，失焦恢复 placeholder-class 原始色
const { onFocus, onBlur, phStyle } = usePlaceholder()

function toggleNotify(key) {
  notify[key] = !notify[key]
}

function handleMenu() {
  uni.showToast({ title: '更多操作', icon: 'none' })
}

function handleNewEntry() {
  // 点击"新建计划"入口卡：切换显示"新建计划详情"表单卡
  showForm.value = true
}

function handleAddTime() {
  uni.showToast({ title: '添加提醒时间', icon: 'none' })
}

function handleDeleteTime(idx) {
  uni.showToast({ title: `删除时间段 ${idx + 1}`, icon: 'none' })
}

function handleSave() {
  uni.showToast({ title: '保存计划', icon: 'none' })
}
</script>

<style lang="scss">
.plan-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.plan-page__main {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 100px 24px 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ===== 页面标题区 ===== */
.plan-page__header {
  padding: 0 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plan-page__title {
  color: #0e0f0c;
  font-size: 32px;
  line-height: 36px;
  font-weight: 600;
}

.plan-page__desc {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
  padding-top: 4px;
  white-space: pre-line;
}

/* ===== 已有计划列表 ===== */
.plan-page__list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.plan-page__card {
  position: relative;
  padding: 16px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.plan-page__card-stripe {
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background: #e1e0da;
  border-radius: 12px 0 0 12px;
}

.plan-page__card-stripe--active {
  background: #2f6c00;
}

.plan-page__card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
}

.plan-page__card-head {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: flex-start;
}

.plan-page__card-title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.plan-page__card-title {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

.plan-page__card-subtitle {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}

.plan-page__card-menu {
  width: 4px;
  height: 22px;
  padding: 3px 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
}

.plan-page__dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #454745;
}

.plan-page__card-pills {
  display: flex;
  flex-direction: row;
  gap: 4px;
  padding-top: 8px;
}

.plan-page__pill {
  padding: 4px 8px;
  border-radius: 9999px;
  background: #e8ebe6;
  color: #41493a;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
}

/* ===== 新建计划入口卡 ===== */
.plan-page__new-entry {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 8px;
  height: 96px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #c1cab5;
}

.plan-page__new-entry-icon {
  width: 14px;
  height: 14px;
  display: block;
}

.plan-page__new-entry-text {
  color: #2f6c00;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

/* ===== 新建计划表单 ===== */
.plan-page__form-wrap {
  padding-top: 32px;
}

.plan-page__form {
  padding: 16px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 卡片切换淡入过渡：点击"新建计划"后表单卡从透明渐显，视觉过渡自然 */
.plan-page__form--fade-in {
  animation: plan-page-fade-in 0.3s ease-out;
}

@keyframes plan-page-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.plan-page__form-heading {
  color: #0e0f0c;
  font-size: 18px;
  line-height: 24px;
  font-weight: 600;
  padding-bottom: 8px;
}

.plan-page__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.plan-page__label {
  color: #454745;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.plan-page__placeholder {
  color: #868685;
  font-size: 16px;
}

.plan-page__input {
  height: 41px;
  padding: 10px 12px 8px;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 6px;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  color: #0e0f0c;
  font-size: 16px;
  line-height: 21px;
}

.plan-page__textarea {
  height: 66px;
  padding: 8px 12px 32px;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 6px;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
}

.plan-page__date-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.plan-page__date-input {
  flex: 1;
  height: 42px;
  padding: 8px 12px;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 6px;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
}

/* 日期范围中间的右箭头（CSS 绘制） */
.plan-page__arrow {
  width: 7px;
  height: 7px;
  border-top: 1.5px solid #454745;
  border-right: 1.5px solid #454745;
  transform: rotate(45deg);
  flex-shrink: 0;
}

/* ===== 提醒时间 ===== */
.plan-page__time-label-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.plan-page__add-time {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 4px;
}

.plan-page__add-time-icon {
  width: 14px;
  height: 14px;
  display: block;
}

.plan-page__add-time-text {
  color: #2f6c00;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
}

.plan-page__time-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 4px;
  padding: 4px;
  box-sizing: border-box;
  background: #e8ebe6;
  border-radius: 6px;
  height: 40px;
}

.plan-page__time-input {
  flex: 1;
  height: 32px;
  padding: 4px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 4px;
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
}

.plan-page__time-dash {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  flex-shrink: 0;
}

.plan-page__time-delete {
  width: 24px;
  height: 32px;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.plan-page__time-delete-icon {
  width: 16px;
  height: 18px;
  display: block;
}

/* ===== 通知方式 ===== */
.plan-page__notify-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 31px;
  padding-top: 4px;
}

.plan-page__notify-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 7px;
}

.plan-page__checkbox {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  display: flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}

.plan-page__checkbox--checked {
  background: #2f6c00;
  box-shadow: inset 0 0 0 1px #2f6c00;
}

/* 选中态对勾（CSS 绘制） */
.plan-page__checkmark {
  width: 6px;
  height: 10px;
  border-right: 2px solid #ffffff;
  border-bottom: 2px solid #ffffff;
  transform: rotate(45deg) translate(-1px, -1px);
}

.plan-page__notify-text {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}

/* ===== 保存按钮 ===== */
.plan-page__save {
  margin-top: 16px;
  height: 48px;
  padding: 12px 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #2f6c00;
  box-shadow: 0 4px 6px -4px rgba(0, 0, 0, 0.1), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.plan-page__save-icon {
  width: 20px;
  height: 20px;
  display: block;
}

.plan-page__save-text {
  color: #ffffff;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}
</style>
