<template>
  <view :data-theme="themeKey" class="plan-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="plan-page__main">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 notification/profile 等页面保持一致） -->
      <PageHeader :title="$t('plan.title')" :desc="$t('plan.desc')" />

      <!-- 新建计划入口卡（点击后切换为"新建计划"表单卡，隐藏所有已有计划） -->
      <view class="plan-page__new-entry guide-target-new-plan" v-if="!showForm && !editingPlanId" @click="handleNewEntry">
        <image class="plan-page__new-entry-icon" :src="jiaJihua" mode="aspectFit" />
        <text class="plan-page__new-entry-text">{{ $t('plan.newEntry') }}</text>
      </view>

      <!-- 新建计划表单卡（默认隐藏，点击"新建计划"后显示，已有计划全部隐藏；表单字段由 PlanForm 组件承载） -->
      <view class="plan-page__form-wrap" v-if="showForm">
        <view class="plan-page__form plan-page__form--fade-in">
          <PlanForm
            key="create"
            :plan="null"
            :available-channels="availableChannels"
            show-heading
            @submit="handleCreateSubmit"
          />
        </view>
      </view>

      <!-- 已有计划列表（从数据库动态加载，点击卡片就地展开编辑表单） -->
      <view class="plan-page__list" v-if="!showForm && plans.length > 0">
        <view
          v-for="plan in plans"
          :key="plan.id"
          class="plan-page__card-wrapper"
        >
          <!-- 计划卡片（点击展开/收起编辑表单） -->
          <view
            class="plan-page__card"
            :class="{
              'plan-page__card--active': planDisplayStatus[plan.id] === 1,
              'plan-page__card--editing': editingPlanId === plan.id
            }"
            @click="toggleEditPlan(plan)"
          >
            <view
              class="plan-page__card-stripe"
              :class="{
                'plan-page__card-stripe--active': planDisplayStatus[plan.id] === 1,
                'plan-page__card-stripe--paused': planDisplayStatus[plan.id] === 2
              }"
            ></view>
            <view class="plan-page__card-body">
              <view class="plan-page__card-head">
                <view class="plan-page__card-title-group">
                  <text class="plan-page__card-title">{{ plan.name }}</text>
                  <text class="plan-page__card-subtitle">{{ plan.remark || $t('plan.noRemark') }}</text>
                </view>
                <view class="plan-page__card-delete" @click.stop="handleDeletePlan(plan.id)">
                  <image class="plan-page__card-delete-icon" :src="shanchuIcon" mode="aspectFit" />
                </view>
              </view>
              <view
                class="plan-page__card-pills"
                v-if="(plan.notification_times && plan.notification_times.length > 0) || (planExtraPills[plan.id] && planExtraPills[plan.id].length > 0)"
              >
                <view
                  v-for="t in plan.notification_times"
                  :key="t.id"
                  class="plan-page__pill"
                >
                  {{ t.notification_time }}
                </view>
                <view
                  v-for="(p, i) in planExtraPills[plan.id] || []"
                  :key="'x' + i"
                  class="plan-page__pill"
                >
                  {{ p }}
                </view>
              </view>
            </view>
          </view>

          <!-- 编辑表单（就地展开，无标题，从卡片延伸出来的视觉效果；字段由 PlanForm 组件承载） -->
          <view v-if="editingPlanId === plan.id" class="plan-page__card-edit plan-page__form--fade-in">
            <PlanForm
              :key="plan.id"
              :plan="plan"
              :available-channels="availableChannels"
              @submit="payload => handleUpdateSubmit(plan.id, payload)"
              @status-change="editingStatus = $event"
            />
          </view>
        </view>
      </view>
    </view>

    <!-- 新手引导遮罩（仅在引导激活时渲染） -->
    <BeginnerGuide />
  </view>
</template>

<script setup>
/**
 * 制定计划页（plan.vue）
 * --------------------------------------------------------------------------
 * 功能：用药 / 健康提醒计划的制定与管理
 *  - 已有计划列表：从数据库动态加载，按状态（进行中>暂停>已结束）+ 优先级（数字越小越靠前）+ 创建时间（新在前）排序
 *  - 就地展开编辑：点击已有计划卡片在卡片下方展开编辑表单（无标题，从卡片延伸），再次点击收缩
 *  - 新建计划：点击"新建计划"入口卡后隐藏所有已有计划，显示"新建计划"表单卡
 *  - 表单字段（新建/编辑共用 PlanForm 组件）：计划名称、备注、结束方式、起始日期（90/365天快捷）、
 *    重复星期（预设+多选）、提醒时间（每时间点独立的提醒次数 1/2/3 与等间隔 5-60 分钟）、
 *    优先级（0-3单选框）、通知方式、任务状态
 *  - 通知方式：从 notification_channels 表查询当前用户已配置的通知渠道（站内信默认勾选逻辑在 PlanForm 内）
 *  - 保存计划：调用后端 API 写入 checkin_plans + plan_notification_times + plan_notification_channels
 *  - 卡片标签联动：提醒时间 pills + 重复规则/结束方式标签（非默认配置时显示）
 */
