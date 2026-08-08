import { defineStore } from 'pinia'
import { ref } from 'vue'
import { setLocale } from '../../locale'

// 当前语言偏好的本地持久化键
const LANGUAGE_STORAGE_KEY = 'app-language'

// 支持的语言清单（name 用各语言自身书写，不参与翻译，符合语言选择器惯例）
export const LANGUAGE_LIST = [
  { key: 'zh-CN', name: '简体中文' },
  { key: 'en', name: 'English' }
]

// 根据设备地区推断默认语言：中国相关地区（含大陆/港澳台）默认简体中文，其余默认 English。
// 仅在用户未显式持久化过语言偏好时作为兜底，不影响已保存的偏好。
function detectDefaultLocale() {
  let sys = ''
  try {
    sys = (typeof uni.getLocale === 'function' && uni.getLocale()) ||
      uni.getSystemInfoSync().language || ''
  } catch (e) {
    sys = ''
  }
  sys = String(sys).toLowerCase().replace('_', '-')
  // 全部 zh 变体（zh、zh-CN、zh-Hans、zh-HK、zh-TW、zh-MO、zh-Hant 等）均视为中国相关地区
  if (sys.startsWith('zh')) return 'zh-CN'
  return 'en'
}

export const useLanguageStore = defineStore('language', () => {
  // 优先读取本地持久化值；无持久化偏好时按设备地区推断默认语言
  const stored = uni.getStorageSync(LANGUAGE_STORAGE_KEY)
  const initial = stored && LANGUAGE_LIST.some((l) => l.key === stored)
    ? stored
    : detectDefaultLocale()
  const current = ref(initial)

  // 初始化时同步给 locale 核心，使纯 JS 模块（api/request.js 等无组件上下文处）
  // 在首屏即可取到正确语言
  setLocale(current.value)

  // 切换并持久化语言偏好。
  // current 为响应式 ref，变更后 main.js 注册的 langMixin 中的 $t 会重算，
  // 所有模板文案即时切换，无需刷新页面。
  function setLanguage(key) {
    if (!LANGUAGE_LIST.some((l) => l.key === key)) return
    current.value = key
    setLocale(key)
    try {
      uni.setStorageSync(LANGUAGE_STORAGE_KEY, key)
    } catch (e) {
      console.warn('保存语言偏好失败', e)
    }
  }

  return { current, setLanguage }
})
