<template>
  <view :data-theme="themeKey" class="delete-account-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="delete-account-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 contact/help 等页面保持一致） -->
      <PageHeader title="账号删除与数据说明" desc="了解如何删除您的账号及与之相关的数据处理方式。本说明页无需登录即可访问。" />

      <!-- 白色卡片：说明正文 -->
      <view class="delete-account-page__card">
        <view class="delete-account-page__list">
          <!-- 1. 两种删除途径 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">一、如何删除账号</text>
            <text class="delete-account-page__item-text">您可以通过以下任一途径自助申请注销账号并删除全部数据，两条途径效果完全相同：</text>
            <view class="delete-account-page__sub">
              <text class="delete-account-page__sub-label">应用内：</text>
              <text class="delete-account-page__sub-text">打开本产品，进入「设置 - 个人信息」页面，点击底部的「删除账号」。</text>
            </view>
            <view class="delete-account-page__sub">
              <text class="delete-account-page__sub-label">网页端：</text>
              <text class="delete-account-page__sub-text">访问 yao.wuzuniao.com/pages/user/profile ，登录后点击「删除账号」即可。</text>
            </view>
            <view class="delete-account-page__btn" @click="goLogin">
              <text class="delete-account-page__btn-text">前往网页端登录后删除</text>
            </view>
          </view>

          <!-- 2. 冷静期 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">二、24 小时冷静期</text>
            <text class="delete-account-page__item-text">申请提交后，您的账号立即被冻结、全部登录令牌立即失效。系统提供 24 小时冷静期，期间您可以重新登录并撤销注销申请，撤销后账号恢复正常。冷静期届满后，系统将自动彻底删除您的数据且不可恢复。</text>
          </view>

          <!-- 3. 删除范围 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">三、将被删除的数据</text>
            <text class="delete-account-page__item-text">冷静期届满后，以下数据将被物理删除且不可恢复：账号主记录（用户名、邮箱、密码哈希、个性签名、头像标识）、微信绑定关系（OpenID）、全部打卡计划及其提醒时间点与渠道绑定、全部打卡记录、全部通知渠道配置（含加密的邮箱密码与设备推送标识）、全部通知发送记录。</text>
            <text class="delete-account-page__item-text">删除为直接物理删除，我们不保留您数据的备份副本或匿名化残留；仅服务器访问日志中可能残留请求 IP 与时间戳，该日志不含您的账号内容。</text>
          </view>

          <!-- 4. 不可删除的部分 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">四、依法须保留的部分</text>
            <text class="delete-account-page__item-text">如法律法规另有强制保存期限规定，超出前述删除范围的部分将在法定期限届满后再行删除，期间依法限制其使用。</text>
          </view>

          <!-- 5. 其他权利 -->
          <view class="delete-account-page__item">
            <text class="delete-account-page__item-title">五、其他个人信息权利</text>
            <text class="delete-account-page__item-text">除删除账号外，您还享有查阅、复制、更正、补充个人信息以及撤回同意等权利。如需通过邮件行使上述权利，请发送邮件至 xpg@wuzuniao.com，我们将在核验身份后于十五个工作日内响应。更多说明详见《隐私政策》与《服务协议》。</text>
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

useShare({ title: '账号删除与数据说明' })

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
