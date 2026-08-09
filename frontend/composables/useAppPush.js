/**
 * App 推送（友盟+ U-Push）composable
 * --------------------------------------------------------------------------
 * 仅 Android / iOS 端（#ifdef APP-PLUS）生效；鸿蒙端与小程序 / H5 端调用直接返回 false，
 * 不产生副作用。
 *
 * ⚠️ 鸿蒙端为何不支持（勿改回 #ifdef APP）：
 *   xtf-umengpush 为 DCloud 付费「加密」UTS 插件（三端 index.uts 均为密文）。按官方规范，
 *   加密 UTS 插件发行到「Web / 小程序 / 鸿蒙」时须走云端编译换取 module.har，而该云编译链路
 *   仅支持 uni-app x 工程，不支持本项目所用的传统 uni-app 工程。故鸿蒙编译时
 *   oh-package.json5 会声明 utssdk/app-harmony/module.har 依赖但该文件永不生成，
 *   ohpm 安装即报 00617202 Fetch Local Package Failed。
 *   因此已在插件 package.json 将 harmony 标记为 "-"，本文件同步改用 APP-PLUS 隔离，
 *   两者必须保持一致，否则鸿蒙端会残留悬空 import 导致编译失败。
 *   鸿蒙用户的提醒能力由邮件 / 站内信通道承担。
 *
 * 通过已购插件 xtf-umengpush（普通授权版，绑定 __UNI__528E611 / 包名 com.wuzuniao.yao）集成，
 * 友盟 appKey / messageSecret 配置在插件自带 umeng-push-config.json（鸿蒙为 umconfig.json），不在 manifest.json。
 *  - getDeviceToken(): 取本机友盟 deviceToken（初始化返回值 / register-state 事件 / 轮询三重通道）
 *  - reportDeviceToken({ createIfMissing, silent }): 上报设备标识到后端通知渠道
 *      - createIfMissing=true：通知方式页添加，渠道不存在时新建
 *      - createIfMissing=false：打卡完成时刷新，渠道不存在后端静默跳过
 *  - registerPushClick(): 监听通知栏点击，跳转首页打卡（App 启动/后台唤起均生效）
 *  - requestPermission(): 申请系统通知权限，已开启则直接返回、不重复弹窗
 *  - isNotificationEnabled() / openNotificationSettings(): 权限状态查询与设置页跳转
 */
// 友盟推送插件 API 仅 Android / iOS 端存在，import 必须置于条件编译内，
// 避免鸿蒙 / 小程序 / H5 引用不存在的导出（鸿蒙不支持原因见文件头说明）
// #ifdef APP-PLUS
import {
  initializeUmengPush,
  createUmengPushInitOptions,
  onUmengPushRuntimeEvent,
  getUmengPushDebugState,
  getPushDeviceInfo,
  requestNotificationPermission,
  openUmengNotificationSettings
} from '@/uni_modules/xtf-umengpush'
// #endif

import { upsertAppPushChannel } from '../api/modules/notification'
import { t } from '../locale'

// 点击推送通知后的跳转页面（与后端 UMENG_PUSH_PAGE 保持一致）
const PUSH_TARGET_PAGE = '/pages/index/index'
// 等待友盟注册返回 deviceToken 的最长时长（毫秒）
// 真机首次安装需联网向友盟服务器注册，耗时常达数秒，过短会误判为「获取失败」
const DEVICE_TOKEN_TIMEOUT = 12000
// 轮询兜底的间隔（毫秒）：register-state 事件为主，轮询防止事件被其他监听覆盖时取不到
const DEVICE_TOKEN_POLL_INTERVAL = 500

// 通知栏点击监听只需注册一次，避免重复跳转
let clickListenerRegistered = false
// 友盟 SDK 只需初始化一次
let initialized = false
// 缓存已取得的 deviceToken：注册成功后 token 不再变化，避免重复等待
let cachedDeviceToken = ''
// 运行时事件监听只注册一次（插件为单监听器模型，新注册会覆盖旧注册，
// 故点击跳转与 register-state 取 token 必须合并进同一个回调）
let runtimeListenerRegistered = false

/**
 * 记录一次从插件结果中提取到的 deviceToken
 * @param {string | null | undefined} token
 */
function cacheDeviceToken(token) {
  if (typeof token === 'string' && token.length > 0) {
    cachedDeviceToken = token
  }
}

/**
 * 注册友盟运行时事件监听（幂等，单监听器模型下必须集中处理所有事件类型）
 *  - register-state：注册成功时回传 deviceToken，是取 token 的主通道
 *  - notification-click：通知栏点击跳转
 */
