/**
 * useInputLimit —— 输入框字符过滤与长度限制
 * --------------------------------------------------------------------------
 * 功能：
 *   1. 字符限制与后端字段严格匹配（通过 maxLength 参数传入，配合 input 组件 :maxlength）
 *   2. 特殊字符过滤（通过 allowedPattern 白名单正则过滤非法字符）
 *
 * 设计原则：
 *   仅在用户输入违反规则时才显示提示（由各页面 errors 字段驱动错误提示），
 *   不再提供"还可输入 X 字""已达上限"等冗余计数提示。
 *   长度上限由 input 组件 :maxlength 属性硬性限制，无需文字提示。
 *
 * 使用方式：
 *   const usernameLimit = useInputLimit(15, /^[\u4e00-\u9fa5a-zA-Z0-9]$/)
 *   <input v-model="form.username" :maxlength="usernameLimit.max"
 *     @input="e => form.username = usernameLimit.handleInput(e)" />
 *
 * 参考：
 *   - Vue 3 组合式函数（Composables）官方文档
 *     https://cn.vuejs.org/guide/reusability/composables.html
 *   - 微信小程序 input 组件 maxlength 属性
 *     https://developers.weixin.qq.com/miniprogram/dev/component/input.html
 */

/**
 * 创建单个输入框的限制器
 * @param {number} maxLength - 最大字符数（与后端字段限制严格匹配）
 * @param {RegExp} [allowedPattern] - 允许的单字符正则（白名单），不匹配的字符将被过滤。
 *        不传则不过滤字符（仅限长度）。正则应匹配单个字符，如 /^[a-zA-Z0-9]$/
 * @returns {{
 *   max: number,
 *   filter: (v: string) => string,
 *   handleInput: (event: any) => string
 * }}
 */
export function useInputLimit(maxLength, allowedPattern) {
  // 最大字符数（供模板 :maxlength 绑定）
  const max = maxLength

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
   * input 组件 @input 事件统一处理：过滤字符 → 返回新值
   * 在模板中用法：@input="e => form.username = usernameLimit.handleInput(e)"
   * @param {any} event - input 组件事件对象
   * @returns {string} 过滤后的新值
   */
  function handleInput(event) {
    const raw = (event && event.detail && event.detail.value) || ''
    return filter(raw)
  }

  return { max, filter, handleInput }
}
