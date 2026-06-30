/**
 * 统一请求封装（基于 uni.request）
 * --------------------------------------------------------------------------
 * - baseURL 从 VITE_API_BASE_URL 读取，开发环境回退到 localhost:8000
 * - 统一解析后端响应与错误：
 *   - 成功（2xx）：resolve 响应体
 *   - 失败：reject Error，message 兼容 FastAPI 校验错误（detail 数组）/ HTTPException（detail 字符串）/ 业务格式
 * - 网络失败（fail 回调）：保留微信小程序 errMsg 诊断信息，针对域名未配置场景给出明确指引
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function request({ url, method = 'GET', data, header, timeout }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: { 'Content-Type': 'application/json', ...header },
      timeout,
      success: (res) => {
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
