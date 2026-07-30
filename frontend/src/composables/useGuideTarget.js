import { watch, getCurrentInstance, onUnmounted } from 'vue'
import { useGuideStore } from '../store/modules/guide'

/**
 * 新手引导目标元素位置上报 composable
 * --------------------------------------------------------------------------
 * 在含引导目标的组件/页面中调用，自动在引导激活且当前步骤匹配时
 * 查询目标元素的 boundingClientRect 并上报到 guide store。
 *
 * 当前步骤匹配时，查询目标位置并上报一次（带重试）；引导激活时蒙版阻止页面
 * 滚动（@touchmove.stop），目标位置稳定，无需持续刷新。布局变化（如异步加载、
 * admin 按钮出现）由各页面手动调用 requery 处理。
 *
 * 当某元素仅作为提示卡片定位锚点（steps[].cardAnchor）而非高亮目标时，
 * 只要当前步骤引用它，同样会上报位置，供 BeginnerGuide 的 cardPosition='anchor-top' 使用。
 *
 * 使用 .in(instance.proxy) 确保能查询到自定义组件内部的节点
 * （微信小程序自定义组件存在 shadow 边界，页面级查询无法穿透）。
 *
 * 位置去重：reportRect 用 Math.round 整数比较，新旧位置整数相同时跳过 setTargetRect，
 * 避免 BeginnerGuide computed 链重算与视图重建。
 *
 * @param {string} targetKey - 目标标识（与 store 中 steps[].target 或 steps[].cardAnchor 对应）
 * @param {string} selector - CSS 选择器（如 '.guide-target-settings-tab'）
 * @returns {{ requery: Function }}
 *   - requery：手动触发一次位置重新查询（带重试），供页面布局变化时调用
 *
 * 用法：
 *   import { useGuideTarget } from '../../composables/useGuideTarget'
 *   const { requery } = useGuideTarget('settings-tab', '.guide-target-settings-tab')
 */
export function useGuideTarget(targetKey, selector) {
  const guideStore = useGuideStore()
  const instance = getCurrentInstance()

  // 上报一次有效矩形
  // 整数比较去重：boundingClientRect 返回的浮点值在 sub-pixel 范围抖动时，
  // Math.round 后整数相同则跳过 setTargetRect，避免创建新对象引用触发
  // BeginnerGuide computed 链重算与视图重建（设置页第 4/5 步高亮闪烁根因）。
  // 之前用 <1px 浮点阈值，1px 边界附近的抖动（如 100.0 ↔ 101.0）仍会触发更新。
  function reportRect(rect) {
    const existing = guideStore.targetRects[targetKey]
    if (
      existing &&
      Math.round(existing.top) === Math.round(rect.top) &&
      Math.round(existing.left) === Math.round(rect.left) &&
      Math.round(existing.width) === Math.round(rect.width) &&
      Math.round(existing.height) === Math.round(rect.height)
    ) {
      return
    }
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

  // 手动触发一次位置重新查询（供页面在布局变化时调用，如管理员按钮出现导致目标位移）
  function requery() {
    queryAndReport()
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

  // 监听引导状态：当引导激活且当前步骤的目标或锚点是本目标时，查询并上报位置
  // immediate: true 确保组件挂载时如果引导已在进行中，立即上报
  // nextTick + setTimeout 确保 DOM 已渲染完成后再查询
  //
  // 定时刷新已移除：原 startRefresh 每 250ms 调用 queryOnce，boundingClientRect
  // 返回的浮点值在 sub-pixel 范围抖动时，即便 reportRect 去重，仍可能频繁触发
  // setTargetRect → computed 链重算 → BeginnerGuide 高亮区域频繁闪烁。
  // 引导激活时蒙版阻止页面滚动（@touchmove.stop），目标位置稳定，无需持续刷新；
  // 布局变化（如异步加载、admin 按钮出现）由各页面手动调用 requery 处理。
  // 下面在首次查询后追加一次延迟 requery，覆盖异步加载完成后的布局修正。
  let requeryTimer = null
  const stopWatch = watch(
    () => {
      const step = guideStore.currentStepData
      return guideStore.isActive && !!step && (step.target === targetKey || step.cardAnchor === targetKey)
    },
    (active) => {
      if (requeryTimer) {
        clearTimeout(requeryTimer)
        requeryTimer = null
      }
      if (active) {
        // 延迟查询：等待 DOM 渲染完成（页面切换后需留出渲染时间）
        setTimeout(() => {
          queryAndReport()
          // 500ms 后再次查询，覆盖异步加载（如 channels/plans）完成后的布局修正
          requeryTimer = setTimeout(() => {
            queryAndReport()
            requeryTimer = null
          }, 500)
        }, 150)
      }
    },
    { immediate: true }
  )

  // 组件卸载时停止监听并清理位置数据
  onUnmounted(() => {
    stopWatch()
    if (requeryTimer) {
      clearTimeout(requeryTimer)
    }
    guideStore.clearTargetRect(targetKey)
  })

  return { requery }
}
