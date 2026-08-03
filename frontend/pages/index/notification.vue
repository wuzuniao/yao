<template>
  <!-- #ifdef MP-WEIXIN -->
  <!-- 引导激活时禁用 page 滚动：原蒙版 4 个透明矩形只覆盖高亮洞以外区域，
       高亮洞内无 view 拦截 touchmove，用户在洞内滑动时 page 滚动导致高亮与目标错位。
       page-meta 的 scroll-y 是微信小程序官方属性，可可靠禁用 page 滚动（iOS/Android 均生效），
       且不拦截 click，高亮洞内目标按钮仍可点击 -->
  <page-meta :scroll-y="!guideScrollLock" />
  <!-- #endif -->
  <view class="notification-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="notification-page__main">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/profile 等页面保持一致） -->
      <PageHeader title="通知方式" desc="管理您的提醒接收渠道，确保不错过任何重要提醒。" />

      <!-- 通知方式列表（动态从数据库加载，仅展示用户已配置的通知方式） -->
      <view class="notification-page__section" v-if="channels.length > 0">
        <!-- 站内信卡片（无删除图标、无点击事件，不允许修改） -->
        <view v-if="hasZnx" class="notification-page__card">
          <view class="notification-page__card-info">
            <image class="notification-page__card-icon" :src="znxIcon" mode="aspectFit" />
            <view class="notification-page__card-text">
              <text class="notification-page__card-title">站内信</text>
              <text class="notification-page__card-subtitle">系统内置通知</text>
            </view>
          </view>
        </view>

        <!-- 邮件卡片（含删除图标；点击卡片展开配置表单） -->
        <view v-for="ch in emailChannels" :key="ch.id">
          <view class="notification-page__card" :class="{ 'notification-page__card--disabled': !ch.enabled }" @click="toggleEmailEdit(ch.id)">
            <view class="notification-page__card-info">
              <image class="notification-page__card-icon" :src="yxIcon" mode="aspectFit" />
              <view class="notification-page__card-text">
                <text class="notification-page__card-title">邮件</text>
                <text class="notification-page__card-subtitle">{{ ch.email_config?.email || '点击查看配置' }}</text>
              </view>
            </view>
            <view class="notification-page__card-delete" @click.stop="handleDeleteEmail(ch.id)">
              <image class="notification-page__card-delete-icon" :src="deleteIcon" mode="aspectFit" />
            </view>
          </view>

          <!-- 邮件配置表单（点击卡片展开，含 SMTP/端口/邮箱/密码/是否启用 + 提交按钮） -->
          <view v-if="expandedEmailId === ch.id" class="notification-page__email-form">
            <view class="notification-page__field">
              <text class="notification-page__label">SMTP服务器地址</text>
              <input
                class="notification-page__input"
                :class="{ 'notification-page__input--error': editHostError }"
                v-model="editForm.smtp_host"
                placeholder="例如：smtp.exmail.qq.com"
                placeholder-class="notification-page__placeholder"
                :maxlength="editHostLimit.max"
                @input="e => editForm.smtp_host = editHostLimit.handleInput(e)"
                @blur="editHostError = validateHost(editForm.smtp_host)"
              />
              <text v-if="editHostError" class="notification-page__error-text">{{ editHostError }}</text>
              <text v-if="editHostLimit.limitReached && editHostLimit.limitHint && editHostLimit.limitHint.includes('已达')" class="notification-page__limit-text">{{ editHostLimit.limitHint }}</text>
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">SMTP服务器端口</text>
              <input
                class="notification-page__input"
                :class="{ 'notification-page__input--error': editPortError }"
                v-model="editForm.smtp_port"
                type="number"
                placeholder="例如：465"
                placeholder-class="notification-page__placeholder"
                :maxlength="editPortLimit.max"
                @input="e => { const raw = e.detail.value || ''; const filtered = editPortLimit.handleInput(e); editForm.smtp_port = filtered; editPortHasNonDigit = raw !== filtered }"
                @focus="editPortError = ''"
                @blur="editPortError = editPortHasNonDigit ? '请输入有效的数字' : validatePort(editForm.smtp_port)"
              />
              <text v-if="editPortError" class="notification-page__error-text">{{ editPortError }}</text>
              <text v-if="editPortLimit.limitReached && editPortLimit.limitHint && editPortLimit.limitHint.includes('已达')" class="notification-page__limit-text">{{ editPortLimit.limitHint }}</text>
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">发件邮箱地址</text>
              <input
                class="notification-page__input"
                :class="{ 'notification-page__input--error': editEmailError }"
                v-model="editForm.email"
                placeholder="例如：user@example.com"
                placeholder-class="notification-page__placeholder"
                :maxlength="editEmailLimit.max"
                @input="e => editForm.email = editEmailLimit.handleInput(e)"
                @blur="editEmailError = validateEmail(editForm.email)"
              />
              <text v-if="editEmailError" class="notification-page__error-text">{{ editEmailError }}</text>
              <text v-if="editEmailLimit.limitReached && editEmailLimit.limitHint && editEmailLimit.limitHint.includes('已达')" class="notification-page__limit-text">{{ editEmailLimit.limitHint }}</text>
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">客户端专用密码</text>
              <input
                class="notification-page__input"
                v-model="editForm.password"
                :password="true"
                placeholder="留空表示不修改，重新输入请填写"
                placeholder-class="notification-page__placeholder"
                :maxlength="editPwdLimit.max"
                @input="e => editForm.password = editPwdLimit.handleInput(e)"
              />
              <text v-if="editPwdLimit.limitReached && editPwdLimit.limitHint && editPwdLimit.limitHint.includes('已达')" class="notification-page__limit-text">{{ editPwdLimit.limitHint }}</text>
            </view>
            <!-- 是否启用单选框（与 enabled 字段绑定） -->
            <view class="notification-page__field">
              <text class="notification-page__label">是否启用</text>
              <view class="notification-page__radio-row">
                <view class="notification-page__radio-item" @click="editForm.enabled = true">
                  <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': editForm.enabled }">
                    <view v-if="editForm.enabled" class="notification-page__radio-dot"></view>
                  </view>
                  <text class="notification-page__radio-text">是</text>
                </view>
                <view class="notification-page__radio-item" @click="editForm.enabled = false">
                  <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': !editForm.enabled }">
                    <view v-if="!editForm.enabled" class="notification-page__radio-dot"></view>
                  </view>
                  <text class="notification-page__radio-text">否</text>
                </view>
              </view>
            </view>
            <view class="notification-page__btn-row">
              <view class="notification-page__save notification-page__btn-row-item" @click="handleUpdateEmail(ch.id)">
                <text class="notification-page__save-text">提交</text>
              </view>
              <view class="notification-page__cancel notification-page__btn-row-item" @click="cancelEmailEdit">
                <text class="notification-page__cancel-text">取消</text>
              </view>
            </view>
          </view>
        </view>

        <!-- #ifdef MP-WEIXIN -->
        <!-- 微信订阅消息卡片（含剩余额度与重新授权入口；点击卡片展开启用状态修改表单） -->
        <view v-if="hasWechat">
          <view class="notification-page__card" :class="{ 'notification-page__card--disabled': wechatChannel && !wechatChannel.enabled }" @click="toggleWechatEdit">
            <view class="notification-page__card-info">
              <view class="notification-page__card-badge notification-page__card-badge--wechat">微</view>
              <view class="notification-page__card-text">
                <text class="notification-page__card-title">微信</text>
                <text class="notification-page__card-subtitle">
                  {{ wechatRemaining > 0 ? `订阅消息提醒 · 剩余可发 ${wechatRemaining} 次` : '授权额度已用完，请重新授权' }}
                </text>
              </view>
            </view>
            <view class="notification-page__card-actions">
              <view v-if="wechatRemaining <= 0" class="notification-page__card-reauth" @click.stop="handleWechatReauth">
                <text class="notification-page__card-reauth-text">重新授权</text>
              </view>
              <view class="notification-page__card-delete" @click.stop="handleDeleteWechat">
                <image class="notification-page__card-delete-icon" :src="deleteIcon" mode="aspectFit" />
              </view>
            </view>
          </view>

          <!-- 微信启用状态修改表单（点击卡片展开，仅"是否启用"单选 + 提交/取消按钮） -->
          <view v-if="wechatEditExpanded" class="notification-page__email-form">
            <view class="notification-page__field">
              <text class="notification-page__label">是否启用</text>
              <view class="notification-page__radio-row">
                <view class="notification-page__radio-item" @click="wechatEditForm.enabled = true">
                  <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': wechatEditForm.enabled }">
                    <view v-if="wechatEditForm.enabled" class="notification-page__radio-dot"></view>
                  </view>
                  <text class="notification-page__radio-text">是</text>
                </view>
                <view class="notification-page__radio-item" @click="wechatEditForm.enabled = false">
                  <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': !wechatEditForm.enabled }">
                    <view v-if="!wechatEditForm.enabled" class="notification-page__radio-dot"></view>
                  </view>
                  <text class="notification-page__radio-text">否</text>
                </view>
              </view>
            </view>
            <view class="notification-page__btn-row">
              <view class="notification-page__save notification-page__btn-row-item" @click="handleUpdateWechat">
                <text class="notification-page__save-text">提交</text>
              </view>
              <view class="notification-page__cancel notification-page__btn-row-item" @click="wechatEditExpanded = false">
                <text class="notification-page__cancel-text">取消</text>
              </view>
            </view>
          </view>
        </view>
        <!-- #endif -->

        <!-- #ifdef APP-PLUS -->
        <!-- App 推送卡片（仅 App 端显示；含删除图标，删除后本机不再接收系统通知栏推送） -->
        <view v-if="hasAppPush" class="notification-page__card" :class="{ 'notification-page__card--disabled': appPushChannel && !appPushChannel.enabled }">
          <view class="notification-page__card-info">
            <view class="notification-page__card-badge notification-page__card-badge--app">推</view>
            <view class="notification-page__card-text">
              <text class="notification-page__card-title">App推送</text>
              <text class="notification-page__card-subtitle">系统通知栏提醒 · 已登记 {{ appPushDeviceCount }} 台设备</text>
            </view>
          </view>
          <view class="notification-page__card-delete" @click.stop="handleDeleteAppPush">
            <image class="notification-page__card-delete-icon" :src="deleteIcon" mode="aspectFit" />
          </view>
        </view>
        <!-- #endif -->
      </view>

      <!-- 添加新方式入口卡（点击后切换为"新建通知方式"表单卡） -->
      <view class="notification-page__add guide-target-add-notification" v-if="!showForm" @click="handleAdd">
        <view class="notification-page__add-plus">
          <view class="notification-page__add-plus-h"></view>
          <view class="notification-page__add-plus-v"></view>
        </view>
        <text class="notification-page__add-text">添加新的通知方式</text>
      </view>

      <!-- 新建通知方式表单卡（默认隐藏，点击"添加新的通知方式"后显示，淡入过渡） -->
      <view v-if="showForm">
        <view class="notification-page__form notification-page__form--fade-in guide-target-notification-form-card">
          <text class="notification-page__form-heading">新建通知方式</text>

          <!-- 通知类型（单选框：邮件/微信） -->
          <view class="notification-page__field">
            <text class="notification-page__label">通知类型</text>
            <view class="notification-page__radio-row">
              <view class="notification-page__radio-item guide-target-email-type-radio" @click="selectType('邮件')">
                <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': formType === '邮件' }">
                  <view v-if="formType === '邮件'" class="notification-page__radio-dot"></view>
                </view>
                <text class="notification-page__radio-text">邮件</text>
              </view>
              <!-- #ifdef MP-WEIXIN -->
              <view class="notification-page__radio-item" @click="selectType('微信')">
                <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': formType === '微信' }">
                  <view v-if="formType === '微信'" class="notification-page__radio-dot"></view>
                </view>
                <text class="notification-page__radio-text">微信</text>
              </view>
              <!-- #endif -->
              <!-- #ifdef APP-PLUS -->
              <view class="notification-page__radio-item" @click="selectType('App推送')">
                <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': formType === 'App推送' }">
                  <view v-if="formType === 'App推送'" class="notification-page__radio-dot"></view>
                </view>
                <text class="notification-page__radio-text">App推送</text>
              </view>
              <!-- #endif -->
            </view>
          </view>

          <!-- #ifdef MP-WEIXIN -->
          <!-- 微信订阅授权说明（仅"微信"类型时显示，使用默认文字样式） -->
          <template v-if="formType === '微信'">
            <text>点击下方「授权订阅提醒」并选择允许，打卡时间到达时将通过微信订阅消息提醒您（一次性订阅，每次授权可下发 1 条）。您每日完成打卡时也会自动补充授权额度。</text>
          </template>
          <!-- #endif -->

          <!-- #ifdef APP-PLUS -->
          <!-- App 推送说明（仅"App推送"类型时显示，使用默认文字样式） -->
          <template v-if="formType === 'App推送'">
            <text>点击下方「开启推送」后，打卡时间到达时将通过系统通知栏提醒您，App 退出后依然可以收到。多台设备可分别开启，点击通知栏消息会自动跳转到首页打卡。</text>
          </template>
          <!-- #endif -->

          <!-- 邮件配置表单（仅"邮件"类型时显示） -->
          <template v-if="formType === '邮件'">
            <view class="notification-page__field">
              <text class="notification-page__label">SMTP服务器地址</text>
              <input
                class="notification-page__input"
                :class="{ 'notification-page__input--error': hostError }"
                v-model="form.smtp_host"
                placeholder="例如：smtp.qq.com"
                placeholder-class="notification-page__placeholder"
                :placeholder-style="phStyle('smtp_host')"
                :maxlength="hostLimit.max"
                @input="e => form.smtp_host = hostLimit.handleInput(e)"
                @focus="onFocus('smtp_host')"
                @blur="() => { onBlur(); hostError = validateHost(form.smtp_host) }"
              />
              <text v-if="hostError" class="notification-page__error-text">{{ hostError }}</text>
              <text v-if="hostLimit.limitReached && hostLimit.limitHint && hostLimit.limitHint.includes('已达')" class="notification-page__limit-text">{{ hostLimit.limitHint }}</text>
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">SMTP服务器端口</text>
              <input
                class="notification-page__input"
                :class="{ 'notification-page__input--error': portError }"
                v-model="form.smtp_port"
                type="number"
                placeholder="例如：465"
                placeholder-class="notification-page__placeholder"
                :placeholder-style="phStyle('smtp_port')"
                :maxlength="portLimit.max"
                @input="e => { const raw = e.detail.value || ''; const filtered = portLimit.handleInput(e); form.smtp_port = filtered; portHasNonDigit = raw !== filtered }"
                @focus="() => { onFocus('smtp_port'); portError = '' }"
                @blur="() => { onBlur(); portError = portHasNonDigit ? '请输入有效的数字' : validatePort(form.smtp_port) }"
              />
              <text v-if="portError" class="notification-page__error-text">{{ portError }}</text>
              <text v-if="portLimit.limitReached && portLimit.limitHint && portLimit.limitHint.includes('已达')" class="notification-page__limit-text">{{ portLimit.limitHint }}</text>
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">发件邮箱地址</text>
              <input
                class="notification-page__input"
                :class="{ 'notification-page__input--error': emailError }"
                v-model="form.email"
                placeholder="例如：bbs.wuzuniao@qq.com"
                placeholder-class="notification-page__placeholder"
                :placeholder-style="phStyle('email')"
                :maxlength="emailLimit.max"
                @input="e => form.email = emailLimit.handleInput(e)"
                @focus="onFocus('email')"
                @blur="() => { onBlur(); emailError = validateEmail(form.email) }"
              />
              <text v-if="emailError" class="notification-page__error-text">{{ emailError }}</text>
              <text v-if="emailLimit.limitReached && emailLimit.limitHint && emailLimit.limitHint.includes('已达')" class="notification-page__limit-text">{{ emailLimit.limitHint }}</text>
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">客户端专用密码</text>
              <input
                class="notification-page__input"
                v-model="form.password"
                :password="true"
                placeholder="请输入客户端专用密码"
                placeholder-class="notification-page__placeholder"
                :placeholder-style="phStyle('password')"
                :maxlength="pwdLimit.max"
                @input="e => form.password = pwdLimit.handleInput(e)"
                @focus="onFocus('password')"
                @blur="onBlur"
              />
              <text v-if="pwdLimit.limitReached && pwdLimit.limitHint && pwdLimit.limitHint.includes('已达')" class="notification-page__limit-text">{{ pwdLimit.limitHint }}</text>
            </view>
            <!-- 是否启用单选框（与 enabled 字段绑定，默认是） -->
            <view class="notification-page__field">
              <text class="notification-page__label">是否启用</text>
              <view class="notification-page__radio-row">
                <view class="notification-page__radio-item" @click="form.enabled = true">
                  <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': form.enabled }">
                    <view v-if="form.enabled" class="notification-page__radio-dot"></view>
                  </view>
                  <text class="notification-page__radio-text">是</text>
                </view>
                <view class="notification-page__radio-item" @click="form.enabled = false">
                  <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': !form.enabled }">
                    <view v-if="!form.enabled" class="notification-page__radio-dot"></view>
                  </view>
                  <text class="notification-page__radio-text">否</text>
                </view>
              </view>
            </view>
          </template>

          <!-- 保存按钮：邮件类型填写完整可点击；微信类型点击即发起授权；App推送类型点击即登记本机设备 -->
          <view
            class="notification-page__save guide-target-wechat-auth-button guide-target-email-save-button"
            :class="{ 'notification-page__save--disabled': !canSave }"
            @click="handleSave"
          >
            <text class="notification-page__save-text">{{ saveButtonText }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 邮箱未绑定倒计时弹窗（3秒后自动跳转绑定邮箱页面） -->
    <view v-if="showCountdown" class="notification-page__countdown-mask">
      <view class="notification-page__countdown-box">
        <text class="notification-page__countdown-title">提示</text>
        <text class="notification-page__countdown-text">未绑定邮箱不支持邮件通知，{{ countdown }}秒后跳转绑定邮箱</text>
      </view>
    </view>

    <!-- 新手引导遮罩（仅在引导激活时渲染） -->
    <BeginnerGuide />
  </view>
</template>

<script setup>
/**
 * 通知方式页（notification.vue）
 * --------------------------------------------------------------------------
 * 功能：管理用户接收提醒的渠道
 *  - 通知方式列表：从数据库动态加载用户已配置的通知渠道（站内信、邮件）
 *  - 站内信卡片：无删除图标、无点击事件，由系统注册时自动创建，不允许用户修改
 *  - 邮件卡片：含删除图标；点击卡片展开配置表单，可修改 SMTP 配置后提交更新
 *  - 添加新方式：通知类型单选（微信/邮件），默认选中微信；选邮件时展开 SMTP 配置表单
 *  - 数据存储：邮件 channel_value 以 JSON 字符串存储（含 smtp_host/smtp_port/email/password）
 */
import { reactive, ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import BeginnerGuide from '../../components/BeginnerGuide.vue'
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { useInputLimit } from '../../composables/useInputLimit'
import { useGuideTarget } from '../../composables/useGuideTarget'
import { useUserStore } from '../../store/modules/user'
import { useGuideStore } from '../../store/modules/guide'
import {
  listNotificationChannels,
  createEmailChannel,
  updateEmailChannel,
  deleteNotificationChannel
} from '../../api/modules/notification'
// 微信订阅消息相关（仅微信小程序端使用）
// #ifdef MP-WEIXIN
import { bindWechat } from '../../api/modules/user'
import { updateWechatChannel } from '../../api/modules/notification'
import { useWechatSubscribe } from '../../composables/useWechatSubscribe'
// #endif
// App 推送相关（仅 App 端使用）
// #ifdef APP-PLUS
import { useAppPush } from '../../composables/useAppPush'
// #endif
import znxIcon from '../../assets/images/tz_znx.png'
import yxIcon from '../../assets/images/tz_yx.png'
import deleteIcon from '../../assets/images/shanchu.png'
import { useShare } from '../../composables/useShare'

useShare({ title: '通知方式' })

const userStore = useUserStore()
const guideStore = useGuideStore()

// 引导激活且当前页面为通知方式页时，禁用 page 滚动（配合 page-meta 的 scroll-y）
const guideScrollLock = computed(() => guideStore.isActive && guideStore.currentPage === 'notification')

// 新手引导：上报「添加新的通知方式」按钮与新建通知方式表单卡位置
useGuideTarget('add-notification', '.guide-target-add-notification')
// #ifdef MP-WEIXIN
useGuideTarget('wechat-auth-button', '.guide-target-wechat-auth-button')
// #endif
useGuideTarget('notification-form-card', '.guide-target-notification-form-card')
// 新手引导：上报邮件类型单选框与保存按钮位置（非微信小程序端第 4 步目标）
useGuideTarget('email-type-radio', '.guide-target-email-type-radio')
useGuideTarget('email-save-button', '.guide-target-email-save-button')

// 微信订阅消息授权（仅在微信小程序端生效）
// #ifdef MP-WEIXIN
const { requestSubscribe, isSubscribeSilentRejected } = useWechatSubscribe()
// #endif

// App 推送设备登记（仅在 App 端生效）
// #ifdef APP-PLUS
const { reportDeviceToken, requestPermission } = useAppPush()
// #endif

// 用户的通知渠道列表（从数据库加载）
const channels = ref([])
// 当前展开配置表单的邮件渠道ID（null 表示未展开）
const expandedEmailId = ref(null)
// 卡片切换：默认显示"添加新的通知方式"入口卡，点击后切换为"新建通知方式"表单卡
const showForm = ref(false)
// 表单通知类型：微信小程序端默认 '微信'（订阅消息为推荐提醒方式），App 端默认 'App推送'，其他端默认 '邮件'
let _defaultFormType = '邮件'
// #ifdef MP-WEIXIN
_defaultFormType = '微信'
// #endif
// #ifdef APP-PLUS
_defaultFormType = 'App推送'
// #endif
const formType = ref(_defaultFormType)
// 邮箱未绑定倒计时弹窗（3秒后自动跳转绑定邮箱页面）
const showCountdown = ref(false)
const countdown = ref(3)
let countdownTimer = null
// 新建邮件表单
const form = reactive({
  smtp_host: '',
  smtp_port: '',
  email: '',
  password: '',
  enabled: true
})
// 编辑邮件表单（展开已有邮件卡片时使用）
const editForm = reactive({
  smtp_host: '',
  smtp_port: '',
  email: '',
  password: '',
  enabled: true
})
// 微信启用状态修改表单（仅微信小程序端使用）
// #ifdef MP-WEIXIN
// 微信启用状态修改表单是否展开（点击微信卡片切换）
const wechatEditExpanded = ref(false)
// 微信启用状态修改表单（仅 enabled 字段）
const wechatEditForm = reactive({
  enabled: true
})
// #endif

// 端口格式错误提示（编辑表单与新建表单各自独立）
const portError = ref('')
const editPortError = ref('')
// 端口输入是否有非数字字符（用于 blur 时判断）
const portHasNonDigit = ref(false)
const editPortHasNonDigit = ref(false)
// 邮箱格式错误提示（新建表单）
const emailError = ref('')
// SMTP服务器地址格式错误提示（新建表单）
const hostError = ref('')
// 编辑表单邮箱格式错误提示
const editEmailError = ref('')
// 编辑表单SMTP服务器地址格式错误提示
const editHostError = ref('')

// 输入框 placeholder 聚焦交互：聚焦变浅灰 #c0c0c0，失焦恢复 placeholder-class 原始色
const { onFocus, onBlur, phStyle } = usePlaceholder()

// 输入框字符限制（与后端字段限制严格匹配）
// 编辑表单
const editHostLimit = useInputLimit(255)
const editPortLimit = useInputLimit(5, /^\d$/)
const editEmailLimit = useInputLimit(254)
const editPwdLimit = useInputLimit(64)
// 新建表单
const hostLimit = useInputLimit(255)
const portLimit = useInputLimit(5, /^\d$/)
const emailLimit = useInputLimit(254)
const pwdLimit = useInputLimit(64)

// 计算属性：是否已配置站内信
const hasZnx = computed(() => channels.value.some(ch => ch.channel_type === '站内信'))
// 计算属性：所有邮件渠道
const emailChannels = computed(() => channels.value.filter(ch => ch.channel_type === '邮件'))
// 计算属性：微信渠道相关（仅微信小程序端使用）
// #ifdef MP-WEIXIN
// 计算属性：是否已配置微信渠道
const hasWechat = computed(() => channels.value.some(ch => ch.channel_type === '微信'))
// 计算属性：微信渠道对象
const wechatChannel = computed(() => channels.value.find(ch => ch.channel_type === '微信') || null)
// 计算属性：微信剩余可下发次数（来自后端返回的 remaining）
const wechatRemaining = computed(() => {
  const ch = wechatChannel.value
  return ch && typeof ch.remaining === 'number' ? ch.remaining : 0
})
// #endif

// 计算属性：App 推送渠道相关（仅 App 端使用）
// #ifdef APP-PLUS
// 计算属性：是否已配置 App 推送渠道（每用户仅一行，多设备共存于该行）
const hasAppPush = computed(() => channels.value.some(ch => ch.channel_type === 'app_push'))
// 计算属性：App 推送渠道对象
const appPushChannel = computed(() => channels.value.find(ch => ch.channel_type === 'app_push') || null)
// 计算属性：已登记设备数量（后端仅返回数量与平台，不回传 device_token 原文）
const appPushDeviceCount = computed(() => {
  const ch = appPushChannel.value
  return ch && typeof ch.device_count === 'number' ? ch.device_count : 0
})
// #endif

// 计算属性：保存按钮是否可点击（邮件类型需填写完整；微信/App推送类型可点击）
const canSave = computed(() => {
  if (formType.value === '邮件') {
    return form.smtp_host && form.smtp_port && form.email && form.password
  }
  // #ifdef MP-WEIXIN
  if (formType.value === '微信') {
    return true
  }
  // #endif
  // #ifdef APP-PLUS
  if (formType.value === 'App推送') {
    return true
  }
  // #endif
  return false
})

// 计算属性：保存按钮文案（按通知类型区分）
const saveButtonText = computed(() => {
  // #ifdef MP-WEIXIN
  if (formType.value === '微信') return '授权订阅提醒'
  // #endif
  // #ifdef APP-PLUS
  if (formType.value === 'App推送') return '开启推送'
  // #endif
  return '保存通知'
})

// 端口格式校验：空值返回空，非整数或超出 1-65535 范围返回错误提示
function validatePort(v) {
  if (!v) return ''
  const num = Number(v)
  if (!Number.isInteger(num) || num < 1 || num > 65535) {
    return '端口必须为 1-65535 之间的数字'
  }
  return ''
}

// 邮箱格式校验：参照注册页规则
function validateEmail(v) {
  if (!v) return '请输入邮箱地址'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return '邮箱格式不正确'
  return ''
}

// SMTP服务器地址格式校验：非空 + 基本域名格式
function validateHost(v) {
  if (!v) return '请输入SMTP服务器地址'
  if (!/^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*(\.[a-zA-Z]{2,})$/.test(v) && !/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(v)) {
    return '服务器地址格式不正确'
  }
  return ''
}

// 加载用户通知渠道列表
async function loadChannels() {
  if (!userStore.userInfo) return
  try {
    const res = await listNotificationChannels()
    if (res.code === 0 && res.data) {
      channels.value = res.data
    }
  } catch (e) {
    uni.showToast({ title: e.message || '加载通知方式失败', icon: 'none' })
  }
}

onMounted(() => {
  loadChannels()
})

// 新手引导：页面显示时上报当前页面（引导激活时推进/回退步骤）
onShow(() => {
  guideStore.onPageEnter('notification')
})

// 选择通知类型（选"邮件"时校验用户是否已绑定邮箱）
function selectType(type) {
  if (type === '邮件') {
    // 邮件通知前置校验：未绑定邮箱不允许选择邮件类型，引导跳转绑定邮箱
    if (!userStore.userInfo || !userStore.userInfo.email) {
      startEmailCountdown()
      return
    }
  }
  formType.value = type
  // 新手引导：非微信小程序端选择邮件后进入保存邮件通知步骤
  if (
    guideStore.isActive &&
    guideStore.currentStepData?.target === 'email-type-radio'
  ) {
    guideStore.nextStep()
  }
}

// 启动邮箱未绑定倒计时弹窗（3秒后跳转 profile.vue 绑定邮箱区域）
function startEmailCountdown() {
  showCountdown.value = true
  countdown.value = 3
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      showCountdown.value = false
      uni.navigateTo({ url: '/pages/user/profile?focus=email' })
    }
  }, 1000)
}

