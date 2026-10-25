/**
 * 轻量国际化（i18n）核心
 * --------------------------------------------------------------------------
 * 设计取舍：不引入 vue-i18n，原因如下
 *   1. 工程为 HBuilderX 标准布局，内置编译器对第三方 Vue 插件的小程序端兼容性不可控；
 *   2. 本项目仅两种语言（zh-CN / en）、无复数与日期本地化等高级需求；
 *   3. 复用既有 themeMixin 的成熟链路（全局 mixin + Pinia 响应式），跨端行为已验证。
 *
 * 机制：
 *   - 词条集中在 locale/zh-CN.js 与 locale/en.js，结构为嵌套对象；
 *   - zh-CN 为兜底语言恒静态注册；H5 端 en 按需动态加载（loadLocale），
 *     小程序/App 端两套均静态注册（见下方条件编译块）；
 *   - main.js 注册全局 langMixin，向所有组件注入响应式 $t（依赖 languageStore.current）；
 *   - 语言切换 → store.current 变化 → 所有模板中的 $t(...) 自动重算 → 全站即时切换。
 *
 * 用法：
 *   模板：{{ $t('common.submit') }}、{{ $t('profile.usernameLimit', { max: 15 }) }}
 *   脚本：import { t } from '../../locale'; t('common.submit')
 */
import zhCN from './zh-CN'

// #ifndef H5
import en from './en'
// #endif

// 语言包注册表（新增语言仅需在此追加，并在 store/modules/language.js 的 LANGUAGE_LIST 增项）。
// 兜底语言 zh-CN 恒为静态注册（词条缺失回退依赖它同步可用）。
const MESSAGES = {
  'zh-CN': zhCN
}

// #ifndef H5
// 小程序/App 端不支持动态 import，en 与 zh-CN 一样静态注册（两套语言包随主包下发）
MESSAGES.en = en
// #endif

// #ifdef H5
// H5 端 en 改为按需动态加载：vite 将 en.js 拆为独立 chunk，首屏入口不再包含
// 英文词条（入口体积约减 80KB 源码）；英文用户首帧短暂回退中文文案，
// chunk 到达后由 languageStore 写入 current 触发 langMixin 全站重算刷新
let enLoading = null

function ensureEnLoaded() {
  if (MESSAGES.en) return Promise.resolve()
  if (!enLoading) {
    enLoading = import('./en').then((m) => {
      MESSAGES.en = m.default
    })
  }
  return enLoading
}
// #endif

/**
 * 确保指定语言的词条已注册（H5 端 en 为异步 chunk，其余语言恒同步可用）
 * @param {string} locale - 语言键
 * @returns {Promise<void>} 词条就绪后 resolve；加载失败 reject（调用方可回退）
 */
export function loadLocale(locale) {
  // #ifdef H5
  if (locale === 'en') return ensureEnLoaded()
  // #endif
  return Promise.resolve()
}

// 兜底语言：词条缺失时回退到简体中文，避免界面出现空白
const FALLBACK_LOCALE = 'zh-CN'

// 当前语言。由 store/modules/language.js 在初始化与切换时写入，
// 使纯 JS 模块（api/request.js、composables 等无组件上下文处）也能取到当前语言。
let currentLocale = FALLBACK_LOCALE

/**
 * 设置当前语言（仅供 languageStore 调用，业务代码请用 languageStore.setLanguage）
 * @param {string} locale - 语言键，如 'zh-CN' / 'en'
 */
export function setLocale(locale) {
  if (MESSAGES[locale]) currentLocale = locale
}

/**
 * 读取当前语言键
 * @returns {string}
 */
export function getLocale() {
  return currentLocale
}

/**
 * 按点号路径从语言包对象中取值
 * @param {Object} dict - 语言包对象
 * @param {string} path - 点号分隔路径，如 'profile.title'
 * @returns {string|undefined}
 */
function resolve(dict, path) {
  let node = dict
  for (const seg of path.split('.')) {
    if (node === null || typeof node !== 'object') return undefined
    node = node[seg]
  }
  return typeof node === 'string' ? node : undefined
}

/**
 * 翻译函数
 * @param {string} key - 词条路径，如 'common.confirm'
 * @param {Object} [params] - 插值参数，模板中以 {name} 占位
 * @param {string} [locale] - 指定语言，缺省用当前语言
 * @returns {string} 翻译结果；词条缺失时回退简体中文，仍缺失则返回 key 本身
 */
export function t(key, params, locale) {
  const lang = locale || currentLocale
  let text = resolve(MESSAGES[lang] || {}, key)
  if (text === undefined) text = resolve(MESSAGES[FALLBACK_LOCALE], key)
  if (text === undefined) return key
  if (!params) return text
  // 插值：将 {name} 替换为 params.name，未提供的占位保持原样便于排查
  return text.replace(/\{(\w+)\}/g, (raw, name) =>
    Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : raw
  )
}

/**
 * 取语言包原始值（支持数组 / 对象，不做字符串化处理与插值）。
 * 用于需要数组/对象的词条（如月份标签、星期数组），这些无法用 t() 返回。
 * 缺失时回退简体中文，仍缺失返回 undefined。
 * @param {string} key - 词条路径
 * @param {string} [locale] - 指定语言，缺省用当前语言
 * @returns {any}
 */
export function tm(key, locale) {
  const lang = locale || currentLocale
  // 直接深层取值并返回原始值（支持数组/对象），不复用 resolve：
  // resolve 仅返回 string（数组/对象会被其 typeof 过滤为 undefined），故此处独立取值。
  let node = getNode(MESSAGES[lang] || {}, key)
  if (node === undefined) node = getNode(MESSAGES[FALLBACK_LOCALE], key)
  return node
}

// 按点号路径从对象中取值，返回原始值（不过滤类型，数组/对象/字符串均可）
function getNode(dict, path) {
  let node = dict
  for (const seg of path.split('.')) {
    if (node === null || typeof node !== 'object' || !(seg in node)) return undefined
    node = node[seg]
  }
  return node
}

export { MESSAGES, FALLBACK_LOCALE }
