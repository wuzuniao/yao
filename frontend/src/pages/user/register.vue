<template>
  <view class="register-page">
    <!-- 顶部通知按钮（复用项目通知组件，非导航栏） -->
    <NoticeButton :has-notification="hasNotification" />

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
              v-model="form.username"
              placeholder="请输入用户名"
              placeholder-class="register-page__placeholder"
              :placeholder-style="phStyle('username')"
              @focus="onFocus('username')"
              @blur="onBlur"
            />
          </view>

          <!-- 密码 -->
          <view class="register-page__field">
            <text class="register-page__label">密码</text>
            <input
              class="register-page__input"
              v-model="form.password"
              :password="true"
              placeholder="请设置强密码"
              placeholder-class="register-page__placeholder"
              :placeholder-style="phStyle('password')"
              @focus="onFocus('password')"
              @blur="onBlur"
            />
          </view>

          <!-- 确认密码 -->
          <view class="register-page__field">
            <text class="register-page__label">确认密码</text>
            <input
              class="register-page__input"
              v-model="form.confirmPassword"
              :password="true"
              placeholder="请再次输入密码"
              placeholder-class="register-page__placeholder"
              :placeholder-style="phStyle('confirmPassword')"
              @focus="onFocus('confirmPassword')"
              @blur="onBlur"
            />
          </view>

          <!-- 电子邮箱 -->
          <view class="register-page__field">
            <text class="register-page__label">电子邮箱</text>
            <input
              class="register-page__input"
              v-model="form.email"
              placeholder="请输入邮箱地址"
              placeholder-class="register-page__placeholder"
              :placeholder-style="phStyle('email')"
              @focus="onFocus('email')"
              @blur="onBlur"
            />
          </view>

          <!-- 验证码 -->
          <view class="register-page__field">
            <text class="register-page__label">验证码</text>
            <view class="register-page__code-row">
              <input
                class="register-page__code-input"
                v-model="form.code"
                placeholder="请输入验证码"
                placeholder-class="register-page__placeholder"
                :placeholder-style="phStyle('code')"
                @focus="onFocus('code')"
                @blur="onBlur"
              />
              <view class="register-page__code-btn" @click="handleGetCode">
                <text class="register-page__code-btn-text">{{ codeText }}</text>
              </view>
            </view>
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
 * 功能：新用户账号注册
 *  - 表单字段：用户名、密码、确认密码、电子邮箱、验证码
 *  - 验证码：60 秒倒计时，防止重复发送
 *  - 协议勾选：必须勾选《隐私政策》才能注册（点击文本跳转 privacy.vue）
 *  - 注册按钮：校验字段完整性 + 两次密码一致性 + 协议勾选状态
 *  - 底部提供登录入口，跳转 login.vue
 * 输入框 placeholder 聚焦交互复用 composables/usePlaceholder.js
 */
import { reactive, ref } from 'vue'
import NoticeButton from '../../components/NoticeButton.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'

// 设计稿顶栏铃铛为绿色无红点态
const hasNotification = false

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  code: ''
})

const agreed = ref(false)
const codeText = ref('获取验证码')
const counting = ref(false)

// 输入框 placeholder 聚焦交互：聚焦变浅灰 #c0c0c0，失焦恢复 placeholder-class 原始色
const { onFocus, onBlur, phStyle } = usePlaceholder()

function toggleAgree() {
  agreed.value = !agreed.value
}

function handleGetCode() {
  if (counting.value) return
  if (!form.email) {
    uni.showToast({ title: '请先输入邮箱', icon: 'none' })
    return
  }
  uni.showToast({ title: '验证码已发送', icon: 'none' })
  // 60 秒倒计时
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

function handleRegister() {
  if (!form.username || !form.password || !form.confirmPassword || !form.email || !form.code) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }
  if (form.password !== form.confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }
  if (!agreed.value) {
    uni.showToast({ title: '请同意隐私政策', icon: 'none' })
    return
  }
  uni.showToast({ title: '注册成功', icon: 'success' })
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
.register-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.register-page__canvas {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与卡片重叠 */
  padding: 100px 24px 36px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

/* ===== 白色卡片容器 ===== */
.register-page__card {
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

/* ===== 标题区 ===== */
.register-page__header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.register-page__title {
  color: #0e0f0c;
  font-size: 32px;
  line-height: 36px;
  font-weight: 600;
  text-align: center;
}

.register-page__subtitle {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
  text-align: center;
}

/* ===== 注册表单 ===== */
.register-page__form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.register-page__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.register-page__label {
  color: #0e0f0c;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.register-page__input {
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

.register-page__placeholder {
  color: #454745;
  font-size: 16px;
}

/* ===== 验证码行 ===== */
.register-page__code-row {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.register-page__code-input {
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

.register-page__code-btn {
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

.register-page__code-btn-text {
  color: #0e0f0c;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

/* ===== 协议勾选 ===== */
.register-page__agree {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
}

.register-page__checkbox {
  width: 16px;
  height: 16px;
  border-radius: 4px;
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
  width: 5px;
  height: 8px;
  border-right: 1.5px solid #ffffff;
  border-bottom: 1.5px solid #ffffff;
  transform: rotate(45deg) translate(-1px, -1px);
}

.register-page__agree-text {
  color: #454745;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
}

/* 《隐私政策》可点击链接：与同行文本样式一致，点击触发跳转 */
.register-page__agree-link {
  color: #454745;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
}

/* ===== 注册按钮 ===== */
.register-page__submit {
  height: 48px;
  padding: 12px 0;
  box-sizing: border-box;
  background: #9fe870;
  border-radius: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.register-page__submit-text {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

/* ===== 底部登录链接 ===== */
.register-page__footer {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.register-page__footer-text {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}
</style>
