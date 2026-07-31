<template>
  <view class="index-page">
    <view class="index-page__frame">
      <NoticeButton />

      <view
        class="index-page__main-canvas"
        :class="{
          'index-page__main-canvas--guest': !isLoggedIn,
          'index-page__main-canvas--empty': isLoggedIn && !hasActivePlans
        }"
      >
        <!-- 未登录：欢迎卡片（撑满首屏剩余高度；上方简介突出展示，中下方 logo 词云），点击词云区切换到介绍卡片 -->
        <view v-if="!isLoggedIn && !showIntroCard" class="index-page__welcome-card">
          <view class="index-page__welcome-copy">
            <text class="index-page__welcome-slogan">制定通用打卡计划并按时提醒、记录的跨端APP</text>
            <text class="index-page__intro-p">我非常重视安全，隐私数据加密传输、存储，请放心使用。若依旧担心数据安全，可<text class="index-page__intro-em">自行部署</text>此小程序。</text>
            <text class="index-page__intro-p">开源地址：<text class="index-page__intro-link" @click="copyRepoUrl">https://github.com/wuzuniao/yao</text></text>
          </view>
          <!-- 词云区：logo 居中且始终位于最上层，关键词每次进入首页在整块区域随机分布（位于 logo 下方图层）；点击整个区域切换到介绍卡片 -->
          <view class="index-page__welcome-cloud" @click="showIntroCard = true">
            <image class="index-page__welcome-logo" :src="brandLogo" mode="aspectFit" />
            <text
              v-for="word in cloudWords"
              :key="word.text"
              class="index-page__welcome-word"
              :class="[`index-page__welcome-word--s${word.size}`, `index-page__welcome-word--c${word.color}`]"
              :style="word.style"
            >{{ word.text }}</text>
          </view>
        </view>

        <!-- 未登录：介绍卡片（标题“按时吃药”，介绍功能与登录引导） -->
        <view v-else-if="!isLoggedIn" class="index-page__intro-card">
          <text class="index-page__intro-title">按时吃药</text>
          <view class="index-page__intro-scroll">
            <view class="index-page__intro-section">
              <text class="index-page__intro-section-title">主要功能</text>
              <text class="index-page__intro-p"><text class="index-page__intro-label">制定打卡计划：</text>设置计划内容、持续周期、每日提醒时间、通知方式等。到达提醒时间后，系统会自动发送通知进行提醒。</text>
              <text class="index-page__intro-p"><text class="index-page__intro-label">多途径通知：</text>支持<text class="index-page__intro-em">站内信、微信、邮件</text>等多种通知渠道。</text>
            </view>
            <view class="index-page__intro-section">
              <text class="index-page__intro-section-title">新手引导</text>
              <text class="index-page__intro-p"><text class="index-page__intro-strong">打卡功能必须登录后才能使用。</text></text>
              <text class="index-page__intro-p">若只在微信中使用，建议使用<text class="index-page__intro-em">微信一键登录</text>并使用<text class="index-page__intro-em">微信订阅消息通知</text>，此方式最方便。</text>
              <text class="index-page__intro-p">若账号想在无足鸟系列软件产品中通用，可<text class="index-page__intro-em">绑定邮箱并设置密码</text>。或者使用普通注册方式创建账号，<text class="index-page__intro-strong">一次注册，多端畅享</text>。使用普通注册方式时，<text class="index-page__intro-warning">请务必牢记账号与密码</text>，避免账号丢失或密码泄露。</text>
              <view class="index-page__intro-action" @click="startBeginnerGuide">
                <text class="index-page__intro-action-text">点我开启新手引导</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 已登录：原有任务卡片 / 空状态 + 公告卡 + 打卡按钮 -->
        <template v-else>
          <!-- 空状态提示（已登录无进行中计划时，展示新手引导卡片；样式参考未登录介绍卡片） -->
          <view v-if="!hasActivePlans" class="index-page__guide-card">
            <text class="index-page__guide-title" decode>新手引导</text>
            <view class="index-page__guide-content">
              <view class="index-page__guide-section">
                <text class="index-page__guide-line" decode><text class="index-page__guide-em">【可选】</text>点击设置页 <text class="index-page__guide-arrow" decode>-></text> 通知方式 <text class="index-page__guide-arrow" decode>-></text> 新增消息通知方式，建议使用微信订阅消息。</text>
                <text class="index-page__guide-line" decode>点击设置页 <text class="index-page__guide-arrow" decode>-></text> 制定计划 <text class="index-page__guide-arrow" decode>-></text> 创建打卡计划。</text>
                <text class="index-page__guide-line" decode>若APP不会操作，可参考<text class="index-page__guide-link">帮助中心</text>Q&A，或通过邮箱反馈问题。</text>
              </view>
            </view>
            <view class="index-page__guide-action" @click="startLoggedInGuide">
              <text class="index-page__guide-action-text" decode>点我重新开启新手引导</text>
            </view>
          </view>

          <!-- 任务卡片区域（已登录且有进行中计划时显示） -->
          <view v-else class="index-page__hero">
          <!-- 主要卡片（不设置点击事件，仅展示当前选中任务） -->
          <view class="index-page__primary-card">
            <view class="index-page__primary-copy">
              <text class="index-page__primary-title">{{ primaryPlan.name }}</text>
              <text class="index-page__primary-desc">{{ primaryPlan.remark || '无备注' }}</text>
            </view>
            <view class="index-page__status-badge">
              <view class="index-page__status-dot"></view>
              <text class="index-page__status-text">进行中</text>
            </view>
          </view>

          <!-- 次要卡片（仅2+进行中任务时显示，点击后与主要卡片内容互换） -->
          <view v-if="secondaryPlan" class="index-page__secondary-card" @click="handleSecondaryClick">
            <view class="index-page__secondary-copy">
              <text class="index-page__secondary-title">{{ secondaryPlan.name }}</text>
              <text class="index-page__secondary-desc">{{ secondaryPlan.remark || '无备注' }}</text>
            </view>
            <!-- 3+任务时右侧显示"..."按钮，点击展开任务列表；2个任务时不显示任何按钮 -->
            <view v-if="activePlans.length > 2" class="index-page__secondary-more" @click.stop="toggleTaskList">
              <text class="index-page__secondary-more-text">···</text>
            </view>
          </view>
        </view>

          <!-- 公告临时卡片（最近7天未读公告轮播，填充首页空白高度，位于任务卡与打卡按钮之间）；新手引导期间隐藏，避免与引导卡片/高亮区域冲突 -->
          <AnnouncementCard
            v-if="recentAnnouncements.length && !guideStore.isActive"
            :announcements="recentAnnouncements"
          />

          <!-- 立即打卡按钮（状态：灰色无任务 / 红色立即打卡 / 已完成 / 未到打卡时间） -->
          <view
            class="index-page__checkin-shell"
            :class="{ 'index-page__checkin-shell--empty': isLoggedIn && !hasActivePlans }"
          >
            <view
              class="index-page__checkin-button guide-target-checkin-button"
              :class="{
                'index-page__checkin-button--disabled': isButtonDisabled,
                'index-page__checkin-button--done': isCheckinDone,
                'index-page__checkin-button--waiting': isWaiting
              }"
              @click="handleCheckin"
              @longpress="handleLongPress"
              @touchend="handleLongPressEnd"
              @touchcancel="handleLongPressEnd"
            >
              <template v-if="longPressCountdown > 0">
                <text class="index-page__checkin-countdown">{{ longPressCountdown }}</text>
              </template>
              <template v-else>
                <image v-if="showCheckinIcon" class="index-page__checkin-icon" :src="checkinIcon" mode="aspectFit" />
                <text class="index-page__checkin-text">{{ checkinText }}</text>
              </template>
            </view>
          </view>
        </template>
      </view>

      <!-- 任务列表弹层（点击"..."展开，列出所有进行中任务，点击某任务替换到主要卡片） -->
      <view v-if="showTaskList" class="index-page__task-mask" @click="showTaskList = false">
        <view class="index-page__task-list" @click.stop>
          <text class="index-page__task-list-title">选择任务</text>
          <view
            v-for="plan in activePlans"
            :key="plan.id"
            class="index-page__task-item"
            :class="{ 'index-page__task-item--active': plan.id === primaryPlanId }"
            @click="handleSelectTask(plan)"
          >
            <text class="index-page__task-item-name">{{ plan.name }}</text>
            <text v-if="plan.id === primaryPlanId" class="index-page__task-item-check">✓</text>
          </view>
        </view>
      </view>

      <BottomNav active="home" />

      <!-- 新手引导遮罩（仅在引导激活时渲染，position:fixed 覆盖整屏） -->
      <BeginnerGuide />
    </view>
  </view>
