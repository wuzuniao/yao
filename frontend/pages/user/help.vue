<template>
  <view :data-theme="themeKey" class="help-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="help-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/notification 等页面保持一致） -->
      <PageHeader :title="$t('help.title')" :desc="$t('help.desc')" />

      <!-- FAQ 卡片列表 -->
      <view class="help-page__list">
        <!-- Card 1 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">{{ $t('help.q1Title') }}</text>
            <text class="help-page__card-text">{{ $t('help.q1Text') }}</text>
          </view>
        </view>

        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">{{ $t('help.q2Title') }}</text>
            <text class="help-page__card-text">{{ $t('help.q2Text1') }}</text>
            <text class="help-page__card-text">{{ $t('help.q2Text2') }}</text>
            <text class="help-page__card-text">{{ $t('help.q2Text3') }}</text>
          </view>
        </view>

        <!-- Card 2 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">{{ $t('help.q3Title') }}</text>
            <text class="help-page__card-text">{{ $t('help.q3Text') }}<text class="help-page__card-link" @click="copySmtpLink">{{ $t('help.q3Link') }}</text></text>
          </view>
        </view>

        <!-- Card 3 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">{{ $t('help.q4Title') }}</text>
            <text class="help-page__card-text">{{ $t('help.q4Text') }}</text>
          </view>
        </view>

        <!-- Card 4 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">{{ $t('help.q5Title') }}</text>
            <text class="help-page__card-text">{{ $t('help.q5Text1') }}</text>
            <text class="help-page__card-text">{{ $t('help.q5Text2') }}</text>
          </view>
        </view>

        <!-- Card 5 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">{{ $t('help.q6Title') }}</text>
            <text class="help-page__card-text">{{ $t('help.q6Text1') }}</text>
            <text class="help-page__card-text">{{ $t('help.q6Text2') }}</text>
            <text class="help-page__card-text">{{ $t('help.q6Text3') }}</text>
            <text class="help-page__card-text">{{ $t('help.q6Text4') }}</text>
            <text class="help-page__card-text">{{ $t('help.q6Text5') }}</text>
          </view>
        </view>

        <!-- Card 6 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">{{ $t('help.q7Title') }}</text>
            <text class="help-page__card-text">{{ $t('help.q7Text1') }}</text>
            <text class="help-page__card-text">{{ $t('help.q7Text2') }}</text>
            <text class="help-page__card-text">{{ $t('help.q7Text3') }}</text>
            <text class="help-page__card-text">{{ $t('help.q7Text4') }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 帮助中心页（help.vue）
 * --------------------------------------------------------------------------
 * 功能：展示常见问题解答（FAQ）列表
 *  - 5 张 FAQ 卡片：修改打卡时间、添加多个时间段、通知收不到、恢复误删记录、导出历史数据
 *  - 纯展示页面，无交互逻辑，内容为静态文案
 */
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { useShare } from '../../composables/useShare'
import { t } from '../../locale'

useShare({ title: t('share.help') })

// 复制 SMTP 配置教程链接到剪贴板
function copySmtpLink() {
  const url = 'https://mp.weixin.qq.com/s/JNOseGYNjaFxWcTpERXnTQ'
  uni.setClipboardData({
    data: url,
    success: () => {
      uni.showToast({ title: t('common.copySuccess'), icon: 'success' })
    },
    fail: () => {
      uni.showToast({ title: t('common.copyFailed'), icon: 'none' })
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
.help-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

/* ===== 主内容画布（对应设计稿 Main Content Canvas）===== */
.help-page__canvas {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 210rpx 48rpx 64rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
  min-height: 100vh;
}

/* ===== FAQ 卡片列表（对应设计稿 FAQ Cards List）===== */
.help-page__list {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

/* ===== 单张 FAQ 卡片（对应设计稿 Card 1~5）===== */
.help-page__card {
  padding: 32rpx;
  box-sizing: border-box;
  background: var(--color-card-bg);
  border-radius: 24rpx;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
}

.help-page__card-body {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.help-page__card-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 700;
}

.help-page__card-text {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 52rpx;
  font-weight: 400;
  white-space: pre-line;
}

.help-page__card-link {
  color: var(--color-link);
  text-decoration: underline;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 */
@media screen and (min-width: 768px) {
  .help-page__canvas {
    padding: 105px 24px 32px;
    gap: 32px;
  }
  .help-page__list {
    gap: 16px;
  }
  .help-page__card {
    padding: 16px;
    border-radius: 12px;
  }
  .help-page__card-body {
    gap: 4px;
  }
  .help-page__card-title {
    font-size: 16px;
    line-height: 24px;
    font-weight: 700;
  }
  .help-page__card-text {
    font-size: 16px;
    line-height: 26px;
  }
}
</style>
