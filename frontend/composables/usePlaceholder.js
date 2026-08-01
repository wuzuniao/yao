/**
 * usePlaceholder —— 输入框 placeholder 聚焦交互复用逻辑
 * --------------------------------------------------------------------------
 * 适用场景：login.vue / register.vue / plan.vue / notification.vue 共 4 个页面的输入框，
 *   交互效果完全一致：
 *   - 聚焦（focus）：placeholder 文字颜色变为浅灰 #c0c0c0，弱化提示
 *   - 失焦（blur / 鼠标移出）且未输入内容：恢复 placeholder-class 原始颜色与默认对齐
 *
 * 实现说明：
 *   - 小程序无原生 mouseout 事件，input 组件的 @blur 失焦事件已等效覆盖"鼠标移出"场景
 *     （参考微信小程序 input 组件文档：https://developers.weixin.qq.com/miniprogram/dev/component/input.html）
 *   - 通过 :placeholder-style 动态绑定行内样式，优先级高于 placeholder-class，
 *     聚焦时覆盖颜色；失焦时返回空串，placeholder-class 接管恢复原始颜色
 *   - placeholder-class 仅含 color + font-size，从不改变垂直对齐，placeholder 始终保持
 *     默认垂直居中，无需额外处理对齐恢复
 *
 * 参考：Vue 3 组合式函数（Composables）官方文档
 *   https://cn.vuejs.org/guide/reusability/composables.html
 *
 * @returns {{ activeField: Ref<string>, onFocus: (key: string) => void, onBlur: () => void, phStyle: (key: string) => string }}
 */
import { ref } from 'vue'

export function usePlaceholder() {
  // 当前聚焦输入框的 key（由调用方传入，如 'username'、'password'）
  const activeField = ref('')

  /** 聚焦处理：记录当前聚焦字段 key */
  function onFocus(key) {
    activeField.value = key
  }

  /** 失焦处理：清空聚焦记录，使 phStyle 返回空串，恢复 placeholder-class 原始样式 */
  function onBlur() {
    activeField.value = ''
  }

  /**
   * 生成 placeholder 行内样式
   * @param {string} key - 输入框字段标识
   * @returns {string} 聚焦时返回 'color: #c0c0c0;'，否则返回空串（恢复默认）
   */
  function phStyle(key) {
    return activeField.value === key ? 'color: #c0c0c0;' : ''
  }

  return { activeField, onFocus, onBlur, phStyle }
}