function handleAdd() {
  // 点击"添加新的通知方式"入口卡：切换显示"新建通知方式"表单卡
  showForm.value = true
  // 默认通知类型：微信小程序端选"微信"（订阅消息为推荐提醒方式），App 端选"App推送"，其他端选"邮件"
  // #ifdef MP-WEIXIN
  formType.value = '微信'
  // #endif
  // #ifdef APP-PLUS
  formType.value = 'App推送'
  // #endif
  // #ifndef MP-WEIXIN || APP-PLUS
  formType.value = '邮件'
  // #endif
  form.smtp_host = ''
  form.smtp_port = ''
  form.email = ''
  form.password = ''
  form.enabled = true
  portError.value = ''
  emailError.value = ''
  hostError.value = ''
  // 新手引导：当前步骤为「添加新的通知方式」时，点击进入下一步「授权订阅提醒」
  if (guideStore.isActive && guideStore.currentStepData?.target === 'add-notification') {
    guideStore.nextStep()
    // 非微信小程序端已默认选中邮件，直接进入「保存邮件通知」步骤
    if (!guideStore.isWechatMP && guideStore.currentStepData?.target === 'email-type-radio') {
      guideStore.nextStep()
    }
  }
}

// 保存通知：邮件类型走 SMTP 保存；微信类型走授权流程（仅微信小程序端）；App推送类型登记本机设备（仅 App 端）
async function handleSave() {
  // #ifdef MP-WEIXIN
  if (formType.value === '微信') {
    await handleWechatAuthorize()
    return
  }
  // #endif
  // #ifdef APP-PLUS
  if (formType.value === 'App推送') {
    await handleEnableAppPush()
    return
  }
  // #endif
  if (!canSave.value) return
  if (!userStore.userInfo) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  hostError.value = validateHost(form.smtp_host)
  if (hostError.value) {
    uni.showToast({ title: hostError.value, icon: 'none' })
    return
  }
  portError.value = validatePort(form.smtp_port)
  if (portError.value) {
    uni.showToast({ title: portError.value, icon: 'none' })
    return
  }
  emailError.value = validateEmail(form.email)
  if (emailError.value) {
    uni.showToast({ title: emailError.value, icon: 'none' })
    return
  }
  try {
    const res = await createEmailChannel({
      smtp_host: form.smtp_host,
      smtp_port: Number(form.smtp_port),
      email: form.email,
      password: form.password,
      enabled: form.enabled
    })
    if (res.code === 0) {
      uni.showToast({ title: '保存成功', icon: 'success' })
      showForm.value = false
      await loadChannels()
      // 新手引导：非微信小程序端保存邮件通知后进入下一步（步骤 5：制定计划）
      if (guideStore.isActive && guideStore.currentStepData?.target === 'email-save-button') {
        guideStore.nextStep()
      }
    }
  } catch (e) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' })
  }
}

