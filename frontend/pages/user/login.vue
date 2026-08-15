<template>
  <view :data-theme="themeKey" class="login-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <!-- 微信一键登录区（仅微信小程序端展示，H5 端无微信一键登录能力） -->
    <!-- #ifdef MP-WEIXIN -->
    <view v-if="loginMode === 'wechat'" class="login-page__wechat">
      <text class="login-page__title">{{ $t('auth.wechatLogin') }}</text>
      <view class="login-page__wechat-btn guide-target-wechat-login" @click="handleWechatLogin">
        <image class="login-page__wechat-icon" :src="wxIcon" mode="aspectFit" />
      </view>
      <!-- 微信登录隐私勾选（独立于账号密码登录的隐私勾选） -->
      <view class="login-page__remember login-page__remember--wechat" @click="toggleWechatAgree">
        <view class="login-page__checkbox" :class="{ 'login-page__checkbox--checked': wechatAgree }">
          <view v-if="wechatAgree" class="login-page__checkmark"></view>
        </view>
        <text class="login-page__remember-text">{{ $t('auth.agreePrefix') }}</text>
        <text class="login-page__agree-link" @click.stop="goAgreement">{{ $t('auth.agreementName') }}</text>
        <text class="login-page__remember-text">{{ $t('auth.and') }}</text>
        <text class="login-page__agree-link" @click.stop="goPrivacy">{{ $t('auth.privacyName') }}</text>
      </view>
      <!-- 切换到账号密码登录引导（放大突出） -->
      <view class="login-page__switch" @click="switchMode('normal')">
        <text class="login-page__switch-text">{{ $t('auth.switchToPassword') }}</text>
      </view>
    </view>
    <!-- #endif -->

    <!-- App 端指纹一键登录区（仅 App 端，设备支持指纹且本地存在凭证时展示） -->
    <!-- #ifdef APP -->
    <view v-if="loginMode === 'fingerprint' && biometricVisible" class="login-page__wechat">
      <text class="login-page__title">{{ $t('auth.wechatLogin') }}</text>
      <view class="login-page__wechat-btn guide-target-fingerprint-login" @click="handleFingerprintLogin">
        <image class="login-page__wechat-icon" :src="fingerprint" mode="aspectFit" />
      </view>
      <!-- 指纹登录隐私勾选（与微信端对称） -->
      <view class="login-page__remember login-page__remember--wechat" @click="toggleFingerprintAgree">
        <view class="login-page__checkbox" :class="{ 'login-page__checkbox--checked': fingerprintAgree }">
          <view v-if="fingerprintAgree" class="login-page__checkmark"></view>
        </view>
        <text class="login-page__remember-text">{{ $t('auth.agreePrefix') }}</text>
        <text class="login-page__agree-link" @click.stop="goAgreement">{{ $t('auth.agreementName') }}</text>
        <text class="login-page__remember-text">{{ $t('auth.and') }}</text>
        <text class="login-page__agree-link" @click.stop="goPrivacy">{{ $t('auth.privacyName') }}</text>
      </view>
      <!-- 切换到账号密码登录引导 -->
      <view class="login-page__switch" @click="switchMode('normal')">
        <text class="login-page__switch-text">{{ $t('auth.switchToPassword') }}</text>
      </view>
    </view>
    <!-- #endif -->

    <!-- 主登录卡片（账号密码登录，H5 端默认展示；微信端切换或注册页跳转时展示） -->
    <view v-if="loginMode === 'normal'" class="login-page__card">
      <text class="login-page__title">{{ $t('auth.welcome') }}</text>

      <view class="login-page__form">
        <!-- 用户名或邮箱 -->
        <view class="login-page__field">
          <text class="login-page__label">{{ $t('auth.usernameOrEmail') }}</text>
          <input
            class="login-page__input"
            :class="{ 'login-page__input--error': errors.username }"
            v-model="form.username"
            :placeholder="$t('auth.usernameOrEmailPlaceholder')"
            placeholder-class="login-page__placeholder"
            :placeholder-style="phStyle('username')"
            :maxlength="usernameLimit.max"
            @input="e => form.username = usernameLimit.handleInput(e)"
            @focus="handleFocus('username')"
            @blur="handleBlur('username')"
          />
          <text v-if="errors.username" class="login-page__error-text">{{ errors.username }}</text>
          <text v-if="usernameLimit.limitReached" class="login-page__limit-text">{{ usernameLimit.limitHint }}</text>
        </view>

        <!-- 密码 -->
        <view class="login-page__field login-page__field--password">
          <text class="login-page__label">{{ $t('auth.password') }}</text>
          <view
            class="login-page__password-row"
            :class="{ 'login-page__password-row--error': errors.password }"
          >
            <input
              class="login-page__input login-page__input--password"
              v-model="form.password"
              :password="!showPassword"
              :key="'login-pwd-' + showPassword"
              :placeholder="$t('auth.passwordPlaceholder')"
              placeholder-class="login-page__placeholder"
              :placeholder-style="phStyle('password')"
              :maxlength="passwordLimit.max"
              @input="e => form.password = passwordLimit.handleInput(e)"
              @focus="handleFocus('password')"
              @blur="handleBlur('password')"
            />
            <view class="login-page__eye" @click="togglePassword">
              <PasswordEye :visible="showPassword" />
            </view>
          </view>
          <text v-if="errors.password" class="login-page__error-text">{{ errors.password }}</text>
          <text v-if="passwordLimit.limitReached" class="login-page__limit-text">{{ passwordLimit.limitHint }}</text>
          <view class="login-page__forgot-row">
            <text class="login-page__forgot" @click="handleForgot">{{ $t('auth.forgotPassword') }}</text>
          </view>
        </view>

        <!-- 操作区 -->
        <view class="login-page__actions">
          <view class="login-page__remember" @click="toggleRemember">
            <view class="login-page__checkbox" :class="{ 'login-page__checkbox--checked': remember }">
              <view v-if="remember" class="login-page__checkmark"></view>
            </view>
            <text class="login-page__remember-text">{{ $t('auth.agreePrefix') }}</text>
            <text class="login-page__agree-link" @click.stop="goAgreement">{{ $t('auth.agreementName') }}</text>
            <text class="login-page__remember-text">{{ $t('auth.and') }}</text>
            <text class="login-page__agree-link" @click.stop="goPrivacy">{{ $t('auth.privacyName') }}</text>
          </view>
          <view class="login-page__submit guide-target-login-submit" @click="handleLogin">
            <text class="login-page__submit-text">{{ $t('auth.login') }}</text>
          </view>
        </view>
      </view>

      <!-- 切换到微信一键登录引导（仅微信小程序端展示） -->
      <!-- #ifdef MP-WEIXIN -->
      <view class="login-page__switch" @click="switchMode('wechat')">
        <text class="login-page__switch-text">{{ $t('auth.switchToWechat') }}</text>
      </view>
      <!-- #endif -->
    </view>

    <!-- 底部注册链接（位于普通登录卡片外，但随普通登录卡片一起出现；仅"立即注册"可点击） -->
    <view v-if="loginMode === 'normal'" class="login-page__footer">
      <text class="login-page__footer-text">{{ $t('auth.noAccount') }}</text>
      <text class="login-page__footer-link guide-target-register-link" @click="goRegister">{{ $t('auth.registerNow') }}</text>
    </view>

    <!-- 新手引导遮罩（仅在引导激活时渲染） -->
    <BeginnerGuide />
  </view>
