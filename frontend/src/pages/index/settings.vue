<template>
  <view class="settings-page">
    <NoticeButton :has-notification="hasNotification" />

    <view class="settings-page__main">
      <!-- 用户资料卡片 -->
      <view class="settings-page__profile-card" @click="goProfileOrLogin">
        <view class="settings-page__profile-card-glow"></view>
        <view class="settings-page__profile-info">
          <text class="settings-page__profile-name">{{ displayName }}</text>
          <text class="settings-page__profile-slogan">{{ displaySlogan }}</text>
        </view>
        <view class="settings-page__profile-avatar-wrap">
          <image v-if="avatarUrl" class="settings-page__profile-avatar" :src="avatarUrl" mode="aspectFit" />
        </view>
      </view>

      <!-- 分组 1：制定计划 + 通知方式（删除冷静期内置灰禁点击） -->
      <view class="settings-page__group1" :class="{ 'settings-page__group1--disabled': isDeletionScheduled }">
        <view class="settings-page__link-card settings-page__link-card--plan" @click="!isDeletionScheduled && goPlan()">
          <view class="settings-page__link-left">
            <text class="settings-page__link-title">制定计划</text>
            <!-- 仅当存在进行中的计划时显示"进行中"状态徽章 -->
            <view class="settings-page__link-status" v-if="activePlanName">
              <view class="settings-page__link-status-dot"></view>
              <text class="settings-page__link-status-text">进行中</text>
            </view>
          </view>
          <view class="settings-page__link-right">
            <!-- 动态展示第一个进行中的计划名称，无则显示空 -->
            <text v-if="activePlanName" class="settings-page__link-value settings-page__link-value--active">{{ activePlanName }}</text>
            <view class="u-arrow-right settings-page__arrow--green"></view>
          </view>
        </view>

        <view class="settings-page__link-card" @click="!isDeletionScheduled && goNotification()">
          <view class="settings-page__link-left">
            <text class="settings-page__link-title">通知方式</text>
          </view>
          <view class="settings-page__link-right">
            <!-- 动态展示除站内信外第一个通知类型名称，无则显示空 -->
            <text v-if="notificationTypeName" class="settings-page__link-value">{{ notificationTypeName }}</text>
            <view class="u-arrow-right"></view>
          </view>
        </view>
      </view>

      <!-- 分组 2：帮助中心 + 联系我们 + 隐私政策 -->
      <view class="settings-page__group2">
        <view class="settings-page__group2-item settings-page__group2-item--bordered" @click="goHelp">
          <text class="settings-page__group2-text">帮助中心</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="settings-page__group2-item settings-page__group2-item--bordered" @click="goContact">
          <text class="settings-page__group2-text">联系我们</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="settings-page__group2-item" @click="goPrivacy">
          <text class="settings-page__group2-text">隐私政策</text>
          <view class="u-arrow-right"></view>
        </view>
      </view>
    </view>

    <BottomNav active="settings" />
  </view>
</template>

<script setup>
/**
 * 设置页（settings.vue）
 * --------------------------------------------------------------------------
 * 功能：应用设置与功能入口聚合页
 *  - 用户资料卡：展示昵称、个性签名、头像
 *    - 已登录：显示用户信息，点击跳转 profile.vue
 *    - 未登录：用户名显示"请登录"，点击跳转 login.vue
 *  - 分组 1（功能入口）：制定计划（含进行中状态徽章 + 绿色箭头）、通知方式
 *  - 分组 2（帮助入口）：帮助中心、联系我们、隐私政策
 *  - 底部固定导航栏（BottomNav），当前激活项为"设置"
 */
