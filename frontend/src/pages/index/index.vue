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
.index-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
}

.index-page__frame {
  position: relative;
  /* min-height 100vh + box-sizing border-box：含 padding-top 17px 不超出视口，消除底部空白滚动 */
  min-height: 100vh;
  padding-top: 17px;
  box-sizing: border-box;
}

.index-page__main-canvas {
  /* padding-top 105px：通知按钮 top约50px + 高40px = 底部约90px，留 15px 间隙避免与内容重叠 */
  /* min-height calc(100vh - 17px)：填满 frame 内容区（frame padding-top 17px），使打卡按钮可通过 margin-top:auto 定位至底部 */
  padding: 105px 24px 0;
  box-sizing: border-box;
  min-height: calc(100vh - 17px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 66px;
}

/* ===== 空状态提示 ===== */
.index-page__empty {
  width: 342px;
  padding: 48px 16px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-page__empty-text {
  color: #454745;
  font-size: 20px;
  line-height: 30px;
  font-weight: 400;
  text-align: center;
}

/* ===== 任务卡片区域 ===== */
.index-page__hero {
  width: 342px;
  padding-top: 32px;
  box-sizing: border-box;
}

.index-page__primary-card {
  position: relative;
  width: 342px;
  height: 148px;
  padding: 16px;
  box-sizing: border-box;
  border-radius: 32px;
  background: #ffffff;
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
  font-size: 24px;
  line-height: 32px;
  font-weight: 600;
  /* 动态截断：占满可用宽度后省略号截断，padding-right 为右上角"进行中"徽章预留空间 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 80px;
  box-sizing: border-box;
}

.index-page__primary-desc {
  margin-top: 4px;
  color: #454745;
  font-size: 16px;
  line-height: 24px;
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
  top: 17px;
  right: 17px;
  height: 28px;
  padding: 4px 8px;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #9fe870;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.index-page__status-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #2ead4b;
}

.index-page__status-text {
  color: #2e6900;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
}

.index-page__secondary-card {
  margin-top: -32px;
  width: 342px;
  height: 85px;
  padding: 32px 16px 12px;
  box-sizing: border-box;
  border-radius: 0 0 32px 32px;
  background: #f3f3f4;
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
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.index-page__secondary-desc {
  color: #454745;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 3+任务时的"..."按钮 */
.index-page__secondary-more {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.index-page__secondary-more-text {
  color: #454745;
  font-size: 20px;
  line-height: 24px;
  font-weight: 600;
  letter-spacing: 2px;
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
  width: 300px;
  max-height: 400px;
  padding: 16px;
  box-sizing: border-box;
  border-radius: 16px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.index-page__task-list-title {
  color: #0e0f0c;
  font-size: 18px;
  line-height: 24px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8ebe6;
}

.index-page__task-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  box-sizing: border-box;
  border-radius: 8px;
  background: #f9f9f9;
}

.index-page__task-item--active {
  background: #e8f5e0;
}

.index-page__task-item-name {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
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
  font-size: 16px;
  font-weight: 600;
}

/* ===== 立即打卡按钮 ===== */
.index-page__checkin-shell {
  width: 342px;
  padding: 32px 75px 0;
  box-sizing: border-box;
  /* margin-top:auto 将打卡按钮推至 main-canvas 底部；margin-bottom calc(20vh + 101px) 使按钮底部距底部导航栏顶部 20% 页面高度（101px = 导航栏高 86px + 底部偏移 15px） */
  margin-top: auto;
  margin-bottom: calc(20vh + 101px);
}

.index-page__checkin-button {
  width: 192px;
  height: 192px;
  border-radius: 9999px;
  background: #d03238;
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
  width: 32px;
  height: 36px;
  margin-top: 50px;
  display: block;
}

.index-page__checkin-text {
  margin-top: 32px;
  color: #ffffff;
  font-size: 18px;
  line-height: 24px;
  font-weight: 500;
}

/* 无图标态文字垂直居中（disabled/waiting 无图标时 margin-top 调整为 (192-24)/2 = 84px） */
.index-page__checkin-button--disabled .index-page__checkin-text,
.index-page__checkin-button--waiting .index-page__checkin-text {
  margin-top: 84px;
}
</style>