</template>

<script setup>
/**
 * 登录页（login.vue）
 * --------------------------------------------------------------------------
 * 功能：用户账号密码登录 + 微信一键登录入口
 *  - 登录方式切换：loginMode 'wechat'(默认) | 'normal'
 *    · 未登录默认进入：展示微信一键登录卡片，下方引导切换到账号密码登录
 *    · 注册页"去登录"或注册成功跳转（URL 带 ?mode=normal）：展示账号密码卡片，下方引导切换到微信登录
 *    · 两卡片互斥显示，点击引导文字调用 switchMode 切换
 *  - 账号密码登录：用户名/邮箱 + 密码，支持密码显隐切换、忘记密码、勾选隐私协议
 *  - 前端验证：用户名/密码非空校验（参照 register.vue）
 *  - 后端验证：调用 /login 接口验证用户名/邮箱 + 密码
 *  - 登录成功：写入 Pinia 用户状态 → 跳转 settings.vue
 *  - 微信一键登录：点击微信图标触发 wx.login → 后端换 openid → 写入状态 → 跳转
 *  - 底部提供注册入口，跳转 register.vue
 *  - 《隐私政策》文本可点击跳转 privacy.vue
 * 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
 */
import { reactive, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import BackButton from '../../components/BackButton.vue'
import BeginnerGuide from '../../components/BeginnerGuide.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { useInputLimit } from '../../composables/useInputLimit'
import { loginUser } from '../../api/modules/user'
import { useUserStore } from '../../store/modules/user'
import { useGuideStore } from '../../store/modules/guide'
import PasswordEye from '../../components/PasswordEye.vue'
import { useShare } from '../../composables/useShare'
import { useGuideTarget } from '../../composables/useGuideTarget'
import { biometricLogin } from '../../api/modules/user'
import { t } from '../../locale'
// 微信一键登录相关（仅微信小程序端使用）
// #ifdef MP-WEIXIN
import { wechatLogin } from '../../api/modules/user'
import wxIcon from '../../assets/images/dl_wx.png'
// #endif
// App 端生物识别（指纹）一键登录相关（仅 App 端使用）
// #ifdef APP
import { useBiometric } from '../../composables/useBiometric'
import { useThemeIcon } from '../../composables/useThemeIcon'
import fingerprintIcon from '../../assets/images/dl_fingerprint.png'

// 指纹图标按当前主题换色（green 用原图，其余主题用 static/theme-icons 产物）
const fingerprint = useThemeIcon('dl_fingerprint.png', fingerprintIcon)
// #endif

useShare({ title: t('share.login') })

const guideStore = useGuideStore()

// 新手引导：上报「立即注册」链接位置（非微信小程序端第 3 步目标）
useGuideTarget('register-link', '.guide-target-register-link')
// 新手引导：上报微信一键登录按钮位置（仅微信小程序端引导第 3 步目标）
// #ifdef MP-WEIXIN
useGuideTarget('wechat-login', '.guide-target-wechat-login')
// #endif

// 登录方式：微信小程序端默认 'wechat'(微信一键登录)，其他端默认 'normal'(账号密码登录)
// 注册页跳转时 URL 带 ?mode=normal，则初始展示账号密码卡片
let _defaultLoginMode = 'normal'
// #ifdef MP-WEIXIN
_defaultLoginMode = 'wechat'
// #endif
const loginMode = ref(_defaultLoginMode)

// App 端指纹一键登录卡片是否可显示（设备支持指纹 + 本地存在已登录凭证）
// 仅在 App 端使用，其他端恒为 false
const biometricVisible = ref(false)
// #ifdef APP
const biometric = useBiometric()
// #endif

onLoad((options = {}) => {
  if (options.mode === 'normal') {
    loginMode.value = 'normal'
  }
})

// 新手引导：页面显示时上报当前页面（引导激活时推进/回退步骤）
onShow(async () => {
  guideStore.onPageEnter('login')
  // App 端：页面显示时检测指纹能力，决定是否默认展示指纹一键登录卡片
  // 三者同时满足才默认指纹卡片：设备支持指纹 + 本地存在凭证 + 用户已开启指纹开关
  // 否则默认账号密码登录；用户可临时切到指纹（switchMode('fingerprint')）
  // #ifdef APP
  const ok = await biometric.isAvailable()
  const hasToken = !!biometric.getBiometricToken()
  const enabled = biometric.isEnabled()
  biometricVisible.value = ok && hasToken && enabled
  if (biometricVisible.value) {
    loginMode.value = 'fingerprint'
  } else {
    loginMode.value = 'normal'
  }
  // #endif
})

// 切换登录方式（互斥显示对应卡片）
function switchMode(mode) {
  loginMode.value = mode
}

const form = reactive({ username: '', password: '' })
const showPassword = ref(false)
const remember = ref(false)
const submitting = ref(false)
const userStore = useUserStore()
// 微信登录独立隐私勾选（仅微信小程序端使用，与账号密码登录的 remember 分离）
// #ifdef MP-WEIXIN
const wechatAgree = ref(false)
// #endif

// App 端指纹登录独立隐私勾选（仅 App 端使用）
// #ifdef APP
const fingerprintAgree = ref(false)
// #endif

// 各字段错误信息（失焦时实时校验并写入，输入时清空）
const errors = reactive({
  username: '',
  password: ''
})

// 输入框 placeholder 聚焦交互：聚焦变浅灰 var(--color-text-disabled)，失焦恢复 placeholder-class 原始色
const { onFocus, onBlur, phStyle } = usePlaceholder()

// 输入框字符限制（与后端字段长度严格匹配）
const usernameLimit = useInputLimit(254)
const passwordLimit = useInputLimit(20)

// ===== 前端输入校验（参照 register.vue）=====
function validateUsername(v) {
  if (!v) return t('validate.usernameRequired')
  return ''
}

function validatePassword(v) {
  if (!v) return t('validate.passwordRequired')
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

// 微信登录隐私勾选切换（仅微信小程序端使用）
// #ifdef MP-WEIXIN
function toggleWechatAgree() {
  wechatAgree.value = !wechatAgree.value
}
// #endif

// App 端指纹登录隐私勾选切换（仅 App 端使用）
// #ifdef APP
function toggleFingerprintAgree() {
  fingerprintAgree.value = !fingerprintAgree.value
}
// #endif

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
      title: t('common.tip'),
      content: t('auth.agreePrivacy'),
      confirmText: t('common.confirm'),
      cancelText: t('common.cancel'),
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
    // App 端传入 device_id，使后端下发生物识别（指纹）登录凭证
    // #ifdef APP
    const deviceId = biometric.getDeviceId()
    // #endif
    const res = await loginUser({
      username: form.username,
      password: form.password,
      // #ifdef APP
      device_id: deviceId
      // #endif
    })
    // 4. 写入用户状态
    userStore.setUser(res.data)
    // App 端：登录成功后若后端下发了生物识别凭证，则本地存储。
    // 凭证存储不依赖开关状态（isEnabled），避免「未开启→不下发→开启时取不到凭证」死锁；
    // 是否默认弹出指纹一键登录由 onShow 的 isEnabled() 判定。
    // #ifdef APP
    if (res.data && res.data.biometric_token) {
      biometric.storeBiometricToken(res.data.biometric_token)
    }
    // 引导开启指纹登录：设备支持指纹且本地未开启时，弹窗询问是否开启
    // 用户确认 → 置位开关，下次进登录页默认显示指纹一键登录
    // 用户取消 → 仅提示登录成功，凭证已存、可在 profile 页随时开启
    const _bioSupported = await biometric.isAvailable()
    if (_bioSupported && !biometric.isEnabled()) {
      uni.showModal({
        title: t('auth.enableBiometric'),
        content: t('auth.enableBiometricContent'),
        confirmText: t('common.confirm'),
        cancelText: t('common.cancel'),
        success: (r) => {
          if (r.confirm) {
            biometric.setEnabled(true)
            uni.showToast({ title: t('auth.enableBiometricOk'), icon: 'success' })
          } else {
            uni.showToast({ title: t('auth.loginSuccess'), icon: 'success' })
          }
          // 登录成功后推进新手引导（跳过注册页步骤，直接进入通知方式步骤）
          guideStore.advanceOnLoginSuccess()
          setTimeout(() => {
            uni.redirectTo({ url: '/pages/index/settings' })
          }, 1500)
        }
      })
      return
    }
    // #endif
    // 登录成功后推进新手引导（跳过注册页步骤，直接进入通知方式步骤）
    guideStore.advanceOnLoginSuccess()
    uni.showToast({ title: t('auth.loginSuccess'), icon: 'success' })
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
      uni.showToast({ title: t('common.navigateFailed'), icon: 'none' })
    }
  })
}

