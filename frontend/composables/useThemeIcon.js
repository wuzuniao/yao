import { computed } from 'vue'
import { useThemeStore } from '../store/modules/theme'

/**
 * 主题图标组合式函数：按当前主题返回换色适配后的图标地址
 * --------------------------------------------------------------------------
 * 约定：
 * - green（wise 默认）主题直接使用 assets/images 原图（调用方静态 import 后作为 original 传入）；
 * - 其余 9 套主题使用构建期批量换色产物 /static/theme-icons/{主题}/{文件名}.png
 *   （由 scripts/gen-theme-icons.js 生成，映射规则与 global.scss 各主题 palette 对齐，
 *   白色图标/头像/二维码/删除红/微信绿图标不参与换色，仍引用原图）。
 *
 * @param {string} name 图标文件名，须与 assets/images 内原图同名（如 'dh_shouye_1.png'）
 * @param {string} original 原图静态 import 地址（green 主题回落值）
 * @returns {import('vue').ComputedRef<string>} 当前主题应使用的图标地址
 */
export function useThemeIcon(name, original) {
  const themeStore = useThemeStore()
  return computed(() =>
    themeStore.current === 'green'
      ? original
      : `/static/theme-icons/${themeStore.current}/${name}`
  )
}
