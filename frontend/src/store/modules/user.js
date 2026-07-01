import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getUserInfo } from '../../api/modules/user'
import { getUnreadCount } from '../../api/modules/message'

/**
 * 用户状态管理 Store
 * --------------------------------------------------------------------------
 * - 管理用户登录状态和个人信息
 * - 用户信息包含：id、username、signature、avatar_url、email、has_password、status
 * - status：1-正常，0-待删除（后台任务1分钟后清理）
 * - 未登录时 userInfo 为 null，登录成功后写入用户信息
 * - 用户信息持久化到本地存储（uni.setStorageSync）
 */
export const useUserStore = defineStore('user', () => {
  // 用户信息（未登录为 null）
  const userInfo = ref(null)

  // 未读站内信数量（全局共享，供 NoticeButton 图标切换：tongzhi_1/tongzhi_0）
  const unreadCount = ref(0)
  let unreadFetchTime = 0

  // 从本地存储加载用户信息（页面刷新后恢复状态）
  function loadUserFromStorage() {
    try {
      const stored = uni.getStorageSync('userInfo')
      if (stored && stored.id) {
        userInfo.value = stored
      }
    } catch (e) {
      console.warn('读取本地用户信息失败', e)
    }
  }

  // 设置用户信息（登录成功后调用）
  function setUser(data) {
    userInfo.value = {
      id: data.id,
      username: data.username,
      signature: data.signature != null ? String(data.signature) : '',
      avatar_url: data.avatar_url || '',
      email: data.email || '',
      has_password: !!data.has_password,
      status: data.status ?? 1
    }
    try {
      uni.setStorageSync('userInfo', userInfo.value)
    } catch (e) {
      console.warn('保存用户信息到本地失败', e)
    }
  }

  // 清除用户信息（退出登录时调用）
  function clearUser() {
    userInfo.value = null
    unreadCount.value = 0
    try {
      uni.removeStorageSync('userInfo')
    } catch (e) {
      console.warn('清除本地用户信息失败', e)
    }
  }

  // 初始化时加载本地存储的用户信息
  loadUserFromStorage()

  // 账号删除倒计时定时器（status=0 后 60 秒自动清理前端状态）
  const deletionTimer = ref(null)

  // 启动账号删除倒计时（scheduleDeletion 成功后调用）
  function startDeletionCountdown() {
    clearDeletionTimer()
    deletionTimer.value = setTimeout(() => {
      clearUser()
      clearDeletionTimer()
      uni.showToast({ title: '账号已删除', icon: 'none' })
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/user/login' })
      }, 1500)
    }, 60000)
  }

  // 清除账号删除倒计时（cancelDeletion 成功后调用）
  function clearDeletionTimer() {
    if (deletionTimer.value) {
      clearTimeout(deletionTimer.value)
      deletionTimer.value = null
    }
  }

  // 验证用户账号是否仍然存在（App.vue onShow 调用，用于检测后端已删除账号）
  async function verifyUserExists() {
    if (!userInfo.value) return
    try {
      const result = await getUserInfo(userInfo.value.id)
      // 账号存在，更新本地信息（如 status 已变化）
      if (result.data) {
        setUser(result.data)
      }
    } catch (e) {
      // 账号已被后端删除（404），清除前端状态并跳转登录页
      clearUser()
      clearDeletionTimer()
      uni.showToast({ title: '账号已被删除', icon: 'none' })
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/user/login' })
      }, 1500)
    }
  }

  // 查询未读站内信数量（10 秒节流，避免页面快速切换时重复请求）
  // force=true 时强制刷新（如站内信页轮询检测新消息）
  async function loadUnreadCount(force = false) {
    if (!userInfo.value) {
      unreadCount.value = 0
      return
    }
    const now = Date.now()
    if (!force && now - unreadFetchTime < 10000) return
    unreadFetchTime = now
    try {
      const res = await getUnreadCount(userInfo.value.id)
      if (res.code === 0 && res.data) {
        unreadCount.value = res.data.unread_count || 0
      }
    } catch (e) {
      console.warn('查询未读站内信数量失败', e)
    }
  }

  // 直接设置未读数量（站内信页加载列表后同步到全局，供其它页面 NoticeButton 读取）
  function setUnreadCount(n) {
    unreadCount.value = n || 0
  }

  // 未读数量减一（站内信页标记已读后同步全局图标状态）
  function decrementUnread() {
    if (unreadCount.value > 0) unreadCount.value -= 1
  }

  return {
    userInfo,
    unreadCount,
    setUser,
    clearUser,
    loadUserFromStorage,
    startDeletionCountdown,
    clearDeletionTimer,
    verifyUserExists,
    loadUnreadCount,
    setUnreadCount,
    decrementUnread
  }
})