<template>
  <view :data-theme="themeKey" class="messages-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="messages-page__canvas">
      <!-- 页面标题区（复用 PageHeader 组件，结构与 help/notification 等页面保持一致） -->
      <PageHeader :title="$t('messages.title')" :desc="$t('messages.desc')" />

      <!-- 工具栏：提醒/公告分类切换（左） + 当前分类全部已读按钮（右） -->
      <view class="messages-page__toolbar">
        <view class="messages-page__tabs">
          <view
            class="messages-page__tab"
            :class="{ 'messages-page__tab--active': activeTab === 'reminders' }"
            @click="switchTab('reminders')"
          >
            {{ $t('messages.tabReminders') }}
          </view>
          <view
            class="messages-page__tab"
            :class="{ 'messages-page__tab--active': activeTab === 'announcements' }"
            @click="switchTab('announcements')"
          >
            {{ $t('messages.tabAnnouncements') }}
          </view>
        </view>
        <!-- 全部已读（仅当前分类存在未读且非加载中时显示） -->
        <view
          v-if="currentTabHasUnread && !currentTabLoading"
          class="messages-page__mark-all"
          :class="{ 'messages-page__mark-all--disabled': markingAll }"
          @click="handleMarkAllRead"
        >
          {{ $t('messages.markAll') }}
        </view>
      </view>

      <!-- 提醒列表（数据来源：yao 后端 notification_logs） -->
      <view v-if="activeTab === 'reminders'" class="messages-page__list">
        <!-- 加载中（初次加载） -->
        <view v-if="loading && messages.length === 0" class="messages-page__status">
          <text class="messages-page__status-text">{{ $t('common.loading') }}</text>
        </view>

        <!-- 加载失败（初次加载，点击重试） -->
        <view v-else-if="error && messages.length === 0" class="messages-page__status" @click="retry">
          <text class="messages-page__status-text messages-page__status-text--error">{{ $t('common.loadFailedRetry') }}</text>
        </view>

        <!-- 空数据 -->
        <view v-else-if="messages.length === 0" class="messages-page__status">
          <text class="messages-page__status-text">{{ $t('messages.empty') }}</text>
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
            <text class="messages-page__status-text">{{ $t('common.loadingMore') }}</text>
          </view>
          <!-- 没有更多 -->
          <view v-else-if="!hasMore && messages.length > 0" class="messages-page__status">
            <text class="messages-page__status-text">{{ $t('common.noMore') }}</text>
          </view>
        </template>
      </view>

      <!-- 公告列表（数据来源：auth /api/v1/announcements，卡片直接显示全部内容） -->
      <view v-else class="messages-page__list">
        <!-- 加载中（初次加载） -->
        <view v-if="annLoading && announcements.length === 0" class="messages-page__status">
          <text class="messages-page__status-text">{{ $t('common.loading') }}</text>
        </view>

        <!-- 加载失败（初次加载，点击重试） -->
        <view v-else-if="annError && announcements.length === 0" class="messages-page__status" @click="retryAnnouncements">
          <text class="messages-page__status-text messages-page__status-text--error">{{ $t('common.loadFailedRetry') }}</text>
        </view>

        <!-- 空数据 -->
        <view v-else-if="announcements.length === 0" class="messages-page__status">
          <text class="messages-page__status-text">{{ $t('messages.announcementEmpty') }}</text>
        </view>

        <!-- 公告卡片列表 -->
        <template v-else>
          <view
            v-for="item in announcements"
            :key="'ann-' + item.id"
            class="messages-page__card"
            :class="{ 'messages-page__card--unread': !item.is_read }"
            @click="handleAnnouncementClick(item)"
          >
            <!-- 未读左侧高亮标识 -->
            <view v-if="!item.is_read" class="messages-page__card-bar"></view>
            <view class="messages-page__card-body">
              <text class="messages-page__card-title">{{ item.title }}</text>
              <text class="messages-page__card-meta">{{ formatSendTime(item.created_at) }}</text>
              <text class="messages-page__card-text">{{ item.content }}</text>
            </view>
          </view>

          <!-- 加载更多（分页加载中） -->
          <view v-if="annLoadingMore" class="messages-page__status">
            <text class="messages-page__status-text">{{ $t('common.loadingMore') }}</text>
          </view>
          <!-- 没有更多 -->
          <view v-else-if="!annHasMore && announcements.length > 0" class="messages-page__status">
            <text class="messages-page__status-text">{{ $t('common.noMore') }}</text>
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
 * 功能：展示当前用户的站内信消息列表与系统公告，支持标记已读
 *  - 分类切换：「提醒」（yao 后端 notification_logs，打卡提醒）/「公告」（auth 直连查询）
 *  - 「全部已读」仅作用于当前选中分类（公告已读状态存 auth，按项目独立维护）
 *  - 提醒卡片内容：计划名称 + 备注说明 + 发送时间
 *  - 公告卡片内容：公告标题 + 发布时间 + 全部内容（未读高亮同提醒）
 *  - 通知按钮图标：提醒未读 + 公告未读合计驱动（有未读显示 tongzhi_1.png）
 *  - 公告未读数仅在打开本页时查询并入全局未读（刷新时机与原提醒逻辑一致）
 *  - 分页加载：触底加载下一页（onReachBottom，两分类独立分页）
 *  - 加载中/空数据/加载失败三种状态反馈，失败可点击重试
 */
