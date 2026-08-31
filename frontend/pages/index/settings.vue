<template>
  <view :data-theme="themeKey" class="settings-page">
    <NoticeButton />

    <view class="settings-page__main">
      <!-- 用户资料卡 + 公告管理（靠近，减少间距） -->
      <view class="settings-page__near-group">
        <!-- 用户资料卡片（普通版式：未登录或角色等级 ≤1） -->
        <view v-if="!isAdminProfile" class="settings-page__profile-card guide-target-profile-card" @click="goProfileOrLogin">
          <!-- 左侧品牌色装饰竖条（设计稿样式，覆盖卡片左缘全高） -->
          <view class="settings-page__profile-accent"></view>
          <view class="settings-page__profile-info">
            <text class="settings-page__profile-name">{{ displayName }}</text>
            <text class="settings-page__profile-slogan">{{ displaySlogan }}</text>
          </view>
          <view class="settings-page__profile-avatar-wrap">
            <image v-if="avatarUrl" class="settings-page__profile-avatar" :src="avatarUrl" mode="aspectFit" />
          </view>
          <!-- 右上角 45° 斜切角（页面背景色三角覆盖形成，与右下 40px 圆角几何呼应） -->
          <view class="settings-page__profile-notch"></view>
        </view>

        <!-- 用户资料卡片（管理员版式：已登录且角色等级 >1；Kinetic Asymmetric Cut 设计稿——上绿 PRO 横幅 + 下深信息板错位叠放） -->
        <view v-else class="settings-page__kinetic-card guide-target-profile-card" @click="goProfileOrLogin">
          <!-- 上半：品牌绿横幅（PRO 徽标 + 头像直接落绿底、无环无裁剪），右下 48px 圆角 -->
          <view class="settings-page__kinetic-hero">
            <view class="settings-page__kinetic-pro-wrap">
              <text class="settings-page__kinetic-pro">{{ $t('settings.proBadge', { level: memberLevel }) }}</text>
            </view>
            <image v-if="avatarUrl" class="settings-page__kinetic-avatar" :src="avatarUrl" mode="widthFix" />
          </view>
          <!-- 下半：深色信息板（左上 48px 圆角，上叠 24px，弧外月牙露出绿横幅与白卡底） -->
          <view class="settings-page__kinetic-panel">
            <text class="settings-page__kinetic-name">{{ displayName }}</text>
            <view v-if="displaySlogan" class="settings-page__kinetic-slogan-box">
              <text class="settings-page__kinetic-slogan">{{ displaySlogan }}</text>
            </view>
          </view>
        </view>

        <!-- 会员卡片（仅登录的普通用户 role=0 可见；深色权益卡，样式与内容均为纯前端静态展示） -->
        <view v-if="showMemberCard" class="settings-page__member-card">
          <view class="settings-page__member-glow"></view>
          <view class="settings-page__member-info">
            <view class="settings-page__member-badge">
              <image class="settings-page__member-badge-icon" :src="huiyuanIcon" mode="aspectFit" />
              <text class="settings-page__member-badge-text">{{ $t('settings.memberBadgeTitle') }}</text>
            </view>
            <text class="settings-page__member-title">{{ $t('settings.memberTitle') }}</text>
          </view>
          <view class="settings-page__member-price-row">
            <text class="settings-page__member-price">{{ $t('settings.memberPrice') }}</text>
            <view class="settings-page__member-price-meta">
              <text class="settings-page__member-price-original">{{ $t('settings.memberOriginalPrice') }}</text>
              <text class="settings-page__member-price-unit">{{ $t('settings.memberPriceUnit') }}</text>
            </view>
          </view>
          <view class="settings-page__member-btn" hover-class="settings-page__member-btn--hover" :hover-stay-time="70" @click="goMemberPay">
            <text class="settings-page__member-btn-text">{{ $t('settings.memberBuyNow') }}</text>
          </view>
        </view>

        <!-- 公共管理（仅管理员可见，紧贴用户资料卡下方；占半行：无图标、无副标题、无箭头，仅标题） -->
        <view v-if="isAdmin" class="settings-page__admin-row">
          <view class="settings-page__admin-card" @click="goAnnouncement">
            <text class="settings-page__admin-title">{{ $t('settings.announcementAdmin') }}</text>
          </view>
        </view>
      </view>

      <!-- 分组 1：制定计划 + 通知方式（删除冷静期内整体置灰禁点击，独占整行） -->
      <view class="settings-page__group1" :class="{ 'settings-page__group1--disabled': isDeletionScheduled }">
        <view class="settings-page__link-card settings-page__link-card--plan guide-target-plan-method" @click="!isDeletionScheduled && goPlan()">
          <view class="settings-page__link-left">
            <text class="settings-page__link-title">{{ $t('settings.plan') }}</text>
            <!-- 仅当存在进行中的计划时显示"进行中"状态徽章 -->
            <view class="settings-page__link-status" v-if="activePlanName">
              <view class="settings-page__link-status-dot"></view>
              <text class="settings-page__link-status-text">{{ $t('settings.planActive') }}</text>
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
            <text class="settings-page__link-title">{{ $t('settings.notification') }}</text>
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
          <text class="settings-page__group2-text">{{ $t('settings.help') }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="settings-page__group2-item settings-page__group2-item--bordered" @click="goContact">
          <text class="settings-page__group2-text">{{ $t('settings.contact') }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="settings-page__group2-item settings-page__group2-item--bordered" @click="goAgreement">
          <text class="settings-page__group2-text">{{ $t('settings.agreement') }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="settings-page__group2-item" @click="goPrivacy">
          <text class="settings-page__group2-text">{{ $t('settings.privacy') }}</text>
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
 *  - 会员卡片：深色权益卡（徽章、主题权益标题、价格、抢购按钮），
 *    仅登录的普通用户（role=0）显示，未登录及 role≥1（含管理员）隐藏
 *  - 资料卡双版式：未登录/角色 0 用普通白卡版式；
 *    已登录且角色 ≥1 用管理员版式（Kinetic Asymmetric Cut：上绿 PRO 横幅 + 下深信息板，
 *    PRO 徽标后数字动态显示用户角色等级）
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
import huiyuanIcon from '../../assets/images/huiyuan.png'
import { useUserStore } from '../../store/modules/user'
import { useGuideStore } from '../../store/modules/guide'
import { listNotificationChannels } from '../../api/modules/notification'
import { listPlans } from '../../api/modules/plan'
import { useShare } from '../../composables/useShare'
import { useGuideTarget } from '../../composables/useGuideTarget'
import { t } from '../../locale'

useShare({ title: t('share.settings') })

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

// 用户角色等级（未登录为 0），驱动 PRO 徽标数字与管理员版式判断
const memberLevel = computed(() => userStore.userInfo?.role ?? 0)

// 是否使用管理员版式资料卡：已登录且角色等级 ≥1（Kinetic Asymmetric Cut 设计稿版式）
const isAdminProfile = computed(() => memberLevel.value >= 1)

// 是否显示会员卡片：仅登录且角色等级为 0（普通用户）时显示，未登录及 role≥1（含管理员）隐藏
const showMemberCard = computed(() => !!userStore.userInfo && userStore.userInfo.role === 0)

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
  return t('settings.login')
})

// 个性签名显示：已登录显示 signature（可能为空），未登录显示默认文案
const displaySlogan = computed(() => {
  if (userStore.userInfo) {
    return userStore.userInfo.signature != null ? String(userStore.userInfo.signature) : ''
  }
  return t('settings.defaultSlogan')
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

// 会员卡片「立即抢购」→ 会员支付页（user 分包，前端静态页）
function goMemberPay() {
  navigate('/pages/user/member-pay')
}

// 用户资料卡点击跳转：已登录跳转 profile.vue，未登录跳转 login.vue
function goProfileOrLogin() {
  const url = userStore.userInfo ? '/pages/user/profile' : '/pages/user/login'
  uni.navigateTo({
    url,
    fail: () => {
      uni.showToast({ title: t('common.navigateFailed'), icon: 'none' })
    }
  })
}

// 统一导航辅助函数：失败时 toast 提示，避免静默跳转失败
function navigate(url) {
  uni.navigateTo({
    url,
    fail: () => {
      uni.showToast({ title: t('common.navigateFailed'), icon: 'none' })
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
  height: 286rpx;
  padding: 48rpx;
  box-sizing: border-box;
  /* 设计稿仅右下角 40px 大圆角，其余三角直角 */
  border-radius: 0 0 80rpx 0;
  background: var(--color-card-bg);
  /* 阴影收紧为紧贴边缘的微阴影（--shadow-card）：切角由页面背景色三角覆盖形成，
     大范围扩散阴影（--shadow-popup）会沿矩形轮廓在右上切角处残留穿帮，
     换用紧贴边框的 1px 级微影后切角旁阴影肉眼不可辨 */
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
}

/* 左缘品牌色装饰竖条（全高，绝对定位不参与 flex 布局） */
.settings-page__profile-accent {
  position: absolute;
  left: 0;
  top: 0;
  width: 12rpx;
  height: 100%;
  background: var(--color-brand-bg);
}

/* 右上角 45° 斜切角：40px×40px 页面背景色直角三角覆盖卡片角形成，
   斜边自顶边距右缘 40px 处切至右缘距顶 40px 处（设计稿实测值）；
   采用 border 三角 + var(--page-bg-color) 而非 clip-path——
   后者会连 box-shadow 一并裁掉且小程序端兼容性弱 */
.settings-page__profile-notch {
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-top: 80rpx solid var(--page-bg-color);
  border-left: 80rpx solid transparent;
}

/* ===== 用户资料卡片·管理员版式（Kinetic Asymmetric Cut，role>1） ===== */
/* 外层卡：底色取页面背景色（两块层叠衔接处的月牙区不露纯白，与页面浑然一体），
   左上/右下 48px 大圆角，overflow 裁出整体轮廓；
   阴影用紧贴边缘的 1px 级微影（--shadow-card）：大扩散阴影（--shadow-elevated）会在
   卡左右两侧的页面背景上残留约 4-6px 宽暗色带（尤其绿黑重叠高度的左右两端最显眼，
   实测卡缘外 2px 处 rgb(223,226,221) vs 页面 rgb(232,235,230)），与 profile-card 切角
   穿帮问题同源，换微影后卡外背景与页面浑然一体 */
.settings-page__kinetic-card {
  position: relative;
  width: 100%;
  box-sizing: border-box;
  border-radius: 96rpx 0 96rpx 0;
  background: var(--page-bg-color);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 上半绿横幅（上层）：品牌浅绿 + 自上而下白高光渐变，右下 48px 圆角——弧外月牙露
   底层黑板，形成「绿卡叠在黑卡上」的错位叠压关系；padding-right 24px 使头像
   距横幅右缘固定 24px */
.settings-page__kinetic-hero {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 48rpx;
  padding-right: 24px;
  border-radius: 0 0 96rpx 0;
  background-color: var(--color-brand-bg);
  background-image: linear-gradient(180deg, var(--color-highlight-strong), var(--color-highlight-faint));
}

/* PRO 文字容器：flex 基准取剩余宽度 100%（flex:1 1 100%，与固定 88px 头像按
   百分比分宽后收缩让位），文字在自身宽度内居中对齐 */
.settings-page__kinetic-pro-wrap {
  flex: 1 1 100%;
  min-width: 0;
  display: flex;
  flex-direction: row;
  justify-content: center;
}

/* PRO 徽标大字（设计稿 56px，粗体 + 斜体强调，带 1px 级微投影）；
   单行完整显示（不用省略号截断） */
.settings-page__kinetic-pro {
  flex-shrink: 0;
  color: var(--color-text-primary);
  font-size: 112rpx;
  line-height: 112rpx;
  font-weight: 700;
  font-style: italic;
  text-shadow: var(--shadow-card);
  white-space: nowrap;
}

/* 头像：不做圆形裁剪（widthFix 按图片原始比例完整显示），固定像素为图像自身大小
   （原图 88x88，不随容器宽度改变），固定距横幅右缘 24px */
.settings-page__kinetic-avatar {
  width: 88px;
  flex-shrink: 0;
  display: block;
}

/* 下半深色信息板（底层）：左上 48px 圆弧与右下角（外层卡容器圆弧）对称；
   上叠 24px 藏于上层绿横幅之后（绿卡叠黑卡），左上弧外区上段被绿横幅覆盖、
   下段露卡容器页面色（与页面背景一致）；padding-top 48px 使名字位于绿横幅底缘下方 24px 呼吸位 */
.settings-page__kinetic-panel {
  box-sizing: border-box;
  margin-top: -48rpx;
  padding: 96rpx 48rpx 48rpx;
  border-radius: 96rpx 0 0 0;
  background: var(--color-card-bg-inverse);
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

/* 用户名：品牌浅绿大字（设计稿 32px） */
.settings-page__kinetic-name {
  color: var(--color-brand-bg);
  font-size: 64rpx;
  line-height: 64rpx;
  font-weight: 400;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 签名框：仅左侧 4px 品牌绿竖线（设计稿实测，非四边描边） */
.settings-page__kinetic-slogan-box {
  border-left: 4px solid var(--color-brand-bg);
  padding: 8rpx 0 8rpx 32rpx;
}

.settings-page__kinetic-slogan {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--color-text-secondary-inverse);
  font-size: 32rpx;
  line-height: 52rpx;
  font-weight: 400;
  font-style: italic;
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
  font-weight: 700;
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

/* ===== 会员卡片（设计稿深色权益卡） ===== */
.settings-page__member-card {
  position: relative;
  width: 100%;
  /* 中文内容自然高度恰为 278px，min-height 兜底防其他语言长文案撑破 */
  min-height: 556rpx;
  /* near-group 间距 32rpx + 此处 32rpx = 64rpx（设计稿两卡间距 32px） */
  margin-top: 32rpx;
  padding: 48rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg-inverse);
  box-shadow: var(--shadow-popup);
  display: flex;
  flex-direction: column;
  gap: 48rpx;
  overflow: hidden;
}

/* 右上角品牌微光装饰圆（radial 渐隐，溢出部分被卡片裁剪） */
.settings-page__member-glow {
  position: absolute;
  top: -32rpx;
  right: -32rpx;
  width: 192rpx;
  height: 192rpx;
  border-radius: 9999px;
  background: radial-gradient(circle, var(--color-brand-glow-faint) 0%, transparent 100%);
}

.settings-page__member-info {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

/* 徽章行：会员图标 + 标题 */
.settings-page__member-badge {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
}

.settings-page__member-badge-icon {
  width: 32rpx;
  height: 42rpx;
  flex-shrink: 0;
}

.settings-page__member-badge-text {
  color: var(--color-brand-bg);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

.settings-page__member-title {
  color: var(--color-text-inverse);
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 400;
}

/* 价格行：左侧大价格顶对齐，右侧说明组贴底 */
.settings-page__member-price-row {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: row;
  min-height: 140rpx;
}

.settings-page__member-price {
  color: var(--color-brand-bg);
  font-size: 96rpx;
  line-height: 96rpx;
  font-weight: 700;
}

.settings-page__member-price-meta {
  display: flex;
  flex-direction: column;
  /* 底对齐：说明组贴价格行底部，与设计稿位置一致 */
  align-self: flex-end;
  margin-left: 20rpx;
}

.settings-page__member-price-original {
  color: var(--color-text-inverse);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
  /* 旧价格删除线（与会员支付页原价样式一致） */
  text-decoration: line-through;
}

.settings-page__member-price-unit {
  color: var(--color-brand-bg);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

/* 抢购按钮：品牌浅绿胶囊 */
.settings-page__member-btn {
  position: relative;
  z-index: 1;
  height: 96rpx;
  border-radius: 9999px;
  background: var(--color-brand-bg);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s ease-in-out, transform 0.1s ease-in-out;
}

/* 按压态（hover-class）：对应设计稿 hover opacity 0.8 / click scale 0.95 */
.settings-page__member-btn--hover {
  opacity: 0.8;
  transform: scale(0.95);
}

.settings-page__member-btn-text {
  color: var(--color-brand-dark);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
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
    height: 143px;
    padding: 24px;
    border-radius: 0 0 40px 0;
  }
  .settings-page__profile-accent {
    width: 6px;
  }
  .settings-page__profile-notch {
    border-top-width: 40px;
    border-left-width: 40px;
  }
  /* 管理员版式资料卡（Kinetic Asymmetric Cut） */
  .settings-page__kinetic-card {
    border-radius: 48px 0 48px 0;
  }
  .settings-page__kinetic-hero {
    padding: 24px;
    border-radius: 0 0 48px 0;
  }
  .settings-page__kinetic-pro {
    font-size: 56px;
    line-height: 56px;
  }
  .settings-page__kinetic-panel {
    margin-top: -24px;
    padding: 48px 24px 24px;
    border-radius: 48px 0 0 0;
    gap: 12px;
  }
  .settings-page__kinetic-name {
    font-size: 32px;
    line-height: 32px;
  }
  .settings-page__kinetic-slogan-box {
    border-left-width: 4px;
    padding: 4px 0 4px 16px;
  }
  .settings-page__kinetic-slogan {
    font-size: 16px;
    line-height: 26px;
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
  /* 会员卡片 */
  .settings-page__member-card {
    min-height: 278px;
    margin-top: 16px;
    padding: 24px;
    border-radius: 12px;
    gap: 24px;
  }
  .settings-page__member-glow {
    top: -16px;
    right: -16px;
    width: 96px;
    height: 96px;
  }
  .settings-page__member-info {
    gap: 8px;
  }
  .settings-page__member-badge {
    gap: 4px;
  }
  .settings-page__member-badge-icon {
    width: 16px;
    height: 21px;
  }
  .settings-page__member-title {
    font-size: 24px;
    line-height: 32px;
  }
  .settings-page__member-price-row {
    min-height: 70px;
  }
  .settings-page__member-price {
    font-size: 48px;
    line-height: 48px;
  }
  .settings-page__member-price-meta {
    margin-left: 10px;
  }
  .settings-page__member-price-original {
    font-size: 12px;
    line-height: 16px;
  }
  .settings-page__member-price-unit {
    font-size: 16px;
    line-height: 24px;
  }
  .settings-page__member-btn {
    height: 48px;
  }
  .settings-page__member-btn-text {
    font-size: 16px;
    line-height: 24px;
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
