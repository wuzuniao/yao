/**
 * 跨子域 SSO Cookie 工具（H5 专用；账号别名与合并改造：Cookie 固定持有平台令牌）
 * --------------------------------------------------------------------------
 * 同一浏览器内「一处登录，处处通行」——各子域 localStorage 互相隔离（同源策略），
 * 经父域 Cookie（Domain=.wuzuniao.com）互通登录态。
 *
 * 令牌体系（N13=A1 / N23 / N34 / P39）：
 * - Cookie（wz_sso）固定持有「平台令牌」（client_id=auth，sub=主账号 id），
 *   仅用于跨站登录态恢复与交换，不直接用于业务数据接口
 * - 各项目本地持「项目令牌」（sub=该项目认识的 identity id），业务接口用
 * - 登录/刷新拿到项目令牌后：经 POST /oauth/token-exchange 换平台令牌写入 Cookie
 * - 恢复：本地已有有效项目令牌则不交换（N34，各项目本地身份独立维持）；
 *   仅本地无令牌时读 Cookie 平台令牌 → 交换 → 项目令牌写本地
 *   （平台 access 过期时用 Cookie 内平台 refresh_token 走 /oauth/token client=auth
 *   独立刷新链续期后再交换，P39）
 *
 * Cookie 内容：单条 wz_sso，值为 encodeURIComponent(JSON)：
 *   { at: 平台 access_token, rt: 平台 refresh_token, exp: access 过期毫秒时间戳, ui: 用户信息 }
 * 属性：Domain=.wuzuniao.com（生产）；Path=/；SameSite=Lax；HTTPS 下加 Secure。
 *
 * 非 H5 端（App/小程序无 document.cookie）全部为 no-op，调用方无需判断平台。
 */
import { AUTH_BASE_URL, AUTH_CLIENT_ID } from '../config/env'

// Cookie 名（统一前缀，与各端 localStorage key 区分）
const SSO_COOKIE_NAME = 'wz_sso'
// Cookie 有效期（秒）：与 refresh_token TTL（14 天）对齐；access_token 时效由 exp 字段控制
const SSO_COOKIE_MAX_AGE = 14 * 24 * 3600
// access_token 缺省有效期（秒）：与 auth 服务 ACCESS_TOKEN_EXPIRE_DAYS 一致
const DEFAULT_ACCESS_TTL_SECONDS = 3 * 24 * 3600
// auth 平台 client_id（Cookie 内平台令牌的签发目标，N12/P24）
const PLATFORM_CLIENT_ID = 'auth'

/** 当前是否为 H5 端（条件编译期确定） */
function isH5() {
  // #ifdef H5
  return true
  // #endif
  // #ifndef H5
  return false
  // #endif
}

/** 生产跨子域场景（wuzuniao.com 的子域）才设置 Domain 属性 */
function cookieDomainAttr() {
  return /\.wuzuniao\.com$/.test(location.hostname) ? '; Domain=.wuzuniao.com' : ''
}

