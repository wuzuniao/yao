<template>
  <template v-if="visible && ready">
    <!-- 视觉蒙版：单 view + box-shadow 大扩散绘制高亮洞以外的灰色蒙版；
         view 本身透明，高亮洞内显示目标元素，连续渲染无 SVG mask 抗锯齿黑边 -->
    <view
      v-if="highlightRect"
      class="beginner-guide__mask-hole"
      :style="maskHoleStyle"
    ></view>

    <!-- #ifndef H5 -->
    <!-- 微信小程序点击阻挡层：4 个透明矩形覆盖高亮洞以外区域，高亮洞内无 view，点击直达目标；
         H5 端蒙版 view pointer-events:none 不阻挡点击，无需点击阻挡层 -->
    <template v-if="highlightRect">
      <view class="beginner-guide__bar" :style="topBarStyle" @touchmove.stop @click.stop></view>
      <view class="beginner-guide__bar" :style="bottomBarStyle" @touchmove.stop @click.stop></view>
      <view class="beginner-guide__bar" :style="leftBarStyle" @touchmove.stop @click.stop></view>
      <view class="beginner-guide__bar" :style="rightBarStyle" @touchmove.stop @click.stop></view>
    </template>
    <!-- #endif -->

    <!-- 全屏蒙版（目标位置尚未上报时，覆盖整屏阻止操作） -->
    <view
      v-if="!targetRect"
      class="beginner-guide__mask beginner-guide__mask--full"
      @touchmove.stop
      @click.stop
    ></view>

    <!-- 高亮边框：与目标元素完全重合，pointer-events:none 不阻挡点击 -->
    <view
      v-if="highlightRect"
      class="beginner-guide__highlight"
      :style="highlightStyle"
    ></view>

    <!-- 步骤卡片 -->
    <view
      v-if="targetRect && stepData"
      class="beginner-guide__card"
      :style="cardStyle"
      @touchmove.stop
    >
      <view class="beginner-guide__card-header">
        <text class="beginner-guide__step-badge">{{ $t('guide.badge', { current: guideStore.displayStepNumber, total: guideStore.displayTotalSteps }) }}</text>
        <text class="beginner-guide__skip" @click.stop="handleSkip">{{ $t('guide.skip') }}</text>
      </view>
      <text class="beginner-guide__card-title">{{ stepData.title }}</text>
      <text class="beginner-guide__card-desc">{{ stepData.description }}</text>
    </view>
  </template>
</template>

<script setup>
/**
 * 新手引导遮罩组件（BeginnerGuide.vue）
 * --------------------------------------------------------------------------
 * 功能：跨页面新手引导的视觉呈现层
 *  - 灰色蒙版：覆盖目标元素以外的区域
 *    - H5 与微信小程序均使用单 view box-shadow 大扩散绘制洞外蒙版（连续渲染无 SVG mask 抗锯齿黑边）
 *    - 微信小程序额外用 4 个透明矩形作点击阻挡层（H5 端蒙版 view pointer-events:none 不阻挡点击）
 *  - 高亮边框：围绕目标元素描边，吸引视线（pointer-events:none 不阻挡目标点击）
 *  - 步骤卡片：显示步骤序号、标题、说明文字，附带"跳过"按钮
 *  - 目标位置由 useGuideTarget composable 在各页面/组件内查询并上报到 guide store
 *  - 支持步骤分支：可选步骤点击「跳过」可跳转到指定后续步骤（如步骤 4 通知方式分支）
 *  - 支持步骤配置 shape（circle/pill）实现高亮圆角与目标完全一致，避免胶囊按钮/圆形按钮出现白边
 *  - 支持步骤配置 cardPosition='bottom' 强制提示卡片位于目标下方，避免覆盖表单卡片；
 *    cardPosition='anchor-top' 基于 cardAnchor 指定元素顶部定位，使卡片底部位于参考元素顶部上方 12px；上方空间不足时 fallback 到参考元素内部
 *  - 所有步骤均在对应页面加载完成、目标元素位置成功上报后才显示蒙版/高亮/卡片；滚动过程中 useGuideTarget 持续刷新位置，高亮与卡片同步跟随
 *
 * 蒙版原理：
 *  - 视觉层：单 view + box-shadow 大扩散一次性绘制高亮洞以外的灰色蒙版，
 *    单层连续渲染，无拼接线，背景颜色一致；view 本身透明，高亮洞内显示目标元素。
 *  - H5：蒙版 view pointer-events:none 不阻挡任何点击，无需点击阻挡层。
 *  - 微信小程序：额外用 4 个透明矩形覆盖高亮洞以外的整屏区域（pointer-events:auto），
 *    高亮洞内不放置任何 view，点击直达目标；透明矩形拼接处不可见，视觉无影响。
 *  - 呼吸边框用 box-shadow 绘制于高亮 view（不使用 ::after 伪元素，
 *    避免微信小程序伪元素不尊重 pointer-events:none 而误拦目标点击）。
 *
 * 使用方式：在需要引导的页面引入 <BeginnerGuide /> 即可，组件内部读取 guide store
 * 自动判断是否渲染及渲染哪个步骤。
 */
