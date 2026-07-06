<template>
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
          <view class="notification-page__card" @click="toggleEmailEdit(ch.id)">
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
                v-model="editForm.smtp_host"
                placeholder="例如：smtp.exmail.qq.com"
                placeholder-class="notification-page__placeholder"
                :maxlength="editHostLimit.max"
                @input="e => editForm.smtp_host = editHostLimit.handleInput(e)"
              />
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">SMTP服务器端口</text>
              <input
                class="notification-page__input"
                v-model="editForm.smtp_port"
                type="number"
                placeholder="例如：465"
                placeholder-class="notification-page__placeholder"
                :maxlength="editPortLimit.max"
                @input="e => editForm.smtp_port = editPortLimit.handleInput(e)"
                @blur="editPortError = validatePort(editForm.smtp_port)"
              />
              <text v-if="editPortError" style="color: #e5484d; font-size: 12px; line-height: 16px; margin-top: 4px;">{{ editPortError }}</text>
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">发件邮箱地址</text>
              <input
                class="notification-page__input"
                v-model="editForm.email"
                placeholder="例如：user@example.com"
                placeholder-class="notification-page__placeholder"
                :maxlength="editEmailLimit.max"
                @input="e => editForm.email = editEmailLimit.handleInput(e)"
              />
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
            <view class="notification-page__save" @click="handleUpdateEmail(ch.id)">
              <text class="notification-page__save-text">提交</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 添加新方式入口卡（点击后切换为"新建通知方式"表单卡） -->
      <view class="notification-page__add" v-if="!showForm" @click="handleAdd">
        <view class="notification-page__add-plus">
          <view class="notification-page__add-plus-h"></view>
          <view class="notification-page__add-plus-v"></view>
        </view>
        <text class="notification-page__add-text">添加新的通知方式</text>
      </view>

      <!-- 新建通知方式表单卡（默认隐藏，点击"添加新的通知方式"后显示，淡入过渡） -->
      <view v-if="showForm">
        <view class="notification-page__form notification-page__form--fade-in">
          <text class="notification-page__form-heading">新建通知方式</text>

          <!-- 通知类型（单选框：邮件/站内信，邮件在前） -->
          <view class="notification-page__field">
            <text class="notification-page__label">通知类型</text>
            <view class="notification-page__radio-row">
              <view class="notification-page__radio-item" @click="selectType('邮件')">
                <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': formType === '邮件' }">
                  <view v-if="formType === '邮件'" class="notification-page__radio-dot"></view>
                </view>
                <text class="notification-page__radio-text">邮件</text>
              </view>
              <view class="notification-page__radio-item" @click="selectType('站内信')">
                <view class="notification-page__radio" :class="{ 'notification-page__radio--checked': formType === '站内信' }">
                  <view v-if="formType === '站内信'" class="notification-page__radio-dot"></view>
                </view>
                <text class="notification-page__radio-text">站内信</text>
              </view>
            </view>
          </view>

          <!-- 邮件配置表单（仅"邮件"类型时显示） -->
          <template v-if="formType === '邮件'">
            <view class="notification-page__field">
              <text class="notification-page__label">SMTP服务器地址</text>
              <input
                class="notification-page__input"
                v-model="form.smtp_host"
                placeholder="例如：smtp.qq.com"
                placeholder-class="notification-page__placeholder"
                :placeholder-style="phStyle('smtp_host')"
                :maxlength="hostLimit.max"
                @input="e => form.smtp_host = hostLimit.handleInput(e)"
                @focus="onFocus('smtp_host')"
                @blur="onBlur"
              />
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">SMTP服务器端口</text>
              <input
                class="notification-page__input"
                v-model="form.smtp_port"
                type="number"
                placeholder="例如：465"
                placeholder-class="notification-page__placeholder"
                :placeholder-style="phStyle('smtp_port')"
                :maxlength="portLimit.max"
                @input="e => form.smtp_port = portLimit.handleInput(e)"
                @focus="onFocus('smtp_port')"
                @blur="() => { onBlur(); portError = validatePort(form.smtp_port) }"
              />
              <text v-if="portError" style="color: #e5484d; font-size: 12px; line-height: 16px; margin-top: 4px;">{{ portError }}</text>
            </view>
            <view class="notification-page__field">
              <text class="notification-page__label">发件邮箱地址</text>
              <input
                class="notification-page__input"
                v-model="form.email"
                placeholder="例如：bbs.wuzuniao@qq.com"
                placeholder-class="notification-page__placeholder"
                :placeholder-style="phStyle('email')"
                :maxlength="emailLimit.max"
                @input="e => form.email = emailLimit.handleInput(e)"
                @focus="onFocus('email')"
                @blur="onBlur"
              />
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

          <!-- 保存按钮：站内信类型置灰不可点击；邮件类型且填写完整时可点击 -->
          <view
            class="notification-page__save"
            :class="{ 'notification-page__save--disabled': !canSave }"
            @click="handleSave"
          >
            <text class="notification-page__save-text">保存通知</text>
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
 *  - 添加新方式：通知类型单选（站内信/邮件），选站内信时保存按钮置灰；选邮件时展开 SMTP 配置表单
 *  - 数据存储：邮件 channel_value 以 JSON 字符串存储（含 smtp_host/smtp_port/email/password）
 */
