<template>
  <view class="back-button" :style="positionStyle" @click="handleClick">
    <image class="back-button__icon" :src="backIcon" mode="aspectFit" />
  </view>
</template>

<script setup>
/**
 * BackButton —— 次级页面返回按钮组件
 * --------------------------------------------------------------------------
 * 设计依据：以 NoticeButton.vue 为蓝本，仅替换图标资源与点击行为。
 *   - 图标：fanhui.png
 *   - 行为：点击触发 uni.navigateBack()，返回上一页（页面栈为空时回退到首页）
 *
 * 适用范围：所有次级页面（非首页/记录/设置的一级页面）。
 *   一级页面（index/record/settings）继续使用 NoticeButton，不变更。
 *
 * 位置规范：与 NoticeButton 完全一致，左上角绝对定位，避开状态栏。
 *
 * 参考：
 *   - uni-app navigateBack API：https://uniapp.dcloud.net.cn/api/router.html#navigaterback
 *   - Vue 3 组件基础：https://cn.vuejs.org/guide/essentials/component-basics.html
 */
import { computed } from 'vue'
import backIcon from '../assets/images/fanhui.png'

const props = defineProps({
  // 距顶部偏移：基于设备状态栏高度动态计算，确保各机型顶部留白一致
  // 与 NoticeButton 保持一致，便于次级页面与一级页面图标位置对齐
  top: {
    type: String,
    default: ''
  }
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

// 点击返回上一页：优先使用 navigateBack(delta=1)
// 页面栈为空（如直接被分享打开）时回退到首页 index/index
function handleClick() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack({ delta: 1 })
  } else {
    uni.reLaunch({ url: '/pages/index/index' })
  }
}
</script>

<style lang="scss" scoped>
.back-button {
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

.back-button__icon {
  width: 40px;
  height: 40px;
  display: block;
}
</style>
