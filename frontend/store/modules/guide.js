import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { t } from '../../locale'
import { useLanguageStore } from './language'

/**
 * 新手引导状态管理 Store
 * --------------------------------------------------------------------------
 * - 管理跨页面新手引导的全局状态（激活、当前步骤、目标元素位置）
 * - 微信小程序端引导流程（用户可见共 6 步；已登录时跳过步骤 2、3，显示为连续的 4 步）：
 *   1. 首页 → 点击底部「设置」
 *   2. 设置页 → 点击用户资料卡 → 进入登录页
 *   3. 登录页 → 微信一键登录 → 登录成功后自动回到设置页
 *   4. 设置页 → 点击「通知方式」（可选）
 *      · 点击「通知方式」后进入通知方式页，继续引导添加新方式并微信授权订阅
 *      · 点击「跳过」则跳过本步分支，直接进入步骤 5
 *   5. 设置页 → 点击「制定计划」→ 进入计划页新建计划
 *   6. 设置页 → 点击底部「首页」→ 首页高亮打卡按钮并介绍使用方式（最后一步）
 * - 非微信小程序端引导流程（微信登录/订阅不可用）：
 *   · 第 3 步改为：登录页 → 点击「立即注册」→ 注册页高亮整个卡片（允许填写表单）→ 注册成功后回到设置页
 *   · 第 4 步改为：设置页 → 点击「通知方式」（提示卡片说明完整流程：进入通知方式页添加邮件并保存）→ 通知方式页内无引导蒙版、用户自由操作 → 返回设置页进入步骤 5
 *   · 其余步骤与微信小程序端一致
 * - 每个页面 onShow 时调用 onPageEnter(pageName) 上报当前页面，store 据此推进/回退步骤
 * - 已登录用户从首页启动引导（startGuideForLoggedIn）：完成步骤 1 后自动跳过登录相关步骤，直接进入步骤 4；
 *   步骤徽章通过 guideMode='logged-in' 重新映射为连续的 1-4 编号
 * - 步骤配置支持 shape（circle/pill，控制高亮圆角）与 cardPosition（bottom/anchor-top 等，控制提示卡片位置）
 * - 目标元素位置由 useGuideTarget composable 在各页面/组件内查询并上报
 */
