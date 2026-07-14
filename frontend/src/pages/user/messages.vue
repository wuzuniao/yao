<template>
  <view class="messages-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="messages-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 help/notification 等页面保持一致） -->
      <PageHeader title="站内信" desc="查看您的打卡提醒消息，点击未读消息可标记为已读。" />

      <!-- 全部已读按钮（仅当存在未读消息且非加载中时显示） -->
      <view
        v-if="hasUnread && !loading && !loadingMore"
        class="messages-page__mark-all"
        :class="{ 'messages-page__mark-all--disabled': markingAll }"
        @click="handleMarkAllRead"
      >
        全部已读
      </view>

      <!-- 消息卡片列表 -->
      <view class="messages-page__list">
        <!-- 加载中（初次加载） -->
        <view v-if="loading && messages.length === 0" class="messages-page__status">
          <text class="messages-page__status-text">加载中...</text>
        </view>

        <!-- 加载失败（初次加载，点击重试） -->
        <view v-else-if="error && messages.length === 0" class="messages-page__status" @click="retry">
          <text class="messages-page__status-text messages-page__status-text--error">加载失败，点击重试</text>
        </view>

        <!-- 空数据 -->
        <view v-else-if="messages.length === 0" class="messages-page__status">
          <text class="messages-page__status-text">暂无站内信消息</text>
        </view>

        <!-- 消息卡片列表 -->
        <template v-else>
          <view
            v-for="item in messages"
            :key="item.id"
            class="messages-page__card"
            :class="{ 'messages-page__card--unread': item.is_unread }"
            @click="handleCardClick(item)"
          >
            <!-- 未读左侧高亮标识 -->
            <view v-if="item.is_unread" class="messages-page__card-bar"></view>
            <view class="messages-page__card-body">
              <text class="messages-page__card-title">{{ item.plan_name }}</text>
              <text v-if="item.plan_remark" class="messages-page__card-text">{{ item.plan_remark }}</text>
              <text class="messages-page__card-time">{{ formatSendTime(item.send_time) }}</text>
            </view>
          </view>

          <!-- 加载更多（分页加载中） -->
          <view v-if="loadingMore" class="messages-page__status">
            <text class="messages-page__status-text">加载更多...</text>
          </view>
          <!-- 没有更多 -->
          <view v-else-if="!hasMore && messages.length > 0" class="messages-page__status">
            <text class="messages-page__status-text">没有更多消息了</text>
          </view>
        </template>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 站内信页（messages.vue）
 * --------------------------------------------------------------------------
 * 功能：展示当前用户的站内信消息列表，支持标记已读
 *  - 数据来源：notification_logs 表（channel_type='站内信'，按 send_time 倒序）
 *  - 卡片内容：计划名称 + 备注说明 + 发送时间
 *  - 未读消息（is_unread=true）：左侧绿色高亮条 + 浅绿背景
 *  - 点击未读卡片：调用 API 标记已读，前端实时移除高亮（卡片保留）
 *  - 全部已读：一键将所有未读消息标记为已读（按钮仅在存在未读时显示）
 *  - 通知按钮图标：有未读显示 tongzhi_1.png，全部已读显示 tongzhi_0.png（实时切换）
 *  - 分页加载：触底加载下一页（onReachBottom）
 *  - 加载中/空数据/加载失败三种状态反馈，失败可点击重试
 */
import { ref, computed } from 'vue'
import { onShow, onReachBottom } from '@dcloudio/uni-app'
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { useUserStore } from '../../store/modules/user'
import { listMessages, markMessageRead, markAllMessagesRead } from '../../api/modules/message'
import { useShare } from '../../composables/useShare'

useShare({ title: '站内信' })

const userStore = useUserStore()

const messages = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(false)
const hasMore = ref(false)
const page = ref(1)
const markingAll = ref(false) // 全部已读按钮防抖（点击后立即置灰，避免重复点击）

// 列表中是否存在未读消息（控制"全部已读"按钮显示）
const hasUnread = computed(() => messages.value.some((item) => item.is_unread))

const PAGE_SIZE = 20

// ===== 数据加载 =====

