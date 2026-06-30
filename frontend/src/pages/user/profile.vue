<template>
  <view class="profile-page">
    <!-- 顶部通知按钮（复用项目通知组件，非导航栏） -->
    <NoticeButton :has-notification="false" />

    <view class="profile-page__main">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/notification 等页面保持一致） -->
      <PageHeader title="个人信息" :desc="`管理您的账户资料与安全设置，${'\n'}随时修改个人信息。`" />

      <!-- 分组 1：资料修改（修改头像、修改签名、修改密码、修改邮箱） -->
      <view class="profile-page__group">
        <!-- 修改头像 -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('avatar')">
          <text class="profile-page__group-text">修改头像</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改头像表单（动态显示） -->
        <view v-if="expandedSections.avatar" class="profile-page__form-section">
          <view class="profile-page__avatar-list">
            <view
              v-for="item in avatarOptions"
              :key="item.key"
              class="profile-page__avatar-option"
              :class="{ 'profile-page__avatar-option--selected': avatarForm.selected === item.key }"
              @click="avatarForm.selected = item.key"
            >
              <image class="profile-page__avatar-image" :src="item.src" mode="aspectFit" />
            </view>
          </view>
          <view class="profile-page__form-actions">
            <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('avatar')">
              <text class="profile-page__btn-text">取消</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleUpdateAvatar">
              <text class="profile-page__btn-text">提交</text>
            </view>
          </view>
        </view>

        <!-- 修改签名 -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('signature')">
          <text class="profile-page__group-text">修改签名</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改签名表单（动态显示） -->
        <view v-if="expandedSections.signature" class="profile-page__form-section">
          <input
            class="profile-page__input"
            :class="{ 'profile-page__input--error': signatureError }"
            v-model="signatureForm.value"
            placeholder="请输入签名（最多 255 个字符）"
            placeholder-class="profile-page__placeholder"
            maxlength="255"
          />
          <text v-if="signatureError" class="profile-page__error-text">{{ signatureError }}</text>
          <view class="profile-page__form-actions">
            <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('signature')">
              <text class="profile-page__btn-text">取消</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleUpdateSignature">
              <text class="profile-page__btn-text">提交</text>
            </view>
          </view>
        </view>

        <!-- 修改密码 -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('password')">
          <text class="profile-page__group-text">修改密码</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改密码表单（动态显示） -->
        <view v-if="expandedSections.password" class="profile-page__form-section">
          <view class="profile-page__form-field">
            <text class="profile-page__form-label">旧密码</text>
            <input
              class="profile-page__input"
              :class="{ 'profile-page__input--error': passwordErrors.oldPassword }"
              v-model="passwordForm.oldPassword"
              :password="true"
              placeholder="请输入旧密码"
              placeholder-class="profile-page__placeholder"
            />
            <text v-if="passwordErrors.oldPassword" class="profile-page__error-text">{{ passwordErrors.oldPassword }}</text>
          </view>
          <view class="profile-page__form-field">
            <text class="profile-page__form-label">新密码</text>
            <input
              class="profile-page__input"
              :class="{ 'profile-page__input--error': passwordErrors.newPassword }"
              v-model="passwordForm.newPassword"
              :password="true"
              placeholder="请设置强密码"
              placeholder-class="profile-page__placeholder"
            />
            <text v-if="passwordErrors.newPassword" class="profile-page__error-text">{{ passwordErrors.newPassword }}</text>
          </view>
          <view class="profile-page__form-field">
            <text class="profile-page__form-label">确认密码</text>
            <input
              class="profile-page__input"
              :class="{ 'profile-page__input--error': passwordErrors.confirmPassword }"
              v-model="passwordForm.confirmPassword"
              :password="true"
              placeholder="请再次输入密码"
              placeholder-class="profile-page__placeholder"
            />
            <text v-if="passwordErrors.confirmPassword" class="profile-page__error-text">{{ passwordErrors.confirmPassword }}</text>
          </view>
          <view class="profile-page__form-actions">
            <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('password')">
              <text class="profile-page__btn-text">取消</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleChangePassword">
              <text class="profile-page__btn-text">提交</text>
            </view>
          </view>
        </view>

        <!-- 修改邮箱 -->
        <view class="profile-page__group-item" @click="toggleSection('email')">
          <text class="profile-page__group-text">修改邮箱</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改邮箱表单（动态显示） -->
        <view v-if="expandedSections.email" class="profile-page__form-section">
          <!-- 步骤1：旧邮箱验证 -->
          <view v-if="emailStep === 1">
            <view class="profile-page__form-field">
              <text class="profile-page__form-label">旧邮箱验证码</text>
              <view class="profile-page__code-row">
                <input
                  class="profile-page__input profile-page__input--code"
                  :class="{ 'profile-page__input--error': emailErrors.oldCode }"
                  v-model="emailForm.oldCode"
                  placeholder="请输入验证码"
                  placeholder-class="profile-page__placeholder"
                />
                <view class="profile-page__code-btn" @click="handleGetOldEmailCode">
                  <text class="profile-page__code-btn-text">{{ emailOldCodeText }}</text>
                </view>
              </view>
              <text v-if="emailErrors.oldCode" class="profile-page__error-text">{{ emailErrors.oldCode }}</text>
            </view>
            <view class="profile-page__form-actions">
              <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('email')">
                <text class="profile-page__btn-text">取消</text>
              </view>
              <view class="profile-page__btn profile-page__btn--submit" @click="handleVerifyOldEmail">
                <text class="profile-page__btn-text">验证</text>
              </view>
            </view>
          </view>
          <!-- 步骤2：新邮箱验证 -->
          <view v-else>
            <view class="profile-page__form-field">
              <text class="profile-page__form-label">新邮箱地址</text>
              <input
                class="profile-page__input"
                :class="{ 'profile-page__input--error': emailErrors.newEmail }"
                v-model="emailForm.newEmail"
                placeholder="请输入新邮箱地址"
                placeholder-class="profile-page__placeholder"
              />
              <text v-if="emailErrors.newEmail" class="profile-page__error-text">{{ emailErrors.newEmail }}</text>
            </view>
            <view class="profile-page__form-field">
              <text class="profile-page__form-label">新邮箱验证码</text>
              <view class="profile-page__code-row">
                <input
                  class="profile-page__input profile-page__input--code"
                  :class="{ 'profile-page__input--error': emailErrors.newCode }"
                  v-model="emailForm.newCode"
                  placeholder="请输入验证码"
                  placeholder-class="profile-page__placeholder"
                />
                <view class="profile-page__code-btn" @click="handleGetNewEmailCode">
                  <text class="profile-page__code-btn-text">{{ emailNewCodeText }}</text>
                </view>
              </view>
              <text v-if="emailErrors.newCode" class="profile-page__error-text">{{ emailErrors.newCode }}</text>
            </view>
            <view class="profile-page__form-actions">
              <view class="profile-page__btn profile-page__btn--cancel" @click="handleResetEmailStep">
                <text class="profile-page__btn-text">返回</text>
              </view>
              <view class="profile-page__btn profile-page__btn--submit" @click="handleChangeEmail">
                <text class="profile-page__btn-text">修改</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 分组 2：退出登录 + 注销账号（危险操作，单独分组并使用红色文字提示） -->
      <view class="profile-page__group">
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="handleLogout">
          <text class="profile-page__group-text profile-page__group-text--danger">退出登录</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="profile-page__group-item" @click="handleDeletion">
          <text class="profile-page__group-text profile-page__group-text--danger">
            {{ isDeletionScheduled ? '取消注销' : '注销账号' }}
          </text>
          <view class="u-arrow-right"></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 个人信息页（profile.vue）
 * --------------------------------------------------------------------------
 * 功能：管理当前登录用户的账户资料与安全设置
 *  - 修改签名：点击后动态插入输入框和提交按钮，保存到数据库
 *  - 修改密码：旧密码验证（后端）+ 新密码复杂性验证（前端）
 *  - 修改邮箱：两步验证（旧邮箱验证码 → 新邮箱验证码 → 更新）
 *  - 退出登录：弹窗二次确认，清除状态并跳转 settings.vue
 * 视觉规范参照 settings.vue 分组卡片，保持应用内设置类页面一致性
 */
