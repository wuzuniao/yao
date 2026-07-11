<template>
  <view class="forgot-password-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <!-- 找回密码卡片 -->
    <view class="forgot-password-page__card">
      <view class="forgot-password-page__header">
        <text class="forgot-password-page__title">找回密码</text>
      </view>

      <!-- 步骤1：邮箱 + 验证码 -->
      <view v-if="step === 1" class="forgot-password-page__form">
        <!-- 邮箱 -->
        <view class="forgot-password-page__field">
          <text class="forgot-password-page__label">邮箱</text>
          <input
            class="forgot-password-page__input"
            :class="{ 'forgot-password-page__input--error': errors.email }"
            v-model="form.email"
            placeholder="请输入邮箱地址"
            placeholder-class="forgot-password-page__placeholder"
            :placeholder-style="phStyle('email')"
            :maxlength="emailLimit.max"
            @input="e => form.email = emailLimit.handleInput(e)"
            @focus="handleFocus('email')"
            @blur="handleBlur('email')"
          />
          <text v-if="errors.email" class="forgot-password-page__error-text">{{ errors.email }}</text>
          <text v-if="emailLimit.limitReached" class="forgot-password-page__limit-text">{{ emailLimit.limitHint }}</text>
        </view>

        <!-- 验证码 -->
        <view class="forgot-password-page__field">
          <text class="forgot-password-page__label">验证码</text>
          <view class="forgot-password-page__code-row">
            <input
              class="forgot-password-page__code-input"
              :class="{ 'forgot-password-page__code-input--error': errors.code }"
              v-model="form.code"
              placeholder="请输入验证码"
              placeholder-class="forgot-password-page__placeholder"
              :placeholder-style="phStyle('code')"
              :maxlength="codeLimit.max"
              @input="e => form.code = codeLimit.handleInput(e)"
              @focus="handleFocus('code')"
              @blur="handleBlur('code')"
            />
            <view
              class="forgot-password-page__code-btn"
              :class="{ 'forgot-password-page__code-btn--disabled': counting || isSending }"
              @click="handleGetCode"
            >
              <text class="forgot-password-page__code-btn-text">{{ codeText }}</text>
            </view>
          </view>
          <text v-if="errors.code" class="forgot-password-page__error-text">{{ errors.code }}</text>
          <text v-if="codeLimit.limitReached" class="forgot-password-page__limit-text">{{ codeLimit.limitHint }}</text>
        </view>

        <!-- 找回按钮 -->
        <view class="forgot-password-page__submit" @click="handleStep1Submit">
          <text class="forgot-password-page__submit-text">下一步</text>
        </view>
      </view>

      <!-- 步骤2：新密码 + 确认密码 -->
      <view v-else class="forgot-password-page__form">
        <!-- 新密码 -->
        <view class="forgot-password-page__field">
          <text class="forgot-password-page__label">新密码</text>
          <input
            class="forgot-password-page__input"
            :class="{ 'forgot-password-page__input--error': errors.newPassword }"
            v-model="form.newPassword"
            :password="true"
            placeholder="请设置强密码"
            placeholder-class="forgot-password-page__placeholder"
            :placeholder-style="phStyle('newPassword')"
            :maxlength="newPwdLimit.max"
            @input="e => form.newPassword = newPwdLimit.handleInput(e)"
            @focus="handleFocus('newPassword')"
            @blur="handleBlur('newPassword')"
          />
          <text v-if="errors.newPassword" class="forgot-password-page__error-text">{{ errors.newPassword }}</text>
          <text v-if="newPwdLimit.limitReached" class="forgot-password-page__limit-text">{{ newPwdLimit.limitHint }}</text>
        </view>

        <!-- 确认密码 -->
        <view class="forgot-password-page__field">
          <text class="forgot-password-page__label">确认密码</text>
          <input
            class="forgot-password-page__input"
            :class="{ 'forgot-password-page__input--error': errors.confirmPassword }"
            v-model="form.confirmPassword"
            :password="true"
            placeholder="请再次输入密码"
            placeholder-class="forgot-password-page__placeholder"
            :placeholder-style="phStyle('confirmPassword')"
            :maxlength="confirmPwdLimit.max"
            @input="e => form.confirmPassword = confirmPwdLimit.handleInput(e)"
            @focus="handleFocus('confirmPassword')"
            @blur="handleBlur('confirmPassword')"
          />
          <text v-if="errors.confirmPassword" class="forgot-password-page__error-text">{{ errors.confirmPassword }}</text>
          <text v-if="confirmPwdLimit.limitReached" class="forgot-password-page__limit-text">{{ confirmPwdLimit.limitHint }}</text>
        </view>

        <!-- 找回按钮 -->
        <view class="forgot-password-page__submit" @click="handleStep2Submit">
          <text class="forgot-password-page__submit-text">找回</text>
        </view>
      </view>
    </view>

    <!-- 底部登录链接 -->
    <view class="forgot-password-page__footer" @click="goLogin">
      <text class="forgot-password-page__footer-text">返回登录</text>
    </view>
  </view>