</template>

<script setup>
/**
 * 首页（index.vue）
 * --------------------------------------------------------------------------
 * 功能：应用主入口，展示用户当日打卡任务与打卡按钮
 *  - 顶部通知按钮（NoticeButton）
 *  - 任务卡片：从 checkin_plans 表获取当前用户进行中计划，按"到达提醒时间且未打卡优先"规则排序
 *    - 排序规则：当前匹配区间未打卡的排前（冲突时按 priority 升序），已打卡/无提醒的排后（按最近提醒时间升序）
 *    - 主要卡片：展示当前选中任务，不设置点击事件，显示计划名称、备注
 *    - 次要卡片：展示第二个任务，点击后与主要卡片内容互换；3+任务时右侧显示"..."按钮
 *    - "..."按钮：3+任务时显示，点击展开任务列表（同主/次卡片排序规则），可选择任务替换到主要卡片
 *  - 空状态：未登录先显示欢迎卡片（撑满首屏剩余高度；上方简介 slogan 突出展示，
 *    中下方"免费/易用/安全/开源"词云每次进入首页随机分布在无足鸟 logo 周围/下方），
 *    点击词云区（含 logo）后单向切换为介绍卡片（含功能说明与开启新手引导入口）；已登录无进行中计划显示"新手引导"卡片，
 *    提供操作指引并支持一键开启引导（从步骤 1 开始，点击设置后自动跳到步骤 4 继续）
 *  - 立即打卡按钮（多状态）：
 *    - 灰色"无打卡任务"：未登录/无任务/不在计划日期范围内/无提醒时间
 *    - 橙色"未到打卡时间"：未到第一个提醒时间的"开始打卡时间"（提醒时间前2小时），不显示图标
 *    - 红色"立即打卡"：已到开始打卡时间且当前匹配区间未打卡
 *    - 绿色"已打卡"：当前匹配区间已匹配到打卡记录，持续到匹配区间结束（下一个中点或24:00）
 *    - 长按3秒：waiting/done 状态可长按3秒重置为"立即打卡"
 *    - 新手引导最后一步：在打卡按钮高亮区域内点击即完成引导，不触发正常打卡流程（即使按钮为 disabled/done/waiting 状态）
 *    - 打卡成功后不弹窗，按钮直接转为绿色"已打卡"状态
 *    - 打卡防抖：同一任务3秒内只允许点击一次
 *    - 新手引导期间禁用长按重置
 *    - 打卡记录匹配：按相邻提醒的中点划分匹配区间，覆盖全天0:00-24:00无间隙、无留白
 *    - 用户不在线时（onHide）不进行检查，清除定时器；onShow 时重启并立即同步
 */
import { ref, computed, onUnmounted, getCurrentInstance, nextTick } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import NoticeButton from '../../components/NoticeButton.vue'
import BottomNav from '../../components/BottomNav.vue'
import AnnouncementCard from '../../components/AnnouncementCard.vue'
import BeginnerGuide from '../../components/BeginnerGuide.vue'
import { useUserStore } from '../../store/modules/user'
import { useGuideStore } from '../../store/modules/guide'
import { listPlans } from '../../api/modules/plan'
import { createCheckin, listTodayCheckins } from '../../api/modules/checkin'
import { getRecentAnnouncements } from '../../api/modules/announcement'
import { listNotificationChannels } from '../../api/modules/notification'
import checkinInactiveIcon from '../../assets/images/daka_0.png'
import checkinDoneIcon from '../../assets/images/daka_1.png'
import brandLogo from '../../assets/images/touxiang/hong.png'
import { useShare } from '../../composables/useShare'
import { useWechatSubscribe } from '../../composables/useWechatSubscribe'
import { useGuideTarget } from '../../composables/useGuideTarget'

useShare({ title: '首页' })

const guideStore = useGuideStore()

// 新手引导：上报首页打卡按钮位置
useGuideTarget('checkin-button', '.guide-target-checkin-button')

// 未登录首屏：false 展示欢迎卡片，点击词云区后置为 true 展示介绍卡片（单向切换，不提供返回）
const showIntroCard = ref(false)

// ===== 欢迎卡片词云（每次进入首页随机生成位置/字号/颜色/旋转） =====
const CLOUD_WORD_TEXTS = ['免费', '易用', '安全', '开源']
// 字号档位（s1-s5）与颜色池（c1-c6，取自 global.scss 设计令牌：
// 品牌绿/品牌深绿/链接蓝/警告黄/成功绿/次要文本色）。
// 字号采用等差数列：s1 = CLOUD_SIZE_BASE，其后每档 +CLOUD_SIZE_STEP（档差固定、依次叠加），
// 渲染值由样式变体类定义，须与下方常量保持一致。
const CLOUD_SIZE_LEVELS = 5
const CLOUD_COLOR_COUNT = 6
const CLOUD_SIZE_BASE = 74   // s1 最小档字号(rpx)，保持不变
const CLOUD_SIZE_STEP = 18   // 档差(rpx)，逐档叠加（s2=92, s3=110, s4=128, s5=146）
// 由档位换算 rpx 字号（与 CSS 变体类一致），供词间互斥避让计算包围盒
function cloudSizeRpx(level) {
  return CLOUD_SIZE_BASE + (level - 1) * CLOUD_SIZE_STEP
}
// 词云关键词数据：{ text, size(1-5 字号档), color(1-6 颜色档), style(随机位置+旋转) }
const cloudWords = ref([])
// 组件实例：用于 createSelectorQuery().in() 限定查询范围（H5 端必须指定，否则 parentElement 为 null）
const instance = getCurrentInstance()

// Fisher-Yates 洗牌（返回新数组，不修改原数组）
function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

// 随机生成词云：颜色与字号均不重复（四词互不相同），字号从 5 档取 4（必含 s4/s5 之一）；
// 位置经测量词云容器实际尺寸后在容器内随机落点，并与已放置词做 AABB 互斥避让（词之间不重叠）。
// 字号/颜色通过变体类控制，便于平板媒体查询覆盖；位置以百分比存储（随容器缩放自适应）。
function randomizeCloud() {
  const count = CLOUD_WORD_TEXTS.length
  // 颜色不重复抽取（6 取 4）；字号不重复抽取（5 取 4，丢弃 1 档后仍含 s4/s5 之一）
  const colors = shuffle(Array.from({ length: CLOUD_COLOR_COUNT }, (_, i) => i + 1)).slice(0, count)
  const sizes = shuffle(Array.from({ length: CLOUD_SIZE_LEVELS }, (_, i) => i + 1)).slice(0, count)

  // 根据容器像素尺寸生成词云数据（W/H 为容器实际像素尺寸，未就绪时由调用方传回退估算值）
  const generateWords = (W, H) => {
    const margin = uni.upx2px(12) // 词间最小间距(px)
    const placed = []
    cloudWords.value = CLOUD_WORD_TEXTS.map((text, i) => {
      const Fpx = uni.upx2px(cloudSizeRpx(sizes[i]))
      // 2 字宽≈2F、行高1.2→高≈1.2F；旋转 ±12° 放大包围盒，外加 margin
      const hw = Fpx * 1.1 + margin
      const hh = Fpx * 0.8 + margin
      const maxX = Math.max(hw, W - hw)
      const maxY = Math.max(hh, H - hh)
      let cx
      let cy
      // 拒绝采样：在容器内随机落点，避开已放置词的 AABB，最多 80 次兜底
      for (let t = 0; t < 80; t++) {
        const px = hw + Math.random() * (maxX - hw)
        const py = hh + Math.random() * (maxY - hh)
        const clash = placed.some(
          (p) => Math.abs(px - p.cx) < hw + p.hw && Math.abs(py - p.cy) < hh + p.hh
        )
        if (!clash) {
          cx = px
          cy = py
          break
        }
      }
      if (cx === undefined) {
        cx = hw + Math.random() * (maxX - hw)
        cy = hh + Math.random() * (maxY - hh)
      }
      placed.push({ cx, cy, hw, hh })
      const rotate = Math.round(Math.random() * 24 - 12) // -12° ~ 12° 随机旋转
      const xPct = (cx / W) * 100
      const yPct = (cy / H) * 100
      return {
        text,
        size: sizes[i],
        color: colors[i],
        style: `left:${xPct.toFixed(1)}%;top:${yPct.toFixed(1)}%;transform:translate(-50%,-50%) rotate(${rotate}deg);`
      }
    })
  }

  // 测量词云容器像素尺寸（与 upx2px 换算单位一致），未就绪时回退估算值
  // #ifdef H5
  // H5 端使用 nextTick + DOM API 获取容器尺寸（createSelectorQuery 在 H5 端有 parentElement 兼容问题）
  nextTick(() => {
    const el = document.querySelector('.index-page__welcome-cloud')
    const W = el && el.offsetWidth > 0 ? el.offsetWidth : uni.upx2px(604)
    const H = el && el.offsetHeight > 0 ? el.offsetHeight : uni.upx2px(700)
    generateWords(W, H)
  })
  // #endif
  // #ifndef H5
  // 微信小程序端使用 createSelectorQuery（需 .in(instance.proxy) 限定组件上下文）
  uni.createSelectorQuery()
    .in(instance.proxy)
    .select('.index-page__welcome-cloud')
    .boundingClientRect()
    .exec((res) => {
      const rect = res && res[0]
      const W = rect && rect.width > 0 ? rect.width : uni.upx2px(604)
      const H = rect && rect.height > 0 ? rect.height : uni.upx2px(700)
      generateWords(W, H)
    })
  // #endif
}

