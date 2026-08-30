import { defineStore } from 'pinia'
import { ref } from 'vue'

// 当前激活主题的本地持久化键
const THEME_STORAGE_KEY = 'app-theme'

// 主题清单（与 global.scss 中 [data-theme] 方案一一对应）
// key 用于 data-theme 属性与持久化；name 为用户可见名称（按代表色命名）；
// swatch 为选项预览色，统一取各主题 global.scss 的 --palette-brand-light（品牌亮色），
// 展示主题最鲜明的代表色；ink 主题品牌亮色为浅灰不可辨，取墨黑本色 #171717。
// 用于 profile.vue 主题选择器的色块展示。
export const THEME_LIST = [
  { key: 'green', name: '青绿', swatch: '#9fe870' },
  { key: 'ink', name: '墨黑', swatch: '#171717' },
  { key: 'indigo', name: '靛蓝', swatch: '#b9b9f9' },
  { key: 'cyan', name: '青碧', swatch: '#67d3ea' },
  { key: 'amber', name: '琥珀', swatch: '#fbbf24' },
  { key: 'coral', name: '珊瑚', swatch: '#ff9b91' },
  { key: 'rose', name: '玫瑰', swatch: '#f472b6' },
  { key: 'crimson', name: '绯红', swatch: '#f87171' },
  { key: 'gold', name: '流金', swatch: '#e3c45c' },
  { key: 'lavender', name: '薰衣草', swatch: '#828fff' }
]

export const useThemeStore = defineStore('theme', () => {
  // 默认主题为青绿（green），优先读取本地持久化值
  const current = ref(uni.getStorageSync(THEME_STORAGE_KEY) || 'green')

  // H5 端：将当前主题同步到 <html> 的 data-theme 属性。
  // 原因：H5 端页面根 view（带 data-theme）只覆盖内容区；<html>/<body> 背景（页面外区域，
  // 尤其 PC 浏览器两侧留白）由 :root/html 的 background-color: var(--page-bg-color) 承载，
  // 而 html 本身不带 data-theme，故取默认绿主题值、不随主题切换。给 html 设 data-theme 后，
  // html[data-theme="x"] 命中 global.scss 方案块，页面外背景随主题切换。
  // 小程序/App 端 html 概念不适用，用 #ifdef H5 隔离避免报错。
  function syncHtmlTheme(key) {
    /* #ifdef H5 */
    if (typeof document !== 'undefined') {
      document.documentElement.dataset.theme = key
    }
    /* #endif */
  }

  // 初始化时同步一次（首屏避免页面外背景闪现默认绿）
  syncHtmlTheme(current.value)

  // 切换并持久化主题（仅写入 key，具体配色由 global.scss 的 [data-theme] 方案块决定）
  function setTheme(key) {
    if (!THEME_LIST.some((t) => t.key === key)) return
    current.value = key
    syncHtmlTheme(key)
    try {
      uni.setStorageSync(THEME_STORAGE_KEY, key)
    } catch (e) {
      console.warn('保存主题偏好失败', e)
    }
  }

  return { current, setTheme }
})
