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
            <text class="help-page__card-title">如何修改打卡时间？</text>
            <text class="help-page__card-text">在首页点击对应的习惯卡片进入详情页。点{{ '\n' }}击右上角的“设置”图标，即可在“打卡时间”选{{ '\n' }}项中重新设定您的专属时间。</text>
          </view>
        </view>

        <!-- Card 2 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">如何添加多个时间段？</text>
            <text class="help-page__card-text">创建或编辑习惯时，在时间设置模块下方点{{ '\n' }}击“+ 添加时间段”按钮。您可以为同一个习{{ '\n' }}惯（例如：喝水）设定早、中、晚多个独立{{ '\n' }}提醒。</text>
          </view>
        </view>

        <!-- Card 3 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">通知收不到怎么办？</text>
            <text class="help-page__card-text">首先，请确保在手机系统的“设置”中已允许{{ '\n' }}本应用发送通知。其次，进入应用内的“设置{{ '\n' }}> 通知中心”，检查是否开启了总开关及对应{{ '\n' }}习惯的提醒开关。</text>
          </view>
        </view>

        <!-- Card 4 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">可以恢复误删的记录吗？</text>
            <text class="help-page__card-text">非常抱歉，出于严格的隐私保护机制，一旦{{ '\n' }}您确认删除单条打卡记录，数据将从本地和{{ '\n' }}云端永久抹除，无法进行恢复操作。</text>
          </view>
        </view>

        <!-- Card 5 -->
        <view class="help-page__card">
          <view class="help-page__card-body">
            <text class="help-page__card-title">如何导出我的历史数据？</text>
            <text class="help-page__card-text">前往应用的“设置”页面，找到“数据与隐私”选{{ '\n' }}项卡。点击“导出数据报表”，系统将打包您{{ '\n' }}的所有记录，并发送至您绑定的电子邮箱。</text>
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
  padding: 100px 24px 32px;
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
