/**
 * useInputLimit —— 输入框字符过滤与长度限制
 * --------------------------------------------------------------------------
 * 功能：
 *   1. 字符限制与后端字段严格匹配（通过 maxLength 参数传入，配合 input 组件 :maxlength）
 *   2. 特殊字符过滤（通过 allowedPattern 白名单正则过滤非法字符）
 *   3. 字符限制提示：仅在用户达到上限后继续输入时显示已达 X 字上限，未达上限或刚达到上限时不显示
 *
 * 设计原则：
 *   - 长度上限由 input 组件 :maxlength 属性硬性限制
 *   - 达到上限时不立即显示提示，仅当用户在该状态下继续尝试输入时才触发
 *   - 未达上限时不显示任何提示信息
 *
 * 使用方式：
 *   const usernameLimit = useInputLimit(15, /^[\u4e00-\u9fa5a-zA-Z0-9]$/)
 *   <input v-model="form.username" :maxlength="usernameLimit.max"
 *     @input="e => form.username = usernameLimit.handleInput(e)" />
 *   <text v-if="usernameLimit.limitReached" class="...">{{ usernameLimit.limitHint }}</text>
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
 *   max: number,
 *   filter: (v: string) => string,
 *   handleInput: (event: any) => string,
 *   wasAtLimit: import('vue').Ref<boolean>,
 *   limitReached: import('vue').Ref<boolean>,
 *   limitHint: import('vue').ComputedRef<string>,
 *   checkLimit: (value: string) => void
 * }}
 */
export function useInputLimit(maxLength, allowedPattern) {
  // 最大字符数（供模板 :maxlength 绑定）
  const max = maxLength
  // 上一次输入后是否已达上限（用于判断本次输入是否属于"超限后继续输入"）
  const wasAtLimit = ref(false)
  // 是否触发超限提示（仅当 wasAtLimit 为 true 且当前值仍达上限时显示）
  const limitReached = ref(false)
  // 上限提示文本（仅超限触发时有值）
  const limitHint = computed(() => limitReached.value ? `已达 ${maxLength} 字上限` : '')

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
   * input 组件 @input 事件统一处理：过滤字符 → 更新超限状态 → 返回新值
   * 提示触发规则：仅当用户在上一次已达上限后继续尝试输入时才显示提示
   * 在模板中用法：@input="e => form.username = usernameLimit.handleInput(e)"
   * @param {any} event - input 组件事件对象
   * @returns {string} 过滤后的新值
   */
  function handleInput(event) {
    const raw = (event && event.detail && event.detail.value) || ''
    const result = filter(raw)
    // 仅当 wasAtLimit 为 true（上一次已达上限）且当前仍达上限时，才触发提示
    limitReached.value = wasAtLimit.value && result.length >= maxLength
    // 更新 wasAtLimit 状态供下次输入判断
    wasAtLimit.value = result.length >= maxLength
    return result
  }

  /**
   * 手动同步当前值是否已达上限（用于 v-model 直接赋值等非 @input 场景）
   * 仅更新 wasAtLimit 内部状态，不触发超限提示
   * @param {string} value - 当前输入值
   */
  function checkLimit(value) {
    wasAtLimit.value = (value || '').length >= maxLength
  }

  return { max, filter, handleInput, limitReached, limitHint, checkLimit }
}
