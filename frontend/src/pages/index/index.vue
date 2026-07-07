<template>
  <view class="index-page">
    <view class="index-page__frame">
      <NoticeButton :has-notification="hasNotification" />

      <view class="index-page__main-canvas">
        <!-- 空状态提示（未登录或已登录无进行中计划时，隐藏任务卡片） -->
        <view v-if="!hasActivePlans" class="index-page__empty">
          <text class="index-page__empty-text">{{ emptyText }}</text>
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

        <!-- 立即打卡按钮（状态：灰色无任务 / 红色立即打卡 / 已完成 / 未到打卡时间） -->
        <view class="index-page__checkin-shell">
          <view
            class="index-page__checkin-button"
            :class="{
              'index-page__checkin-button--disabled': isButtonDisabled,
              'index-page__checkin-button--done': isCheckinDone,
              'index-page__checkin-button--waiting': isWaiting
            }"
            @click="handleCheckin"
            @longpress="handleLongPress"
          >
            <image v-if="showCheckinIcon" class="index-page__checkin-icon" :src="checkinIcon" mode="aspectFit" />
            <text class="index-page__checkin-text">{{ checkinText }}</text>
          </view>
        </view>
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
    </view>
  </view>
</template>

<script setup>
/**
 * 首页（index.vue）
 * --------------------------------------------------------------------------
 * 功能：应用主入口，展示用户当日打卡任务与打卡按钮
 *  - 顶部通知按钮（NoticeButton）
 *  - 任务卡片：从 checkin_plans 表获取当前用户进行中计划，按 priority 升序排序
 *    - 主要卡片：展示当前选中任务，不设置点击事件，显示计划名称、备注
 *    - 次要卡片：展示第二个任务，点击后与主要卡片内容互换；3+任务时右侧显示"..."按钮
 *    - "..."按钮：3+任务时显示，点击展开任务列表，可选择任务替换到主要卡片
 *  - 空状态：未登录显示欢迎语，已登录无计划显示创建提示
 *  - 立即打卡按钮（多状态）：
 *    - 灰色"无打卡任务"：未登录/无任务/不在计划日期范围内/无提醒时间
 *    - 橙色"未到打卡时间"：未到任何提醒时间的"开始打卡时间"（提醒时间前1小时），不显示图标
 *    - 红色"立即打卡"：已到开始打卡时间且当前提醒未打卡（从提醒前1小时持续到打卡为止）
 *    - 绿色"已打卡"：当前提醒已匹配到打卡记录，持续到下一次提醒开始打卡时间或当日24:00
 *    - 长按3秒：waiting/done 状态可长按3秒重置为"立即打卡"
 *    - 打卡成功后不弹窗，按钮直接转为绿色"已打卡"状态
 *    - 打卡记录匹配：单条提醒看全天任意记录；多条提醒看提醒时间前后各1小时区间记录
 */
