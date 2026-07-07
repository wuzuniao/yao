<template>
  <view class="plan-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="plan-page__main">
      <!-- 页面标题区 -->
      <view class="plan-page__header">
        <text class="plan-page__title">制定计划</text>
        <text class="plan-page__desc">合理规划您的用药与健康提醒，助您养成良好的生活习惯。</text>
      </view>

      <!-- 新建计划入口卡（点击后切换为"新建计划详情"表单卡，隐藏所有已有计划） -->
      <view class="plan-page__new-entry" v-if="!showForm && !editingPlanId" @click="handleNewEntry">
        <image class="plan-page__new-entry-icon" :src="jiaJihuaIcon" mode="aspectFit" />
        <text class="plan-page__new-entry-text">新建计划</text>
      </view>

      <!-- 新建计划详情表单卡（默认隐藏，点击"新建计划"后显示，已有计划全部隐藏） -->
      <view class="plan-page__form-wrap" v-if="showForm">
        <view class="plan-page__form plan-page__form--fade-in">
          <text class="plan-page__form-heading">新建计划详情</text>

          <!-- 计划名称 -->
          <view class="plan-page__field">
            <text class="plan-page__label">计划名称</text>
            <input
              class="plan-page__input"
              v-model="form.name"
              placeholder="例如：按时吃药"
              placeholder-class="plan-page__placeholder"
              :placeholder-style="phStyle('name')"
              :maxlength="nameLimit.max"
              @input="e => form.name = nameLimit.handleInput(e)"
              @focus="onFocus('name')"
              @blur="onBlur"
            />
            <text v-if="nameLimit.limitReached" class="plan-page__limit-text">{{ nameLimit.limitHint }}</text>
          </view>

          <!-- 备注说明 -->
          <view class="plan-page__field">
            <text class="plan-page__label">备注说明</text>
            <textarea
              class="plan-page__textarea"
              v-model="form.remark"
              placeholder="例如：饭后半小时服用"
              placeholder-class="plan-page__placeholder"
              :placeholder-style="phStyle('remark')"
              :maxlength="remarkLimit.max"
              @input="e => form.remark = remarkLimit.handleInput(e)"
              @focus="onFocus('remark')"
              @blur="onBlur"
            />
            <text v-if="remarkLimit.limitReached" class="plan-page__limit-text">{{ remarkLimit.limitHint }}</text>
          </view>

          <!-- 计划持续起始日期（起止日期双控件，禁止手动输入） -->
          <view class="plan-page__field">
            <text class="plan-page__label">计划持续起始日期</text>
            <view class="plan-page__date-range">
              <picker mode="date" :value="form.startDate" @change="handleStartDateChange" class="plan-page__date-picker">
                <view class="plan-page__picker-display">
                  <text
                    class="plan-page__picker-text"
                    :class="{ 'plan-page__picker-text--placeholder': !form.startDate }"
                  >{{ form.startDate || '开始日期' }}</text>
                </view>
              </picker>
              <text class="plan-page__date-separator">至</text>
              <picker mode="date" :value="form.endDate" @change="handleEndDateChange" class="plan-page__date-picker">
                <view class="plan-page__picker-display">
                  <text
                    class="plan-page__picker-text"
                    :class="{ 'plan-page__picker-text--placeholder': !form.endDate }"
                  >{{ form.endDate || '结束日期' }}</text>
                </view>
              </picker>
            </view>
          </view>

          <!-- 提醒时间（多个单个时间控件，可动态添加/删除） -->
          <view class="plan-page__field">
            <view class="plan-page__time-label-row">
              <text class="plan-page__label">提醒时间</text>
              <view class="plan-page__add-time" @click="handleAddTime">
                <image class="plan-page__add-time-icon" :src="jiaShijianIcon" mode="aspectFit" />
                <text class="plan-page__add-time-text">添加时间</text>
              </view>
            </view>
            <view
              v-for="(t, idx) in form.times"
              :key="idx"
              class="plan-page__time-row"
            >
              <picker mode="time" :value="t" @change="handleTimeChange($event, idx)" class="plan-page__time-picker">
                <view class="plan-page__time-picker-display">
                  <text
                    class="plan-page__time-picker-text"
                    :class="{ 'plan-page__time-picker-text--placeholder': !t }"
                  >{{ t || '选择时间' }}</text>
                </view>
              </picker>
              <view class="plan-page__time-delete" @click="handleDeleteTime(idx)">
                <image class="plan-page__time-delete-icon" :src="shanchuIcon" mode="aspectFit" />
              </view>
            </view>
          </view>

          <!-- 优先级单选框（0-7，数字越小优先级越高，默认3） -->
          <view class="plan-page__field">
            <text class="plan-page__label">优先级（数字越小越优先）</text>
            <view class="plan-page__priority-row">
              <view
                v-for="n in 8"
                :key="n - 1"
                class="plan-page__priority-item"
                @click="form.priority = n - 1"
              >
                <view class="plan-page__radio" :class="{ 'plan-page__radio--checked': form.priority === n - 1 }">
                  <view v-if="form.priority === n - 1" class="plan-page__radio-dot"></view>
                </view>
                <text class="plan-page__priority-text">{{ n - 1 }}</text>
              </view>
            </view>
          </view>

          <!-- 通知方式（从数据库动态加载） -->
          <view class="plan-page__field">
            <text class="plan-page__label">通知方式</text>
            <view class="plan-page__notify-row" v-if="availableChannels.length > 0">
              <view
                v-for="ch in availableChannels"
                :key="ch.id"
                class="plan-page__notify-item"
                @click="toggleChannel(ch.id)"
              >
                <view class="plan-page__checkbox" :class="{ 'plan-page__checkbox--checked': selectedChannelIds.includes(ch.id) }">
                  <view v-if="selectedChannelIds.includes(ch.id)" class="plan-page__checkmark"></view>
                </view>
                <text class="plan-page__notify-text">{{ ch.channel_type }}</text>
              </view>
            </view>
            <view v-else class="plan-page__notify-empty">
              <text class="plan-page__notify-empty-text">暂无通知方式，请先到"通知方式"页配置</text>
            </view>
          </view>

          <!-- 任务状态（单选框：进行中/暂停/已结束，对应 1/2/0） -->
          <view class="plan-page__field">
            <text class="plan-page__label">任务状态</text>
            <view class="plan-page__status-row">
              <view class="plan-page__status-item" @click="form.status = 1">
                <view class="plan-page__radio" :class="{ 'plan-page__radio--checked': form.status === 1 }">
                  <view v-if="form.status === 1" class="plan-page__radio-dot"></view>
                </view>
                <text class="plan-page__status-text">进行中</text>
              </view>
              <view class="plan-page__status-item" @click="form.status = 2">
                <view class="plan-page__radio" :class="{ 'plan-page__radio--checked': form.status === 2 }">
                  <view v-if="form.status === 2" class="plan-page__radio-dot"></view>
                </view>
                <text class="plan-page__status-text">暂停</text>
              </view>
              <view class="plan-page__status-item" @click="form.status = 0">
                <view class="plan-page__radio" :class="{ 'plan-page__radio--checked': form.status === 0 }">
                  <view v-if="form.status === 0" class="plan-page__radio-dot"></view>
                </view>
                <text class="plan-page__status-text">已结束</text>
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
                  <text class="plan-page__card-subtitle">{{ plan.remark || '无备注' }}</text>
                </view>
                <view class="plan-page__card-delete" @click.stop="handleDeletePlan(plan.id)">
                  <image class="plan-page__card-delete-icon" :src="shanchuIcon" mode="aspectFit" />
                </view>
              </view>
              <view class="plan-page__card-pills" v-if="plan.notification_times && plan.notification_times.length > 0">
                <view
                  v-for="t in plan.notification_times"
                  :key="t.id"
                  class="plan-page__pill"
                >
                  {{ t.notification_time }}
                </view>
              </view>
            </view>
          </view>

          <!-- 编辑表单（就地展开，无标题，从卡片延伸出来的视觉效果） -->
          <view v-if="editingPlanId === plan.id" class="plan-page__card-edit plan-page__form--fade-in">
            <!-- 计划名称 -->
            <view class="plan-page__field">
              <text class="plan-page__label">计划名称</text>
              <input
                class="plan-page__input"
                v-model="editingForm.name"
                placeholder="例如：按时吃药"
                placeholder-class="plan-page__placeholder"
                :maxlength="editNameLimit.max"
                @input="e => editingForm.name = editNameLimit.handleInput(e)"
              />
              <text v-if="editNameLimit.limitReached" class="plan-page__limit-text">{{ editNameLimit.limitHint }}</text>
            </view>

            <!-- 备注说明 -->
            <view class="plan-page__field">
              <text class="plan-page__label">备注说明</text>
              <textarea
                class="plan-page__textarea"
                v-model="editingForm.remark"
                placeholder="例如：饭后半小时服用"
                placeholder-class="plan-page__placeholder"
                :maxlength="editRemarkLimit.max"
                @input="e => editingForm.remark = editRemarkLimit.handleInput(e)"
              />
              <text v-if="editRemarkLimit.limitReached" class="plan-page__limit-text">{{ editRemarkLimit.limitHint }}</text>
            </view>

            <!-- 计划持续起始日期 -->
            <view class="plan-page__field">
              <text class="plan-page__label">计划持续起始日期</text>
              <view class="plan-page__date-range">
                <picker mode="date" :value="editingForm.startDate" @change="handleEditStartDateChange" class="plan-page__date-picker">
                  <view class="plan-page__picker-display">
                    <text
                      class="plan-page__picker-text"
                      :class="{ 'plan-page__picker-text--placeholder': !editingForm.startDate }"
                    >{{ editingForm.startDate || '开始日期' }}</text>
                  </view>
                </picker>
                <text class="plan-page__date-separator">至</text>
                <picker mode="date" :value="editingForm.endDate" @change="handleEditEndDateChange" class="plan-page__date-picker">
                  <view class="plan-page__picker-display">
                    <text
                      class="plan-page__picker-text"
                      :class="{ 'plan-page__picker-text--placeholder': !editingForm.endDate }"
                    >{{ editingForm.endDate || '结束日期' }}</text>
                  </view>
                </picker>
              </view>
            </view>

            <!-- 提醒时间 -->
            <view class="plan-page__field">
              <view class="plan-page__time-label-row">
                <text class="plan-page__label">提醒时间</text>
                <view class="plan-page__add-time" @click="handleEditAddTime">
                  <image class="plan-page__add-time-icon" :src="jiaShijianIcon" mode="aspectFit" />
                  <text class="plan-page__add-time-text">添加时间</text>
                </view>
              </view>
              <view
                v-for="(t, idx) in editingForm.times"
                :key="idx"
                class="plan-page__time-row"
              >
                <picker mode="time" :value="t" @change="handleEditTimeChange($event, idx)" class="plan-page__time-picker">
                  <view class="plan-page__time-picker-display">
                    <text
                      class="plan-page__time-picker-text"
                      :class="{ 'plan-page__time-picker-text--placeholder': !t }"
                    >{{ t || '选择时间' }}</text>
                  </view>
                </picker>
                <view class="plan-page__time-delete" @click="handleEditDeleteTime(idx)">
                  <image class="plan-page__time-delete-icon" :src="shanchuIcon" mode="aspectFit" />
                </view>
              </view>
            </view>

            <!-- 优先级单选框 -->
            <view class="plan-page__field">
              <text class="plan-page__label">优先级（数字越小越优先）</text>
              <view class="plan-page__priority-row">
                <view
                  v-for="n in 8"
                  :key="n - 1"
                  class="plan-page__priority-item"
                  @click="editingForm.priority = n - 1"
                >
                  <view class="plan-page__radio" :class="{ 'plan-page__radio--checked': editingForm.priority === n - 1 }">
                    <view v-if="editingForm.priority === n - 1" class="plan-page__radio-dot"></view>
                  </view>
                  <text class="plan-page__priority-text">{{ n - 1 }}</text>
                </view>
              </view>
            </view>

            <!-- 通知方式 -->
            <view class="plan-page__field">
              <text class="plan-page__label">通知方式</text>
              <view class="plan-page__notify-row" v-if="availableChannels.length > 0">
                <view
                  v-for="ch in availableChannels"
                  :key="ch.id"
                  class="plan-page__notify-item"
                  @click="toggleEditChannel(ch.id)"
                >
                  <view class="plan-page__checkbox" :class="{ 'plan-page__checkbox--checked': editingSelectedChannelIds.includes(ch.id) }">
                    <view v-if="editingSelectedChannelIds.includes(ch.id)" class="plan-page__checkmark"></view>
                  </view>
                  <text class="plan-page__notify-text">{{ ch.channel_type }}</text>
                </view>
              </view>
              <view v-else class="plan-page__notify-empty">
                <text class="plan-page__notify-empty-text">暂无通知方式，请先到"通知方式"页配置</text>
              </view>
            </view>

            <!-- 任务状态 -->
            <view class="plan-page__field">
              <text class="plan-page__label">任务状态</text>
              <view class="plan-page__status-row">
                <view class="plan-page__status-item" @click="editingForm.status = 1">
                  <view class="plan-page__radio" :class="{ 'plan-page__radio--checked': editingForm.status === 1 }">
                    <view v-if="editingForm.status === 1" class="plan-page__radio-dot"></view>
                  </view>
                  <text class="plan-page__status-text">进行中</text>
                </view>
                <view class="plan-page__status-item" @click="editingForm.status = 2">
                  <view class="plan-page__radio" :class="{ 'plan-page__radio--checked': editingForm.status === 2 }">
                    <view v-if="editingForm.status === 2" class="plan-page__radio-dot"></view>
                  </view>
                  <text class="plan-page__status-text">暂停</text>
                </view>
                <view class="plan-page__status-item" @click="editingForm.status = 0">
                  <view class="plan-page__radio" :class="{ 'plan-page__radio--checked': editingForm.status === 0 }">
                    <view v-if="editingForm.status === 0" class="plan-page__radio-dot"></view>
                  </view>
                  <text class="plan-page__status-text">已结束</text>
                </view>
              </view>
            </view>

            <!-- 更新按钮 -->
            <view class="plan-page__save" @click="handleSaveEdit(plan.id)">
              <image class="plan-page__save-icon" :src="baocunJihuaIcon" mode="aspectFit" />
              <text class="plan-page__save-text">更新计划</text>
            </view>
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
 *  - 已有计划列表：从数据库动态加载，按状态（进行中>暂停>已结束）+ 优先级（数字越小越靠前）+ 创建时间（新在前）排序
 *  - 就地展开编辑：点击已有计划卡片在卡片下方展开编辑表单（无标题，从卡片延伸），再次点击收缩
 *  - 新建计划：点击"新建计划"入口卡后隐藏所有已有计划，显示"新建计划详情"表单卡
 *  - 表单字段：计划名称、备注、起止日期、提醒时间（多时间控件，宽度50%）、优先级（0-7单选框）、通知方式、任务状态
 *  - 通知方式：从 notification_channels 表查询当前用户已配置的通知渠道，站内信默认勾选
 *  - 保存计划：调用后端 API 写入 checkin_plans + plan_notification_times + plan_notification_channels
 * 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
 */
