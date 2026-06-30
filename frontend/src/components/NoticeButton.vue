<template>
  <view class="notice-button" :style="positionStyle" @click="handleClick">
    <image class="notice-button__icon" :src="iconSrc" mode="aspectFit" />
  </view>
</template>

<script setup>
import { computed } from 'vue'
import noticeInactiveIcon from '../assets/images/tongzhi_0.png'
import noticeActiveIcon from '../assets/images/tongzhi_1.png'

const props = defineProps({
  hasNotification: {
    type: Boolean,
    default: false
  },
  // 距顶部偏移：基于设备状态栏高度动态计算，确保各机型顶部留白一致
  // iPhone 13 mini（statusBarHeight≈50）：top ≈ 45px
  // iPhone 15 Pro（statusBarHeight≈59）：top ≈ 54px（新机型自动增加约10px）
  top: {
    type: String,
    default: ''
  }
})

const iconSrc = computed(() => {
  return props.hasNotification ? noticeActiveIcon : noticeInactiveIcon
})

// 动态计算 top：若未传入 top，则基于 statusBarHeight 计算
// 在基础偏移上额外增加 0.6vh（约5px），使用相对单位确保各屏幕尺寸下视觉比例一致
const computedTop = computed(() => {
  if (props.top) return props.top
  try {
    const sysInfo = uni.getSystemInfoSync()
    const statusBarHeight = sysInfo.statusBarHeight || 44
    return `calc(${statusBarHeight - 5}px + 0.6vh)`
  } catch (e) {
    return 'calc(45px + 0.6vh)'
  }
})

const positionStyle = computed(() => ({
  top: computedTop.value
}))

// 模内紧耦：点击跳转设置页逻辑封装在组件内部，页面无需重复实现
function handleClick() {
  uni.reLaunch({
    url: '/pages/index/settings'
  })
}
</script>

<style lang="scss" scoped>
.notice-button {
  position: absolute;
  top: calc(45px + 0.6vh);
  left: 24px;
  z-index: 10;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notice-button__icon {
  width: 40px;
  height: 40px;
  display: block;
}
</style>