/**
 * 跨子域 SSO Cookie 工具（H5 专用）
 * --------------------------------------------------------------------------
 * 目标：同一浏览器内「一处登录，处处通行」——yao.wuzuniao.com 与
 * auth.wuzuniao.com 两个子域的 localStorage 互相隔离（同源策略），
 * 故将令牌双件套 + 用户信息同步写入父域 Cookie（Domain=.wuzuniao.com），
 * 两端前端各自在「保存登录态时写入、页面加载时恢复、登出时清除」。
 *
 * Cookie 内容：单条 `wz_sso`，值为 encodeURIComponent(JSON)：
 *   { at: access_token, rt: refresh_token, exp: access 过期毫秒时间戳, ui: 用户信息 }
 * 属性：Domain=.wuzuniao.com（生产）；Path=/；SameSite=Lax；HTTPS 下加 Secure。
 * 开发环境（localhost 等）省略 Domain——Cookie 不区分端口，localhost:8000/10000/5173 互通。
 *
 * 安全说明：该 Cookie 仅在前端 JS 层流转（后端不读取、不作为认证凭证），
 * 令牌本就以 Authorization 头明示发送，风险面与 localStorage 存储等同；
 * 不设 HttpOnly 是因为两端 JS 均需读取以附加 Bearer 头。
 *
 * 非 H5 端（App/小程序无 document.cookie）全部为 no-op，调用方无需判断平台。
 */

// Cookie 名（统一前缀，与两端 localStorage key 区分）
const SSO_COOKIE_NAME = 'wz_sso'
// Cookie 有效期（秒）：与 refresh_token TTL（14 天）对齐；access_token 时效由 exp 字段控制
const SSO_COOKIE_MAX_AGE = 14 * 24 * 3600
// access_token 缺省有效期（秒）：与 auth 服务 ACCESS_TOKEN_EXPIRE_DAYS 一致
const DEFAULT_ACCESS_TTL_SECONDS = 3 * 24 * 3600

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
 * 同步登录态到父域 Cookie（登录/注册/绑定成功、令牌静默刷新/续期后调用）
 * @param {Object} params
 * @param {string} params.access_token 访问令牌
 * @param {string} [params.refresh_token] 刷新令牌（轮换制，刷新后为新值）
 * @param {number} [params.expires_in] access_token 有效期（秒）
 * @param {Object} [params.userInfo] 用户信息（展示用精简对象）
 */
export function syncAuthCookie({ access_token, refresh_token, expires_in, userInfo } = {}) {
  if (!isH5() || !access_token) return
  try {
    // 已有 Cookie 时保留旧 refresh/userInfo（部分调用点仅更新 access_token）
    const prev = readAuthCookie() || {}
    const payload = {
      at: access_token,
      rt: refresh_token || prev.rt || '',
      exp: Date.now() + (expires_in || DEFAULT_ACCESS_TTL_SECONDS) * 1000,
      ui: userInfo || prev.ui || null
    }
    writeCookie(encodeURIComponent(JSON.stringify(payload)))
  } catch (e) {
    // Cookie 不可用（隐私模式等）不影响主流程
  }
}

/**
 * 页面加载时从父域 Cookie 同步登录态到本地存储（三站以父域 Cookie 为登录态权威源）
 * 1. Cookie 缺失：另一子域已登出（清 Cookie 且服务端撤销该账号全部 refresh_token）、
 *    Cookie 已过期（活跃用户每次静默刷新都会续写 Cookie，故过期时本地令牌必也失效）
 *    或用户清理了浏览器数据——本地令牌必为废态，主动清除保持三站一致（对齐 www 端
 *    「Cookie 缺失即退出」语义；SPA 标签页不刷新的场景仍由请求 401 链兜底收敛）。
 * 2. Cookie 与本地不一致（另一子域登录/换号/令牌轮换后本域访问）：以 Cookie 为准覆盖
 *    本地——Cookie 由各端最近一次登录或静默刷新写入，代表最新登录态；本地旧令牌可能
 *    已被登出撤销，继续使用将触发 401→刷新失败→清态跳登录的连锁，且清态时误清 Cookie
 *    会破坏另一子域刚写入的新登录态。
 * 3. Cookie 与本地一致：无动作。
 * 仅同步不校验——令牌若已失效由各页面请求的 401 处理（静默刷新或跳登录）。
 * @returns {boolean} 是否发生了同步
 */
export function restoreAuthFromCookie() {
  if (!isH5()) return false
  try {
    const saved = readAuthCookie()
    if (!saved || !saved.access_token) {
      // Cookie 缺失：清除本地登录态（清除列表与 clearUser 一致）
      if (uni.getStorageSync('accessToken')) {
        uni.removeStorageSync('accessToken')
        uni.removeStorageSync('refreshToken')
        uni.removeStorageSync('userInfo')
      }
      return false
    }
    if (uni.getStorageSync('accessToken') === saved.access_token) return false
    uni.setStorageSync('accessToken', saved.access_token)
    if (saved.refresh_token) uni.setStorageSync('refreshToken', saved.refresh_token)
    if (saved.userInfo && saved.userInfo.id) uni.setStorageSync('userInfo', saved.userInfo)
    return true
  } catch (e) {
    return false
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

/** 读取 Cookie 中的登录态（无则返回 null） */
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
