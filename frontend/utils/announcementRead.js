/**
 * 首页公告已读持久化工具
 * ----------------------------------------------------------------------------
 * 需求：
 *   1) 已读状态与登录 token 绑定，token 过期后已读失效（未读公告重新展示）。
 *   2) 公告在后端被更新后（updated_at 变化）忽略前端已读缓存，重新展示。
 * 实现：本地存储 { exp, readMap }
 *   - exp：当前 JWT 的过期时间戳（秒），用于绑定登录会话；缺失/不一致（重新登录/过期）视为失效。
 *   - readMap：{ [公告id]: 已读时该公告的 updated_at }。
 *     判定「已读」需同时满足：id 存在于 readMap 且其值等于当前公告的 updated_at。
 *     因此：新增公告（id 不存在）或被更新的公告（updated_at 变化）均判为未读，重新展示。
 */

const STORAGE_KEY = 'announcementReadState'

/**
 * 解析 JWT payload 中的 exp（秒）。解析失败返回 null。
 * 兼容微信小程序（无 atob）：优先用全局 atob，否则回退 uni 的 base64 工具。
 */
function getTokenExp(token) {
  if (!token || typeof token !== 'string') return null
  const parts = token.split('.')
  if (parts.length < 2) return null
  try {
    let b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const pad = b64.length % 4
    if (pad) b64 += '='.repeat(4 - pad)

    let bin
    if (typeof atob === 'function') {
      bin = atob(b64)
    } else {
      const ab = uni.base64ToArrayBuffer(b64)
      const bytes = new Uint8Array(ab)
      let s = ''
      for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i])
      bin = s
    }
    let json
    try {
      json = decodeURIComponent(escape(bin))
    } catch (e) {
      json = bin
    }
    const payload = JSON.parse(json)
    return payload.exp || null
  } catch (e) {
    return null
  }
}

/**
 * 读取当前 token 下的已读映射 { id: updated_at }。
 * 当前无 token / 解析失败 / 过期 / 与已存 exp 不一致时，返回空对象（全部视为未读）。
 */
function loadReadMap() {
  const token = uni.getStorageSync('accessToken') || ''
  const exp = getTokenExp(token)
  if (!exp) return {}
  try {
    const state = uni.getStorageSync(STORAGE_KEY)
    if (!state || state.exp !== exp) return {}
    return state.readMap && typeof state.readMap === 'object' ? state.readMap : {}
  } catch (e) {
    return {}
  }
}

/**
 * 标记某公告已读（记录该公告当前的 updated_at，并绑定当前 token 的 exp）。
 * @param {object} item 公告项，含 id 与 updated_at
 */
function markRead(item) {
  if (!item || item.id == null) return
  const token = uni.getStorageSync('accessToken') || ''
  const exp = getTokenExp(token)
  if (!exp) return
  const readMap = loadReadMap()
  readMap[item.id] = item.updated_at || ''
  try {
    uni.setStorageSync(STORAGE_KEY, { exp, readMap })
  } catch (e) {
    // 存储失败时静默降级，不影响本次展示
  }
}

/**
 * 从公告列表中过滤出未读项（绑定当前 token；updated_at 变化视为未读）。
 * @param {Array} list 公告列表，每项含 id 与 updated_at
 * @returns {Array} 未读公告列表
 */
function getUnread(list) {
  if (!list || !list.length) return []
  const readMap = loadReadMap()
  return list.filter((item) => readMap[item.id] !== (item.updated_at || ''))
}

export { loadReadMap, markRead, getUnread }
