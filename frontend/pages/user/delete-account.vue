<template>
  <view :data-theme="themeKey" class="delete-account-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="delete-account-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 contact/help 等页面保持一致） -->
      <PageHeader :title="$t('deleteAccount.title')" :desc="$t('deleteAccount.desc')" />

      <!-- 白色卡片：说明正文 -->
      <view class="delete-account-page__card">
        <view class="delete-account-page__list">
          <!-- 1. 两种删除途径 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">{{ $t('deleteAccount.s1Title') }}</text>
            <text class="delete-account-page__item-text">{{ $t('deleteAccount.s1Text') }}</text>
            <view class="delete-account-page__sub">
              <text class="delete-account-page__sub-label">{{ $t('deleteAccount.s1InAppLabel') }}</text>
              <text class="delete-account-page__sub-text">{{ $t('deleteAccount.s1InAppText') }}</text>
            </view>
            <view class="delete-account-page__sub">
              <text class="delete-account-page__sub-label">{{ $t('deleteAccount.s1WebLabel') }}</text>
              <text class="delete-account-page__sub-text">{{ $t('deleteAccount.s1WebText') }}</text>
            </view>
            <view class="delete-account-page__btn" @click="goLogin">
              <text class="delete-account-page__btn-text">{{ $t('deleteAccount.s1Btn') }}</text>
            </view>
          </view>

          <!-- 2. 冷静期 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">{{ $t('deleteAccount.s2Title') }}</text>
            <text class="delete-account-page__item-text">{{ $t('deleteAccount.s2Text') }}</text>
          </view>

          <!-- 3. 删除范围 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">{{ $t('deleteAccount.s3Title') }}</text>
            <text class="delete-account-page__item-text">{{ $t('deleteAccount.s3Text1') }}</text>
            <text class="delete-account-page__item-text">{{ $t('deleteAccount.s3Text2') }}</text>
          </view>

          <!-- 4. 不可删除的部分 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">{{ $t('deleteAccount.s4Title') }}</text>
            <text class="delete-account-page__item-text">{{ $t('deleteAccount.s4Text') }}</text>
          </view>

          <!-- 5. 其他权利 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">{{ $t('deleteAccount.s5Title') }}</text>
            <text class="delete-account-page__item-text">{{ $t('deleteAccount.s5Text') }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 账号删除说明页（delete-account.vue）
 * --------------------------------------------------------------------------
 * 功能：免登录公开的账号删除与数据处理说明页
 *  - 满足 Google Play 账号删除政策对「可直接访问的网页端删除说明入口」要求
 *  - 纯静态说明，不依赖登录态；提供跳登录页 / 隐私政策 / 服务协议的入口
 *  - 覆盖：两种删除途径、24h 冷静期、删除范围、依法保留部分、其他权利
 *  - 布局/类名复用 contact.vue 风格，引用语义令牌保持单一配色真源
 */
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { useShare } from '../../composables/useShare'
import { t } from '../../locale'

useShare({ title: t('share.deleteAccount') })

function goLogin() {
  uni.navigateTo({ url: '/pages/user/login' })
}
</script>

<style lang="scss">
/* ==========================================================================
 * 响应式单位说明（px → rpx 转换）
 * 基准：375px 设计稿，1px = 2rpx；平板/折叠屏断点 ≥768px 锁定 px
 * ========================================================================== */
.delete-account-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.delete-account-page__canvas {
  padding: 210rpx 48rpx 64rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
  min-height: 100vh;
}

/* ===== 白色卡片 ===== */
.delete-account-page__card {
  padding: 48rpx;
  box-sizing: border-box;
  background: var(--color-card-bg);
  border-radius: 48rpx;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.delete-account-page__list {
  display: flex;
  flex-direction: column;
  gap: 48rpx;
}

.delete-account-page__item {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.delete-account-page__item-title {
  color: var(--color-text-primary);
  font-size: 36rpx;
  line-height: 52rpx;
  font-weight: 600;
}

.delete-account-page__item-text {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  white-space: pre-line;
}

.delete-account-page__sub {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  padding-left: 8rpx;
}

.delete-account-page__sub-label {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
}

.delete-account-page__sub-text {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  white-space: pre-line;
  word-break: break-all;
}

/* 跳转登录按钮 */
.delete-account-page__btn {
  margin-top: 8rpx;
  align-self: flex-start;
  height: 80rpx;
  padding: 0 40rpx;
  box-sizing: border-box;
  border-radius: 40rpx;
  background: var(--color-brand);
  display: flex;
  justify-content: center;
  align-items: center;
}

.delete-account-page__btn-text {
  color: var(--color-text-inverse);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 500;
}

/* ===== 平板/折叠屏断点（≥768px）===== */
@media screen and (min-width: 768px) {
  .delete-account-page__canvas {
    padding: 105px 24px 32px;
    gap: 32px;
  }
  .delete-account-page__card {
    padding: 24px;
    border-radius: 24px;
  }
  .delete-account-page__list {
    gap: 24px;
  }
  .delete-account-page__item {
    gap: 8px;
  }
  .delete-account-page__item-title {
    font-size: 18px;
    line-height: 26px;
  }
  .delete-account-page__item-text {
    font-size: 16px;
    line-height: 24px;
  }
  .delete-account-page__sub {
    gap: 4px;
    padding-left: 4px;
  }
  .delete-account-page__sub-label {
    font-size: 16px;
    line-height: 24px;
  }
  .delete-account-page__sub-text {
    font-size: 16px;
    line-height: 24px;
  }
  .delete-account-page__btn {
    height: 40px;
    padding: 0 20px;
    border-radius: 20px;
  }
  .delete-account-page__btn-text {
    font-size: 14px;
    line-height: 20px;
  }
}
</style>
