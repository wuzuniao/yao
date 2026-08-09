import { fileURLToPath, URL } from 'node:url'
import { rmSync, existsSync } from 'node:fs'
import { pathToFileURL } from 'node:url'

import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// 工程已改为 HBuilderX 标准布局（源码位于项目根目录，无 src 层），
// CLI 构建与 HBuilderX「运行/发行」共用同一套目录结构。

// 小程序端（mp-weixin）不需要 App 原生图标，但 uni 编译器会把 app-plus.icons
// 对应的聚合资源 static/app-icons/app-icons.png（约 357KB）一并打进产物，
// 既撑大小程序主包，又触发微信「图片资源应不超过 200k」的代码质量告警。
// 该资源小程序端从不引用，故在打包完成后清理掉。
function removeAppIconsForMpWeixin() {
  return {
    name: 'remove-app-icons-mp-weixin',
    apply: () => process.env.UNI_PLATFORM === 'mp-weixin',
    closeBundle() {
      const outDir = process.env.UNI_OUTPUT_DIR
      if (!outDir) return
      const target = fileURLToPath(pathToFileURL(outDir + '/static/app-icons'))
      if (existsSync(target)) {
        rmSync(target, { recursive: true, force: true })
      }
    },
  }
}

export default defineConfig(({ mode }) => {
  // 仅 H5 构建将 public/ 下的静态文件（robots.txt、sitemap.xml）复制到产物根目录，
  // 供搜索引擎与 sitemap 抓取；小程序（mp-weixin）构建不设置 publicDir，完全不受影响。
  const isH5 = process.env.UNI_PLATFORM === 'h5'
  return {
    plugins: [uni(), removeAppIconsForMpWeixin()],
    root: '.',
    ...(isH5 ? { publicDir: 'public' } : {}),
    resolve: {
      alias: {
        // 指向项目根目录（即源码目录），供 `@/utils/xxx` 等导入使用
        '@': fileURLToPath(new URL('.', import.meta.url)),
      },
    },
  }
})
