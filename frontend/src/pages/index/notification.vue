<template>
  <view class="notification-page">
    <NoticeButton :has-notification="hasNotification" />

    <view class="notification-page__main">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/profile 等页面保持一致） -->
      <PageHeader title="通知方式" :desc="`管理您的提醒接收渠道，确保不错过任何重要${'\n'}提醒。`" />

      <!-- 通知方式列表 -->
      <view class="notification-page__section">
        <!-- 站内信 -->
        <view class="notification-page__card">
          <view class="notification-page__card-info">
            <image class="notification-page__card-icon" :src="znxIcon" mode="aspectFit" />
            <view class="notification-page__card-text">
              <text class="notification-page__card-title">站内信</text>
              <text class="notification-page__card-subtitle">wuzuniao_com</text>
            </view>
          </view>
          <view class="notification-page__card-delete" @click="handleDelete('znx')">
            <image class="notification-page__card-delete-icon" :src="deleteIcon" mode="aspectFit" />
          </view>
        </view>

        <!-- 邮件 -->
        <view class="notification-page__card">
          <view class="notification-page__card-info">
            <image class="notification-page__card-icon" :src="yxIcon" mode="aspectFit" />
            <view class="notification-page__card-text">
              <text class="notification-page__card-title">邮件</text>
              <text class="notification-page__card-subtitle">xpg@wuzuniao.com</text>
            </view>
          </view>
          <view class="notification-page__card-delete" @click="handleDelete('yx')">
            <image class="notification-page__card-delete-icon" :src="deleteIcon" mode="aspectFit" />
          </view>
        </view>
      </view>

      <!-- 添加新方式入口卡（点击后切换为"新建通知方式"表单卡） -->
      <view class="notification-page__add" v-if="!showForm" @click="handleAdd">
        <view class="notification-page__add-plus">
          <view class="notification-page__add-plus-h"></view>
          <view class="notification-page__add-plus-v"></view>
        </view>
        <text class="notification-page__add-text">添加新的通知方式</text>
      </view>

      <!-- 新建通知方式表单卡（默认隐藏，点击"添加新的通知方式"后显示，淡入过渡） -->
      <view v-if="showForm">
        <view class="notification-page__form notification-page__form--fade-in">
          <text class="notification-page__form-heading">新建通知方式</text>

          <!-- 通知名称 -->
          <view class="notification-page__field">
            <text class="notification-page__label">通知名称</text>
            <input
              class="notification-page__input"
              placeholder="例如：站内信"
              placeholder-class="notification-page__placeholder"
              :placeholder-style="phStyle('name')"
              @focus="onFocus('name')"
              @blur="onBlur"
            />
          </view>

          <!-- 接收地址 -->
          <view class="notification-page__field">
            <text class="notification-page__label">接收地址</text>
            <input
              class="notification-page__input"
              placeholder="例如：邮箱地址"
              placeholder-class="notification-page__placeholder"
              :placeholder-style="phStyle('address')"
              @focus="onFocus('address')"
              @blur="onBlur"
            />
          </view>

          <!-- 保存按钮 -->
          <view class="notification-page__save" @click="handleSave">
            <text class="notification-page__save-text">保存通知</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 通知方式页（notification.vue）
 * --------------------------------------------------------------------------
 * 功能：管理用户接收提醒的渠道
 *  - 通知方式列表：展示已配置的站内信、邮件等渠道（含名称、地址、删除入口）
 *  - 卡片切换：默认显示"添加新的通知方式"入口卡，点击后淡入切换为"新建通知方式"表单卡
 *  - 表单字段：通知名称、接收地址
 *  - 保存通知：提交表单（当前为占位 toast，待接入后端 API）
 * 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
 */
import { ref } from 'vue'
import NoticeButton from '../../components/NoticeButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import znxIcon from '../../assets/images/tz_znx.png'
import yxIcon from '../../assets/images/tz_yx.png'
import deleteIcon from '../../assets/images/shanchu_hui.png'

// 设计稿顶部铃铛含红点，使用激活态图标
const hasNotification = true

// 卡片切换：默认显示"添加新的通知方式"入口卡，点击后切换为"新建通知方式"表单卡
const showForm = ref(false)

// 输入框 placeholder 聚焦交互：聚焦变浅灰 #c0c0c0，失焦恢复 placeholder-class 原始色
const { onFocus, onBlur, phStyle } = usePlaceholder()

function handleDelete(type) {
  const name = type === 'znx' ? '站内信' : '邮件'
  uni.showToast({ title: `删除${name}通知`, icon: 'none' })
}

function handleAdd() {
  // 点击"添加新的通知方式"入口卡：切换显示"新建通知方式"表单卡
  showForm.value = true
}

function handleSave() {
  uni.showToast({ title: '保存通知', icon: 'none' })
}
</script>

<style lang="scss">
.notification-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.notification-page__main {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 100px 24px 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ===== 通知方式列表 ===== */
.notification-page__section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.notification-page__card {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
}

.notification-page__card-info {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.notification-page__card-icon {
  width: 48px;
  height: 48px;
  display: block;
  flex-shrink: 0;
}

.notification-page__card-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.notification-page__card-title {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

.notification-page__card-subtitle {
  color: #454745;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
  padding-top: 2px;
}

.notification-page__card-delete {
  width: 32px;
  height: 34px;
  padding: 8px;
  box-sizing: border-box;
  border-radius: 9999px;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.notification-page__card-delete-icon {
  width: 16px;
  height: 18px;
  display: block;
}

/* ===== 添加新方式 ===== */
.notification-page__add {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 12px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #c1cab5;
}

/* CSS 绘制加号图标（避免引入额外二进制资源） */
.notification-page__add-plus {
  position: relative;
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.notification-page__add-plus-h {
  position: absolute;
  top: 50%;
  left: 0;
  width: 14px;
  height: 2px;
  background: #2f6c00;
  transform: translateY(-50%);
}

.notification-page__add-plus-v {
  position: absolute;
  left: 50%;
  top: 0;
  width: 2px;
  height: 14px;
  background: #2f6c00;
  transform: translateX(-50%);
}

.notification-page__add-text {
  color: #2f6c00;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

/* ===== 新建通知方式表单卡（样式参照 plan 页"新建计划详情"卡片，保持设计一致） ===== */
.notification-page__form {
  padding: 16px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 卡片切换淡入过渡：点击"添加新的通知方式"后表单卡从透明渐显，视觉过渡自然 */
.notification-page__form--fade-in {
  animation: notification-page-fade-in 0.3s ease-out;
}

@keyframes notification-page-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notification-page__form-heading {
  color: #0e0f0c;
  font-size: 18px;
  line-height: 24px;
  font-weight: 600;
  padding-bottom: 8px;
}

.notification-page__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.notification-page__label {
  color: #454745;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.notification-page__placeholder {
  color: #868685;
  font-size: 16px;
}

.notification-page__input {
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

/* ===== 保存通知按钮（参照 plan 页保存按钮样式） ===== */
.notification-page__save {
  margin-top: 16px;
  height: 48px;
  padding: 12px 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #2f6c00;
  box-shadow: 0 4px 6px -4px rgba(0, 0, 0, 0.1), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  align-items: center;
}

.notification-page__save-text {
  color: #ffffff;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}
</style>