// 点击邮件卡片：展开/收起配置表单
function toggleEmailEdit(channelId) {
  if (expandedEmailId.value === channelId) {
    expandedEmailId.value = null
    return
  }
  // 找到对应渠道，填充表单
  // 注意：password 字段始终置空，后端 API 返回的 password 已为空值（不暴露解密内容）
  // 用户修改密码时需重新输入，留空提交则后端保留原加密密码
  const ch = channels.value.find(c => c.id === channelId)
  if (ch && ch.email_config) {
    editForm.smtp_host = ch.email_config.smtp_host
    editForm.smtp_port = String(ch.email_config.smtp_port)
    editForm.email = ch.email_config.email
    editForm.password = ''
  }
  // 填充启用状态（默认 true）
  editForm.enabled = ch ? !!ch.enabled : true
  editPortError.value = ''
  editHostError.value = ''
  editEmailError.value = ''
  expandedEmailId.value = channelId
}

// 取消邮件配置修改：收起表单并清空校验错误提示
function cancelEmailEdit() {
  expandedEmailId.value = null
  editPortError.value = ''
  editHostError.value = ''
  editEmailError.value = ''
}

// 提交邮件配置更新
// password 为空字符串时后端保留原加密密码，非空时加密新密码后更新
async function handleUpdateEmail(channelId) {
  if (!editForm.smtp_host || !editForm.smtp_port || !editForm.email) {
    uni.showToast({ title: '请填写完整配置', icon: 'none' })
    return
  }
  editHostError.value = validateHost(editForm.smtp_host)
  if (editHostError.value) {
    uni.showToast({ title: editHostError.value, icon: 'none' })
    return
  }
  editPortError.value = validatePort(editForm.smtp_port)
  if (editPortError.value) {
    uni.showToast({ title: editPortError.value, icon: 'none' })
    return
  }
  editEmailError.value = validateEmail(editForm.email)
  if (editEmailError.value) {
    uni.showToast({ title: editEmailError.value, icon: 'none' })
    return
  }
  if (!userStore.userInfo) return
  try {
    const res = await updateEmailChannel({
      channel_id: channelId,
      smtp_host: editForm.smtp_host,
      smtp_port: Number(editForm.smtp_port),
      email: editForm.email,
      password: editForm.password,
      enabled: editForm.enabled
    })
    if (res.code === 0) {
      uni.showToast({ title: '更新成功', icon: 'success' })
      expandedEmailId.value = null
      await loadChannels()
    }
  } catch (e) {
    uni.showToast({ title: e.message || '更新失败', icon: 'none' })
  }
}