import { computed, ref, onMounted, watch, onUnmounted } from 'vue'
import { useGuideStore } from '../store/modules/guide'

const guideStore = useGuideStore()

// 屏幕尺寸（px，用于蒙版计算）
const screenWidth = ref(375)
const screenHeight = ref(667)

// 卡片预估高度（px，用于定位计算）
const cardHeight = 180

// 获取屏幕尺寸
function updateScreenSize() {
  try {
    const info = uni.getSystemInfoSync()
    screenWidth.value = info.windowWidth || info.screenWidth || 375
    screenHeight.value = info.windowHeight || info.screenHeight || 667
  } catch (e) {
    // 降级使用默认值
  }
}

onMounted(() => {
  updateScreenSize()
})

// 当前步骤数据
const stepData = computed(() => guideStore.currentStepData)
const totalSteps = computed(() => guideStore.totalSteps)

// 组件是否可见：引导激活 + 当前步骤的页面与当前页面一致
const visible = computed(() => {
  if (!guideStore.isActive || !stepData.value) return false
  return stepData.value.page === guideStore.currentPage
})

// 当前目标元素的位置
const targetRect = computed(() => {
  if (!stepData.value) return null
  return guideStore.targetRects[stepData.value.target] || null
})

// 当前步骤是否已准备好显示：页面匹配 + 目标元素位置已上报；
// 若步骤配置了 cardAnchor，还需锚点元素位置已上报。
// 这样可以确保对应页面加载完成、目标元素布局稳定后，高亮区域与提示卡片再出现。
const ready = computed(() => {
  if (!visible.value) return false
  if (!targetRect.value) return false
  const anchorKey = stepData.value?.cardAnchor
  if (anchorKey) {
    return !!guideStore.targetRects[anchorKey]
  }
  return true
})

// 微信小程序：引导就绪时禁用 page 滚动，防止用户滚动导致高亮与目标不匹配。
// 原蒙版 4 个透明矩形只覆盖高亮洞以外区域（@touchmove.stop），高亮洞内无 view 拦截
// touchmove，用户在洞内滑动时 touchmove 冒泡到 page 容器，page 滚动，高亮位置与目标错位。
// 在洞内加 view 会拦截 click（目标按钮点不到），故改用 setPageStyle 在页面级别禁用滚动。
// 引导结束/组件卸载时恢复，确保页面可正常滚动。
// #ifdef MP-WEIXIN
watch(ready, (val) => {
  if (val) {
    uni.setPageStyle({ style: { overflow: 'hidden' } })
  } else {
    uni.setPageStyle({ style: { overflow: '' } })
  }
}, { immediate: true })

onUnmounted(() => {
  uni.setPageStyle({ style: { overflow: '' } })
})
// #endif

// 当前步骤的高亮区域外边距（px），默认 0，仅微信登录图标需要外扩
const stepPadding = computed(() => stepData.value?.padding ?? 0)

// 扩大后的高亮区域（用于蒙版洞和高亮框）
const highlightRect = computed(() => {
  const rect = targetRect.value
  const pad = stepPadding.value
  if (!rect) return null
  return {
    top: rect.top - pad,
    left: rect.left - pad,
    width: rect.width + pad * 2,
    height: rect.height + pad * 2,
    right: rect.right + pad,
    bottom: rect.bottom + pad
  }
})

// rpx 转 px（以 750rpx = screenWidth 为基准）
function rpxToPx(rpx) {
  return (rpx * screenWidth.value) / 750
}