import { reactive, ref, onMounted, computed } from 'vue'
import BackButton from '../../components/BackButton.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { useInputLimit } from '../../composables/useInputLimit'
import { useUserStore } from '../../store/modules/user'
import { listNotificationChannels } from '../../api/modules/notification'
import { listPlans, createPlan, updatePlan, deletePlan } from '../../api/modules/plan'
import jiaJihuaIcon from '../../assets/images/jia_jihua.png'
import jiaShijianIcon from '../../assets/images/jia_shijian.png'
import shanchuIcon from '../../assets/images/shanchu.png'
import baocunJihuaIcon from '../../assets/images/baocun_jihua.png'
import { useShare } from '../../composables/useShare'

useShare({ title: '制定计划' })

const userStore = useUserStore()

// 已有计划列表（从数据库加载，后端已按 status>priority>created_at 排序）
const plans = ref([])
// 用户已配置的通知渠道列表（从数据库加载，用于"通知方式"选项）
const availableChannels = ref([])

// 卡片切换：默认显示"新建计划"入口卡，点击后切换为"新建计划详情"表单卡
const showForm = ref(false)
// 当前展开编辑的计划ID（null 表示无展开；非 null 表示对应计划卡片下方展开编辑表单）
const editingPlanId = ref(null)

// 新建计划表单
const form = reactive({
  name: '',
  remark: '',
  startDate: '',
  endDate: '',
  times: [''],
  priority: 3,  // 优先级：0-7，数字越小优先级越高，默认3
  status: 1  // 任务状态：1-进行中，2-暂停，0-已结束（默认进行中）
})
// 用户已选中的通知渠道ID列表（新建模式）
const selectedChannelIds = ref([])