// 删除邮件通知方式
async function handleDeleteEmail(channelId) {
  if (!userStore.userInfo) return
  uni.showModal({
    title: '提示',
    content: '确定要删除该邮件通知方式吗？',
    confirmText: '删除',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const r = await deleteNotificationChannel({
          channel_id: channelId
        })
        if (r.code === 0) {
          uni.showToast({ title: '删除成功', icon: 'success' })
          if (expandedEmailId.value === channelId) {
            expandedEmailId.value = null
          }
          await loadChannels()
        }
      } catch (e) {
        uni.showToast({ title: e.message || '删除失败', icon: 'none' })
      }
    }
  })
}

// #ifdef APP-PLUS
// 开启 App 推送：登记本机设备标识到后端（渠道不存在时新建，已存在则追加/刷新本机设备）
async function handleEnableAppPush() {
  if (!userStore.userInfo) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  uni.showLoading({ title: '开启中...' })
  // 用户主动添加 App 推送时才申请系统通知权限（避免 App 启动即弹授权打扰）
  requestPermission()
  const ok = await reportDeviceToken({ createIfMissing: true, silent: false })
  uni.hideLoading()
  if (!ok) return
  uni.showToast({ title: '开启成功', icon: 'success' })
  showForm.value = false
  await loadChannels()
}

