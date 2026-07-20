<template>
  <!-- 常规态：临时公告卡片，flex:1 填充首页空白高度（任务卡与打卡按钮之间） -->
  <view
    v-if="visible && current"
    class="announcement-card"
    @click="expand"
  >
    <view class="announcement-card__badge">{{ remaining }}s</view>
    <view :key="current.id" class="announcement-card__body">
      <text class="announcement-card__title">{{ displayTitle }}</text>
      <text class="announcement-card__content">{{ current.content }}</text>
    </view>
  </view>

  <!-- 满屏态：点击卡片后暂停倒计时并满屏展示，再次点击缩回 -->
  <view
    v-if="expanded && current"
    class="announcement-fullscreen"
    @click="collapse"
  >
    <view class="announcement-fullscreen__card" @click.stop="collapse">
      <view class="announcement-fullscreen__badge">{{ remaining }}s</view>
      <!-- 卡片尺寸固定；标题+内容放入 scroll-view，超出时卡片内右侧滚动 -->
      <scroll-view scroll-y class="announcement-fullscreen__scroll" @click.stop="collapse">
        <text class="announcement-fullscreen__title">{{ displayTitle }}</text>
        <text class="announcement-fullscreen__content">{{ current.content }}</text>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
/**
 * 首页公告临时卡片
 * ----------------------------------------------------------------------------
 * - 接收最近 7 天公告（已按创建时间倒序），先用已读持久化过滤出未读项
 * - 逐条轮播，每条展示 10 秒；最新优先，依次到最旧，最后一条结束卡片消失
 * - 卡片 flex:1 填充首页空白高度，保持一屏无滚动
 * - 点击卡片：暂停倒计时并满屏展示；再次点击满屏卡片：缩回并继续倒计时
 * - 倒计时数字常驻卡片右上角（常规态与满屏态均显示）
 */
import { ref, computed, watch, onUnmounted } from 'vue'
import { getUnread, markRead } from '@/utils/announcementRead'

const props = defineProps({
  // 最近 7 天公告（按创建时间倒序），每项含 id/title/content/created_at
  announcements: {
    type: Array,
    default: () => []
  }
})

const DISPLAY_SECONDS = 10
const currentIndex = ref(0)
const remaining = ref(DISPLAY_SECONDS)
const expanded = ref(false)
const finished = ref(false)
let timer = null

// 未读公告队列（绑定当前登录 token 的已读持久化）
const queue = computed(() => getUnread(props.announcements))
const visible = computed(
  () => !finished.value && queue.value.length > 0 && currentIndex.value < queue.value.length
)
const current = computed(() => (visible.value ? queue.value[currentIndex.value] : null))
// 标题统一前缀：固定拼接「【官方公告】」
const displayTitle = computed(() => (current.value ? `【官方公告】${current.value.title}` : ''))

function markCurrentRead() {
  if (current.value) markRead(current.value)
}

function start() {
  finished.value = false
  currentIndex.value = 0
  remaining.value = DISPLAY_SECONDS
  markCurrentRead()
  startTimer()
}

function startTimer() {
  stopTimer()
  timer = setInterval(() => {
    // 满屏展示时暂停倒计时
    if (expanded.value) return
    remaining.value -= 1
    if (remaining.value <= 0) advance()
  }, 1000)
}

function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function advance() {
  if (currentIndex.value + 1 < queue.value.length) {
    currentIndex.value += 1
    remaining.value = DISPLAY_SECONDS
    markCurrentRead()
  } else {
    // 最后一条展示结束 → 标记已读并隐藏卡片
    markCurrentRead()
    finished.value = true
    stopTimer()
  }
}

function expand() {
  expanded.value = true
}

function collapse() {
  expanded.value = false
}