// 编辑计划表单（点击已有计划卡片时填充）
const editingForm = reactive({
  name: '',
  remark: '',
  startDate: '',
  endDate: '',
  times: [''],
  priority: 3,
  status: 1
})
// 编辑模式下已选中的通知渠道ID列表
const editingSelectedChannelIds = ref([])

// 表单提交中标志位（防止保存按钮频繁点击导致重复提交）
const isSubmitting = ref(false)

// 获取当前系统时间（HH:MM 格式，用于时间控件默认值）
function getCurrentTime() {
  const now = new Date()
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

// 输入框 placeholder 聚焦交互：聚焦变浅灰 #c0c0c0，失焦恢复 placeholder-class 原始色
const { onFocus, onBlur, phStyle } = usePlaceholder()

// 输入框字符限制（与后端字段限制严格匹配：计划名称100字符，备注255字符）
const nameLimit = useInputLimit(100)
const remarkLimit = useInputLimit(255)
const editNameLimit = useInputLimit(100)
const editRemarkLimit = useInputLimit(255)

// 每个计划当前显示的状态映射（编辑中时使用 editingForm.status 实时反映单选框选择，否则使用 plan.status）
// 使用 computed 显式建立对 editingForm.status / editingPlanId / plans 的响应式依赖，
// 避免普通函数在 v-for 中调用时 reactive 属性变化不触发正在编辑卡片的重渲染
const planDisplayStatus = computed(() => {
  const map = {}
  for (const plan of plans.value) {
    map[plan.id] = editingPlanId.value === plan.id ? editingForm.status : plan.status
  }
  return map
})

// 加载用户已有计划
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

// 加载用户已配置的通知渠道（仅显示可用状态，加载后默认勾选站内信，供新建表单使用）
async function loadChannels() {
  if (!userStore.userInfo) return
  try {
    const res = await listNotificationChannels(userStore.userInfo.id)
    if (res.code === 0 && res.data) {
      // 仅显示状态为可用的通知方式
      availableChannels.value = res.data.filter(ch => ch.enabled)
      // 默认勾选站内信（供新建表单使用）
      const znxChannel = availableChannels.value.find(c => c.channel_type === '站内信')
      if (znxChannel && !selectedChannelIds.value.includes(znxChannel.id)) {
        selectedChannelIds.value.push(znxChannel.id)
      }
    }
  } catch (e) {
    console.warn('加载通知渠道失败', e)
  }
}

onMounted(() => {
  loadPlans()
  loadChannels()
})

// 删除计划（点击 shanchu 图标后二次确认）
function handleDeletePlan(planId) {
  if (!userStore.userInfo) return
  uni.showModal({
    title: '提示',
    content: '确定要删除该计划吗？',
    confirmText: '删除',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const r = await deletePlan(planId, userStore.userInfo.id)
        if (r.code === 0) {
          uni.showToast({ title: '删除成功', icon: 'success' })
          // 如果正在编辑被删除的计划，收起编辑表单
          if (editingPlanId.value === planId) {
            editingPlanId.value = null
          }
          await loadPlans()
        }
      } catch (e) {
        uni.showToast({ title: e.message || '删除失败', icon: 'none' })
      }
    }
  })
}