// 删除 App 推送通知方式（复用通用删除接口，删除后本机及其他已登记设备均不再收到推送）
async function handleDeleteAppPush() {
  const ch = appPushChannel.value
  if (!ch || !userStore.userInfo) return
  uni.showModal({
    title: '提示',
    content: '确定要删除App推送通知方式吗？删除后所有已登记设备都将不再收到通知栏提醒。',
    confirmText: '删除',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const r = await deleteNotificationChannel({ channel_id: ch.id })
        if (r.code === 0) {
          uni.showToast({ title: '删除成功', icon: 'success' })
          await loadChannels()
        }
      } catch (e) {
        uni.showToast({ title: e.message || '删除失败', icon: 'none' })
      }
    }
  })
}
// #endif

// #ifdef MP-WEIXIN
// 微信订阅授权主流程（发起授权）
// 抽取为独立函数，供「已绑定微信直接授权」与「先绑定微信再授权」两种入口复用
// 真机首次授权弹窗即包含「总是保持以上选择，不再询问」选项，无需二次授权引导
// 当用户勾选「总是保持」并取消后，后续 requestSubscribeMessage 会静默返回 reject，
// 此时通过 getSetting 检测静默拒绝状态，引导用户前往设置重新开启后再次发起授权
async function doWechatAuthorize() {
  uni.showLoading({ title: '授权中...' })
  const ok = await requestSubscribe()
  uni.hideLoading()
  if (ok) {
    uni.showToast({ title: '授权成功', icon: 'success' })
    showForm.value = false
    await loadChannels()
    // 新手引导：授权成功后自动进入下一步（步骤 5：制定计划）
    if (guideStore.isActive && guideStore.currentStepData?.target === 'wechat-auth-button') {
      guideStore.nextStep()
    }
    return
  }
  // 授权未成功：检测是否为静默拒绝（用户此前勾选了「总是保持以上选择」并取消）
  const silentRejected = await isSubscribeSilentRejected()
  if (!silentRejected) return
  // 静默拒绝：引导用户前往小程序设置重新开启订阅消息授权
  uni.showModal({
    title: '需要重新允许授权',
    content: '您此前勾选了「总是保持以上选择」并取消了授权，微信不再弹窗询问。是否前往设置重新开启订阅消息授权？',
    confirmText: '去设置',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      uni.openSetting({
        success: async () => {
          // 设置页返回后再次发起授权（用户若已解除限制，会重新弹官方授权弹窗）
          uni.showLoading({ title: '授权中...' })
          const retryOk = await requestSubscribe()
          uni.hideLoading()
          if (retryOk) {
            uni.showToast({ title: '授权成功', icon: 'success' })
            showForm.value = false
            await loadChannels()
          }
        }
      })
    }
  })
}

