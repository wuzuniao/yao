const fs = require('fs')
const path = require('path')

const chinese = /[一-鿿]/
// 仅扫描 .vue 的 <template> 区域里、作为可见文本节点、且未走 $t 的中文
const files = []
function walk(d) {
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f)
    const s = fs.statSync(p)
    if (s.isDirectory()) {
      if (['node_modules', 'unpackage', 'dist', '.git', 'static', 'public'].includes(f)) continue
      walk(p)
    } else if (f.endsWith('.vue')) {
      files.push(p)
    }
  }
}
walk('frontend')

// 提取 template 段
function extractTemplate(src) {
  const m = src.match(/<template>([\s\S]*?)<\/template>/)
  return m ? m[1] : ''
}

let hits = 0
const out = []
for (const fp of files) {
  const src = fs.readFileSync(fp, 'utf8')
  const tpl = extractTemplate(src)
  const lines = tpl.split('\n')
  // 跟踪跨行 HTML 注释状态（<!-- ... --> 可折行书写），注释内的行不算裸文本
  let inComment = false
  lines.forEach((line, i) => {
    if (inComment) {
      if (line.includes('-->')) inComment = false
      return
    }
    const openIdx = line.indexOf('<!--')
    if (openIdx !== -1) {
      const closeIdx = line.indexOf('-->', openIdx)
      if (closeIdx === -1) { inComment = true; return } // 注释跨行，后续行跳过
      line = line.slice(closeIdx + 3)                    // 同行闭合，仅检查注释外剩余部分
      if (!line.trim()) return
    }
    if (!chinese.test(line)) return
    if (/\$t\(/.test(line)) return            // 已走 i18n
    // 仅保留"文本节点"：行内含 '>' 后接中文 或 中文后接 '<'，即标签之间的裸文本
    const bare = line.replace(/<[^>]+>/g, '')
    if (!chinese.test(bare)) return
    out.push(fp.replace('frontend/', '') + ' L' + (i + 1) + ': ' + bare.trim().slice(0, 80))
    hits++
  })
}
console.log(out.join('\n'))
console.log('\n=== template 裸文本节点疑似硬编码中文(排除 $t 与注释): ' + hits)