// 点击已有计划卡片：就地展开/收起编辑表单
function toggleEditPlan(plan) {
  if (editingPlanId.value === plan.id) {
    // 再次点击同一卡片：收起编辑表单
    editingPlanId.value = null
    return
  }
  // 展开新卡片：填充编辑表单数据
  editingPlanId.value = plan.id
  showForm.value = false  // 隐藏新建表单
  editingForm.name = plan.name || ''
  editingForm.remark = plan.remark || ''
  editingForm.startDate = plan.start_date || ''
  editingForm.endDate = plan.end_date || ''
  editingForm.times = (plan.notification_times && plan.notification_times.length > 0)
    ? plan.notification_times.map(t => t.notification_time)
    : [getCurrentTime()]
  editingForm.priority = plan.priority != null ? plan.priority : 3
  editingForm.status = plan.status != null ? plan.status : 1
  // 设置已选中的通知渠道
  editingSelectedChannelIds.value = plan.channel_ids ? [...plan.channel_ids] : []
  // 确保站内信默认勾选（如果存在且未包含）
  const znxChannel = availableChannels.value.find(c => c.channel_type === '站内信')
  if (znxChannel && !editingSelectedChannelIds.value.includes(znxChannel.id)) {
    editingSelectedChannelIds.value.push(znxChannel.id)
  }
}

