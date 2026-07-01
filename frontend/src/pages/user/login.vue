<template>
  <view class="login-page">
    <!-- 顶部通知按钮（复用项目通知组件，非导航栏） -->
    <NoticeButton :has-notification="hasNotification" />

    <!-- 氛围背景装饰圆（设计稿 Background+Blur） -->
    <view class="login-page__ambient"></view>

    <!-- 主登录卡片 -->
    <view class="login-page__card">
      <text class="login-page__title">欢迎回来</text>

      <view class="login-page__form">
        <!-- 用户名或邮箱 -->
        <view class="login-page__field">
          <text class="login-page__label">用户名或邮箱</text>
          <input
            class="login-page__input"
            :class="{ 'login-page__input--error': errors.username }"
            v-model="form.username"
            placeholder="请输入用户名或邮箱"
            placeholder-class="login-page__placeholder"
            :placeholder-style="phStyle('username')"
            :maxlength="usernameLimit.max"
            @input="e => form.username = usernameLimit.handleInput(e)"
            @focus="handleFocus('username')"
            @blur="handleBlur('username')"
          />
          <text
            v-if="usernameLimit.hint.value"
            :class="['input-limit-hint', { 'input-limit-hint--near': usernameLimit.isNear.value, 'input-limit-hint--full': usernameLimit.isFull.value }]"
          >{{ usernameLimit.hint.value }}</text>
          <text v-if="errors.username" class="login-page__error-text">{{ errors.username }}</text>
        </view>

        <!-- 密码 -->
        <view class="login-page__field login-page__field--password">
          <text class="login-page__label">密码</text>
          <view class="login-page__password-row">
            <input
              class="login-page__input login-page__input--password"
              :class="{ 'login-page__input--error': errors.password }"
              v-model="form.password"
              :password="!showPassword"
              placeholder="请输入密码"
              placeholder-class="login-page__placeholder"
              :placeholder-style="phStyle('password')"
              :maxlength="passwordLimit.max"
              @input="e => form.password = passwordLimit.handleInput(e)"
              @focus="handleFocus('password')"
              @blur="handleBlur('password')"
            />
            <view class="login-page__eye" @click="togglePassword">
              <image class="login-page__eye-icon" :src="mimaIcon" mode="aspectFit" />
            </view>
          </view>
          <text
            v-if="passwordLimit.hint.value"
            :class="['input-limit-hint', { 'input-limit-hint--near': passwordLimit.isNear.value, 'input-limit-hint--full': passwordLimit.isFull.value }]"
          >{{ passwordLimit.hint.value }}</text>
          <text v-if="errors.password" class="login-page__error-text">{{ errors.password }}</text>
          <view class="login-page__forgot-row">
            <text class="login-page__forgot" @click="handleForgot">忘记密码？</text>
          </view>
        </view>

        <!-- 操作区 -->
        <view class="login-page__actions">
          <view class="login-page__remember" @click="toggleRemember">
            <view class="login-page__checkbox" :class="{ 'login-page__checkbox--checked': remember }">
              <view v-if="remember" class="login-page__checkmark"></view>
            </view>
            <text class="login-page__remember-text">查看并同意</text>
            <text class="login-page__agree-link" @click.stop="goPrivacy">《隐私政策》</text>
          </view>
          <view class="login-page__submit" @click="handleLogin">
            <text class="login-page__submit-text">登录</text>
          </view>
        </view>
      </view>

      <!-- 底部注册链接 -->
      <view class="login-page__footer" @click="goRegister">
        <text class="login-page__footer-text">还没有账号？ 立即注册</text>
      </view>
    </view>

    <!-- 微信一键登录区 -->
    <view class="login-page__wechat">
      <text class="login-page__wechat-title">微信一键登录</text>
      <view class="login-page__wechat-btn" @click="handleWechatLogin">
        <image class="login-page__wechat-icon" :src="wxIcon" mode="aspectFit" />
      </view>
      <!-- 微信登录隐私勾选（独立于账号密码登录的隐私勾选） -->
      <view class="login-page__remember login-page__remember--wechat" @click="toggleWechatAgree">
        <view class="login-page__checkbox" :class="{ 'login-page__checkbox--checked': wechatAgree }">
          <view v-if="wechatAgree" class="login-page__checkmark"></view>
        </view>
        <text class="login-page__remember-text">查看并同意</text>
        <text class="login-page__agree-link" @click.stop="goPrivacy">《隐私政策》</text>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 登录页（login.vue）
 * --------------------------------------------------------------------------
 * 功能：用户账号密码登录 + 微信一键登录入口
 *  - 账号密码登录：用户名/邮箱 + 密码，支持密码显隐切换、忘记密码、勾选隐私协议
 *  - 前端验证：用户名/密码非空校验（参照 register.vue）
 *  - 后端验证：调用 /login 接口验证用户名/邮箱 + 密码
 *  - 登录成功：写入 Pinia 用户状态 → 跳转 settings.vue
 *  - 微信一键登录：点击微信图标触发（当前为占位 toast，待接入 wx.login）
 *  - 底部提供注册入口，跳转 register.vue
 *  - 《隐私政策》文本可点击跳转 privacy.vue
 * 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
 */
