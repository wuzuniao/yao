/**
 * Token 静默续期 composable（多端共用，无平台条件编译）
 * --------------------------------------------------------------------------
 * - 解码本地 JWT 的 exp（仅读声明，不校验签名）
 * - 当剩余有效期不足 1 天时，调用 /refresh-token 换新 token 覆盖本地
 * - 失败仅 warn，不跳登录（真正 401 由 request.js 统一处理）
 * - App.vue onShow 调用，实现「默认进首页、仅刷新有效期」的诉求
 */
import { useUserStore } from '../store/modules/user'
import { refreshToken as refreshTokenApi } from '../api/modules/user'

const REFRESH_THRESHOLD_SECONDS = 1 * 24 * 3600 // 剩余不足 1 天续期

// 解码 JWT payload 的 exp（不校验签名，仅读声明）
function getTokenExp(token) {
  try {
    const payload = JSON.parse(decodeURIComponent(escape(atob(token.split('.')[1]))))
    return payload.exp || 0
  } catch (e) {
    return 0
  }
}

let _refreshing = false

export function useTokenRefresh() {
  const userStore = useUserStore()

  async function tryRefresh() {
    const token = userStore.accessToken
    if (!token || _refreshing) return
    const exp = getTokenExp(token)
    const now = Math.floor(Date.now() / 1000)
    // 未临近过期则跳过
    if (exp - now < REFRESH_THRESHOLD_SECONDS) return
    _refreshing = true
    try {
      // 已登录续期时一并把 device_id 传给后端，用于顺延生物识别凭证有效期
      // device_id 由 App 端首次登录生成并持久化于本地（生物识别模块管理），多端共用安全读取
      let deviceId = ''
      try {
        deviceId = uni.getStorageSync('biometricDeviceId') || ''
      } catch (e) {
        deviceId = ''
      }
      const res = await refreshTokenApi({ device_id: deviceId })
      if (res && res.code === 0 && res.data && res.data.access_token) {
        // 仅更新 token，保留 userInfo 不变
        userStore.accessToken = res.data.access_token
        try {
          uni.setStorageSync('accessToken', res.data.access_token)
        } catch (e) {
          console.warn('保存刷新后的 token 失败', e)
        }
      }
    } catch (e) {
      // 续期失败不强制跳登录，等真正 401 时再处理
      console.warn('token 续期失败', e)
    } finally {
      _refreshing = false
    }
  }

  return { tryRefresh }
}
