<template>
  <view class="notice-button" :style="positionStyle" @click="handleClick">
    <image class="notice-button__icon" :src="iconSrc" mode="aspectFit" />
  </view>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useUserStore } from '../store/modules/user'
import noticeInactiveIcon from '../assets/images/tongzhi_0.png'
import noticeActiveIcon from '../assets/images/tongzhi_1.png'

const props = defineProps({
  // hasNotification 已废弃：图标现由全局未读站内信数量（userStore.unreadCount）驱动
  // 保留 prop 定义以兼容各页面历史调用，实际不再使用
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

const userStore = useUserStore()

// 图标由全局未读数量驱动：有未读显示 tongzhi_1.png，无消息/全部已读显示 tongzhi_0.png
const iconSrc = computed(() => {
  return userStore.unreadCount > 0 ? noticeActiveIcon : noticeInactiveIcon
})

// 组件挂载时拉取未读数量（store 内置 10 秒节流与登录校验，未登录时不请求）
onMounted(() => {
  userStore.loadUnreadCount()
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

// 模内紧耦：点击直达站内信页，逻辑封装在组件内部，页面无需重复实现
function handleClick() {
  // 检测当前是否已在站内信页：避免在 messages.vue 内重复入栈
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  if (currentPage && currentPage.route === 'pages/user/messages') {
    return
  }
  // 使用 navigateTo 保留页面栈，确保 messages.vue 可通过返回手势（左滑/右滑）回到上一页
  // （原 reLaunch 会清空页面栈导致栈底无返回目标，返回手势失效）
  uni.navigateTo({
    url: '/pages/user/messages'
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