import { reactive, ref, computed } from 'vue'
import NoticeButton from '../../components/NoticeButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { useUserStore } from '../../store/modules/user'
import {
  updateSignature,
  changePassword,
  sendChangeEmailOldCode,
  sendChangeEmailNewCode,
  changeEmail,
  updateAvatar,
  scheduleDeletion,
  cancelDeletion
} from '../../api/modules/user'
import heiAvatar from '../../assets/images/touxiang/hei.png'
import hongAvatar from '../../assets/images/touxiang/hong.png'
import lanAvatar from '../../assets/images/touxiang/lan.png'

const userStore = useUserStore()

// 可选头像列表
const avatarOptions = [
  { key: 'hei', src: heiAvatar },
  { key: 'hong', src: hongAvatar },
  { key: 'lan', src: lanAvatar }
]

// 头像 key 与数据库存储值的映射（数据库存储 key，前端通过 key 查找 import 的图片）
const avatarKeyToDbValue = {
  hei: 'hei',
  hong: 'hong',
  lan: 'lan'
}

// 数据库值反查 key
const urlToAvatarKey = (url) => {
  if (!url) return 'hong'
  for (const [key, val] of Object.entries(avatarKeyToDbValue)) {
    if (url === val || url.includes(val)) return key
  }
  return 'hong'
}

