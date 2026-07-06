/**
 * useShare —— 微信小程序分享统一配置
 * --------------------------------------------------------------------------
 * 功能：为页面注册"转发给朋友"与"分享到朋友圈"两个分享入口。
 *   - 转发给朋友：对应 onShareAppMessage 生命周期（点击右上角"..."→转发）
 *   - 分享到朋友圈：对应 onShareTimeline 生命周期（点击右上角"..."→分享到朋友圈）
 *   - 复制链接：微信小程序"..."菜单默认提供，无需额外代码配置
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
import { onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'

const DEFAULT_TITLE = '无足鸟按时吃药打卡'

export function useShare(options = {}) {
  const { title = DEFAULT_TITLE, path, imageUrl } = options

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
