#!/usr/bin/env node
/**
 * 主题图标批量换色脚本（构建期方案）
 *
 * 用法：node scripts/gen-theme-icons.js（或 npm run gen:theme-icons）
 * 输入：assets/images/ 下 16 个参与换色的 PNG（wise/green 主题原图）
 * 输出：static/theme-icons/{主题}/{图标名}.png，共 9 套（green 主题不生成，运行时直接引用原图）
 *
 * 换色规则（与 wise 主题的颜色对比关系对齐）：
 * 1. 逐像素最近锚点匹配（RGB 欧氏距离 ≤ MATCH_DIST）→ 替换为主题目标色，保留 alpha 抗锯齿形状；
 *    未命中任何锚点的像素保持原色（如 tongzhi_1 的红点、白色高光）。
 * 2. 目标色 = 该主题 global.scss 中同名 palette 键的值（如 dh_*_1 的 #2F6C00 → --palette-brand-base）。
 * 3. 对比度兜底（用户约定「暗色主题要突出对比，可按需调整」）：
 *    - 前景色与落点背景（卡片底/页面底）对比度不足时，按 WCAG 亮度公式向明度反方向逐步混色补救；
 *    - ink 主题无彩色（brand-light 为浅灰），铃铛改用墨黑主色（Vercel 单色图标风格）；
 *    - tz_znx 在暗色主题下底色提亮至与卡片底 ≥2:1，前景保证与底色 ≥3:1；
 *    - tz_yx（邮件角标）走中性映射：主体 #EEEEEE≈neutral-30、描边 #5E5F5A=neutral-85（wise 精确命中），
 *      暗色主题自动反转为暗底亮描边。
 *
 * ⚠️ THEMES 表数值复制自 assets/styles/global.scss 各 [data-theme] 块，
 *    修改主题配色后须同步本表并重跑本脚本。
 */
const fs = require('fs')
const path = require('path')
const zlib = require('zlib')

const FRONTEND = path.resolve(__dirname, '..')
const SRC_DIR = path.join(FRONTEND, 'assets', 'images')
const OUT_ROOT = path.join(FRONTEND, 'static', 'theme-icons')

/* ---------- 主题 palette 摘录（与 global.scss 同步） ----------
 * card=--palette-neutral-0（卡片底）  pageBg=--palette-neutral-40（页面底）
 * n30=--palette-neutral-30  n85=--palette-neutral-85  n90=--palette-neutral-90
 * base/dark/darker/light=--palette-brand-*
 * selected=--palette-brand-selected  success=--palette-success
 */
const THEMES = {
  ink:      { card: '#ffffff', pageBg: '#fafafa', n30: '#f0f0f0', n85: '#737373', n90: '#4d4d4d', base: '#171717', dark: '#171717', darker: '#171717', light: '#f2f2f2', selected: '#dcdcdc', success: '#0070f3' },
  indigo:   { card: '#ffffff', pageBg: '#f6f9fc', n30: '#f0f2f5', n85: '#4a5568', n90: '#334155', base: '#533afd', dark: '#4326e0', darker: '#34209e', light: '#b9b9f9', selected: '#eef0fe', success: '#533afd' },
  lavender: { card: '#1c1d20', pageBg: '#010102', n30: '#23252a', n85: '#b4b6bc', n90: '#d8dade', base: '#5e6ad2', dark: '#5560c0', darker: '#4a55a8', light: '#828fff', selected: '#2a2d44', success: '#5e6ad2' },
  cyan:     { card: '#ffffff', pageBg: '#e9f4f6', n30: '#eef6f7', n85: '#3f7a82', n90: '#1f5b63', base: '#0891b2', dark: '#0e7490', darker: '#155e75', light: '#67d3ea', selected: '#e0f6fa', success: '#0891b2' },
  amber:    { card: '#ffffff', pageBg: '#fdf3e0', n30: '#fdf1df', n85: '#8a5e1e', n90: '#6b4715', base: '#f59e0b', dark: '#d97706', darker: '#b45309', light: '#fbbf24', selected: '#fdf2dc', success: '#f59e0b' },
  coral:    { card: '#ffffff', pageBg: '#fff1ef', n30: '#ffeeec', n85: '#a8453c', n90: '#8a352d', base: '#ff6b5e', dark: '#f0503f', darker: '#d83b2c', light: '#ff9b91', selected: '#ffe6e2', success: '#ff6b5e' },
  rose:     { card: '#ffffff', pageBg: '#fff1f6', n30: '#ffeef4', n85: '#a83d6c', n90: '#8c2f5a', base: '#e11d74', dark: '#be185d', darker: '#9d174d', light: '#f472b6', selected: '#fce2ee', success: '#e11d74' },
  crimson:  { card: '#341717', pageBg: '#1a0808', n30: '#3e1c1c', n85: '#f0c4c4', n90: '#f3d6d6', base: '#dc2626', dark: '#b91c1c', darker: '#991b1b', light: '#f87171', selected: '#3a1316', success: '#dc2626' },
  gold:     { card: '#322a12', pageBg: '#181307', n30: '#3c3315', n85: '#ecdc9e', n90: '#f0e6bf', base: '#c9a227', dark: '#a8841c', darker: '#8a6d16', light: '#e3c45c', selected: '#2a2410', success: '#c9a227' },
}