import { reactive, ref } from 'vue'
import NoticeButton from '../../components/NoticeButton.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { useInputLimit } from '../../composables/useInputLimit'
import { loginUser, wechatLogin } from '../../api/modules/user'
import { useUserStore } from '../../store/modules/user'
import mimaIcon from '../../assets/images/mima_1.png'
import wxIcon from '../../assets/images/dl_wx.png'

// 设计稿顶栏铃铛为绿色无红点态
const hasNotification = false

const form = reactive({ username: '', password: '' })
const showPassword = ref(false)
const remember = ref(false)
// 微信登录独立隐私勾选（与账号密码登录的 remember 分离，互不影响）
const wechatAgree = ref(false)
const submitting = ref(false)
const userStore = useUserStore()

// 各字段错误信息（失焦时实时校验并写入，输入时清空）
const errors = reactive({
  username: '',
  password: ''
})

// 输入框 placeholder 聚焦交互：聚焦变浅灰 #c0c0c0，失焦恢复 placeholder-class 原始色
const { onFocus, onBlur, phStyle } = usePlaceholder()

// 输入框字符限制（与后端字段长度严格匹配）
const usernameLimit = useInputLimit(254)
const passwordLimit = useInputLimit(20)

// ===== 前端输入校验（参照 register.vue）=====
function validateUsername(v) {
  if (!v) return '请输入用户名或邮箱'
  return ''
}

function validatePassword(v) {
  if (!v) return '请输入密码'
  return ''
}

// 失焦时校验指定字段并写入 errors（实时反馈）
function validateField(field) {
  const map = {
    username: validateUsername,
    password: validatePassword
  }
  errors[field] = map[field](form[field])
}

// 失焦处理：先恢复 placeholder 原始色，再触发字段校验
function handleBlur(field) {
  onBlur()
  validateField(field)
}

// 聚焦处理：记录聚焦字段并清空该字段错误
function handleFocus(field) {
  onFocus(field)
  errors[field] = ''
}

function togglePassword() {
  showPassword.value = !showPassword.value
}

function toggleRemember() {
  remember.value = !remember.value
}

// 微信登录隐私勾选切换
function toggleWechatAgree() {
  wechatAgree.value = !wechatAgree.value
}