// 未登录介绍卡片：点击开源地址复制到剪贴板
function copyRepoUrl() {
  uni.setClipboardData({
    data: 'https://github.com/wuzuniao/yao',
    success: () => {
      uni.showToast({ title: '链接已复制', icon: 'none' })
    }
  })
}

// 开启新手引导
function startBeginnerGuide() {
  guideStore.startGuide()
}

// 已登录用户从首页空状态开启新手引导：从步骤 1 开始，点击设置后自动跳到步骤 4
function startLoggedInGuide() {
  guideStore.startGuideForLoggedIn()
}

const userStore = useUserStore()

// 微信订阅消息（静默补授权，仅在微信小程序端生效）
const { requestSubscribe } = useWechatSubscribe()

// 进行中的计划列表（从数据库加载，按 priority 升序排序）
const activePlans = ref([])
// 当前主要卡片计划ID（null 表示使用列表第一项）
const primaryPlanId = ref(null)
// 当前次要卡片计划ID（null 表示使用列表第二项，点击次要卡片时与主要卡片互换）
const secondaryPlanId = ref(null)
// 是否显示任务列表弹层
const showTaskList = ref(false)
// 今日所有计划的打卡记录（按 plan_id 分组，用于排序与"匹配打卡记录"判定）
// 结构：{ [planId]: [{ timeId, minutes }] }，minutes = 实际打卡时间的小时*60+分钟
const allTodayCheckins = ref({})
// 最近 7 天公告列表（普通用户），用于首页临时卡片轮播
const recentAnnouncements = ref([])
// 当前用户的通知渠道列表（用于判断计划是否关联微信通知方式）
const userChannels = ref([])
// 状态刷新定时器（每分钟检查打卡时段变化）
let refreshTimer = null
// 长按3秒重置标志：true 时强制按钮为"立即打卡"可点击状态
const forceActive = ref(false)
// 长按计时器
let longPressTimer = null
// 长按倒计时秒数（0 表示未在倒计时）
const longPressCountdown = ref(0)
// 长按倒计时 interval
let longPressInterval = null
// 打卡防抖时间戳：同一任务3秒内只允许点击一次
let lastCheckinTime = 0

// ===== 计算属性 =====

const isLoggedIn = computed(() => !!userStore.userInfo)
const hasActivePlans = computed(() => activePlans.value.length > 0)

// 主要卡片计划
const primaryPlan = computed(() => {
  if (!activePlans.value.length) return null
  if (primaryPlanId.value !== null) {
    return activePlans.value.find(p => p.id === primaryPlanId.value) || activePlans.value[0]
  }
  return activePlans.value[0]
})

// 主要卡片计划今日打卡记录（从 allTodayCheckins 派生，供 checkinState 判定 done/active）
const todayCheckinMinutes = computed(() => {
  if (!primaryPlan.value) return []
  return allTodayCheckins.value[primaryPlan.value.id] || []
})

// 次要卡片计划（支持双 ref 跟踪，点击次要卡片时与主要卡片互换内容）
const secondaryPlan = computed(() => {
  if (activePlans.value.length < 2) return null
  if (secondaryPlanId.value !== null) {
    return activePlans.value.find(p => p.id === secondaryPlanId.value) || activePlans.value[1]
  }
  // 默认取第二个非主要卡片的计划
  const primaryId = primaryPlan.value?.id
  return activePlans.value.find(p => p.id !== primaryId) || activePlans.value[1]
})

// 当前是否在计划日期范围内
const isWithinDateRange = computed(() => {
  if (!primaryPlan.value) return false
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  const plan = primaryPlan.value
  // start_date <= today <= end_date
  return plan.start_date <= todayStr && todayStr <= plan.end_date
})

// 排序后的提醒时间列表（分钟数）
const sortedTimes = computed(() => {
  if (!primaryPlan.value) return []
  return (primaryPlan.value.notification_times || []).map(t => {
    const [h, m] = t.notification_time.split(':').map(Number)
    return { id: t.id, time: t.notification_time, minutes: h * 60 + m }
  }).sort((a, b) => a.minutes - b.minutes)
})

// 将 ISO 时间字符串（如 "2026-07-02T14:30:00"）转换为当日分钟数（14*60+30=870）
function parseIsoToMinutes(isoStr) {
  if (!isoStr) return 0
  const timePart = isoStr.split('T')[1] || ''
  const parts = timePart.split(':').map(Number)
  return (parts[0] || 0) * 60 + (parts[1] || 0)
}

// 计算每个提醒时间的匹配区间（按相邻中点划分，覆盖全天 0:00-24:00，无间隙、无留白）
// - 第一次提醒：[0:00, midpoint(t1, t2)]
// - 中间提醒：[midpoint(t_{i-1}, t_i), midpoint(t_i, t_{i+1})]
// - 最后一次提醒：[midpoint(t_{n-1}, t_n), 24:00]
function getMatchIntervals(times) {
  const intervals = []
  for (let i = 0; i < times.length; i++) {
    let start
    let end
    if (i === 0) {
      start = 0 // 0:00
    } else {
      start = Math.floor((times[i - 1].minutes + times[i].minutes) / 2)
    }
    if (i === times.length - 1) {
      end = 1440 // 24:00
    } else {
      end = Math.floor((times[i].minutes + times[i + 1].minutes) / 2)
    }
    intervals.push({ start, end })
  }
  return intervals
}

// 找当前时间所在的匹配区间索引（全天无留白，必定能找到）
function findCurrentTargetIndex(times, nowMinutes) {
  const intervals = getMatchIntervals(times)
  for (let i = 0; i < intervals.length; i++) {
    if (nowMinutes >= intervals[i].start && nowMinutes < intervals[i].end) {
      return i
    }
  }
  // 边界情况：恰好 24:00（1440分钟），归属最后一个区间
  return intervals.length - 1
}

// 判定某匹配区间是否已打卡（基于今日打卡记录）
function isIntervalChecked(times, intervalIndex) {
  if (todayCheckinMinutes.value.length === 0) return false
  const intervals = getMatchIntervals(times)
  const interval = intervals[intervalIndex]
  return todayCheckinMinutes.value.some(r => r.minutes >= interval.start && r.minutes < interval.end)
}

// 打卡状态计算：'disabled' | 'waiting' | 'active' | 'done'
// 判定优先级（从高到低）：
// 1. disabled: 未登录/无任务/不在日期范围/无提醒时间
// 2. forceActive: 用户长按3秒强制重置 → active（允许从 done/waiting 重新打卡）
// 3. done: 当前匹配区间已匹配到打卡记录（优先于时间窗口判断，不受 t_1-120 阻断）
// 4. waiting: 未到第一个提醒时间的"开始打卡时间"（t_1 - 120）
// 5. active: 已到开始打卡时间且当前匹配区间未打卡
const checkinState = computed(() => {
  if (!isLoggedIn.value || !hasActivePlans.value) return { status: 'disabled' }
  if (!primaryPlan.value) return { status: 'disabled' }
  if (!isWithinDateRange.value) return { status: 'disabled' }
  const times = sortedTimes.value
  if (times.length === 0) return { status: 'disabled' }

  const now = new Date()
  const nowMinutes = now.getHours() * 60 + now.getMinutes()

  // 找当前时间所在的匹配区间索引（全天无留白，必定能找到）
  const idx = findCurrentTargetIndex(times, nowMinutes)
  const target = times[idx]

  // 长按重置：强制为 active（优先级最高，允许已打卡后重新打卡）
  if (forceActive.value) {
    return { status: 'active', timeId: target.id }
  }

  // 判定当前匹配区间是否已打卡（优先于时间窗口判断）
  if (isIntervalChecked(times, idx)) {
    return { status: 'done', timeId: target.id }
  }

  // 未到第一个提醒的开始打卡时间（t_1 - 120）→ waiting
  if (nowMinutes < times[0].minutes - 120) {
    return { status: 'waiting' }
  }

  return { status: 'active', timeId: target.id }
})