import { ref, onMounted, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import BeginnerGuide from '../../components/BeginnerGuide.vue'
import PlanForm from '../../components/PlanForm.vue'
import { useGuideTarget } from '../../composables/useGuideTarget'
import { useGuideStore } from '../../store/modules/guide'
import { useUserStore } from '../../store/modules/user'
import { useLanguageStore } from '../../store/modules/language'
import { listNotificationChannels } from '../../api/modules/notification'
import { listPlans, createPlan, updatePlan, deletePlan } from '../../api/modules/plan'
import jiaJihuaIcon from '../../assets/images/jia_jihua.png'
import shanchuIcon from '../../assets/images/shanchu.png'
import { useThemeIcon } from '../../composables/useThemeIcon'
import { useShare } from '../../composables/useShare'
import { t } from '../../locale'

// 图标按当前主题换色（green 用原图，其余主题用 static/theme-icons 产物）
// shanchu（删除红）不参与换色，保持原引用
const jiaJihua = useThemeIcon('jia_jihua.png', jiaJihuaIcon)

useShare({ title: t('share.plan') })

const userStore = useUserStore()
const guideStore = useGuideStore()
const languageStore = useLanguageStore()

// 新手引导：上报「新建计划」入口位置
useGuideTarget('new-plan', '.guide-target-new-plan')

// 新手引导：页面显示时上报当前页面（引导激活时推进/回退步骤）
onShow(() => {
  guideStore.onPageEnter('plan')
  // 每次进入页面刷新通知渠道列表：覆盖从通知方式页添加/修改渠道后返回的场景
  // （App 端页面常驻栈内、onMounted 仅首次触发，不刷新会导致新渠道不出现在选项中）
  loadChannels()
})

// 已有计划列表（从数据库加载，后端已按 status>priority>created_at 排序）
const plans = ref([])
// 用户已配置的通知渠道列表（从数据库加载，传给 PlanForm 供"通知方式"选项）
const availableChannels = ref([])

// 卡片切换：默认显示"新建计划"入口卡，点击后切换为"新建计划"表单卡
const showForm = ref(false)
// 当前展开编辑的计划ID（null 表示无展开；非 null 表示对应计划卡片下方展开编辑表单）
const editingPlanId = ref(null)
// 编辑中计划的任务状态（PlanForm status-change 事件同步，卡片色条实时跟随表单单选）
const editingStatus = ref(null)

// 表单提交中标志位（防止保存按钮频繁点击导致重复提交）
const isSubmitting = ref(false)

// 每个计划当前显示的状态映射（编辑中时使用 editingStatus 实时反映单选框选择，否则使用 plan.status）
// 使用 computed 显式建立对 editingStatus / editingPlanId / plans 的响应式依赖，
// 避免普通函数在 v-for 中调用时 reactive 属性变化不触发正在编辑卡片的重渲染
const planDisplayStatus = computed(() => {
  const map = {}
  for (const plan of plans.value) {
    map[plan.id] = editingPlanId.value === plan.id
      ? (editingStatus.value != null ? editingStatus.value : plan.status)
      : plan.status
  }
  return map
})

// 计划卡片的附加标签（重复规则/结束方式联动展示；默认配置不显示，避免视觉噪音）
const planExtraPills = computed(() => {
  void languageStore.current // 建立语言依赖，切换语言时即时更新
  const map = {}
  for (const plan of plans.value) {
    const pills = []
    const weekdays = plan.repeat_weekdays ?? 127
    if (weekdays === 31) {
      pills.push(t('plan.pillWeekday'))
    } else if (weekdays === 96) {
      pills.push(t('plan.pillWeekend'))
    } else if (weekdays !== 127) {
      pills.push(t('plan.pillCustomRepeat'))
    }
    const endMode = plan.end_mode ?? 0
    if (endMode === 2) {
      pills.push(t('plan.pillLongTerm'))
    } else if (endMode === 1 && plan.total_target_count) {
      pills.push(t('plan.pillCountEnd', { n: plan.total_target_count }))
    }
    map[plan.id] = pills
  }
  return map
})

// 加载用户已有计划
async function loadPlans() {
  if (!userStore.userInfo) return
  try {
    const res = await listPlans()
    if (res.code === 0 && res.data) {
      plans.value = res.data
    }
  } catch (e) {
    console.warn('加载计划列表失败', e)
  }
}

// 加载用户已配置的通知渠道（仅显示可用状态，站内信默认勾选逻辑在 PlanForm 组件内处理）
async function loadChannels() {
  if (!userStore.userInfo) return
  try {
    const res = await listNotificationChannels()
    if (res.code === 0 && res.data) {
      // 仅显示状态为可用的通知方式
      availableChannels.value = res.data.filter(ch => ch.enabled)
    }
  } catch (e) {
    console.warn('加载通知渠道失败', e)
  }
}

onMounted(() => {
  // 仅加载计划列表；通知渠道由 onShow 统一刷新（覆盖首次进入与从通知方式页返回场景），
  // 此处不再重复调用 loadChannels，避免首次进入页面时发出两次相同请求
  loadPlans()
})

// 删除计划（点击 shanchu 图标后二次确认）
function handleDeletePlan(planId) {
  if (!userStore.userInfo) return
  uni.showModal({
    title: t('common.tip'),
    content: t('plan.deleteConfirm'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    success: async (res) => {
      if (!res.confirm) return
      try {
        const r = await deletePlan(planId)
        if (r.code === 0) {
          uni.showToast({ title: t('plan.deleted'), icon: 'success' })
          // 如果正在编辑被删除的计划，收起编辑表单
          if (editingPlanId.value === planId) {
            editingPlanId.value = null
            editingStatus.value = null
          }
          await loadPlans()
        }
      } catch (e) {
        uni.showToast({ title: e.message || t('plan.deleteFailed'), icon: 'none' })
      }
    }
  })
}

// 点击已有计划卡片：就地展开/收起编辑表单
async function toggleEditPlan(plan) {
  if (editingPlanId.value === plan.id) {
    // 再次点击同一卡片：收起编辑表单
    editingPlanId.value = null
    editingStatus.value = null
    return
  }
  // 展开前先刷新通知渠道列表，确保用户在通知方式页新添加的渠道（如 App推送）
  // 能立即出现在编辑表单的可选项中（App 端页面常驻栈内、onMounted 不重跑，不刷新会看不到）
  await loadChannels()
  // 展开新卡片：表单数据填充由 PlanForm 组件按 plan prop 完成（:key=plan.id 重建实例）
  editingPlanId.value = plan.id
  editingStatus.value = plan.status != null ? plan.status : 1
  showForm.value = false  // 隐藏新建表单
}

// 新建计划入口：点击"新建计划"入口卡，隐藏所有已有计划，显示新建表单
async function handleNewEntry() {
  // 每次打开新建计划页面时重新从数据库加载通知方式（仅显示可用状态）
  await loadChannels()
  showForm.value = true
  editingPlanId.value = null
  editingStatus.value = null
  // 新手引导：当前步骤为「新建计划」时，点击后进入下一步（步骤 6：返回首页）
  if (guideStore.isActive && guideStore.currentStepData?.target === 'new-plan') {
    guideStore.nextStep()
  }
}

// 保存新建计划（表单校验与 payload 组装由 PlanForm 完成）
async function handleCreateSubmit(payload) {
  // 防重复提交：提交中直接返回
  if (isSubmitting.value) return
  if (!userStore.userInfo) {
    uni.showToast({ title: t('plan.needLogin'), icon: 'none' })
    return
  }
  isSubmitting.value = true
  try {
    const res = await createPlan(payload)
    if (res.code === 0) {
      uni.showToast({ title: t('plan.created'), icon: 'success' })
      showForm.value = false
      await loadPlans()
    }
  } catch (e) {
    uni.showToast({ title: e.message || t('plan.saveFailed'), icon: 'none' })
  } finally {
    isSubmitting.value = false
  }
}

// 保存编辑计划（更新；表单校验与 payload 组装由 PlanForm 完成）
async function handleUpdateSubmit(planId, payload) {
  // 防重复提交：提交中直接返回
  if (isSubmitting.value) return
  if (!userStore.userInfo) return
  isSubmitting.value = true
  try {
    const res = await updatePlan(planId, payload)
    if (res.code === 0) {
      uni.showToast({ title: t('plan.updated'), icon: 'success' })
      // 先刷新计划列表数据，再收起编辑表单。
      // 若先置 editingPlanId=null 再 loadPlans，色条 class 会经历 --active→无→--active 的往返，
      // 微信小程序 setData diff 机制可能将最终状态与编辑中状态对比认为相同而跳过更新，导致色条停留在中间灰色态。
      // 调换顺序后 planDisplayStatus[A.id] 始终为新 status 值，色条无中间态闪烁。
      await loadPlans()
      editingPlanId.value = null
      editingStatus.value = null
    }
  } catch (e) {
    uni.showToast({ title: e.message || t('plan.updateFailed'), icon: 'none' })
  } finally {
    isSubmitting.value = false
  }
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
 * 注：表单字段样式（输入框/选择器/单选框等）已随 PlanForm 组件迁移至 components/PlanForm.vue
 * ========================================================================== */
.plan-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.plan-page__main {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 210rpx 48rpx 64rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
}

/* ===== 新建计划入口卡 ===== */
.plan-page__new-entry {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 16rpx;
  height: 192rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-input);
}

.plan-page__new-entry-icon {
  width: 28rpx;
  height: 28rpx;
  display: block;
}

.plan-page__new-entry-text {
  color: var(--color-brand);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 新建计划表单（外壳卡片，字段内容由 PlanForm 组件渲染） ===== */
.plan-page__form-wrap {
  padding-top: 0;
}

.plan-page__form {
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border), var(--shadow-card);
}

/* 卡片切换淡入过渡 */
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

/* ===== 已有计划列表 ===== */
.plan-page__list {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.plan-page__card-wrapper {
  display: flex;
  flex-direction: column;
}

.plan-page__card {
  position: relative;
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* 编辑态卡片：底部圆角去除，与下方编辑表单衔接 */
.plan-page__card--editing {
  border-radius: 24rpx 24rpx 0 0;
}

.plan-page__card-stripe {
  position: absolute;
  left: 0;
  top: 0;
  width: 8rpx;
  height: 100%;
  background: var(--color-stripe-default);
  border-radius: 24rpx 0 0 24rpx;
}

.plan-page__card-stripe--active {
  background: var(--color-brand);
}

.plan-page__card-stripe--paused {
  background: var(--color-stripe-paused);
}

.plan-page__card-body {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
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
  gap: 8rpx;
  flex: 1;
  min-width: 0;
}

.plan-page__card-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-page__card-subtitle {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-page__card-delete {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.plan-page__card-delete-icon {
  width: 32rpx;
  height: 36rpx;
  display: block;
}

.plan-page__card-pills {
  display: flex;
  flex-direction: row;
  gap: 8rpx;
  padding-top: 16rpx;
  flex-wrap: wrap;
}

.plan-page__pill {
  padding: 8rpx 16rpx;
  border-radius: 9999px;
  background: var(--page-bg-color);
  color: var(--color-label);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

/* ===== 就地展开编辑表单（从卡片延伸，无标题；字段内容由 PlanForm 组件渲染） ===== */
.plan-page__card-edit {
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 0 0 24rpx 24rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border), var(--shadow-card);
  /* 顶部无 margin，与卡片底部紧密衔接，呈现从卡片延伸的视觉效果 */
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 * 规则：将本页面主要容器的宽度、卡片宽度、按钮尺寸锁定为设计稿原 px 值
 */
@media screen and (min-width: 768px) {
  /* 主容器内边距与间距 */
  .plan-page__main {
    padding: 105px 24px 32px;
    gap: 32px;
  }
  /* 新建计划入口卡 */
  .plan-page__new-entry {
    gap: 8px;
    height: 96px;
    border-radius: 12px;
  }
  .plan-page__new-entry-icon {
    width: 14px;
    height: 14px;
  }
  .plan-page__new-entry-text {
    font-size: 16px;
    line-height: 24px;
  }
  /* 新建计划表单卡 */
  .plan-page__form {
    padding: 16px;
    border-radius: 12px;
  }
  /* 已有计划列表 */
  .plan-page__list {
    gap: 16px;
  }
  .plan-page__card {
    padding: 16px;
    border-radius: 12px;
  }
  .plan-page__card--editing {
    border-radius: 12px 12px 0 0;
  }
  .plan-page__card-stripe {
    width: 4px;
    border-radius: 12px 0 0 12px;
  }
  .plan-page__card-body {
    gap: 8px;
  }
  .plan-page__card-title-group {
    gap: 4px;
  }
  .plan-page__card-title {
    font-size: 16px;
    line-height: 24px;
  }
  .plan-page__card-subtitle {
    font-size: 16px;
    line-height: 24px;
  }
  .plan-page__card-delete {
    width: 32px;
    height: 32px;
  }
  .plan-page__card-delete-icon {
    width: 16px;
    height: 18px;
  }
  .plan-page__card-pills {
    gap: 4px;
    padding-top: 8px;
  }
  .plan-page__pill {
    padding: 4px 8px;
    font-size: 12px;
    line-height: 16px;
  }
  /* 就地展开编辑表单 */
  .plan-page__card-edit {
    padding: 16px;
    border-radius: 0 0 12px 12px;
  }
}
</style>
