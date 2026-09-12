/**
 * 统一请求封装（基于 uni.request）
 * --------------------------------------------------------------------------
 * - baseURL 从 config/env.js 读取（按环境区分，兼容 HBuilderX 与 CLI 构建）；
 *   request() 支持 baseUrl 参数覆盖默认值（用户模块接口直连 auth 服务域名）
 * - 自动附加 JWT：从本地存储读取 accessToken，存在则添加 Authorization: Bearer <token>
 * - 统一解析后端响应与错误：
 *   - 成功（2xx）：resolve 响应体
 *   - 失败：reject Error，message 兼容 FastAPI 校验错误（detail 数组）/ HTTPException（detail 字符串）/ 业务格式
 * - 401 处理（静默刷新重试）：
 *   - 非刷新请求且本地存在 refreshToken 时，先经 uni.request 直连
 *     AUTH_BASE_URL + /oauth/token 静默刷新（轮换制，更新双 token），
 *     成功则重试原请求一次（重试请求带 skipAuthRefresh 标记防递归）；
 *   - 刷新失败或重试仍 401 才走 _handleUnauthorized（清态跳登录页）；
 *   - 并发 401 共享同一次刷新请求（_refreshPromise 去重）
 * - 网络失败（fail 回调）：保留微信小程序 errMsg 诊断信息，针对域名未配置场景给出明确指引
 */
import { API_BASE_URL, AUTH_BASE_URL, AUTH_CLIENT_ID } from '../config/env'
import { t } from '../locale'
import { syncAuthCookie, clearAuthCookie } from '../utils/authCookie'

const BASE_URL = API_BASE_URL

// 登录页路由（401 时跳转目标，避免循环跳转）
const LOGIN_PAGE = '/pages/user/login'

// 标记是否已触发 401 跳转，防止短时间内多次 401 重复弹窗
let _isHandling401 = false

// 共享的静默刷新 Promise（并发 401 只发一次刷新请求）
let _refreshPromise = null

/**
 * 读取本地 JWT access_token
 * 直接用 uni.getStorageSync 读取，避免 import store 导致循环依赖
 */
function _getAccessToken() {
  try {
    return uni.getStorageSync('accessToken') || ''
  } catch (e) {
    return ''
  }
}

/**
 * 读取本地 refresh_token（auth 服务签发，14 天轮换制）
 */
function _getRefreshToken() {
  try {
    return uni.getStorageSync('refreshToken') || ''
  } catch (e) {
    return ''
  }
}

/**
 * 401 处理：清除本地登录态，提示用户并跳转登录页
 * - 仅在本地存在 token 但收到 401 时提示"登录已过期"（说明 token 失效）
 * - 本地无 token 的 401 视为未登录访问，静默跳转登录页
 * - 使用 _isHandling401 标记防止并发请求同时触发多次跳转
 */
function _handleUnauthorized() {
  if (_isHandling401) return
  _isHandling401 = true
  const hadToken = !!_getAccessToken()
  // 清除本地登录态
  try {
    uni.removeStorageSync('accessToken')
    uni.removeStorageSync('refreshToken')
    uni.removeStorageSync('userInfo')
  } catch (e) {
    console.warn('清除本地登录态失败', e)
  }
  // 同步清除父域 SSO Cookie（H5），避免另一子域仍读到已失效令牌
  clearAuthCookie()
  if (hadToken) {
    uni.showToast({ title: t('request.sessionExpired'), icon: 'none' })
  }
  setTimeout(() => {
    uni.reLaunch({ url: LOGIN_PAGE, complete: () => { _isHandling401 = false } })
  }, hadToken ? 1500 : 0)
}

/**
 * 静默刷新令牌（直连 auth 服务 /oauth/token，refresh_token 轮换制）
 * - 成功后更新本地双 token（accessToken / refreshToken）并 resolve 新 access_token
 * - 并发调用共享同一 Promise（轮换制下并发刷新会触发重放检测导致全端下线）
 * - 内联实现 uni.request，避免与 api/modules/user.js 循环依赖
 */