// 按钮是否禁用（灰色"无打卡任务"）
const isButtonDisabled = computed(() => checkinState.value.status === 'disabled')

// 是否处于"已打卡"状态（当前提醒已匹配到打卡记录）
const isCheckinDone = computed(() => checkinState.value.status === 'done')

// 是否处于"未到打卡时间"状态
const isWaiting = computed(() => checkinState.value.status === 'waiting')

// 按钮文本
const checkinText = computed(() => {
  if (isButtonDisabled.value) return '无打卡任务'
  if (isWaiting.value) return '未到打卡时间'
  if (isCheckinDone.value) return '已打卡'
  return '立即打卡'
})

// 是否显示打卡图标（仅 active 和 done 显示图标，waiting/disabled 不显示）
const showCheckinIcon = computed(() => {
  const s = checkinState.value.status
  return s === 'active' || s === 'done'
})

// 打卡图标（已完成状态使用 daka_1.png，可打卡状态使用 daka_0.png）
const checkinIcon = computed(() => {
  return isCheckinDone.value ? checkinDoneIcon : checkinInactiveIcon
})

// 当前主要计划是否包含微信通知方式（用于打卡成功后决定是否自动补授权微信订阅消息）
const hasWechatNotification = computed(() => {
  if (!primaryPlan.value || !primaryPlan.value.channel_ids || !userChannels.value.length) return false
  return primaryPlan.value.channel_ids.some(channelId => {
    const channel = userChannels.value.find(c => c.id === channelId)
    return channel && channel.channel_type === '微信'
  })
})

// ===== 数据加载 =====

// 计算单个计划的排序键（用于主要/次要卡片及任务列表排序）
// 排序规则：
//   1. 第一键 dateGroup：今天在计划日期范围内（start_date <= today <= end_date）的排前（dateGroup=0），否则排后（dateGroup=1）
//   2. 第二键 group：提醒时间已到且当前匹配区间未打卡的排前（group=0），其余排后（group=1）
//      —— "提醒时间已到"判定为 nowMinutes >= 当前匹配区间对应的提醒时间（times[currentIdx].minutes）
//   3. 第三键 sortKey：
//      - group=0（提醒已到且未打卡）：按 priority 升序（冲突时优先级高的在前）
//      - group=1（提醒未到/已打卡/无提醒）：按"下一个最近提醒时间"升序（未来最近的任务在前，无提醒时间设为 Infinity 排最后）
//   4. 第四键 priority：group=1 同提醒时间时按优先级升序
//   5. 第五键 createdAt：保持稳定排序
function computePlanSortKey(plan, nowMinutes, checkinMinutesList) {
  const priority = plan.priority ?? 3
  const createdAt = new Date(plan.created_at || 0).getTime()

  // 第一键：今天是否在计划日期范围内
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  const dateGroup = (plan.start_date <= todayStr && todayStr <= plan.end_date) ? 0 : 1

  const times = (plan.notification_times || []).map(t => {
    const [h, m] = t.notification_time.split(':').map(Number)
    return { id: t.id, minutes: h * 60 + m }
  }).sort((a, b) => a.minutes - b.minutes)

  if (times.length === 0) {
    // 无提醒时间：归到 group=1，最近提醒时间设为 Infinity 排最后
    return { dateGroup, group: 1, sortKey: Infinity, priority, createdAt }
  }

  // 计算当前匹配区间索引（全天无留白，必定能找到）
  const intervals = getMatchIntervals(times)
  let currentIdx = intervals.length - 1
  for (let i = 0; i < intervals.length; i++) {
    if (nowMinutes >= intervals[i].start && nowMinutes < intervals[i].end) {
      currentIdx = i
      break
    }
  }

  // 判定当前匹配区间是否已打卡（checkinMinutesList 元素为 { timeId, minutes }，需取 .minutes 比较）
  const interval = intervals[currentIdx]
  const isChecked = (checkinMinutesList || []).some(m => m.minutes >= interval.start && m.minutes < interval.end)

  // 判定"提醒时间是否已到"：当前时间 >= 当前匹配区间对应的提醒时间
  // 例：提醒 8:00/16:00，当前 14:00 在 16:00 的匹配区间内，16:00 未到 → isReminderReached=false
  const isReminderReached = nowMinutes >= times[currentIdx].minutes

  // 计算下一个最近提醒时间（>= nowMinutes 的最小提醒时间，无则回绕到明天第一个 +1440）
  let nextReminder = Infinity
  for (const t of times) {
    if (t.minutes >= nowMinutes) {
      nextReminder = t.minutes
      break
    }
  }
  if (nextReminder === Infinity) {
    nextReminder = times[0].minutes + 1440
  }

  if (isReminderReached && !isChecked) {
    // group=0：提醒时间已到且当前匹配区间未打卡，sortKey 用 priority（冲突时优先级高的在前）
    return { dateGroup, group: 0, sortKey: priority, priority, createdAt }
  }
  // group=1：提醒时间未到、已打卡、或无提醒，sortKey 用下一个最近提醒时间
  return { dateGroup, group: 1, sortKey: nextReminder, priority, createdAt }
}

// 按新规则排序 plans：
//   1. 先按 dateGroup 升序：今天在计划日期范围内的排前
//   2. 日期分组内按 group/sortKey/priority/createdAt 排序
function sortPlansByCheckinStatus(plans, nowMinutes, allCheckinsByPlan) {
  return [...plans].sort((a, b) => {
    const keyA = computePlanSortKey(a, nowMinutes, allCheckinsByPlan[a.id])
    const keyB = computePlanSortKey(b, nowMinutes, allCheckinsByPlan[b.id])
    if (keyA.dateGroup !== keyB.dateGroup) return keyA.dateGroup - keyB.dateGroup
    if (keyA.group !== keyB.group) return keyA.group - keyB.group
    if (keyA.sortKey !== keyB.sortKey) return keyA.sortKey - keyB.sortKey
    if (keyA.priority !== keyB.priority) return keyA.priority - keyB.priority
    return keyA.createdAt - keyB.createdAt
  })
}

// 加载进行中的计划（仅 status=1，按"当前匹配区间未打卡优先，冲突时按优先级"规则排序）
async function loadActivePlans() {
  if (!isLoggedIn.value) {
    activePlans.value = []
    allTodayCheckins.value = {}
    return
  }
  try {
    const res = await listPlans()
    if (res.code === 0 && res.data) {
      // 仅保留进行中的计划
      const plans = res.data.filter(p => p.status === 1)
      // 加载今日所有计划打卡记录（排序依赖打卡状态）
      await loadAllTodayCheckins()
      // 按新规则排序：当前匹配区间未打卡的排前，已打卡的排后
      const now = new Date()
      const nowMinutes = now.getHours() * 60 + now.getMinutes()
      activePlans.value = sortPlansByCheckinStatus(plans, nowMinutes, allTodayCheckins.value)
      // 设置默认主要卡片（排序后第一项即最优；用户已手动选择且仍存在时保持）
      const currentPrimary = primaryPlanId.value
      const primaryExists = currentPrimary !== null && activePlans.value.some(p => p.id === currentPrimary)
      if (!primaryExists) {
        primaryPlanId.value = activePlans.value.length > 0 ? activePlans.value[0].id : null
      }
    }
  } catch (e) {
    console.warn('加载计划失败', e)
  }
}

// 加载当前用户的通知渠道列表，用于判断计划是否包含微信通知方式
async function loadUserChannels() {
  if (!isLoggedIn.value) {
    userChannels.value = []
    return
  }
  try {
    const res = await listNotificationChannels()
    if (res.code === 0 && res.data) {
      userChannels.value = res.data
    }
  } catch (e) {
    console.warn('加载通知渠道失败', e)
  }
}

// 加载最近 7 天公告（普通用户），用于首页临时卡片轮播；失败不阻塞首页
// 后端接口已排除 id=1 的公共模板，此处再做一次防御性过滤
async function loadRecentAnnouncements() {
  if (!isLoggedIn.value) {
    recentAnnouncements.value = []
    return
  }
  try {
    const res = await getRecentAnnouncements()
    if (res.code === 0 && res.data) {
      recentAnnouncements.value = res.data.filter(item => item.id !== 1)
    }
  } catch (e) {
    console.warn('加载公告失败', e)
  }
}

