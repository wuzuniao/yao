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
.bottom-nav {
  /* position: fixed 相对视口定位，不随页面内容滚动，始终固定在可视区域底部 */
  position: fixed;
  left: 50%;
  bottom: 15px;
  transform: translateX(-50%);
  width: 351px;
  height: 86px;
  padding: 8px 25.5px;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #ffffff;
  box-shadow:
    0 4px 6px -4px rgba(0, 0, 0, 0.1),
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    inset 0 0 0 1px #e2e2e2;
  display: flex;
  align-items: center;
  gap: 35px;
  z-index: 100;
}

.bottom-nav__item {
  width: 76px;
  height: 68px;
  padding: 12px 24px;
  box-sizing: border-box;
  border-radius: 9999px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.bottom-nav__item--active {
  height: 66px;
  background: #9fe870;
}

.bottom-nav__icon {
  display: block;
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
  color: #454745;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
}

.bottom-nav__text--active {
  color: #2f6c00;
}
</style>