import { reactive, ref, computed, onMounted } from 'vue'
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { useInputLimit } from '../../composables/useInputLimit'
import { useUserStore } from '../../store/modules/user'
import {
  listNotificationChannels,
  createEmailChannel,
  updateEmailChannel,
  deleteNotificationChannel
} from '../../api/modules/notification'
import znxIcon from '../../assets/images/tz_znx.png'
import yxIcon from '../../assets/images/tz_yx.png'
import deleteIcon from '../../assets/images/shanchu.png'
import { useShare } from '../../composables/useShare'

useShare({ title: '通知方式' })

const userStore = useUserStore()

// 用户的通知渠道列表（从数据库加载）
const channels = ref([])
// 当前展开配置表单的邮件渠道ID（null 表示未展开）
const expandedEmailId = ref(null)
// 卡片切换：默认显示"添加新的通知方式"入口卡，点击后切换为"新建通知方式"表单卡
const showForm = ref(false)
// 表单通知类型（'站内信' / '邮件'）
const formType = ref('站内信')
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

// 端口格式错误提示（编辑表单与新建表单各自独立）
const portError = ref('')
const editPortError = ref('')

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

// 计算属性：保存按钮是否可点击（站内信类型置灰；邮件类型需填写完整）
const canSave = computed(() => {
  if (formType.value === '邮件') {
    return form.smtp_host && form.smtp_port && form.email && form.password
  }
  return false
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

// 加载用户通知渠道列表
async function loadChannels() {
  if (!userStore.userInfo) return
  try {
    const res = await listNotificationChannels(userStore.userInfo.id)
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

// 选择通知类型（选"邮件"时校验用户是否已绑定邮箱）
function selectType(type) {
  if (type === '邮件') {
    // 邮件通知前置校验：未绑定邮箱不允许选择邮件类型
    if (!userStore.userInfo || !userStore.userInfo.email) {
      uni.showModal({
        title: '提示',
        content: '未绑定邮箱不支持邮件通知，请先绑定邮箱',
        showCancel: false,
        confirmText: '我知道了'
      })
      return
    }
  }
  formType.value = type
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
  // 默认选中"邮件"选项
  formType.value = '邮件'
  form.smtp_host = ''
  form.smtp_port = ''
  form.email = ''
  form.password = ''
  form.enabled = true
  portError.value = ''
  // 未绑定邮箱时启动3秒倒计时弹窗，结束后跳转绑定邮箱页面
  if (!userStore.userInfo || !userStore.userInfo.email) {
    startEmailCountdown()
  }
}

// 保存通知（仅邮件类型可保存）
async function handleSave() {
  if (!canSave.value) return
  if (!userStore.userInfo) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  portError.value = validatePort(form.smtp_port)
  if (portError.value) {
    uni.showToast({ title: portError.value, icon: 'none' })
    return
  }
  try {
    const res = await createEmailChannel({
      user_id: userStore.userInfo.id,
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
  expandedEmailId.value = channelId
}

// 提交邮件配置更新
// password 为空字符串时后端保留原加密密码，非空时加密新密码后更新
async function handleUpdateEmail(channelId) {
  if (!editForm.smtp_host || !editForm.smtp_port || !editForm.email) {
    uni.showToast({ title: '请填写完整配置', icon: 'none' })
    return
  }
  editPortError.value = validatePort(editForm.smtp_port)
  if (editPortError.value) {
    uni.showToast({ title: editPortError.value, icon: 'none' })
    return
  }
  if (!userStore.userInfo) return
  try {
    const res = await updateEmailChannel({
      channel_id: channelId,
      user_id: userStore.userInfo.id,
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
          channel_id: channelId,
          user_id: userStore.userInfo.id
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
</script>

<style lang="scss">
.notification-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.notification-page__main {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 105px 24px 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ===== 通知方式列表 ===== */
.notification-page__section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.notification-page__card {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
}

.notification-page__card-info {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.notification-page__card-icon {
  width: 48px;
  height: 48px;
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
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

.notification-page__card-subtitle {
  color: #454745;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
  padding-top: 2px;
  /* 动态截断：占满可用宽度后省略号截断 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-page__card-delete {
  width: 32px;
  height: 34px;
  padding: 8px;
  box-sizing: border-box;
  border-radius: 9999px;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.notification-page__card-delete-icon {
  width: 16px;
  height: 18px;
  display: block;
}

/* ===== 邮件配置表单（点击邮件卡片展开） ===== */
.notification-page__email-form {
  padding: 16px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: -8px;
}

/* ===== 添加新方式 ===== */
.notification-page__add {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 12px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #c1cab5;
}

/* CSS 绘制加号图标（避免引入额外二进制资源） */
.notification-page__add-plus {
  position: relative;
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.notification-page__add-plus-h {
  position: absolute;
  top: 50%;
  left: 0;
  width: 14px;
  height: 2px;
  background: #2f6c00;
  transform: translateY(-50%);
}

.notification-page__add-plus-v {
  position: absolute;
  left: 50%;
  top: 0;
  width: 2px;
  height: 14px;
  background: #2f6c00;
  transform: translateX(-50%);
}

.notification-page__add-text {
  color: #2f6c00;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

/* ===== 新建通知方式表单卡（样式参照 plan 页"新建计划详情"卡片，保持设计一致） ===== */
.notification-page__form {
  padding: 16px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  color: #0e0f0c;
  font-size: 18px;
  line-height: 24px;
  font-weight: 600;
  padding-bottom: 8px;
}

.notification-page__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.notification-page__label {
  color: #454745;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.notification-page__placeholder {
  color: #868685;
  font-size: 16px;
}

.notification-page__input {
  height: 41px;
  /* 去除纵向 padding，通过 line-height=height 实现文本垂直居中 */
  /* 解决微信小程序原生 input 组件文本超出下边框问题（含聚焦态） */
  padding: 0 12px;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 6px;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  color: #0e0f0c;
  font-size: 16px;
  line-height: 41px;
}

/* ===== 通知类型单选框 ===== */
.notification-page__radio-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 31px;
  padding-top: 4px;
}

.notification-page__radio-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 7px;
}

.notification-page__radio {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  display: flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}

.notification-page__radio--checked {
  background: #2f6c00;
  box-shadow: inset 0 0 0 1px #2f6c00;
}

/* 单选框选中态圆点（CSS 绘制） */
.notification-page__radio-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ffffff;
}

.notification-page__radio-text {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}

/* ===== 保存通知按钮（参照 plan 页保存按钮样式） ===== */
.notification-page__save {
  margin-top: 16px;
  height: 48px;
  padding: 12px 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #2f6c00;
  box-shadow: 0 4px 6px -4px rgba(0, 0, 0, 0.1), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 保存按钮置灰态（站内信类型或邮件类型未填写完整时） */
.notification-page__save--disabled {
  background: #c1cab5;
  box-shadow: none;
}

.notification-page__save-text {
  color: #ffffff;
  font-size: 16px;
  line-height: 24px;
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
  width: 280px;
  padding: 24px;
  box-sizing: border-box;
  border-radius: 12px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.notification-page__countdown-title {
  color: #0e0f0c;
  font-size: 18px;
  line-height: 24px;
  font-weight: 600;
}

.notification-page__countdown-text {
  color: #454745;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
  text-align: center;
}
</style>