// 高亮框圆角（px）：根据步骤配置的 shape 或目标长宽比自动选择
// - shape='circle'：正圆（短边一半）
// - shape='pill'：胶囊形（短边一半，与 border-radius:9999px 的按钮完全贴合）
// - 其它：默认 32rpx 大圆角
const highlightRadiusValue = computed(() => {
  const rect = highlightRect.value
  if (!rect) return rpxToPx(32)
  const shape = stepData.value?.shape
  if (shape === 'circle' || shape === 'pill') {
    return Math.min(rect.width, rect.height) / 2
  }
  const ratio = Math.max(rect.width, rect.height) / Math.min(rect.width, rect.height)
  if (ratio <= 1.3) {
    return Math.min(rect.width, rect.height) / 2
  }
  return rpxToPx(32)
})

// 高亮框样式（位置、尺寸、圆角）：与高亮洞整数边界一致，点击可穿透
const highlightStyle = computed(() => {
  const b = maskBounds.value
  if (!b) return {}
  return {
    top: b.T + 'px',
    left: b.L + 'px',
    width: b.R - b.L + 'px',
    height: b.B - b.T + 'px',
    borderRadius: b.cs + 'px'
  }
})

// 高亮洞的整数边界：相邻矩形/补片紧邻拼接且互不重叠，避免半透明双重叠加产生拼接线
//
// 闪烁根因与缓存说明：
// useGuideTarget 每 250ms 刷新目标位置，boundingClientRect 返回的浮点值存在 sub-pixel 抖动；
// 抖动 ≥1px 时 reportRect 去重失效，setTargetRect 创建新 targetRects 引用，触发下游 computed 链重算。
// 本 computed 用 Math.floor/ceil 取整，会把 sub-pixel 抖动放大为相邻整数跳变（如 T: 100↔101），
// 若每次返回新对象，下游 topBarStyle/bottomBarStyle/.../highlightStyle 全部重算返回新对象，
// Vue patcher 全量更新 style，高亮洞位置 1px 反复跳变，肉眼可见频繁闪烁。
//
// 修复：基于整数签名缓存返回值，相同签名返回同一对象引用，下游 computed 依赖未变不重算，DOM 不更新。
// 只有高亮洞整数边界真正变化（如用户滚动、目标位移）时才返回新对象，触发合理更新。
let _maskBoundsSig = null
let _maskBoundsVal = null
const maskBounds = computed(() => {
  const rect = highlightRect.value
  if (!rect) {
    _maskBoundsSig = null
    _maskBoundsVal = null
    return null
  }
  const T = Math.floor(rect.top)
  const B = Math.ceil(rect.bottom)
  const L = Math.floor(rect.left)
  const R = Math.ceil(rect.right)
  const r = highlightRadiusValue.value
  // 圆角补片边长，限制为圆角半径与半宽/半高的最小值，确保四角补片互不重叠
  const cs = Math.max(0, Math.min(r, (R - L) / 2, (B - T) / 2))
  // 签名含四边整数边界与圆角半径整数（cs 取整避免浮点抖动触发新对象）
  const sig = `${T}|${B}|${L}|${R}|${Math.round(cs)}`
  if (sig === _maskBoundsSig) return _maskBoundsVal
  _maskBoundsSig = sig
  _maskBoundsVal = { T, B, L, R, cs }
  return _maskBoundsVal
})

// 微信小程序：四边矩形蒙版样式（整数边界、互不重叠，高亮区域内无 view，点击直达目标）
const topBarStyle = computed(() => {
  const b = maskBounds.value
  if (!b) return {}
  return {
    top: '0px',
    left: '0px',
    width: screenWidth.value + 'px',
    height: b.T + 'px'
  }
})

const bottomBarStyle = computed(() => {
  const b = maskBounds.value
  if (!b) return {}
  return {
    top: b.B + 'px',
    left: '0px',
    width: screenWidth.value + 'px',
    height: screenHeight.value - b.B + 'px'
  }
})

const leftBarStyle = computed(() => {
  const b = maskBounds.value
  if (!b) return {}
  return {
    top: b.T + 'px',
    left: '0px',
    width: b.L + 'px',
    height: b.B - b.T + 'px'
  }
})

