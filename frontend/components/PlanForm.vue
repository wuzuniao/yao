<template>
  <view class="plan-form">
    <!-- 表单标题（新建模式显示，编辑模式由卡片外壳衔接不显示） -->
    <text v-if="showHeading" class="plan-form__heading">{{ $t('plan.newFormHeading') }}</text>

    <!-- 计划名称 -->
    <view class="plan-form__field">
      <text class="plan-form__label">{{ $t('plan.name') }}</text>
      <input
        class="plan-form__input"
        v-model="form.name"
        :placeholder="$t('plan.namePlaceholder')"
        placeholder-class="plan-form__placeholder"
        :placeholder-style="phStyle('name')"
        :maxlength="nameLimit.max"
        @input="e => form.name = nameLimit.handleInput(e)"
        @focus="onFocus('name')"
        @blur="onBlur"
      />
      <text v-if="nameLimit.limitReached" class="plan-form__limit-text">{{ nameLimit.limitHint }}</text>
    </view>

    <!-- 备注说明 -->
    <view class="plan-form__field">
      <text class="plan-form__label">{{ $t('plan.remark') }}</text>
      <textarea
        class="plan-form__textarea"
        v-model="form.remark"
        :placeholder="$t('plan.remarkPlaceholder')"
        placeholder-class="plan-form__placeholder"
        :placeholder-style="phStyle('remark')"
        :maxlength="remarkLimit.max"
        @input="e => form.remark = remarkLimit.handleInput(e)"
        @focus="onFocus('remark')"
        @blur="onBlur"
      />
      <text v-if="remarkLimit.limitReached" class="plan-form__limit-text">{{ remarkLimit.limitHint }}</text>
    </view>

    <!-- 起始日期 + 结束日期 + 重复（合并为一个 1px 边框块：同属计划生效时间定义） -->
    <view class="plan-form__group">
      <!-- 起始日期（end_mode=0 显示起止双控件；1/2 仅开始日期） -->
      <view class="plan-form__field">
        <text class="plan-form__label">{{ $t('plan.dateRange') }}</text>
        <view class="plan-form__date-range">
          <picker mode="date" :value="form.startDate" @change="handleStartDateChange" class="plan-form__date-picker">
            <view class="plan-form__picker-display">
              <text
                class="plan-form__picker-text"
                :class="{ 'plan-form__picker-text--placeholder': !form.startDate }"
              >{{ form.startDate || $t('plan.startDate') }}</text>
            </view>
          </picker>
          <template v-if="form.endMode === 0">
            <text class="plan-form__date-separator">{{ $t('plan.dateTo') }}</text>
            <picker mode="date" :value="form.endDate" @change="handleEndDateChange" class="plan-form__date-picker">
              <view class="plan-form__picker-display">
                <text
                  class="plan-form__picker-text"
                  :class="{ 'plan-form__picker-text--placeholder': !form.endDate }"
                >{{ form.endDate || $t('plan.endDate') }}</text>
              </view>
            </picker>
          </template>
        </view>
        <!-- 时长快捷选项（从开始日期起含头共 N 天，仅按日期结束模式显示） -->
        <view v-if="form.endMode === 0" class="plan-form__duration-row">
          <view
            class="plan-form__duration-chip"
            :class="{ 'plan-form__duration-chip--active': isDurationChipActive(90) }"
            @click="applyDurationQuick(90)"
          >{{ $t('plan.durationQuick90') }}</view>
          <view
            class="plan-form__duration-chip"
            :class="{ 'plan-form__duration-chip--active': isDurationChipActive(365) }"
            @click="applyDurationQuick(365)"
          >{{ $t('plan.durationQuick365') }}</view>
        </view>
      </view>

      <!-- 结束日期单选（2-长期默认 / 0-按日期 / 1-按次数；长期置首并默认选中；
           目标打卡次数为「按打卡次数」的次级字段，隶属本块下方） -->
      <view class="plan-form__field">
        <text class="plan-form__label">{{ $t('plan.endMode') }}</text>
        <view class="plan-form__mode-row">
          <view class="plan-form__mode-item" @click="form.endMode = 2">
            <view class="plan-form__radio" :class="{ 'plan-form__radio--checked': form.endMode === 2 }">
              <view v-if="form.endMode === 2" class="plan-form__radio-dot"></view>
            </view>
            <text class="plan-form__mode-text">{{ $t('plan.endModeForever') }}</text>
          </view>
          <view class="plan-form__mode-item" @click="form.endMode = 0">
            <view class="plan-form__radio" :class="{ 'plan-form__radio--checked': form.endMode === 0 }">
              <view v-if="form.endMode === 0" class="plan-form__radio-dot"></view>
            </view>
            <text class="plan-form__mode-text">{{ $t('plan.endModeDate') }}</text>
          </view>
          <view class="plan-form__mode-item" @click="form.endMode = 1">
            <view class="plan-form__radio" :class="{ 'plan-form__radio--checked': form.endMode === 1 }">
              <view v-if="form.endMode === 1" class="plan-form__radio-dot"></view>
            </view>
            <text class="plan-form__mode-text">{{ $t('plan.endModeCount') }}</text>
          </view>
        </view>
        <!-- 目标打卡次数输入框（end_mode=1 时显示；无副标题，仅输入框以 placeholder 提示） -->
        <view v-if="form.endMode === 1" class="plan-form__subfield">
          <input
            class="plan-form__input"
            type="number"
            v-model="form.totalTargetCount"
            :placeholder="$t('plan.targetCountPlaceholder')"
            placeholder-class="plan-form__placeholder"
          />
        </view>
      </view>

      <!-- 重复（预设 每天/工作日/周末/自定义，选自定义才展开星期多选；位掩码 bit0=周一…bit6=周日） -->
      <view class="plan-form__field">
        <text class="plan-form__label">{{ $t('plan.repeat') }}</text>
        <view class="plan-form__repeat-row">
          <view
            class="plan-form__repeat-preset"
            :class="{ 'plan-form__repeat-preset--active': !repeatCustom && form.repeatWeekdays === 127 }"
            @click="selectRepeatPreset(127)"
          >{{ $t('plan.repeatEveryday') }}</view>
          <view
            class="plan-form__repeat-preset"
            :class="{ 'plan-form__repeat-preset--active': !repeatCustom && form.repeatWeekdays === 31 }"
            @click="selectRepeatPreset(31)"
          >{{ $t('plan.repeatWeekday') }}</view>
          <view
            class="plan-form__repeat-preset"
            :class="{ 'plan-form__repeat-preset--active': !repeatCustom && form.repeatWeekdays === 96 }"
            @click="selectRepeatPreset(96)"
          >{{ $t('plan.repeatWeekend') }}</view>
          <view
            class="plan-form__repeat-preset"
            :class="{ 'plan-form__repeat-preset--active': repeatCustom }"
            @click="selectRepeatCustom"
          >{{ $t('plan.repeatCustom') }}</view>
        </view>
        <view v-if="repeatCustom" class="plan-form__weekdays-row">
          <view
            v-for="(w, i) in weekdaysShort"
            :key="i"
            class="plan-form__weekday-chip"
            :class="{ 'plan-form__weekday-chip--active': isWeekdaySelected(i) }"
            @click="toggleWeekday(i)"
          >{{ w }}</view>
        </view>
      </view>
    </view>

    <!-- 提醒时间（多时间控件，每个时间点独立的提醒次数/间隔配置） -->
    <view class="plan-form__field">
      <view class="plan-form__time-label-row">
        <text class="plan-form__label">{{ $t('plan.time') }}</text>
        <view class="plan-form__add-time" @click="handleAddTime">
          <image class="plan-form__add-time-icon" :src="jiaShijian" mode="aspectFit" />
          <text class="plan-form__add-time-text">{{ $t('plan.addTime') }}</text>
        </view>
      </view>
      <view
        v-for="(tItem, idx) in form.times"
        :key="idx"
        class="plan-form__time-block"
      >
        <view class="plan-form__time-row">
          <picker mode="time" :value="tItem.time" @change="handleTimeChange($event, idx)" class="plan-form__time-picker">
            <view class="plan-form__time-picker-display">
              <text
                class="plan-form__time-picker-text"
                :class="{ 'plan-form__time-picker-text--placeholder': !tItem.time }"
              >{{ tItem.time || $t('plan.selectTime') }}</text>
            </view>
          </picker>
          <view class="plan-form__time-delete" @click="handleDeleteTime(idx)">
            <image class="plan-form__time-delete-icon" :src="shanchuIcon" mode="aspectFit" />
          </view>
        </view>
        <!-- 提醒次数（前置次级标签「提醒次数」+ 1/2/3 chips，3=默认三段式）+ 自定义间隔（count=2 时显示） -->
        <view class="plan-form__followup-row">
          <view class="plan-form__followup-left">
            <text class="plan-form__label-sub">{{ $t('plan.reminderCount') }}</text>
            <view class="plan-form__followup-chips">
              <view
                v-for="n in 3"
                :key="n"
                class="plan-form__followup-chip"
                :class="{ 'plan-form__followup-chip--active': tItem.followupCount === n }"
                @click="setFollowupCount(idx, n)"
              >{{ n }}</view>
            </view>
          </view>
          <picker
            v-if="tItem.followupCount === 2"
            mode="selector"
            :range="intervalOptions(tItem)"
            :value="intervalIndex(tItem)"
            @change="handleIntervalChange($event, idx)"
            class="plan-form__interval-picker"
          >
            <view class="plan-form__interval-display">
              <text class="plan-form__interval-text">{{ $t('plan.interval') }} {{ tItem.followupIntervalMin }}min</text>
            </view>
          </picker>
        </view>
        <text class="plan-form__followup-desc">{{ followupDesc(tItem) }}</text>
      </view>
    </view>

    <!-- 优先级单选框（0-3，数字越小优先级越高，默认3；括号说明不加粗） -->
    <view class="plan-form__field">
      <view class="plan-form__label-row">
        <text class="plan-form__label">{{ $t('plan.priority') }}</text>
        <text class="plan-form__label-hint">{{ $t('plan.priorityHint') }}</text>
      </view>
      <view class="plan-form__priority-row">
        <view
          v-for="n in 4"
          :key="n - 1"
          class="plan-form__priority-item"
          @click="form.priority = n - 1"
        >
          <view class="plan-form__radio" :class="{ 'plan-form__radio--checked': form.priority === n - 1 }">
            <view v-if="form.priority === n - 1" class="plan-form__radio-dot"></view>
          </view>
          <text class="plan-form__priority-text">{{ n - 1 }}</text>
        </view>
      </view>
    </view>

    <!-- 通知方式（从数据库动态加载） -->
    <view class="plan-form__field">
      <text class="plan-form__label">{{ $t('plan.channel') }}</text>
      <view class="plan-form__notify-row" v-if="availableChannels.length > 0">
        <view
          v-for="ch in availableChannels"
          :key="ch.id"
          class="plan-form__notify-item"
          @click="toggleChannel(ch.id)"
        >
          <view class="plan-form__checkbox" :class="{ 'plan-form__checkbox--checked': selectedChannelIds.includes(ch.id) }">
            <view v-if="selectedChannelIds.includes(ch.id)" class="plan-form__checkmark"></view>
          </view>
          <text class="plan-form__notify-text">{{ ch.channel_type }}</text>
        </view>
      </view>
      <view v-else class="plan-form__notify-empty">
        <text class="plan-form__notify-empty-text">{{ $t('plan.channelEmpty') }}</text>
      </view>
    </view>

    <!-- 任务状态（单选框：进行中/暂停/已结束，对应 1/2/0） -->
    <view class="plan-form__field">
      <text class="plan-form__label">{{ $t('plan.status') }}</text>
      <view class="plan-form__status-row">
        <view class="plan-form__status-item" @click="form.status = 1">
          <view class="plan-form__radio" :class="{ 'plan-form__radio--checked': form.status === 1 }">
            <view v-if="form.status === 1" class="plan-form__radio-dot"></view>
          </view>
          <text class="plan-form__status-text">{{ $t('plan.statusActive') }}</text>
        </view>
        <view class="plan-form__status-item" @click="form.status = 2">
          <view class="plan-form__radio" :class="{ 'plan-form__radio--checked': form.status === 2 }">
            <view v-if="form.status === 2" class="plan-form__radio-dot"></view>
          </view>
          <text class="plan-form__status-text">{{ $t('plan.statusPaused') }}</text>
        </view>
        <view class="plan-form__status-item" @click="form.status = 0">
          <view class="plan-form__radio" :class="{ 'plan-form__radio--checked': form.status === 0 }">
            <view v-if="form.status === 0" class="plan-form__radio-dot"></view>
          </view>
          <text class="plan-form__status-text">{{ $t('plan.statusEnded') }}</text>
        </view>
      </view>
    </view>

    <!-- 保存/更新按钮 -->
    <view class="plan-form__save" @click="handleSubmit">
      <image class="plan-form__save-icon" :src="baocunJihuaIcon" mode="aspectFit" />
      <text class="plan-form__save-text">{{ isEdit ? $t('plan.update') : $t('plan.save') }}</text>
    </view>
  </view>
