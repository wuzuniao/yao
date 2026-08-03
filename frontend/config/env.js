/**
 * 全端环境配置
 * --------------------------------------------------------------------------
 * 为什么不用 .env / import.meta.env：
 *   HBuilderX 内置编译器不加载 .env 文件，`import.meta.env.VITE_*` 会取到
 *   undefined，导致接口地址静默回退到 localhost、订阅消息模板 ID 变空串。
 *   为同时支持 HBuilderX（App/iOS/多端小程序）与 CLI 构建，改用本常量模块，
 *   通过 uni-app 条件编译区分开发与生产环境。
 *
 * 使用方式：
 *   import { API_BASE_URL, WX_SUBSCRIBE_TEMPLATE_ID } from '../config/env'
 *
 * 切换生产环境：
 *   HBuilderX：菜单「发行」构建时自动进入 #ifdef 的生产分支（NODE_ENV=production）
 *   CLI：`npm run build:mp-weixin` 同样进入生产分支
 *   本地开发（运行/dev）走开发分支
 *
 * 注意：本文件提交 Git，不得写入密码、密钥等敏感信息。
 *      模板 ID 与接口域名属公开信息，可安全提交。
 */

// 后端 API 基础地址
// App 端（Android/iOS）恒定使用生产 HTTPS 域名，原因：
//   1. HBuilderX「运行到手机」时 NODE_ENV 为 development，若沿用 localhost，
//      真机上 localhost 指向手机自身，所有接口必然失败。
//   2. Android 9+ 与 iOS ATS 默认禁止明文 HTTP，局域网 IP 亦需额外放行配置。
// 如需 App 端连本地后端联调，把下方 APP_PLUS 判断临时改为局域网 IP，
// 并在 manifest.json 的 app-plus.distribute.android 开启 usesCleartextTraffic。
// UNI_PLATFORM 由 uni-app 编译期静态替换为字符串字面量（如 'app-plus'），单分支声明避免重复导出。
const APP_PLUS = process.env.UNI_PLATFORM === 'app-plus'
export const API_BASE_URL = APP_PLUS
  ? 'https://yao.wuzuniao.com'
  : (process.env.NODE_ENV === 'production'
      ? 'https://yao.wuzuniao.com'
      : 'http://localhost:8000')

// 微信订阅消息模板 ID（一次性订阅，打卡提醒模板）
// 全端始终导出：模板 ID 属公开信息，无敏感风险；import 处（useWechatSubscribe.js）
// 在任意平台都需能静态解析到该名字，避免非微信端打包时「未导出」构建失败。
// 实际仅微信小程序端使用，使用处由 #ifdef MP-WEIXIN 隔离，非微信端取到空串由调用方兜底。
export const WX_SUBSCRIBE_TEMPLATE_ID = 'Tvn1TtWubjqi0RrYRRTjQgg9qaTB3Fntzt0Jju8RmEY'