import { ref, computed } from 'vue'
import { onShow, onReachBottom } from '@dcloudio/uni-app'
import BackButton from '../../components/BackButton.vue'
import PageHeader from '../../components/PageHeader.vue'
import { useUserStore } from '../../store/modules/user'
import { listMessages, markMessageRead, markAllMessagesRead } from '../../api/modules/message'
import {
  getAnnouncements,
  markAnnouncementRead,
  markAllAnnouncementsRead
} from '../../api/modules/announcement'
import { useShare } from '../../composables/useShare'
import { t } from '../../locale'

useShare({ title: t('share.messages') })

const userStore = useUserStore()

// ===== 分类状态 =====
const activeTab = ref('reminders') // reminders=提醒（打卡通知） / announcements=公告（auth）

// ===== 提醒状态（yao 后端 notification_logs） =====
const messages = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(false)
const hasMore = ref(false)
const page = ref(1)
const reminderUnread = ref(0)

// ===== 公告状态（auth 直连） =====
const announcements = ref([])
const annPage = ref(1)
const annLoading = ref(false)
const annLoadingMore = ref(false)
const annError = ref(false)
const annHasMore = ref(false)
const annUnread = ref(0)

const markingAll = ref(false) // 全部已读按钮防抖（点击后立即置灰，避免重复点击）

// 当前分类是否存在未读（控制"全部已读"按钮显示）与是否初次加载中
const currentTabHasUnread = computed(() => {
  if (activeTab.value === 'reminders') {
    return messages.value.some((item) => item.is_unread)
  }
  return announcements.value.some((item) => !item.is_read)
})
const currentTabLoading = computed(() =>
  activeTab.value === 'reminders' ? loading.value : annLoading.value
)

const PAGE_SIZE = 20

// ===== 全局未读数同步（提醒 + 公告合计，供所有页面 NoticeButton 图标切换） =====
function syncUnread() {
  userStore.setUnreadCount(reminderUnread.value + annUnread.value)
}

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
      // 记录提醒未读数并与公告未读合计同步到全局 store（供所有页面 NoticeButton 图标切换）
      reminderUnread.value = res.data.unread_count || 0
      syncUnread()
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

// 点击提醒卡片：未读则标记已读（已读卡片无操作）
async function handleCardClick(item) {
  if (!item.is_unread || !userStore.userInfo) return
  try {
    const res = await markMessageRead({ log_id: item.id })
    if (res.code === 0) {
      // 状态更新成功：前端实时移除高亮（卡片保留在列表）
      item.is_unread = false
      // 同步全局未读数量（提醒未读 -1），所有页面 NoticeButton 图标即时切换
      if (reminderUnread.value > 0) reminderUnread.value -= 1
      syncUnread()
    }
  } catch (e) {
    // 优雅的错误提示，不中断用户操作
    uni.showToast({ title: e.message || t('messages.markFailed'), icon: 'none' })
  }
}

// 点击公告卡片：未读则向 auth 标记已读（已读公告无操作）
async function handleAnnouncementClick(item) {
  if (item.is_read || !userStore.userInfo) return
  try {
    const res = await markAnnouncementRead(item.id)
    if (res.code === 0) {
      // 状态更新成功：前端实时移除高亮（卡片保留在列表）
      item.is_read = true
      annUnread.value = (res.data && res.data.unread_count) || Math.max(0, annUnread.value - 1)
      syncUnread()
    }
  } catch (e) {
    uni.showToast({ title: e.message || t('messages.markFailed'), icon: 'none' })
  }
}