// ===== 微信一键登录（仅微信小程序端）：wx.login 获取 code → 后端换取 openid → 写入状态 → 跳转 =====
// 使用 callback 风格调用 uni.login + 超时安全网覆盖整个流程（含后端请求）
// #ifdef MP-WEIXIN
function handleWechatLogin() {
  if (submitting.value) return
  // 隐私协议勾选校验：未勾选时弹出确认对话框，用户点击"确认"后直接执行登录
  if (!wechatAgree.value) {
    uni.showModal({
      title: t('common.tip'),
      content: t('auth.agreePrivacy'),
      confirmText: t('common.confirm'),
      cancelText: t('common.cancel'),
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
  uni.showLoading({ title: t('auth.wechatLoggingIn'), mask: true })

  // 超时安全网：覆盖整个登录流程（uni.login + 后端请求），15秒后自动重置
  // 注意：不在 uni.login success 中清除，等后端请求完成后才清除
  const timeoutId = setTimeout(() => {
    submitting.value = false
    uni.hideLoading()
    setTimeout(() => {
      uni.showToast({ title: t('auth.wechatTimeout'), icon: 'none' })
    }, 200)
  }, 15000)

  uni.login({
    success: async (loginRes) => {
      if (!loginRes || !loginRes.code) {
        clearTimeout(timeoutId)
        uni.hideLoading()
        setTimeout(() => {
          uni.showToast({ title: t('auth.wechatCodeFail'), icon: 'none' })
        }, 200)
        submitting.value = false
        return
      }
      try {
        const res = await wechatLogin(loginRes.code)
        clearTimeout(timeoutId)
        uni.hideLoading()
        userStore.setUser(res.data)
        // 登录成功后推进新手引导（跳过注册页步骤，直接进入通知方式步骤）
        guideStore.advanceOnLoginSuccess()
        uni.showToast({ title: t('auth.loginSuccess'), icon: 'success' })
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
          uni.showToast({ title: t('auth.wechatCancel'), icon: 'none' })
        } else {
          uni.showToast({ title: t('auth.wechatFail'), icon: 'none' })
        }
      }, 200)
      submitting.value = false
    }
  })
}
// #endif

// ===== App 端指纹一键登录（仅 App 端）：指纹验证 → 后端 biometric-login → 写入状态 → 跳转 =====
// #ifdef APP
async function handleFingerprintLogin() {
  if (submitting.value) return
  // 隐私协议勾选校验（与微信登录对称）
  if (!fingerprintAgree.value) {
    uni.showModal({
      title: t('common.tip'),
      content: t('auth.agreePrivacy'),
      confirmText: t('common.confirm'),
      cancelText: t('common.cancel'),
      success: (res) => {
        if (res.confirm) {
          fingerprintAgree.value = true
          handleFingerprintLogin()
        }
      }
    })
    return
  }
  const token = biometric.getBiometricToken()
  if (!token) {
    // 本地凭证缺失（如清缓存），回退账号密码登录
    loginMode.value = 'normal'
    return
  }
  submitting.value = true
  uni.showLoading({ title: t('push.biometricAuthContent'), mask: true })
  try {
    // 1. 系统级指纹验证（未通过不会返回成功）
    await biometric.authenticate()
    // 2. 用本地凭证 + 设备标识调用后端指纹登录
    const res = await biometricLogin({
      token,
      device_id: biometric.getDeviceId()
    })
    uni.hideLoading()
    userStore.setUser(res.data)
    // 登录成功后推进新手引导（跳过注册页步骤，直接进入通知方式步骤）
    guideStore.advanceOnLoginSuccess()
    uni.showToast({ title: t('auth.loginSuccess'), icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/index/settings' })
    }, 1500)
  } catch (e) {
    uni.hideLoading()
    setTimeout(() => {
      const errMsg = (e && e.errMsg) || ''
      // 用户取消指纹验证（auth cancel）不提示错误，其余提示
      if (!errMsg.includes('cancel') && !errMsg.includes('authenticate fail')) {
        const msg = e.message || '指纹登录失败，请使用账号密码登录'
        uni.showToast({ title: msg, icon: 'none' })
      }
    }, 200)
  } finally {
    submitting.value = false
  }
}
// #endif

function goRegister() {
  uni.navigateTo({
    url: '/pages/user/register',
    fail: () => {
      uni.showToast({ title: t('common.navigateFailed'), icon: 'none' })
    }
  })
}

function goPrivacy() {
  uni.navigateTo({
    url: '/pages/user/privacy',
    fail: () => {
      uni.showToast({ title: t('common.navigateFailed'), icon: 'none' })
    }
  })
}

function goAgreement() {
  uni.navigateTo({
    url: '/pages/user/agreement',
    fail: () => {
      uni.showToast({ title: t('common.navigateFailed'), icon: 'none' })
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
.login-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
  /* padding-top 105px：通知按钮 top约50px + 高40px = 底部约90px，留 15px 间隙避免与卡片重叠 */
  padding: 210rpx 48rpx 67rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* ===== 主登录卡片（与微信登录卡片互斥显示，作首卡片需顶部留白避开 BackButton） ===== */
.login-page__card {
  position: relative;
  z-index: 1;
  width: 684rpx;
  margin-top: 64rpx;
  padding: 48rpx;
  box-sizing: border-box;
  background: var(--color-card-bg);
  border-radius: 48rpx;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 48rpx;
}

.login-page__title {
  color: var(--color-text-primary);
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
  text-align: center;
}

/* ===== 表单 ===== */
.login-page__form {
  display: flex;
  flex-direction: column;
  padding-top: 16rpx;
}

.login-page__field {
  display: flex;
  flex-direction: column;
}

.login-page__field--password {
  padding-top: 32rpx;
}

.login-page__label {
  color: var(--color-label);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.login-page__input {
  margin-top: 8rpx;
  height: 98rpx;
  padding: 28rpx 24rpx 24rpx;
  box-sizing: border-box;
  background: var(--color-card-bg);
  border-radius: 24rpx;
  box-shadow: inset 0 0 0 1px var(--color-border-input);
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 42rpx;
}

/* 输入框错误态：红色边框（覆盖默认 var(--color-border-input)） */
.login-page__input--error {
  box-shadow: inset 0 0 0 1px var(--color-form-error);
}

/* 错误提示文字 */
.login-page__error-text {
  color: var(--color-form-error);
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

/* 字符限制提示文字 */
.login-page__limit-text {
  color: var(--color-warning);
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

.login-page__placeholder {
  color: var(--color-text-secondary);
  font-size: 32rpx;
}

/* 密码行：统一边框容器，内含输入框与眼睛图标（用 border 而非 box-shadow，避免原生 input 白色背景覆盖 inset shadow） */
.login-page__password-row {
  position: relative;
  display: flex;
  align-items: stretch;
  margin-top: 8rpx;
  border: 1px solid var(--color-border-input);
  border-radius: 16rpx;
  background: var(--color-card-bg);
}

.login-page__password-row:focus-within {
  border-color: var(--color-text-secondary);
}

.login-page__password-row--error {
  border-color: var(--color-form-error);
}

.login-page__input--password {
  flex: 1;
  border: none;
  box-shadow: none;
  background-color: transparent;
  border-radius: 16rpx 0 0 16rpx;
  padding-right: 24rpx;
  margin-top: 0;
}

.login-page__eye {
  flex: none;
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 24rpx;
  border-radius: 0 16rpx 16rpx 0;
}

/* 忘记密码链接行 */
.login-page__forgot-row {
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
  padding-top: 8rpx;
  height: 40rpx;
}

.login-page__forgot {
  color: var(--color-text-secondary);
  font-size: 24rpx;
  line-height: 32rpx;
}

/* ===== 操作区 ===== */
.login-page__actions {
  padding-top: 32rpx;
  display: flex;
  flex-direction: column;
}

.login-page__remember {
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 32rpx;
}

.login-page__checkbox {
  width: 32rpx;
  height: 32rpx;
  border-radius: 8rpx;
  background: var(--color-card-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-input);
  display: flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}

.login-page__checkbox--checked {
  background: var(--color-brand);
  box-shadow: inset 0 0 0 1px var(--color-brand);
}

/* 选中态对勾（CSS 绘制） */
.login-page__checkmark {
  width: 10rpx;
  height: 16rpx;
  border-right: 1.5px solid var(--color-text-inverse);
  border-bottom: 1.5px solid var(--color-text-inverse);
  transform: rotate(45deg) translate(-1px, -1px);
}

.login-page__remember-text {
  margin-left: 16rpx;
  color: var(--color-text-secondary);
  font-size: 24rpx;
  line-height: 32rpx;
}

/* 《隐私政策》可点击链接：与同行文本样式一致，点击触发跳转 */
.login-page__agree-link {
  color: var(--color-text-secondary);
  font-size: 24rpx;
  line-height: 32rpx;
}

.login-page__submit {
  margin-top: 24rpx;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  background: var(--color-brand-bg);
  border-radius: 48rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-page__submit-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 底部注册链接（位于普通登录卡片外，但随普通登录卡片一起出现） ===== */
.login-page__footer {
  display: flex;
  justify-content: center;
  margin-top: 48rpx;
}

.login-page__footer-text {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

.login-page__footer-link {
  color: var(--color-brand);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 登录方式切换引导（放大突出，引导用户切换登录方式） ===== */
.login-page__switch {
  display: flex;
  justify-content: center;
}

.login-page__switch-text {
  color: var(--color-brand);
  font-size: 36rpx;
  line-height: 52rpx;
  font-weight: 600;
}

/* ===== 微信一键登录区（置于上方，首卡片顶部留白避开 BackButton） ===== */
.login-page__wechat {
  position: relative;
  z-index: 1;
  width: 684rpx;
  margin-top: 64rpx;
  padding: 48rpx;
  box-sizing: border-box;
  background: var(--color-card-bg);
  border-radius: 48rpx;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.login-page__wechat-btn {
  width: 96rpx;
  height: 96rpx;
  margin: 24rpx auto 0;
  border-radius: 9999px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-page__wechat-icon {
  width: 96rpx;
  height: 96rpx;
  display: block;
}

/* 微信登录区隐私勾选：与账号密码登录的隐私勾选样式一致，居中显示 */
.login-page__remember--wechat {
  justify-content: center;
  margin-top: 8rpx;
}

/* 微信卡片切换引导与上方隐私勾选拉开距离（叠加 gap 24rpx 共 48rpx，参考普通卡片间距） */
.login-page__wechat .login-page__switch {
  margin-top: 24rpx;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 * 规则：将本页面主要容器的宽度、卡片宽度、按钮尺寸锁定为设计稿原 px 值
 */
@media screen and (min-width: 768px) {
  /* 页面主容器 padding */
  .login-page {
    padding: 105px 24px 33.5px;
  }

  /* 主登录卡片 */
  .login-page__card {
    width: 342px;
    margin-top: 32px;
    padding: 24px;
    border-radius: 24px;
    gap: 24px;
  }

  .login-page__title {
    font-size: 32px;
    line-height: 36px;
  }

  /* 表单 */
  .login-page__form {
    padding-top: 8px;
  }

  .login-page__field--password {
    padding-top: 16px;
  }

  .login-page__label {
    font-size: 14px;
    line-height: 20px;
  }

  /* 输入框 */
  .login-page__input {
    margin-top: 4px;
    height: 49px;
    padding: 14px 12px 12px;
    border-radius: 12px;
    font-size: 16px;
    line-height: 21px;
  }

  .login-page__error-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }

  .login-page__limit-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }

  .login-page__placeholder {
    font-size: 16px;
  }

  /* 密码行 */
  .login-page__password-row {
    margin-top: 4px;
  }

  .login-page__input--password {
    padding-right: 12px;
  }

  .login-page__eye {
    padding: 0 12px;
  }

  /* 忘记密码行 */
  .login-page__forgot-row {
    padding-top: 4px;
    height: 20px;
  }

  .login-page__forgot {
    font-size: 12px;
    line-height: 16px;
  }

  /* 操作区 */
  .login-page__actions {
    padding-top: 16px;
  }

  .login-page__remember {
    height: 16px;
  }

  /* 复选框 */
  .login-page__checkbox {
    width: 16px;
    height: 16px;
    border-radius: 4px;
  }

  /* 对勾 */
  .login-page__checkmark {
    width: 5px;
    height: 8px;
  }

  .login-page__remember-text {
    margin-left: 8px;
    font-size: 12px;
    line-height: 16px;
  }

  .login-page__agree-link {
    font-size: 12px;
    line-height: 16px;
  }

  /* 提交按钮 */
  .login-page__submit {
    margin-top: 12px;
    height: 48px;
    padding: 12px 0;
    border-radius: 24px;
  }

  .login-page__submit-text {
    font-size: 16px;
    line-height: 24px;
  }

  /* 底部注册链接 */
  .login-page__footer {
    margin-top: 24px;
  }

  .login-page__footer-text {
    font-size: 16px;
    line-height: 24px;
  }

  .login-page__footer-link {
    font-size: 16px;
    line-height: 24px;
  }

  /* 登录方式切换引导 */
  .login-page__switch-text {
    font-size: 18px;
    line-height: 26px;
  }

  /* 微信登录区 */
  .login-page__wechat {
    width: 342px;
    margin-top: 32px;
    padding: 24px;
    border-radius: 24px;
    gap: 12px;
  }

  .login-page__wechat-btn {
    width: 48px;
    height: 48px;
    margin-top: 12px;
    border-radius: 9999px;
    overflow: hidden;
  }

  .login-page__wechat-icon {
    width: 48px;
    height: 48px;
  }

  .login-page__remember--wechat {
    margin-top: 4px;
  }

  .login-page__wechat .login-page__switch {
    margin-top: 12px;
  }
}
</style>
