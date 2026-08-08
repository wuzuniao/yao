<template>
  <view :data-theme="themeKey" class="profile-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="profile-page__main">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/notification 等页面保持一致） -->
      <PageHeader :title="$t('profile.title')" :desc="$t('profile.desc')" />

      <!-- 分组 1：资料修改（修改用户名、修改头像、修改签名、修改密码、修改邮箱） -->
      <view class="profile-page__group" :class="{ 'profile-page__group--disabled': isDeletionScheduled }">
        <!-- 修改用户名 -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('username')">
          <text class="profile-page__group-text">{{ $t('profile.changeUsername') }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改用户名表单（动态显示） -->
        <view v-if="expandedSections.username" class="profile-page__form-section">
          <view class="profile-page__form-field">
            <text class="profile-page__form-label">{{ $t('profile.newUsername') }}</text>
            <input
              class="profile-page__input"
              :class="{ 'profile-page__input--error': usernameError }"
              v-model="usernameForm.value"
              :placeholder="$t('profile.newUsernamePlaceholder')"
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
              <text class="profile-page__btn-text">{{ $t('common.cancel') }}</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleUpdateUsername">
              <text class="profile-page__btn-text">{{ $t('common.submit') }}</text>
            </view>
          </view>
        </view>

        <!-- 修改头像 -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('avatar')">
          <text class="profile-page__group-text">{{ $t('profile.changeAvatar') }}</text>
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
              <text class="profile-page__btn-text">{{ $t('common.cancel') }}</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleUpdateAvatar">
              <text class="profile-page__btn-text">{{ $t('common.submit') }}</text>
            </view>
          </view>
        </view>

        <!-- 修改签名 -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('signature')">
          <text class="profile-page__group-text">{{ $t('profile.changeSignature') }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改签名表单（动态显示） -->
        <view v-if="expandedSections.signature" class="profile-page__form-section">
          <input
            class="profile-page__input"
            :class="{ 'profile-page__input--error': signatureError }"
            v-model="signatureForm.value"
            :placeholder="$t('profile.signaturePlaceholder')"
            placeholder-class="profile-page__placeholder"
            :maxlength="signatureLimit.max"
            @input="e => signatureForm.value = signatureLimit.handleInput(e)"
          />
          <text v-if="signatureError" class="profile-page__error-text">{{ signatureError }}</text>
          <text v-if="signatureLimit.limitReached" class="profile-page__limit-text">{{ signatureLimit.limitHint }}</text>
          <view class="profile-page__form-actions">
            <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('signature')">
              <text class="profile-page__btn-text">{{ $t('common.cancel') }}</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleUpdateSignature">
              <text class="profile-page__btn-text">{{ $t('common.submit') }}</text>
            </view>
          </view>
        </view>

        <!-- 修改密码 / 设置密码（无密码用户显示"设置密码"） -->
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="toggleSection('password')">
          <text class="profile-page__group-text">{{ hasPassword ? $t('profile.changePassword') : $t('profile.setPassword') }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改/设置密码表单（动态显示） -->
        <view v-if="expandedSections.password" class="profile-page__form-section">
          <!-- 旧密码（仅已设置密码的用户需要验证） -->
          <view v-if="hasPassword" class="profile-page__form-field">
            <text class="profile-page__form-label">{{ $t('profile.oldPassword') }}</text>
            <view
              class="profile-page__password-row"
              :class="{ 'profile-page__password-row--error': passwordErrors.oldPassword }"
            >
              <input
                class="profile-page__input profile-page__input--password"
                v-model="passwordForm.oldPassword"
                :password="!showOldPassword"
                :key="'pro-old-' + showOldPassword"
                :placeholder="$t('profile.oldPasswordPlaceholder')"
                placeholder-class="profile-page__placeholder"
                :maxlength="oldPwdLimit.max"
                @input="e => passwordForm.oldPassword = oldPwdLimit.handleInput(e)"
                @blur="passwordErrors.oldPassword = passwordForm.oldPassword ? '' : $t('validate.oldPasswordRequired')"
              />
              <view class="profile-page__eye" @click="toggleOldPassword">
                <PasswordEye :visible="showOldPassword" />
              </view>
            </view>
            <text v-if="passwordErrors.oldPassword" class="profile-page__error-text">{{ passwordErrors.oldPassword }}</text>
            <text v-if="oldPwdLimit.limitReached" class="profile-page__limit-text">{{ oldPwdLimit.limitHint }}</text>
          </view>
          <view class="profile-page__form-field">
            <text class="profile-page__form-label">{{ $t('profile.newPassword') }}</text>
            <view
              class="profile-page__password-row"
              :class="{ 'profile-page__password-row--error': passwordErrors.newPassword }"
            >
              <input
                class="profile-page__input profile-page__input--password"
                v-model="passwordForm.newPassword"
                :password="!showNewPassword"
                :key="'pro-new-' + showNewPassword"
                :placeholder="$t('profile.newPasswordPlaceholder')"
                placeholder-class="profile-page__placeholder"
                :maxlength="newPwdLimit.max"
                @input="e => passwordForm.newPassword = newPwdLimit.handleInput(e)"
                @blur="passwordErrors.newPassword = validatePassword(passwordForm.newPassword)"
              />
              <view class="profile-page__eye" @click="toggleNewPassword">
                <PasswordEye :visible="showNewPassword" />
              </view>
            </view>
            <text v-if="passwordErrors.newPassword" class="profile-page__error-text">{{ passwordErrors.newPassword }}</text>
            <text v-if="newPwdLimit.limitReached" class="profile-page__limit-text">{{ newPwdLimit.limitHint }}</text>
          </view>
          <view class="profile-page__form-field">
            <text class="profile-page__form-label">{{ $t('profile.confirmPassword') }}</text>
            <view
              class="profile-page__password-row"
              :class="{ 'profile-page__password-row--error': passwordErrors.confirmPassword }"
            >
              <input
                class="profile-page__input profile-page__input--password"
                v-model="passwordForm.confirmPassword"
                :password="!showConfirmPassword"
                :key="'pro-cpwd-' + showConfirmPassword"
                :placeholder="$t('profile.confirmPasswordPlaceholder')"
                placeholder-class="profile-page__placeholder"
                :maxlength="confirmPwdLimit.max"
                @input="e => passwordForm.confirmPassword = confirmPwdLimit.handleInput(e)"
                @blur="passwordErrors.confirmPassword = passwordForm.confirmPassword ? (passwordForm.confirmPassword !== passwordForm.newPassword ? $t('validate.confirmPasswordMismatch') : '') : $t('validate.confirmPasswordRequired')"
              />
              <view class="profile-page__eye" @click="toggleConfirmPassword">
                <PasswordEye :visible="showConfirmPassword" />
              </view>
            </view>
            <text v-if="passwordErrors.confirmPassword" class="profile-page__error-text">{{ passwordErrors.confirmPassword }}</text>
            <text v-if="confirmPwdLimit.limitReached" class="profile-page__limit-text">{{ confirmPwdLimit.limitHint }}</text>
          </view>
          <view class="profile-page__form-actions">
            <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('password')">
              <text class="profile-page__btn-text">{{ $t('common.cancel') }}</text>
            </view>
            <view class="profile-page__btn profile-page__btn--submit" @click="handleChangePassword">
              <text class="profile-page__btn-text">{{ $t('common.submit') }}</text>
            </view>
          </view>
        </view>

        <!-- 修改邮箱 / 绑定邮箱（无邮箱用户显示"绑定邮箱"），作为分组1最后一项无需下边框 -->
        <view class="profile-page__group-item" @click="toggleSection('email')">
          <text class="profile-page__group-text">{{ hasEmail ? $t('profile.changeEmail') : $t('profile.bindEmail') }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 修改/绑定邮箱表单（动态显示） -->
        <view v-if="expandedSections.email" class="profile-page__form-section">
          <!-- 步骤1：旧邮箱验证（仅已有邮箱的用户需要） -->
          <view v-if="hasEmail && emailStep === 1">
            <view class="profile-page__form-field">
              <text class="profile-page__form-label">{{ $t('profile.oldEmailCode') }}</text>
              <view class="profile-page__code-row">
                <input
                class="profile-page__input profile-page__input--code"
                :class="{ 'profile-page__input--error': emailErrors.oldCode }"
                v-model="emailForm.oldCode"
                :placeholder="$t('profile.codePlaceholder')"
                placeholder-class="profile-page__placeholder"
                :maxlength="oldCodeLimit.max"
                @input="e => emailForm.oldCode = oldCodeLimit.handleInput(e)"
              />
                <view
                  class="profile-page__code-btn"
                  :class="{ 'profile-page__code-btn--disabled': emailOldCodeCounting || emailOldCodeSending }"
                  @click="handleGetOldEmailCode"
                >
                  <text class="profile-page__code-btn-text">{{ emailOldCodeText }}</text>
                </view>
              </view>
              <text v-if="emailErrors.oldCode" class="profile-page__error-text">{{ emailErrors.oldCode }}</text>
              <text v-if="oldCodeLimit.limitReached" class="profile-page__limit-text">{{ oldCodeLimit.limitHint }}</text>
            </view>
            <view class="profile-page__form-actions">
              <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('email')">
                <text class="profile-page__btn-text">{{ $t('common.cancel') }}</text>
              </view>
              <view class="profile-page__btn profile-page__btn--submit" @click="handleVerifyOldEmail">
                <text class="profile-page__btn-text">{{ $t('common.verify') }}</text>
              </view>
            </view>
          </view>
          <!-- 步骤2：新邮箱验证 / 绑定邮箱（无邮箱用户直接显示此步骤） -->
          <view v-else>
            <view class="profile-page__form-field">
              <text class="profile-page__form-label">{{ $t('profile.newEmail') }}</text>
              <input
                class="profile-page__input"
                :class="{ 'profile-page__input--error': emailErrors.newEmail }"
                v-model="emailForm.newEmail"
                :placeholder="$t('profile.newEmailPlaceholder')"
                placeholder-class="profile-page__placeholder"
                :maxlength="newEmailLimit.max"
                @input="e => emailForm.newEmail = newEmailLimit.handleInput(e)"
                @blur="emailErrors.newEmail = validateEmail(emailForm.newEmail)"
              />
              <text v-if="emailErrors.newEmail" class="profile-page__error-text">{{ emailErrors.newEmail }}</text>
              <text v-if="newEmailLimit.limitReached" class="profile-page__limit-text">{{ newEmailLimit.limitHint }}</text>
            </view>
            <view class="profile-page__form-field">
              <text class="profile-page__form-label">{{ $t('profile.newEmailCode') }}</text>
              <view class="profile-page__code-row">
                <input
                  class="profile-page__input profile-page__input--code"
                  :class="{ 'profile-page__input--error': emailErrors.newCode }"
                  v-model="emailForm.newCode"
                  :placeholder="$t('profile.codePlaceholder')"
                  placeholder-class="profile-page__placeholder"
                  :maxlength="newCodeLimit.max"
                  @input="e => emailForm.newCode = newCodeLimit.handleInput(e)"
                />
                <view
                  class="profile-page__code-btn"
                  :class="{ 'profile-page__code-btn--disabled': emailNewCodeCounting || emailNewCodeSending }"
                  @click="handleGetNewEmailCode"
                >
                  <text class="profile-page__code-btn-text">{{ emailNewCodeText }}</text>
                </view>
              </view>
              <text v-if="emailErrors.newCode" class="profile-page__error-text">{{ emailErrors.newCode }}</text>
              <text v-if="newCodeLimit.limitReached" class="profile-page__limit-text">{{ newCodeLimit.limitHint }}</text>
            </view>
            <view class="profile-page__form-actions">
              <view class="profile-page__btn profile-page__btn--cancel" @click="hasEmail ? handleResetEmailStep() : toggleSection('email')">
                <text class="profile-page__btn-text">{{ hasEmail ? $t('common.back') : $t('common.cancel') }}</text>
              </view>
              <view class="profile-page__btn profile-page__btn--submit" @click="handleChangeEmail">
                <text class="profile-page__btn-text">{{ hasEmail ? $t('common.modify') : $t('common.bind') }}</text>
              </view>
            </view>
          </view>
        </view>

      </view>

      <!-- 分组 1.5：偏好设置（语言 / 指纹登录 / 主题，独立成区） -->
      <view class="profile-page__group">
        <!-- 语言切换（简体中文 / English） -->
        <view class="profile-page__group-item profile-page__group-item--bordered">
          <text class="profile-page__group-text">{{ $t('profile.language') }}</text>
          <!-- 纯 CSS 手写开关（独立类，区别于指纹开关）：旋钮滑动指示状态，
               开关内居中显示当前语言名，引用语义令牌保持单一配色真源 -->
          <view
            class="profile-page__lang-switch"
            :class="{ 'profile-page__lang-switch--on': languageIsEnglish }"
            role="switch"
            :aria-checked="languageIsEnglish"
            @click="toggleLanguage"
          >
            <view class="profile-page__lang-knob" />
            <text class="profile-page__lang-text">{{ $t('language.' + (languageStore.current === 'zh-CN' ? 'zhCN' : 'en')) }}</text>
          </view>
        </view>

        <!-- 指纹登录开关（仅 App 端：设备支持指纹 + 已登录时显示） -->
        <!-- #ifdef APP -->
        <view v-if="showBiometric" class="profile-page__group-item profile-page__group-item--bordered">
          <text class="profile-page__group-text">{{ $t('profile.biometric') }}</text>
          <!-- 纯 CSS 手写开关：原生 switch 的 color 属性编译期取色、不支持 var()，
               故手写以引用语义令牌 var(--color-wechat)，保持全局单一配色真源 -->
          <view
            class="profile-page__biometric-switch"
            :class="{ 'profile-page__biometric-switch--on': biometricEnabled }"
            role="switch"
            :aria-checked="biometricEnabled"
            @click="toggleBiometric"
          >
            <view class="profile-page__biometric-switch-knob" />
          </view>
        </view>
        <!-- #endif -->

        <!-- 主题切换：仅 role>1 用户显示（进入页面时已查询数据库刷新 role） -->
        <template v-if="showTheme">
          <view class="profile-page__group-item" @click="toggleSection('theme')">
            <text class="profile-page__group-text">{{ $t('profile.theme') }}</text>
            <view class="u-arrow-right"></view>
          </view>
          <!-- 主题选择（动态显示） -->
          <view v-if="expandedSections.theme" class="profile-page__form-section">
            <view class="profile-page__theme-list">
              <view
                v-for="item in themeList"
                :key="item.key"
                class="profile-page__theme-option"
                :class="{ 'profile-page__theme-option--selected': themeForm.selected === item.key }"
                @click="themeForm.selected = item.key"
              >
                <view class="profile-page__theme-swatch" :style="{ background: item.swatch }"></view>
                <text class="profile-page__theme-name">{{ item.name }}</text>
              </view>
            </view>
            <view class="profile-page__form-actions">
              <view class="profile-page__btn profile-page__btn--cancel" @click="toggleSection('theme')">
                <text class="profile-page__btn-text">{{ $t('common.cancel') }}</text>
              </view>
              <view class="profile-page__btn profile-page__btn--submit" @click="handleApplyTheme">
                <text class="profile-page__btn-text">{{ $t('common.submit') }}</text>
              </view>
            </view>
          </view>
        </template>
      </view>

      <!-- 分组 2：退出登录 + 删除账号（危险操作，单独分组并使用红色文字提示） -->
      <view class="profile-page__group">
        <view class="profile-page__group-item profile-page__group-item--bordered" @click="handleLogout">
          <text class="profile-page__group-text profile-page__group-text--danger">{{ $t('profile.logout') }}</text>
          <view class="u-arrow-right"></view>
        </view>
        <view class="profile-page__group-item" @click="handleDeletion">
          <text class="profile-page__group-text profile-page__group-text--danger">
            {{ isDeletionScheduled ? $t('profile.cancelDeletion') : $t('profile.deleteAccount') }}
          </text>
          <view class="u-arrow-right"></view>
        </view>
        <!-- 免登录账号删除说明入口（满足 Google Play 网页删除入口要求） -->
        <view class="profile-page__group-item profile-page__group-item--hint" @click="goDeleteAccountHelp">
          <text class="profile-page__group-text profile-page__group-text--hint">{{ $t('profile.deleteAccountHelp') }}</text>
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
import PasswordEye from '../../components/PasswordEye.vue'
import { useInputLimit } from '../../composables/useInputLimit'
import { useUserStore } from '../../store/modules/user'
import { useThemeStore, THEME_LIST } from '../../store/modules/theme'
import { useLanguageStore } from '../../store/modules/language'
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
  bindEmail,
  getUserInfo,
} from '../../api/modules/user'
import heiAvatar from '../../assets/images/touxiang/hei.png'
import hongAvatar from '../../assets/images/touxiang/hong.png'
import lanAvatar from '../../assets/images/touxiang/lan.png'
import { useShare } from '../../composables/useShare'
import { t } from '../../locale'
// App 端生物识别（指纹）登录开关（仅 App 端使用）
// #ifdef APP
import { useBiometric } from '../../composables/useBiometric'
// #endif

useShare({ title: t('share.profile') })

const userStore = useUserStore()
const themeStore = useThemeStore()
// 语言偏好（默认简体中文，本次仅做按钮切换，不接入翻译）
const languageStore = useLanguageStore()
const languageIsEnglish = computed(() => languageStore.current === 'en')
// 主题清单（与 global.scss 的 [data-theme] 方案一一对应，按代表色命名）
const themeList = THEME_LIST

// 输入框字符限制（与后端字段长度严格匹配）
const usernameLimit = useInputLimit(15, /^[\u4e00-\u9fa5a-zA-Z0-9]$/)
const signatureLimit = useInputLimit(70)
const oldPwdLimit = useInputLimit(20)
const newPwdLimit = useInputLimit(20)
const confirmPwdLimit = useInputLimit(20)

// 密码显隐切换（默认隐藏，点击眼睛睁眼显示明文）
const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
function toggleOldPassword() {
  showOldPassword.value = !showOldPassword.value
}
function toggleNewPassword() {
  showNewPassword.value = !showNewPassword.value
}
function toggleConfirmPassword() {
  showConfirmPassword.value = !showConfirmPassword.value
}
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

// 账号是否处于待删除状态（status=0：用户已确认删除，24小时倒计时中）
const isDeletionScheduled = computed(() => userStore.userInfo?.status === 0)
// 当前用户是否已设置密码（微信登录用户可能无密码）
const hasPassword = computed(() => !!userStore.userInfo?.has_password)
// 当前用户是否已绑定邮箱（微信登录用户可能无邮箱）
const hasEmail = computed(() => !!userStore.userInfo?.email)
// 仅 users 表中 role > 1 的用户显示「主题」入口（进入页面时查询数据库刷新）
const showTheme = computed(() => (userStore.userInfo?.role ?? 0) > 1)

// ===== App 端指纹登录开关（仅 App 端）=====
// 显示条件：设备支持指纹 + 当前已登录
// #ifdef APP
const biometric = useBiometric()
const biometricSupported = ref(false)
const biometricEnabled = ref(false)
// #endif
// #ifdef APP
// 指纹登录开关是否展示：设备支持指纹且页面处于已登录状态
const showBiometric = computed(() => biometricSupported.value && !!userStore.userInfo?.id)
// #endif

const expandedSections = reactive({
  username: false,
  avatar: false,
  signature: false,
  password: false,
  email: false,
  theme: false
})

// 页面加载时接收参数：focus=email 时自动展开绑定邮箱区域（从 notification 页跳转）
onLoad((options) => {
  if (options && options.focus === 'email' && !isDeletionScheduled.value) {
    expandedSections.email = true
  }
  // 查询数据库刷新最新 userInfo（含 role），用于「主题」入口按 role>1 显隐判定
  if (userStore.userInfo?.id) {
    getUserInfo()
      .then((res) => {
        if (res && res.data) {
          userStore.userInfo = { ...userStore.userInfo, ...res.data }
          try {
            uni.setStorageSync('userInfo', userStore.userInfo)
          } catch (e) {
            console.warn('刷新本地用户信息失败', e)
          }
        }
      })
      .catch((e) => console.warn('获取用户信息失败', e))
  }
  // App 端：检测指纹能力并读取本地开关状态
  // #ifdef APP
  biometric.isAvailable().then((ok) => {
    biometricSupported.value = ok
    if (ok) {
      biometricEnabled.value = biometric.isEnabled()
    }
  })
  // #endif
})

// ===== 修改用户名 =====
const usernameForm = reactive({ value: '' })
const usernameError = ref('')

// ===== 修改头像 =====
const avatarForm = reactive({
  selected: urlToAvatarKey(userStore.userInfo?.avatar_url)
})

// ===== 主题切换 =====
const themeForm = reactive({
  // 默认选中当前已生效主题
  selected: themeStore.current
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
  } else if (section === 'theme') {
    themeForm.selected = themeStore.current
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
  if (!v) return t('validate.usernameRequired')
  if (v.length < 2 || v.length > 15) return t('validate.usernameLength')
  if (!/^[\u4e00-\u9fa5a-zA-Z0-9]+$/.test(v)) return t('validate.usernameFormat')
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
      new_username: usernameForm.value.trim()
    })
    // 同步更新本地用户信息
    userStore.userInfo.username = result.data.username
    try {
      uni.setStorageSync('userInfo', userStore.userInfo)
    } catch (e) {
      console.warn(t('profile.usernameUpdated'), e)
    }
    uni.showToast({ title: t('profile.usernameUpdated'), icon: 'success' })
    toggleSection('username')
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function handleUpdateAvatar() {
  const avatarValue = avatarKeyToDbValue[avatarForm.selected]
  if (!avatarValue) {
    uni.showToast({ title: t('profile.avatarRequired'), icon: 'none' })
    return
  }
  try {
    await updateAvatar({
      avatar_url: avatarValue
    })
    // 同步更新本地用户信息
    userStore.userInfo.avatar_url = avatarValue
    try {
      uni.setStorageSync('userInfo', userStore.userInfo)
    } catch (e) {
      console.warn(t('profile.avatarUpdated'), e)
    }
    uni.showToast({ title: t('profile.avatarUpdated'), icon: 'success' })
    toggleSection('avatar')
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function handleApplyTheme() {
  if (!themeForm.selected) {
    uni.showToast({ title: t('profile.themeRequired'), icon: 'none' })
    return
  }
  // 写入主题 store（内部持久化 + 更新 App.vue 根 data-theme，全端即时生效）
  themeStore.setTheme(themeForm.selected)
  uni.showToast({ title: t('profile.themeApplied'), icon: 'success' })
  toggleSection('theme')
}

async function handleUpdateSignature() {
  if (!signatureForm.value.trim()) {
    signatureError.value = t('validate.signatureRequired')
    return
  }
  if (signatureForm.value.length > 70) {
    signatureError.value = t('validate.signatureTooLong')
    return
  }
  try {
    await updateSignature({
      signature: signatureForm.value.trim()
    })
    // 同步更新本地用户信息，settings.vue 通过 computed 自动刷新签名显示
    userStore.userInfo.signature = signatureForm.value.trim()
    try {
      uni.setStorageSync('userInfo', userStore.userInfo)
    } catch (e) {
      console.warn(t('profile.signatureUpdated'), e)
    }
    uni.showToast({ title: t('profile.signatureUpdated'), icon: 'success' })
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
  if (!v) return t('validate.passwordRequired')
  if (v.length < 8 || v.length > 20) return t('validate.passwordLength')
  let categories = 0
  if (/[a-z]/.test(v)) categories++
  if (/[A-Z]/.test(v)) categories++
  if (/[0-9]/.test(v)) categories++
  if (/[^a-zA-Z0-9]/.test(v)) categories++
  if (categories < 3) return t('validate.passwordStrength')
  return ''
}

async function handleChangePassword() {
  passwordErrors.newPassword = validatePassword(passwordForm.newPassword)
  passwordErrors.confirmPassword = passwordForm.confirmPassword ? '' : t('validate.confirmPasswordRequired')

  if (passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordErrors.confirmPassword = t('validate.confirmPasswordMismatch')
  }

  // 已有密码用户需校验旧密码
  if (hasPassword.value) {
    passwordErrors.oldPassword = passwordForm.oldPassword ? '' : t('validate.oldPasswordRequired')
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
          old_password: passwordForm.oldPassword,
        new_password: passwordForm.newPassword
      })
      uni.showToast({ title: t('profile.passwordUpdated'), icon: 'success' })
    } else {
      // 设置密码：无密码用户首次设置
      await setPassword({
          new_password: passwordForm.newPassword
      })
      // 设置密码成功后更新本地 has_password 状态
      userStore.userInfo.has_password = true
      try {
        uni.setStorageSync('userInfo', userStore.userInfo)
      } catch (e) {
        console.warn(t('profile.passwordUpdated'), e)
      }
      uni.showToast({ title: t('profile.passwordSet'), icon: 'success' })
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
const emailOldCodeSending = ref(false)
const emailNewCodeCounting = ref(false)
const emailNewCodeText = ref('获取验证码')
const emailNewCodeSending = ref(false)

function validateEmail(v) {
  if (!v) return t('validate.emailRequired')
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return t('validate.emailFormat')
  return ''
}

function validateCode(v) {
  if (!v) return t('validate.codeRequired')
  if (!/^\d{6}$/.test(v)) return t('validate.codeFormat')
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
      targetText.value = t('common.getCode')
    } else {
      targetText.value = `${sec}s`
    }
  }, 1000)
}

async function handleGetOldEmailCode() {
  if (emailOldCodeCounting.value || emailOldCodeSending.value) return
  emailOldCodeSending.value = true
  emailOldCodeText.value = t('common.sending')
  try {
    await sendChangeEmailOldCode()
    uni.showToast({ title: t('common.codeSent'), icon: 'none' })
    startCountdown(emailOldCodeText, emailOldCodeCounting)
  } catch (e) {
    // 发送失败恢复按钮，允许用户立即重试
    emailOldCodeText.value = t('common.getCode')
    uni.showToast({ title: e.message, icon: 'none' })
  } finally {
    emailOldCodeSending.value = false
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
  emailNewCodeText.value = t('common.getCode')
}

async function handleGetNewEmailCode() {
  if (emailNewCodeCounting.value || emailNewCodeSending.value) return
  const emailErr = validateEmail(emailForm.newEmail)
  if (emailErr) {
    emailErrors.newEmail = emailErr
    uni.showToast({ title: emailErr, icon: 'none' })
    return
  }
  emailNewCodeSending.value = true
  emailNewCodeText.value = t('common.sending')
  try {
    // 绑定邮箱场景（无邮箱用户）允许邮箱已存在以触发账号合并；修改邮箱场景禁止已存在
    await sendChangeEmailNewCode(emailForm.newEmail, !hasEmail.value)
    uni.showToast({ title: t('common.codeSent'), icon: 'none' })
    startCountdown(emailNewCodeText, emailNewCodeCounting)
  } catch (e) {
    // 发送失败恢复按钮，允许用户立即重试
    emailNewCodeText.value = t('common.getCode')
    uni.showToast({ title: e.message, icon: 'none' })
  } finally {
    emailNewCodeSending.value = false
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
          old_code: emailForm.oldCode,
        new_email: emailForm.newEmail,
        new_code: emailForm.newCode
      })
      uni.showToast({ title: t('profile.emailUpdated'), icon: 'success' })
    } else {
      // 绑定邮箱：无邮箱用户首次绑定，仅需新邮箱验证码
      // 若邮箱已存在会触发账号合并，返回的主账号 id 和 access_token 可能与当前不同
      const result = await bindEmail({
          new_email: emailForm.newEmail,
        new_code: emailForm.newCode
      })
      // 账号合并后用后端返回的完整用户信息更新本地状态（id/username/email/avatar_url/signature/access_token 等均可能变化）
      userStore.setUser(result.data)
      // 刷新未读站内信等用户相关缓存，确保合并后全局状态与主账号一致
      userStore.loadUnreadCount(true)
      uni.showToast({ title: t('profile.emailBound'), icon: 'success' })
    }
    toggleSection('email')
  } catch (e) {
    // 验证码错误时统一提示"请输入正确验证码"
    const msg = /验证码/.test(e.message) ? t('profile.codeIncorrectHint') : e.message
    uni.showToast({ title: msg, icon: 'none' })
  }
}

// ===== 删除账号 =====
function handleDeletion() {
  if (isDeletionScheduled.value) {
    // 处于冷静期，执行取消删除
    uni.showModal({
      title: t('common.tip'),
      content: t('profile.cancelDeletionConfirm'),
      success: async (res) => {
        if (res.confirm) {
          try {
            await cancelDeletion()
            userStore.userInfo.status = 1
            try {
              uni.setStorageSync('userInfo', userStore.userInfo)
            } catch (e) {
              console.warn(t('profile.deletionCancelled'), e)
            }
            // 取消删除倒计时
            userStore.clearDeletionTimer()
            uni.showToast({ title: t('profile.deletionCancelled'), icon: 'success' })
          } catch (e) {
            uni.showToast({ title: e.message, icon: 'none' })
          }
        }
      }
    })
  } else {
    // 未处于冷静期，执行删除
    uni.showModal({
      title: t('profile.deleteConfirmTitle'),
      content: t('profile.deleteConfirmContent'),
      confirmText: t('profile.deleteConfirmText'),
      cancelText: t('common.cancel'),
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await scheduleDeletion()
            userStore.userInfo.status = result.data.status
            try {
              uni.setStorageSync('userInfo', userStore.userInfo)
            } catch (e) {
              console.warn(t('profile.deletionScheduled'), e)
            }
            // 启动 24 小时倒计时，到期后自动清除前端状态并跳转登录页
            userStore.startDeletionCountdown()
            uni.showToast({ title: t('profile.deletionScheduled'), icon: 'none' })
          } catch (e) {
            uni.showToast({ title: e.message, icon: 'none' })
          }
        }
      }
    })
  }
}