import { computed, ref, onMounted } from 'vue'
import NoticeButton from '../../components/NoticeButton.vue'
import BottomNav from '../../components/BottomNav.vue'
import touxiangHei from '../../assets/images/touxiang/hei.png'
import touxiangHong from '../../assets/images/touxiang/hong.png'
import touxiangLan from '../../assets/images/touxiang/lan.png'
import { useUserStore } from '../../store/modules/user'
import { listNotificationChannels } from '../../api/modules/notification'
import { listPlans } from '../../api/modules/plan'
import { useShare } from '../../composables/useShare'

useShare({ title: '设置' })

const hasNotification = false
const userStore = useUserStore()

// 账号是否处于删除冷静期（status=0）
const isDeletionScheduled = computed(() => userStore.userInfo?.status === 0)

// 用户的通知渠道列表和计划列表（从数据库动态加载）
const channels = ref([])
const plans = ref([])

// 计算属性：第一个进行中的计划名称（无则返回空字符串）
const activePlanName = computed(() => {
  const activePlan = plans.value.find(p => p.status === 1)
  return activePlan ? activePlan.name : ''
})

// 计算属性：除"站内信"外第一个通知类型名称（无则返回空字符串）
const notificationTypeName = computed(() => {
  const ch = channels.value.find(c => c.channel_type !== '站内信')
  return ch ? ch.channel_type : ''
})

// 加载用户通知渠道列表
async function loadChannels() {
  if (!userStore.userInfo) return
  try {
    const res = await listNotificationChannels(userStore.userInfo.id)
    if (res.code === 0 && res.data) {
      channels.value = res.data
    }
  } catch (e) {
    // 静默失败，不影响页面渲染
    console.warn('加载通知渠道失败', e)
  }
}

// 加载用户计划列表
async function loadPlans() {
  if (!userStore.userInfo) return
  try {
    const res = await listPlans(userStore.userInfo.id)
    if (res.code === 0 && res.data) {
      plans.value = res.data
    }
  } catch (e) {
    console.warn('加载计划列表失败', e)
  }
}

onMounted(() => {
  loadChannels()
  loadPlans()
})

// 头像 key 与图片资源的映射
const avatarMap = {
  hei: touxiangHei,
  hong: touxiangHong,
  lan: touxiangLan
}

// 用户名显示：已登录显示 username（可能为空，如微信登录用户），未登录显示"请登录"
const displayName = computed(() => {
  if (userStore.userInfo) {
    return userStore.userInfo.username || ''
  }
  return '请登录'
})

// 个性签名显示：已登录显示 signature（可能为空），未登录显示默认文案
const displaySlogan = computed(() => {
  if (userStore.userInfo) {
    return userStore.userInfo.signature != null ? String(userStore.userInfo.signature) : ''
  }
  return '"保持热爱，奔赴山海，每一天都要好好生活。"'
})

// 用户头像：未登录使用默认头像 hong；已登录从数据库获取，字段为空则不显示头像
const avatarUrl = computed(() => {
  if (!userStore.userInfo) {
    return touxiangHong
  }
  const key = userStore.userInfo.avatar_url
  if (key && avatarMap[key]) {
    return avatarMap[key]
  }
  return ''
})

function goNotification() {
  uni.navigateTo({ url: '/pages/index/notification' })
}

function goPlan() {
  uni.navigateTo({ url: '/pages/index/plan' })
}

// 用户资料卡点击跳转：已登录跳转 profile.vue，未登录跳转 login.vue
function goProfileOrLogin() {
  const url = userStore.userInfo ? '/pages/user/profile' : '/pages/user/login'
  uni.navigateTo({
    url,
    fail: () => {
      uni.showToast({ title: '页面跳转失败', icon: 'none' })
    }
  })
}

// 统一导航辅助函数：失败时 toast 提示，避免静默跳转失败
function navigate(url) {
  uni.navigateTo({
    url,
    fail: () => {
      uni.showToast({ title: '页面跳转失败', icon: 'none' })
    }
  })
}

function goHelp() {
  navigate('/pages/user/help')
}

function goContact() {
  navigate('/pages/user/contact')
}