import { ref, computed, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import NoticeButton from '../../components/NoticeButton.vue'
import BottomNav from '../../components/BottomNav.vue'
import { useUserStore } from '../../store/modules/user'
import { listPlans } from '../../api/modules/plan'
import { createCheckin, listTodayCheckinsByPlan } from '../../api/modules/checkin'
import checkinInactiveIcon from '../../assets/images/daka_0.png'
import checkinDoneIcon from '../../assets/images/daka_1.png'
import { useShare } from '../../composables/useShare'

useShare({ title: '首页' })

const userStore = useUserStore()
// 通知按钮红点（暂固定为 true，后续可对接通知状态）
const hasNotification = true

// 进行中的计划列表（从数据库加载，按 priority 升序排序）
const activePlans = ref([])
// 当前主要卡片计划ID（null 表示使用列表第一项）
const primaryPlanId = ref(null)
// 当前次要卡片计划ID（null 表示使用列表第二项，点击次要卡片时与主要卡片互换）
const secondaryPlanId = ref(null)
// 是否显示任务列表弹层
const showTaskList = ref(false)
// 今日打卡记录列表（含打卡时间分钟数，用于"匹配打卡记录"判定 done/active）
// 结构：[{ timeId, minutes }]，minutes = 实际打卡时间的小时*60+分钟
const todayCheckinMinutes = ref([])
// 状态刷新定时器（每分钟检查打卡时段变化）
let refreshTimer = null
// 长按3秒重置标志：true 时强制按钮为"立即打卡"可点击状态
const forceActive = ref(false)
// 长按计时器
let longPressTimer = null

// ===== 计算属性 =====

const isLoggedIn = computed(() => !!userStore.userInfo)
const hasActivePlans = computed(() => activePlans.value.length > 0)

// 空状态提示文本
const emptyText = computed(() => {
  if (!isLoggedIn.value) return '欢迎使用无足鸟按时吃药打卡！'
  return '请先到设置界面创建您的打卡计划，常见问题可参考同界面里的帮助中心。'
})

// 主要卡片计划
const primaryPlan = computed(() => {
  if (!activePlans.value.length) return null
  if (primaryPlanId.value !== null) {
    return activePlans.value.find(p => p.id === primaryPlanId.value) || activePlans.value[0]
  }
  return activePlans.value[0]
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

// 判定某提醒时间 t 是否已打卡（基于今日打卡记录的"匹配打卡记录"规则）
// - 单条提醒时间：全天有任意一条打卡记录即视为已打卡
// - 多条提醒时间：在 t 的前后各1小时 [t-60, t+60] 内存在打卡记录即视为已打卡
function isTimeChecked(t, allTimes) {
  if (todayCheckinMinutes.value.length === 0) return false
  if (allTimes.length === 1) {
    return true
  }
  const lo = t.minutes - 60
  const hi = t.minutes + 60
  return todayCheckinMinutes.value.some(r => r.minutes >= lo && r.minutes <= hi)
}

// 找当前时间应针对的提醒时间索引（从后往前找第一个 nowMinutes >= t-60 的）
// 小间隔（gap≤120）前半段归属前一个提醒
function findCurrentTargetIndex(times, nowMinutes) {
  for (let i = times.length - 1; i >= 0; i--) {
    if (nowMinutes >= times[i].minutes - 60) {
      // 小间隔前半段归属前一个提醒
      if (i > 0) {
        const prev = times[i - 1]
        const gap = times[i].minutes - prev.minutes
        if (gap <= 120) {
          const midpoint = (prev.minutes + times[i].minutes) / 2
          if (nowMinutes < midpoint) {
            return i - 1
          }
        }
      }
      return i
    }
  }
  return -1
}

// 打卡状态计算：'disabled' | 'waiting' | 'active' | 'done'
// - disabled: 未登录/无任务/不在日期范围/无提醒时间
// - waiting: 未到任何提醒时间的"开始打卡时间"（t-60）
// - active: 已到开始打卡时间且当前提醒未匹配到打卡记录（从 t-60 持续到用户打卡为止，
//           超过提醒时间 t 仍未打卡仍为 active，直到下一个提醒开始打卡时间或当日24:00）
// - done: 当前提醒已匹配到打卡记录，持续到下一次提醒开始打卡时间或当日24:00后重置为 waiting
const checkinState = computed(() => {
  if (!isLoggedIn.value || !hasActivePlans.value) return { status: 'disabled' }
  if (!primaryPlan.value) return { status: 'disabled' }
  if (!isWithinDateRange.value) return { status: 'disabled' }
  const times = sortedTimes.value
  if (times.length === 0) return { status: 'disabled' }

  const now = new Date()
  const nowMinutes = now.getHours() * 60 + now.getMinutes()

  const idx = findCurrentTargetIndex(times, nowMinutes)
  // 未到任何提醒的开始打卡时间 → waiting
  if (idx === -1) {
    // 长按重置：强制为 active，针对第一个未来提醒
    if (forceActive.value) {
      let target = times[0]
      for (let i = 0; i < times.length; i++) {
        if (times[i].minutes >= nowMinutes) {
          target = times[i]
          break
        }
      }
      return { status: 'active', timeId: target.id }
    }
    return { status: 'waiting' }
  }

  const target = times[idx]

  // 长按重置：强制为 active（允许已打卡后重新打卡）
  if (forceActive.value) {
    return { status: 'active', timeId: target.id }
  }

  // 判定当前提醒是否已匹配打卡记录
  if (isTimeChecked(target, times)) {
    return { status: 'done', timeId: target.id }
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

// ===== 数据加载 =====

// 加载进行中的计划（仅 status=1，按 priority 升序）
async function loadActivePlans() {
  if (!isLoggedIn.value) {
    activePlans.value = []
    return
  }
  try {
    const res = await listPlans(userStore.userInfo.id)
    if (res.code === 0 && res.data) {
      // 仅保留进行中的计划，按 priority 升序排序
      activePlans.value = res.data
        .filter(p => p.status === 1)
        .sort((a, b) => (a.priority ?? 3) - (b.priority ?? 3))
    }
  } catch (e) {
    console.warn('加载计划失败', e)
  }
}

// 加载今日打卡记录（针对主要卡片计划）
// 异步查询数据库，存储打卡记录的分钟数列表，用于"匹配打卡记录"判定 done/active
async function loadTodayCheckins() {
  if (!primaryPlan.value || !isLoggedIn.value) {
    todayCheckinMinutes.value = []
    return
  }
  try {
    const res = await listTodayCheckinsByPlan(userStore.userInfo.id, primaryPlan.value.id)
    if (res.code === 0 && res.data) {
      const records = res.data.records || []
      todayCheckinMinutes.value = records
        .filter(r => r.actual_time)
        .map(r => ({ timeId: r.plan_time_id, minutes: parseIsoToMinutes(r.actual_time) }))
    }
  } catch (e) {
    // 数据库连接异常时不阻塞界面，按钮保持默认状态
    console.warn('加载打卡记录失败', e)
  }
}

// ===== 任务切换 =====

// 切换任务列表弹层显示
function toggleTaskList() {
  showTaskList.value = !showTaskList.value
}

// 点击次要卡片：次要卡片与主要卡片内容互换
function handleSecondaryClick() {
  if (secondaryPlan.value && primaryPlan.value) {
    // 互换主要和次要卡片的计划ID
    const oldPrimaryId = primaryPlan.value.id
    primaryPlanId.value = secondaryPlan.value.id
    secondaryPlanId.value = oldPrimaryId
    showTaskList.value = false
    forceActive.value = false
    loadTodayCheckins()
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
  loadTodayCheckins()
}

// ===== 打卡功能 =====

// 立即打卡：生成当前主要卡片任务的打卡记录并写入数据库
// 打卡成功后立即将记录加入本地列表，触发 checkinState 重算为 done（绿色"已打卡"，不弹窗）
async function handleCheckin() {
  // 仅 active 状态可点击打卡（done/waiting/disabled 均被拦截）
  if (checkinState.value.status !== 'active') return
  const timeId = checkinState.value.timeId
  if (!primaryPlan.value || !isLoggedIn.value || !timeId) return

  try {
    // 构造本地时间字符串（无时区后缀），避免 toISOString() 转为 UTC 导致时区偏差
    const now = new Date()
    const pad = (n) => String(n).padStart(2, '0')
    const localTimeStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
    const res = await createCheckin({
      user_id: userStore.userInfo.id,
      plan_id: primaryPlan.value.id,
      plan_time_id: timeId,
      actual_time: localTimeStr
    })
    if (res.code === 0) {
      // 立即把打卡记录加入本地列表，触发 checkinState 重算为 done
      const nowMinutes = now.getHours() * 60 + now.getMinutes()
      todayCheckinMinutes.value.push({ timeId, minutes: nowMinutes })
      // 打卡成功后重置长按标志
      forceActive.value = false
    }
  } catch (e) {
    uni.showToast({ title: e.message || '打卡失败', icon: 'none' })
  }
}

// 长按3秒重置：任何非"立即打卡"状态长按3秒后重置为"立即打卡"
function handleLongPress() {
  // 仅在非 disabled 状态下生效（必须有计划且在日期范围内）
  if (!primaryPlan.value || !isWithinDateRange.value) return
  // active 状态无需重置
  if (checkinState.value.status === 'active') return
  // 启动3秒计时器
  if (longPressTimer) clearTimeout(longPressTimer)
  uni.showLoading({ title: '请长按3秒...', mask: true })
  longPressTimer = setTimeout(() => {
    forceActive.value = true
    uni.hideLoading()
    uni.showToast({ title: '已重置为立即打卡', icon: 'success' })
  }, 3000)
}

// ===== 生命周期 =====

// 页面显示时加载数据（含从其他页面返回时刷新）
onShow(() => {
  loadActivePlans().then(() => {
    if (primaryPlan.value) {
      loadTodayCheckins()
    }
  })
  // 每分钟刷新打卡时段状态（检测打卡窗口是否打开）
  if (!refreshTimer) {
    refreshTimer = setInterval(() => {
      if (primaryPlan.value) {
        loadTodayCheckins()
      }
    }, 60000)
  }
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (longPressTimer) clearTimeout(longPressTimer)
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
  /* height 100vh + overflow hidden 严格锁定视口高度，禁止出现上下滚动条 */
  height: 100vh;
  overflow: hidden;
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
  /* padding-top 200rpx：通知按钮 top约100rpx + 高80rpx = 底部约180rpx，留 20rpx 间隙避免与内容重叠 */
  /* gap 64rpx：hero 与打卡按钮之间的间隔，小屏断点(max-height:700px)会进一步压缩 */
  padding: 200rpx 48rpx 0;
  box-sizing: border-box;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 64rpx;
}

/* ===== 空状态提示 ===== */
.index-page__empty {
  width: 684rpx;
  padding: 96rpx 32rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-page__empty-text {
  color: #454745;
  font-size: 40rpx;
  line-height: 60rpx;
  font-weight: 400;
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
  background: #ffffff;
  /* box-shadow 偏移/模糊保留 px（视觉特效不随屏缩放），1px 内描边保留 */
  box-shadow: inset 0 0 0 1px #e2e2e2, 0 1px 2px rgba(0, 0, 0, 0.05);
}

.index-page__primary-copy {
  display: flex;
  flex-direction: column;
  /* min-width:0 允许 flex 子项收缩，使文本截断生效 */
  min-width: 0;
}

.index-page__primary-title {
  color: #0e0f0c;
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
  color: #454745;
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
  background: #9fe870;
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
}

.index-page__status-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 9999px;
  background: #2ead4b;
}

.index-page__status-text {
  color: #2e6900;
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
  background: #f3f3f4;
  /* 1px 内描边保留，避免高分屏消失 */
  box-shadow: inset 0 0 0 1px #e2e2e2;
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
  color: #0e0f0c;
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
  color: #454745;
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
  color: #454745;
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
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.index-page__task-list-title {
  color: #0e0f0c;
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
  /* 1px 物理边框保留 */
  border-bottom: 1px solid #e8ebe6;
}

.index-page__task-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  box-sizing: border-box;
  border-radius: 16rpx;
  background: #f9f9f9;
}

.index-page__task-item--active {
  background: #e8f5e0;
}

.index-page__task-item-name {
  color: #0e0f0c;
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
  color: #2f6c00;
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
  background: #d03238;
  /* box-shadow 偏移/模糊保留 px */
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}

/* 禁用态（未登录/无任务/不在计划日期范围）：灰色背景，不显示图标，文字垂直居中 */
.index-page__checkin-button--disabled {
  background: #8a8a8a;
  box-shadow: none;
}

/* 已完成态（多提醒时间间隔≤2小时，处于两次提醒间隔的前半部分）：绿色背景 */
.index-page__checkin-button--done {
  background: #2ead4b;
}

/* 未到打卡时间态（在日期范围内但未到任何提醒时间的提前一小时窗口）：橙色背景 */
.index-page__checkin-button--waiting {
  background: #d97706;
}

.index-page__checkin-icon {
  width: 64rpx;
  height: 72rpx;
  margin-top: 100rpx;
  display: block;
}

.index-page__checkin-text {
  margin-top: 64rpx;
  color: #ffffff;
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 500;
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
    /* padding-top 170rpx：通知按钮 100rpx + 高 80rpx = 180rpx，留 10rpx 减少顶部留白 */
    padding-top: 170rpx;
    /* gap 32rpx：hero 与打卡按钮之间的最小间隔，保证视觉分隔 */
    gap: 32rpx;
  }
  .index-page__hero {
    padding-top: 16rpx;
  }
  .index-page__checkin-shell {
    /* padding-top 24rpx + margin-bottom 280rpx：压缩打卡按钮上下留白 */
    /* margin-bottom 280rpx = 导航栏高172rpx + 底部偏移30rpx + 按钮距导航栏顶部78rpx */
    padding: 24rpx 150rpx 0;
    margin-bottom: 280rpx;
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
  .index-page__empty,
  .index-page__hero,
  .index-page__primary-card,
  .index-page__secondary-card,
  .index-page__checkin-shell {
    width: 342px;
  }

  /* 主画布 padding/gap 锁定为 px，避免 rpx 在平板上过度放大导致溢出 */
  .index-page__main-canvas {
    padding-top: 80px;
    gap: 24px;
  }

  /* 空状态 */
  .index-page__empty {
    padding: 48px 16px;
  }
  .index-page__empty-text {
    font-size: 20px;
    line-height: 30px;
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
