/**
 * 微信订阅消息授权 composable
 * --------------------------------------------------------------------------
 * 封装 uni.requestSubscribeMessage（仅在微信小程序端生效，H5/开发端自动跳过）
 *  - requestSubscribe({ silent }): 发起一次性订阅授权
 *      - silent=false（默认，显式授权场景）：授权失败有 toast 提示
 *      - silent=true（打卡后静默补授权场景）：失败静默忽略，不影响主流程
 *  - isSubscribeSilentRejected(): 检测用户是否已勾选「总是保持以上选择」并拒绝
 *      （即静默拒绝状态，此时后续 requestSubscribeMessage 不再弹窗，直接返回 reject）
 *  - 用户点击「允许」(accept) 后调用后端 grantWechatChannel 累加下发额度
 */
import { grantWechatChannel } from '../api/modules/notification'

const TEMPLATE_ID = import.meta.env.VITE_WX_SUBSCRIBE_TEMPLATE_ID || ''

export function useWechatSubscribe() {
  /**
   * 发起微信订阅消息授权
   * @param {{ silent?: boolean }} [options]
   * @returns {Promise<boolean>} 是否授权成功（用户允许且后端记录成功）
   */
  async function requestSubscribe({ silent = false } = {}) {
    // 非微信小程序端不发起授权（如 H5 / 开发预览），避免无意义弹窗
    // #ifndef MP-WEIXIN
    if (!silent) {
      uni.showToast({ title: '请在微信小程序中使用订阅消息', icon: 'none' })
    }
    return false
    // #endif

    // #ifdef MP-WEIXIN
    if (!TEMPLATE_ID) {
      if (!silent) {
        uni.showToast({ title: '订阅消息模板未配置', icon: 'none' })
      }
      return false
    }
    try {
      const res = await uni.requestSubscribeMessage({
        tmplIds: [TEMPLATE_ID]
      })
      // 用户点击「允许」才视为授权成功，后端累加一次下发额度
      if (res && res[TEMPLATE_ID] === 'accept') {
        try {
          await grantWechatChannel()
        } catch (e) {
          if (!silent) {
            uni.showToast({ title: e.message || '授权失败', icon: 'none' })
          }
          return false
        }
        return true
      }
      // 用户拒绝/关闭或模板被封禁：非错误，静默返回（显式场景仅对后端失败提示）
      return false
    } catch (e) {
      if (!silent) {
        uni.showToast({ title: e.message || '授权失败', icon: 'none' })
      }
      return false
    }
    // #endif
  }

  /**
   * 检测用户是否已勾选「总是保持以上选择」并拒绝订阅消息（静默拒绝状态）
   * 通过 uni.getSetting({ withSubscriptions: true }) 查询订阅消息设置：
   *   withSubscriptions 仅返回用户勾选过「总是保持以上选择，不再询问」的记录，
   *   itemSettings[模板ID] === 'reject' 表示用户勾选了「总是保持」并选择拒绝，
   *   此时后续 requestSubscribeMessage 不再弹窗，直接静默返回 reject。
   * @returns {Promise<boolean>} 是否处于静默拒绝状态
   */
  async function isSubscribeSilentRejected() {
    return new Promise((resolve) => {
      uni.getSetting({
        withSubscriptions: true,
        success: (res) => {
          const itemSettings =
            res && res.subscriptionsSetting && res.subscriptionsSetting.itemSettings
          resolve(!!(itemSettings && itemSettings[TEMPLATE_ID] === 'reject'))
        },
        fail: () => resolve(false)
      })
    })
  }

  return { requestSubscribe, isSubscribeSilentRejected }
}
