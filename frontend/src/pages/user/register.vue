<template>
  <view class="register-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="register-page__canvas">
      <!-- 白色卡片容器 -->
      <view class="register-page__card">
        <!-- 标题区 -->
        <view class="register-page__header">
          <text class="register-page__title">注册账号</text>
          <text class="register-page__subtitle">加入我们，开始您的健康之旅。</text>
        </view>

        <!-- 注册表单 -->
        <view class="register-page__form">
          <!-- 用户名 -->
          <view class="register-page__field">
            <text class="register-page__label">用户名</text>
            <input
              class="register-page__input"
              :class="{ 'register-page__input--error': errors.username }"
              v-model="form.username"
              placeholder="请输入用户名"
              placeholder-class="register-page__placeholder"
              :placeholder-style="phStyle('username')"
              :maxlength="usernameLimit.max"
              @input="e => form.username = usernameLimit.handleInput(e)"
              @focus="handleFocus('username')"
              @blur="handleBlur('username')"
            />
            <text v-if="errors.username" class="register-page__error-text">{{ errors.username }}</text>
            <text v-if="usernameLimit.limitReached" class="register-page__limit-text">{{ usernameLimit.limitHint }}</text>
          </view>

          <!-- 密码 -->
          <view class="register-page__field">
            <text class="register-page__label">密码</text>
            <input
              class="register-page__input"
              :class="{ 'register-page__input--error': errors.password }"
              v-model="form.password"
              :password="true"
              placeholder="请设置强密码"
              placeholder-class="register-page__placeholder"
              :placeholder-style="phStyle('password')"
              :maxlength="passwordLimit.max"
              @input="e => form.password = passwordLimit.handleInput(e)"
              @focus="handleFocus('password')"
              @blur="handleBlur('password')"
            />
            <text v-if="errors.password" class="register-page__error-text">{{ errors.password }}</text>
            <text v-if="passwordLimit.limitReached" class="register-page__limit-text">{{ passwordLimit.limitHint }}</text>
          </view>

          <!-- 确认密码 -->
          <view class="register-page__field">
            <text class="register-page__label">确认密码</text>
            <input
              class="register-page__input"
              :class="{ 'register-page__input--error': errors.confirmPassword }"
              v-model="form.confirmPassword"
              :password="true"
              placeholder="请再次输入密码"
              placeholder-class="register-page__placeholder"
              :placeholder-style="phStyle('confirmPassword')"
              :maxlength="confirmPwdLimit.max"
              @input="e => form.confirmPassword = confirmPwdLimit.handleInput(e)"
              @focus="handleFocus('confirmPassword')"
              @blur="handleBlur('confirmPassword')"
            />
            <text v-if="errors.confirmPassword" class="register-page__error-text">{{ errors.confirmPassword }}</text>
            <text v-if="confirmPwdLimit.limitReached" class="register-page__limit-text">{{ confirmPwdLimit.limitHint }}</text>
          </view>

          <!-- 电子邮箱 -->
          <view class="register-page__field">
            <text class="register-page__label">电子邮箱</text>
            <input
              class="register-page__input"
              :class="{ 'register-page__input--error': errors.email }"
              v-model="form.email"
              placeholder="请输入邮箱地址"
              placeholder-class="register-page__placeholder"
              :placeholder-style="phStyle('email')"
              :maxlength="emailLimit.max"
              @input="e => form.email = emailLimit.handleInput(e)"
              @focus="handleFocus('email')"
              @blur="handleBlur('email')"
            />
            <text v-if="errors.email" class="register-page__error-text">{{ errors.email }}</text>
            <text v-if="emailLimit.limitReached" class="register-page__limit-text">{{ emailLimit.limitHint }}</text>
          </view>

          <!-- 验证码 -->
          <view class="register-page__field">
            <text class="register-page__label">验证码</text>
            <view class="register-page__code-row">
              <input
                class="register-page__code-input"
                :class="{ 'register-page__code-input--error': errors.code }"
                v-model="form.code"
                placeholder="请输入验证码"
                placeholder-class="register-page__placeholder"
                :placeholder-style="phStyle('code')"
                :maxlength="codeLimit.max"
                @input="e => form.code = codeLimit.handleInput(e)"
                @focus="handleFocus('code')"
                @blur="handleBlur('code')"
              />
              <view class="register-page__code-btn" @click="handleGetCode">
                <text class="register-page__code-btn-text">{{ codeText }}</text>
              </view>
            </view>
            <text v-if="errors.code" class="register-page__error-text">{{ errors.code }}</text>
            <text v-if="codeLimit.limitReached" class="register-page__limit-text">{{ codeLimit.limitHint }}</text>
          </view>

          <!-- 协议勾选 -->
          <view class="register-page__agree" @click="toggleAgree">
            <view class="register-page__checkbox" :class="{ 'register-page__checkbox--checked': agreed }">
              <view v-if="agreed" class="register-page__checkmark"></view>
            </view>
            <text class="register-page__agree-text">查看并同意</text>
            <text class="register-page__agree-link" @click.stop="goPrivacy">《隐私政策》</text>
          </view>

          <!-- 注册按钮 -->
          <view class="register-page__submit" @click="handleRegister">
            <text class="register-page__submit-text">注册</text>
          </view>
        </view>
      </view>

      <!-- 底部登录链接 -->
      <view class="register-page__footer" @click="goLogin">
        <text class="register-page__footer-text">已有账号？去登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 注册页（register.vue）
 * --------------------------------------------------------------------------
 * 功能：新用户账号注册（前端 + 后端双重校验）
 *  - 表单字段：用户名、密码、确认密码、电子邮箱、验证码
 *  - 输入校验（前端）：
 *      · 用户名：仅中文/英文/数字，长度 2-15
 *      · 密码：8-20 位，大小写字母/数字/特殊符号至少三种
 *      · 邮箱：标准邮箱格式
 *      · 验证码：6 位数字，需通过后端发送并匹配（后端二次校验）
 *  - 验证码：点击「获取验证码」调用后端发送邮件，60 秒倒计时防重复
 *  - 隐私政策同意机制：
 *      · 已勾选 → 直接提交
 *      · 未勾选 → 弹出确认弹窗（确认/取消）；确认则自动勾选并提交，取消则关闭弹窗
 *  - 注册按钮：前端校验通过后调用后端 /register 接口入库
 *  - 底部提供登录入口，跳转 login.vue
 * 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
 */