// ===== 登录提交：前端校验 → 后端验证 → 写入状态 → 跳转 =====
async function handleLogin() {
  if (submitting.value) return

  // 1. 前端字段校验（同步写入 errors 以展示视觉反馈）
  validateField('username')
  validateField('password')
  const firstErr = ['username', 'password'].find((f) => errors[f])
  if (firstErr) {
    uni.showToast({ title: errors[firstErr], icon: 'none' })
    return
  }

  // 2. 隐私协议勾选校验：未勾选时显示确认弹窗
  if (!remember.value) {
    uni.showModal({
      title: '提示',
      content: '请先查看并同意《隐私政策》',
      confirmText: '确认',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          remember.value = true
          handleLogin()
        }
      }
    })
    return
  }

  // 3. 调用后端登录接口
  submitting.value = true
  try {
    const res = await loginUser({
      username: form.username,
      password: form.password
    })
    // 4. 写入用户状态
    userStore.setUser(res.data)
    uni.showToast({ title: '登录成功', icon: 'success' })
    // 5. 登录成功后跳转 settings.vue
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/index/settings' })
    }, 1500)
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function handleForgot() {
  uni.navigateTo({
    url: '/pages/user/forgot-password',
    fail: () => {
      uni.showToast({ title: '页面跳转失败', icon: 'none' })
    }
  })
}

// ===== 微信一键登录：wx.login 获取 code → 后端换取 openid → 写入状态 → 跳转 =====
// 使用 callback 风格调用 uni.login + 超时安全网覆盖整个流程（含后端请求）
function handleWechatLogin() {
  if (submitting.value) return
  // 隐私协议勾选校验：未勾选时弹出确认对话框，用户点击"确认"后直接执行登录
  if (!wechatAgree.value) {
    uni.showModal({
      title: '提示',
      content: '请先查看并同意《隐私政策》',
      confirmText: '确认',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          wechatAgree.value = true
          handleWechatLogin()
        }
      }
    })
    return
  }
  submitting.value = true
  uni.showLoading({ title: '微信登录中...', mask: true })

  // 超时安全网：覆盖整个登录流程（uni.login + 后端请求），15秒后自动重置
  // 注意：不在 uni.login success 中清除，等后端请求完成后才清除
  const timeoutId = setTimeout(() => {
    submitting.value = false
    uni.hideLoading()
    setTimeout(() => {
      uni.showToast({ title: '登录超时，请检查网络或后端服务', icon: 'none' })
    }, 200)
  }, 15000)

  uni.login({
    success: async (loginRes) => {
      if (!loginRes || !loginRes.code) {
        clearTimeout(timeoutId)
        uni.hideLoading()
        setTimeout(() => {
          uni.showToast({ title: '获取微信登录凭证失败', icon: 'none' })
        }, 200)
        submitting.value = false
        return
      }
      try {
        const res = await wechatLogin(loginRes.code)
        clearTimeout(timeoutId)
        uni.hideLoading()
        userStore.setUser(res.data)
        uni.showToast({ title: '登录成功', icon: 'success' })
        setTimeout(() => {
          uni.redirectTo({ url: '/pages/index/settings' })
        }, 1500)
      } catch (e) {
        clearTimeout(timeoutId)
        uni.hideLoading()
        // 延迟 200ms 显示 toast，避免与 hideLoading 冲突
        setTimeout(() => {
          const msg = e.message || '微信登录失败'
          uni.showToast({ title: msg, icon: 'none' })
        }, 200)
      } finally {
        submitting.value = false
      }
    },
    fail: (err) => {
      clearTimeout(timeoutId)
      uni.hideLoading()
      setTimeout(() => {
        const msg = (err && err.errMsg) || ''
        if (msg.includes('cancel') || msg.includes('auth deny')) {
          uni.showToast({ title: '已取消微信登录', icon: 'none' })
        } else {
          uni.showToast({ title: '微信登录失败', icon: 'none' })
        }
      }, 200)
      submitting.value = false
    }
  })
}