const rightBarStyle = computed(() => {
  const b = maskBounds.value
  if (!b) return {}
  return {
    top: b.T + 'px',
    left: b.R + 'px',
    width: screenWidth.value - b.R + 'px',
    height: b.B - b.T + 'px'
  }
})

// 微信小程序：视觉层单 view 样式
// box-shadow 大扩散一次性绘制高亮洞以外的灰色蒙版，单层连续无拼接线；
// 视图本身背景透明且 pointer-events:none，不阻挡洞内目标点击，洞外点击由透明矩形阻挡层处理
const spreadPx = computed(() => Math.max(screenWidth.value, screenHeight.value) * 2)
const maskHoleStyle = computed(() => {
  const b = maskBounds.value
  if (!b) return {}
  return {
    top: b.T + 'px',
    left: b.L + 'px',
    width: b.R - b.L + 'px',
    height: b.B - b.T + 'px',
    borderRadius: b.cs + 'px',
    boxShadow: `0 0 0 ${spreadPx.value}px var(--color-mask-60)`
  }
})

// 步骤卡片定位：
// - 默认：优先放在目标下方，空间不足时放上方
// - cardPosition='bottom'：强制卡片位于目标下方
// - cardPosition='top-viewport'：固定于视口顶部（16px 安全边距），确保在长页面底部目标时卡片仍可见且不覆盖表单卡片
// - cardPosition='anchor-top'：基于 cardAnchor 指定的参考元素顶部定位，卡片底部位于参考元素顶部上方 12px；
//   极端情况下上方空间不足时，改为置于参考元素内部（顶部偏下 12px），优先保证可见。用于「授权订阅提醒」步骤
//
// 缓存说明：与 maskBounds 同理，基于整数签名复用对象引用，避免 targetRect 浮点抖动触发 DOM 频繁更新。
// 仅在卡片整数位置真正变化时返回新对象，sub-pixel 抖动被拦截。
let _cardStyleSig = null
let _cardStyleVal = null
const cardStyle = computed(() => {
  const rect = targetRect.value
  if (!rect) {
    _cardStyleSig = null
    _cardStyleVal = null
    return {}
  }
  const gap = 16
  const safeTop = 16
  const cardWidth = Math.min(screenWidth.value - 32, 300)
  const position = stepData.value?.cardPosition
  const anchorKey = stepData.value?.cardAnchor
  const anchorRect = anchorKey ? guideStore.targetRects[anchorKey] : null
  let top
  if (position === 'top-viewport') {
    top = safeTop
  } else if (position === 'anchor-top' && anchorRect) {
    const anchorGap = 12
    top = anchorRect.top - cardHeight - anchorGap
    // 极端情况下若卡片被顶到屏幕外，则置于新建通知方式卡片内部（顶部偏下 12px），优先保证可见
    if (top < safeTop) {
      top = anchorRect.top + anchorGap
    }
  } else {
    top = rect.bottom + gap
    // 未强制下方时：下方空间不足则放上方
    if (position !== 'bottom') {
      if (top + cardHeight > screenHeight.value) {
        top = rect.top - cardHeight - gap
        // 上方也不够时，强制放下方（极端情况）
        if (top < 0) top = rect.bottom + gap
      }
    }
  }
  // 水平居中于目标，但限制在屏幕内
  let left = rect.left + rect.width / 2 - cardWidth / 2
  if (left < 16) left = 16
  if (left + cardWidth > screenWidth.value - 16) {
    left = screenWidth.value - cardWidth - 16
  }
  // 整数签名：top/left 取整，避免浮点抖动触发新对象；cardWidth 由 screenWidth 决定，稳定
  const sig = `${Math.round(top)}|${Math.round(left)}|${cardWidth}`
  if (sig === _cardStyleSig) return _cardStyleVal
  _cardStyleSig = sig
  _cardStyleVal = {
    top: top + 'px',
    left: left + 'px',
    width: cardWidth + 'px'
  }
  return _cardStyleVal
})

// 当前是否为内部步骤数组的最后一步
const isLastInternalStep = computed(() => guideStore.currentStep === guideStore.steps.length - 1)

// 跳过引导：普通步骤结束引导；带 skipTo 的步骤跳转到指定后续步骤（支持可选分支）
function handleSkip() {
  if (stepData.value?.skipTo) {
    guideStore.skipToStepByTarget(stepData.value.skipTo)
    return
  }
  guideStore.skipGuide()
}
</script>