// ===== 语言切换（简体中文 / English）=====
function toggleLanguage() {
  // 在简体中文（zh-CN）与 English（en）之间切换，持久化到本地
  languageStore.setLanguage(languageIsEnglish.value ? 'zh-CN' : 'en')
}

// ===== App 端指纹登录开关切换（仅 App 端）=====
// #ifdef APP
function toggleBiometric() {
  // 账号待删除状态下禁止操作
  if (isDeletionScheduled.value) return
  const next = !biometricEnabled.value
  if (next) {
    // 开启：若本地无凭证，提示用户先使用账号密码登录一次以生成凭证
    const hasToken = !!biometric.getBiometricToken()
    if (!hasToken) {
      biometricEnabled.value = false
      uni.showToast({ title: t('profile.biometricNeedLogin'), icon: 'none' })
      return
    }
    biometric.setEnabled(true)
    biometricEnabled.value = true
  } else {
    // 关闭：仅切换本地开关标记，不清理本地凭证、不撤销服务端凭证
    // 用户主动关闭/打开指纹登录不主动清理本地信息，便于再次打开时无需重新账号密码登录；
    // 退出登录时同样保留凭证，真正的凭证清理仅在注销账号时统一处理（关闭指纹 ≠ 退出登录）
    biometric.setEnabled(false)
    biometricEnabled.value = false
  }
}
// #endif

