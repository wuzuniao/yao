import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 新手引导状态管理 Store
 * --------------------------------------------------------------------------
 * - 管理跨页面新手引导的全局状态（激活、当前步骤、目标元素位置）
 * - 引导步骤：首页(点设置) → 设置页(点用户资料卡) → 登录页(点微信一键登录)
 * - 每个页面 onShow 时调用 onPageEnter(pageName) 上报当前页面，store 据此推进步骤
 * - 目标元素位置由 useGuideTarget composable 在各页面/组件内查询并上报
 * - 登录成功后由 BeginnerGuide 组件监听 userStore.userInfo 自动完成引导
 */
export const useGuideStore = defineStore('guide', () => {
  // 引导是否激活
  const isActive = ref(false)
  // 当前步骤索引（0-based）
  const currentStep = ref(0)
  // 当前所在页面名称（由各页面 onShow 上报）
  const currentPage = ref('')
  // 各目标元素的位置信息（key → { top, left, width, height, right, bottom }）
  const targetRects = ref({})

  // 引导步骤配置（顺序即引导流程顺序）
  const steps = ref([
    {
      page: 'home',
      target: 'settings-tab',
      stepNumber: 1,
      padding: 0,
      title: '点击「设置」',
      description: '在底部导航栏中点击「设置」按钮，进入设置页面。'
    },
    {
      page: 'settings',
      target: 'profile-card',
      stepNumber: 2,
      padding: 0,
      title: '点击用户资料卡',
      description: '点击顶部的用户资料卡片，进入登录页面。'
    },
    {
      page: 'login',
      target: 'wechat-login',
      stepNumber: 3,
      padding: 10,
      title: '微信一键登录',
      description: '点击微信图标，即可一键登录并开始使用。'
    }
  ])

  // 当前步骤数据
  const currentStepData = computed(() => steps.value[currentStep.value] || null)

  // 总步骤数
  const totalSteps = computed(() => steps.value.length)

  // 开启新手引导（从第 1 步开始）
  function startGuide() {
    isActive.value = true
    currentStep.value = 0
    targetRects.value = {}
  }

  // 跳过引导（用户主动取消）
  function skipGuide() {
    isActive.value = false
    currentStep.value = 0
    targetRects.value = {}
  }

  // 完成引导（全部步骤完成或登录成功）
  function completeGuide() {
    isActive.value = false
    currentStep.value = 0
    targetRects.value = {}
  }

  // 页面进入时上报（由各页面 onShow 调用）
  // 根据当前页面推进或回退步骤：找到匹配 page 的步骤，设置为当前步骤
  function onPageEnter(page) {
    currentPage.value = page
    if (!isActive.value) return
    const stepIndex = steps.value.findIndex(s => s.page === page)
    if (stepIndex === -1) return
    // 无论前进还是后退，都同步到匹配的步骤
    currentStep.value = stepIndex
  }

  // 设置目标元素位置（由 useGuideTarget composable 调用）
  function setTargetRect(key, rect) {
    targetRects.value = { ...targetRects.value, [key]: rect }
  }

  // 清除目标元素位置（页面离开时清理）
  function clearTargetRect(key) {
    const next = { ...targetRects.value }
    delete next[key]
    targetRects.value = next
  }

  return {
    isActive,
    currentStep,
    currentPage,
    targetRects,
    steps,
    currentStepData,
    totalSteps,
    startGuide,
    skipGuide,
    completeGuide,
    onPageEnter,
    setTargetRect,
    clearTargetRect
  }
})
