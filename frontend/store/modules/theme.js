import { defineStore } from 'pinia'
import { ref } from 'vue'

// 当前激活主题的本地持久化键
const THEME_STORAGE_KEY = 'app-theme'

// 主题清单（与 global.scss 中 [data-theme] 方案一一对应）
// key 用于 data-theme 属性与持久化；name 为用户可见名称（按代表色命名）；
// swatch 为选项预览色（主题代表色），用于 profile.vue 主题选择器的色块展示。
export const THEME_LIST = [
  { key: 'green', name: '青绿', swatch: '#2f6c00', swatchBg: '#e8ebe6' },
  { key: 'ink', name: '墨黑', swatch: '#171717', swatchBg: '#fafafa' }
]

export const useThemeStore = defineStore('theme', () => {
  // 默认主题为青绿（green），优先读取本地持久化值
  const current = ref(uni.getStorageSync(THEME_STORAGE_KEY) || 'green')

  // 切换并持久化主题（仅写入 key，具体配色由 global.scss 的 [data-theme] 方案块决定）
  function setTheme(key) {
    if (!THEME_LIST.some((t) => t.key === key)) return
    current.value = key
    try {
      uni.setStorageSync(THEME_STORAGE_KEY, key)
    } catch (e) {
      console.warn('保存主题偏好失败', e)
    }
  }

  return { current, setTheme }
})