// ===== 跳转免登录账号删除说明页 =====
function goDeleteAccountHelp() {
  uni.navigateTo({ url: '/pages/user/delete-account' })
}

// ===== 退出登录 =====
function handleLogout() {
  uni.showModal({
    title: t('common.tip'),
    content: t('profile.logoutConfirm'),
    success: (res) => {
      if (res.confirm) {
        userStore.clearUser()
        uni.showToast({ title: t('profile.loggedOut'), icon: 'none' })
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
  background: var(--color-card-bg);
  box-shadow: var(--shadow-card);
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
  border-bottom: 1px solid var(--color-separator);
}

/* 账号待删除状态下（status=0）：分组1整体置灰且禁用所有交互 */
.profile-page__group--disabled {
  opacity: 0.5;
  pointer-events: none;
}

.profile-page__group-text {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

.profile-page__group-text--danger {
  color: var(--color-danger);
}

/* 免登录账号删除说明入口（弱提示样式，区别于危险操作） */
.profile-page__group-item--hint {
  border-top: 1px solid var(--color-separator);
}

.profile-page__group-text--hint {
  color: var(--color-brand);
}

/* 指纹登录开关：纯 CSS 手写开关（替代原生 switch，以支持 var() 单一配色真源） */
.profile-page__biometric-switch {
  position: relative;
  width: 88rpx;
  height: 48rpx;
  border-radius: 9999px;
  background: var(--color-border-input); /* 关态轨道色 */
  transition: background 0.2s ease;
  flex-shrink: 0;
}
.profile-page__biometric-switch--on {
  background: var(--color-wechat); /* 开态轨道色（随主题代表色：绿/蓝/靛蓝/薰衣草） */
}
.profile-page__biometric-switch-knob {
  position: absolute;
  top: 4rpx;
  left: 4rpx;
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: var(--color-text-inverse); /* 白色滑块 */
  transition: transform 0.2s ease;
}
.profile-page__biometric-switch--on .profile-page__biometric-switch-knob {
  transform: translateX(40rpx);
}

/* 语言切换开关：纯 CSS 手写开关（独立于指纹开关）
   旋钮滑动指示状态，文字显示在旋钮对侧（避免被白色圆点遮挡），引用语义令牌保持单一配色真源 */
.profile-page__lang-switch {
  position: relative;
  width: 176rpx;
  height: 56rpx;
  border-radius: 9999px;
  background: var(--color-border-input); /* 关态轨道色（简体中文） */
  transition: background 0.2s ease;
  flex-shrink: 0;
  overflow: hidden;
}
.profile-page__lang-switch--on {
  background: var(--color-wechat); /* 开态轨道色（随主题代表色，English） */
}
.profile-page__lang-knob {
  position: absolute;
  top: 4rpx;
  left: 4rpx;
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: var(--color-text-inverse); /* 白色滑块 */
  transition: transform 0.2s ease;
  z-index: 0;
}
.profile-page__lang-switch--on .profile-page__lang-knob {
  transform: translateX(120rpx);
}
.profile-page__lang-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end; /* 关态旋钮在左，文字靠右避开圆点 */
  padding-right: 16rpx;
  box-sizing: border-box;
  font-size: 24rpx;
  line-height: 1;
  font-weight: 500;
  color: var(--color-text-secondary); /* 关态文字色（简体中文） */
  transition: color 0.2s ease;
  z-index: 1;
  pointer-events: none;
}
.profile-page__lang-switch--on .profile-page__lang-text {
  justify-content: flex-start; /* 开态旋钮在右，文字靠左避开圆点 */
  padding-right: 0;
  padding-left: 16rpx;
  color: var(--color-text-inverse); /* 开态文字色（English，白字） */
}

/* ===== 动态表单区域 ===== */
.profile-page__form-section {
  padding: 24rpx 32rpx;
  box-sizing: border-box;
  background: var(--color-surface-form);
}

.profile-page__form-field {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-bottom: 24rpx;
}

.profile-page__form-label {
  color: var(--color-label);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.profile-page__input {
  height: 88rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  background: var(--color-card-bg);
  border-radius: 16rpx;
  border: 1px solid var(--color-border-input);
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 42rpx;
}

.profile-page__input--error {
  border-color: var(--color-form-error);
}

/* 密码行：统一边框容器，内含输入框与眼睛图标 */
.profile-page__password-row {
  position: relative;
  display: flex;
  align-items: stretch;
  border: 1px solid var(--color-border-input);
  border-radius: 16rpx;
  background: var(--color-card-bg);
}

.profile-page__password-row:focus-within {
  border-color: var(--color-text-secondary);
}

.profile-page__password-row--error {
  border-color: var(--color-form-error);
}

.profile-page__input--password {
  flex: 1;
  border: none;
  background-color: transparent;
  border-radius: 16rpx 0 0 16rpx;
  padding-right: 24rpx;
}

.profile-page__eye {
  flex: none;
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 24rpx;
  border-radius: 0 16rpx 16rpx 0;
}

.profile-page__input--code {
  flex: 1;
}

.profile-page__placeholder {
  color: var(--color-text-secondary);
  font-size: 28rpx;
}

.profile-page__error-text {
  color: var(--color-form-error);
  font-size: 24rpx;
  line-height: 32rpx;
}

/* 字符限制提示文字 */
.profile-page__limit-text {
  color: var(--color-warning);
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
  border: 1px solid var(--color-border-input);
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.profile-page__code-btn--disabled {
  opacity: 0.6;
}

.profile-page__code-btn-text {
  color: var(--color-text-primary);
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
  background: var(--color-btn-cancel-bg);
  color: var(--color-text-primary);
}

.profile-page__btn--submit {
  background: var(--color-brand);
  color: var(--color-text-inverse);
}

.profile-page__btn-text {
  color: inherit;
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

/* ===== 主题选择列表 ===== */
.profile-page__theme-list {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 24rpx;
  padding: 16rpx 0;
}

.profile-page__theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 20rpx 16rpx;
  box-sizing: border-box;
  border-radius: 20rpx;
  border: 2px solid transparent;
  background: var(--color-surface-hover);
}

.profile-page__theme-option--selected {
  border-color: var(--color-brand-bg);
  background: var(--color-selected-bg);
}

.profile-page__theme-swatch {
  width: 96rpx;
  height: 96rpx;
  border-radius: 16rpx;
  box-shadow: var(--shadow-card);
}

.profile-page__theme-name {
  color: var(--color-text-primary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 500;
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
  background: var(--color-surface-hover);
}

.profile-page__avatar-option--selected {
  border-color: var(--color-brand-bg);
  background: var(--color-selected-bg);
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

  /* 语言切换开关（平板锁定，避免 rpx 过度放大） */
  .profile-page__lang-switch {
    width: 88px;
    height: 28px;
  }

  .profile-page__lang-knob {
    top: 2px;
    left: 2px;
    width: 24px;
    height: 24px;
  }

  .profile-page__lang-switch--on .profile-page__lang-knob {
    transform: translateX(60px);
  }

  .profile-page__lang-text {
    font-size: 12px;
    padding-right: 8px;
  }

  .profile-page__lang-switch--on .profile-page__lang-text {
    padding-right: 0;
    padding-left: 8px;
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

  /* 密码行 */
  .profile-page__input--password {
    padding-right: 12px;
  }

  .profile-page__eye {
    padding: 0 12px;
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

  /* 主题选择列表 */
  .profile-page__theme-list {
    gap: 12px;
    padding: 8px 0;
  }

  .profile-page__theme-option {
    gap: 6px;
    padding: 10px 8px;
    border-radius: 10px;
  }

  .profile-page__theme-swatch {
    width: 48px;
    height: 48px;
    border-radius: 8px;
  }

  .profile-page__theme-name {
    font-size: 14px;
    line-height: 20px;
  }
}
</style>