// 加载今日所有计划的打卡记录（按 plan_id 分组，用于排序与 done/active 判定）
async function loadAllTodayCheckins() {
  if (!isLoggedIn.value) {
    allTodayCheckins.value = {}
    return
  }
  try {
    const res = await listTodayCheckins()
    if (res.code === 0 && res.data) {
      const grouped = {}
      for (const r of res.data) {
        if (!r.actual_time) continue
        const planId = r.plan_id
        if (!grouped[planId]) grouped[planId] = []
        grouped[planId].push({
          timeId: r.plan_time_id,
          minutes: parseIsoToMinutes(r.actual_time)
        })
      }
      allTodayCheckins.value = grouped
    }
  } catch (e) {
    // 数据库连接异常时不阻塞界面，按钮保持默认状态
    console.warn('加载打卡记录失败', e)
  }
}

// 刷新打卡状态：重新加载所有打卡记录并按新规则重排 activePlans，每次刷新替换用户选择
// 用于每1分钟定时刷新：到达提醒时间且未打卡的任务优先展示到主要卡片，替换掉用户1分钟前的选择
async function refreshCheckinStatus() {
  if (!isLoggedIn.value || !hasActivePlans.value) return
  await loadAllTodayCheckins()
  const now = new Date()
  const nowMinutes = now.getHours() * 60 + now.getMinutes()
  activePlans.value = sortPlansByCheckinStatus(activePlans.value, nowMinutes, allTodayCheckins.value)
  // 每次刷新都按新规则重新选择主要/次要卡片（排序后第一项为主要，第二项为次要）
  primaryPlanId.value = activePlans.value.length > 0 ? activePlans.value[0].id : null
  secondaryPlanId.value = null
  forceActive.value = false
}

// 启动/重置1分钟刷新计时器（用户主动选择任务时调用以重置，保证用户选择至少保留1分钟）
function startRefreshTimer() {
  if (refreshTimer) clearInterval(refreshTimer)
  refreshTimer = setInterval(() => {
    refreshCheckinStatus()
  }, 60000) // 1分钟
}

// ===== 任务切换 =====

// 切换任务列表弹层显示
function toggleTaskList() {
  showTaskList.value = !showTaskList.value
}

// 点击次要卡片：次要卡片与主要卡片内容互换
function handleSecondaryClick() {
  if (secondaryPlan.value && primaryPlan.value) {
    // 互换主要和次要卡片的计划ID（todayCheckinMinutes 为 computed，会自动跟随 primaryPlan 更新）
    const oldPrimaryId = primaryPlan.value.id
    primaryPlanId.value = secondaryPlan.value.id
    secondaryPlanId.value = oldPrimaryId
    showTaskList.value = false
    forceActive.value = false
    // 用户主动选择，重置1分钟刷新计时器（保证该选择至少保留1分钟）
    startRefreshTimer()
  }
}

// 从任务列表选择任务作为主要卡片
function handleSelectTask(plan) {
  // 如果选中的任务当前是次要卡片，则互换主要和次要
  if (secondaryPlanId.value === plan.id) {
    const oldPrimaryId = primaryPlanId.value
    primaryPlanId.value = plan.id
    secondaryPlanId.value = oldPrimaryId
  } else {
    // 选中的任务成为主要卡片，原主要卡片成为次要卡片
    const oldPrimaryId = primaryPlan.value?.id
    primaryPlanId.value = plan.id
    if (oldPrimaryId && oldPrimaryId !== plan.id) {
      secondaryPlanId.value = oldPrimaryId
    }
  }
  showTaskList.value = false
  forceActive.value = false
  // 用户主动选择，重置1分钟刷新计时器（保证该选择至少保留1分钟）
  startRefreshTimer()
}

// ===== 打卡功能 =====

// 立即打卡：生成当前主要卡片任务的打卡记录并写入数据库
// 打卡成功后立即将记录加入本地列表，触发 checkinState 重算为 done（绿色"已打卡"，不弹窗）
// 防抖：同一任务3秒内只允许点击一次
async function handleCheckin() {
  // 新手引导：最后一步在打卡按钮高亮范围内点击即完成引导，不触发正常打卡流程
  if (guideStore.isActive && guideStore.currentStepData?.target === 'checkin-button') {
    guideStore.completeGuide()
    return
  }
  // 仅 active 状态可点击打卡（done/waiting/disabled 均被拦截）
  if (checkinState.value.status !== 'active') return
  const timeId = checkinState.value.timeId
  if (!primaryPlan.value || !isLoggedIn.value || !timeId) return

  // 防抖：3秒内只允许一次打卡
  const nowMs = Date.now()
  if (nowMs - lastCheckinTime < 3000) return
  lastCheckinTime = nowMs

  try {
    // 构造本地时间字符串（无时区后缀），避免 toISOString() 转为 UTC 导致时区偏差
    const now = new Date()
    const pad = (n) => String(n).padStart(2, '0')
    const localTimeStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
    const res = await createCheckin({
      plan_id: primaryPlan.value.id,
      plan_time_id: timeId,
      actual_time: localTimeStr
    })
    if (res.code === 0) {
      // 立即把打卡记录加入 allTodayCheckins，触发 checkinState 重算为 done
      const nowMinutes = now.getHours() * 60 + now.getMinutes()
      const planId = primaryPlan.value.id
      if (!allTodayCheckins.value[planId]) {
        allTodayCheckins.value[planId] = []
      }
      allTodayCheckins.value[planId].push({ timeId, minutes: nowMinutes })
      // 打卡成功后重置长按标志
      forceActive.value = false
      // 触发后端自动标记已读并同步刷新 NoticeButton 图标状态
      userStore.loadUnreadCount(true)
      // 打卡成功后，若当前计划包含微信通知方式，则为微信订阅消息静默补充一次授权额度
      // 用户已勾选"保持选择"时不弹窗；失败静默忽略（如用户已取消授权），不影响打卡主流程
      if (hasWechatNotification.value) {
        await requestSubscribe({ silent: true })
      }
    }
  } catch (e) {
    uni.showToast({ title: e.message || '打卡失败', icon: 'none' })
  }
}

// 长按3秒重置开始：非 active 状态长按触发，显示 3-2-1 倒计时
function handleLongPress() {
  // 新手引导期间禁用长按重置，避免干扰引导流程
  if (guideStore.isActive && guideStore.currentStepData?.target === 'checkin-button') return
  // 仅在非 disabled 状态下生效（必须有计划且在日期范围内）
  if (!primaryPlan.value || !isWithinDateRange.value) return
  // active 状态无需重置
  if (checkinState.value.status === 'active') return
  // 清除上一次的计时器
  if (longPressTimer) clearTimeout(longPressTimer)
  if (longPressInterval) clearInterval(longPressInterval)
  // 启动 3 秒倒计时显示
  longPressCountdown.value = 3
  longPressInterval = setInterval(() => {
    longPressCountdown.value -= 1
    if (longPressCountdown.value <= 0) {
      clearInterval(longPressInterval)
      longPressInterval = null
    }
  }, 1000)
  // 3 秒后强制重置为立即打卡
  longPressTimer = setTimeout(() => {
    forceActive.value = true
    longPressCountdown.value = 0
    if (longPressInterval) {
      clearInterval(longPressInterval)
      longPressInterval = null
    }
    uni.showToast({ title: '已重置', icon: 'success' })
  }, 3000)
}

// 长按3秒重置结束：手指离开或触摸被取消时清除计时，未满足 3 秒则取消重置
function handleLongPressEnd() {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
  if (longPressInterval) {
    clearInterval(longPressInterval)
    longPressInterval = null
  }
  longPressCountdown.value = 0
}

// ===== 生命周期 =====

// 页面显示时加载数据（含从其他页面返回时刷新），并启动每1分钟刷新定时器
onShow(() => {
  // 新手引导：上报当前页面（引导激活时推进/回退步骤）
  guideStore.onPageEnter('home')
  // 未登录欢迎卡片：每次进入首页重新随机词云布局
  if (!userStore.userInfo) {
    randomizeCloud()
  }
  // loadActivePlans 内部已加载今日所有打卡记录并按新规则排序，无需再单独加载
  loadActivePlans()
  // 并行加载最近 7 天公告（不阻塞任务卡片）
  loadRecentAnnouncements()
  // 并行加载用户通知渠道，用于判断打卡后是否需要补授权微信订阅消息
  loadUserChannels()
  // 已登录情况下，首页加载完成后触发一次未读站内信刷新，基于打卡记录自动标记已读并同步通知图标
  if (userStore.userInfo) {
    userStore.loadUnreadCount(true)
  }
  // 每1分钟刷新打卡状态：重新加载所有打卡记录并按新规则重排，替换用户选择
  // 用户主动选择任务时会重置此计时器，保证选择至少保留1分钟
  startRefreshTimer()
})