</template>

<script setup>
/**
 * 计划表单组件（PlanForm.vue）
 * --------------------------------------------------------------------------
 * 新建计划与编辑计划共用的统一表单（两表单字段完全一致，差异仅在容器外壳与提交行为）：
 *  - 新建模式：父级传 plan=null + show-heading，外层为独立表单卡片（含标题）
 *  - 编辑模式：父级传 plan 对象，外层为计划卡片下方延伸的编辑区（无标题）
 *  - 父级通过 :key 重建实例实现表单重置（新建 key 固定，编辑 key=plan.id），
 *    组件 setup 时根据 plan 一次性填充字段，避免状态残留
 *  - 提交：校验通过后 emit('submit', payload)，由父级决定调用 createPlan/updatePlan
 *
 * 表单字段（合并块内顺序：起始日期 → 结束日期 → 重复）：
 *  - 计划名称、备注说明
 *  - 起始日期（新建开始日期默认当天；end_mode=0 显示起止双控件 + 90天/365天快捷）
 *  - 结束日期（原「结束方式」；2-长期【置首且新建默认选中】/0-按日期/1-按打卡次数；
 *    目标打卡次数为「按打卡次数」的次级输入框 subfield——无副标题，仅 placeholder 提示）
 *  - 重复（预设 每天/工作日/周末/自定义；仅选中「自定义」才展开星期多选行，
 *    位掩码 bit0=周一…bit6=周日；编辑回显非预设值自动进入自定义模式）
 *  - 提醒时间（每个时间点独立配置提醒次数 1/2/3 与自定义等间隔 5-60 分钟；
 *    新增时间行默认预填当前时间；次数 chips 前置次级「提醒次数」标签 label-sub 不加粗小一号）
 *  - 优先级（0-3，括号说明不加粗）、通知方式、任务状态
 *  - 各字段标题加粗加大（plan-form__label 32rpx/600）使表单段明显区分；
 *    次级标题 label-sub（28rpx/400）
 *  - H5 端鼠标悬停输入框时 placeholder 变淡（CSS :hover，与聚焦变淡一致）
 *
 * 后端契约（对应 backend/app/schemas/plan.py）：
 *  - end_mode=1/2 时 end_date 传 null，由后端 effective_end_date 落 9999-12-31 哨兵
 *  - followup_count=3（默认三段式）时 followup_interval_min 统一归位 10
 *  - 编辑回显：end_mode=1/2 的计划 end_date 为哨兵值，不回填结束日期控件
 */