function registerRuntimeListener() {
  // #ifdef APP-PLUS
  if (runtimeListenerRegistered) {
    return
  }
  runtimeListenerRegistered = true
  onUmengPushRuntimeEvent((event) => {
    if (!event) {
      return
    }
    // 任何事件都可能携带 deviceToken（register-state 最典型），有则缓存
    cacheDeviceToken(event.deviceToken)
    if (event.type !== 'notification-click') {
      return
    }
    let route = PUSH_TARGET_PAGE
    try {
      const payload = event.payload ? JSON.parse(event.payload) : null
      if (payload && payload.route) {
        route = payload.route
      }
    } catch (e) {
      // payload 非 JSON：按默认首页跳转
    }
    uni.reLaunch({
      url: route,
      fail: () => uni.reLaunch({ url: PUSH_TARGET_PAGE })
    })
  })
  // #endif
}

/**
 * 初始化友盟推送 SDK（幂等）
 * 必须早于取 token / 注册点击监听。普通授权版源码在云端，仅支持云打包/自定义基座。
 * 注意：initializeUmengPush 的返回值本身即携带 deviceToken（已注册过时同步返回），
 * 必须在此处缓存，否则会白白丢弃最快的一条取值通道。
 * @returns {boolean} SDK 是否已完成初始化
 */
function initUmeng() {
  // #ifndef APP-PLUS
  return false
  // #endif

  // #ifdef APP-PLUS
  if (initialized) {
    return true
  }
  // 先挂监听再初始化，避免注册回调早于监听注册而丢失 register-state 事件
  registerRuntimeListener()
  try {
    const result = initializeUmengPush(createUmengPushInitOptions())
    // initialized 以插件返回的 initialized 为准：success 仅表示「本次调用已触发」，
    // 部分平台会先返回 deferred 再延迟完成，用 success 判断会导致重复初始化
    initialized = !!(result && (result.initialized || result.success))
    if (result) {
      cacheDeviceToken(result.deviceToken)
      if (!result.isConfigured) {
        console.warn('[AppPush] 友盟配置不完整，缺失项：', result.missingKeys)
      }
      if (result.registerErrorCode) {
        console.warn('[AppPush] 友盟注册失败：', result.registerErrorCode, result.registerErrorMessage)
      }
    }
    if (!initialized) {
      console.warn('[AppPush] 友盟初始化未成功：', result && result.message)
    }
    return initialized
  } catch (e) {
    console.error('[AppPush] 友盟初始化异常：', e)
    return false
  }
  // #endif
}

/**
 * 查询系统通知权限当前是否已开启
 * @returns {boolean} 已开启返回 true；查询异常时返回 true（避免误拦截正常流程）
 */
function isNotificationEnabled() {
  // #ifndef APP-PLUS
  return false
  // #endif

  // #ifdef APP-PLUS
  try {
    const info = getPushDeviceInfo()
    if (!info) {
      return true
    }
    // systemNotificationEnabled 为系统通知总开关，notificationPermissionGranted 为
    // Android 13+ 的 POST_NOTIFICATIONS 运行时权限，两者需同时满足才能展示通知
    return !!info.systemNotificationEnabled && !!info.notificationPermissionGranted
  } catch (e) {
    console.warn('[AppPush] 查询通知权限状态异常：', e)
    return true
  }
  // #endif
}

/**
 * 申请系统通知权限（已开启则直接返回，不重复弹窗）
 * 不随初始化自动调用，仅在通知方式页用户主动添加 App 推送时由页面调用，
 * 避免 App 启动即弹出授权打扰用户。
 * @returns {Promise<boolean>} 最终是否已获得通知权限
 */
function requestPermission() {
  // #ifndef APP-PLUS
  return Promise.resolve(false)
  // #endif

  // #ifdef APP-PLUS
  return new Promise((resolve) => {
    // 已开启则忽略，不再弹窗打扰
    if (isNotificationEnabled()) {
      resolve(true)
      return
    }
    try {
      if (plus.os.name === 'iOS') {
        // iOS 走友盟封装（相对成熟，无厂商 ROM 差异）：首次调用由系统弹 APNs 授权框，
        // 已拒绝过则系统不再弹窗，此时 granted=false，由调用方引导去系统设置
        initUmeng()
        requestNotificationPermission({
          success: (res) => resolve(!!(res && res.granted)),
          fail: () => resolve(false)
        })
        return
      }
      // Android：申请标准通知权限（Android 13+ 弹系统授权，低版本默认授予）。
      // 不用友盟插件的 requestNotificationPermission：其在部分厂商 ROM（如 vivo）上
      // 会尝试跳转厂商特定设置页，页面不存在时抛 "Not Found" 报错。标准系统权限
      // 申请不依赖厂商页面，跨 ROM 稳定。
      plus.android.requestPermissions(
        ['android.permission.POST_NOTIFICATIONS'],
        () => resolve(isNotificationEnabled()),
        () => resolve(false)
      )
    } catch (e) {
      console.warn('[AppPush] 申请通知权限异常：', e)
      resolve(false)
    }
  })
  // #endif
}

