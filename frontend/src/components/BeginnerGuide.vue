<template>
  <template v-if="visible">
    <!-- #ifdef H5 -->
    <!-- SVG 精确蒙版：全屏覆盖，中心挖圆角矩形洞，避免四角漏白 -->
    <svg
      v-if="targetRect"
      class="beginner-guide__svg-mask"
      :style="svgMaskStyle"
    >
      <defs>
        <mask :id="maskId">
          <rect x="0" y="0" :width="screenWidth" :height="screenHeight" fill="white" />
          <rect
            :x="highlightRect.left"
            :y="highlightRect.top"
            :width="highlightRect.width"
            :height="highlightRect.height"
            :rx="highlightRadiusValue"
            :ry="highlightRadiusValue"
            fill="black"
          />
        </mask>
      </defs>
      <rect
        x="0"
        y="0"
        :width="screenWidth"
        :height="screenHeight"
        fill="rgba(0, 0, 0, 0.6)"
        :mask="`url(#${maskId})`"
      />
    </svg>
    <!-- #endif -->

    <!-- #ifndef H5 -->
    <!-- 微信小程序蒙版：
         视觉层（单 view + box-shadow 大扩散）一次绘制高亮洞以外的灰色蒙版，无相邻 view 拼接线；
         点击阻挡层（4 个透明矩形）覆盖高亮洞以外区域，高亮洞内无 view，点击直达目标 -->
    <template v-if="highlightRect">
      <!-- 点击阻挡层：4 个透明矩形（pointer-events 默认 auto），覆盖高亮洞以外的整屏区域；
           透明背景使相邻 view 拼接处不可见，视觉蒙版由下方 box-shadow 视觉层统一绘制 -->
      <view class="beginner-guide__bar" :style="topBarStyle" @touchmove.stop @click.stop></view>
      <view class="beginner-guide__bar" :style="bottomBarStyle" @touchmove.stop @click.stop></view>
      <view class="beginner-guide__bar" :style="leftBarStyle" @touchmove.stop @click.stop></view>
      <view class="beginner-guide__bar" :style="rightBarStyle" @touchmove.stop @click.stop></view>
      <!-- 视觉层：单 view，box-shadow 大扩散绘制高亮洞以外的灰色蒙版（pointer-events:none 不阻挡点击） -->
      <view class="beginner-guide__mask-hole" :style="maskHoleStyle"></view>
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
        <text class="beginner-guide__step-badge">第 {{ stepData.stepNumber }} 步 / 共 {{ totalSteps }} 步</text>
        <text class="beginner-guide__skip" @click.stop="handleSkip">跳过</text>
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
 *  - 灰色蒙版：覆盖目标元素以外的区域，阻止用户点击非目标按钮
 *    - H5：全屏 SVG mask，中心挖一个与目标元素同尺寸同圆角的洞
 *    - 微信小程序：单 view box-shadow 大扩散绘制洞外蒙版 + 4 透明矩形作点击阻挡层
 *  - 高亮边框：围绕目标元素描边，吸引视线（pointer-events:none 不阻挡目标点击）
 *  - 步骤卡片：显示步骤序号、标题、说明文字，附带"跳过"按钮
 *  - 目标位置由 useGuideTarget composable 在各页面/组件内查询并上报到 guide store
 *  - 登录成功后监听 userStore.userInfo 自动完成引导
 *
 * 蒙版原理：
 *  - H5：使用 SVG mask 精确挖洞，pointer-events:none 不阻挡目标点击。
 *  - 微信小程序：视觉层用单个 view 的 box-shadow 大扩散一次性绘制高亮洞以外的灰色蒙版，
 *    单层连续渲染，无相邻 view 拼接处，杜绝 1px 拼接线，背景颜色一致；
 *    点击阻挡层用 4 个透明矩形覆盖高亮洞以外的整屏区域（pointer-events:auto），
 *    高亮洞内不放置任何 view，点击直达目标；透明矩形拼接处不可见，视觉无影响。
 *    呼吸边框直接用 box-shadow 绘制于高亮 view（不使用 ::after 伪元素，
 *    避免微信小程序伪元素不尊重 pointer-events:none 而误拦目标点击）。
 *
 * 使用方式：在需要引导的页面引入 <BeginnerGuide /> 即可，组件内部读取 guide store
 * 自动判断是否渲染及渲染哪个步骤。
 */
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useGuideStore } from '../store/modules/guide'
import { useUserStore } from '../store/modules/user'

const guideStore = useGuideStore()
const userStore = useUserStore()

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

// SVG mask 唯一标识
const maskId = 'beginner-guide-mask'