// 绑定微信到当前用户：复用微信一键登录获取 code 的流程，将 openid 关联到当前账号
// （后端写入 user_miniapp_accounts，使微信通知可正常下发）
async function bindWechatAccount() {
  if (!userStore.userInfo) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  uni.showLoading({ title: '绑定中...' })
  let finished = false
  const timeout = setTimeout(() => {
    if (!finished) {
      uni.hideLoading()
      uni.showToast({ title: '微信绑定超时，请重试', icon: 'none' })
    }
  }, 10000)
  try {
    let code = null
    const loginRes = await new Promise((resolve, reject) => {
      uni.login({ provider: 'weixin', success: resolve, fail: reject })
    })
    code = loginRes.code
    if (!code) {
      clearTimeout(timeout)
      uni.hideLoading()
      uni.showToast({ title: '仅微信小程序内可绑定微信', icon: 'none' })
      return
    }
    const res = await bindWechat(code)
    clearTimeout(timeout)
    finished = true
    uni.hideLoading()
    if (res.code === 0) {
      // 更新本地登录态与微信绑定状态，随后继续订阅授权
      userStore.setUser(res.data)
      uni.showToast({ title: '微信绑定成功', icon: 'success' })
      await doWechatAuthorize()
    } else {
      uni.showToast({ title: res.msg || '微信绑定失败', icon: 'none' })
    }
  } catch (e) {
    clearTimeout(timeout)
    finished = true
    uni.hideLoading()
    uni.showToast({ title: e.message || '微信绑定失败', icon: 'none' })
  }
}