// 新建计划入口：点击"新建计划"入口卡，隐藏所有已有计划，显示新建表单
async function handleNewEntry() {
  // 每次打开新建计划页面时重新从数据库加载通知方式（仅显示可用状态）
  // 先清空选中状态，loadChannels 会重新勾选站内信
  selectedChannelIds.value = []
  await loadChannels()
  showForm.value = true
  editingPlanId.value = null
  form.name = ''
  form.remark = ''
  form.startDate = ''
  form.endDate = ''
  form.times = [getCurrentTime()]
  form.priority = 3
  form.status = 1
}

// ===== 新建表单事件处理 =====
function handleStartDateChange(e) {
  form.startDate = e.detail.value
}
function handleEndDateChange(e) {
  form.endDate = e.detail.value
}
function handleTimeChange(e, idx) {
  form.times[idx] = e.detail.value
}
function handleAddTime() {
  form.times.push('')
}
function handleDeleteTime(idx) {
  if (form.times.length <= 1) {
    uni.showToast({ title: '至少保留一个提醒时间', icon: 'none' })
    return
  }
  form.times.splice(idx, 1)
}
function toggleChannel(channelId) {
  const i = selectedChannelIds.value.indexOf(channelId)
  if (i >= 0) {
    selectedChannelIds.value.splice(i, 1)
  } else {
    selectedChannelIds.value.push(channelId)
  }
}