// rpx 转 px（以 750rpx = screenWidth 为基准）
function rpxToPx(rpx) {
  return (rpx * screenWidth.value) / 750
}

// 高亮框圆角（px）：接近正方形的目标用圆形，否则用 32rpx 大圆角
const highlightRadiusValue = computed(() => {
  const rect = highlightRect.value
  if (!rect) return rpxToPx(32)
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
const maskBounds = computed(() => {
  const rect = highlightRect.value
  if (!rect) return null
  const T = Math.floor(rect.top)
  const B = Math.ceil(rect.bottom)
  const L = Math.floor(rect.left)
  const R = Math.ceil(rect.right)
  const r = highlightRadiusValue.value
  // 圆角补片边长，限制为圆角半径与半宽/半高的最小值，确保四角补片互不重叠
  const cs = Math.max(0, Math.min(r, (R - L) / 2, (B - T) / 2))
  return { T, B, L, R, cs }
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
    boxShadow: `0 0 0 ${spreadPx.value}px rgba(0, 0, 0, 0.6)`
  }
})

// SVG 蒙版定位样式
const svgMaskStyle = computed(() => ({
  top: 0,
  left: 0,
  width: screenWidth.value + 'px',
  height: screenHeight.value + 'px'
}))

// 步骤卡片定位：优先放在目标下方，空间不足时放上方
const cardStyle = computed(() => {
  const rect = targetRect.value
  if (!rect) return {}
  const gap = 16
  const cardWidth = Math.min(screenWidth.value - 32, 300)
  let top = rect.bottom + gap
  // 下方空间不足时放上方
  if (top + cardHeight > screenHeight.value) {
    top = rect.top - cardHeight - gap
    // 上方也不够时，强制放下方（极端情况）
    if (top < 0) top = rect.bottom + gap
  }
  // 水平居中于目标，但限制在屏幕内
  let left = rect.left + rect.width / 2 - cardWidth / 2
  if (left < 16) left = 16
  if (left + cardWidth > screenWidth.value - 16) {
    left = screenWidth.value - cardWidth - 16
  }
  return {
    top: top + 'px',
    left: left + 'px',
    width: cardWidth + 'px'
  }
})

// 跳过引导
function handleSkip() {
  guideStore.skipGuide()
}

// 监听登录成功：自动完成引导
const stopUserWatch = watch(
  () => userStore.userInfo,
  (val) => {
    if (val && guideStore.isActive) {
      guideStore.completeGuide()
    }
  }
)

onUnmounted(() => {
  stopUserWatch()
})
</script>

<style lang="scss" scoped>
/* ==========================================================================
 * 响应式单位说明
 * --------------------------------------------------------------------------
 * 蒙版与高亮定位使用 px（来自 boundingClientRect 的实际像素值）。
 * 步骤卡片内部样式使用 rpx（随屏缩放），平板断点(≥768px)锁定为 px。
 * ========================================================================== */

.beginner-guide__svg-mask {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9998;
  pointer-events: none;
}

.beginner-guide__mask {
  position: fixed;
  background: rgba(0, 0, 0, 0.6);
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
  box-shadow: 0 0 0 2px #9fe870, 0 0 20px rgba(159, 232, 112, 0.6);
  animation: guide-pulse 1.8s ease-in-out infinite;
}
/* #endif */

/* 微信小程序：高亮边框直接用 box-shadow 绘制于高亮 view 本身（不使用 ::after 伪元素，
   避免微信小程序伪元素不尊重 pointer-events:none 而误拦目标点击） */
/* #ifndef H5 */
.beginner-guide__highlight {
  box-shadow: 0 0 0 2px #9fe870, 0 0 12px rgba(159, 232, 112, 0.4);
  animation: guide-pulse 1.8s ease-in-out infinite;
}
/* #endif */

@keyframes guide-pulse {
  0%, 100% {
    box-shadow: 0 0 0 2px #9fe870, 0 0 12px rgba(159, 232, 112, 0.4);
  }
  50% {
    box-shadow: 0 0 0 4px #9fe870, 0 0 28px rgba(159, 232, 112, 0.8);
  }
}

.beginner-guide__card {
  position: fixed;
  z-index: 10000;
  padding: 28rpx 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
  background: #e8f5e0;
  color: #2f6c00;
  font-size: 24rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.beginner-guide__skip {
  color: #868685;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
  padding: 4rpx 8rpx;
}

.beginner-guide__card-title {
  color: #0e0f0c;
  font-size: 36rpx;
  line-height: 50rpx;
  font-weight: 600;
}

.beginner-guide__card-desc {
  color: #454745;
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