function _silentRefresh() {
  if (_refreshPromise) return _refreshPromise
  _refreshPromise = new Promise((resolve, reject) => {
    const refreshTokenValue = _getRefreshToken()
    let deviceId = ''
    try {
      deviceId = uni.getStorageSync('biometricDeviceId') || ''
    } catch (e) {
      deviceId = ''
    }
    const body = {
      grant_type: 'refresh_token',
      refresh_token: refreshTokenValue,
      client_id: AUTH_CLIENT_ID
    }
    if (deviceId) body.device_id = deviceId
    uni.request({
      url: AUTH_BASE_URL + '/oauth/token',
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: body,
      timeout: 10000,
      success: (res) => {
        // /oauth/token 成功直接返回令牌三件套（非 {code,msg,data} 业务格式）
        if (res.statusCode >= 200 && res.statusCode < 300 && res.data && res.data.access_token) {
          try {
            uni.setStorageSync('accessToken', res.data.access_token)
            if (res.data.refresh_token) {
              uni.setStorageSync('refreshToken', res.data.refresh_token)
            }
          } catch (e) {
            console.warn('保存刷新后的令牌失败', e)
          }
          // 同步刷新后的令牌到父域 SSO Cookie（H5），保持另一子域登录态可用
          syncAuthCookie({
            access_token: res.data.access_token,
            refresh_token: res.data.refresh_token,
            expires_in: res.data.expires_in
          })
          resolve(res.data.access_token)
        } else {
          reject(new Error('refresh token failed'))
        }
      },
      fail: (err) => reject(new Error((err && err.errMsg) || 'refresh token failed'))
    })
  })
  // 结束后重置共享标记（不使用 finally，兼容旧引擎）
  const cleanup = () => { _refreshPromise = null }
  _refreshPromise.then(cleanup, cleanup)
  return _refreshPromise
}

export function request({ url, method = 'GET', data, header, timeout, baseUrl, skipAuthRefresh }) {
  return new Promise((resolve, reject) => {
    // 构造请求头：默认 Content-Type，附加 JWT Authorization 头（若存在 token）
    const reqHeader = { 'Content-Type': 'application/json', ...header }
    const token = _getAccessToken()
    if (token) {
      reqHeader['Authorization'] = `Bearer ${token}`
    }
    uni.request({
      url: (baseUrl || BASE_URL) + url,
      method,
      data,
      header: reqHeader,
      timeout,
      success: (res) => {
        // 401 未授权：token 失效或缺失
        if (res.statusCode === 401) {
          // 静默刷新重试：非刷新请求且本地有 refreshToken 时先刷新再重试一次
          if (!skipAuthRefresh && _getRefreshToken()) {
            _silentRefresh()
              .then(() => {
                // 刷新成功：重试原请求一次（skipAuthRefresh 防递归）
                request({ url, method, data, header, timeout, baseUrl, skipAuthRefresh: true })
                  .then(resolve, reject)
              })
              .catch(() => {
                // 刷新失败（refresh_token 已失效/被撤销）：清态跳登录
                _handleUnauthorized()
                reject(new Error(t('request.sessionExpired')))
              })
            return
          }
          _handleUnauthorized()
          reject(new Error(t('request.sessionExpired')))
          return
        }
        // 429 限流：请求过于频繁，展示后端 detail 文案或本地化提示，不跳转登录页
        if (res.statusCode === 429) {
          let msg = t('request.tooManyRequests')
          const detail = res.data && res.data.detail
          if (typeof detail === 'string' && detail) {
            msg = detail
          }
          reject(new Error(msg))
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        // 解析错误信息
        let msg = t('request.failed')
        const detail = res.data && res.data.detail
        if (typeof detail === 'string') {
          msg = detail
        } else if (Array.isArray(detail)) {
          // Pydantic 校验错误：[{ msg: '...' }, ...]
          msg = detail.map((e) => e.msg).join(t('request.errorSeparator'))
        }
        reject(new Error(msg))
      },
      fail: (err) => {
        // 保留请求失败诊断信息（如微信小程序 "request:fail url not in domain list"）
        const errMsg = (err && err.errMsg) || ''
        let msg = '网络请求失败'
        // 微信小程序端错误文案（开发期常见原因：未在开发者工具勾选「不校验合法域名」）
        // #ifdef MP-WEIXIN
        if (errMsg.includes('domain') || errMsg.includes('url not in')) {
          msg = t('request.domainNotConfigured')
        } else if (errMsg.includes('timeout')) {
          msg = t('request.timeout')
        } else if (errMsg.includes('refused') || errMsg.includes('ECONNREFUSED')) {
          // 仅本地后端（开发环境）提示确认后端已启动；生产/远程后端走通用文案，避免本地地址误导用户
          msg = (baseUrl || BASE_URL).includes('localhost') ? t('request.connectRefusedMp') : t('request.connectRefusedRemote')
        } else if (errMsg) {
          msg = t('request.networkFailedDetail', { detail: errMsg })
        }
        // #endif
        // H5 端错误文案（浏览器 fetch/XHR 错误）
        // #ifndef MP-WEIXIN
        if (errMsg.includes('timeout')) {
          msg = t('request.timeout')
        } else if (errMsg.includes('Network Error') || errMsg.includes('Failed to fetch')) {
          msg = t('request.connectRefusedH5')
        } else if (errMsg) {
          msg = t('request.networkFailedDetail', { detail: errMsg })
        }
        // #endif
        const e = new Error(msg)
        e.errMsg = errMsg
        e.isNetworkError = true
        reject(e)
      }
    })
  })
}