/* ---------- 参与换色的图标清单 ----------
 * anchors: [{ from: wise 原色, key: 目标 palette 键, bg: 落点背景(card|page), min: 最低对比度(0 表示不做对比度检查) }]
 * 特殊图标（bell/holes/znx）由 resolveAnchors 单独处理。
 */
const ICONS = [
  { file: 'dh_shouye_0.png', anchors: [{ from: '#454745', key: 'n90', bg: 'card', min: 3 }] },
  { file: 'dh_jilu_0.png', anchors: [{ from: '#454745', key: 'n90', bg: 'card', min: 3 }] },
  { file: 'dh_shezhi_0.png', anchors: [{ from: '#454745', key: 'n90', bg: 'card', min: 3 }] },
  { file: 'dh_shouye_1.png', anchors: [{ from: '#2f6c00', key: 'base', bg: 'card', min: 2.5 }] },
  { file: 'dh_jilu_1.png', anchors: [{ from: '#2f6c00', key: 'base', bg: 'card', min: 2.5 }] },
  { file: 'dh_shezhi_1.png', anchors: [{ from: '#2f6c00', key: 'base', bg: 'card', min: 2.5 }] },
  { file: 'fanhui.png', anchors: [{ from: '#2f6c00', key: 'base', bg: 'page', min: 2.5 }] },
  { file: 'jia_jihua.png', anchors: [{ from: '#2f6c00', key: 'base', bg: 'card', min: 2.5 }] },
  { file: 'jia_shijian.png', anchors: [{ from: '#2f6c00', key: 'base', bg: 'card', min: 2.5 }] },
  { file: 'jilu_xq.png', anchors: [{ from: '#2f6c00', key: 'base', bg: 'card', min: 2.5 }] },
  { file: 'jilu_wc.png', anchors: [{ from: '#2ead4b', key: 'success', bg: 'card', min: 2.5 }] },
  { file: 'dl_fingerprint.png', anchors: [{ from: '#154d31', key: 'dark', bg: 'page', min: 2.5 }] },
  { file: 'tongzhi_0.png', special: 'bell' },
  { file: 'tongzhi_1.png', special: 'bell+holes' },
  { file: 'tz_znx.png', special: 'znx' },
  { file: 'tz_yx.png', anchors: [
    // 信封主体≈neutral-30（表面色，不做对比度检查，与卡片底的微差与 wise 一致）；描边=neutral-85
    { from: '#eeeeee', key: 'n30', bg: 'card', min: 0 },
    { from: '#5e5f5a', key: 'n85', bg: 'card', min: 3 },
  ] },
]

const MATCH_DIST = 90 // 锚点匹配阈值（RGB 欧氏距离），覆盖抗锯齿边缘色偏