function goRegister() {
  uni.navigateTo({
    url: '/pages/user/register',
    fail: () => {
      uni.showToast({ title: '页面跳转失败', icon: 'none' })
    }
  })
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
.login-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
  /* padding-top 105px：通知按钮 top约50px + 高40px = 底部约90px，留 15px 间隙避免与卡片重叠 */
  padding: 105px 24px 33.5px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* 氛围背景装饰圆（312x312 #e2f6d5，居中模糊） */
.login-page__ambient {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 312px;
  height: 312px;
  margin-top: -156px;
  margin-left: -156px;
  background: #e2f6d5;
  border-radius: 9999px;
  z-index: 0;
  pointer-events: none;
}

/* ===== 主登录卡片 ===== */
.login-page__card {
  position: relative;
  z-index: 1;
  width: 342px;
  margin-top: 32px;
  padding: 24px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.login-page__title {
  color: #0e0f0c;
  font-size: 32px;
  line-height: 36px;
  font-weight: 600;
  text-align: center;
}

/* ===== 表单 ===== */
.login-page__form {
  display: flex;
  flex-direction: column;
  padding-top: 8px;
}

.login-page__field {
  display: flex;
  flex-direction: column;
}

.login-page__field--password {
  padding-top: 16px;
}

.login-page__label {
  color: #41493a;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.login-page__input {
  margin-top: 4px;
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

/* 输入框错误态：红色边框（覆盖默认 #c1cab5） */
.login-page__input--error {
  box-shadow: inset 0 0 0 1px #e5484d;
}

/* 错误提示文字 */
.login-page__error-text {
  color: #e5484d;
  font-size: 12px;
  line-height: 16px;
  margin-top: 4px;
}

.login-page__placeholder {
  color: #454745;
  font-size: 16px;
}

/* 密码行：输入框 + 眼睛图标 */
.login-page__password-row {
  position: relative;
  margin-top: 4px;
}

.login-page__input--password {
  padding-right: 24px;
  margin-top: 0;
}

.login-page__eye {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  width: 18.33px;
  height: 12.5px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-page__eye-icon {
  width: 18.33px;
  height: 12.5px;
  display: block;
}

/* 忘记密码链接行 */
.login-page__forgot-row {
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
  padding-top: 4px;
  height: 20px;
}

.login-page__forgot {
  color: #454745;
  font-size: 12px;
  line-height: 16px;
}

/* ===== 操作区 ===== */
.login-page__actions {
  padding-top: 16px;
  display: flex;
  flex-direction: column;
}

.login-page__remember {
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 16px;
}

.login-page__checkbox {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #c1cab5;
  display: flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}

.login-page__checkbox--checked {
  background: #2f6c00;
  box-shadow: inset 0 0 0 1px #2f6c00;
}

/* 选中态对勾（CSS 绘制） */
.login-page__checkmark {
  width: 5px;
  height: 8px;
  border-right: 1.5px solid #ffffff;
  border-bottom: 1.5px solid #ffffff;
  transform: rotate(45deg) translate(-1px, -1px);
}

.login-page__remember-text {
  margin-left: 8px;
  color: #454745;
  font-size: 12px;
  line-height: 16px;
}

/* 《隐私政策》可点击链接：与同行文本样式一致，点击触发跳转 */
.login-page__agree-link {
  color: #454745;
  font-size: 12px;
  line-height: 16px;
}

.login-page__submit {
  margin-top: 12px;
  height: 48px;
  padding: 12px 0;
  box-sizing: border-box;
  background: #9fe870;
  border-radius: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-page__submit-text {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

/* ===== 底部注册链接 ===== */
.login-page__footer {
  display: flex;
  justify-content: center;
}

.login-page__footer-text {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}

/* ===== 微信一键登录区 ===== */
.login-page__wechat {
  position: relative;
  z-index: 1;
  width: 342px;
  margin-top: 16px;
  padding: 24px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.login-page__wechat-title {
  color: #41493a;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
  text-align: center;
}

.login-page__wechat-btn {
  width: 48px;
  height: 48px;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-page__wechat-icon {
  width: 48px;
  height: 48px;
  display: block;
}

/* 微信登录区隐私勾选：与账号密码登录的隐私勾选样式一致，居中显示 */
.login-page__remember--wechat {
  justify-content: center;
  margin-top: 4px;
}
</style>
