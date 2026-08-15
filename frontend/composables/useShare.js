/**
 * useShare —— 微信小程序分享统一配置
 * --------------------------------------------------------------------------
 * 功能：为页面提供分享配置（标题/路径/封面图），并显式启用分享菜单。
 *   - 转发给朋友：对应 onShareAppMessage 生命周期（点击右上角"..."→转发）
 *   - 分享到朋友圈：对应 onShareTimeline 生命周期（点击右上角"..."→分享到朋友圈）
 *   - 复制链接：微信小程序"..."菜单默认提供，依赖转发功能启用后自动可用
 *
 * 钩子注册机制（重要，与常规 composable 不同）：
 *   uni-app 编译器只检测【页面源码中直接调用】的 onShareAppMessage/onShareTimeline
 *   并为该页注入 __runtimeHooks；在 composable 内注册（本文件）不会被编译器检测，
 *   小程序侧不生成桥接方法，微信拿不到回调 → 分享回落默认行为（自动截页）。
 *   因此分享钩子实际由 main.js 的全局 shareMixin（options 钩子）统一注册：
 *   uni-app 运行时的 initMixinRuntimeHooks 会扫描全局 mixin 中的分享钩子，
 *   并为每个页面注入小程序侧桥接方法，钩子体内读取本函数挂到页面实例的
 *   $shareConfig 返回给微信。页面只需调用 useShare()，无需（也不应）再单独注册。
 *
 *   依据：
 *   - wx.showShareMenu：https://developers.weixin.qq.com/miniprogram/dev/api/share/wx.showShareMenu.html
 *   - Page 生命周期：https://developers.weixin.qq.com/miniprogram/dev/reference/api/Page.html
 *
 * 使用示例：
 *   import { useShare } from '../../composables/useShare'
 *   useShare({ title: '首页' })                          // 封面默认 SHARE_COVER_URL 词云图
 *   useShare({ title: '首页', imageUrl: 'https://...' }) // 覆盖封面
 *
 * @param {Object} [options]
 * @param {string} [options.title] - 分享标题，默认"无足鸟按时吃药打卡"
 * @param {string} [options.path] - 转发后打开的页面路径（带 / 开头），
 *        不传则使用当前页面路径
 * @param {string} [options.imageUrl] - 分享封面图，默认 config/env.js 的
 *        SHARE_COVER_URL（https 网络地址，须在小程序后台配置 downloadFile 合法域名）
 */
import { onLoad } from '@dcloudio/uni-app'
import { getCurrentInstance } from 'vue'
import { SHARE_COVER_URL } from '../config/env'
import { t } from '../locale'

const DEFAULT_TITLE = t('share.default')

export function useShare(options = {}) {
  const { title = DEFAULT_TITLE, path, imageUrl = SHARE_COVER_URL } = options

  // 分享为微信小程序专有功能，H5 端无分享菜单，整体条件编译隔离
  // #ifdef MP-WEIXIN
  // 分享配置挂到当前页面实例，由 main.js 全局 shareMixin 的分享钩子读取返回给微信
  const instance = getCurrentInstance()
  if (instance && instance.proxy) {
    instance.proxy.$shareConfig = { title, path, imageUrl }
  }

  // 页面加载时显式启用分享菜单（含朋友圈），否则菜单项为灰色不可点击
  onLoad(() => {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    })
  })
  // #endif
}