/* ---------- 色彩工具（WCAG） ---------- */
function hex2rgb(h) {
  const n = parseInt(h.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
function mix(h1, h2, t) {
  const a = hex2rgb(h1), b = hex2rgb(h2)
  return '#' + [0, 1, 2]
    .map(i => Math.round(Math.max(0, Math.min(255, a[i] + (b[i] - a[i]) * t))))
    .map(v => v.toString(16).padStart(2, '0'))
    .join('')
}
function luminance(hex) {
  const [r, g, b] = hex2rgb(hex).map(v => {
    v /= 255
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
function contrast(a, b) {
  const l1 = luminance(a), l2 = luminance(b)
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
}
function isDark(hex) {
  return luminance(hex) < 0.1
}
/** 对比度不足时向明度反方向逐步混色补救（暗底向白、亮底向黑） */
function enforceContrast(hex, bg, min, log, label) {
  if (contrast(hex, bg) >= min) return hex
  const target = isDark(bg) ? '#ffffff' : '#000000'
  for (let i = 1; i <= 19; i++) {
    const cand = mix(hex, target, i * 0.05)
    if (contrast(cand, bg) >= min) {
      log.push(`  [调整] ${label}: ${hex} → ${cand}（vs ${bg} 对比度 ${contrast(hex, bg).toFixed(2)} → ${contrast(cand, bg).toFixed(2)}）`)
      return cand
    }
  }
  log.push(`  [警告] ${label}: 无法满足对比度 ≥${min}，保持 ${hex}`)
  return hex
}

/* ---------- 每主题解析各图标最终锚点色 ---------- */
function resolveAnchors(name, themeKey, icon, log) {
  const t = THEMES[themeKey]

  // 铃铛（NoticeButton，落在页面底上）：wise 为高饱和浅绿，靠色相对比；ink 无彩色需换墨黑主色
  const resolveBell = () => {
    if (themeKey === 'ink') {
      log.push('  [调整] 铃铛: ink 无彩色主题，brand-light(#f2f2f2) 在 canvas 上不可见 → 改用墨黑主色 #171717')
      return t.base
    }
    // 候选从浅到深：浅色略降明度即可保住「亮色铃铛」的 wise 观感
    const cands = [t.light, mix(t.light, t.base, 0.3), mix(t.light, t.base, 0.6), t.base]
    for (const c of cands) {
      if (contrast(c, t.pageBg) >= 1.55) return c
    }
    return enforceContrast(t.base, t.pageBg, 1.55, log, '铃铛')
  }

  if (icon.special === 'bell') {
    return [{ from: '#9fe870', to: resolveBell() }]
  }
  if (icon.special === 'bell+holes') {
    return [
      { from: '#9fe870', to: resolveBell() },
      // E8EBE6 在 wise 中即页面底色（图标内「挖空」效果），各主题映射到各自页面底
      { from: '#e8ebe6', to: t.pageBg },
    ]
  }
  if (icon.special === 'znx') {
    // 底色：暗色主题下 brand-selected 与卡片底几乎同色，提亮至 ≥2:1 使底块成形
    let body = t.selected
    if (isDark(t.card) && contrast(body, t.card) < 2) {
      for (let i = 1; i <= 19; i++) {
        const c = mix(t.selected, '#ffffff', i * 0.05)
        if (contrast(c, t.card) >= 2) {
          log.push(`  [调整] 站内信底色: ${t.selected} → ${c}（vs 卡片底 ${t.card} 对比度 ${contrast(t.selected, t.card).toFixed(2)} → ${contrast(c, t.card).toFixed(2)}）`)
          body = c
          break
        }
      }
    }
    // 前景色：先取品牌色阶（亮色主题逐级加深 / 暗色主题转浅色），仍不足再向明度反方向补救
    let glyph = null
    const seq = isDark(t.card)
      ? [t.base, t.light]
      : [t.base, t.dark, t.darker]
    for (const c of seq) {
      if (contrast(c, body) >= 3) { glyph = c; break }
    }
    if (!glyph) {
      const start = isDark(t.card) ? t.light : t.darker
      glyph = start
      const target = isDark(t.card) ? '#ffffff' : '#000000'
      for (let i = 1; i <= 19; i++) {
        const c = mix(start, target, i * 0.05)
        if (contrast(c, body) >= 3) { glyph = c; break }
      }
      log.push(`  [调整] 站内信前景: 品牌色阶均不足 3:1 → ${glyph}（vs 底色 ${body} 对比度 ${contrast(glyph, body).toFixed(2)}）`)
    } else if (glyph !== t.base) {
      log.push(`  [调整] 站内信前景: base ${t.base} 与底色对比不足 → 品牌色阶改用 ${glyph}（对比度 ${contrast(glyph, body).toFixed(2)}）`)
    }
    return [
      { from: '#2f6c00', to: glyph },
      { from: '#e2f6d5', to: body },
    ]
  }

  // 常规锚点：直接取 palette 键值 + 对比度兜底
  return icon.anchors.map(an => {
    const bg = an.bg === 'card' ? t.card : t.pageBg
    const to = an.min > 0
      ? enforceContrast(t[an.key], bg, an.min, log, `${icon.file} ${an.key}`)
      : t[an.key]
    return { from: an.from, to }
  })
}

/* ---------- PNG 编解码（零依赖，支持 8bit 非隔行 colorType 0/2/3/4/6） ---------- */
function paeth(a, b, c) {
  const p = a + b - c
  const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c)
  return pa <= pb && pa <= pc ? a : pb <= pc ? b : c
}
function unfilter(type, line, prev, bpp, stride) {
  const out = Buffer.from(line)
  for (let i = 0; i < stride; i++) {
    const left = i >= bpp ? out[i - bpp] : 0
    const up = prev[i]
    const ul = i >= bpp ? prev[i - bpp] : 0
    if (type === 1) out[i] = (out[i] + left) & 255
    else if (type === 2) out[i] = (out[i] + up) & 255
    else if (type === 3) out[i] = (out[i] + ((left + up) >> 1)) & 255
    else if (type === 4) out[i] = (out[i] + paeth(left, up, ul)) & 255
  }
  return out
}
function decodePng(buf) {
  if (buf.readUInt32BE(0) !== 0x89504e47) throw new Error('非 PNG 文件')
  let off = 8
  let width, height, bitDepth, colorType, interlace
  let plte = null, trns = null
  const idat = []
  while (off < buf.length) {
    const len = buf.readUInt32BE(off)
    const type = buf.toString('ascii', off + 4, off + 8)
    const data = buf.subarray(off + 8, off + 8 + len)
    if (type === 'IHDR') {
      width = data.readUInt32BE(0)
      height = data.readUInt32BE(4)
      bitDepth = data[8]
      colorType = data[9]
      interlace = data[12]
    } else if (type === 'PLTE') plte = data
    else if (type === 'tRNS') trns = data
    else if (type === 'IDAT') idat.push(data)
    else if (type === 'IEND') break
    off += 12 + len
  }
  if (bitDepth !== 8) throw new Error(`仅支持 8 位色深（实际 ${bitDepth}）`)
  if (interlace) throw new Error('不支持隔行 PNG')
  const channels = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 }[colorType]
  const stride = width * channels
  const raw = zlib.inflateSync(Buffer.concat(idat))
  const out = Buffer.alloc(width * height * 4)
  let prev = Buffer.alloc(stride)
  for (let y = 0; y < height; y++) {
    const filterType = raw[y * (stride + 1)]
    const line = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1))
    const cur = unfilter(filterType, line, prev, channels, stride)
    for (let x = 0; x < width; x++) {
      let r = 0, g = 0, b = 0, al = 255
      if (colorType === 6) { r = cur[x * 4]; g = cur[x * 4 + 1]; b = cur[x * 4 + 2]; al = cur[x * 4 + 3] }
      else if (colorType === 2) { r = cur[x * 3]; g = cur[x * 3 + 1]; b = cur[x * 3 + 2] }
      else if (colorType === 4) { r = g = b = cur[x * 2]; al = cur[x * 2 + 1] }
      else if (colorType === 0) { r = g = b = cur[x] }
      else if (colorType === 3) {
        const idx = cur[x]
        r = plte[idx * 3]; g = plte[idx * 3 + 1]; b = plte[idx * 3 + 2]
        al = trns ? trns[idx] : 255
      }
      const o = (y * width + x) * 4
      out[o] = r; out[o + 1] = g; out[o + 2] = b; out[o + 3] = al
    }
    prev = cur
  }
  return { width, height, data: out }
}

const CRC_TABLE = (() => {
  const t = new Int32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    t[n] = c
  }
  return t
})()
function crc32(buf) {
  let c = -1
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 255] ^ (c >>> 8)
  return (c ^ -1) >>> 0
}
function chunk(type, data) {
  const len = Buffer.alloc(4)
  len.writeUInt32BE(data.length)
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data])
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(body))
  return Buffer.concat([len, body, crc])
}
function encodePng(img) {
  const stride = img.width * 4
  const raw = Buffer.alloc((stride + 1) * img.height)
  for (let y = 0; y < img.height; y++) {
    raw[y * (stride + 1)] = 0 // filter: None
    img.data.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride)
  }
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(img.width, 0)
  ihdr.writeUInt32BE(img.height, 4)
  ihdr[8] = 8; ihdr[9] = 6 // 8bit RGBA
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ])
}