export const useGuideStore = defineStore('guide', () => {
  // 引导是否激活
  const isActive = ref(false)
  // 当前步骤索引（0-based，对应 steps 数组内部索引）
  const currentStep = ref(0)
  // 当前所在页面名称（由各页面 onShow 上报）
  const currentPage = ref('')
  // 各目标元素的位置信息（key → { top, left, width, height, right, bottom }）
  const targetRects = ref({})
  // 已登录用户启动引导时：完成步骤 1（点击设置）后跳过登录步骤直接跳到步骤 4
  const fastForwardToStep4 = ref(false)
  // 引导模式：'full' 为完整 6 步（未登录），'logged-in' 为已登录跳过登录步骤的 4 步
  const guideMode = ref('full')
  // 当前运行平台是否为微信小程序（通过编译期条件确定，决定使用哪套步骤配置）
  const isWechatMP = ref(false)
  // #ifdef MP-WEIXIN
  isWechatMP.value = true
  // #endif

  // ===== 微信小程序端步骤配置 =====
  const wechatSteps = [
    {
      page: 'home',
      target: 'settings-tab',
      stepNumber: 1,
      padding: 0,
      key: 'settingsTab'
    },
    {
      page: 'settings',
      target: 'profile-card',
      stepNumber: 2,
      padding: 0,
      key: 'profileCard'
    },
    {
      page: 'login',
      target: 'wechat-login',
      stepNumber: 3,
      padding: 10,
      key: 'wechatLogin'
    },
    {
      page: 'settings',
      target: 'notification-method',
      stepNumber: 4,
      padding: 0,
      key: 'notificationOptional',
      optional: true,
      skipTo: 'plan-method'
    },
    {
      page: 'notification',
      target: 'add-notification',
      stepNumber: 4,
      padding: 0,
      key: 'addNotification',
      skipTo: 'plan-method'
    },
    {
      page: 'notification',
      target: 'wechat-auth-button',
      stepNumber: 4,
      padding: 0,
      shape: 'pill',
      cardPosition: 'anchor-top',
      cardAnchor: 'notification-form-card',
      key: 'wechatAuth',
      skipTo: 'plan-method'
    },
    {
      page: 'settings',
      target: 'plan-method',
      stepNumber: 5,
      padding: 0,
      key: 'planMethod'
    },
    {
      page: 'plan',
      target: 'new-plan',
      stepNumber: 5,
      padding: 0,
      key: 'newPlan'
    },
    {
      page: 'settings',
      target: 'home-tab',
      stepNumber: 6,
      padding: 0,
      key: 'homeTab'
    },
    {
      page: 'home',
      target: 'checkin-button',
      stepNumber: 6,
      padding: 0,
      shape: 'circle',
      key: 'checkin'
    }
  ]

  // ===== 非微信小程序端步骤配置（微信登录/订阅不可用） =====
  const nonWechatSteps = [
    {
      page: 'home',
      target: 'settings-tab',
      stepNumber: 1,
      padding: 0,
      key: 'settingsTab'
    },
    {
      page: 'settings',
      target: 'profile-card',
      stepNumber: 2,
      padding: 0,
      key: 'profileCard'
    },
    {
      page: 'login',
      target: 'register-link',
      stepNumber: 3,
      padding: 0,
      key: 'registerLink'
    },
    {
      page: 'register',
      target: 'register-card',
      stepNumber: 3,
      padding: 8,
      key: 'registerCard'
    },
    {
      page: 'settings',
      target: 'notification-method',
      stepNumber: 4,
      padding: 0,
      key: 'notificationOptionalNonWechat',
      optional: true,
      skipTo: 'plan-method'
    },
    {
      page: 'settings',
      target: 'plan-method',
      stepNumber: 5,
      padding: 0,
      key: 'planMethod'
    },
    {
      page: 'plan',
      target: 'new-plan',
      stepNumber: 5,
      padding: 0,
      key: 'newPlan'
    },
    {
      page: 'settings',
      target: 'home-tab',
      stepNumber: 6,
      padding: 0,
      key: 'homeTab'
    },
    {
      page: 'home',
      target: 'checkin-button',
      stepNumber: 6,
      padding: 0,
      shape: 'circle',
      key: 'checkin'
    }
  ]

  // 当前生效的步骤配置（根据平台自动选择）
  const steps = ref(isWechatMP.value ? wechatSteps : nonWechatSteps)

  // 当前步骤数据（注入翻译后的标题与说明，使其随语言切换即时更新）
  // 注意：t() 读取模块级 currentLocale，非 Vue 响应式；必须在 computed 内读取
  // languageStore.current 以建立响应式依赖，否则切换语言时引导卡片文案不会重算。
  const languageStore = useLanguageStore()
  const currentStepData = computed(() => {
    void languageStore.current
    const step = steps.value[currentStep.value]
    if (!step) return null
    const base = `guide.steps.${step.key}`
    return {
      ...step,
      title: t(`${base}.title`),
      description: t(`${base}.description`)
    }
  })

  // 总步骤数（按用户可见 stepNumber 的最大值计算）
  const totalSteps = computed(() => {
    const numbers = steps.value.map(s => s.stepNumber).filter(n => typeof n === 'number')
    return numbers.length ? Math.max(...numbers) : steps.value.length
  })

  // 根据引导模式映射内部步骤索引到用户可见步骤号（已登录时跳过登录相关步骤，保证编号连续）
  const displayStepNumber = computed(() => {
    const step = currentStepData.value
    if (!step) return 1
    if (guideMode.value === 'logged-in') {
      if (currentStep.value === 0) return 1
      // 登录相关步骤被跳过，剩余步骤的 stepNumber 4/5/6 对外显示为 2/3/4
      const n = step.stepNumber
      if (n === 4) return 2
      if (n === 5) return 3
      if (n === 6) return 4
      return n
    }
    return step.stepNumber
  })

  // 根据引导模式返回用户可见总步数
  const displayTotalSteps = computed(() => {
    return guideMode.value === 'logged-in' ? 4 : totalSteps.value
  })

  // 开启新手引导（从第 1 步开始）
  function startGuide() {
    isActive.value = true
    currentStep.value = 0
    targetRects.value = {}
    fastForwardToStep4.value = false
    guideMode.value = 'full'
  }

  // 已登录用户开启新手引导：从第 1 步开始，点击设置后跳过登录步骤直接进入步骤 4
  function startGuideForLoggedIn() {
    isActive.value = true
    currentStep.value = 0
    targetRects.value = {}
    fastForwardToStep4.value = true
    guideMode.value = 'logged-in'
  }

  // 跳过引导（用户主动取消）
  function skipGuide() {
    isActive.value = false
    currentStep.value = 0
    targetRects.value = {}
    fastForwardToStep4.value = false
    guideMode.value = 'full'
  }

  // 完成引导（全部步骤完成）
  function completeGuide() {
    isActive.value = false
    currentStep.value = 0
    targetRects.value = {}
    fastForwardToStep4.value = false
    guideMode.value = 'full'
  }

  // 前进到下一步（用于页面内完成某个操作后主动推进，如点击「添加新的通知方式」）
  function nextStep() {
    if (currentStep.value < steps.value.length - 1) {
      currentStep.value++
    }
  }

  // 跳转到指定目标步骤（用于可选步骤的「跳过」分支）
  function skipToStepByTarget(targetKey) {
    const idx = steps.value.findIndex(s => s.target === targetKey)
    if (idx !== -1) {
      currentStep.value = idx
    }
  }

  // 登录/注册成功后推进引导（由登录页在登录成功跳转前调用）
  // 当前步骤处于登录页（login）时，跳过后续注册页步骤，直接进入「通知方式」步骤。
  // 场景：App/H5 端用户在登录页直接账号密码/指纹登录（未走注册流程），
  // 若不主动推进，返回设置页时 onPageEnter 会把步骤回退到 profile-card（第 2 步），
  // 表现为「引导项没有向下更新」。
  // 微信小程序端步骤 3 之后本就是 settings 页，onPageEnter 会自动推进；
  // 此处主动推进到同一目标步骤，幂等无副作用。
  function advanceOnLoginSuccess() {
    if (!isActive.value) return
    const step = steps.value[currentStep.value]
    if (!step || step.page !== 'login') return
    const idx = steps.value.findIndex(s => s.target === 'notification-method')
    if (idx !== -1) {
      currentStep.value = idx
    }
  }

  // 页面进入时上报（由各页面 onShow 调用）
  // 根据当前步骤与页面名的前后关系推进或回退；页面名可能重复出现，因此不再使用 findIndex
  function onPageEnter(page) {
    currentPage.value = page
    if (!isActive.value) return
    const step = steps.value[currentStep.value]
    if (!step) return

    // 当前步骤已在该页面，无需调整
    if (step.page === page) return

    // 下一步页面匹配：前进一步
    const next = steps.value[currentStep.value + 1]
    if (next && next.page === page) {
      // 已登录用户从首页启动引导：完成步骤 1（点击设置）后跳过登录步骤，直接进入步骤 4
      if (fastForwardToStep4.value && currentStep.value === 0) {
        const step4Idx = steps.value.findIndex(s => s.target === 'notification-method')
        if (step4Idx !== -1) {
          currentStep.value = step4Idx
        } else {
          currentStep.value++
        }
        fastForwardToStep4.value = false
      } else {
        currentStep.value++
      }
      return
    }

    // 上一步页面匹配：回退一步
    const prev = steps.value[currentStep.value - 1]
    if (prev && prev.page === page) {
      currentStep.value--
    }
  }

  // 设置目标元素位置（由 useGuideTarget composable 调用）
  // 属性级赋值：直接修改 targetRects.value[key]，触发 key 级响应式依赖，
  // 不创建新对象引用，避免 ref 级依赖触发导致 BeginnerGuide 所有依赖 targetRects
  // 的 computed 链全量重算（ref 内 plain object 在 ref 创建时已被 reactive 包装）。
  function setTargetRect(key, rect) {
    targetRects.value[key] = rect
  }

  // 清除目标元素位置（页面离开时清理）
  function clearTargetRect(key) {
    delete targetRects.value[key]
  }

  return {
    isActive,
    currentStep,
    currentPage,
    targetRects,
    fastForwardToStep4,
    guideMode,
    isWechatMP,
    steps,
    currentStepData,
    totalSteps,
    displayStepNumber,
    displayTotalSteps,
    startGuide,
    startGuideForLoggedIn,
    skipGuide,
    completeGuide,
    nextStep,
    skipToStepByTarget,
    advanceOnLoginSuccess,
    onPageEnter,
    setTargetRect,
    clearTargetRect
  }
})