import { reactive, ref, computed, watch } from 'vue'
import { usePlaceholder } from '../composables/usePlaceholder'
import { useInputLimit } from '../composables/useInputLimit'
import { useThemeIcon } from '../composables/useThemeIcon'
import { useLanguageStore } from '../store/modules/language'
import { tm, t } from '../locale'
import jiaShijianIcon from '../assets/images/jia_shijian.png'
import shanchuIcon from '../assets/images/shanchu.png'
import baocunJihuaIcon from '../assets/images/baocun_jihua.png'

// 图标按当前主题换色（green 用原图，其余主题用 static/theme-icons 产物）
// shanchu（删除红）/baocun_jihua（白色）不参与换色，保持原引用
const jiaShijian = useThemeIcon('jia_shijian.png', jiaShijianIcon)

const props = defineProps({
  /** 编辑时传入计划对象（null=新建模式）；父级通过 :key 重建实例实现重置 */
  plan: { type: Object, default: null },
  /** 可用通知渠道列表（父页面加载，站内信默认勾选逻辑在组件内处理） */
  availableChannels: { type: Array, default: () => [] },
  /** 是否显示表单标题（新建模式 true，编辑模式 false） */
  showHeading: { type: Boolean, default: false }
})

const emit = defineEmits(['submit', 'status-change'])