// 页面隐藏时清除定时器（用户不在线时不进行检查）
onHide(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (longPressTimer) clearTimeout(longPressTimer)
  if (longPressInterval) clearInterval(longPressInterval)
})
</script>

<style lang="scss">
/* ==========================================================================
 * 响应式单位说明
 * --------------------------------------------------------------------------
 * 全局采用 rpx（uni-app 标准响应式像素，750rpx = 屏幕宽度），
 * 基于 375px 设计稿，1px = 2rpx，自动适配不同手机宽度。
 * 以下保留 px 的场景：
 *   - 1px 物理边框 / box-shadow 内描边（避免高分屏消失）
 *   - box-shadow 偏移与模糊半径（视觉特效，不应随屏缩放）
 *   - 9999px（胶囊圆角最大值）
 * 平板/折叠屏（≥768px）通过媒体查询用 px 锁定关键尺寸，防止 rpx 过度放大。
 * 参考：
 *   - uni-app rpx 单位 https://uniapp.dcloud.net.cn/tutorial/syntax-css.html#rpx
 *   - MDN 媒体查询 https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_media_queries
 * ========================================================================== */

.index-page {
  /* 至少撑满一屏；内容超出时允许整页纵向滚动（overflow-x:hidden 会令 overflow-y 计算为 auto）
     一屏可展示完时不会出现滚动条 */
  min-height: 100vh;
  overflow-x: hidden;
  background-color: var(--page-bg-color);
  display: flex;
  flex-direction: column;
}