import { reactive, ref } from 'vue'
import BackButton from '../../components/BackButton.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { useInputLimit } from '../../composables/useInputLimit'
import { sendRegisterCode, registerUser } from '../../api/modules/user'
import { useShare } from '../../composables/useShare'

useShare({ title: '注册账号' })

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  code: ''
})

// 各字段错误信息（失焦时实时校验并写入，输入时清空）
const errors = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  code: ''
})

const agreed = ref(false)
const codeText = ref('获取验证码')
const counting = ref(false)
const submitting = ref(false)

// 输入框 placeholder 聚焦交互：聚焦变浅灰 #c0c0c0，失焦恢复 placeholder-class 原始色
const { onFocus, onBlur, phStyle } = usePlaceholder()

// 输入框字符限制（与后端字段长度严格匹配）
const usernameLimit = useInputLimit(15, /^[\u4e00-\u9fa5a-zA-Z0-9]$/)
const passwordLimit = useInputLimit(20)
const confirmPwdLimit = useInputLimit(20)
const emailLimit = useInputLimit(254)
const codeLimit = useInputLimit(6, /^\d$/)

// ===== 前端输入校验（与后端规则保持一致）=====
function validateUsername(v) {
  if (!v) return '请输入用户名'
  if (v.length < 2 || v.length > 15) return '用户名长度需为 2-15 个字符'
  if (!/^[\u4e00-\u9fa5a-zA-Z0-9]+$/.test(v)) return '用户名仅允许中文、英文及数字字符'
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
  if (v !== form.password) return '两次密码不一致'
  return ''
}

function validateEmail(v) {
  if (!v) return '请输入邮箱地址'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return '邮箱格式不正确'
  return ''
}

// 失焦时校验指定字段并写入 errors（实时反馈）
function validateField(field) {
  const map = {
    username: validateUsername,
    password: validatePassword,
    confirmPassword: validateConfirmPassword,
    email: validateEmail,
    code: (v) => (!v ? '请输入验证码' : '')
  }
  errors[field] = map[field](form[field])
}