watch(
  () => props.announcements,
  (list) => {
    if (list && list.length) {
      start()
    } else {
      finished.value = true
      stopTimer()
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  stopTimer()
})
</script>

<style lang="scss">
.announcement-card {
  /* flex:1 自动填满首页空白高度；出现即吸收空白、消失即释放，始终一屏无滚动 */
  flex: 1 1 auto;
  min-height: 0;
  width: 684rpx;
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 64rpx;
  background: #ffffff;
  /* 与首页任务卡一致的描边/阴影 */
  box-shadow: inset 0 0 0 1px #e2e2e2, 0 1px 2px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.announcement-card__badge {
  position: absolute;
  top: 34rpx;
  right: 34rpx;
  padding: 4rpx 16rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #9fe870;
  color: #2e6900;
  font-size: 24rpx;
  line-height: 40rpx;
  font-weight: 600;
}

.announcement-card__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
  /* 切换公告时的轻微淡入微动效 */
  animation: announcement-fade 0.25s ease;
}

.announcement-card__title {
  color: #0e0f0c;
  font-size: 36rpx;
  line-height: 52rpx;
  font-weight: 600;
  /* 单行截断，padding-right 为右上角倒计时胶囊预留空间 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 120rpx;
  box-sizing: border-box;
}

.announcement-card__content {
  margin-top: 16rpx;
  color: #454745;
  font-size: 28rpx;
  line-height: 44rpx;
  font-weight: 400;
  /* 最多 3 行截断 */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  overflow: hidden;
  word-break: break-all;
}

/* 满屏态 */
.announcement-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
  box-sizing: border-box;
  z-index: 1000;
  /* 遮罩淡入 */
  animation: announcement-mask 0.2s ease;
}

.announcement-fullscreen__card {
  position: relative;
  width: 100%;
  max-width: 684rpx;
  /* 固定卡片大小：高度不随内容多少变化，内容超出由内部 scroll-view 滚动 */
  height: 70vh;
  padding: 48rpx;
  box-sizing: border-box;
  border-radius: 64rpx;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  /* 卡片轻微缩放弹出 */
  animation: announcement-pop 0.2s ease;
}

.announcement-fullscreen__badge {
  position: absolute;
  top: 48rpx;
  right: 48rpx;
  padding: 4rpx 16rpx;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #9fe870;
  color: #2e6900;
  font-size: 24rpx;
  line-height: 40rpx;
  font-weight: 600;
  z-index: 1;
}

/* 标题+内容滚动区：填满卡片剩余高度，超出时右侧滚动 */
.announcement-fullscreen__scroll {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.announcement-fullscreen__title {
  display: block;
  color: #0e0f0c;
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 600;
  /* 展开态标题完整多行显示，右侧为倒计时胶囊预留空间 */
  padding-right: 120rpx;
  box-sizing: border-box;
  word-break: break-word;
}

.announcement-fullscreen__content {
  display: block;
  margin-top: 24rpx;
  color: #454745;
  font-size: 32rpx;
  line-height: 52rpx;
  font-weight: 400;
  white-space: pre-wrap;
  word-break: break-word;
}

@keyframes announcement-fade {
  from {
    opacity: 0;
    transform: translateY(8rpx);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes announcement-mask {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes announcement-pop {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 平板/折叠屏适配（≥768px）：锁宽与字号，避免 rpx 过度放大 */
@media screen and (min-width: 768px) {
  .announcement-card {
    width: 342px;
    padding: 16px;
    border-radius: 32px;
  }
  .announcement-card__badge {
    top: 17px;
    right: 17px;
    padding: 2px 8px;
    font-size: 12px;
    line-height: 20px;
  }
  .announcement-card__title {
    font-size: 18px;
    line-height: 26px;
    padding-right: 60px;
  }
  .announcement-card__content {
    margin-top: 8px;
    font-size: 14px;
    line-height: 22px;
  }
  .announcement-fullscreen {
    padding: 24px;
  }
  .announcement-fullscreen__card {
    max-width: 342px;
    padding: 24px;
    border-radius: 32px;
  }
  .announcement-fullscreen__badge {
    top: 24px;
    right: 24px;
    padding: 2px 8px;
    font-size: 12px;
    line-height: 20px;
  }
  .announcement-fullscreen__title {
    font-size: 24px;
    line-height: 32px;
    padding-right: 60px;
  }
  .announcement-fullscreen__content {
    margin-top: 12px;
    font-size: 16px;
    line-height: 26px;
  }
}
</style>