<style lang="scss" scoped>
/* ==========================================================================
 * 响应式单位说明
 * --------------------------------------------------------------------------
 * 蒙版与高亮定位使用 px（来自 boundingClientRect 的实际像素值）。
 * 步骤卡片内部样式使用 rpx（随屏缩放），平板断点(≥768px)锁定为 px。
 * ========================================================================== */

.beginner-guide__mask {
  position: fixed;
  background: var(--color-mask-60);
  z-index: 9998;
}

.beginner-guide__mask--full {
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.beginner-guide__highlight {
  position: fixed;
  /* border-radius 由 style 动态绑定，根据目标形状在 32rpx 大圆角与正圆之间自适应 */
  pointer-events: none;
  z-index: 9999;
}

/* 微信小程序点击阻挡层：4 个透明矩形（视觉蒙版由 mask-hole 的 box-shadow 统一绘制，故此处透明，
   相邻矩形拼接处无颜色、不可见，视觉无拼接线） */
.beginner-guide__bar {
  position: fixed;
  background: transparent;
  z-index: 9997;
}

/* 微信小程序视觉层：单 view，box-shadow 大扩散绘制高亮洞以外的灰色蒙版；
   单层连续渲染无拼接线；pointer-events:none 不阻挡洞内目标点击 */
.beginner-guide__mask-hole {
  position: fixed;
  background: transparent;
  z-index: 9998;
  pointer-events: none;
}

/* H5：使用 box-shadow 呼吸动画实现高亮边框（SVG mask 负责精确蒙版） */
/* #ifdef H5 */
.beginner-guide__highlight {
  box-shadow: 0 0 0 2px var(--color-brand-bg), 0 0 20px var(--color-brand-glow);
  animation: guide-pulse 1.8s ease-in-out infinite;
}
/* #endif */

/* 微信小程序：高亮边框直接用 box-shadow 绘制于高亮 view 本身（不使用 ::after 伪元素，
   避免微信小程序伪元素不尊重 pointer-events:none 而误拦目标点击） */
/* #ifndef H5 */
.beginner-guide__highlight {
  box-shadow: 0 0 0 2px var(--color-brand-bg), 0 0 12px var(--color-brand-glow-soft);
  animation: guide-pulse 1.8s ease-in-out infinite;
}
/* #endif */

@keyframes guide-pulse {
  0%, 100% {
    box-shadow: 0 0 0 2px var(--color-brand-bg), 0 0 12px var(--color-brand-glow-soft);
  }
  50% {
    box-shadow: 0 0 0 4px var(--color-brand-bg), 0 0 28px var(--color-brand-glow-strong);
  }
}

.beginner-guide__card {
  position: fixed;
  z-index: 10000;
  padding: 28rpx 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: var(--color-card-bg);
  box-shadow: var(--shadow-float);
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.beginner-guide__card-header {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.beginner-guide__step-badge {
  display: inline-block;
  padding: 4rpx 16rpx;
  border-radius: 9999rpx;
  background: var(--color-brand-bg-light);
  color: var(--color-brand);
  font-size: 24rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.beginner-guide__skip {
  color: var(--color-text-tertiary);
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
  padding: 4rpx 8rpx;
}

.beginner-guide__card-title {
  color: var(--color-text-primary);
  font-size: 36rpx;
  line-height: 50rpx;
  font-weight: 600;
}

.beginner-guide__card-desc {
  color: var(--color-text-secondary);
  font-size: 28rpx;
  line-height: 42rpx;
  font-weight: 400;
}

/* ===== 平板/折叠屏断点（≥768px）===== */
@media screen and (min-width: 768px) {
  .beginner-guide__card {
    padding: 14px 16px;
    border-radius: 12px;
    gap: 6px;
  }
  .beginner-guide__step-badge {
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 12px;
    line-height: 18px;
  }
  .beginner-guide__skip {
    font-size: 14px;
    line-height: 20px;
    padding: 2px 4px;
  }
  .beginner-guide__card-title {
    font-size: 18px;
    line-height: 25px;
  }
  .beginner-guide__card-desc {
    font-size: 14px;
    line-height: 21px;
  }
}
</style>