// 失焦处理：先恢复 placeholder 原始色，再触发字段校验
function handleBlur(field) {
  onBlur()
  // 密码修改后需联动重新校验确认密码
  if (field === 'password' && form.confirmPassword) {
    validateField('confirmPassword')
  }
  validateField(field)
}

// 聚焦处理：记录聚焦字段并清空该字段错误
function handleFocus(field) {
  onFocus(field)
  errors[field] = ''
}

function toggleAgree() {
  agreed.value = !agreed.value
}

// ===== 获取验证码：前端校验邮箱 → 调用后端发送邮件 → 倒计时 =====
async function handleGetCode() {
  if (counting.value) return
  const emailErr = validateEmail(form.email)
  if (emailErr) {
    errors.email = emailErr
    uni.showToast({ title: emailErr, icon: 'none' })
    return
  }
  await requestCode()
}

// 网络错误时提供重试机制：modal 提示原因，确认则重试
async function requestCode() {
  try {
    await sendRegisterCode(form.email)
    uni.showToast({ title: '验证码已发送', icon: 'none' })
    startCountdown()
  } catch (e) {
    if (e.isNetworkError) {
      // 网络错误：弹窗提示原因并提供重试入口
      uni.showModal({
        title: '发送失败',
        content: e.message,
        confirmText: '重试',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) requestCode()
        }
      })
    } else {
      // 业务错误（如邮箱已注册）：toast 提示
      uni.showToast({ title: e.message, icon: 'none' })
    }
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

// ===== 注册提交：前端校验 → 隐私政策确认 → 调用后端入库 =====
function handleRegister() {
  if (submitting.value) return

  // 1. 前端字段校验（同步写入 errors 以展示视觉反馈）
  validateField('username')
  validateField('password')
  validateField('confirmPassword')
  validateField('email')
  validateField('code')
  const firstErr = ['username', 'password', 'confirmPassword', 'email', 'code'].find(
    (f) => errors[f]
  )
  if (firstErr) {
    uni.showToast({ title: errors[firstErr], icon: 'none' })
    return
  }

  // 2. 隐私政策同意机制
  if (!agreed.value) {
    uni.showModal({
      title: '提示',
      content: '请先查看并同意《隐私政策》',
      confirmText: '确认',
      cancelText: '取消',
      success: (res) => {
        // 用户点击「确认」：自动勾选并提交表单
        if (res.confirm) {
          agreed.value = true
          submitForm()
        }
        // 用户点击「取消」：关闭弹窗，不提交
      }
    })
    return
  }

  // 3. 已勾选，直接提交
  submitForm()
}