// 全部标记已读：仅作用于当前选中分类（防抖，点击后立即置灰）
async function handleMarkAllRead() {
  if (markingAll.value) return
  markingAll.value = true
  try {
    if (activeTab.value === 'reminders') {
      const res = await markAllMessagesRead()
      if (res.code === 0) {
        // 成功：将列表中所有提醒卡片置为已读（移除高亮，卡片保留）
        messages.value.forEach((item) => {
          item.is_unread = false
        })
        reminderUnread.value = 0
        syncUnread()
        uni.showToast({ title: t('messages.allMarked'), icon: 'none' })
      } else {
        uni.showToast({ title: res.msg || t('common.operationFailed'), icon: 'none' })
      }
    } else {
      const res = await markAllAnnouncementsRead()
      if (res.code === 0) {
        announcements.value.forEach((item) => {
          item.is_read = true
        })
        annUnread.value = 0
        syncUnread()
        uni.showToast({ title: t('messages.allMarked'), icon: 'none' })
      } else {
        uni.showToast({ title: res.msg || t('common.operationFailed'), icon: 'none' })
      }
    }
  } catch (e) {
    uni.showToast({ title: e.message || t('common.operationFailed'), icon: 'none' })
  } finally {
    markingAll.value = false
  }
}

// 重试初次加载（提醒）
function retry() {
  loadMessages(true)
}

// 重试初次加载（公告）
function retryAnnouncements() {
  loadAnnouncements(true)
}

// ===== 公告加载（auth 直连） =====

// 加载公告列表（reset=true 重新加载第一页，false 加载下一页）
async function loadAnnouncements(reset = false) {
  if (!userStore.userInfo) {
    announcements.value = []
    return
  }
  if (reset) {
    annPage.value = 1
    annLoading.value = true
    annError.value = false
  } else {
    annLoadingMore.value = true
  }
  try {
    const res = await getAnnouncements(annPage.value, PAGE_SIZE)
    if (res.code === 0 && res.data) {
      const items = res.data.items || []
      // reset 替换列表，分页追加
      if (reset) {
        announcements.value = items
      } else {
        announcements.value = announcements.value.concat(items)
      }
      annHasMore.value = !!res.data.has_more
      annUnread.value = res.data.unread_count || 0
      syncUnread()
    }
  } catch (e) {
    console.warn('加载公告失败', e)
    // 仅初次加载失败时显示错误态（分页失败静默，避免打断用户）
    if (reset) annError.value = true
  } finally {
    annLoading.value = false
    annLoadingMore.value = false
  }
}

// ===== 分类切换 =====

function switchTab(tab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
}

// 格式化发送时间：ISO 字符串 "2026-07-02T14:30:00" → "2026-07-02 14:30"
function formatSendTime(iso) {
  if (!iso) return ''
  return iso.replace('T', ' ').slice(0, 16)
}

// ===== 生命周期 =====

onShow(() => {
  // 打开站内信页时同时加载提醒与公告（公告未读数此时并入全局未读，驱动通知图标）
  loadMessages(true)
  loadAnnouncements(true)
})

// 触底加载下一页（按当前选中分类）
onReachBottom(() => {
  if (activeTab.value === 'reminders') {
    if (hasMore.value && !loadingMore.value && !loading.value) {
      page.value += 1
      loadMessages(false)
    }
  } else if (annHasMore.value && !annLoadingMore.value && !annLoading.value) {
    annPage.value += 1
    loadAnnouncements(false)
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

/* ===== 工具栏：提醒/公告分类切换（左） + 全部已读（右） ===== */
.messages-page__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.messages-page__tabs {
  display: flex;
  gap: 16rpx;
}

.messages-page__tab {
  padding: 12rpx 32rpx;
  font-size: 28rpx;
  line-height: 40rpx;
  /* 未选中：次级按钮（中性浅底 + 主文字，无描边） */
  background: var(--color-card-bg-alt);
  color: var(--color-text-primary);
  border-radius: 32rpx;
}

/* 选中分类：主按钮（品牌绿实底 + 反色文字，无描边） */
.messages-page__tab--active {
  background: var(--color-brand);
  color: var(--color-text-inverse);
  font-weight: 600;
}

/* 公告卡片发布时间（标题下方次要信息，同提醒卡片时间弱化色） */
.messages-page__card-meta {
  color: var(--color-text-tertiary);
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
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
  background: var(--color-card-bg);
  border-radius: 24rpx;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 未读卡片高亮：浅绿背景，与左侧绿色竖条形成视觉强调 */
.messages-page__card--unread {
  background: var(--color-unread-bg);
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
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
}

.messages-page__card-text {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 52rpx;
  font-weight: 400;
  white-space: pre-line;
}

.messages-page__card-time {
  color: var(--color-text-tertiary);
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
  color: var(--color-text-tertiary);
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
  .messages-page__toolbar {
    gap: 12px;
  }
  .messages-page__tabs {
    gap: 8px;
  }
  .messages-page__tab {
    padding: 6px 16px;
    font-size: 14px;
    line-height: 20px;
    border-radius: 16px;
  }
  .messages-page__card-meta {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
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