// 是否编辑模式
const isEdit = computed(() => !!props.plan)

// 星期短标签（来自语言包，随语言切换）
const languageStore = useLanguageStore()
const weekdaysShort = computed(() => {
  void languageStore.current
  return tm('plan.weekdaysShort')
})

// 提醒次数描述文案（随语言切换）
function followupDesc(tItem) {
  void languageStore.current
  if (tItem.followupCount === 1) return t('plan.reminderCountDesc1')
  if (tItem.followupCount === 2) return t('plan.reminderCountDesc2', { n: tItem.followupIntervalMin })
  return t('plan.reminderCountDesc3')
}

// ===== 表单状态（setup 时按 plan 一次性填充；父级 :key 重建实例实现重置） =====

// 获取当前系统时间（HH:MM 格式，用于时间控件默认值）
function getCurrentTime() {
  const now = new Date()
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

// 获取当天日期字符串（YYYY-MM-DD，用于新建计划开始日期默认值）
function getTodayStr() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

// 将后端返回的时间点数组转为表单结构（兼容旧数据：缺省 followup_count 视为 3）
// 无时间点时预填当前时间（与原新建/编辑展开行为一致）
function initTimes(plan) {
  const list = plan?.notification_times
  if (!list || list.length === 0) {
    return [{ time: getCurrentTime(), followupCount: 3, followupIntervalMin: 10 }]
  }
  return list.map(nt => ({
    time: nt.notification_time || nt.time || '',
    followupCount: nt.followup_count ?? 3,
    followupIntervalMin: nt.followup_interval_min ?? 10
  }))
}

const form = reactive({
  name: props.plan?.name || '',
  remark: props.plan?.remark || '',
  // 新建默认开始日期为当天；编辑回显计划实际开始日期
  startDate: props.plan?.start_date || getTodayStr(),
  // 编辑回显：end_mode=1/2 的计划 end_date 为 9999-12-31 哨兵，不回填控件
  endDate: (props.plan && (props.plan.end_mode ?? 0) === 0) ? (props.plan.end_date || '') : '',
  // 新建默认「长期不结束」（首选项）；编辑回显计划实际结束方式（旧数据缺省视为按日期）
  endMode: props.plan ? (props.plan.end_mode ?? 0) : 2,
  totalTargetCount: props.plan?.total_target_count ?? '',
  repeatWeekdays: props.plan?.repeat_weekdays ?? 127,
  times: initTimes(props.plan),
  priority: props.plan?.priority ?? 3,
  status: props.plan?.status ?? 1
})

// 任务状态变化即时通知父级（编辑模式下卡片色条实时跟随表单中的状态单选）
watch(() => form.status, (v) => {
  emit('status-change', v)
})

// 已选通知渠道ID列表
const selectedChannelIds = ref([])
// 渠道默认勾选初始化标志（仅首次拿到渠道列表时初始化，后续列表刷新不打断用户手动勾选）
let channelsInited = false

// 渠道默认勾选：新建=勾选站内信；编辑=保留计划关联的有效渠道 + 站内信
watch(() => props.availableChannels, (list) => {
  if (channelsInited || !list || list.length === 0) return
  channelsInited = true
  if (props.plan) {
    const validIds = new Set(list.map(c => c.id))
    selectedChannelIds.value = (props.plan.channel_ids || []).filter(id => validIds.has(id))
  } else {
    selectedChannelIds.value = []
  }
  const znxChannel = list.find(c => c.channel_type === '站内信')
  if (znxChannel && !selectedChannelIds.value.includes(znxChannel.id)) {
    selectedChannelIds.value.push(znxChannel.id)
  }
}, { immediate: true })

// 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
const { onFocus, onBlur, phStyle } = usePlaceholder()

// 输入框字符限制（与后端字段限制严格匹配：计划名称100字符，备注255字符）
const nameLimit = useInputLimit(100)
const remarkLimit = useInputLimit(255)

// ===== 日期/结束方式 =====

function handleStartDateChange(e) {
  form.startDate = e.detail.value
}

function handleEndDateChange(e) {
  form.endDate = e.detail.value
}

// 快捷时长：从开始日期起含头共 N 天（end = start + N - 1 天）
function applyDurationQuick(days) {
  if (!form.startDate) {
    uni.showToast({ title: t('plan.needStart'), icon: 'none' })
    return
  }
  // 'YYYY-MM-DD' + T00:00:00 确保按本地时区解析（裸日期字符串会按 UTC 解析导致时区偏差）
  const d = new Date(form.startDate + 'T00:00:00')
  d.setDate(d.getDate() + days - 1)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  form.endDate = `${d.getFullYear()}-${m}-${day}`
}

// 快捷 chip 是否激活（结束日期恰为开始日期 + N - 1 天）
function isDurationChipActive(days) {
  if (!form.startDate || !form.endDate) return false
  const s = new Date(form.startDate + 'T00:00:00')
  const e = new Date(form.endDate + 'T00:00:00')
  const diff = Math.round((e - s) / 86400000)
  return diff === days - 1
}

// ===== 重复星期（位掩码 bit0=周一…bit6=周日） =====

// 预设值（127=每天，31=工作日，96=周末）；其余值为自定义组合
const REPEAT_PRESET_VALUES = [127, 31, 96]

// 是否处于「自定义」模式（选中自定义 chip 才展开星期多选行）
// 编辑回显：非预设值（自定义组合）自动进入自定义模式；新建默认预设（每天）
const repeatCustom = ref(
  !!props.plan && !REPEAT_PRESET_VALUES.includes(props.plan.repeat_weekdays ?? 127)
)

// 选择预设（每天/工作日/周末）：退出自定义模式并写入预设值
function selectRepeatPreset(v) {
  repeatCustom.value = false
  form.repeatWeekdays = v
}

// 选择自定义：进入自定义模式，保持当前星期勾选作为起点（预设值对应勾选），由用户自行调整
function selectRepeatCustom() {
  repeatCustom.value = true
}

function isWeekdaySelected(bit) {
  return Boolean(form.repeatWeekdays & (1 << bit))
}

function toggleWeekday(bit) {
  // 不允许清空：至少保留一个星期
  const next = form.repeatWeekdays ^ (1 << bit)
  if (next === 0) {
    uni.showToast({ title: t('plan.weekdayRequired'), icon: 'none' })
    return
  }
  form.repeatWeekdays = next
}

// ===== 提醒时间（含每时间点的提醒次数/间隔） =====

function handleTimeChange(e, idx) {
  form.times[idx].time = e.detail.value
}

function handleAddTime() {
  // 新增时间行默认预填当前时间（与初始行一致，避免空行占位需二次选择）
  form.times.push({ time: getCurrentTime(), followupCount: 3, followupIntervalMin: 10 })
}

function handleDeleteTime(idx) {
  if (form.times.length <= 1) {
    uni.showToast({ title: t('plan.keepOneTime'), icon: 'none' })
    return
  }
  form.times.splice(idx, 1)
}

// 设置提醒次数（切换为 3 时间隔归位默认 10，与后端 Schema 归一行为一致）
function setFollowupCount(idx, n) {
  form.times[idx].followupCount = n
  if (n === 3) {
    form.times[idx].followupIntervalMin = 10
  }
}

// 间隔档位（5-60 分钟常用档；当前值不在档位中时附加，兼容存量数据回显）
const INTERVAL_STEPS = [5, 10, 15, 20, 30, 45, 60]

function intervalOptions(tItem) {
  const v = tItem.followupIntervalMin
  if (!INTERVAL_STEPS.includes(v)) {
    return [...INTERVAL_STEPS, v].sort((a, b) => a - b)
  }
  return INTERVAL_STEPS
}

function intervalIndex(tItem) {
  return intervalOptions(tItem).indexOf(tItem.followupIntervalMin)
}

function handleIntervalChange(e, idx) {
  form.times[idx].followupIntervalMin = intervalOptions(form.times[idx])[Number(e.detail.value)]
}

// ===== 通知方式 =====

function toggleChannel(channelId) {
  const i = selectedChannelIds.value.indexOf(channelId)
  if (i >= 0) {
    selectedChannelIds.value.splice(i, 1)
  } else {
    selectedChannelIds.value.push(channelId)
  }
}

// ===== 提交（校验 + 组装 payload，提交行为由父级执行） =====

function handleSubmit() {
  if (!form.name.trim()) {
    uni.showToast({ title: t('plan.needName'), icon: 'none' })
    return
  }
  if (!form.startDate) {
    uni.showToast({ title: t('plan.needStart'), icon: 'none' })
    return
  }
  if (form.endMode === 0) {
    if (!form.endDate) {
      uni.showToast({ title: t('plan.needEnd'), icon: 'none' })
      return
    }
    if (form.endDate < form.startDate) {
      uni.showToast({ title: t('plan.endBeforeStart'), icon: 'none' })
      return
    }
  }
  if (form.endMode === 1) {
    const n = Number(form.totalTargetCount)
    // 整数校验：小数（如 12.5）前端不拦会被后端 Pydantic int 拒绝，返回英文校验错误
    if (!n || n < 1 || n > 9999 || !Number.isInteger(n)) {
      uni.showToast({ title: t('plan.needTargetCount'), icon: 'none' })
      return
    }
  }
  const validTimes = form.times.filter(it => it.time)
  if (validTimes.length === 0) {
    uni.showToast({ title: t('plan.needTime'), icon: 'none' })
    return
  }
  // 重复时间校验：相同提醒时间会产生两个独立时间点（防重键含 plan_time_id），
  // 调度器会各发一条导致重复提醒，记录页区间也会重叠——保存前拦截
  const timeSet = new Set(validTimes.map(it => it.time))
  if (timeSet.size !== validTimes.length) {
    uni.showToast({ title: t('plan.duplicateTime'), icon: 'none' })
    return
  }
  if (selectedChannelIds.value.length === 0) {
    uni.showToast({ title: t('plan.needChannel'), icon: 'none' })
    return
  }

  emit('submit', {
    name: form.name,
    remark: form.remark,
    start_date: form.startDate,
    // end_mode=1/2 时 end_date 传 null，由后端 effective_end_date 落哨兵值
    end_date: form.endMode === 0 ? form.endDate : null,
    repeat_weekdays: form.repeatWeekdays,
    end_mode: form.endMode,
    total_target_count: form.endMode === 1 ? Number(form.totalTargetCount) : null,
    notification_times: validTimes.map(it => ({
      time: it.time,
      followup_count: it.followupCount,
      // 默认三段式（count=3）间隔不生效，统一传 10 保持数据干净（与后端归一一致）
      followup_interval_min: it.followupCount === 3 ? 10 : it.followupIntervalMin
    })),
    channel_ids: [...selectedChannelIds.value],
    status: form.status,
    priority: form.priority
  })
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
.plan-form {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.plan-form__heading {
  color: var(--color-text-primary);
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
}

.plan-form__field {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

/* 字段标题：加粗加大（32rpx/600），使各表单段明显区分 */
.plan-form__label {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
}

/* 标题行：主标题 + 不加粗的括号说明（如优先级「（数字越小越优先）」） */
.plan-form__label-row {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 8rpx;
}

.plan-form__label-hint {
  color: var(--color-text-secondary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* 次级标题：比主标题小一号且不加粗（28rpx/400），用于隶属主字段的子项标题
 * （目标打卡次数、提醒次数） */
.plan-form__label-sub {
  color: var(--color-text-secondary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* 次级字段容器：隶属主字段的子项（如目标打卡次数隶属起始日期块） */
.plan-form__subfield {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  padding-top: 24rpx;
}

/* H5 端鼠标悬停输入框时 placeholder 变淡（与聚焦变淡行为一致；
 * 小程序/App 端无鼠标悬停场景，聚焦变淡仍由 :placeholder-style（usePlaceholder）承担） */
/* #ifdef H5 */
.plan-form__input:hover .plan-form__placeholder,
.plan-form__textarea:hover .plan-form__placeholder {
  color: #c0c0c0;
}
/* #endif */

.plan-form__placeholder {
  color: var(--color-text-tertiary);
  font-size: 32rpx;
}

.plan-form__input {
  height: 82rpx;
  /* padding 0 12px + line-height 41px：使 input 文本垂直居中（参考 notification.vue 邮件输入框实现） */
  padding: 0 24rpx;
  box-sizing: border-box;
  background: var(--color-card-bg-alt);
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px var(--color-border);
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 82rpx;
}

/* 字符限制提示文字 */
.plan-form__limit-text {
  color: var(--color-warning);
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

.plan-form__textarea {
  width: 100%;
  /* 高度 88px = 3行 × 24px line-height + 上下 padding 各 8px，使备注说明默认显示3行 */
  height: 176rpx;
  padding: 16rpx 24rpx;
  box-sizing: border-box;
  background: var(--color-card-bg-alt);
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px var(--color-border);
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
}

/* ===== 起始日期 + 结束日期 + 重复合并块（1px 边框包裹，同属计划生效时间定义） ===== */
.plan-form__group {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
  padding: 24rpx;
  box-sizing: border-box;
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px var(--color-border);
}

/* 结束方式单选 */
.plan-form__mode-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 40rpx;
  padding-top: 8rpx;
  flex-wrap: wrap;
}

.plan-form__mode-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14rpx;
}

.plan-form__mode-text {
  color: var(--color-text-primary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* 日期选择器 */
.plan-form__date-range {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
}

/* picker 元素本身设置 flex:1，使两个日期控件平分剩余宽度，共同占满表单单行100% */
.plan-form__date-picker {
  flex: 1;
}

.plan-form__date-separator {
  color: var(--color-text-secondary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
  flex-shrink: 0;
}

.plan-form__picker-display {
  flex: 1;
  height: 82rpx;
  padding: 20rpx 24rpx;
  box-sizing: border-box;
  background: var(--color-card-bg-alt);
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px var(--color-border);
  display: flex;
  align-items: center;
}

.plan-form__picker-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 42rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-form__picker-text--placeholder {
  color: var(--color-text-tertiary);
}

/* 时长快捷 chips（90天/365天） */
.plan-form__duration-row {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
  padding-top: 8rpx;
}

.plan-form__duration-chip {
  padding: 8rpx 24rpx;
  border-radius: 9999px;
  background: var(--color-card-bg-alt);
  box-shadow: inset 0 0 0 1px var(--color-border);
  color: var(--color-text-primary);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

.plan-form__duration-chip--active {
  background: var(--color-brand);
  box-shadow: inset 0 0 0 1px var(--color-brand);
  color: var(--color-text-inverse);
}

/* 重复预设 chips（每天/工作日/周末） */
.plan-form__repeat-row {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
  padding-top: 8rpx;
}

.plan-form__repeat-preset {
  padding: 8rpx 24rpx;
  border-radius: 9999px;
  background: var(--color-card-bg-alt);
  box-shadow: inset 0 0 0 1px var(--color-border);
  color: var(--color-text-primary);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

.plan-form__repeat-preset--active {
  background: var(--color-brand);
  box-shadow: inset 0 0 0 1px var(--color-brand);
  color: var(--color-text-inverse);
}

/* 星期多选 chips（周一…周日） */
.plan-form__weekdays-row {
  display: flex;
  flex-direction: row;
  gap: 12rpx;
  padding-top: 8rpx;
}

.plan-form__weekday-chip {
  min-width: 56rpx;
  height: 56rpx;
  padding: 0 8rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  background: var(--color-card-bg-alt);
  box-shadow: inset 0 0 0 1px var(--color-border);
  color: var(--color-text-primary);
  font-size: 24rpx;
  line-height: 56rpx;
  font-weight: 400;
  text-align: center;
}

.plan-form__weekday-chip--active {
  background: var(--color-brand);
  box-shadow: inset 0 0 0 1px var(--color-brand);
  color: var(--color-text-inverse);
}

/* ===== 提醒时间 ===== */
.plan-form__time-label-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.plan-form__add-time {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
}

.plan-form__add-time-icon {
  width: 28rpx;
  height: 28rpx;
  display: block;
}

.plan-form__add-time-text {
  color: var(--color-brand);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 500;
}

.plan-form__time-block {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  padding: 16rpx;
  box-sizing: border-box;
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.plan-form__time-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
  height: 82rpx;
}

/* picker 标签本身设置 width: 50%，确保时间控件宽度为卡片内容区宽度的50% */
.plan-form__time-picker {
  width: 50%;
}

.plan-form__time-picker-display {
  width: 100%;
  height: 82rpx;
  padding: 20rpx 24rpx;
  box-sizing: border-box;
  background: var(--color-card-bg-alt);
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px var(--color-border);
  display: flex;
  align-items: center;
}

.plan-form__time-picker-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 42rpx;
}

.plan-form__time-picker-text--placeholder {
  color: var(--color-text-tertiary);
}

.plan-form__time-delete {
  width: 64rpx;
  height: 82rpx;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.plan-form__time-delete-icon {
  width: 32rpx;
  height: 36rpx;
  display: block;
}

/* 提醒次数 chips（1/2/3）+ 自定义间隔 picker */
.plan-form__followup-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  flex-wrap: wrap;
}

/* 提醒次数左组：次级「提醒次数」标签 + 次数 chips */
.plan-form__followup-left {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}

.plan-form__followup-chips {
  display: flex;
  flex-direction: row;
  gap: 12rpx;
}

.plan-form__followup-chip {
  min-width: 56rpx;
  height: 56rpx;
  padding: 0 8rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  background: var(--color-card-bg-alt);
  box-shadow: inset 0 0 0 1px var(--color-border);
  color: var(--color-text-primary);
  font-size: 24rpx;
  line-height: 56rpx;
  font-weight: 400;
  text-align: center;
}

.plan-form__followup-chip--active {
  background: var(--color-brand);
  box-shadow: inset 0 0 0 1px var(--color-brand);
  color: var(--color-text-inverse);
}

.plan-form__interval-picker {
  flex-shrink: 0;
}

.plan-form__interval-display {
  height: 56rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  background: var(--color-card-bg-alt);
  box-shadow: inset 0 0 0 1px var(--color-border);
  display: flex;
  align-items: center;
}

.plan-form__interval-text {
  color: var(--color-text-primary);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

.plan-form__followup-desc {
  color: var(--color-text-tertiary);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

/* ===== 优先级单选框（0-3） ===== */
.plan-form__priority-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20rpx;
  padding-top: 8rpx;
  flex-wrap: wrap;
}

.plan-form__priority-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
}

.plan-form__priority-text {
  color: var(--color-text-primary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* ===== 通知方式 ===== */
.plan-form__notify-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 62rpx;
  padding-top: 8rpx;
  flex-wrap: wrap;
}

.plan-form__notify-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14rpx;
}

.plan-form__checkbox {
  width: 40rpx;
  height: 40rpx;
  border-radius: 12rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border);
  display: flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}

.plan-form__checkbox--checked {
  background: var(--color-brand);
  box-shadow: inset 0 0 0 1px var(--color-brand);
}

.plan-form__checkmark {
  width: 12rpx;
  height: 20rpx;
  border-right: 2px solid var(--color-text-inverse);
  border-bottom: 2px solid var(--color-text-inverse);
  transform: rotate(45deg) translate(-1px, -1px);
}

.plan-form__notify-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

.plan-form__notify-empty {
  padding-top: 8rpx;
}

.plan-form__notify-empty-text {
  color: var(--color-text-tertiary);
  font-size: 28rpx;
  line-height: 40rpx;
}

/* ===== 任务状态单选框 ===== */
.plan-form__status-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 48rpx;
  padding-top: 8rpx;
}

.plan-form__status-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14rpx;
}

.plan-form__radio {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border);
  display: flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}

.plan-form__radio--checked {
  background: var(--color-brand);
  box-shadow: inset 0 0 0 1px var(--color-brand);
}

.plan-form__radio-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: var(--color-card-bg);
}

.plan-form__status-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

/* ===== 保存按钮 ===== */
.plan-form__save {
  margin-top: 32rpx;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: var(--color-brand);
  box-shadow: var(--shadow-popup);
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 16rpx;
}

.plan-form__save-icon {
  width: 40rpx;
  height: 40rpx;
  display: block;
}

.plan-form__save-text {
  color: var(--color-text-inverse);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 */
@media screen and (min-width: 768px) {
  .plan-form {
    gap: 16px;
  }
  .plan-form__heading {
    font-size: 18px;
    line-height: 24px;
    padding-bottom: 8px;
  }
  .plan-form__field {
    gap: 4px;
  }
  .plan-form__label {
    font-size: 16px;
    line-height: 24px;
  }
  .plan-form__label-row {
    gap: 4px;
  }
  .plan-form__label-hint {
    font-size: 14px;
    line-height: 20px;
  }
  .plan-form__label-sub {
    font-size: 14px;
    line-height: 20px;
  }
  .plan-form__subfield {
    gap: 4px;
    padding-top: 12px;
  }
  .plan-form__placeholder {
    font-size: 16px;
  }
  .plan-form__input {
    height: 41px;
    padding: 0 12px;
    border-radius: 6px;
    font-size: 16px;
    line-height: 41px;
  }
  .plan-form__limit-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }
  .plan-form__textarea {
    height: 88px;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 16px;
    line-height: 24px;
  }
  /* 起始日期 + 结束日期 + 重复合并块 */
  .plan-form__group {
    gap: 16px;
    padding: 12px;
    border-radius: 6px;
  }
  .plan-form__mode-row {
    gap: 20px;
    padding-top: 4px;
  }
  .plan-form__mode-item {
    gap: 7px;
  }
  .plan-form__mode-text {
    font-size: 14px;
    line-height: 20px;
  }
  .plan-form__date-range {
    gap: 8px;
  }
  .plan-form__date-separator {
    font-size: 14px;
    line-height: 20px;
  }
  .plan-form__picker-display {
    height: 41px;
    padding: 10px 12px;
    border-radius: 6px;
  }
  .plan-form__picker-text {
    font-size: 16px;
    line-height: 21px;
  }
  .plan-form__duration-row {
    gap: 8px;
    padding-top: 4px;
  }
  .plan-form__duration-chip {
    padding: 4px 12px;
    font-size: 12px;
    line-height: 16px;
  }
  .plan-form__repeat-row {
    gap: 8px;
    padding-top: 4px;
  }
  .plan-form__repeat-preset {
    padding: 4px 12px;
    font-size: 12px;
    line-height: 16px;
  }
  .plan-form__weekdays-row {
    gap: 6px;
    padding-top: 4px;
  }
  .plan-form__weekday-chip {
    min-width: 28px;
    height: 28px;
    padding: 0 4px;
    font-size: 12px;
    line-height: 28px;
  }
  /* 提醒时间 */
  .plan-form__add-time {
    gap: 4px;
  }
  .plan-form__add-time-icon {
    width: 14px;
    height: 14px;
  }
  .plan-form__add-time-text {
    font-size: 14px;
    line-height: 20px;
  }
  .plan-form__time-block {
    gap: 6px;
    padding: 8px;
    border-radius: 6px;
  }
  .plan-form__time-row {
    gap: 8px;
    height: 41px;
  }
  .plan-form__time-picker-display {
    height: 41px;
    padding: 10px 12px;
    border-radius: 6px;
  }
  .plan-form__time-picker-text {
    font-size: 16px;
    line-height: 21px;
  }
  .plan-form__time-delete {
    width: 32px;
    height: 41px;
  }
  .plan-form__time-delete-icon {
    width: 16px;
    height: 18px;
  }
  .plan-form__followup-row {
    gap: 8px;
  }
  .plan-form__followup-left {
    gap: 6px;
  }
  .plan-form__followup-chips {
    gap: 6px;
  }
  .plan-form__followup-chip {
    min-width: 28px;
    height: 28px;
    padding: 0 4px;
    font-size: 12px;
    line-height: 28px;
  }
  .plan-form__interval-display {
    height: 28px;
    padding: 0 12px;
  }
  .plan-form__interval-text {
    font-size: 12px;
    line-height: 16px;
  }
  .plan-form__followup-desc {
    font-size: 12px;
    line-height: 16px;
  }
  /* 优先级单选框 */
  .plan-form__priority-row {
    gap: 10px;
    padding-top: 4px;
  }
  .plan-form__priority-item {
    gap: 4px;
  }
  .plan-form__priority-text {
    font-size: 14px;
    line-height: 20px;
  }
  /* 通知方式 */
  .plan-form__notify-row {
    gap: 31px;
    padding-top: 4px;
  }
  .plan-form__notify-item {
    gap: 7px;
  }
  .plan-form__checkbox {
    width: 20px;
    height: 20px;
    border-radius: 6px;
  }
  .plan-form__checkmark {
    width: 6px;
    height: 10px;
  }
  .plan-form__notify-text {
    font-size: 16px;
    line-height: 24px;
  }
  .plan-form__notify-empty {
    padding-top: 4px;
  }
  .plan-form__notify-empty-text {
    font-size: 14px;
    line-height: 20px;
  }
  /* 任务状态单选框 */
  .plan-form__status-row {
    gap: 24px;
    padding-top: 4px;
  }
  .plan-form__status-item {
    gap: 7px;
  }
  .plan-form__radio {
    width: 20px;
    height: 20px;
  }
  .plan-form__radio-dot {
    width: 8px;
    height: 8px;
  }
  .plan-form__status-text {
    font-size: 16px;
    line-height: 24px;
  }
  /* 保存按钮 */
  .plan-form__save {
    margin-top: 16px;
    height: 48px;
    padding: 12px 0;
    gap: 8px;
  }
  .plan-form__save-icon {
    width: 20px;
    height: 20px;
  }
  .plan-form__save-text {
    font-size: 16px;
    line-height: 24px;
  }
}
</style>
