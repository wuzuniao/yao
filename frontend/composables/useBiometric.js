// #ifdef APP-PLUS
/**
 * 生物识别（指纹）登录 composable（仅 App 端）
 * --------------------------------------------------------------------------
 * - 设备指纹能力检测：checkIsSupportSoterAuthentication + checkIsSoterEnrolledInDevice
 * - 指纹验证：uni.startSoterAuthentication（authContent 文案已确认为「指纹验证已登录」）
 * - 本地凭证安全存储：PBKDF2 派生 AES-256-GCM 密钥，加密 biometric_token 后存本地
 *   · 密钥派生材料来自设备指纹（首次登录生成的 UUID + 机型/系统版本），不使用硬编码密钥
 *   · 仅 App 端引入 @noble/ciphers（纯 ESM，支持 AES-256-GCM）
 * - 注意：device_id 由本地生成并持久化，登录/续期/指纹登录时一并传给后端做绑定校验
 */
import { gcm } from '@noble/ciphers/aes'
import { pbkdf2 } from '@noble/hashes/pbkdf2'
import { sha256 } from '@noble/hashes/sha256'

const DEVICE_ID_KEY = 'biometricDeviceId'
const TOKEN_ENC_KEY = 'biometricTokenEnc'
const BIO_ENABLED_KEY = 'biometricEnabled'

// 派生密钥用的设备信息盐（非敏感，仅增加跨设备派生差异）
function getDeviceSalt() {
  try {
    const info = uni.getSystemInfoSync()
    return `${info.model || ''}|${info.system || ''}|${info.platform || ''}`
  } catch (e) {
    return 'default-salt'
  }
}

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

// PBKDF2 高迭代派生 AES-256 密钥（32 字节）
function deriveKey(passphrase) {
  const salt = new TextEncoder().encode(`yao-bio-${getDeviceSalt()}`)
  return pbkdf2(sha256, passphrase, salt, { c: 120000, dkLen: 32 })
}

// base64 编解码（兼容 App 端 uni 环境）
function b64encode(bytes) {
  let bin = ''
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i])
  return btoa(bin)
}
function b64decode(str) {
  const bin = atob(str)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

// 加密 biometric_token 为 base64 字符串（iv + ciphertext+tag）
function encryptToken(plainToken) {
  const key = deriveKey(getDeviceId())
  const nonce = new Uint8Array(12)
  try {
    const cryptoObj = (typeof crypto !== 'undefined' && crypto) || (typeof globalThis !== 'undefined' && globalThis.crypto)
    if (cryptoObj && cryptoObj.getRandomValues) cryptoObj.getRandomValues(nonce)
    else for (let i = 0; i < nonce.length; i++) nonce[i] = (Math.random() * 256) | 0
  } catch (e) {
    for (let i = 0; i < nonce.length; i++) nonce[i] = (Math.random() * 256) | 0
  }
  const pt = new TextEncoder().encode(plainToken)
  const cipher = gcm(key, nonce).encrypt(pt)
  // nonce(12) + cipher
  const merged = new Uint8Array(nonce.length + cipher.length)
  merged.set(nonce, 0)
  merged.set(cipher, nonce.length)
  return b64encode(merged)
}

// 解密 base64 字符串还原 biometric_token（失败返回空串）
function decryptToken(encStr) {
  try {
    const merged = b64decode(encStr)
    const nonce = merged.slice(0, 12)
    const ct = merged.slice(12)
    const key = deriveKey(getDeviceId())
    const pt = gcm(key, nonce).decrypt(ct)
    return new TextDecoder().decode(pt)
  } catch (e) {
    console.warn('解密生物识别凭证失败', e)
    return ''
  }
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

  // 加密并存储后端下发的 biometric_token
  function storeBiometricToken(token) {
    if (!token) return false
    try {
      uni.setStorageSync(TOKEN_ENC_KEY, encryptToken(token))
      return true
    } catch (e) {
      console.warn('存储生物识别凭证失败', e)
      return false
    }
  }

  // 读取并解密本地 biometric_token（无则返回空串）
  function getBiometricToken() {
    try {
      const enc = uni.getStorageSync(TOKEN_ENC_KEY)
      if (!enc) return ''
      return decryptToken(enc)
    } catch (e) {
      return ''
    }
  }

  // 清除本地 biometric_token（关闭开关时调用，不退出登录）
  function clearBiometricToken() {
    try {
      uni.removeStorageSync(TOKEN_ENC_KEY)
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
