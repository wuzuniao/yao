/**
 * App 推送（友盟+ U-Push）composable
 * --------------------------------------------------------------------------
 * 仅 App 端（#ifdef APP-PLUS）生效，小程序 / H5 端调用直接返回 false，不产生副作用。
 * 通过已购插件 xtf-umengpush（普通授权版，绑定 __UNI__528E611 / 包名 com.wuzuniao.yao）集成，
 * 友盟 appKey / messageSecret 配置在插件自带 umeng-push-config.json，不在 manifest.json。
 *  - getDeviceToken(): 取本机友盟 deviceToken
 *  - reportDeviceToken({ createIfMissing, silent }): 上报设备标识到后端通知渠道
 *      - createIfMissing=true：通知方式页添加，渠道不存在时新建
 *      - createIfMissing=false：打卡完成时刷新，渠道不存在后端静默跳过
 *  - registerPushClick(): 监听通知栏点击，跳转首页打卡（App 启动/后台唤起均生效）
 */
// 友盟推送插件 API 仅 App 端存在，import 必须置于条件编译内，避免小程序/H5 引用不存在的导出
// #ifdef APP-PLUS
import {
  initializeUmengPush,
  createUmengPushInitOptions,
  onUmengPushRuntimeEvent,
  getUmengPushDebugState,
  requestNotificationPermission
} from '@/uni_modules/xtf-umengpush'
// #endif

import { upsertAppPushChannel } from '../api/modules/notification'

// 点击推送通知后的跳转页面（与后端 UMENG_PUSH_PAGE 保持一致）
const PUSH_TARGET_PAGE = '/pages/index/index'

// 通知栏点击监听只需注册一次，避免重复跳转
let clickListenerRegistered = false
// 友盟 SDK 只需初始化一次
let initialized = false

/**
 * 初始化友盟推送 SDK（幂等）
 * 必须早于取 token / 注册点击监听。普通授权版源码在云端，仅支持云打包/自定义基座。
 */
function initUmeng() {
  // #ifndef APP-PLUS
  return false
  // #endif

  // #ifdef APP-PLUS
  if (initialized) {
    return true
  }
  try {
    const result = initializeUmengPush(createUmengPushInitOptions())
    initialized = !!(result && result.success)
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
 * 申请系统通知权限（Android 13+ 弹系统授权，低版本直接返回已授权）
 * 不随初始化自动调用，仅在通知方式页用户主动添加 App 推送时由页面调用，
 * 避免 App 启动即弹出授权打扰用户。
 * @returns {boolean} 是否成功发起申请
 */
function requestPermission() {
  // #ifndef APP-PLUS
  return false
  // #endif

  // #ifdef APP-PLUS
  try {
    const platform = plus.os.name === 'iOS' ? 'ios' : 'android'
    if (platform === 'android') {
      // 直接申请 Android 标准通知权限（Android 13+ 弹系统授权，低版本默认授予）。
      // 不用友盟插件的 requestNotificationPermission：其在部分厂商 ROM（如 vivo）上
      // 会尝试跳转厂商特定设置页，页面不存在时抛 "Not Found" 报错。标准系统权限
      // 申请不依赖厂商页面，跨 ROM 稳定，且满足「主动添加时授权提示」需求。
      const activity = plus.android.runtimeMainActivity()
      plus.android.requestPermissions(
        ['android.permission.POST_NOTIFICATIONS'],
        () => {},
        () => {}
      )
      void activity
      return true
    }
    // iOS：走友盟封装（相对成熟，无厂商 ROM 差异）
    if (!initialized) {
      initUmeng()
    }
    requestNotificationPermission({
      success() {},
      fail() {}
    })
    return true
  } catch (e) {
    console.warn('[AppPush] 申请通知权限异常：', e)
    return false
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
        // 初始化同步返回 deviceToken；首次注册可能稍晚，延迟重试一次兜底
        let token = ''
        try {
          const res = getUmengPushDebugState()
          token = (res && res.deviceToken) || ''
        } catch (e) {
          token = ''
        }
        if (token) {
          resolve({ token, platform })
          return
        }
        setTimeout(() => {
          let retryToken = ''
          try {
            const retry = getUmengPushDebugState()
            retryToken = (retry && retry.deviceToken) || ''
          } catch (e) {
            retryToken = ''
          }
          resolve(retryToken ? { token: retryToken, platform } : null)
        }, 1500)
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
      uni.showToast({ title: '请在App中开启推送通知', icon: 'none' })
    }
    return false
    // #endif

    // #ifdef APP-PLUS
    const device = await getDeviceToken()
    if (!device) {
      if (!silent) {
        uni.showToast({ title: '获取设备标识失败，请稍后重试', icon: 'none' })
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
        uni.showToast({ title: e.message || '开启推送失败', icon: 'none' })
      }
      return false
    }
    // #endif
  }

  /**
   * 注册通知栏点击监听：点击推送后跳转首页打卡
   * 改用友盟插件 onUmengPushRuntimeEvent 的 notification-click 事件（替代 5+ 引擎 plus.push）
   * payload 为字符串，解析出 route 字段跳转；非 JSON 时回退首页
   */
  function registerPushClick() {
    // #ifdef APP-PLUS
    if (clickListenerRegistered) {
      return
    }
    clickListenerRegistered = true
    initUmeng()
    onUmengPushRuntimeEvent((event) => {
      if (!event || event.type !== 'notification-click') {
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

  return { getDeviceToken, reportDeviceToken, registerPushClick, requestPermission }
}