function goPrivacy() {
  navigate('/pages/user/privacy')
}
</script>

<style lang="scss">
.settings-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
  padding-bottom: 177px;
}

.settings-page__main {
  /* padding-top 105px：通知按钮 top约50px + 高40px = 底部约90px，留 15px 间隙避免与内容重叠 */
  padding: 105px 24px 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ===== 用户资料卡片 ===== */
.settings-page__profile-card {
  position: relative;
  width: 100%;
  height: 145px;
  padding: 24px;
  box-sizing: border-box;
  border-radius: 24px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e2e2e2, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
}

/* 右上角绿色渐变点缀：绝对定位 + 渐变到透明，仅作背景装饰，不影响头像 */
.settings-page__profile-card-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 160px;
  height: 160px;
  background: linear-gradient(
    225deg,
    rgba(159, 232, 112, 0.45) 0%,
    rgba(226, 246, 213, 0.18) 55%,
    transparent 100%
  );
  border-top-right-radius: 24px;
  z-index: 0;
  pointer-events: none;
}

.settings-page__profile-info {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
  /* min-width:0 是 flexbox 文本截断的关键，否则长文本会撑开容器挤压头像 */
  min-width: 0;
}

.settings-page__profile-name {
  color: #0e0f0c;
  font-size: 28px;
  line-height: 35px;
  font-weight: 600;
  padding-bottom: 8px;
  /* 用户名单行截断，过长时显示省略号 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-page__profile-slogan {
  color: #454745;
  font-size: 16px;
  line-height: 26px;
  font-weight: 400;
  /* 个性签名最多显示3行，超出部分省略号截断 */
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.settings-page__profile-avatar-wrap {
  position: relative;
  z-index: 1;
  width: 88px;
  height: 88px;
  flex-shrink: 0;
}

.settings-page__profile-avatar {
  position: relative;
  width: 88px;
  height: 88px;
  z-index: 1;
}

/* ===== 分组 1 ===== */
.settings-page__group1 {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 删除冷静期内（status=0）分组1整体置灰并禁用所有交互 */
.settings-page__group1--disabled {
  opacity: 0.5;
  pointer-events: none;
}

.settings-page__link-card {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 24px 16px;
  box-sizing: border-box;
  border-radius: 24px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e2e2e2, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.settings-page__link-card--plan {
  background: #e2f6d5;
  box-shadow: inset 0 0 0 1px #9fe870, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.settings-page__link-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.settings-page__link-title {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

.settings-page__link-status {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 4px;
  padding-top: 4px;
}

.settings-page__link-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #2f6c00;
}

.settings-page__link-status-text {
  color: #2f6c00;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
}

.settings-page__link-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  /* justify-content:flex-end 让右侧内容靠右对齐，避免文字紧贴左侧标题；
     max-width:66.666% 限制右侧整体宽度不超过当前行的 2/3；
     min-width:0 允许文本截断 */
  justify-content: flex-end;
  max-width: 66.666%;
  min-width: 0;
}

.settings-page__link-value {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
  /* 右对齐：文字块在容器内靠右展示 */
  text-align: right;
  /* 动态截断：超出最大宽度时省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-page__link-value--active {
  color: #2f6c00;
  font-weight: 500;
}

/* 确保右箭头不被压缩 */
.settings-page__link-right .u-arrow-right {
  flex-shrink: 0;
}

/* ===== 右箭头颜色变体（基础样式复用全局 .u-arrow-right，此处仅覆盖颜色） ===== */
.settings-page__arrow--green {
  border-left-color: #2f6c00;
}

/* ===== 分组 2 ===== */
.settings-page__group2 {
  border-radius: 24px;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.settings-page__group2-item {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  box-sizing: border-box;
  height: 49px;
}

.settings-page__group2-item--bordered {
  border-bottom: 1px solid #f3f3f4;
}

.settings-page__group2-text {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}
</style>
