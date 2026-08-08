<template>
  <view :data-theme="themeKey" class="privacy-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="privacy-page__container">
      <!-- 标题区 -->
      <view class="privacy-page__heading">
        <text class="privacy-page__title">{{ $t('agreementDoc.title') }}</text>
      </view>

      <!-- 前言 -->
      <view class="privacy-page__intro">
        <text class="privacy-page__intro-text">{{ $t('agreementDoc.intro1') }}<text class="privacy-page__em">{{ $t('agreementDoc.intro1Em') }}</text>{{ $t('agreementDoc.intro1b') }}

{{ $t('agreementDoc.intro2') }}<text class="privacy-page__em">{{ $t('agreementDoc.intro2Em') }}</text>{{ $t('agreementDoc.intro2b') }}

{{ $t('agreementDoc.intro3') }}</text>
      </view>

      <!-- 主内容卡片 -->
      <view class="privacy-page__card">
        <!-- 一、协议的确认与接纳 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c1Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c1p1') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c1p2') }}<text class="privacy-page__em">{{ $t('agreementDoc.c1p2Em') }}</text>{{ $t('agreementDoc.c1p2b') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c1p3') }}<text class="privacy-page__em">{{ $t('agreementDoc.c1p3Em') }}</text>{{ $t('agreementDoc.c1p3b') }}</text>
        </view>

        <!-- 二、账号注册与使用资格 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c2Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c2p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c2p1Em') }}</text>{{ $t('agreementDoc.c2p1b') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('agreementDoc.c2l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('agreementDoc.c2l2') }}<text class="privacy-page__em">{{ $t('agreementDoc.c2l2Em') }}</text>{{ $t('agreementDoc.c2l2b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('agreementDoc.c2l3') }}</text>
            </view>
          </view>
        </view>

        <!-- 三、服务内容与形式 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c3Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c3p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c3p1Em') }}</text>{{ $t('agreementDoc.c3p1b') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c3p2') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('agreementDoc.c3p3Em') }}</text>{{ $t('agreementDoc.c3p3b') }}<text class="privacy-page__em">{{ $t('agreementDoc.c3p3Em2') }}</text>{{ $t('agreementDoc.c3p3b2') }}</text>
        </view>

        <!-- 四、用户行为规范 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c4Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c4p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c4p1Em') }}</text>{{ $t('agreementDoc.c4p1b') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('agreementDoc.c4l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('agreementDoc.c4l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('agreementDoc.c4l3') }}</text>
            </view>
          </view>
          <text class="privacy-page__para">{{ $t('agreementDoc.c4p2') }}<text class="privacy-page__em">{{ $t('agreementDoc.c4p2Em') }}</text>{{ $t('agreementDoc.c4p2b') }}</text>
        </view>

        <!-- 五、知识产权 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c5Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c5p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c5p1Em') }}</text>{{ $t('agreementDoc.c5p1b') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c5p2') }}<text class="privacy-page__em">{{ $t('agreementDoc.c5p2Em') }}</text>{{ $t('agreementDoc.c5p2b') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c5p3') }}<text class="privacy-page__em">{{ $t('agreementDoc.c5p3Em') }}</text>{{ $t('agreementDoc.c5p3b') }}</text>
        </view>

        <!-- 六、个人信息保护 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c6Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c6p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c6p1Em') }}</text>{{ $t('agreementDoc.c6p1b') }}</text>
        </view>

        <!-- 七、免责声明 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c7Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c7p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c7p1Em') }}</text>{{ $t('agreementDoc.c7p1b') }}<text class="privacy-page__em">{{ $t('agreementDoc.c7p1Em2') }}</text>{{ $t('agreementDoc.c7p1b2') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c7p2') }}<text class="privacy-page__em">{{ $t('agreementDoc.c7p2Em') }}</text>{{ $t('agreementDoc.c7p2b') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c7p3') }}<text class="privacy-page__em">{{ $t('agreementDoc.c7p3Em') }}</text>{{ $t('agreementDoc.c7p3b') }}</text>
        </view>

        <!-- 八、违约处理 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c8Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c8p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c8p1Em') }}</text>{{ $t('agreementDoc.c8p1b') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c8p2') }}<text class="privacy-page__em">{{ $t('agreementDoc.c8p2Em') }}</text>{{ $t('agreementDoc.c8p2b') }}</text>
        </view>

        <!-- 九、服务的变更、中断与终止 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c9Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c9p1') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c9p2') }}<text class="privacy-page__em">{{ $t('agreementDoc.c9p2Em') }}</text>{{ $t('agreementDoc.c9p2b') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c9p3') }}<text class="privacy-page__em">{{ $t('agreementDoc.c9p3Em') }}</text>{{ $t('agreementDoc.c9p3b') }}</text>
        </view>

        <!-- 十、第三方服务 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c10Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c10p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c10p1Em') }}</text>{{ $t('agreementDoc.c10p1b') }}<text class="privacy-page__em">{{ $t('agreementDoc.c10p1Em2') }}</text>{{ $t('agreementDoc.c10p1b2') }}</text>
        </view>

        <!-- 十一、协议变更 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c11Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c11p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c11p1Em') }}</text>{{ $t('agreementDoc.c11p1b') }}</text>
        </view>

        <!-- 十二、争议解决与管辖 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c12Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c12p1') }}<text class="privacy-page__em">{{ $t('agreementDoc.c12p1Em') }}</text>{{ $t('agreementDoc.c12p1b') }}<text class="privacy-page__em">{{ $t('agreementDoc.c12p1Em2') }}</text>{{ $t('agreementDoc.c12p1b2') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c12p2') }}<text class="privacy-page__em">{{ $t('agreementDoc.c12p2Em') }}</text>{{ $t('agreementDoc.c12p2b') }}</text>
        </view>

        <!-- 十三、联系我们 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('agreementDoc.c13Title') }}</text>
          <text class="privacy-page__para">{{ $t('agreementDoc.c13p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('agreementDoc.c13l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('agreementDoc.c13l2') }}</text>
            </view>
          </view>
          <text class="privacy-page__para privacy-page__para--footer">{{ $t('agreementDoc.c13footer') }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 服务协议页面（agreement.vue）
 * --------------------------------------------------------------------------
 * 功能：展示《服务协议》全文，与隐私政策页（privacy.vue）布局完全一致。
 *  - 覆盖端：微信小程序 / H5 / App（Android、iOS、HarmonyOS）共 5 个发行版本
 *  - 标题区 + 前言（同意机制说明）
 *  - 协议正文共 13 章：协议确认与接纳、账号注册与使用资格、服务内容与形式、
 *    用户行为规范、知识产权、个人信息保护、免责声明、违约处理、
 *    服务的变更中断与终止、第三方服务、协议变更、争议解决与管辖、联系我们
 *  - 纯展示页面，无交互逻辑
 *  - 布局与类名完全复用 privacy.vue，仅文案不同；重点条款用嵌套
 *    <text class="privacy-page__em"> 加粗强调（微信小程序不支持 HTML 加粗标签）
 *  - themeKey 由 main.js 全局 mixin 注入，模板直接绑定 :data-theme
 */
import BackButton from '../../components/BackButton.vue'
import { useShare } from '../../composables/useShare'
import { t } from '../../locale'

useShare({ title: t('share.agreement') })
</script>

<style lang="scss">
/* 样式完全复用 privacy.vue 的 .privacy-page 同名规则，确保两页视觉一致 */
.privacy-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.privacy-page__container {
  padding: 210rpx 32rpx 96rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.privacy-page__heading {
  padding: 16rpx 0 32rpx;
}

.privacy-page__title {
  color: var(--color-text-primary);
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
}

.privacy-page__intro {
  padding-bottom: 32rpx;
}

.privacy-page__intro-text {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  white-space: pre-line;
}

/* 微信小程序端：主内容卡片外侧加留白，避免与导航胶囊/状态栏顶栏过近 */
.privacy-page__card {
  padding: 48rpx;
  box-sizing: border-box;
  background: var(--color-card-bg);
  border-radius: 48rpx;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 64rpx;
}

.privacy-page__section {
  display: flex;
  flex-direction: column;
}

.privacy-page__section-title {
  color: var(--color-text-primary);
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 600;
  padding-bottom: 24rpx;
  white-space: pre-line;
}

.privacy-page__para {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  padding-bottom: 32rpx;
  white-space: pre-line;
}

.privacy-page__para--footer {
  padding-top: 32rpx;
}

.privacy-page__em {
  color: var(--color-text-primary);
  font-weight: 600;
}

.privacy-page__sub-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
}

.privacy-page__list {
  padding: 0 0 32rpx 40rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.privacy-page__list-item {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
}

.privacy-page__bullet {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  width: 14rpx;
  flex-shrink: 0;
}

.privacy-page__list-text {
  flex: 1;
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  white-space: pre-line;
}

/* 平板/折叠屏断点（≥768px）：rpx 会过度放大，关键尺寸锁定为 px */
@media screen and (min-width: 768px) {
  .privacy-page__container {
    padding: 105px 16px 48px;
  }
  .privacy-page__heading {
    padding: 8px 0 16px;
  }
  .privacy-page__title {
    font-size: 32px;
    line-height: 36px;
  }
  .privacy-page__intro {
    padding-bottom: 16px;
  }
  .privacy-page__intro-text {
    font-size: 16px;
    line-height: 24px;
  }
  .privacy-page__card {
    padding: 24px;
    border-radius: 24px;
    gap: 32px;
  }
  .privacy-page__section-title {
    font-size: 24px;
    line-height: 32px;
    padding-bottom: 12px;
  }
  .privacy-page__para {
    font-size: 16px;
    line-height: 24px;
    padding-bottom: 16px;
  }
  .privacy-page__para--footer {
    padding-top: 16px;
  }
  .privacy-page__sub-title {
    font-size: 16px;
    line-height: 24px;
    padding-bottom: 8px;
  }
  .privacy-page__list {
    padding: 0 0 16px 20px;
    gap: 8px;
  }
  .privacy-page__bullet {
    font-size: 16px;
    line-height: 24px;
    width: 7px;
  }
  .privacy-page__list-text {
    font-size: 16px;
    line-height: 24px;
  }
}
</style>
