<template>
  <view class="profile-page">
    <!-- 顶部通知按钮（复用项目通知组件，非导航栏） -->
    <NoticeButton :has-notification="hasNotification" />

    <view class="profile-page__main">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/notification 等页面保持一致） -->
      <PageHeader title="个人信息" :desc="`管理您的账户资料与安全设置，${'\n'}随时修改个人信息。`" />

      <!-- 分组 1：资料修改（修改签名、修改密码、修改邮箱） -->
      <view class="profile-page__group">
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="handleEdit('sign')">
          <text class="profile-page__group-text">修改签名</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="handleEdit('password')">
          <text class="profile-page__group-text">修改密码</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="profile-page__group-item" @click="handleEdit('email')">
          <text class="profile-page__group-text">修改邮箱</text>
          <view class="u-arrow-right"></view>
        </view>
      </view>

      <!-- 分组 2：退出登录（危险操作，单独分组并使用红色文字提示） -->
      <view class="profile-page__group">
        <view class="profile-page__group-item" @click="handleLogout">
          <text class="profile-page__group-text profile-page__group-text--danger">退出登录</text>
          <view class="u-arrow-right"></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 个人信息页（profile.vue）
 * --------------------------------------------------------------------------
 * 功能：管理当前登录用户的账户资料与安全设置
 *  - 分组 1（资料修改）：修改签名、修改密码、修改邮箱，点击进入对应表单（当前 toast 占位）
 *  - 分组 2（退出登录）：危险操作，单独分组并红色文字提示，弹窗二次确认避免误触
 * 视觉规范参照 settings.vue 分组卡片，保持应用内设置类页面一致性
 */
import NoticeButton from '../../components/NoticeButton.vue'
import PageHeader from '../../components/PageHeader.vue'

// 设计稿顶栏铃铛为绿色无红点态
const hasNotification = false

// 资料修改：签名 / 密码 / 邮箱，具体表单待后续接入，此处统一 toast 占位
function handleEdit(type) {
  const map = { sign: '修改签名', password: '修改密码', email: '修改邮箱' }
  uni.showToast({ title: map[type], icon: 'none' })
}

// 退出登录：弹窗二次确认，避免误触，符合危险操作交互规范
function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        uni.showToast({ title: '已退出登录', icon: 'none' })
      }
    }
  })
}
</script>

<style lang="scss">
.profile-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.profile-page__main {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 100px 24px 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ===== 分组卡片（样式参照 settings 页分组2，保持视觉一致） ===== */
.profile-page__group {
  border-radius: 24px;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.profile-page__group-item {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  box-sizing: border-box;
  height: 49px;
}

.profile-page__group-item--bordered {
  border-bottom: 1px solid #f3f3f4;
}

.profile-page__group-text {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

/* 退出登录危险操作文字：红色提示，区别于普通操作 */
.profile-page__group-text--danger {
  color: #d03238;
}
</style>