// 是否处于注销冷静期
const isDeletionScheduled = computed(() => !!userStore.userInfo?.deletion_scheduled_at)

const expandedSections = reactive({
  avatar: false,
  signature: false,
  password: false,
  email: false
})

// ===== 修改头像 =====
const avatarForm = reactive({
  selected: urlToAvatarKey(userStore.userInfo?.avatar_url)
})

// ===== 修改签名 =====
const signatureForm = reactive({ value: '' })
const signatureError = ref('')

function toggleSection(section) {
  expandedSections[section] = !expandedSections[section]
  if (!expandedSections[section]) {
    resetSection(section)
  }
}

function resetSection(section) {
  if (section === 'avatar') {
    avatarForm.selected = urlToAvatarKey(userStore.userInfo?.avatar_url)
  } else if (section === 'signature') {
    signatureForm.value = ''
    signatureError.value = ''
  } else if (section === 'password') {
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    passwordErrors.oldPassword = ''
    passwordErrors.newPassword = ''
    passwordErrors.confirmPassword = ''
  } else if (section === 'email') {
    emailStep.value = 1
    emailForm.oldCode = ''
    emailForm.newEmail = ''
    emailForm.newCode = ''
    emailErrors.oldCode = ''
    emailErrors.newEmail = ''
    emailErrors.newCode = ''
    emailOldCodeCounting.value = false
    emailOldCodeText.value = '获取验证码'
    emailNewCodeCounting.value = false
    emailNewCodeText.value = '获取验证码'
  }
}

