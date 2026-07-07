<template>
  <view class="profile-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="profile-page__main">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/notification 等页面保持一致） -->
      <PageHeader title="个人信息" desc="管理您的账户资料与安全设置，随时修改个人信息。" />

      <!-- 分组 1：资料修改（修改用户名、修改头像、修改签名、修改密码、修改邮箱） -->
      <view class="profile-page__group" :class="{ 'profile-page__group--disabled': isDeletionScheduled }">
        <!-- 修改用户名 -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('username')">
          <text class="profile-page__group-text">修改用户名</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改用户名表单（动态显示） -->
        <view v-if="expandedSections.username" class="profile-page__form-section">
          <view class="profile-page__form-field">
            <text class="profile-page__form-label">新用户名</text>
            <input
              class="profile-page__input"
              :class="{ 'profile-page__input--error': usernameError }"
              v-model="usernameForm.value"
              placeholder="请输入新用户名（2-15 个字符）"
              placeholder-class="profile-page__placeholder"
              :maxlength="usernameLimit.max"
              @input="e => usernameForm.value = usernameLimit.handleInput(e)"
              @blur="usernameError = validateUsername(usernameForm.value)"
            />
            <text v-if="usernameError" class="profile-page__error-text">{{ usernameError }}</text>
            <text v-if="usernameLimit.limitReached" class="profile-page__limit-text">{{ usernameLimit.limitHint }}</text>
          </view>
          <view class="profile-page__form-actions">
            <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('username')">
              <text class="profile-page__btn-text">取消</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleUpdateUsername">
              <text class="profile-page__btn-text">提交</text>
            </view>
          </view>
        </view>

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
            placeholder="请输入签名（最多 70 个字符）"
            placeholder-class="profile-page__placeholder"
            :maxlength="signatureLimit.max"
            @input="e => signatureForm.value = signatureLimit.handleInput(e)"
          />
          <text v-if="signatureError" class="profile-page__error-text">{{ signatureError }}</text>
          <text v-if="signatureLimit.limitReached" class="profile-page__limit-text">{{ signatureLimit.limitHint }}</text>
          <view class="profile-page__form-actions">
            <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('signature')">
              <text class="profile-page__btn-text">取消</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleUpdateSignature">
              <text class="profile-page__btn-text">提交</text>
            </view>
          </view>
        </view>

        <!-- 修改密码 / 设置密码（无密码用户显示"设置密码"） -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('password')">
          <text class="profile-page__group-text">{{ hasPassword ? '修改密码' : '设置密码' }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改/设置密码表单（动态显示） -->
        <view v-if="expandedSections.password" class="profile-page__form-section">
          <!-- 旧密码（仅已设置密码的用户需要验证） -->
          <view v-if="hasPassword" class="profile-page__form-field">
            <text class="profile-page__form-label">旧密码</text>
            <input
              class="profile-page__input"
              :class="{ 'profile-page__input--error': passwordErrors.oldPassword }"
              v-model="passwordForm.oldPassword"
              :password="true"
              placeholder="请输入旧密码"
              placeholder-class="profile-page__placeholder"
              :maxlength="oldPwdLimit.max"
              @input="e => passwordForm.oldPassword = oldPwdLimit.handleInput(e)"
              @blur="passwordErrors.oldPassword = passwordForm.oldPassword ? '' : '请输入旧密码'"
            />
            <text v-if="passwordErrors.oldPassword" class="profile-page__error-text">{{ passwordErrors.oldPassword }}</text>
            <text v-if="oldPwdLimit.limitReached" class="profile-page__limit-text">{{ oldPwdLimit.limitHint }}</text>
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
              :maxlength="newPwdLimit.max"
              @input="e => passwordForm.newPassword = newPwdLimit.handleInput(e)"
              @blur="passwordErrors.newPassword = validatePassword(passwordForm.newPassword)"
            />
            <text v-if="passwordErrors.newPassword" class="profile-page__error-text">{{ passwordErrors.newPassword }}</text>
            <text v-if="newPwdLimit.limitReached" class="profile-page__limit-text">{{ newPwdLimit.limitHint }}</text>
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
              :maxlength="confirmPwdLimit.max"
              @input="e => passwordForm.confirmPassword = confirmPwdLimit.handleInput(e)"
              @blur="passwordErrors.confirmPassword = passwordForm.confirmPassword ? (passwordForm.confirmPassword !== passwordForm.newPassword ? '两次密码不一致' : '') : '请再次输入密码'"
            />
            <text v-if="passwordErrors.confirmPassword" class="profile-page__error-text">{{ passwordErrors.confirmPassword }}</text>
            <text v-if="confirmPwdLimit.limitReached" class="profile-page__limit-text">{{ confirmPwdLimit.limitHint }}</text>
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

        <!-- 修改邮箱 / 绑定邮箱（无邮箱用户显示"绑定邮箱"） -->
        <view class="profile-page__group-item" @click="toggleSection('email')">
          <text class="profile-page__group-text">{{ hasEmail ? '修改邮箱' : '绑定邮箱' }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改/绑定邮箱表单（动态显示） -->
        <view v-if="expandedSections.email" class="profile-page__form-section">
          <!-- 步骤1：旧邮箱验证（仅已有邮箱的用户需要） -->
          <view v-if="hasEmail && emailStep === 1">
            <view class="profile-page__form-field">
              <text class="profile-page__form-label">旧邮箱验证码</text>
              <view class="profile-page__code-row">
                <input
                class="profile-page__input profile-page__input--code"
                :class="{ 'profile-page__input--error': emailErrors.oldCode }"
                v-model="emailForm.oldCode"
                placeholder="请输入验证码"
                placeholder-class="profile-page__placeholder"
                :maxlength="oldCodeLimit.max"
                @input="e => emailForm.oldCode = oldCodeLimit.handleInput(e)"
              />
                <view class="profile-page__code-btn" @click="handleGetOldEmailCode">
                  <text class="profile-page__code-btn-text">{{ emailOldCodeText }}</text>
                </view>
              </view>
              <text v-if="emailErrors.oldCode" class="profile-page__error-text">{{ emailErrors.oldCode }}</text>
              <text v-if="oldCodeLimit.limitReached" class="profile-page__limit-text">{{ oldCodeLimit.limitHint }}</text>
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
          <!-- 步骤2：新邮箱验证 / 绑定邮箱（无邮箱用户直接显示此步骤） -->
          <view v-else>
            <view class="profile-page__form-field">
              <text class="profile-page__form-label">新邮箱地址</text>
              <input
                class="profile-page__input"
                :class="{ 'profile-page__input--error': emailErrors.newEmail }"
                v-model="emailForm.newEmail"
                placeholder="请输入新邮箱地址"
                placeholder-class="profile-page__placeholder"
                :maxlength="newEmailLimit.max"
                @input="e => emailForm.newEmail = newEmailLimit.handleInput(e)"
                @blur="emailErrors.newEmail = validateEmail(emailForm.newEmail)"
              />
              <text v-if="emailErrors.newEmail" class="profile-page__error-text">{{ emailErrors.newEmail }}</text>
              <text v-if="newEmailLimit.limitReached" class="profile-page__limit-text">{{ newEmailLimit.limitHint }}</text>
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
                  :maxlength="newCodeLimit.max"
                  @input="e => emailForm.newCode = newCodeLimit.handleInput(e)"
                />
                <view class="profile-page__code-btn" @click="handleGetNewEmailCode">
                  <text class="profile-page__code-btn-text">{{ emailNewCodeText }}</text>
                </view>
              </view>
              <text v-if="emailErrors.newCode" class="profile-page__error-text">{{ emailErrors.newCode }}</text>
              <text v-if="newCodeLimit.limitReached" class="profile-page__limit-text">{{ newCodeLimit.limitHint }}</text>
            </view>
            <view class="profile-page__form-actions">
              <view class="profile-page__btn profile-page__btn--cancel" @click="hasEmail ? handleResetEmailStep() : toggleSection('email')">
                <text class="profile-page__btn-text">{{ hasEmail ? '返回' : '取消' }}</text>
              </view>
              <view class="profile-page__btn profile-page__btn--submit" @click="handleChangeEmail">
                <text class="profile-page__btn-text">{{ hasEmail ? '修改' : '绑定' }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 分组 2：退出登录 + 删除账号（危险操作，单独分组并使用红色文字提示） -->
      <view class="profile-page__group">
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="handleLogout">
          <text class="profile-page__group-text profile-page__group-text--danger">退出登录</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="profile-page__group-item" @click="handleDeletion">
          <text class="profile-page__group-text profile-page__group-text--danger">
            {{ isDeletionScheduled ? '取消删除' : '删除账号' }}
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
 *  - 修改用户名：含前端格式校验 + 后端唯一性校验
 *  - 修改签名：点击后动态插入输入框和提交按钮，保存到数据库
 *  - 修改密码 / 设置密码：有密码用户走旧密码验证流程；无密码用户直接设置新密码
 *  - 修改邮箱 / 绑定邮箱：有邮箱用户走两步验证（旧邮箱 → 新邮箱）；无邮箱用户直接绑定新邮箱
 *  - 退出登录：弹窗二次确认，清除状态并跳转 settings.vue
 * 视觉规范参照 settings.vue 分组卡片，保持应用内设置类页面一致性
 */
import { reactive, ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { useInputLimit } from '../../composables/useInputLimit'
import { useUserStore } from '../../store/modules/user'
import {
  updateSignature,
  changePassword,
  sendChangeEmailOldCode,
  sendChangeEmailNewCode,
  changeEmail,
  updateAvatar,
  scheduleDeletion,
  cancelDeletion,
  updateUsername,
  setPassword,
  bindEmail
} from '../../api/modules/user'
import heiAvatar from '../../assets/images/touxiang/hei.png'
import hongAvatar from '../../assets/images/touxiang/hong.png'
import lanAvatar from '../../assets/images/touxiang/lan.png'
import { useShare } from '../../composables/useShare'

useShare({ title: '个人信息' })

const userStore = useUserStore()

// 输入框字符限制（与后端字段长度严格匹配）
const usernameLimit = useInputLimit(15, /^[\u4e00-\u9fa5a-zA-Z0-9]$/)
const signatureLimit = useInputLimit(70)
const oldPwdLimit = useInputLimit(20)
const newPwdLimit = useInputLimit(20)
const confirmPwdLimit = useInputLimit(20)
const oldCodeLimit = useInputLimit(6, /^\d$/)
const newEmailLimit = useInputLimit(254)
const newCodeLimit = useInputLimit(6, /^\d$/)

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

// 账号是否处于待删除状态（status=0：用户已确认删除，1分钟倒计时中）
const isDeletionScheduled = computed(() => userStore.userInfo?.status === 0)
// 当前用户是否已设置密码（微信登录用户可能无密码）
const hasPassword = computed(() => !!userStore.userInfo?.has_password)
// 当前用户是否已绑定邮箱（微信登录用户可能无邮箱）
const hasEmail = computed(() => !!userStore.userInfo?.email)

const expandedSections = reactive({
  username: false,
  avatar: false,
  signature: false,
  password: false,
  email: false
})

// 页面加载时接收参数：focus=email 时自动展开绑定邮箱区域（从 notification 页跳转）
onLoad((options) => {
  if (options && options.focus === 'email' && !isDeletionScheduled.value) {
    expandedSections.email = true
  }
})

// ===== 修改用户名 =====
const usernameForm = reactive({ value: '' })
const usernameError = ref('')

// ===== 修改头像 =====
const avatarForm = reactive({
  selected: urlToAvatarKey(userStore.userInfo?.avatar_url)
})

// ===== 修改签名 =====
const signatureForm = reactive({ value: '' })
const signatureError = ref('')

function toggleSection(section) {
  // 账号待删除状态下（status=0）禁止展开任何修改项
  if (isDeletionScheduled.value) return
  expandedSections[section] = !expandedSections[section]
  if (!expandedSections[section]) {
    resetSection(section)
  }
}

function resetSection(section) {
  if (section === 'username') {
    usernameForm.value = ''
    usernameError.value = ''
  } else if (section === 'avatar') {
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

// ===== 修改用户名 =====
function validateUsername(v) {
  if (!v) return '请输入用户名'
  if (v.length < 2 || v.length > 15) return '用户名长度需为 2-15 个字符'
  if (!/^[\u4e00-\u9fa5a-zA-Z0-9]+$/.test(v)) return '用户名仅允许中文、英文及数字字符'
  return ''
}

async function handleUpdateUsername() {
  const err = validateUsername(usernameForm.value.trim())
  if (err) {
    usernameError.value = err
    uni.showToast({ title: err, icon: 'none' })
    return
  }
  try {
    const result = await updateUsername({
      user_id: userStore.userInfo.id,
      new_username: usernameForm.value.trim()
    })
    // 同步更新本地用户信息
    userStore.userInfo.username = result.data.username
    try {
      uni.setStorageSync('userInfo', userStore.userInfo)
    } catch (e) {
      console.warn('保存本地用户信息失败', e)
    }
    uni.showToast({ title: '用户名修改成功', icon: 'success' })
    toggleSection('username')
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
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
  if (signatureForm.value.length > 70) {
    signatureError.value = '签名长度不能超过 70 个字符'
    return
  }
  try {
    await updateSignature({
      user_id: userStore.userInfo.id,
      signature: signatureForm.value.trim()
    })
    // 同步更新本地用户信息，settings.vue 通过 computed 自动刷新签名显示
    userStore.userInfo.signature = signatureForm.value.trim()
    try {
      uni.setStorageSync('userInfo', userStore.userInfo)
    } catch (e) {
      console.warn('保存本地用户信息失败', e)
    }
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
  passwordErrors.newPassword = validatePassword(passwordForm.newPassword)
  passwordErrors.confirmPassword = passwordForm.confirmPassword ? '' : '请输入确认密码'

  if (passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordErrors.confirmPassword = '两次密码不一致'
  }

  // 已有密码用户需校验旧密码
  if (hasPassword.value) {
    passwordErrors.oldPassword = passwordForm.oldPassword ? '' : '请输入旧密码'
  } else {
    passwordErrors.oldPassword = ''
  }

  const hasError = Object.values(passwordErrors).some((e) => e)
  if (hasError) {
    const firstErr = Object.values(passwordErrors).find((e) => e)
    uni.showToast({ title: firstErr, icon: 'none' })
    return
  }

  try {
    if (hasPassword.value) {
      // 修改密码：验证旧密码后更新
      await changePassword({
        user_id: userStore.userInfo.id,
        old_password: passwordForm.oldPassword,
        new_password: passwordForm.newPassword
      })
      uni.showToast({ title: '密码修改成功', icon: 'success' })
    } else {
      // 设置密码：无密码用户首次设置
      await setPassword({
        user_id: userStore.userInfo.id,
        new_password: passwordForm.newPassword
      })
      // 设置密码成功后更新本地 has_password 状态
      userStore.userInfo.has_password = true
      try {
        uni.setStorageSync('userInfo', userStore.userInfo)
      } catch (e) {
        console.warn('保存本地用户信息失败', e)
      }
      uni.showToast({ title: '密码设置成功', icon: 'success' })
    }
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
    // 绑定邮箱场景（无邮箱用户）允许邮箱已存在以触发账号合并；修改邮箱场景禁止已存在
    await sendChangeEmailNewCode(emailForm.newEmail, !hasEmail.value)
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
    if (hasEmail.value) {
      // 修改邮箱：需旧邮箱验证码 + 新邮箱验证码
      await changeEmail({
        user_id: userStore.userInfo.id,
        old_code: emailForm.oldCode,
        new_email: emailForm.newEmail,
        new_code: emailForm.newCode
      })
      uni.showToast({ title: '邮箱修改成功', icon: 'success' })
    } else {
      // 绑定邮箱：无邮箱用户首次绑定，仅需新邮箱验证码
      // 若邮箱已存在会触发账号合并，返回的主账号 id 可能与当前不同
      const result = await bindEmail({
        user_id: userStore.userInfo.id,
        new_email: emailForm.newEmail,
        new_code: emailForm.newCode
      })
      // 账号合并后用后端返回的完整用户信息更新本地状态（id/username/email/avatar_url/signature 等均可能变化）
      userStore.setUser(result.data)
      uni.showToast({ title: '邮箱绑定成功', icon: 'success' })
    }
    toggleSection('email')
  } catch (e) {
    // 验证码错误时统一提示"请输入正确验证码"
    const msg = /验证码/.test(e.message) ? '请输入正确验证码' : e.message
    uni.showToast({ title: msg, icon: 'none' })
  }
}

// ===== 删除账号 =====
function handleDeletion() {
  if (isDeletionScheduled.value) {
    // 处于冷静期，执行取消删除
    uni.showModal({
      title: '提示',
      content: '确定要取消账号删除吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await cancelDeletion(userStore.userInfo.id)
            userStore.userInfo.status = 1
            try {
              uni.setStorageSync('userInfo', userStore.userInfo)
            } catch (e) {
              console.warn('保存本地用户信息失败', e)
            }
            // 取消删除倒计时
            userStore.clearDeletionTimer()
            uni.showToast({ title: '账号删除已取消', icon: 'success' })
          } catch (e) {
            uni.showToast({ title: e.message, icon: 'none' })
          }
        }
      }
    })
  } else {
    // 未处于冷静期，执行删除
    uni.showModal({
      title: '删除账号',
      content: '账号将在1分钟后自动删除，且无法恢复，请保留个人数据',
      confirmText: '确认删除',
      cancelText: '取消',
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await scheduleDeletion(userStore.userInfo.id)
            userStore.userInfo.status = result.data.status
            try {
              uni.setStorageSync('userInfo', userStore.userInfo)
            } catch (e) {
              console.warn('保存本地用户信息失败', e)
            }
            // 启动 60 秒倒计时，到期后自动清除前端状态并跳转登录页
            userStore.startDeletionCountdown()
            uni.showToast({ title: '已计划删除，1分钟后自动删除', icon: 'none' })
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
/* ==========================================================================
 * 响应式单位说明（px → rpx 转换）
 * --------------------------------------------------------------------------
 * 基准：375px 设计稿，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * 转 rpx：width/height/padding/margin/gap/font-size/line-height/border-radius/定位偏移
 * 保留 px：1px 边框、box-shadow 偏移/模糊、9999px、百分比、vh、z-index
 * 平板/折叠屏断点：≥768px 锁定关键尺寸为 px，避免 rpx 过度放大
 * ========================================================================== */
.profile-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.profile-page__main {
  padding: 210rpx 48rpx 64rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
}

/* ===== 分组卡片 ===== */
.profile-page__group {
  border-radius: 48rpx;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.profile-page__group-item {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx;
  box-sizing: border-box;
  height: 98rpx;
}

.profile-page__group-item--bordered {
  border-bottom: 1px solid #f3f3f4;
}

/* 账号待删除状态下（status=0）：分组1整体置灰且禁用所有交互 */
.profile-page__group--disabled {
  opacity: 0.5;
  pointer-events: none;
}

.profile-page__group-text {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

.profile-page__group-text--danger {
  color: #d03238;
}

/* ===== 动态表单区域 ===== */
.profile-page__form-section {
  padding: 24rpx 32rpx;
  box-sizing: border-box;
  background: #fafafa;
}

.profile-page__form-field {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-bottom: 24rpx;
}

.profile-page__form-label {
  color: #41493a;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.profile-page__input {
  height: 88rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 16rpx;
  border: 1px solid #c1cab5;
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 42rpx;
}

.profile-page__input--error {
  border-color: #e5484d;
}

.profile-page__input--code {
  flex: 1;
}

.profile-page__placeholder {
  color: #454745;
  font-size: 28rpx;
}

.profile-page__error-text {
  color: #e5484d;
  font-size: 24rpx;
  line-height: 32rpx;
}

/* 字符限制提示文字 */
.profile-page__limit-text {
  color: #d97706;
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

/* ===== 验证码行 ===== */
.profile-page__code-row {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
}

.profile-page__code-btn {
  width: 192rpx;
  height: 88rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  border-radius: 16rpx;
  border: 1px solid #c1cab5;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.profile-page__code-btn-text {
  color: #0e0f0c;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* ===== 表单操作按钮 ===== */
.profile-page__form-actions {
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
  gap: 24rpx;
  margin-top: 32rpx;
}

.profile-page__btn {
  height: 72rpx;
  padding: 0 40rpx;
  box-sizing: border-box;
  border-radius: 36rpx;
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
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

/* ===== 头像选择列表 ===== */
.profile-page__avatar-list {
  display: flex;
  flex-direction: row;
  gap: 32rpx;
  padding: 16rpx 0;
}

.profile-page__avatar-option {
  width: 144rpx;
  height: 144rpx;
  border-radius: 24rpx;
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
  width: 112rpx;
  height: 112rpx;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 * 规则：将本页面主要容器的宽度、卡片宽度、按钮尺寸锁定为设计稿原 px 值
 */
@media screen and (min-width: 768px) {
  /* 页面主容器：锁定 padding 与分组间距 */
  .profile-page__main {
    padding: 105px 24px 32px;
    gap: 32px;
  }

  /* 分组卡片圆角 */
  .profile-page__group {
    border-radius: 24px;
  }

  /* 列表项高度与内边距 */
  .profile-page__group-item {
    padding: 12px 16px;
    height: 49px;
  }

  /* 主文字字号 */
  .profile-page__group-text {
    font-size: 16px;
    line-height: 24px;
  }

  /* 表单区域内边距 */
  .profile-page__form-section {
    padding: 12px 16px;
  }

  .profile-page__form-field {
    gap: 4px;
    margin-bottom: 12px;
  }

  .profile-page__form-label {
    font-size: 14px;
    line-height: 20px;
  }

  /* 输入框尺寸 */
  .profile-page__input {
    height: 44px;
    padding: 0 12px;
    border-radius: 8px;
    font-size: 16px;
    line-height: 21px;
  }

  .profile-page__placeholder {
    font-size: 14px;
  }

  .profile-page__error-text {
    font-size: 12px;
    line-height: 16px;
  }

  .profile-page__limit-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }

  /* 验证码行 */
  .profile-page__code-row {
    gap: 8px;
  }

  .profile-page__code-btn {
    width: 96px;
    height: 44px;
    padding: 0 12px;
    border-radius: 8px;
  }

  .profile-page__code-btn-text {
    font-size: 14px;
    line-height: 20px;
  }

  /* 表单操作按钮 */
  .profile-page__form-actions {
    gap: 12px;
    margin-top: 16px;
  }

  .profile-page__btn {
    height: 36px;
    padding: 0 20px;
    border-radius: 18px;
  }

  .profile-page__btn-text {
    font-size: 14px;
    line-height: 20px;
  }

  /* 头像选择列表 */
  .profile-page__avatar-list {
    gap: 16px;
    padding: 8px 0;
  }

  .profile-page__avatar-option {
    width: 72px;
    height: 72px;
    border-radius: 12px;
  }

  .profile-page__avatar-image {
    width: 56px;
    height: 56px;
  }
}
</style>
