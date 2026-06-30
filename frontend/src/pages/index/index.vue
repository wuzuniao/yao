<template>
  <view class="index-page">
    <view class="index-page__frame">
      <NoticeButton :has-notification="hasNotification" />

      <view class="index-page__main-canvas">
        <view class="index-page__hero">
          <view class="index-page__primary-card">
            <view class="index-page__primary-copy">
              <text class="index-page__primary-title">按时吃药</text>
              <text class="index-page__primary-desc">让您的健康步入正轨。</text>
            </view>
            <view class="index-page__status-badge">
              <view class="index-page__status-dot"></view>
              <text class="index-page__status-text">进行中</text>
            </view>
          </view>

          <view class="index-page__secondary-card">
            <view class="index-page__secondary-copy">
              <text class="index-page__secondary-title">每日饮水</text>
              <text class="index-page__secondary-desc">下个提醒: 14:00</text>
            </view>
            <view class="index-page__secondary-button">
              <view class="index-page__secondary-button-line"></view>
            </view>
          </view>
        </view>

        <view class="index-page__checkin-shell">
          <view class="index-page__checkin-button">
            <image class="index-page__checkin-icon" :src="checkinIcon" mode="aspectFit" />
            <text class="index-page__checkin-text">立即打卡</text>
          </view>
        </view>
      </view>

      <BottomNav active="home" />
    </view>
  </view>
</template>

<script setup>
/**
 * 首页（index.vue）
 * --------------------------------------------------------------------------
 * 功能：应用主入口，展示用户当日打卡状态与快捷功能入口
 *  - 顶部通知按钮（NoticeButton）
 *  - Hero 区：今日打卡状态卡片，点击触发打卡（hasCheckedIn 切换图标）
 *  - 快捷入口：制定计划、打卡记录、通知方式、更多功能（入口卡点击跳转对应页面）
 *  - 底部固定导航栏（BottomNav），当前激活项为"首页"
 */
import NoticeButton from '../../components/NoticeButton.vue'
import BottomNav from '../../components/BottomNav.vue'
import checkinInactiveIcon from '../../assets/images/daka_0.png'
import checkinActiveIcon from '../../assets/images/daka_1.png'

const hasNotification = false
const hasCheckedIn = false

const checkinIcon = hasCheckedIn ? checkinActiveIcon : checkinInactiveIcon
</script>

<style lang="scss">
.index-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
}

.index-page__frame {
  position: relative;
  /* min-height 100vh + box-sizing border-box：含 padding-top 17px 不超出视口，消除底部空白滚动 */
  min-height: 100vh;
  padding-top: 17px;
  box-sizing: border-box;
}

.index-page__main-canvas {
  /* 去掉 min-height: 884px（强制撑高导致滚动），内容顶部位置 = frame 17px + 100px = 117px 保持不变 */
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  /* padding-bottom 120px：底部导航高 86 + bottom 15 = 101px，留 19px 余量避免遮挡 */
  padding: 100px 24px 120px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 66px;
}

.index-page__hero {
  width: 342px;
  padding-top: 32px;
  box-sizing: border-box;
}

.index-page__primary-card {
  position: relative;
  width: 342px;
  height: 141px;
  padding: 16px;
  box-sizing: border-box;
  border-radius: 32px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e2e2e2, 0 1px 2px rgba(0, 0, 0, 0.05);
}

.index-page__primary-copy {
  display: flex;
  flex-direction: column;
}

.index-page__primary-title {
  color: #0e0f0c;
  font-size: 24px;
  line-height: 32px;
  font-weight: 600;
}

.index-page__primary-desc {
  margin-top: 4px;
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}

.index-page__status-badge {
  position: absolute;
  top: 17px;
  right: 17px;
  height: 28px;
  padding: 4px 8px;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #9fe870;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.index-page__status-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #2ead4b;
}

.index-page__status-text {
  color: #2e6900;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
}

.index-page__secondary-card {
  margin-top: -32px;
  width: 342px;
  height: 85px;
  padding: 32px 16px 12px;
  box-sizing: border-box;
  border-radius: 0 0 32px 32px;
  background: #f3f3f4;
  box-shadow: inset 0 0 0 1px #e2e2e2;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.index-page__secondary-copy {
  display: flex;
  flex-direction: column;
}

.index-page__secondary-title {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
}

.index-page__secondary-desc {
  color: #454745;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
}

.index-page__secondary-button {
  width: 24px;
  height: 18px;
  padding: 4px 4px 10px;
  box-sizing: border-box;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-page__secondary-button-line {
  width: 16px;
  height: 4px;
  border-radius: 9999px;
  background: #454745;
}

.index-page__checkin-shell {
  width: 342px;
  padding: 32px 75px 0;
  box-sizing: border-box;
}

.index-page__checkin-button {
  width: 192px;
  height: 192px;
  border-radius: 9999px;
  background: #d03238;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}

.index-page__checkin-icon {
  width: 32px;
  height: 36px;
  margin-top: 50px;
  display: block;
}

.index-page__checkin-text {
  margin-top: 32px;
  color: #ffffff;
  font-size: 18px;
  line-height: 24px;
  font-weight: 500;
}
</style>