async function handleUpdateAvatar() {
  const avatarValue = avatarKeyToDbValue[avatarForm.selected]
  if (!avatarValue) {
    uni.showToast({ title: '请选择头像', icon: 'none' })
    return
  }
  try {
    await updateAvatar({
      user_id: userStore.userInfo.id,
      avatar_url: avatarValue
    })
    // 同步更新本地用户信息
    userStore.userInfo.avatar_url = avatarValue
    try {
      uni.setStorageSync('userInfo', userStore.userInfo)
    } catch (e) {
      console.warn('保存本地用户信息失败', e)
    }
    uni.showToast({ title: '头像更新成功', icon: 'success' })
    toggleSection('avatar')
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function handleUpdateSignature() {
  if (!signatureForm.value.trim()) {
    signatureError.value = '请输入签名'
    return
  }
  if (signatureForm.value.length > 255) {
    signatureError.value = '签名长度不能超过 255 个字符'
    return
  }
  try {
    await updateSignature({
      user_id: userStore.userInfo.id,
      signature: signatureForm.value.trim()
    })
    uni.showToast({ title: '签名更新成功', icon: 'success' })
    toggleSection('signature')
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

// ===== 修改密码 =====
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordErrors = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

function validatePassword(v) {
  if (!v) return '请输入密码'
  if (v.length < 8 || v.length > 20) return '密码长度需为 8-20 位'
  let categories = 0
  if (/[a-z]/.test(v)) categories++
  if (/[A-Z]/.test(v)) categories++
  if (/[0-9]/.test(v)) categories++
  if (/[^a-zA-Z0-9]/.test(v)) categories++
  if (categories < 3) return '密码需包含大小写字母、数字、特殊符号中的至少三种'
  return ''
}

async function handleChangePassword() {
  passwordErrors.oldPassword = passwordForm.oldPassword ? '' : '请输入旧密码'
  passwordErrors.newPassword = validatePassword(passwordForm.newPassword)
  passwordErrors.confirmPassword = passwordForm.confirmPassword ? '' : '请输入确认密码'

  if (passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordErrors.confirmPassword = '两次密码不一致'
  }

  const hasError = Object.values(passwordErrors).some((e) => e)
  if (hasError) {
    const firstErr = Object.values(passwordErrors).find((e) => e)
    uni.showToast({ title: firstErr, icon: 'none' })
    return
  }

  try {
    await changePassword({
      user_id: userStore.userInfo.id,
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword
    })
    uni.showToast({ title: '密码修改成功', icon: 'success' })
    toggleSection('password')
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

// ===== 修改邮箱 =====
const emailStep = ref(1)
const emailForm = reactive({
  oldCode: '',
  newEmail: '',
  newCode: ''
})

const emailErrors = reactive({
  oldCode: '',
  newEmail: '',
  newCode: ''
})

const emailOldCodeCounting = ref(false)
const emailOldCodeText = ref('获取验证码')
const emailNewCodeCounting = ref(false)
const emailNewCodeText = ref('获取验证码')

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

function startCountdown(targetText, targetCounting) {
  let sec = 60
  targetCounting.value = true
  targetText.value = `${sec}s`
  const timer = setInterval(() => {
    sec--
    if (sec <= 0) {
      clearInterval(timer)
      targetCounting.value = false
      targetText.value = '获取验证码'
    } else {
      targetText.value = `${sec}s`
    }
  }, 1000)
}

async function handleGetOldEmailCode() {
  if (emailOldCodeCounting.value) return
  try {
    await sendChangeEmailOldCode(userStore.userInfo.id)
    uni.showToast({ title: '验证码已发送', icon: 'none' })
    startCountdown(emailOldCodeText, emailOldCodeCounting)
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function handleVerifyOldEmail() {
  emailErrors.oldCode = validateCode(emailForm.oldCode)
  if (emailErrors.oldCode) {
    uni.showToast({ title: emailErrors.oldCode, icon: 'none' })
    return
  }
  emailStep.value = 2
}

function handleResetEmailStep() {
  emailStep.value = 1
  emailForm.newEmail = ''
  emailForm.newCode = ''
  emailErrors.newEmail = ''
  emailErrors.newCode = ''
  emailNewCodeCounting.value = false
  emailNewCodeText.value = '获取验证码'
}

async function handleGetNewEmailCode() {
  if (emailNewCodeCounting.value) return
  const emailErr = validateEmail(emailForm.newEmail)
  if (emailErr) {
    emailErrors.newEmail = emailErr
    uni.showToast({ title: emailErr, icon: 'none' })
    return
  }
  try {
    await sendChangeEmailNewCode(emailForm.newEmail)
    uni.showToast({ title: '验证码已发送', icon: 'none' })
    startCountdown(emailNewCodeText, emailNewCodeCounting)
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function handleChangeEmail() {
  emailErrors.newEmail = validateEmail(emailForm.newEmail)
  emailErrors.newCode = validateCode(emailForm.newCode)

  const hasError = emailErrors.newEmail || emailErrors.newCode
  if (hasError) {
    const firstErr = emailErrors.newEmail || emailErrors.newCode
    uni.showToast({ title: firstErr, icon: 'none' })
    return
  }

  try {
    await changeEmail({
      user_id: userStore.userInfo.id,
      old_code: emailForm.oldCode,
      new_email: emailForm.newEmail,
      new_code: emailForm.newCode
    })
    uni.showToast({ title: '邮箱修改成功', icon: 'success' })
    toggleSection('email')
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

// ===== 注销账号 =====
function handleDeletion() {
  if (isDeletionScheduled.value) {
    // 处于冷静期，执行取消注销
    uni.showModal({
      title: '提示',
      content: '确定要取消账号注销吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await cancelDeletion(userStore.userInfo.id)
            userStore.userInfo.deletion_scheduled_at = null
            try {
              uni.setStorageSync('userInfo', userStore.userInfo)
            } catch (e) {
              console.warn('保存本地用户信息失败', e)
            }
            uni.showToast({ title: '账号注销已取消', icon: 'success' })
          } catch (e) {
            uni.showToast({ title: e.message, icon: 'none' })
          }
        }
      }
    })
  } else {
    // 未处于冷静期，执行注销
    uni.showModal({
      title: '注销账号',
      content: '账号将在一天后自动删除，且无法恢复，请保留个人数据',
      confirmText: '确认注销',
      cancelText: '取消',
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await scheduleDeletion(userStore.userInfo.id)
            userStore.userInfo.deletion_scheduled_at = result.data.deletion_scheduled_at
            try {
              uni.setStorageSync('userInfo', userStore.userInfo)
            } catch (e) {
              console.warn('保存本地用户信息失败', e)
            }
            uni.showToast({ title: '已计划注销，24小时后自动删除', icon: 'none' })
          } catch (e) {
            uni.showToast({ title: e.message, icon: 'none' })
          }
        }
      }
    })
  }
}

// ===== 退出登录 =====
function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.clearUser()
        uni.showToast({ title: '已退出登录', icon: 'none' })
        setTimeout(() => {
          uni.redirectTo({ url: '/pages/index/settings' })
        }, 1500)
      }
    }
  })
}
</script>

<style lang="scss">
.profile-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.profile-page__main {
  padding: 100px 24px 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ===== 分组卡片 ===== */
.profile-page__group {
  border-radius: 24px;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.profile-page__group-item {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  box-sizing: border-box;
  height: 49px;
}

.profile-page__group-item--bordered {
  border-bottom: 1px solid #f3f3f4;
}

.profile-page__group-text {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

.profile-page__group-text--danger {
  color: #d03238;
}

/* ===== 动态表单区域 ===== */
.profile-page__form-section {
  padding: 12px 16px;
  box-sizing: border-box;
  background: #fafafa;
}

.profile-page__form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.profile-page__form-label {
  color: #41493a;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.profile-page__input {
  height: 44px;
  padding: 0 12px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #c1cab5;
  color: #0e0f0c;
  font-size: 16px;
  line-height: 21px;
}

.profile-page__input--error {
  border-color: #e5484d;
}

.profile-page__input--code {
  flex: 1;
}

.profile-page__placeholder {
  color: #454745;
  font-size: 14px;
}

.profile-page__error-text {
  color: #e5484d;
  font-size: 12px;
  line-height: 16px;
}

/* ===== 验证码行 ===== */
.profile-page__code-row {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.profile-page__code-btn {
  width: 96px;
  height: 44px;
  padding: 0 12px;
  box-sizing: border-box;
  border-radius: 8px;
  border: 1px solid #c1cab5;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.profile-page__code-btn-text {
  color: #0e0f0c;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

/* ===== 表单操作按钮 ===== */
.profile-page__form-actions {
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.profile-page__btn {
  height: 36px;
  padding: 0 20px;
  box-sizing: border-box;
  border-radius: 18px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.profile-page__btn--cancel {
  background: #f0f0f0;
}

.profile-page__btn--submit {
  background: #9fe870;
}

.profile-page__btn-text {
  color: #0e0f0c;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

/* ===== 头像选择列表 ===== */
.profile-page__avatar-list {
  display: flex;
  flex-direction: row;
  gap: 16px;
  padding: 8px 0;
}

.profile-page__avatar-option {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  border: 2px solid transparent;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f5f5;
}

.profile-page__avatar-option--selected {
  border-color: #9fe870;
  background: #e2f6d5;
}

.profile-page__avatar-image {
  width: 56px;
  height: 56px;
}
</style>
