<template>
  <view class="messages-page">
    <!-- 顶部通知按钮：图标随未读状态切换（tongzhi_1/tongzhi_0） -->
    <NoticeButton :has-notification="hasNotification" />

    <view class="messages-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 help/notification 等页面保持一致） -->
      <PageHeader title="站内信" :desc="`查看您的打卡提醒消息，${'\n'}点击未读消息可标记为已读。`" />

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
 *  - 未读消息（status=2）：左侧绿色高亮条 + 浅绿背景
 *  - 点击未读卡片：调用 API 更新 status 为 0，前端实时移除高亮（卡片保留）
 *  - 通知按钮图标：有未读显示 tongzhi_1.png，全部已读显示 tongzhi_0.png（实时切换）
 *  - 分页加载：触底加载下一页（onReachBottom）
 *  - 定时轮询：每 30 秒查询未读数量，有新消息时自动刷新列表
 *  - 加载中/空数据/加载失败三种状态反馈，失败可点击重试
 */
import { ref, computed } from 'vue'
import { onShow, onHide, onReachBottom } from '@dcloudio/uni-app'
import NoticeButton from '../../components/NoticeButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { useUserStore } from '../../store/modules/user'
import { listMessages, markMessageRead, getUnreadCount } from '../../api/modules/message'

const userStore = useUserStore()

const messages = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(false)
const hasMore = ref(false)
const page = ref(1)

const PAGE_SIZE = 20
const POLL_INTERVAL = 30000 // 30 秒轮询（与项目后台清理任务节奏一致）
let pollTimer = null

// 通知按钮图标状态：读取全局未读数量（与其它页面共享，标记已读后即时切换）
const hasNotification = computed(() => userStore.unreadCount > 0)

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
    const res = await listMessages(userStore.userInfo.id, page.value, PAGE_SIZE)
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

// 轮询未读数量（轻量请求；检测到新消息时刷新列表）
async function pollUnreadCount() {
  if (!userStore.userInfo) return
  try {
    const res = await getUnreadCount(userStore.userInfo.id)
    if (res.code === 0 && res.data) {
      const newCount = res.data.unread_count || 0
      // 未读数量增加说明有新消息，刷新列表以展示新消息
      if (newCount > userStore.unreadCount) {
        await loadMessages(true)
      } else {
        userStore.setUnreadCount(newCount)
      }
    }
  } catch (e) {
    // 轮询失败静默，不打断用户
    console.warn('查询未读数量失败', e)
  }
}

// ===== 交互 =====

// 点击卡片：未读则标记已读（已读卡片无操作）
async function handleCardClick(item) {
  if (!item.is_unread || !userStore.userInfo) return
  try {
    const res = await markMessageRead({ log_id: item.id, user_id: userStore.userInfo.id })
    if (res.code === 0) {
      // 状态更新成功：前端实时移除高亮（卡片保留在列表）
      item.is_unread = false
      item.status = 0
      // 同步全局未读数量，所有页面 NoticeButton 图标即时切换
      userStore.decrementUnread()
    }
  } catch (e) {
    // 优雅的错误提示，不中断用户操作
    uni.showToast({ title: e.message || '标记失败，请重试', icon: 'none' })
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
  // 页面显示：拉取数据 + 启动轮询
  loadMessages(true)
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(pollUnreadCount, POLL_INTERVAL)
})

onHide(() => {
  // 页面隐藏：停止轮询，避免后台无效请求
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
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
.messages-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

/* ===== 主内容画布（结构与 help.vue 一致）===== */
.messages-page__canvas {
  /* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与内容重叠 */
  padding: 105px 24px 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
  min-height: 100vh;
}

/* ===== 消息卡片列表 ===== */
.messages-page__list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== 单张消息卡片 ===== */
.messages-page__card {
  position: relative;
  padding: 16px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 12px;
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
  width: 4px;
  background: var(--color-brand);
}

.messages-page__card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.messages-page__card-title {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 600;
}

.messages-page__card-text {
  color: #454745;
  font-size: 16px;
  line-height: 26px;
  font-weight: 400;
  white-space: pre-line;
}

.messages-page__card-time {
  color: #868685;
  font-size: 12px;
  line-height: 16px;
  margin-top: 4px;
}

/* ===== 状态提示（加载中 / 空数据 / 加载失败 / 分页）===== */
.messages-page__status {
  padding: 32px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.messages-page__status-text {
  color: #868685;
  font-size: 14px;
}

.messages-page__status-text--error {
  color: var(--color-danger);
}
</style>
