<template>
  <view class="contact-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="contact-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/notification 等页面保持一致） -->
      <PageHeader title="联系我们" desc="如果您在使用过程中遇到任何问题，欢迎随时联系我们。" />

      <!-- 白色卡片：联系方式列表 -->
      <view class="contact-page__card">
        <view class="contact-page__list">
          <!-- 客服邮箱 -->
          <view class="contact-page__item">
            <view class="contact-page__item-info">
              <text class="contact-page__item-label">客服邮箱</text>
              <text class="contact-page__item-value">xpg@wuzuniao.com</text>
            </view>
          </view>

          <!-- 微信公众号 -->
          <view class="contact-page__item">
            <view class="contact-page__item-info">
              <text class="contact-page__item-label">微信公众号</text>
              <text class="contact-page__item-value">无足鸟ICT</text>
              <view class="contact-page__qr-wrap">
                <view class="contact-page__qr-bg">
                  <image class="contact-page__qr-img" :src="wxIcon" mode="aspectFit" />
                </view>
              </view>
            </view>
          </view>

          <!-- QQ群 -->
          <view class="contact-page__item">
            <view class="contact-page__item-info">
              <text class="contact-page__item-label">QQ群</text>
              <text class="contact-page__item-value">278634838</text>
              <view class="contact-page__qr-wrap">
                <view class="contact-page__qr-bg">
                  <image class="contact-page__qr-img" :src="qqIcon" mode="aspectFit" />
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 联系我们页（contact.vue）
 * --------------------------------------------------------------------------
 * 功能：展示官方联系方式
 *  - 客服邮箱：xpg@wuzuniao.com
 *  - 微信公众号：无足鸟ICT（含二维码图片）
 *  - QQ群：278634838（含二维码图片）
 * 纯展示页面，无交互逻辑
 */
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import wxIcon from '../../assets/images/ewm_wx.png'
import qqIcon from '../../assets/images/ewm_qq.png'
import { useShare } from '../../composables/useShare'

useShare({ title: '联系我们' })
</script>

<style lang="scss">
.contact-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

/* ===== 主内容画布（对应设计稿 Main Content Canvas）===== */
.contact-page__canvas {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 105px 24px 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
  min-height: 100vh;
}

/* ===== 白色卡片（对应设计稿 Article）===== */
.contact-page__card {
  padding: 24px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* ===== 联系方式列表（对应设计稿 Contact Details List）===== */
.contact-page__list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ===== 单个联系项 ===== */
.contact-page__item {
  display: flex;
  flex-direction: row;
}

.contact-page__item-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.contact-page__item-label {
  color: #5e5f5a;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.contact-page__item-value {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}

/* ===== 二维码区（对应设计稿 Margin + Background 140x140）===== */
.contact-page__qr-wrap {
  padding-top: 12px;
}

.contact-page__qr-bg {
  width: 140px;
  height: 140px;
  background: #f3f3f4;
  border-radius: 8px;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
}

.contact-page__qr-img {
  width: 140px;
  height: 140px;
}
</style>
