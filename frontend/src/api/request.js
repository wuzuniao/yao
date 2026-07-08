/**
 * 统一请求封装（基于 uni.request）
 * --------------------------------------------------------------------------
 * - baseURL 从 VITE_API_BASE_URL 读取，开发环境回退到 localhost:8000
 * - 自动附加 JWT：从本地存储读取 accessToken，存在则添加 Authorization: Bearer <token>
 * - 统一解析后端响应与错误：
 *   - 成功（2xx）：resolve 响应体
 *   - 失败：reject Error，message 兼容 FastAPI 校验错误（detail 数组）/ HTTPException（detail 字符串）/ 业务格式
 * - 401 处理：token 失效时清除本地登录态并跳转登录页（避免在登录页重复跳转）
 * - 网络失败（fail 回调）：保留微信小程序 errMsg 诊断信息，针对域名未配置场景给出明确指引
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 登录页路由（401 时跳转目标，避免循环跳转）
const LOGIN_PAGE = '/pages/user/login'

// 标记是否已触发 401 跳转，防止短时间内多次 401 重复弹窗
let _isHandling401 = false

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
    uni.removeStorageSync('userInfo')
  } catch (e) {
    console.warn('清除本地登录态失败', e)
  }
  if (hadToken) {
    uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
  }
  setTimeout(() => {
    uni.reLaunch({ url: LOGIN_PAGE, complete: () => { _isHandling401 = false } })
  }, hadToken ? 1500 : 0)
}

export function request({ url, method = 'GET', data, header, timeout }) {
  return new Promise((resolve, reject) => {
    // 构造请求头：默认 Content-Type，附加 JWT Authorization 头（若存在 token）
    const reqHeader = { 'Content-Type': 'application/json', ...header }
    const token = _getAccessToken()
    if (token) {
      reqHeader['Authorization'] = `Bearer ${token}`
    }
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: reqHeader,
      timeout,
      success: (res) => {
        // 401 未授权：token 失效或缺失，触发统一登录态清理与跳转
        if (res.statusCode === 401) {
          _handleUnauthorized()
          reject(new Error('登录已过期，请重新登录'))
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        // 解析错误信息
        let msg = '请求失败'
        const detail = res.data && res.data.detail
        if (typeof detail === 'string') {
          msg = detail
        } else if (Array.isArray(detail)) {
          // Pydantic 校验错误：[{ msg: '...' }, ...]
          msg = detail.map((e) => e.msg).join('；')
        }
        reject(new Error(msg))
      },
      fail: (err) => {
        // 保留微信小程序 errMsg 诊断信息（如 "request:fail url not in domain list"）
        const errMsg = (err && err.errMsg) || ''
        let msg = '网络请求失败'
        // 微信小程序开发期常见原因：未在开发者工具勾选「不校验合法域名」
        if (errMsg.includes('domain') || errMsg.includes('url not in')) {
          msg = '请求域名未配置：请在微信开发者工具 → 详情 → 本地设置，勾选「不校验合法域名、web-view、TLS 版本以及 HTTPS 证书」'
        } else if (errMsg.includes('timeout')) {
          msg = '请求超时，请检查后端服务是否启动'
        } else if (errMsg.includes('refused') || errMsg.includes('ECONNREFUSED')) {
          msg = '无法连接后端服务，请确认后端已启动（localhost:8000）'
        } else if (errMsg) {
          msg = `网络请求失败：${errMsg}`
        }
        const e = new Error(msg)
        e.errMsg = errMsg
        e.isNetworkError = true
        reject(e)
      }
    })
  })
}