async function submitForm() {
  submitting.value = true
  try {
    await registerUser({
      username: form.username,
      password: form.password,
      email: form.email,
      code: form.code
    })
    uni.showToast({ title: '注册成功', icon: 'success' })
    // 注册成功后跳转登录页
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

function goPrivacy() {
  uni.navigateTo({
    url: '/pages/user/privacy',
    fail: () => {
      uni.showToast({ title: '页面跳转失败', icon: 'none' })
    }
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
.register-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.register-page__canvas {
  /* padding-top 105px：通知按钮 top约50px + 高40px = 底部约90px，留 15px 间隙避免与卡片重叠 */
  padding: 210rpx 48rpx 72rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

/* ===== 白色卡片容器 ===== */
.register-page__card {
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

/* ===== 标题区 ===== */
.register-page__header {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  align-items: center;
}

.register-page__title {
  color: #0e0f0c;
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
  text-align: center;
}

.register-page__subtitle {
  color: #454745;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  text-align: center;
}

/* ===== 注册表单 ===== */
.register-page__form {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.register-page__field {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.register-page__label {
  color: #0e0f0c;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.register-page__input {
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

.register-page__placeholder {
  color: #454745;
  font-size: 32rpx;
}

/* 输入框错误态：红色边框（覆盖默认 #c1cab5） */
.register-page__input--error {
  box-shadow: inset 0 0 0 1px #e5484d;
}

/* 错误提示文字 */
.register-page__error-text {
  color: #e5484d;
  font-size: 24rpx;
  line-height: 32rpx;
}

/* 字符限制提示文字 */
.register-page__limit-text {
  color: #d97706;
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

/* ===== 验证码行 ===== */
.register-page__code-row {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
}

.register-page__code-input {
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

/* 验证码输入框错误态：红色边框 */
.register-page__code-input--error {
  box-shadow: inset 0 0 0 1px #e5484d;
}

.register-page__code-btn {
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

.register-page__code-btn-text {
  color: #0e0f0c;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* ===== 协议勾选 ===== */
.register-page__agree {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16rpx;
  padding-bottom: 16rpx;
}

.register-page__checkbox {
  width: 32rpx;
  height: 32rpx;
  border-radius: 8rpx;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #c1cab5;
  display: flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
  flex-shrink: 0;
}

.register-page__checkbox--checked {
  background: #2f6c00;
  box-shadow: inset 0 0 0 1px #2f6c00;
}

/* 选中态对勾（CSS 绘制） */
.register-page__checkmark {
  width: 10rpx;
  height: 16rpx;
  border-right: 1.5px solid #ffffff;
  border-bottom: 1.5px solid #ffffff;
  transform: rotate(45deg) translate(-1px, -1px);
}

.register-page__agree-text {
  color: #454745;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

/* 《隐私政策》可点击链接：与同行文本样式一致，点击触发跳转 */
.register-page__agree-link {
  color: #454745;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
}

/* ===== 注册按钮 ===== */
.register-page__submit {
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  background: #9fe870;
  border-radius: 48rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.register-page__submit-text {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 底部登录链接 ===== */
.register-page__footer {
  margin-top: 48rpx;
  display: flex;
  justify-content: center;
}

.register-page__footer-text {
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
  /* 画布 padding */
  .register-page__canvas {
    padding: 105px 24px 36px;
  }

  /* 白色卡片容器 */
  .register-page__card {
    width: 342px;
    padding: 24px;
    border-radius: 24px;
    gap: 24px;
  }

  /* 标题区 */
  .register-page__header {
    gap: 8px;
  }

  .register-page__title {
    font-size: 32px;
    line-height: 36px;
  }

  .register-page__subtitle {
    font-size: 16px;
    line-height: 24px;
  }

  /* 表单 */
  .register-page__form {
    gap: 16px;
  }

  .register-page__field {
    gap: 8px;
  }

  .register-page__label {
    font-size: 14px;
    line-height: 20px;
  }

  /* 输入框 */
  .register-page__input {
    height: 49px;
    padding: 14px 12px 12px;
    border-radius: 12px;
    font-size: 16px;
    line-height: 21px;
  }

  .register-page__placeholder {
    font-size: 16px;
  }

  .register-page__error-text {
    font-size: 12px;
    line-height: 16px;
  }

  .register-page__limit-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }

  /* 验证码行 */
  .register-page__code-row {
    gap: 8px;
  }

  .register-page__code-input {
    height: 49px;
    padding: 14px 12px 12px;
    border-radius: 12px;
    font-size: 16px;
    line-height: 21px;
  }

  .register-page__code-btn {
    width: 96px;
    height: 49px;
    padding: 13.5px 12px 14.5px;
    border-radius: 12px;
  }

  .register-page__code-btn-text {
    font-size: 14px;
    line-height: 20px;
  }

  /* 协议勾选 */
  .register-page__agree {
    gap: 8px;
    padding-bottom: 8px;
  }

  .register-page__checkbox {
    width: 16px;
    height: 16px;
    border-radius: 4px;
  }

  /* 对勾 */
  .register-page__checkmark {
    width: 5px;
    height: 8px;
  }

  .register-page__agree-text {
    font-size: 12px;
    line-height: 16px;
  }

  .register-page__agree-link {
    font-size: 12px;
    line-height: 16px;
  }

  /* 注册按钮 */
  .register-page__submit {
    height: 48px;
    padding: 12px 0;
    border-radius: 24px;
  }

  .register-page__submit-text {
    font-size: 16px;
    line-height: 24px;
  }

  /* 底部登录链接 */
  .register-page__footer {
    margin-top: 24px;
  }

  .register-page__footer-text {
    font-size: 16px;
    line-height: 24px;
  }
}
</style>
