import { watch, getCurrentInstance, onUnmounted, computed } from 'vue'
import { useGuideStore } from '../store/modules/guide'

/**
 * 新手引导目标元素位置上报 composable
 * --------------------------------------------------------------------------
 * 在含引导目标的组件/页面中调用，自动在引导激活且当前步骤匹配时
 * 查询目标元素的 boundingClientRect 并上报到 guide store。
 *
 * 使用 .in(instance.proxy) 确保能查询到自定义组件内部的节点
 * （微信小程序自定义组件存在 shadow 边界，页面级查询无法穿透）。
 *
 * @param {string} targetKey - 目标标识（与 store 中 steps[].target 对应）
 * @param {string} selector - CSS 选择器（如 '.guide-target-settings-tab'）
 *
 * 用法：
 *   import { useGuideTarget } from '../../composables/useGuideTarget'
 *   useGuideTarget('settings-tab', '.guide-target-settings-tab')
 */
export function useGuideTarget(targetKey, selector) {
  const guideStore = useGuideStore()
  const instance = getCurrentInstance()

  // 查询目标元素位置并上报（带重试）
  // 页面切换/入场动画期间，目标节点可能尚未完成布局，首次查询会返回 null/0 尺寸；
  // 此时若不上报，BeginnerGuide 会回退到全屏阻挡蒙版，导致目标按钮无法点击。
  // 因此在节点未就绪时按 120ms 间隔重试，直到取到有效矩形或达到上限。
  function queryAndReport() {
    if (!instance) return
    let attempts = 0
    const maxAttempts = 8
    const tryQuery = () => {
      const query = uni.createSelectorQuery().in(instance.proxy)
      query.select(selector).boundingClientRect()
      query.exec((res) => {
        const rect = res && res[0]
        if (rect && rect.width > 0 && rect.height > 0) {
          // right/bottom 由 left+width/top+height 推算，避免某些时机下系统返回的 right/bottom 为 0
          // 导致高亮洞退化为左上角小矩形、目标被蒙版覆盖而无法点击
          guideStore.setTargetRect(targetKey, {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
            right: rect.left + rect.width,
            bottom: rect.top + rect.height
          })
        } else if (attempts < maxAttempts) {
          attempts++
          setTimeout(tryQuery, 120)
        }
      })
    }
    tryQuery()
  }

  // 监听引导状态：当引导激活且当前步骤的目标是本目标时，查询并上报位置
  // immediate: true 确保组件挂载时如果引导已在进行中，立即上报
  // nextTick + setTimeout 确保 DOM 已渲染完成后再查询
  const stopWatch = watch(
    () => guideStore.isActive && guideStore.currentStepData?.target === targetKey,
    (active) => {
      if (active) {
        // 延迟查询：等待 DOM 渲染完成（页面切换后需留出渲染时间）
        setTimeout(queryAndReport, 150)
      }
    },
    { immediate: true }
  )

  // 组件卸载时停止监听并清理位置数据
  onUnmounted(() => {
    stopWatch()
    guideStore.clearTargetRect(targetKey)
  })

  // 当前目标激活时的占位样式（预留扩展，目前无需为目标元素额外加样式）
  const activeStyle = computed(() => ({}))

  return { activeStyle }
}