// 微信订阅授权（新建表单中的「授权订阅提醒」按钮）
// 前置校验：若当前账号未绑定微信（未做过微信一键登录），无法直接接收微信提醒，
// 先弹窗引导用户进行微信一键登录以绑定微信，绑定成功后再发起订阅授权
async function handleWechatAuthorize() {
  if (!userStore.userInfo) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  if (!userStore.userInfo.is_wechat_bound) {
    uni.showModal({
      title: '需先绑定微信',
      content: '您当前账号未绑定微信，无法接收微信提醒。是否现在进行微信一键登录以绑定微信？',
      confirmText: '去绑定',
      cancelText: '暂不',
      success: async (res) => {
        if (!res.confirm) return
        await bindWechatAccount()
      }
    })
    return
  }
  await doWechatAuthorize()
}

// 微信订阅重新授权（列表卡片中额度用尽时显示）：补充一次授权额度
async function handleWechatReauth() {
  if (!userStore.userInfo) return
  uni.showLoading({ title: '授权中...' })
  const ok = await requestSubscribe()
  uni.hideLoading()
  if (ok) {
    uni.showToast({ title: '授权成功', icon: 'success' })
    await loadChannels()
  }
}

// 删除微信通知方式
async function handleDeleteWechat() {
  if (!userStore.userInfo) return
  uni.showModal({
    title: '提示',
    content: '确定要删除微信通知方式吗？',
    confirmText: '删除',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const ch = wechatChannel.value
        if (!ch) return
        const r = await deleteNotificationChannel({ channel_id: ch.id })
        if (r.code === 0) {
          uni.showToast({ title: '删除成功', icon: 'success' })
          wechatEditExpanded.value = false
          await loadChannels()
        }
      } catch (e) {
        uni.showToast({ title: e.message || '删除失败', icon: 'none' })
      }
    }
  })
}

// 点击微信卡片：展开/收起启用状态修改表单
function toggleWechatEdit() {
  if (wechatEditExpanded.value) {
    wechatEditExpanded.value = false
    return
  }
  const ch = wechatChannel.value
  wechatEditForm.enabled = ch ? !!ch.enabled : true
  wechatEditExpanded.value = true
}

// 提交微信启用状态修改
async function handleUpdateWechat() {
  const ch = wechatChannel.value
  if (!ch || !userStore.userInfo) return
  try {
    const res = await updateWechatChannel({
      channel_id: ch.id,
      enabled: wechatEditForm.enabled
    })
    if (res.code === 0) {
      uni.showToast({ title: '更新成功', icon: 'success' })
      wechatEditExpanded.value = false
      await loadChannels()
    }
  } catch (e) {
    uni.showToast({ title: e.message || '更新失败', icon: 'none' })
  }
}
// #endif
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
.notification-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.notification-page__main {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 210rpx 48rpx 64rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
}

/* ===== 通知方式列表 ===== */
.notification-page__section {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.notification-page__card {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
}

/* 通知方式未启用：卡片整体置灰（仅改变颜色，不影响点击修改等功能） */
.notification-page__card--disabled {
  background: var(--color-card-disabled-bg);

  .notification-page__card-title {
    color: var(--color-text-disabled);
  }

  .notification-page__card-subtitle {
    color: var(--color-text-disabled-subtle);
  }

  .notification-page__card-icon,
  .notification-page__card-badge {
    filter: grayscale(1);
    opacity: 0.6;
  }
}

.notification-page__card-info {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 24rpx;
  flex: 1;
  min-width: 0;
}

.notification-page__card-icon {
  width: 96rpx;
  height: 96rpx;
  display: block;
  flex-shrink: 0;
}

.notification-page__card-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.notification-page__card-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

.notification-page__card-subtitle {
  color: var(--color-text-secondary);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
  padding-top: 4rpx;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-page__card-delete {
  width: 64rpx;
  height: 68rpx;
  padding: 16rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.notification-page__card-delete-icon {
  width: 32rpx;
  height: 36rpx;
  display: block;
}

/* 微信/App推送渠道圆形角标（以文字替代二进制图标，避免引入图片资源） */
.notification-page__card-badge {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  flex-shrink: 0;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  color: var(--color-text-inverse);
  font-size: 40rpx;
  font-weight: 600;
}

.notification-page__card-badge--wechat {
  background: var(--color-wechat); // 微信绿，便于用户识别
}

/* App 推送角标（沿用主品牌绿，与微信品牌绿区分） */
.notification-page__card-badge--app {
  background: var(--color-brand);
}

/* 渠道操作区（重新授权 + 删除） */
.notification-page__card-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
  flex-shrink: 0;
}

.notification-page__card-reauth {
  height: 64rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  background: var(--color-wechat);
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
}

.notification-page__card-reauth-text {
  color: var(--color-text-inverse);
  font-size: 26rpx;
  font-weight: 500;
}

/* ===== 邮件配置表单（点击邮件卡片展开） ===== */
.notification-page__email-form {
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border), var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 32rpx;
  margin-top: -16rpx;
}

/* ===== 添加新方式 ===== */
.notification-page__add {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-input);
}

/* CSS 绘制加号图标（避免引入额外二进制资源） */
.notification-page__add-plus {
  position: relative;
  width: 28rpx;
  height: 28rpx;
  flex-shrink: 0;
}

.notification-page__add-plus-h {
  position: absolute;
  top: 50%;
  left: 0;
  width: 28rpx;
  height: 4rpx;
  background: var(--color-brand);
  transform: translateY(-50%);
}

.notification-page__add-plus-v {
  position: absolute;
  left: 50%;
  top: 0;
  width: 4rpx;
  height: 28rpx;
  background: var(--color-brand);
  transform: translateX(-50%);
}

