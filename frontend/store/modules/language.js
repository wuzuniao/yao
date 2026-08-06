import { defineStore } from 'pinia'
import { ref } from 'vue'

// 当前语言偏好的本地持久化键
const LANGUAGE_STORAGE_KEY = 'app-language'

// 支持的语言清单（本期仅做按钮切换，暂不接入翻译）
export const LANGUAGE_LIST = [
  { key: 'zh-CN', name: '简体中文' },
  { key: 'en', name: 'English' }
]

export const useLanguageStore = defineStore('language', () => {
  // 默认简体中文，优先读取本地持久化值
  const current = ref(uni.getStorageSync(LANGUAGE_STORAGE_KEY) || 'zh-CN')

  // 切换并持久化语言偏好（本期仅记录用户选择，暂不翻译界面）
  function setLanguage(key) {
    if (!LANGUAGE_LIST.some((l) => l.key === key)) return
    current.value = key
    try {
      uni.setStorageSync(LANGUAGE_STORAGE_KEY, key)
    } catch (e) {
      console.warn('保存语言偏好失败', e)
    }
  }

  return { current, setLanguage }
})