</template>

<script setup>
/**
 * 找回密码页（forgot-password.vue）
 * --------------------------------------------------------------------------
 * 功能：密码找回（两步式流程）
 *  - 步骤1：邮箱 + 验证码，验证通过后进入步骤2
 *  - 步骤2：新密码 + 确认密码，提交后更新数据库密码
 *  - 前端验证：邮箱格式、验证码格式、密码复杂性（参照 register.vue）
 *  - 后端验证：验证码匹配、密码复杂性校验
 * 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
 */
import { reactive, ref } from 'vue'
import BackButton from '../../components/BackButton.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { useInputLimit } from '../../composables/useInputLimit'
import { sendResetCode, resetPassword } from '../../api/modules/user'
import { useShare } from '../../composables/useShare'

useShare({ title: '找回密码' })

const step = ref(1)
const form = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})
const errors = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})
const codeText = ref('获取验证码')
const counting = ref(false)
const isSending = ref(false)
const submitting = ref(false)

const { onFocus, onBlur, phStyle } = usePlaceholder()

// 输入框字符限制（与后端字段长度严格匹配）
const emailLimit = useInputLimit(254)
const codeLimit = useInputLimit(6, /^\d$/)
const newPwdLimit = useInputLimit(20)
const confirmPwdLimit = useInputLimit(20)

// ===== 前端输入校验（参照 register.vue）=====
function validateEmail(v) {
  if (!v) return '请输入邮箱地址'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return '邮箱格式不正确'
  return ''
}

function validateCode(v) {
  if (!v) return '请输入验证码'
  if (!/^\d{6}$/.test(v)) return '验证码为 6 位数字'
  return ''
}

function validatePassword(v) {
  if (!v) return '请设置密码'
  if (v.length < 8 || v.length > 20) return '密码长度需为 8-20 位'
  let categories = 0
  if (/[a-z]/.test(v)) categories++
  if (/[A-Z]/.test(v)) categories++
  if (/[0-9]/.test(v)) categories++
  if (/[^a-zA-Z0-9]/.test(v)) categories++
  if (categories < 3) return '密码需包含大小写字母、数字、特殊符号中的至少三种'
  return ''
}

function validateConfirmPassword(v) {
  if (!v) return '请再次输入密码'
  if (v !== form.newPassword) return '两次密码不一致'
  return ''
}

function validateField(field) {
  const map = {
    email: validateEmail,
    code: validateCode,
    newPassword: validatePassword,
    confirmPassword: validateConfirmPassword
  }
  errors[field] = map[field](form[field])
}

function handleBlur(field) {
  onBlur()
  validateField(field)
}

function handleFocus(field) {
  onFocus(field)
  errors[field] = ''
}

// ===== 获取验证码 =====
async function handleGetCode() {
  if (counting.value || isSending.value) return
  const emailErr = validateEmail(form.email)
  if (emailErr) {
    errors.email = emailErr
    uni.showToast({ title: emailErr, icon: 'none' })
    return
  }
  isSending.value = true
  codeText.value = '发送中...'
  try {
    await sendResetCode(form.email)
    uni.showToast({ title: '验证码已发送', icon: 'none' })
    startCountdown()
  } catch (e) {
    // 发送失败恢复按钮，允许用户立即重试
    codeText.value = '获取验证码'
    uni.showToast({ title: e.message, icon: 'none' })
  } finally {
    isSending.value = false
  }
}

function startCountdown() {
  let sec = 60
  counting.value = true
  codeText.value = `${sec}s`
  const timer = setInterval(() => {
    sec--
    if (sec <= 0) {
      clearInterval(timer)
      counting.value = false
      codeText.value = '获取验证码'
    } else {
      codeText.value = `${sec}s`
    }
  }, 1000)
}