.notification-page__add-text {
  color: var(--color-brand);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 新建通知方式表单卡（样式参照 plan 页"新建计划详情"卡片，保持设计一致） ===== */
.notification-page__form {
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border), var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

/* 卡片切换淡入过渡：点击"添加新的通知方式"后表单卡从透明渐显，视觉过渡自然 */
.notification-page__form--fade-in {
  animation: notification-page-fade-in 0.3s ease-out;
}

@keyframes notification-page-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notification-page__form-heading {
  color: var(--color-text-primary);
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
}

.notification-page__field {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.notification-page__label {
  color: var(--color-text-secondary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.notification-page__placeholder {
  color: var(--color-text-tertiary);
  font-size: 32rpx;
}

.notification-page__input {
  height: 82rpx;
  /* 去除纵向 padding，通过 line-height=height 实现文本垂直居中 */
  /* 解决微信小程序原生 input 组件文本超出下边框问题（含聚焦态） */
  padding: 0 24rpx;
  box-sizing: border-box;
  background: var(--color-card-bg-alt);
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px var(--color-border);
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 82rpx;
}

/* 输入框错误态：红色边框 */
.notification-page__input--error {
  box-shadow: inset 0 0 0 1px var(--color-form-error);
}

/* 错误提示文字 */
.notification-page__error-text {
  color: var(--color-form-error);
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

/* 字符限制提示文字 */
.notification-page__limit-text {
  color: var(--color-warning);
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

/* ===== 通知类型单选框 ===== */
.notification-page__radio-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 62rpx;
  padding-top: 8rpx;
}

.notification-page__radio-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14rpx;
}

.notification-page__radio {
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

.notification-page__radio--checked {
  background: var(--color-brand);
  box-shadow: inset 0 0 0 1px var(--color-brand);
}

/* 单选框选中态圆点（CSS 绘制） */
.notification-page__radio-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: var(--color-card-bg);
}

.notification-page__radio-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

/* ===== 保存通知按钮（参照 plan 页保存按钮样式） ===== */
.notification-page__save {
  margin-top: 32rpx;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: var(--color-brand);
  box-shadow: 0 4px 6px -4px rgba(0, 0, 0, 0.1), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 保存按钮置灰态（邮件类型未填写完整时） */
.notification-page__save--disabled {
  background: var(--color-border-input);
  box-shadow: none;
}

.notification-page__save-text {
  color: var(--color-text-inverse);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* 提交/取消按钮并排行（邮件配置修改表单 & 微信启用状态修改表单复用） */
.notification-page__btn-row {
  display: flex;
  flex-direction: row;
  gap: 24rpx;
}

.notification-page__btn-row-item {
  flex: 1;
}

/* 取消按钮（白底描边，与提交按钮并排） */
.notification-page__cancel {
  margin-top: 32rpx;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-input);
  display: flex;
  justify-content: center;
  align-items: center;
}

.notification-page__cancel-text {
  color: var(--color-brand);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 邮箱未绑定倒计时弹窗 ===== */
.notification-page__countdown-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.notification-page__countdown-box {
  width: 560rpx;
  padding: 48rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.notification-page__countdown-title {
  color: var(--color-text-primary);
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
}

.notification-page__countdown-text {
  color: var(--color-text-secondary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
  text-align: center;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 * 规则：将本页面主要容器的宽度、卡片宽度、按钮尺寸锁定为设计稿原 px 值
 */
@media screen and (min-width: 768px) {
  /* 主容器内边距与间距 */
  .notification-page__main {
    padding: 105px 24px 32px;
    gap: 32px;
  }
  .notification-page__section {
    gap: 16px;
  }
  /* 通知方式卡片 */
  .notification-page__card {
    padding: 12px;
    border-radius: 12px;
  }
  .notification-page__card-info {
    gap: 12px;
  }
  .notification-page__card-icon {
    width: 48px;
    height: 48px;
  }
  .notification-page__card-title {
    font-size: 16px;
    line-height: 24px;
  }
  .notification-page__card-subtitle {
    font-size: 12px;
    line-height: 16px;
    padding-top: 2px;
  }
  .notification-page__card-delete {
    width: 32px;
    height: 34px;
    padding: 8px;
  }
  .notification-page__card-delete-icon {
    width: 16px;
    height: 18px;
  }
  /* 邮件配置表单 */
  .notification-page__email-form {
    padding: 16px;
    border-radius: 12px;
    gap: 16px;
    margin-top: -8px;
  }
  /* 添加新方式入口卡 */
  .notification-page__add {
    gap: 8px;
    padding: 12px;
    border-radius: 12px;
  }
  .notification-page__add-plus {
    width: 14px;
    height: 14px;
  }
  .notification-page__add-plus-h {
    width: 14px;
    height: 2px;
  }
  .notification-page__add-plus-v {
    width: 2px;
    height: 14px;
  }
  .notification-page__add-text {
    font-size: 16px;
    line-height: 24px;
  }
  /* 新建表单卡 */
  .notification-page__form {
    padding: 16px;
    border-radius: 12px;
    gap: 16px;
  }
  .notification-page__form-heading {
    font-size: 18px;
    line-height: 24px;
    padding-bottom: 8px;
  }
  .notification-page__field {
    gap: 4px;
  }
  .notification-page__label {
    font-size: 14px;
    line-height: 20px;
  }
  .notification-page__placeholder {
    font-size: 16px;
  }
  .notification-page__input {
    height: 41px;
    padding: 0 12px;
    border-radius: 6px;
    font-size: 16px;
    line-height: 41px;
  }
  .notification-page__error-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }
  .notification-page__limit-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }
  /* 单选框 */
  .notification-page__radio-row {
    gap: 31px;
    padding-top: 4px;
  }
  .notification-page__radio-item {
    gap: 7px;
  }
  .notification-page__radio {
    width: 20px;
    height: 20px;
  }
  .notification-page__radio-dot {
    width: 8px;
    height: 8px;
  }
  .notification-page__radio-text {
    font-size: 16px;
    line-height: 24px;
  }
  /* 保存按钮 */
  .notification-page__save {
    margin-top: 16px;
    height: 48px;
    padding: 12px 0;
  }
  .notification-page__save-text {
    font-size: 16px;
    line-height: 24px;
  }
  .notification-page__btn-row {
    gap: 12px;
  }
  .notification-page__cancel {
    margin-top: 16px;
    height: 48px;
    padding: 12px 0;
  }
  .notification-page__cancel-text {
    font-size: 16px;
    line-height: 24px;
  }
  /* 倒计时弹窗 */
  .notification-page__countdown-box {
    width: 280px;
    padding: 24px;
    border-radius: 12px;
    gap: 12px;
  }
  .notification-page__countdown-title {
    font-size: 18px;
    line-height: 24px;
  }
  .notification-page__countdown-text {
    font-size: 14px;
    line-height: 20px;
  }
}
</style>
