<template>
  <view class="help-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="help-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/notification 等页面保持一致） -->
      <PageHeader title="帮助中心" desc="找到常见问题的解答，或了解如何更好地管理您的习惯。" />

      <!-- FAQ 卡片列表 -->
      <view class="help-page__list">
        <!-- Card 1 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">小程序的主要用途是什么？</text>
            <text class="help-page__card-text">一个通用任务的定时打卡提醒小程序。</text>
          </view>
        </view>

        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">如何允许微信通知？</text>
            <text class="help-page__card-text">通知方式页面中，授权订阅消息「打卡提醒」，打卡计划中添加「微信」通知方式。</text>
            <text class="help-page__card-text">授权订阅消息通知后，勾选「总是保持以上选择」后，后续每次打卡时会静默+1次授权通知，且不再弹窗；也就是每次打卡自动+1次授权通知次数。不勾选则会弹窗提示。</text>
            <text class="help-page__card-text">可在通知方式页多次授权增加通知次数。</text>
          </view>
        </view>

        <!-- Card 2 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">邮件通知怎么填写？</text>
            <text class="help-page__card-text">参考公众号文章（无足鸟ICT）：<text class="help-page__card-link" @click="copySmtpLink">QQ邮箱中开通SMTP服务并获取授权码</text></text>
          </view>
        </view>

        <!-- Card 3 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">邮件通知怎么第一时间知道？</text>
            <text class="help-page__card-text">微信搜索“QQ邮箱提醒”，绑定自己的邮箱后，有邮件会弹消息。</text>
          </view>
        </view>

        <!-- Card 4 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">为什么邮件通知要配置自己的邮箱客户端专用密码？</text>
            <text class="help-page__card-text">因为要用你的邮箱给你自己发信，保证邮件内容安全，还可以避免邮件被当垃圾邮件拦截。</text>
            <text class="help-page__card-text">邮箱客户端专用密码在数据库中已被再次加密存储，且不会通过接口返回给前端。</text>
          </view>
        </view>

        <!-- Card 5 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">打卡逻辑如何设置的？</text>
            <text class="help-page__card-text">只允许在打卡日期范围内进行打卡。</text>
            <text class="help-page__card-text">未到打卡时间：打卡按钮为“未到打卡时间”。</text>
            <text class="help-page__card-text">提醒时间前后2小时，打卡按钮会变为“立即打卡”，此时允许打卡；已打卡则将打卡按钮变为“已打卡”。</text>
            <text class="help-page__card-text">当存在多个提醒时间时：取两个提醒时间的中间点，将间隔时间分为两段，分别进行是否打卡判断，未打卡则将打卡按钮会变为“立即打卡”，已打卡则将打卡按钮变为“已打卡”。</text>
            <text class="help-page__card-text">当需要打卡时，可长按“未到打卡时间”或“已打卡”按钮3秒，重置按钮为"立即打卡"，此时允许打卡。</text>
          </view>
        </view>

        <!-- Card 6 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">通知逻辑如何设置的？</text>
            <text class="help-page__card-text">只有一次提醒时间时：到达打卡计划的通知时间，且当前打卡计划在当天未打卡时，发送通知。</text>
            <text class="help-page__card-text">当存在多个提醒时间时：到达打卡计划的通知时间，且当前提醒时间的匹配范围内打卡记录数量小于1时，发送通知。</text>
            <text class="help-page__card-text">当超过提醒时间10分钟、1小时（或与下一次提醒时间的中间点，取先到的时间），依旧没有打卡记录时，发送通知。</text>
            <text class="help-page__card-text">微信通知次数足够时，会按照上面方式通知。进行打卡后才会增加一次通知次数，否则不再进行微信通知。</text>
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

useShare({ title: '帮助中心' })

// 复制 SMTP 配置教程链接到剪贴板
function copySmtpLink() {
  const url = 'https://mp.weixin.qq.com/s/JNOseGYNjaFxWcTpERXnTQ'
  uni.setClipboardData({
    data: url,
    success: () => {
      uni.showToast({ title: '链接已复制', icon: 'success' })
    },
    fail: () => {
      uni.showToast({ title: '复制失败', icon: 'none' })
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
  background: #ffffff;
  border-radius: 24rpx;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.help-page__card-body {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.help-page__card-title {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
}

.help-page__card-text {
  color: #454745;
  font-size: 32rpx;
  line-height: 52rpx;
  font-weight: 400;
  white-space: pre-line;
}

.help-page__card-link {
  color: #0066cc;
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
  }
  .help-page__card-text {
    font-size: 16px;
    line-height: 26px;
  }
}
</style>
