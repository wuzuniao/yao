/**
 * useShare —— 微信小程序分享统一配置
 * --------------------------------------------------------------------------
 * 功能：为页面注册"转发给朋友"与"分享到朋友圈"两个分享入口，并显式启用菜单。
 *   - 转发给朋友：对应 onShareAppMessage 生命周期（点击右上角"..."→转发）
 *   - 分享到朋友圈：对应 onShareTimeline 生命周期（点击右上角"..."→分享到朋友圈）
 *   - 复制链接：微信小程序"..."菜单默认提供，依赖转发功能启用后自动可用
 *
 * 关键说明：
 *   仅定义 onShareAppMessage / onShareTimeline 只能让菜单项"显示"，
 *   要让菜单项"可点击"还须调用 wx.showShareMenu 显式启用。
 *   依据：https://developers.weixin.qq.com/miniprogram/dev/api/share/wx.showShareMenu.html
 *   —— "设置右上角点开的详情界面中的分享按钮是否可用"，默认 menus 仅 shareAppMessage。
 *
 * 设计依据：
 *   - 微信小程序 Page 生命周期：
 *     https://developers.weixin.qq.com/miniprogram/dev/reference/api/Page.html
 *   - uni-app 页面生命周期：
 *     https://uniapp.dcloud.net.cn/tutorial/page.html#lifecycle
 *   - Vue 3 组合式函数：
 *     https://cn.vuejs.org/guide/reusability/composables.html
 *
 * 使用示例：
 *   import { useShare } from '../../composables/useShare'
 *   useShare({ title: '首页' })
 *
 * @param {Object} [options]
 * @param {string} [options.title] - 分享标题，默认"无足鸟按时吃药打卡"
 * @param {string} [options.path] - 转发后打开的页面路径（带 / 开头），
 *        不传则使用当前页面路径
 * @param {string} [options.imageUrl] - 分享封面图 URL，
 *        不传则由微信自动截取页面内容作为封面
 */
import { onLoad, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'

const DEFAULT_TITLE = '无足鸟按时吃药打卡'

export function useShare(options = {}) {
  const { title = DEFAULT_TITLE, path, imageUrl } = options

  // 页面加载时显式启用分享菜单（含朋友圈），否则菜单项为灰色不可点击
  onLoad(() => {
    // #ifdef MP-WEIXIN
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    })
    // #endif
  })

  // 转发给朋友：返回分享内容
  onShareAppMessage(() => {
    const result = { title }
    if (path) result.path = path
    if (imageUrl) result.imageUrl = imageUrl
    return result
  })

  // 分享到朋友圈：返回分享内容（path 不适用于朋友圈，仅 title/imageUrl）
  onShareTimeline(() => {
    const result = { title }
    if (imageUrl) result.imageUrl = imageUrl
    return result
  })
}
