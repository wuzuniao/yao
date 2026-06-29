<template>
  <view class="forgot-password-page">
    <!-- 顶部通知按钮（复用项目通知组件，非导航栏） -->
    <NoticeButton :has-notification="false" />

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
            @focus="handleFocus('email')"
            @blur="handleBlur('email')"
          />
          <text v-if="errors.email" class="forgot-password-page__error-text">{{ errors.email }}</text>
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
              @focus="handleFocus('code')"
              @blur="handleBlur('code')"
            />
            <view class="forgot-password-page__code-btn" @click="handleGetCode">
              <text class="forgot-password-page__code-btn-text">{{ codeText }}</text>
            </view>
          </view>
          <text v-if="errors.code" class="forgot-password-page__error-text">{{ errors.code }}</text>
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
            @focus="handleFocus('newPassword')"
            @blur="handleBlur('newPassword')"
          />
          <text v-if="errors.newPassword" class="forgot-password-page__error-text">{{ errors.newPassword }}</text>
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
            @focus="handleFocus('confirmPassword')"
            @blur="handleBlur('confirmPassword')"
          />
          <text v-if="errors.confirmPassword" class="forgot-password-page__error-text">{{ errors.confirmPassword }}</text>
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
import NoticeButton from '../../components/NoticeButton.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { sendResetCode, resetPassword } from '../../api/modules/user'

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
const submitting = ref(false)

const { onFocus, onBlur, phStyle } = usePlaceholder()

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
  if (counting.value) return
  const emailErr = validateEmail(form.email)
  if (emailErr) {
    errors.email = emailErr
    uni.showToast({ title: emailErr, icon: 'none' })
    return
  }
  try {
    await sendResetCode(form.email)
    uni.showToast({ title: '验证码已发送', icon: 'none' })
    startCountdown()
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
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
    uni.showToast({ title: e.message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  uni.navigateTo({ url: '/pages/user/login' })
}
</script>

<style lang="scss">
.forgot-password-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
  padding: 100px 24px 36px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* ===== 找回密码卡片 ===== */
.forgot-password-page__card {
  width: 342px;
  padding: 24px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.forgot-password-page__header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.forgot-password-page__title {
  color: #0e0f0c;
  font-size: 32px;
  line-height: 36px;
  font-weight: 600;
  text-align: center;
}

/* ===== 表单 ===== */
.forgot-password-page__form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.forgot-password-page__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.forgot-password-page__label {
  color: #0e0f0c;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.forgot-password-page__input {
  height: 49px;
  padding: 14px 12px 12px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: inset 0 0 0 1px #c1cab5;
  color: #0e0f0c;
  font-size: 16px;
  line-height: 21px;
}

.forgot-password-page__input--error {
  box-shadow: inset 0 0 0 1px #e5484d;
}

.forgot-password-page__error-text {
  color: #e5484d;
  font-size: 12px;
  line-height: 16px;
}

.forgot-password-page__placeholder {
  color: #454745;
  font-size: 16px;
}

/* ===== 验证码行 ===== */
.forgot-password-page__code-row {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.forgot-password-page__code-input {
  flex: 1;
  height: 49px;
  padding: 14px 12px 12px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: inset 0 0 0 1px #c1cab5;
  color: #0e0f0c;
  font-size: 16px;
  line-height: 21px;
}

.forgot-password-page__code-input--error {
  box-shadow: inset 0 0 0 1px #e5484d;
}

.forgot-password-page__code-btn {
  width: 96px;
  height: 49px;
  padding: 13.5px 12px 14.5px;
  box-sizing: border-box;
  border-radius: 12px;
  box-shadow: inset 0 0 0 1px #c1cab5;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.forgot-password-page__code-btn-text {
  color: #0e0f0c;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

/* ===== 找回按钮 ===== */
.forgot-password-page__submit {
  height: 48px;
  padding: 12px 0;
  box-sizing: border-box;
  background: #9fe870;
  border-radius: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.forgot-password-page__submit-text {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

/* ===== 底部登录链接 ===== */
.forgot-password-page__footer {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.forgot-password-page__footer-text {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}
</style>
