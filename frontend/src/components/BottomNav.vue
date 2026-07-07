<template>
  <view class="bottom-nav">
    <view 
      class="bottom-nav__item" 
      :class="{ 'bottom-nav__item--active': active === 'home' }"
      @click="handleClick('home')"
    >
      <image 
        class="bottom-nav__icon bottom-nav__icon--home" 
        :src="active === 'home' ? homeActiveIcon : homeInactiveIcon" 
        mode="aspectFit" 
      />
      <text class="bottom-nav__text" :class="{ 'bottom-nav__text--active': active === 'home' }">首页</text>
    </view>

    <view 
      class="bottom-nav__item" 
      :class="{ 'bottom-nav__item--active': active === 'record' }"
      @click="handleClick('record')"
    >
      <image 
        class="bottom-nav__icon bottom-nav__icon--record" 
        :src="active === 'record' ? recordActiveIcon : recordInactiveIcon" 
        mode="aspectFit" 
      />
      <text class="bottom-nav__text" :class="{ 'bottom-nav__text--active': active === 'record' }">记录</text>
    </view>

    <view 
      class="bottom-nav__item" 
      :class="{ 'bottom-nav__item--active': active === 'settings' }"
      @click="handleClick('settings')"
    >
      <image 
        class="bottom-nav__icon bottom-nav__icon--settings" 
        :src="active === 'settings' ? settingsActiveIcon : settingsInactiveIcon" 
        mode="aspectFit" 
      />
      <text class="bottom-nav__text" :class="{ 'bottom-nav__text--active': active === 'settings' }">设置</text>
    </view>
  </view>
</template>

<script setup>
import homeActiveIcon from '../assets/images/dh_shouye_1.png'
import homeInactiveIcon from '../assets/images/dh_shouye_0.png'
import recordActiveIcon from '../assets/images/dh_jilu_1.png'
import recordInactiveIcon from '../assets/images/dh_jilu_0.png'
import settingsActiveIcon from '../assets/images/dh_shezhi_1.png'
import settingsInactiveIcon from '../assets/images/dh_shezhi_0.png'

const props = defineProps({
  active: {
    type: String,
    default: 'home',
    validator: (value) => ['home', 'record', 'settings'].includes(value)
  }
})

// 模内紧耦：导航逻辑封装在组件内部，页面无需重复实现
function handleClick(type) {
  // 点击当前已激活的导航项时不重复跳转，避免页面重载
  if (type === props.active) return
  if (type === 'home') {
    uni.reLaunch({ url: '/pages/index/index' })
  } else if (type === 'record') {
    uni.reLaunch({ url: '/pages/index/record' })
  } else if (type === 'settings') {
    uni.reLaunch({ url: '/pages/index/settings' })
  }
}
</script>

<style lang="scss" scoped>
/* ===== 单位转换说明（px → rpx）=====
 * 设计稿基准 375px 宽，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * 已转换属性：width/height/padding/margin/gap/font-size/line-height/top/bottom 等
 * 保留 px 的情况：1px 物理边框、box-shadow 偏移与模糊半径、9999px 胶囊圆角、百分比、translate 百分比、z-index
 */
.bottom-nav {
  /* position: fixed 相对视口定位，不随页面内容滚动，始终固定在可视区域底部 */
  position: fixed;
  left: 50%;
  bottom: 30rpx;
  transform: translateX(-50%);
  width: 702rpx;
  height: 172rpx;
  padding: 16rpx 51rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #ffffff;
  box-shadow:
    0 4px 6px -4px rgba(0, 0, 0, 0.1),
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    inset 0 0 0 1px #e2e2e2;
  display: flex;
  align-items: center;
  gap: 70rpx;
  z-index: 100;
}

.bottom-nav__item {
  width: 152rpx;
  height: 136rpx;
  padding: 24rpx 48rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.bottom-nav__item--active {
  height: 132rpx;
  background: #9fe870;
}

.bottom-nav__icon {
  display: block;
}

.bottom-nav__icon--home {
  width: 32rpx;
  height: 36rpx;
}

.bottom-nav__icon--record {
  width: 36rpx;
  height: 40rpx;
}

.bottom-nav__icon--settings {
  width: 42rpx;
  height: 48rpx;
}

.bottom-nav__text {
  color: #454745;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.bottom-nav__text--active {
  color: #2f6c00;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为原 px 值
 */
@media screen and (min-width: 768px) {
  .bottom-nav {
    bottom: 15px;
    width: 351px;
    height: 86px;
    padding: 8px 25.5px;
    gap: 35px;
  }
  .bottom-nav__item {
    width: 76px;
    height: 68px;
    padding: 12px 24px;
    gap: 4px;
  }
  .bottom-nav__item--active {
    height: 66px;
  }
  .bottom-nav__icon--home {
    width: 16px;
    height: 18px;
  }
  .bottom-nav__icon--record {
    width: 18px;
    height: 20px;
  }
  .bottom-nav__icon--settings {
    width: 21px;
    height: 24px;
  }
  .bottom-nav__text {
    font-size: 14px;
    line-height: 20px;
  }
}
</style>
