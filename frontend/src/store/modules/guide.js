import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

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
 *   · 第 3 步改为：登录页 → 点击「立即注册」→ 注册页提交 → 普通账号密码登录 → 登录成功后回到设置页
 *   · 第 4 步改为：设置页 → 点击「通知方式」→ 添加新方式 → 选择邮件 → 保存邮件通知 → 回到设置页
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
    },
    {
      page: 'settings',
      target: 'notification-method',
      stepNumber: 4,
      padding: 0,
      title: '设置通知方式（可选）',
      description: '点击「通知方式」可添加微信订阅提醒；本次为可选项，也可跳过直接进入下一步。',
      optional: true,
      skipTo: 'plan-method'
    },
    {
      page: 'notification',
      target: 'add-notification',
      stepNumber: 4,
      padding: 0,
      title: '添加新的通知方式',
      description: '点击「添加新的通知方式」，选择微信并授权订阅消息。',
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
      title: '授权订阅提醒',
      description: '点击「授权订阅提醒」并允许，打卡时间到达将通过微信消息提醒您。',
      skipTo: 'plan-method'
    },
    {
      page: 'settings',
      target: 'plan-method',
      stepNumber: 5,
      padding: 0,
      title: '制定计划',
      description: '点击「制定计划」，创建您的第一个打卡计划。'
    },
    {
      page: 'plan',
      target: 'new-plan',
      stepNumber: 5,
      padding: 0,
      title: '新建计划',
      description: '点击「新建计划」，填写计划信息后保存。'
    },
    {
      page: 'settings',
      target: 'home-tab',
      stepNumber: 6,
      padding: 0,
      title: '返回首页',
      description: '点击底部「首页」，回到首页查看打卡按钮。'
    },
    {
      page: 'home',
      target: 'checkin-button',
      stepNumber: 6,
      padding: 0,
      shape: 'circle',
      title: '立即打卡',
      description: '到达提醒时间后，点击打卡按钮即可完成打卡。本次为最后一次引导。'
    }
  ]

  // ===== 非微信小程序端步骤配置（微信登录/订阅不可用） =====
  const nonWechatSteps = [
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
      target: 'register-link',
      stepNumber: 3,
      padding: 0,
      title: '注册账号',
      description: '点击「立即注册」，进入账号注册页面。'
    },
    {
      page: 'register',
      target: 'register-submit',
      stepNumber: 3,
      padding: 0,
      shape: 'pill',
      title: '填写并提交注册',
      description: '填写用户名、密码、邮箱和验证码后，点击「注册」按钮完成注册。'
    },
    {
      page: 'login',
      target: 'login-submit',
      stepNumber: 3,
      padding: 0,
      shape: 'pill',
      title: '普通登录',
      description: '输入账号密码后点击「登录」，登录成功后自动回到设置页。'
    },
    {
      page: 'settings',
      target: 'notification-method',
      stepNumber: 4,
      padding: 0,
      title: '设置通知方式（可选）',
      description: '点击「通知方式」可添加邮件提醒；本次为可选项，也可跳过直接进入下一步。',
      optional: true,
      skipTo: 'plan-method'
    },
    {
      page: 'notification',
      target: 'add-notification',
      stepNumber: 4,
      padding: 0,
      title: '添加新的通知方式',
      description: '点击「添加新的通知方式」，选择邮件类型并填写 SMTP 配置。',
      skipTo: 'plan-method'
    },
    {
      page: 'notification',
      target: 'email-type-radio',
      stepNumber: 4,
      padding: 0,
      title: '选择邮件通知',
      description: '在通知类型中选择「邮件」，即可配置邮件 SMTP 提醒。'
    },
    {
      page: 'notification',
      target: 'email-save-button',
      stepNumber: 4,
      padding: 0,
      shape: 'pill',
      cardPosition: 'anchor-top',
      cardAnchor: 'notification-form-card',
      title: '保存邮件通知',
      description: '填写 SMTP 服务器、端口、发件邮箱和客户端专用密码后，点击「保存通知」。',
      skipTo: 'plan-method'
    },
    {
      page: 'settings',
      target: 'plan-method',
      stepNumber: 5,
      padding: 0,
      title: '制定计划',
      description: '点击「制定计划」，创建您的第一个打卡计划。'
    },
    {
      page: 'plan',
      target: 'new-plan',
      stepNumber: 5,
      padding: 0,
      title: '新建计划',
      description: '点击「新建计划」，填写计划信息后保存。'
    },
    {
      page: 'settings',
      target: 'home-tab',
      stepNumber: 6,
      padding: 0,
      title: '返回首页',
      description: '点击底部「首页」，回到首页查看打卡按钮。'
    },
    {
      page: 'home',
      target: 'checkin-button',
      stepNumber: 6,
      padding: 0,
      shape: 'circle',
      title: '立即打卡',
      description: '到达提醒时间后，点击打卡按钮即可完成打卡。本次为最后一次引导。'
    }
  ]

  // 当前生效的步骤配置（根据平台自动选择）
  const steps = ref(isWechatMP.value ? wechatSteps : nonWechatSteps)

  // 当前步骤数据
  const currentStepData = computed(() => steps.value[currentStep.value] || null)

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
    onPageEnter,
    setTargetRect,
    clearTargetRect
  }
})