// ===== 步骤1提交：验证邮箱和验证码 =====
async function handleStep1Submit() {
  if (submitting.value) return

  validateField('email')
  validateField('code')
  const firstErr = ['email', 'code'].find((f) => errors[f])
  if (firstErr) {
    uni.showToast({ title: errors[firstErr], icon: 'none' })
    return
  }

  submitting.value = true
  try {
    step.value = 2
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

// ===== 步骤2提交：验证新密码并重置 =====
async function handleStep2Submit() {
  if (submitting.value) return

  validateField('newPassword')
  validateField('confirmPassword')
  const firstErr = ['newPassword', 'confirmPassword'].find((f) => errors[f])
  if (firstErr) {
    uni.showToast({ title: errors[firstErr], icon: 'none' })
    return
  }

  submitting.value = true
  try {
    await resetPassword({
      email: form.email,
      code: form.code,
      new_password: form.newPassword
    })
    uni.showToast({ title: '密码重置成功', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/user/login' })
    }, 1500)
  } catch (e) {
    // 验证码错误时统一提示"请输入正确验证码"
    const msg = /验证码/.test(e.message) ? '请输入正确验证码' : e.message
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  uni.navigateTo({ url: '/pages/user/login' })
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
.forgot-password-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
  padding: 210rpx 48rpx 72rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* ===== 找回密码卡片 ===== */
.forgot-password-page__card {
  width: 684rpx;
  padding: 48rpx;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 48rpx;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 48rpx;
}

.forgot-password-page__header {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  align-items: center;
}

.forgot-password-page__title {
  color: #0e0f0c;
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
  text-align: center;
}

/* ===== 表单 ===== */
.forgot-password-page__form {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.forgot-password-page__field {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.forgot-password-page__label {
  color: #0e0f0c;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.forgot-password-page__input {
  height: 98rpx;
  padding: 28rpx 24rpx 24rpx;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 24rpx;
  box-shadow: inset 0 0 0 1px #c1cab5;
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 42rpx;
}

.forgot-password-page__input--error {
  box-shadow: inset 0 0 0 1px #e5484d;
}

.forgot-password-page__error-text {
  color: #e5484d;
  font-size: 24rpx;
  line-height: 32rpx;
}

/* 字符限制提示文字 */
.forgot-password-page__limit-text {
  color: #d97706;
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

.forgot-password-page__placeholder {
  color: #454745;
  font-size: 32rpx;
}

/* ===== 验证码行 ===== */
.forgot-password-page__code-row {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
}

.forgot-password-page__code-input {
  flex: 1;
  height: 98rpx;
  padding: 28rpx 24rpx 24rpx;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 24rpx;
  box-shadow: inset 0 0 0 1px #c1cab5;
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 42rpx;
}

.forgot-password-page__code-input--error {
  box-shadow: inset 0 0 0 1px #e5484d;
}

.forgot-password-page__code-btn {
  width: 192rpx;
  height: 98rpx;
  padding: 27rpx 24rpx 29rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  box-shadow: inset 0 0 0 1px #c1cab5;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.forgot-password-page__code-btn--disabled {
  opacity: 0.6;
}

.forgot-password-page__code-btn-text {
  color: #0e0f0c;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* ===== 找回按钮 ===== */
.forgot-password-page__submit {
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  background: #9fe870;
  border-radius: 48rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.forgot-password-page__submit-text {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 底部登录链接 ===== */
.forgot-password-page__footer {
  margin-top: 48rpx;
  display: flex;
  justify-content: center;
}

.forgot-password-page__footer-text {
  color: #454745;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 * 规则：将本页面主要容器的宽度、卡片宽度、按钮尺寸锁定为设计稿原 px 值
 */
@media screen and (min-width: 768px) {
  /* 页面 padding */
  .forgot-password-page {
    padding: 105px 24px 36px;
  }

  /* 找回密码卡片 */
  .forgot-password-page__card {
    width: 342px;
    padding: 24px;
    border-radius: 24px;
    gap: 24px;
  }

  /* 标题区 */
  .forgot-password-page__header {
    gap: 8px;
  }

  .forgot-password-page__title {
    font-size: 32px;
    line-height: 36px;
  }

  /* 表单 */
  .forgot-password-page__form {
    gap: 16px;
  }

  .forgot-password-page__field {
    gap: 8px;
  }

  .forgot-password-page__label {
    font-size: 14px;
    line-height: 20px;
  }

  /* 输入框 */
  .forgot-password-page__input {
    height: 49px;
    padding: 14px 12px 12px;
    border-radius: 12px;
    font-size: 16px;
    line-height: 21px;
  }

  .forgot-password-page__error-text {
    font-size: 12px;
    line-height: 16px;
  }

  .forgot-password-page__limit-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }

  .forgot-password-page__placeholder {
    font-size: 16px;
  }

  /* 验证码行 */
  .forgot-password-page__code-row {
    gap: 8px;
  }

  .forgot-password-page__code-input {
    height: 49px;
    padding: 14px 12px 12px;
    border-radius: 12px;
    font-size: 16px;
    line-height: 21px;
  }

  .forgot-password-page__code-btn {
    width: 96px;
    height: 49px;
    padding: 13.5px 12px 14.5px;
    border-radius: 12px;
  }

  .forgot-password-page__code-btn-text {
    font-size: 14px;
    line-height: 20px;
  }

  /* 找回按钮 */
  .forgot-password-page__submit {
    height: 48px;
    padding: 12px 0;
    border-radius: 24px;
  }

  .forgot-password-page__submit-text {
    font-size: 16px;
    line-height: 24px;
  }

  /* 底部登录链接 */
  .forgot-password-page__footer {
    margin-top: 24px;
  }

  .forgot-password-page__footer-text {
    font-size: 16px;
    line-height: 24px;
  }
}
</style>
