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
// App 端（Android/iOS/HarmonyOS）恒定使用生产 HTTPS 域名，原因：
//   1. HBuilderX「运行到手机」时 NODE_ENV 为 development，若沿用 localhost，
//      真机上 localhost 指向手机自身，所有接口必然失败。
//   2. Android 9+、iOS ATS 与鸿蒙默认禁止明文 HTTP，局域网 IP 亦需额外放行配置。
// 如需 App 端连本地后端联调，把下方 IS_APP 判断临时改为局域网 IP，
// 并在 manifest.json 的 app-plus.distribute.android 开启 usesCleartextTraffic。
// UNI_PLATFORM 由 uni-app 编译期静态替换为字符串字面量（Android/iOS 为 'app-plus'，
// 鸿蒙为 'app-harmony'），两者都属 App 端，单分支声明避免重复导出。
const IS_APP = process.env.UNI_PLATFORM === 'app-plus' || process.env.UNI_PLATFORM === 'app-harmony'
export const API_BASE_URL = IS_APP
  ? 'https://yao.wuzuniao.com'
  : (process.env.NODE_ENV === 'production'
      ? 'https://yao.wuzuniao.com'
      : 'http://localhost:8000')

// 微信订阅消息模板 ID（一次性订阅，打卡提醒模板）
// 全端始终导出：模板 ID 属公开信息，无敏感风险；import 处（useWechatSubscribe.js）
// 在任意平台都需能静态解析到该名字，避免非微信端打包时「未导出」构建失败。
// 实际仅微信小程序端使用，使用处由 #ifdef MP-WEIXIN 隔离，非微信端取到空串由调用方兜底。
export const WX_SUBSCRIBE_TEMPLATE_ID = 'Tvn1TtWubjqi0RrYRRTjQgg9qaTB3Fntzt0Jju8RmEY'

// 分享封面图（词云 + logo，500x400 PNG）的网络地址
// --------------------------------------------------------------------------
// 图片单份存放于 frontend/static/share-cover.png（App/H5 构建随 static 目录正常
// 拷贝；H5 部署后通过 https://yao.wuzuniao.com/static/share-cover.png 访问）。
// 小程序构建不含此本地图片：由 vite.config.js 的 removeUnusedAssetsForMpWeixin
// 插件在打包完成后从产物清理（与 static/app-icons 同模式），避免撑大主包。
// 各端分享统一引用此 https 网络地址。
// 开发与生产同值：纯静态资源无环境差异；H5 未部署前小程序分享封面
// 加载不到该图会回落自动截图，不影响其他功能。
// 注意：小程序真机使用网络图片作为分享封面，须在小程序管理后台将
// yao.wuzuniao.com 配置为 downloadFile 合法域名（开发者工具关闭校验时可直接预览）。
export const SHARE_COVER_URL = 'https://yao.wuzuniao.com/static/share-cover.png'
