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
  // 距顶部偏移：全局统一为 45px，确保各页面顶部留白一致，
  // 按钮底部落在 85px 处，页面内容 padding-top ≥ 100px 即可避免重叠。
  top: {
    type: String,
    default: '45px'
  }
})

const iconSrc = computed(() => {
  return props.hasNotification ? noticeActiveIcon : noticeInactiveIcon
})

const positionStyle = computed(() => ({
  top: props.top
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
  top: 45px;
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