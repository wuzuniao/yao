import { watch, getCurrentInstance, onUnmounted, computed } from 'vue'
import { useGuideStore } from '../store/modules/guide'

/**
 * 新手引导目标元素位置上报 composable
 * --------------------------------------------------------------------------
 * 在含引导目标的组件/页面中调用，自动在引导激活且当前步骤匹配时
 * 查询目标元素的 boundingClientRect 并上报到 guide store。
 *
 * 当前步骤匹配时，会以 250ms 间隔持续刷新目标位置，使高亮区域与提示卡片
 * 跟随页面/scroll-view 滚动保持同步。
 *
 * 当某元素仅作为提示卡片定位锚点（steps[].cardAnchor）而非高亮目标时，
 * 只要当前步骤引用它，同样会上报位置，供 BeginnerGuide 的 cardPosition='anchor-top' 使用。
 *
 * 使用 .in(instance.proxy) 确保能查询到自定义组件内部的节点
 * （微信小程序自定义组件存在 shadow 边界，页面级查询无法穿透）。
 *
 * @param {string} targetKey - 目标标识（与 store 中 steps[].target 或 steps[].cardAnchor 对应）
 * @param {string} selector - CSS 选择器（如 '.guide-target-settings-tab'）
 *
 * 用法：
 *   import { useGuideTarget } from '../../composables/useGuideTarget'
 *   useGuideTarget('settings-tab', '.guide-target-settings-tab')
 */
export function useGuideTarget(targetKey, selector) {
  const guideStore = useGuideStore()
  const instance = getCurrentInstance()

  // 上报一次有效矩形
  function reportRect(rect) {
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
  }

  // 单次查询（用于持续刷新）
  function queryOnce() {
    if (!instance) return
    const query = uni.createSelectorQuery().in(instance.proxy)
    query.select(selector).boundingClientRect()
    query.exec((res) => {
      const rect = res && res[0]
      if (rect && rect.width > 0 && rect.height > 0) {
        reportRect(rect)
      }
    })
  }

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
          reportRect(rect)
        } else if (attempts < maxAttempts) {
          attempts++
          setTimeout(tryQuery, 120)
        }
      })
    }
    tryQuery()
  }

  // 当前目标或锚点处于激活步骤时，定时刷新位置，保证滚动过程中高亮与卡片跟随目标
  let refreshTimer = null
  function startRefresh() {
    stopRefresh()
    refreshTimer = setInterval(() => {
      const step = guideStore.currentStepData
      const isMatch = step && (step.target === targetKey || step.cardAnchor === targetKey)
      if (!guideStore.isActive || !isMatch) {
        stopRefresh()
        return
      }
      queryOnce()
    }, 250)
  }

  function stopRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  // 监听引导状态：当引导激活且当前步骤的目标或锚点是本目标时，查询并上报位置
  // immediate: true 确保组件挂载时如果引导已在进行中，立即上报
  // nextTick + setTimeout 确保 DOM 已渲染完成后再查询
  const stopWatch = watch(
    () => {
      const step = guideStore.currentStepData
      return guideStore.isActive && !!step && (step.target === targetKey || step.cardAnchor === targetKey)
    },
    (active) => {
      if (active) {
        // 延迟查询：等待 DOM 渲染完成（页面切换后需留出渲染时间）
        setTimeout(() => {
          queryAndReport()
          startRefresh()
        }, 150)
      } else {
        stopRefresh()
      }
    },
    { immediate: true }
  )

  // 组件卸载时停止监听并清理位置数据
  onUnmounted(() => {
    stopWatch()
    stopRefresh()
    guideStore.clearTargetRect(targetKey)
  })

  // 当前目标激活时的占位样式（预留扩展，目前无需为目标元素额外加样式）
  const activeStyle = computed(() => ({}))

  return { activeStyle }
}
