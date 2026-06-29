import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 用户状态管理 Store
 * --------------------------------------------------------------------------
 * - 管理用户登录状态和个人信息
 * - 用户信息包含：id、username、signature、avatar_url
 * - 未登录时 userInfo 为 null，登录成功后写入用户信息
 * - 用户信息持久化到本地存储（uni.setStorageSync）
 */
export const useUserStore = defineStore('user', () => {
  // 用户信息（未登录为 null）
  const userInfo = ref(null)

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
      avatar_url: data.avatar_url || ''
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
    try {
      uni.removeStorageSync('userInfo')
    } catch (e) {
      console.warn('清除本地用户信息失败', e)
    }
  }

  // 初始化时加载本地存储的用户信息
  loadUserFromStorage()

  return {
    userInfo,
    setUser,
    clearUser,
    loadUserFromStorage
  }
})