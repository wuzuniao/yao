<template>
  <view class="help-page">
    <!-- 顶部通知按钮（复用项目通知组件，非导航栏） -->
    <NoticeButton :has-notification="hasNotification" />

    <view class="help-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 plan/notification 等页面保持一致） -->
      <PageHeader title="帮助中心" :desc="`找到常见问题的解答，或了解如何更好地管理${'\n'}您的习惯。`" />

      <!-- FAQ 卡片列表 -->
      <view class="help-page__list">
        <!-- Card 1 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">小程序的主要用途是什么？</text>
            <text class="help-page__card-text">一个通用任务的定时打卡提醒小程序。</text>
          </view>
        </view>

        <!-- Card 2 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">邮件通知怎么填写？</text>
            <text class="help-page__card-text">参考文章：QQ邮箱中开通SMTP服务并获取授权码{{ '\n' }}</text>
          </view>
        </view>

        <!-- Card 3 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">邮件通知怎么第一时间知道？</text>
            <text class="help-page__card-text">微信搜索“QQ邮箱提醒”，绑定自己的邮件后，有邮件会弹消息。</text>
          </view>
        </view>

        <!-- Card 4 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">为什么邮件通知要配置自己的邮箱客户端专用密码？</text>
            <text class="help-page__card-text">因为要用你的邮箱给你自己发信，保证邮件内容安全，还可以避免邮件被当垃圾邮件拦截。{{ '\n' }}邮箱客户端专用密码在数据库中已被再次加密存储，且不会通过接口返回给前端。</text>
          </view>
        </view>

        <!-- Card 5 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">打卡逻辑如何设置的？</text>
            <text class="help-page__card-text">只允许在打卡日期范围内进行打卡。{{ '\n' }}未到打卡时间：打卡按钮为“未到打卡时间”。{{ '\n' }}只有一次提醒时间时：提前一小时打卡按钮会变为“立即打卡”，此时允许打卡。{{ '\n' }}当存在多个提醒时间且两次打卡间隔大于两小时时：提前一小时打卡按钮会变为“立即打卡”，此时允许打卡。{{ '\n' }}当存在多个提醒时间且两次打卡间隔在两小时以下时：两次提醒时间的间隔时间中，前半部分时间为已完成，后半部分时间重置按钮为"立即打卡"，此时允许打卡。{{ '\n' }}当任何时候需要打卡，可长按任何非“立即打卡”按钮3秒，会重置按钮为"立即打卡"，此时允许打卡。</text>
          </view>
        </view>

        <!-- Card 6 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">通知逻辑如何设置的？</text>
            <text class="help-page__card-text">只有一次提醒时间时：到达打卡计划的通知时间，且当前打卡计划在当天未打卡的，发送通知。{{ '\n' }}当存在多个提醒时间时：到达打卡计划的通知时间，且当前打卡计划在当天的打卡记录数量小于提醒时间数量时，发送通知。{{ '\n' }}当超过提醒时间5分钟、30分钟、1小时，依旧没有打卡记录时，在对应时间点发送通知。</text>
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
import NoticeButton from '../../components/NoticeButton.vue'
import PageHeader from '../../components/PageHeader.vue'

// 设计稿顶栏图标为绿色无红点态
const hasNotification = false
</script>

<style lang="scss">
.help-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

/* ===== 主内容画布（对应设计稿 Main Content Canvas）===== */
.help-page__canvas {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 105px 24px 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
  min-height: 100vh;
}

/* ===== FAQ 卡片列表（对应设计稿 FAQ Cards List）===== */
.help-page__list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== 单张 FAQ 卡片（对应设计稿 Card 1~5）===== */
.help-page__card {
  padding: 16px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.help-page__card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.help-page__card-title {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 600;
}

.help-page__card-text {
  color: #454745;
  font-size: 16px;
  line-height: 26px;
  font-weight: 400;
  white-space: pre-line;
}
</style>