/**
 * 引导用户前往系统设置手动开启通知（用户已拒绝且系统不再弹窗时使用）
 */
function openNotificationSettings() {
  // #ifdef APP-PLUS
  try {
    openUmengNotificationSettings()
  } catch (e) {
    console.warn('[AppPush] 打开通知设置页异常：', e)
  }
  // #endif
}

export function useAppPush() {
  /**
   * 获取本机设备标识（友盟 deviceToken）
   * @returns {Promise<{ token: string, platform: string } | null>} 获取失败返回 null
   */
  async function getDeviceToken() {
    // #ifndef APP-PLUS
    return null
    // #endif

    // #ifdef APP-PLUS
    return new Promise((resolve) => {
      try {
        initUmeng()
        const platform = plus.os.name === 'iOS' ? 'ios' : 'android'
        // 通道一：缓存（注册成功后即固定，最快）
        if (cachedDeviceToken) {
          resolve({ token: cachedDeviceToken, platform })
          return
        }
        // 通道二+三：register-state 运行时事件（已随 initUmeng 注册）为主，
        // 轮询 getUmengPushDebugState 兜底（事件被其他插件单监听器覆盖时仍能取到）。
        // 真机首次安装联网注册常需数秒，故超时放宽到 DEVICE_TOKEN_TIMEOUT。
        const startedAt = Date.now()
        const timer = setInterval(() => {
          if (cachedDeviceToken) {
            clearInterval(timer)
            resolve({ token: cachedDeviceToken, platform })
            return
          }
          let pollToken = ''
          try {
            pollToken = getUmengPushDebugState().deviceToken || ''
          } catch (e) {
            pollToken = ''
          }
          if (pollToken) {
            cachedDeviceToken = pollToken
            clearInterval(timer)
            resolve({ token: pollToken, platform })
            return
          }
          if (Date.now() - startedAt > DEVICE_TOKEN_TIMEOUT) {
            clearInterval(timer)
            resolve(null)
          }
        }, DEVICE_TOKEN_POLL_INTERVAL)
      } catch (e) {
        resolve(null)
      }
    })
    // #endif
  }

  /**
   * 上报设备标识到后端
   * @param {{ createIfMissing?: boolean, silent?: boolean }} [options]
   * @returns {Promise<boolean>} 是否上报成功
   */
  async function reportDeviceToken({ createIfMissing = false, silent = true } = {}) {
    // #ifndef APP-PLUS
    if (!silent) {
      uni.showToast({ title: t('push.appOnly'), icon: 'none' })
    }
    return false
    // #endif

    // #ifdef APP-PLUS
    const device = await getDeviceToken()
    if (!device) {
      if (!silent) {
        // 取不到 token 的常见原因是设备尚未完成友盟注册（网络不通/首次注册未完成），
        // 提示中带上「检查网络」以减少用户无效重试
        uni.showToast({ title: t('push.deviceNotReady'), icon: 'none', duration: 3000 })
      }
      return false
    }
    try {
      await upsertAppPushChannel({
        device_token: device.token,
        platform: device.platform,
        create_if_missing: createIfMissing
      })
      return true
    } catch (e) {
      if (!silent) {
        uni.showToast({ title: e.message || t('push.enableFailed'), icon: 'none' })
      }
      return false
    }
    // #endif
  }

  /**
   * 注册通知栏点击监听：点击推送后跳转首页打卡
   * 实际监听逻辑合并在 registerRuntimeListener 内（插件为单监听器模型，
   * 若此处另行调用 onUmengPushRuntimeEvent 会覆盖 register-state 取 token 的监听）
   */
  function registerPushClick() {
    // #ifdef APP-PLUS
    if (clickListenerRegistered) {
      return
    }
    clickListenerRegistered = true
    initUmeng()
    // #endif
  }

  return {
    getDeviceToken,
    reportDeviceToken,
    registerPushClick,
    requestPermission,
    isNotificationEnabled,
    openNotificationSettings
  }
}