// ===== 编辑表单事件处理 =====
function handleEditStartDateChange(e) {
  editingForm.startDate = e.detail.value
}
function handleEditEndDateChange(e) {
  editingForm.endDate = e.detail.value
}
function handleEditTimeChange(e, idx) {
  editingForm.times[idx] = e.detail.value
}
function handleEditAddTime() {
  editingForm.times.push('')
}
function handleEditDeleteTime(idx) {
  if (editingForm.times.length <= 1) {
    uni.showToast({ title: '至少保留一个提醒时间', icon: 'none' })
    return
  }
  editingForm.times.splice(idx, 1)
}
function toggleEditChannel(channelId) {
  const i = editingSelectedChannelIds.value.indexOf(channelId)
  if (i >= 0) {
    editingSelectedChannelIds.value.splice(i, 1)
  } else {
    editingSelectedChannelIds.value.push(channelId)
  }
}

// 保存新建计划
async function handleSave() {
  // 防重复提交：提交中直接返回
  if (isSubmitting.value) return
  if (!userStore.userInfo) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  if (!form.name.trim()) {
    uni.showToast({ title: '请输入计划名称', icon: 'none' })
    return
  }
  if (!form.startDate) {
    uni.showToast({ title: '请选择开始日期', icon: 'none' })
    return
  }
  if (!form.endDate) {
    uni.showToast({ title: '请选择结束日期', icon: 'none' })
    return
  }
  if (form.endDate < form.startDate) {
    uni.showToast({ title: '结束日期不能早于开始日期', icon: 'none' })
    return
  }
  const validTimes = form.times.filter(t => t)
  if (validTimes.length === 0) {
    uni.showToast({ title: '请至少设置一个提醒时间', icon: 'none' })
    return
  }
  if (selectedChannelIds.value.length === 0) {
    uni.showToast({ title: '请至少选择一个通知方式', icon: 'none' })
    return
  }

  isSubmitting.value = true
  try {
    const res = await createPlan({
      user_id: userStore.userInfo.id,
      name: form.name,
      remark: form.remark,
      start_date: form.startDate,
      end_date: form.endDate,
      notification_times: validTimes,
      channel_ids: selectedChannelIds.value,
      status: form.status,
      priority: form.priority
    })
    if (res.code === 0) {
      uni.showToast({ title: '计划创建成功', icon: 'success' })
      showForm.value = false
      await loadPlans()
    }
  } catch (e) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' })
  } finally {
    isSubmitting.value = false
  }
}

