/**
 * Token 静默续期 composable（多端共用，无平台条件编译）
 * --------------------------------------------------------------------------
 * - 解码本地 JWT 的 exp（仅读声明，不校验签名）
 * - 当剩余有效期不足 1 天时，调用 auth 服务 /oauth/token（refresh_token grant，
 *   轮换制）换新令牌对，双 token（access_token/refresh_token）一并覆盖本地
 * - 失败仅 warn，不跳登录（真正 401 由 request.js 统一处理）
 * - App.vue onShow 调用，实现「默认进首页、仅刷新有效期」的诉求
 * - 2026-09-07 修复：原阈值条件写反（剩余<1 天时 return 跳过刷新），
 *   现改为剩余不足 1 天才触发刷新、未临近过期则跳过
 */
import { useUserStore } from '../store/modules/user'
import { refreshToken as refreshTokenApi } from '../api/modules/user'
import { syncAuthCookie } from '../utils/authCookie'

const REFRESH_THRESHOLD_SECONDS = 1 * 24 * 3600 // 剩余不足 1 天续期

// 解码 JWT payload 的 exp（不校验签名，仅读声明）
// 兼容 App 端（5+ 引擎可能缺失 atob）：优先用全局 atob，否则回退 uni.base64ToArrayBuffer
function getTokenExp(token) {
  if (!token || typeof token !== 'string') return 0
  const parts = token.split('.')
  if (parts.length < 2) return 0
  try {
    let b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const pad = b64.length % 4
    if (pad) b64 += '='.repeat(4 - pad)
    let json
    if (typeof atob === 'function') {
      json = decodeURIComponent(escape(atob(b64)))
    } else {
      // App 端无 atob：用 uni.base64ToArrayBuffer 解码为字节再转字符串
      const bytes = new Uint8Array(uni.base64ToArrayBuffer(b64))
      let s = ''
      for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i])
      try {
        json = decodeURIComponent(escape(s))
      } catch (e) {
        json = s
      }
    }
    const payload = JSON.parse(json)
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
    // 未临近过期（剩余 ≥ 1 天）则跳过；临近过期（剩余 < 1 天）才触发刷新
    if (exp - now >= REFRESH_THRESHOLD_SECONDS) return
    // 无刷新令牌无法续期（旧版本登录态或已被清理），交由 401 统一处理
    if (!userStore.refreshToken) return
    _refreshing = true
    try {
      // 已登录续期时一并把 device_id 传给 auth，用于顺延生物识别凭证有效期
      // device_id 由 App 端首次登录生成并持久化于本地（生物识别模块管理），多端共用安全读取
      let deviceId = ''
      try {
        deviceId = uni.getStorageSync('biometricDeviceId') || ''
      } catch (e) {
        deviceId = ''
      }
      // /oauth/token 响应为令牌三件套原始结构（非 {code,msg,data} 业务格式）
      const res = await refreshTokenApi({ device_id: deviceId })
      if (res && res.access_token) {
        // 轮换制：双 token 一并更新，userInfo 保留不变
        userStore.accessToken = res.access_token
        try {
          uni.setStorageSync('accessToken', res.access_token)
          if (res.refresh_token) {
            userStore.refreshToken = res.refresh_token
            uni.setStorageSync('refreshToken', res.refresh_token)
          }
        } catch (e) {
          console.warn('保存刷新后的令牌失败', e)
        }
        // 同步续期后的令牌到父域 SSO Cookie（H5），保持另一子域登录态可用
        syncAuthCookie({
          access_token: res.access_token,
          refresh_token: res.refresh_token,
          expires_in: res.expires_in,
          userInfo: userStore.userInfo
        })
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