/* ---------- 逐像素换色 ---------- */
function recolor(img, anchors) {
  const d = img.data
  const targets = anchors.map(a => ({ from: hex2rgb(a.from), to: hex2rgb(a.to) }))
  let mapped = 0, opaque = 0
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] < 8) continue
    opaque++
    let best = -1, bestDist = MATCH_DIST * MATCH_DIST
    for (let k = 0; k < targets.length; k++) {
      const f = targets[k].from
      const dd = (d[i] - f[0]) ** 2 + (d[i + 1] - f[1]) ** 2 + (d[i + 2] - f[2]) ** 2
      if (dd < bestDist) { bestDist = dd; best = k }
    }
    if (best >= 0) {
      const to = targets[best].to
      d[i] = to[0]; d[i + 1] = to[1]; d[i + 2] = to[2]
      mapped++
    }
  }
  return { mapped, opaque }
}

/* ---------- 主流程 ---------- */
function main() {
  // 清空输出目录，避免残留旧文件
  fs.rmSync(OUT_ROOT, { recursive: true, force: true })

  // 源图只解码一次
  const srcCache = new Map()
  const loadSrc = file => {
    if (!srcCache.has(file)) {
      const p = path.join(SRC_DIR, file)
      if (!fs.existsSync(p)) throw new Error(`源图不存在: ${p}`)
      srcCache.set(file, decodePng(fs.readFileSync(p)))
    }
    return srcCache.get(file)
  }

  let totalFiles = 0, totalBytes = 0
  for (const themeKey of Object.keys(THEMES)) {
    const log = []
    const dir = path.join(OUT_ROOT, themeKey)
    fs.mkdirSync(dir, { recursive: true })
    for (const icon of ICONS) {
      const img = { width: 0, height: 0, data: Buffer.from(loadSrc(icon.file).data) }
      img.width = loadSrc(icon.file).width
      img.height = loadSrc(icon.file).height
      const anchors = resolveAnchors(icon.file, themeKey, icon, log)
      const { mapped, opaque } = recolor(img, anchors)
      const buf = encodePng(img)
      fs.writeFileSync(path.join(dir, icon.file), buf)
      totalFiles++
      totalBytes += buf.length
      // 换色覆盖率异常提醒（多数像素未命中说明源图色彩构成变化，需人工检查映射表）
      const ratio = mapped / Math.max(1, opaque)
      if (ratio < 0.6 && icon.special !== 'bell+holes') {
        log.push(`  [警告] ${icon.file}: 仅 ${Math.round(ratio * 100)}% 不透明像素被换色，请核对锚点色`)
      }
    }
    console.log(`\n=== ${themeKey} ===`)
    if (log.length) console.log(log.join('\n'))
    else console.log('  （全部按 palette 键直接映射，无需调整）')
  }
  console.log(`\n完成：${totalFiles} 个文件，共 ${(totalBytes / 1024).toFixed(1)} KB → ${path.relative(FRONTEND, OUT_ROOT)}`)
}

main()