.index-page__frame {
  position: relative;
  /* flex 1 撑满 index-page 高度；padding-top:0 去掉顶部留白，由 main-canvas padding-top 统一处理通知按钮避让 */
  flex: 1;
  padding-top: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.index-page__main-canvas {
  /* padding-top 210rpx：与记录页(.record-page__main)白色卡片距导航栏顶部距离保持一致 */
  /* gap 64rpx：hero 与打卡按钮之间的间隔，小屏断点(max-height:700px)会进一步压缩 */
  padding: 210rpx 48rpx 0;
  box-sizing: border-box;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 64rpx;
}

.index-page__main-canvas--empty {
  /* 已登录无计划中：使用百分比距离控制上下留白，确保卡片与打卡按钮在一屏内完整展示；
     padding-top 避开顶部通知按钮；padding-bottom 置 0，由打卡按钮外壳的 margin-bottom 控制与底部导航栏的距离。
     当卡片内容可在该区域内完整显示时不会出现滚动条，超出时才允许自然滚动。 */
  padding-top: 14vh;
  padding-bottom: 0;
  justify-content: center;
  gap: 0;
}

/* 已登录空状态：引导卡片与打卡按钮之间的百分比间距 */
.index-page__main-canvas--empty .index-page__guide-card {
  margin-bottom: 2vh;
}

/* 已登录空状态：打卡按钮使用百分比距离控制与底部导航栏的留白 */
.index-page__checkin-shell--empty {
  margin-top: auto;
  margin-bottom: 16vh;
}

/* 未登录：内容区底部预留与记录页(.record-page padding-bottom:240rpx)一致的距离，
   保证介绍卡片底部到导航栏顶部保持一定间距，不贴底 */
.index-page__main-canvas--guest {
  padding-bottom: 240rpx;
}

/* ===== 未登录欢迎卡片（首屏，点击词云区切换为介绍卡片） =====
   卡片通过 flex:1 撑满 main-canvas 剩余高度（视口 - 顶部留白210rpx - 底部与导航栏间隔240rpx），
   上方简介文案（slogan 突出展示），中下方词云区（logo 居中 + 随机关键词）填满剩余空间 */
.index-page__welcome-card {
  width: 684rpx;
  flex: 1;
  padding: 56rpx 40rpx 48rpx;
  box-sizing: border-box;
  border-radius: 64rpx;
  background: var(--color-card-bg);
  /* 1px 内描边保留避免高分屏消失 */
  box-shadow: inset 0 0 0 1px var(--color-border-card), 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.index-page__welcome-copy {
  display: flex;
  flex-direction: column;
}

/* 卡片主标题：与介绍卡片"按时吃药"标题保持一致的字号/行高/字重/颜色 */
.index-page__welcome-slogan {
  display: block;
  color: var(--color-text-primary);
  font-size: 56rpx;
  line-height: 80rpx;
  font-weight: 600;
  text-align: center;
  margin-bottom: 28rpx;
}

/* 词云区：flex:1 填满卡片剩余高度（logo 居中于该区域即位于卡片中下方），
   relative 容器供关键词绝对定位（位置由 JS 每次进入首页在整块区域随机生成），
   整区可点击翻转卡片 */
.index-page__welcome-cloud {
  position: relative;
  flex: 1;
  margin-top: 24rpx;
  min-height: 380rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* logo 始终位于最上层（z-index 高于关键词），词云文字从其下方穿过 */
.index-page__welcome-logo {
  position: relative;
  z-index: 2;
  width: 200rpx;
  height: 200rpx;
  border-radius: 9999px;
  display: block;
}

/* 关键词基础样式：位置/旋转由行内样式随机生成，字号 s1-s5 / 颜色 c1-c6 由变体类随机分配；
   z-index 低于 logo，opacity 降低为浅色系背景装饰，词之间允许部分重叠 */
.index-page__welcome-word {
  position: absolute;
  z-index: 1;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
  opacity: 0.38;
}

/* 字号档位（s1 最小 → s5 最大，档差 18rpx 依次叠加；数值须与 JS 的 CLOUD_SIZE_BASE/STEP 一致） */
.index-page__welcome-word--s1 { font-size: 74rpx; }
.index-page__welcome-word--s2 { font-size: 92rpx; }
.index-page__welcome-word--s3 { font-size: 110rpx; }
.index-page__welcome-word--s4 { font-size: 128rpx; }
.index-page__welcome-word--s5 { font-size: 146rpx; }

/* 颜色池（取自 global.scss 设计令牌）：品牌绿/品牌深绿/链接蓝/警告黄/成功绿/次要文本色，
   统一通过 opacity 淡化为浅色系 */
.index-page__welcome-word--c1 { color: var(--color-brand); }
.index-page__welcome-word--c2 { color: var(--color-brand-dark); }
.index-page__welcome-word--c3 { color: var(--color-link); }
.index-page__welcome-word--c4 { color: var(--color-warning); }
.index-page__welcome-word--c5 { color: var(--color-success); }
.index-page__welcome-word--c6 { color: var(--color-text-secondary); }

/* ===== 未登录介绍卡片 ===== */
.index-page__intro-card {
  width: 684rpx;
  /* 尺寸跟随内容：不再 flex 撑满整屏，仅包裹标题+正文+登录按钮，消除下方多余白底 */
  padding: 48rpx 32rpx 32rpx;
  box-sizing: border-box;
  border-radius: 64rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-card), 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.index-page__intro-title {
  color: var(--color-text-primary);
  font-size: 56rpx;
  line-height: 80rpx;
  font-weight: 600;
  text-align: center;
  flex-shrink: 0;
}

.index-page__intro-scroll {
  margin-top: 24rpx;
}

.index-page__intro-section {
  margin-bottom: 32rpx;
}

.index-page__intro-section:last-child {
  margin-bottom: 0;
}

.index-page__intro-section-title {
  display: block;
  color: var(--color-text-primary);
  font-size: 36rpx;
  line-height: 52rpx;
  font-weight: 600;
  margin-bottom: 12rpx;
}

.index-page__intro-p {
  display: block;
  color: var(--color-text-secondary);
  font-size: 30rpx;
  line-height: 48rpx;
  font-weight: 400;
  margin-bottom: 12rpx;
  /* 正文段落首行缩进两字符（欢迎卡片与介绍卡片共用） */
  text-indent: 2em;
}

.index-page__intro-p:last-child {
  margin-bottom: 0;
}

.index-page__intro-link {
  color: var(--color-brand);
  font-size: 30rpx;
  line-height: 48rpx;
  word-break: break-all;
}

/* ===== 介绍卡片重点强调样式 =====
   层级（由弱到强）：
   - em：行内强调（绿色加粗，呼应链接色，突出关键能力/操作）
   - strong：整句强调（深色加粗，用于必要前提与核心卖点）
   - warning：警示强调（红色加粗，用于风险提示）
   - label：段落子标题（加粗前缀，呼应 section-title 形成层级）
   - action：行动入口（绿色描边胶囊，引导用户点击） */

.index-page__intro-em {
  color: var(--color-brand);
  font-weight: 600;
}

.index-page__intro-strong {
  color: var(--color-text-primary);
  font-weight: 600;
}

.index-page__intro-warning {
  color: var(--color-danger);
  font-weight: 600;
}

.index-page__intro-label {
  color: var(--color-text-primary);
  font-weight: 600;
}

.index-page__intro-action {
  margin-top: 24rpx;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  background: var(--color-brand-bg);
  border-radius: 48rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.index-page__intro-action-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 已登录空状态：新手引导卡片（样式参考未登录介绍卡片） ===== */
.index-page__guide-card {
  width: 684rpx;
  padding: 48rpx 32rpx 32rpx;
  box-sizing: border-box;
  border-radius: 64rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-card), 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.index-page__guide-title {
  color: var(--color-text-primary);
  font-size: 56rpx;
  line-height: 80rpx;
  font-weight: 600;
  text-align: center;
  flex-shrink: 0;
}

.index-page__guide-content {
  margin-top: 24rpx;
  margin-bottom: 24rpx;
  display: flex;
  flex-direction: column;
}

.index-page__guide-section {
  margin-bottom: 32rpx;
}

.index-page__guide-section:last-child {
  margin-bottom: 0;
}

.index-page__guide-line {
  display: block;
  color: var(--color-text-secondary);
  font-size: 30rpx;
  line-height: 48rpx;
  font-weight: 400;
  margin-bottom: 12rpx;
}

.index-page__guide-line:last-child {
  margin-bottom: 0;
}

.index-page__guide-em {
  color: var(--color-brand);
  font-weight: 600;
}

.index-page__guide-arrow {
  color: var(--color-text-muted);
  font-weight: 400;
}

.index-page__guide-link {
  color: var(--color-brand);
  font-weight: 600;
}

.index-page__guide-action {
  margin-top: 24rpx;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  background: var(--color-brand-bg);
  border-radius: 48rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.index-page__guide-action-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
  text-align: center;
}

/* ===== 任务卡片区域 ===== */
.index-page__hero {
  width: 684rpx;
  padding-top: 32rpx;
  box-sizing: border-box;
}

.index-page__primary-card {
  position: relative;
  width: 684rpx;
  /* 移除固定高度，根据实际文字内容自适应高度，确保布局紧凑 */
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 64rpx;
  background: var(--color-card-bg);
  /* box-shadow 偏移/模糊保留 px（视觉特效不随屏缩放），1px 内描边保留 */
  box-shadow: inset 0 0 0 1px var(--color-border-card), 0 1px 2px rgba(0, 0, 0, 0.05);
}

.index-page__primary-copy {
  display: flex;
  flex-direction: column;
  /* min-width:0 允许 flex 子项收缩，使文本截断生效 */
  min-width: 0;
}

.index-page__primary-title {
  color: var(--color-text-primary);
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 600;
  /* 动态截断：占满可用宽度后省略号截断，padding-right 为右上角"进行中"徽章预留空间 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 160rpx;
  box-sizing: border-box;
}

.index-page__primary-desc {
  margin-top: 8rpx;
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  /* 最多3行，超出省略号截断。
     word-break:break-all 允许字母+数字组合在任意位置断行——无空格的长字符串（如 abc123def）
     默认视为不可分割单词不会换行，会导致仅显示1行；break-all 强制按字符断行确保满3行。
     同时定义标准 line-clamp 与 -webkit-line-clamp，前者为 CSS 标准属性（兼容性前向），
     后者为当前浏览器/微信小程序实际生效版本 */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  overflow: hidden;
  word-break: break-all;
}

.index-page__status-badge {
  position: absolute;
  top: 34rpx;
  right: 34rpx;
  height: 56rpx;
  padding: 8rpx 16rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  background: var(--color-brand-bg);
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
}

.index-page__status-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 9999px;
  background: var(--color-success);
}

.index-page__status-text {
  color: var(--color-brand-dark);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 500;
}

.index-page__secondary-card {
  margin-top: -64rpx;
  width: 684rpx;
  height: 170rpx;
  padding: 64rpx 32rpx 24rpx;
  box-sizing: border-box;
  border-radius: 0 0 64rpx 64rpx;
  background: var(--color-separator);
  /* 1px 内描边保留，避免高分屏消失 */
  box-shadow: inset 0 0 0 1px var(--color-border-card);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.index-page__secondary-copy {
  display: flex;
  flex-direction: column;
  /* flex:1 占满次要卡片左侧可用空间，min-width:0 允许文本截断 */
  flex: 1;
  min-width: 0;
}

.index-page__secondary-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
  /* 单行截断：占满可用宽度后省略号截断，使用 line-clamp 方案兼容备注含换行符的场景 */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  overflow: hidden;
  word-break: break-all;
}

.index-page__secondary-desc {
  color: var(--color-text-secondary);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
  /* 单行截断：占满可用宽度后省略号截断，使用 line-clamp 方案兼容备注含换行符的场景 */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  overflow: hidden;
  word-break: break-all;
}

/* 3+任务时的"..."按钮 */
.index-page__secondary-more {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.index-page__secondary-more-text {
  color: var(--color-text-secondary);
  font-size: 40rpx;
  line-height: 48rpx;
  font-weight: 600;
  letter-spacing: 4rpx;
}

/* ===== 任务列表弹层 ===== */
.index-page__task-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.index-page__task-list {
  width: 600rpx;
  max-height: 800rpx;
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 32rpx;
  background: var(--color-card-bg);
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.index-page__task-list-title {
  color: var(--color-text-primary);
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
  /* 1px 物理边框保留 */
  border-bottom: 1px solid var(--color-border);
}

.index-page__task-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  box-sizing: border-box;
  border-radius: 16rpx;
  background: var(--color-card-bg-alt);
}

.index-page__task-item--active {
  background: var(--color-brand-bg-light);
}

.index-page__task-item-name {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  /* 动态截断：占满可用宽度后省略号截断 */
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.index-page__task-item-check {
  color: var(--color-brand);
  font-size: 32rpx;
  font-weight: 600;
}

/* ===== 立即打卡按钮 ===== */
.index-page__checkin-shell {
  width: 684rpx;
  padding: 32rpx 150rpx 0;
  box-sizing: border-box;
  /* margin-top:auto 将打卡按钮推至 main-canvas 底部；
     margin-bottom 340rpx = 导航栏高172rpx + 底部偏移30rpx + 按钮距导航栏顶部138rpx，
     使按钮位于整体中下部；小屏断点(max-height:700px)进一步压缩至 280rpx */
  margin-top: auto;
  margin-bottom: 340rpx;
}

.index-page__checkin-button {
  width: 384rpx;
  height: 384rpx;
  border-radius: 9999px;
  background: var(--color-danger);
  /* box-shadow 偏移/模糊保留 px */
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}

/* 禁用态（未登录/无任务/不在计划日期范围）：灰色背景，不显示图标，文字垂直居中 */
.index-page__checkin-button--disabled {
  background: var(--color-btn-disabled-bg);
  box-shadow: none;
}

/* 已完成态（当前匹配区间内已打卡）：绿色背景 */
.index-page__checkin-button--done {
  background: var(--color-success);
}

/* 未到打卡时间态（未到第一个提醒时间的开始打卡时间，即提醒前2小时）：橙色背景 */
.index-page__checkin-button--waiting {
  background: var(--color-warning);
}

.index-page__checkin-icon {
  width: 64rpx;
  height: 72rpx;
  margin-top: 100rpx;
  display: block;
}

.index-page__checkin-text {
  margin-top: 64rpx;
  color: var(--color-text-inverse);
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* 长按重置倒计时数字，占满按钮并垂直居中 */
.index-page__checkin-countdown {
  color: var(--color-text-inverse);
  font-size: 144rpx;
  line-height: 384rpx;
  font-weight: 600;
}

/* 无图标态文字垂直居中（disabled/waiting 无图标时 margin-top 调整为 (384-48)/2 = 168rpx） */
.index-page__checkin-button--disabled .index-page__checkin-text,
.index-page__checkin-button--waiting .index-page__checkin-text {
  margin-top: 168rpx;
}

/* ==========================================================================
 * 小屏机型适配（max-height: 700px）
 * --------------------------------------------------------------------------
 * iPhone SE(667px) 等小屏机型视口高度有限，进一步压缩 padding/gap/margin，
 * 保持打卡按钮(384rpx)与图标尺寸不变，仅减少留白区域，确保不出现滚动条。
 * 各区域间仍保留合理间隔（gap 32rpx、padding 24rpx、margin 280rpx）。
 * 参考：
 *   - MDN 媒体查询 height 特性 https://developer.mozilla.org/zh-CN/docs/Web/CSS/@media/height
 * ========================================================================== */
@media screen and (max-height: 700px) {
  .index-page__main-canvas {
    /* padding-top 210rpx：与记录页一致，不再为小屏单独压缩顶部留白 */
    padding-top: 210rpx;
    /* gap 32rpx：hero 与打卡按钮之间的最小间隔，保证视觉分隔 */
    gap: 32rpx;
  }
  .index-page__main-canvas--empty {
    /* 小屏进一步压缩百分比留白，确保卡片与打卡按钮一屏完整显示 */
    padding-top: 11vh;
    padding-bottom: 0;
    gap: 0;
  }
  .index-page__main-canvas--empty .index-page__guide-card {
    margin-bottom: 1vh;
  }
  .index-page__checkin-shell {
    /* padding-top 24rpx + margin-bottom 280rpx：压缩打卡按钮上下留白 */
    /* margin-bottom 280rpx = 导航栏高172rpx + 底部偏移30rpx + 按钮距导航栏顶部78rpx */
    padding: 24rpx 150rpx 0;
    margin-bottom: 280rpx;
  }
  .index-page__checkin-shell--empty {
    margin-top: auto;
    margin-bottom: 14vh;
  }
  .index-page__hero {
    padding-top: 16rpx;
  }
}

/* ==========================================================================
 * 平板/折叠屏适配（≥768px）
 * --------------------------------------------------------------------------
 * rpx 在宽屏设备会过度放大（768px 屏 1rpx≈1.02px，元素放大2倍），
 * 以下用 px 锁定关键尺寸（卡片宽度、打卡大圆环、字号、间距），内容居中显示，
 * 确保平板/折叠屏布局合理，不因等比放大而失真。
 * 断点参考 MDN 媒体查询标准：
 *   - 768px：平板竖屏 / 折叠屏内屏
 *   - 1024px：平板横屏 / 折叠屏展开
 * ========================================================================== */
@media screen and (min-width: 768px) {
  /* 内容容器固定 342px 居中，避免宽屏拉伸 */
  .index-page__guide-card,
  .index-page__hero,
  .index-page__primary-card,
  .index-page__secondary-card,
  .index-page__checkin-shell {
    width: 342px;
  }

  /* 主画布 padding/gap 锁定为 px，避免 rpx 在平板上过度放大导致溢出 */
  .index-page__main-canvas {
    /* padding-top 105px：与记录页平板 210rpx(=105px)保持一致 */
    padding-top: 105px;
    gap: 24px;
  }
  /* 未登录：底部间距与记录页平板 240rpx(=120px)保持一致 */
  .index-page__main-canvas--guest {
    padding-bottom: 120px;
  }

  /* 已登录空状态：继续使用百分比距离控制上下留白，打卡按钮底部间距同步百分比 */
  .index-page__main-canvas--empty {
    padding-top: 14vh;
    padding-bottom: 0;
    justify-content: center;
    gap: 0;
  }
  .index-page__main-canvas--empty .index-page__guide-card {
    margin-bottom: 2vh;
  }
  .index-page__checkin-shell--empty {
    margin-top: auto;
    margin-bottom: 16vh;
  }

  /* 已登录空状态：新手引导卡片 */
  .index-page__guide-card {
    width: 342px;
    padding: 24px 16px 16px;
    border-radius: 32px;
  }
  .index-page__guide-title {
    font-size: 28px;
    line-height: 40px;
  }
  .index-page__guide-content {
    margin-top: 12px;
    margin-bottom: 12px;
  }
  .index-page__guide-section {
    margin-bottom: 16px;
  }
  .index-page__guide-line {
    font-size: 15px;
    line-height: 24px;
    margin-bottom: 6px;
  }
  .index-page__guide-action {
    margin-top: 12px;
    height: 48px;
    padding: 12px 0;
    border-radius: 24px;
  }
  .index-page__guide-action-text {
    font-size: 16px;
    line-height: 24px;
  }

  /* 未登录欢迎卡片：rpx→px 锁定，避免宽屏过度放大（词云位置为百分比，随容器自动缩放） */
  .index-page__welcome-card {
    width: 342px;
    padding: 28px 20px 24px;
    border-radius: 32px;
  }
  .index-page__welcome-slogan {
    font-size: 28px;
    line-height: 40px;
    margin-bottom: 14px;
  }
  .index-page__welcome-cloud {
    margin-top: 12px;
    min-height: 190px;
  }
  .index-page__welcome-logo {
    width: 100px;
    height: 100px;
  }
  .index-page__welcome-word--s1 { font-size: 37px; }
  .index-page__welcome-word--s2 { font-size: 46px; }
  .index-page__welcome-word--s3 { font-size: 55px; }
  .index-page__welcome-word--s4 { font-size: 64px; }
  .index-page__welcome-word--s5 { font-size: 73px; }

  /* 未登录介绍卡片 */
  .index-page__intro-card {
    width: 342px;
    padding: 24px 16px 16px;
    border-radius: 32px;
  }
  .index-page__intro-title {
    font-size: 28px;
    line-height: 40px;
  }
  .index-page__intro-scroll {
    margin-top: 12px;
  }
  .index-page__intro-section {
    margin-bottom: 16px;
  }
  .index-page__intro-section-title {
    font-size: 18px;
    line-height: 26px;
    margin-bottom: 6px;
  }
  .index-page__intro-p,
  .index-page__intro-link {
    font-size: 15px;
    line-height: 24px;
  }
  .index-page__intro-p {
    margin-bottom: 6px;
  }
  .index-page__intro-action {
    margin-top: 12px;
    height: 48px;
    padding: 12px 0;
    border-radius: 24px;
  }
  .index-page__intro-action-text {
    font-size: 16px;
    line-height: 24px;
  }

  /* 任务卡片 */
  .index-page__hero {
    padding-top: 16px;
  }
  .index-page__primary-card {
    padding: 16px;
    border-radius: 32px;
  }
  .index-page__primary-title {
    font-size: 24px;
    line-height: 32px;
    padding-right: 80px;
  }
  .index-page__primary-desc {
    margin-top: 4px;
    font-size: 16px;
    line-height: 24px;
  }
  .index-page__status-badge {
    top: 17px;
    right: 17px;
    height: 28px;
    padding: 4px 8px;
    gap: 4px;
  }
  .index-page__status-dot {
    width: 8px;
    height: 8px;
  }
  .index-page__status-text {
    font-size: 14px;
    line-height: 20px;
  }
  .index-page__secondary-card {
    margin-top: -32px;
    height: 85px;
    padding: 32px 16px 12px;
    border-radius: 0 0 32px 32px;
  }
  .index-page__secondary-title {
    font-size: 16px;
    line-height: 24px;
  }
  .index-page__secondary-desc {
    font-size: 12px;
    line-height: 16px;
  }
  .index-page__secondary-more {
    width: 32px;
    height: 32px;
  }
  .index-page__secondary-more-text {
    font-size: 20px;
    line-height: 24px;
    letter-spacing: 2px;
  }

  /* 任务列表弹层 */
  .index-page__task-list {
    width: 300px;
    max-height: 400px;
    padding: 16px;
    border-radius: 16px;
    gap: 8px;
  }
  .index-page__task-list-title {
    font-size: 18px;
    line-height: 24px;
    padding-bottom: 8px;
  }
  .index-page__task-item {
    padding: 12px;
    border-radius: 8px;
  }
  .index-page__task-item-name {
    font-size: 16px;
    line-height: 24px;
  }
  .index-page__task-item-check {
    font-size: 16px;
  }

  /* 打卡按钮区域：固定尺寸，居中显示 */
  .index-page__checkin-shell {
    padding: 24px 75px 0;
    /* margin-bottom 201px = 导航栏高86px + 底部偏移15px + 按钮距导航栏顶部100px */
    margin-bottom: 201px;
  }
  .index-page__checkin-button {
    width: 192px;
    height: 192px;
  }
  .index-page__checkin-icon {
    width: 32px;
    height: 36px;
    margin-top: 50px;
  }
  .index-page__checkin-text {
    margin-top: 32px;
    font-size: 18px;
    line-height: 24px;
  }
  .index-page__checkin-button--disabled .index-page__checkin-text,
  .index-page__checkin-button--waiting .index-page__checkin-text {
    margin-top: 84px;
  }
}

@media screen and (min-width: 1024px) {
  /* 折叠屏展开/平板横屏：进一步限制内容最大宽度，居中显示避免过度留白拉伸 */
  .index-page__main-canvas {
    padding-left: 0;
    padding-right: 0;
  }
}
</style>