function writeCookie(value) {
  const secure = location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${SSO_COOKIE_NAME}=${value}; Max-Age=${SSO_COOKIE_MAX_AGE}; Path=/; SameSite=Lax${secure}${cookieDomainAttr()}`
}

/**
 * 统一交换端点（POST /oauth/token-exchange，N25=a/N46 裸格式响应）
 * @param {string} bearerToken 源 client 有效令牌
 * @param {string} targetClientId 目标 client_id
 * @returns {Promise<{access_token:string, refresh_token:string, expires_in:number}|null>} 失败返回 null
 */
async function exchangeToken(bearerToken, targetClientId) {
  try {
    const res = await uni.request({
      url: `${AUTH_BASE_URL}/oauth/token-exchange`,
      method: 'POST',
      header: { 'Content-Type': 'application/json', Authorization: `Bearer ${bearerToken}` },
      data: { target_client_id: targetClientId },
      timeout: 10000
    })
    const body = res.data
    if (res.statusCode !== 200 || !body || !body.access_token) return null
    return body
  } catch (e) {
    return null
  }
}

/**
 * 平台 refresh_token 刷新（P39 独立刷新链：POST /oauth/token client=auth）
 * @returns {Promise<{access_token:string, refresh_token:string, expires_in:number}|null>}
 */
async function refreshPlatformToken(platformRefreshToken) {
  try {
    const res = await uni.request({
      url: `${AUTH_BASE_URL}/oauth/token`,
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: { grant_type: 'refresh_token', refresh_token: platformRefreshToken, client_id: PLATFORM_CLIENT_ID },
      timeout: 10000
    })
    const body = res.data
    if (res.statusCode !== 200 || !body || !body.access_token) return null
    return body
  } catch (e) {
    return null
  }
}

/**
 * 同步登录态到父域 Cookie（登录/注册/绑定成功、令牌静默刷新/续期后调用）
 * - 传入的为项目令牌：先交换平台令牌再写 Cookie（fire-and-forget，不阻塞调用方）
 * - 交换失败不写 Cookie（本地登录态不受影响；下次触发再试）
 * @param {Object} params
 * @param {string} params.access_token 项目 access_token
 * @param {string} [params.refresh_token] 项目 refresh_token
 * @param {number} [params.expires_in] 项目 access_token 有效期（秒）
 * @param {Object} [params.userInfo] 用户信息（展示用精简对象）
 */
export function syncAuthCookie({ access_token, refresh_token, expires_in, userInfo } = {}) {
  if (!isH5() || !access_token) return
  ;(async () => {
    const platform = await exchangeToken(access_token, PLATFORM_CLIENT_ID)
    if (!platform) return
    try {
      const payload = {
        at: platform.access_token,
        rt: platform.refresh_token || '',
        exp: Date.now() + (platform.expires_in || DEFAULT_ACCESS_TTL_SECONDS) * 1000,
        ui: userInfo || null
      }
      writeCookie(encodeURIComponent(JSON.stringify(payload)))
    } catch (e) {
      // Cookie 不可用（隐私模式等）不影响主流程
    }
  })()
}

/**
 * 页面加载时从父域 Cookie 恢复登录态（H5 端；恢复语义见 N34/P39）
 * 1. Cookie 缺失：另一子域已登出或用户清理了浏览器数据——本地令牌若仍为项目身份可继续用
 *    （N34 本地身份独立维持），但跨站登录态已断，无需动作；本地亦无令牌则无事可做
 * 2. 本地已有项目 access_token：本地有效不交换（N34），直接返回
 * 3. 本地无令牌 + Cookie 有平台令牌：交换 → 项目令牌 + 资料（/users/info）写本地，
 *    并经 onRestored 回调同步 store 响应式状态
 * 4. 平台 access 无效：用 Cookie 内平台 refresh_token 刷新后重试交换（P39）；
 *    平台刷新也失败（Cookie 登录态已失效）→ 清 Cookie 保持一致
 * @param {Function} [onRestored] 恢复成功回调（参数为 { access_token, refresh_token, userInfo }）
 * @returns {boolean} 是否立即完成了本地无令牌判定（异步恢复不改变返回值语义）
 */
export function restoreAuthFromCookie(onRestored) {
  if (!isH5()) return false
  try {
    const saved = readAuthCookie()
    // 本地已有项目令牌：N34 本地有效不交换
    if (uni.getStorageSync('accessToken')) return false
    if (!saved || !saved.access_token) return false
    // 异步恢复：交换 → 资料 → 写本地 → 回调
    ;(async () => {
      let platformSet = { access_token: saved.access_token, refresh_token: saved.refresh_token }
      let project = await exchangeToken(platformSet.access_token, AUTH_CLIENT_ID)
      if (!project && saved.refresh_token) {
        // 平台 access 失效：平台 rt 独立刷新链（P39）
        const refreshed = await refreshPlatformToken(saved.refresh_token)
        if (refreshed) {
          platformSet = refreshed
          project = await exchangeToken(refreshed.access_token, AUTH_CLIENT_ID)
        }
      }
      if (!project) {
        // 平台登录态已失效：清 Cookie（与各站「Cookie 缺失即退出」语义一致）
        clearAuthCookie()
        return
      }
      const userInfo = await fetchProjectUserInfo(project.access_token)
      try {
        uni.setStorageSync('accessToken', project.access_token)
        if (project.refresh_token) uni.setStorageSync('refreshToken', project.refresh_token)
        if (userInfo) uni.setStorageSync('userInfo', userInfo)
      } catch (e) {
        // 本地存储不可用：放弃本次恢复
        return
      }
      if (onRestored) onRestored({
        access_token: project.access_token,
        refresh_token: project.refresh_token,
        userInfo
      })
    })()
    return false
  } catch (e) {
    return false
  }
}

/**
 * 拉取项目身份资料（GET /api/v1/users/info，Bearer=项目令牌）
 * @returns {Promise<Object|null>} 失败返回 null（资料缺失时仅恢复令牌）
 */
async function fetchProjectUserInfo(accessToken) {
  try {
    const res = await uni.request({
      url: `${AUTH_BASE_URL}/api/v1/users/info`,
      method: 'GET',
      header: { Authorization: `Bearer ${accessToken}` },
      timeout: 10000
    })
    const body = res.data
    if (res.statusCode !== 200 || !body || body.code !== 0) return null
    return body.data || null
  } catch (e) {
    return null
  }
}

/** 清除父域 Cookie（退出登录/登录态失效/账号删除时调用） */
export function clearAuthCookie() {
  if (!isH5()) return
  try {
    document.cookie = `${SSO_COOKIE_NAME}=; Max-Age=0; Path=/; SameSite=Lax${cookieDomainAttr()}`
  } catch (e) {
    // 忽略清除失败
  }
}

/** 读取 Cookie 中的平台登录态（无则返回 null） */
export function readAuthCookie() {
  if (!isH5()) return null
  try {
    const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${SSO_COOKIE_NAME}=([^;]*)`))
    if (!match) return null
    const payload = JSON.parse(decodeURIComponent(match[1]))
    if (!payload || !payload.at) return null
    return {
      access_token: payload.at,
      refresh_token: payload.rt || '',
      expires_at: payload.exp || 0,
      userInfo: payload.ui || null
    }
  } catch (e) {
    return null
  }
}
