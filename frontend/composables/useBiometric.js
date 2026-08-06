// #ifdef APP
/**
 * 生物识别（指纹）登录 composable（仅 App 端，含 Android / iOS / HarmonyOS）
 * --------------------------------------------------------------------------
 * 平台宏用 APP 而非 APP-PLUS：APP-PLUS 不含鸿蒙，用它会导致鸿蒙端整个模块被剔除。
 * 鸿蒙端 Soter 三接口自 HBuilderX 4.31 起原生支持（supportMode 同样返回 fingerPrint），
 * 但必须在 harmony-configs/entry/src/main/module.json5 声明 ohos.permission.ACCESS_BIOMETRIC，
 * 否则接口调用直接失败（鸿蒙权限不写在 manifest.json，写在 harmony-configs 增量配置目录）。
 * Android 端另需在 manifest.json 的 app-plus.distribute.android 勾选指纹权限。
 * - 设备指纹能力检测：checkIsSupportSoterAuthentication + checkIsSoterEnrolledInDevice
 * - 指纹验证：uni.startSoterAuthentication（authContent 文案已确认为「指纹验证已登录」）
 * - 本地凭证存储：biometric_token 直接存本地（高熵随机串 + 绑定 device_id，泄露仅限本机可用）
 *   · biometric_token 由后端 secrets.token_hex(32) 生成（256-bit 熵），本身已是安全凭证
 *   · 后端校验 token 与 device_id 绑定关系，跨设备无法复用
 *   · uni storage 在 App 端为应用沙箱，其他应用无法访问
 *   · 此前用 PBKDF2+AES-256-GCM 加密存储，但 @noble/ciphers 在 App 端 5+ 引擎静默失败，
 *     try-catch 吞异常导致凭证从未写入，指纹登录闭环断裂；改用直接存储确保可用
 * - 注意：device_id 由本地生成并持久化，登录/续期/指纹登录时一并传给后端做绑定校验
 */

const DEVICE_ID_KEY = 'biometricDeviceId'
const TOKEN_KEY = 'biometricToken'
const BIO_ENABLED_KEY = 'biometricEnabled'

// 生成或读取本地设备 UUID（首次登录时生成并持久化）
function getDeviceId() {
  let id = ''
  try {
    id = uni.getStorageSync(DEVICE_ID_KEY)
  } catch (e) {
    id = ''
  }
  if (!id) {
    // 简易 UUID v4 生成（App 端 crypto.getRandomValues 可用优先）
    try {
      const cryptoObj = (typeof crypto !== 'undefined' && crypto) || (typeof globalThis !== 'undefined' && globalThis.crypto)
      if (cryptoObj && cryptoObj.getRandomValues) {
        const b = new Uint8Array(16)
        cryptoObj.getRandomValues(b)
        b[6] = (b[6] & 0x0f) | 0x40
        b[8] = (b[8] & 0x3f) | 0x80
        const h = (n) => b[n].toString(16).padStart(2, '0')
        id = `${h(0)}${h(1)}${h(2)}${h(3)}-${h(4)}${h(5)}-${h(6)}${h(7)}-${h(8)}${h(9)}-${h(10)}${h(11)}${h(12)}${h(13)}${h(14)}${h(15)}`
      } else {
        id = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
          const r = (Math.random() * 16) | 0
          const v = c === 'x' ? r : (r & 0x3) | 0x8
          return v.toString(16)
        })
      }
    } catch (e) {
      id = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0
        const v = c === 'x' ? r : (r & 0x3) | 0x8
        return v.toString(16)
      })
    }
    try {
      uni.setStorageSync(DEVICE_ID_KEY, id)
    } catch (e) {
      console.warn('保存设备标识失败', e)
    }
  }
  return id
}

export function useBiometric() {
  // 检测设备是否支持并已录入指纹
  function isAvailable() {
    return new Promise((resolve) => {
      uni.checkIsSupportSoterAuthentication({
        success: (res) => {
          const ok = (res.supportMode || []).includes('fingerPrint')
          if (!ok) return resolve(false)
          uni.checkIsSoterEnrolledInDevice({
            checkAuthMode: 'fingerPrint',
            success: (r) => resolve(!!r.isEnrolled),
            fail: () => resolve(false)
          })
        },
        fail: () => resolve(false)
      })
    })
  }

  // 发起指纹验证（authContent 已确认为「指纹验证已登录」）
  // 成功返回 { authMode, resultJSON, resultJSONSignature }，前端用于调用后端登录
  function authenticate() {
    return new Promise((resolve, reject) => {
      const challenge = String(Date.now())
      uni.startSoterAuthentication({
        requestAuthModes: ['fingerPrint'],
        challenge,
        authContent: '指纹验证已登录',
        success: (res) => resolve(res),
        fail: (err) => reject(err)
      })
    })
  }

  // 本地开关状态
  function isEnabled() {
    try {
      return !!uni.getStorageSync(BIO_ENABLED_KEY)
    } catch (e) {
      return false
    }
  }
  function setEnabled(v) {
    try {
      uni.setStorageSync(BIO_ENABLED_KEY, !!v)
    } catch (e) {
      console.warn('保存指纹开关状态失败', e)
    }
  }

  // 存储后端下发的 biometric_token（直接存储，高熵随机串 + device_id 绑定）
  function storeBiometricToken(token) {
    if (!token) return false
    try {
      uni.setStorageSync(TOKEN_KEY, token)
      return true
    } catch (e) {
      console.warn('存储生物识别凭证失败', e)
      return false
    }
  }

  // 读取本地 biometric_token（无则返回空串）
  function getBiometricToken() {
    try {
      return uni.getStorageSync(TOKEN_KEY) || ''
    } catch (e) {
      return ''
    }
  }

  // 清除本地 biometric_token（关闭开关时调用，不退出登录）
  function clearBiometricToken() {
    try {
      uni.removeStorageSync(TOKEN_KEY)
    } catch (e) {
      console.warn('清除生物识别凭证失败', e)
    }
  }

  return {
    getDeviceId,
    isAvailable,
    authenticate,
    isEnabled,
    setEnabled,
    storeBiometricToken,
    getBiometricToken,
    clearBiometricToken
  }
}
// #endif
