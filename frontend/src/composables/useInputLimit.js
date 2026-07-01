/**
 * useInputLimit —— 输入框字符限制与友好提示
 * --------------------------------------------------------------------------
 * 功能：
 *   1. 字符限制与后端字段严格匹配（通过 maxLength 参数传入）
 *   2. 实时输入长度监测，接近限制时提供视觉提示（剩余字符数）
 *   3. 达到字符限制时阻止继续输入（配合 input 组件 :maxlength 属性）
 *   4. 特殊字符过滤（通过 allowedPattern 白名单正则过滤非法字符）
 *   5. 提示信息在各种屏幕尺寸下清晰可见（通过 CSS 类名控制样式）
 *
 * 使用方式：
 *   const usernameLimit = useInputLimit(15, /^[\u4e00-\u9fa5a-zA-Z0-9]$/)
 *   <input v-model="form.username" :maxlength="usernameLimit.max.value"
 *     @input="e => onInput(e, 'username', usernameLimit)" />
 *   <text v-if="usernameLimit.hint.value"
 *     :class="['input-limit-hint', { 'input-limit-hint--near': usernameLimit.isNear.value,
 *     'input-limit-hint--full': usernameLimit.isFull.value }]">
 *     {{ usernameLimit.hint.value }}
 *   </text>
 *
 * 参考：
 *   - Vue 3 组合式函数（Composables）官方文档
 *     https://cn.vuejs.org/guide/reusability/composables.html
 *   - 微信小程序 input 组件 maxlength 属性
 *     https://developers.weixin.qq.com/miniprogram/dev/component/input.html
 */
import { ref, computed } from 'vue'

/**
 * 创建单个输入框的限制器
 * @param {number} maxLength - 最大字符数（与后端字段限制严格匹配）
 * @param {RegExp} [allowedPattern] - 允许的单字符正则（白名单），不匹配的字符将被过滤。
 *        不传则不过滤字符（仅限长度）。正则应匹配单个字符，如 /^[a-zA-Z0-9]$/
 * @returns {{
 *   count: import('vue').Ref<number>,
 *   max: number,
 *   isNear: import('vue').ComputedRef<boolean>,
 *   isFull: import('vue').ComputedRef<boolean>,
 *   hint: import('vue').ComputedRef<string>,
 *   filter: (v: string) => string,
 *   sync: (v: string) => void,
 *   handleInput: (event: any) => string
 * }}
 */
export function useInputLimit(maxLength, allowedPattern) {
  // 当前已输入字符数
  const count = ref(0)
  // 最大字符数（供模板 :maxlength 绑定）
  const max = maxLength

  // 是否接近限制：剩余字符数 <= 阈值（取 max 的 15% 与 3 的较大值，确保短文本也有提示）
  const isNear = computed(
    () => count.value > 0 && maxLength - count.value <= Math.max(3, Math.ceil(maxLength * 0.15))
  )

  // 是否已达限制
  const isFull = computed(() => count.value >= maxLength)

  // 提示文案：接近时显示剩余字符数，达到时显示已达上限
  const hint = computed(() => {
    if (isFull.value) return `已达上限 ${maxLength} 字`
    if (isNear.value) return `还可输入 ${maxLength - count.value} 字`
    return ''
  })

  /**
   * 过滤非法字符并截断到最大长度
   * @param {string} v - 原始输入值
   * @returns {string} 过滤+截断后的值
   */
  function filter(v) {
    let val = v || ''
    // 白名单正则过滤：逐字符判断，仅保留匹配的字符
    if (allowedPattern) {
      val = val
        .split('')
        .filter((ch) => allowedPattern.test(ch))
        .join('')
    }
    // 截断到最大长度（双重保险，maxlength 属性可能因平台差异不完全可靠）
    if (val.length > maxLength) {
      val = val.substring(0, maxLength)
    }
    return val
  }

  /**
   * 同步计数（v-model 值变化时调用）
   * @param {string} v - 当前 v-model 值
   */
  function sync(v) {
    count.value = (v || '').length
  }

  /**
   * input 组件 @input 事件统一处理：过滤字符 → 同步计数 → 返回新值
   * 在模板中用法：@input="e => onInput(e, 'username', usernameLimit)"
   * 或直接使用返回值赋给 v-model 字段
   * @param {any} event - input 组件事件对象
   * @returns {string} 过滤后的新值
   */
  function handleInput(event) {
    const raw = (event && event.detail && event.detail.value) || ''
    const filtered = filter(raw)
    count.value = filtered.length
    return filtered
  }

  return { count, max, isNear, isFull, hint, filter, sync, handleInput }
}