// 保存编辑计划（更新）
async function handleSaveEdit(planId) {
  // 防重复提交：提交中直接返回
  if (isSubmitting.value) return
  if (!userStore.userInfo) return
  if (!editingForm.name.trim()) {
    uni.showToast({ title: '请输入计划名称', icon: 'none' })
    return
  }
  if (!editingForm.startDate) {
    uni.showToast({ title: '请选择开始日期', icon: 'none' })
    return
  }
  if (!editingForm.endDate) {
    uni.showToast({ title: '请选择结束日期', icon: 'none' })
    return
  }
  if (editingForm.endDate < editingForm.startDate) {
    uni.showToast({ title: '结束日期不能早于开始日期', icon: 'none' })
    return
  }
  const validTimes = editingForm.times.filter(t => t)
  if (validTimes.length === 0) {
    uni.showToast({ title: '请至少设置一个提醒时间', icon: 'none' })
    return
  }
  if (editingSelectedChannelIds.value.length === 0) {
    uni.showToast({ title: '请至少选择一个通知方式', icon: 'none' })
    return
  }

  isSubmitting.value = true
  try {
    const res = await updatePlan(planId, {
      user_id: userStore.userInfo.id,
      name: editingForm.name,
      remark: editingForm.remark,
      start_date: editingForm.startDate,
      end_date: editingForm.endDate,
      notification_times: validTimes,
      channel_ids: editingSelectedChannelIds.value,
      status: editingForm.status,
      priority: editingForm.priority
    })
    if (res.code === 0) {
      uni.showToast({ title: '计划更新成功', icon: 'success' })
      // 先刷新计划列表数据，再收起编辑表单。
      // 若先置 editingPlanId=null 再 loadPlans，色条 class 会经历 --active→无→--active 的往返，
      // 微信小程序 setData diff 机制可能将最终状态与编辑中状态对比认为相同而跳过更新，导致色条停留在中间灰色态。
      // 调换顺序后 planDisplayStatus[A.id] 始终为新 status 值，色条无中间态闪烁。
      await loadPlans()
      editingPlanId.value = null
    }
  } catch (e) {
    uni.showToast({ title: e.message || '更新失败', icon: 'none' })
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

/* ===== 页面标题区 ===== */
.plan-page__header {
  padding: 0 16rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.plan-page__title {
  color: #0e0f0c;
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
}

.plan-page__desc {
  color: #454745;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  padding-top: 8rpx;
  white-space: pre-line;
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
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #c1cab5;
}

.plan-page__new-entry-icon {
  width: 28rpx;
  height: 28rpx;
  display: block;
}

.plan-page__new-entry-text {
  color: #2f6c00;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 新建计划表单 ===== */
.plan-page__form-wrap {
  padding-top: 0;
}

.plan-page__form {
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 32rpx;
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

.plan-page__form-heading {
  color: #0e0f0c;
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
}

.plan-page__field {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.plan-page__label {
  color: #454745;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.plan-page__placeholder {
  color: #868685;
  font-size: 32rpx;
}

.plan-page__input {
  height: 82rpx;
  /* padding 0 12px + line-height 41px：使 input 文本垂直居中（参考 notification.vue 邮件输入框实现） */
  padding: 0 24rpx;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 82rpx;
}

/* 字符限制提示文字 */
.plan-page__limit-text {
  color: #d97706;
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

.plan-page__textarea {
  width: 100%;
  /* 高度 88px = 3行 × 24px line-height + 上下 padding 各 8px，使备注说明默认显示3行 */
  height: 176rpx;
  padding: 16rpx 24rpx;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
}

/* ===== 日期选择器 ===== */
.plan-page__date-range {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
}

/* picker 元素本身设置 flex:1，使两个日期控件平分剩余宽度，共同占满表单单行100% */
.plan-page__date-picker {
  flex: 1;
}

.plan-page__date-separator {
  color: #454745;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
  flex-shrink: 0;
}

.plan-page__picker-display {
  flex: 1;
  height: 82rpx;
  padding: 20rpx 24rpx;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  display: flex;
  align-items: center;
}

.plan-page__picker-text {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 42rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-page__picker-text--placeholder {
  color: #868685;
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
  gap: 8rpx;
}

.plan-page__add-time-icon {
  width: 28rpx;
  height: 28rpx;
  display: block;
}

.plan-page__add-time-text {
  color: #2f6c00;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 500;
}

.plan-page__time-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
  height: 82rpx;
}

/* picker 标签本身设置 width: 50%，确保时间控件宽度为卡片内容区宽度的50% */
.plan-page__time-picker {
  width: 50%;
}

.plan-page__time-picker-display {
  width: 100%;
  height: 82rpx;
  padding: 20rpx 24rpx;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  display: flex;
  align-items: center;
}

.plan-page__time-picker-text {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 42rpx;
}

.plan-page__time-picker-text--placeholder {
  color: #868685;
}

.plan-page__time-delete {
  width: 64rpx;
  height: 82rpx;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.plan-page__time-delete-icon {
  width: 32rpx;
  height: 36rpx;
  display: block;
}

/* ===== 优先级单选框（0-7） ===== */
.plan-page__priority-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20rpx;
  padding-top: 8rpx;
  flex-wrap: wrap;
}

.plan-page__priority-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
}

.plan-page__priority-text {
  color: #0e0f0c;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* ===== 通知方式 ===== */
.plan-page__notify-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 62rpx;
  padding-top: 8rpx;
  flex-wrap: wrap;
}

.plan-page__notify-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14rpx;
}

.plan-page__checkbox {
  width: 40rpx;
  height: 40rpx;
  border-radius: 12rpx;
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

.plan-page__checkmark {
  width: 12rpx;
  height: 20rpx;
  border-right: 2px solid #ffffff;
  border-bottom: 2px solid #ffffff;
  transform: rotate(45deg) translate(-1px, -1px);
}

.plan-page__notify-text {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

.plan-page__notify-empty {
  padding-top: 8rpx;
}

.plan-page__notify-empty-text {
  color: #868685;
  font-size: 28rpx;
  line-height: 40rpx;
}

/* ===== 任务状态单选框 ===== */
.plan-page__status-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 48rpx;
  padding-top: 8rpx;
}

.plan-page__status-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14rpx;
}

.plan-page__radio {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  display: flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}

.plan-page__radio--checked {
  background: #2f6c00;
  box-shadow: inset 0 0 0 1px #2f6c00;
}

.plan-page__radio-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #ffffff;
}

.plan-page__status-text {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

/* ===== 保存按钮 ===== */
.plan-page__save {
  margin-top: 32rpx;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #2f6c00;
  box-shadow: 0 4px 6px -4px rgba(0, 0, 0, 0.1), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 16rpx;
}

.plan-page__save-icon {
  width: 40rpx;
  height: 40rpx;
  display: block;
}

.plan-page__save-text {
  color: #ffffff;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
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
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
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
  background: #e1e0da;
  border-radius: 24rpx 0 0 24rpx;
}

.plan-page__card-stripe--active {
  background: #2f6c00;
}

.plan-page__card-stripe--paused {
  background: #4a4a4a;
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
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-page__card-subtitle {
  color: #454745;
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
  background: #e8ebe6;
  color: #41493a;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

/* ===== 就地展开编辑表单（从卡片延伸，无标题） ===== */
.plan-page__card-edit {
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 0 0 24rpx 24rpx;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 32rpx;
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
  /* 标题区 */
  .plan-page__header {
    padding: 0 8px;
    gap: 8px;
  }
  .plan-page__title {
    font-size: 32px;
    line-height: 36px;
  }
  .plan-page__desc {
    font-size: 16px;
    line-height: 24px;
    padding-top: 4px;
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
    gap: 16px;
  }
  .plan-page__form-heading {
    font-size: 18px;
    line-height: 24px;
    padding-bottom: 8px;
  }
  .plan-page__field {
    gap: 4px;
  }
  .plan-page__label {
    font-size: 14px;
    line-height: 20px;
  }
  .plan-page__placeholder {
    font-size: 16px;
  }
  .plan-page__input {
    height: 41px;
    padding: 0 12px;
    border-radius: 6px;
    font-size: 16px;
    line-height: 41px;
  }
  .plan-page__limit-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }
  .plan-page__textarea {
    height: 88px;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 16px;
    line-height: 24px;
  }
  /* 日期选择器 */
  .plan-page__date-range {
    gap: 8px;
  }
  .plan-page__date-separator {
    font-size: 14px;
    line-height: 20px;
  }
  .plan-page__picker-display {
    height: 41px;
    padding: 10px 12px;
    border-radius: 6px;
  }
  .plan-page__picker-text {
    font-size: 16px;
    line-height: 21px;
  }
  /* 提醒时间 */
  .plan-page__add-time {
    gap: 4px;
  }
  .plan-page__add-time-icon {
    width: 14px;
    height: 14px;
  }
  .plan-page__add-time-text {
    font-size: 14px;
    line-height: 20px;
  }
  .plan-page__time-row {
    gap: 8px;
    height: 41px;
  }
  .plan-page__time-picker-display {
    height: 41px;
    padding: 10px 12px;
    border-radius: 6px;
  }
  .plan-page__time-picker-text {
    font-size: 16px;
    line-height: 21px;
  }
  .plan-page__time-delete {
    width: 32px;
    height: 41px;
  }
  .plan-page__time-delete-icon {
    width: 16px;
    height: 18px;
  }
  /* 优先级单选框 */
  .plan-page__priority-row {
    gap: 10px;
    padding-top: 4px;
  }
  .plan-page__priority-item {
    gap: 4px;
  }
  .plan-page__priority-text {
    font-size: 14px;
    line-height: 20px;
  }
  /* 通知方式 */
  .plan-page__notify-row {
    gap: 31px;
    padding-top: 4px;
  }
  .plan-page__notify-item {
    gap: 7px;
  }
  .plan-page__checkbox {
    width: 20px;
    height: 20px;
    border-radius: 6px;
  }
  .plan-page__checkmark {
    width: 6px;
    height: 10px;
  }
  .plan-page__notify-text {
    font-size: 16px;
    line-height: 24px;
  }
  .plan-page__notify-empty {
    padding-top: 4px;
  }
  .plan-page__notify-empty-text {
    font-size: 14px;
    line-height: 20px;
  }
  /* 任务状态单选框 */
  .plan-page__status-row {
    gap: 24px;
    padding-top: 4px;
  }
  .plan-page__status-item {
    gap: 7px;
  }
  .plan-page__radio {
    width: 20px;
    height: 20px;
  }
  .plan-page__radio-dot {
    width: 8px;
    height: 8px;
  }
  .plan-page__status-text {
    font-size: 16px;
    line-height: 24px;
  }
  /* 保存按钮 */
  .plan-page__save {
    margin-top: 16px;
    height: 48px;
    padding: 12px 0;
    gap: 8px;
  }
  .plan-page__save-icon {
    width: 20px;
    height: 20px;
  }
  .plan-page__save-text {
    font-size: 16px;
    line-height: 24px;
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
    gap: 16px;
  }
}
</style>