// 加载站内信列表（reset=true 重新加载第一页，false 加载下一页）
async function loadMessages(reset = false) {
  if (!userStore.userInfo) {
    messages.value = []
    return
  }
  if (reset) {
    page.value = 1
    loading.value = true
    error.value = false
  } else {
    loadingMore.value = true
  }
  try {
    const res = await listMessages(page.value, PAGE_SIZE)
    if (res.code === 0 && res.data) {
      const items = res.data.items || []
      // reset 替换列表，分页追加
      if (reset) {
        messages.value = items
      } else {
        messages.value = messages.value.concat(items)
      }
      hasMore.value = !!res.data.has_more
      // 同步未读数量到全局 store，供所有页面 NoticeButton 图标切换
      userStore.setUnreadCount(res.data.unread_count || 0)
    }
  } catch (e) {
    console.warn('加载站内信失败', e)
    // 仅初次加载失败时显示错误态（分页失败静默，避免打断用户）
    if (reset) error.value = true
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// ===== 交互 =====

// 点击卡片：未读则标记已读（已读卡片无操作）
async function handleCardClick(item) {
  if (!item.is_unread || !userStore.userInfo) return
  try {
    const res = await markMessageRead({ log_id: item.id })
    if (res.code === 0) {
      // 状态更新成功：前端实时移除高亮（卡片保留在列表）
      item.is_unread = false
      // 同步全局未读数量，所有页面 NoticeButton 图标即时切换
      userStore.decrementUnread()
    }
  } catch (e) {
    // 优雅的错误提示，不中断用户操作
    uni.showToast({ title: e.message || '标记失败，请重试', icon: 'none' })
  }
}

// 全部标记已读：批量将所有未读站内信置为已读（防抖，点击后立即置灰）
async function handleMarkAllRead() {
  if (markingAll.value) return
  markingAll.value = true
  try {
    const res = await markAllMessagesRead()
    if (res.code === 0) {
      // 成功：将列表中所有卡片置为已读（移除高亮，卡片保留）
      messages.value.forEach((item) => {
        item.is_unread = false
      })
      userStore.setUnreadCount(0)
      uni.showToast({ title: '已全部标记为已读', icon: 'none' })
    } else {
      uni.showToast({ title: res.msg || '操作失败，请重试', icon: 'none' })
    }
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败，请重试', icon: 'none' })
  } finally {
    markingAll.value = false
  }
}

// 重试初次加载
function retry() {
  loadMessages(true)
}

// 格式化发送时间：ISO 字符串 "2026-07-02T14:30:00" → "2026-07-02 14:30"
function formatSendTime(iso) {
  if (!iso) return ''
  return iso.replace('T', ' ').slice(0, 16)
}

// ===== 生命周期 =====

onShow(() => {
  loadMessages(true)
})

// 触底加载下一页
onReachBottom(() => {
  if (hasMore.value && !loadingMore.value && !loading.value) {
    page.value += 1
    loadMessages(false)
  }
})
</script>

<style lang="scss">
/* ==========================================================================
 * 响应式单位说明（px → rpx 转换）
 * --------------------------------------------------------------------------
 * 基准：375px 设计稿，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * 转 rpx：width/height/padding/margin/gap/font-size/line-height/border-radius/定位偏移
 * 保留 px：1px 边框、box-shadow 偏移/模糊、9999px、百分比、vh、z-index
 * 平板/折叠屏断点：≥768px 锁定关键尺寸为 px，避免 rpx 过度放大
 * ========================================================================== */
.messages-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

/* ===== 主内容画布（结构与 help.vue 一致）===== */
.messages-page__canvas {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 210rpx 48rpx 64rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
  min-height: 100vh;
}

/* ===== 全部已读按钮 ===== */
.messages-page__mark-all {
  align-self: flex-end;
  padding: 12rpx 24rpx;
  font-size: 28rpx;
  line-height: 40rpx;
  color: var(--color-brand);
  border: 1px solid var(--color-brand);
  border-radius: 32rpx;
}

/* 防抖置灰（点击后等待接口返回期间禁用交互） */
.messages-page__mark-all--disabled {
  opacity: 0.5;
}

/* ===== 消息卡片列表 ===== */
.messages-page__list {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

/* ===== 单张消息卡片 ===== */
.messages-page__card {
  position: relative;
  padding: 32rpx;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 24rpx;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 未读卡片高亮：浅绿背景，与左侧绿色竖条形成视觉强调 */
.messages-page__card--unread {
  background: #f1f8e8;
}

/* 未读左侧高亮竖条（品牌绿） */
.messages-page__card-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 8rpx;
  background: var(--color-brand);
}

.messages-page__card-body {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.messages-page__card-title {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
}

.messages-page__card-text {
  color: #454745;
  font-size: 32rpx;
  line-height: 52rpx;
  font-weight: 400;
  white-space: pre-line;
}

.messages-page__card-time {
  color: #868685;
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

/* ===== 状态提示（加载中 / 空数据 / 加载失败 / 分页）===== */
.messages-page__status {
  padding: 64rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.messages-page__status-text {
  color: #868685;
  font-size: 28rpx;
}

.messages-page__status-text--error {
  color: var(--color-danger);
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 */
@media screen and (min-width: 768px) {
  .messages-page__canvas {
    padding: 105px 24px 32px;
    gap: 32px;
  }
  .messages-page__mark-all {
    padding: 6px 12px;
    font-size: 14px;
    line-height: 20px;
    border-radius: 16px;
  }
  .messages-page__list {
    gap: 16px;
  }
  .messages-page__card {
    padding: 16px;
    border-radius: 12px;
  }
  .messages-page__card-bar {
    width: 4px;
  }
  .messages-page__card-body {
    gap: 4px;
  }
  .messages-page__card-title {
    font-size: 16px;
    line-height: 24px;
  }
  .messages-page__card-text {
    font-size: 16px;
    line-height: 26px;
  }
  .messages-page__card-time {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }
  .messages-page__status {
    padding: 32px 16px;
  }
  .messages-page__status-text {
    font-size: 14px;
  }
}
</style>
