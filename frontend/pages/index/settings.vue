<template>
  <view :data-theme="themeKey" class="settings-page">
    <NoticeButton />

    <view class="settings-page__main">
      <!-- 用户资料卡 + 公告管理（靠近，减少间距） -->
      <view class="settings-page__near-group">
        <!-- 用户资料卡片 -->
        <view class="settings-page__profile-card guide-target-profile-card" @click="goProfileOrLogin">
          <view class="settings-page__profile-info">
            <text class="settings-page__profile-name">{{ displayName }}</text>
            <text class="settings-page__profile-slogan">{{ displaySlogan }}</text>
          </view>
          <view class="settings-page__profile-avatar-wrap">
            <image v-if="avatarUrl" class="settings-page__profile-avatar" :src="avatarUrl" mode="aspectFit" />
          </view>
        </view>

        <!-- 公共管理（仅管理员可见，紧贴用户资料卡下方；占半行：无图标、无副标题、无箭头，仅标题） -->
        <view v-if="isAdmin" class="settings-page__admin-row">
          <view class="settings-page__admin-card" @click="goAnnouncement">
            <text class="settings-page__admin-title">公告管理</text>
          </view>
        </view>
      </view>

      <!-- 分组 1：制定计划 + 通知方式（删除冷静期内整体置灰禁点击，独占整行） -->
      <view class="settings-page__group1" :class="{ 'settings-page__group1--disabled': isDeletionScheduled }">
        <view class="settings-page__link-card settings-page__link-card--plan guide-target-plan-method" @click="!isDeletionScheduled && goPlan()">
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

        <view class="settings-page__link-card guide-target-notification-method" @click="!isDeletionScheduled && goNotification()">
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

      <!-- 分组 2：帮助中心 + 联系我们 + 服务协议 + 隐私政策 -->
      <view class="settings-page__group2">
        <view class="settings-page__group2-item settings-page__group2-item--bordered" @click="goHelp">
          <text class="settings-page__group2-text">帮助中心</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="settings-page__group2-item settings-page__group2-item--bordered" @click="goContact">
          <text class="settings-page__group2-text">联系我们</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="settings-page__group2-item settings-page__group2-item--bordered" @click="goAgreement">
          <text class="settings-page__group2-text">服务协议</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="settings-page__group2-item" @click="goPrivacy">
          <text class="settings-page__group2-text">隐私政策</text>
          <view class="u-arrow-right"></view>
        </view>
      </view>
    </view>

    <BottomNav active="settings" />

    <!-- 新手引导遮罩（仅在引导激活时渲染） -->
    <BeginnerGuide />
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
import { computed, ref, onMounted, watch, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import NoticeButton from '../../components/NoticeButton.vue'
import BottomNav from '../../components/BottomNav.vue'
import BeginnerGuide from '../../components/BeginnerGuide.vue'
import touxiangHei from '../../assets/images/touxiang/hei.png'
import touxiangHong from '../../assets/images/touxiang/hong.png'
import touxiangLan from '../../assets/images/touxiang/lan.png'
import { useUserStore } from '../../store/modules/user'
import { useGuideStore } from '../../store/modules/guide'
import { listNotificationChannels } from '../../api/modules/notification'
import { listPlans } from '../../api/modules/plan'
import { useShare } from '../../composables/useShare'
import { useGuideTarget } from '../../composables/useGuideTarget'

useShare({ title: '设置' })

const userStore = useUserStore()
const guideStore = useGuideStore()

// 新手引导：上报用户资料卡片、通知方式、制定计划入口位置
// 解构 requery 方法，供管理员按钮出现导致布局变化时手动重新查询
const { requery: requeryProfile } = useGuideTarget('profile-card', '.guide-target-profile-card')
const { requery: requeryNotification } = useGuideTarget('notification-method', '.guide-target-notification-method')
const { requery: requeryPlan } = useGuideTarget('plan-method', '.guide-target-plan-method')

// 账号是否处于删除冷静期（status=0）
const isDeletionScheduled = computed(() => userStore.userInfo?.status === 0)

// 是否为管理员（role=7）
const isAdmin = computed(() => userStore.userInfo?.role === 7)

// 管理员按钮出现/消失会导致设置页布局变化（公告管理卡片插入用户资料卡与功能入口之间），
// 引导激活时需重新查询所有目标位置，确保高亮与实际按钮匹配
watch(isAdmin, () => {
  if (!guideStore.isActive) return
  nextTick(() => {
    setTimeout(() => {
      requeryProfile()
      requeryNotification()
      requeryPlan()
    }, 150)
  })
})

// 用户的通知渠道列表和计划列表（从数据库动态加载）
const channels = ref([])
const plans = ref([])

// 计算属性：第一个进行中的计划名称（无则返回空字符串）
const activePlanName = computed(() => {
  const activePlan = plans.value.find(p => p.status === 1)
  return activePlan ? activePlan.name : ''
})

// 计算属性：右侧展示的主通知方式名称
// 规则：在所有启用（enabled=true）的渠道中优先展示第一个非站内信方式；
// 未启用的渠道一律不展示；站内信优先级最低，仅当未设置任何其他通知方式时才展示。
const notificationTypeName = computed(() => {
  const enabledChannels = channels.value.filter(c => c.enabled)
  const primary = enabledChannels.find(c => c.channel_type !== '站内信')
  if (primary) return primary.channel_type
  const znx = enabledChannels.find(c => c.channel_type === '站内信')
  return znx ? znx.channel_type : ''
})

// 加载用户通知渠道列表
async function loadChannels() {
  if (!userStore.userInfo) return
  try {
    const res = await listNotificationChannels()
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
    const res = await listPlans()
    if (res.code === 0 && res.data) {
      plans.value = res.data
    }
  } catch (e) {
    console.warn('加载计划列表失败', e)
  } finally {
    // 引导激活时重新查询目标位置：loadPlans 完成后"进行中"徽章显示/隐藏会改变
    // plan-method 卡片高度，进而影响 notification-method 位置（group1 两卡片贴合）
    if (guideStore.isActive) {
      nextTick(() => {
        setTimeout(() => {
          requeryProfile()
          requeryNotification()
          requeryPlan()
        }, 150)
      })
    }
  }
}

onMounted(() => {
  loadChannels()
  loadPlans()
})

// 新手引导：页面显示时上报当前页面（引导激活时推进/回退步骤）
onShow(() => {
  guideStore.onPageEnter('settings')
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
  // 新手引导：点击「通知方式」后推进到「制定计划」步骤（通知方式页内不再有引导蒙版，用户自由操作）
  if (guideStore.isActive && guideStore.currentStepData?.target === 'notification-method') {
    guideStore.skipToStepByTarget('plan-method')
  }
  uni.navigateTo({ url: '/pages/index/notification' })
}

function goPlan() {
  uni.navigateTo({ url: '/pages/index/plan' })
}

// 跳转到公告管理页
function goAnnouncement() {
  navigate('/pages/user/announcement')
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

function goAgreement() {
  navigate('/pages/user/agreement')
}
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
.settings-page {
  /* 撑满至少一屏：小程序端原生 page 元素不携带 data-theme，其背景取 :root,page 默认值（绿），
     内容不足一屏时底部会显示默认绿底、不随主题切换；此处 min-height:100vh 使页面根 view
     （带 data-theme）的主题背景覆盖整个视口，消除底部色差。box-sizing:border-box 含 padding，
     内容不足一屏时高度恰为一屏、无多余滚动条；内容超屏时自然滚动。 */
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
  /* 底部留白与记录页一致：240rpx（BottomNav 高 + 余量），
     使最后元素到导航栏顶部距离同记录页 */
  padding-bottom: 240rpx;
}

.settings-page__main {
  /* padding-top 105px：通知按钮 top约50px + 高40px = 底部约90px，留 15px 间隙避免与内容重叠 */
  padding: 210rpx 48rpx 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
}

/* ===== 用户资料卡片 ===== */
.settings-page__profile-card {
  position: relative;
  width: 100%;
  height: 290rpx;
  padding: 48rpx;
  box-sizing: border-box;
  border-radius: 48rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-card), var(--shadow-card);
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
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
  color: var(--color-text-primary);
  font-size: 56rpx;
  line-height: 70rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
  /* 用户名单行截断，过长时显示省略号 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-page__profile-slogan {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 52rpx;
  font-weight: 400;
  /* 个性签名最多显示3行，超出部分省略号截断 */
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.settings-page__profile-avatar-wrap {
  position: relative;
  z-index: 1;
  width: 176rpx;
  height: 176rpx;
  flex-shrink: 0;
}

.settings-page__profile-avatar {
  position: relative;
  width: 176rpx;
  height: 176rpx;
  z-index: 1;
}

/* ===== 分组 1 ===== */
.settings-page__group1 {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* 分组 1 两卡片贴合为整体：相邻边去圆角，仅保留外侧圆角，
   中间分隔由两卡片各自的 inset 1px 描边在贴合处自然形成 */
.settings-page__group1 .settings-page__link-card:first-child {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}
.settings-page__group1 .settings-page__link-card:last-child {
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

/* 删除冷静期内（status=0）分组整体置灰并禁用交互 */
.settings-page__group1--disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* 靠近用户资料卡的分组：用户卡 + 公告管理，间距更小（更贴近用户资料卡） */
.settings-page__near-group {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

/* 公共管理行：单列网格，列宽随内容收缩（max-content），卡片随之缩小 */
.settings-page__admin-row {
  display: grid;
  grid-template-columns: max-content;
}

/* 公共管理卡片：简洁文字卡（仅标题，无图标/副标题/箭头），宽度随文字收缩 */
.settings-page__admin-card {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  padding: 24rpx 32rpx;
  box-sizing: border-box;
  border-radius: 48rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-card), var(--shadow-card);
}

.settings-page__admin-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
  text-align: center;
}

.settings-page__link-card {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 32rpx 32rpx;
  box-sizing: border-box;
  border-radius: 48rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-card), var(--shadow-card);
}

.settings-page__link-card--plan {
  background: var(--color-selected-bg);
  box-shadow: inset 0 0 0 1px var(--color-brand-bg), var(--shadow-card);
}

.settings-page__link-left {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.settings-page__link-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

.settings-page__link-status {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
  padding-top: 8rpx;
}

.settings-page__link-status-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 9999px;
  background: var(--color-brand);
}

.settings-page__link-status-text {
  color: var(--color-brand);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

.settings-page__link-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
  /* justify-content:flex-end 让右侧内容靠右对齐，避免文字紧贴左侧标题；
     max-width:66.666% 限制右侧整体宽度不超过当前行的 2/3；
     min-width:0 允许文本截断 */
  justify-content: flex-end;
  max-width: 66.666%;
  min-width: 0;
}

.settings-page__link-value {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  /* 右对齐：文字块在容器内靠右展示 */
  text-align: right;
  /* 动态截断：超出最大宽度时省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-page__link-value--active {
  color: var(--color-brand);
  font-weight: 500;
}

/* 确保右箭头不被压缩 */
.settings-page__link-right .u-arrow-right {
  flex-shrink: 0;
}

/* ===== 右箭头颜色变体（基础样式复用全局 .u-arrow-right，此处仅覆盖颜色） ===== */
.settings-page__arrow--green {
  border-left-color: var(--color-brand);
}

/* ===== 分组 2 ===== */
.settings-page__group2 {
  border-radius: 48rpx;
  background: var(--color-card-bg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.settings-page__group2-item {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx;
  box-sizing: border-box;
  height: 98rpx;
}

.settings-page__group2-item--bordered {
  border-bottom: 1px solid var(--color-separator);
}

.settings-page__group2-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 * 规则：将本页面主要容器的宽度、卡片宽度、按钮尺寸锁定为设计稿原 px 值
 */
@media screen and (min-width: 768px) {
  /* 主容器内边距与间距 */
  .settings-page {
    padding-bottom: 120px;
  }
  .settings-page__main {
    padding: 105px 24px 0;
    gap: 32px;
  }
  /* 用户资料卡片 */
  .settings-page__profile-card {
    height: 145px;
    padding: 24px;
    border-radius: 24px;
  }
  .settings-page__profile-name {
    font-size: 28px;
    line-height: 35px;
    padding-bottom: 8px;
  }
  .settings-page__profile-slogan {
    font-size: 16px;
    line-height: 26px;
  }
  .settings-page__profile-avatar-wrap {
    width: 88px;
    height: 88px;
  }
  .settings-page__profile-avatar {
    width: 88px;
    height: 88px;
  }
  /* 靠近用户资料卡分组 */
  .settings-page__near-group {
    gap: 16px;
  }
  /* 公共管理行（单列网格） */
  .settings-page__admin-row {
    gap: 16px;
  }
  /* 公共管理卡片 */
  .settings-page__admin-card {
    padding: 12px 16px;
    border-radius: 24px;
  }
  .settings-page__admin-title {
    font-size: 16px;
    line-height: 24px;
  }
  /* 分组 1 */
  .settings-page__group1 {
    gap: 0;
  }
  .settings-page__link-card {
    padding: 16px 16px;
    border-radius: 24px;
  }
  .settings-page__link-left {
    gap: 4px;
  }
  .settings-page__link-title {
    font-size: 16px;
    line-height: 24px;
  }
  .settings-page__link-status {
    gap: 4px;
    padding-top: 4px;
  }
  .settings-page__link-status-dot {
    width: 8px;
    height: 8px;
  }
  .settings-page__link-status-text {
    font-size: 12px;
    line-height: 16px;
  }
  .settings-page__link-right {
    gap: 8px;
  }
  .settings-page__link-value {
    font-size: 16px;
    line-height: 24px;
  }
  /* 分组 2 */
  .settings-page__group2 {
    border-radius: 24px;
  }
  .settings-page__group2-item {
    padding: 12px 16px;
    height: 49px;
  }
  .settings-page__group2-text {
    font-size: 16px;
    line-height: 24px;
  }
}
</style>
