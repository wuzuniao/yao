import { fileURLToPath, URL } from 'node:url'
import { rmSync, existsSync } from 'node:fs'
import { pathToFileURL } from 'node:url'

import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// 工程已改为 HBuilderX 标准布局（源码位于项目根目录，无 src 层），
// CLI 构建与 HBuilderX「运行/发行」共用同一套目录结构。

// 小程序端（mp-weixin）不需要的静态资源，打包完成后从产物清理：
// 1. App 原生图标 static/app-icons/（约 357KB）：uni 编译器把 app-plus.icons
//    对应的聚合资源一并打进产物，既撑大小程序主包，又触发微信「图片资源应不超过
//    200k」的代码质量告警。该资源小程序端从不引用。
// 2. 分享封面图 static/share-cover.png（约 16KB）：各端分享统一引用其 https
//    网络地址（config/env.js 的 SHARE_COVER_URL，由 H5 站点托管），小程序包内
//    无引用，排除以避免撑大主包。
// 两者均单份存放在 frontend/static/（App/H5 端构建随 static 目录正常拷贝），
// 仅小程序构建产物中被清理。
function removeUnusedAssetsForMpWeixin() {
  return {
    name: 'remove-unused-assets-mp-weixin',
    apply: () => process.env.UNI_PLATFORM === 'mp-weixin',
    closeBundle() {
      const outDir = process.env.UNI_OUTPUT_DIR
      if (!outDir) return
      for (const rel of ['static/app-icons', 'static/share-cover.png']) {
        const target = fileURLToPath(pathToFileURL(outDir + '/' + rel))
        if (existsSync(target)) {
          rmSync(target, { recursive: true, force: true })
        }
      }
    },
  }
}

export default defineConfig(({ mode }) => {
  // 仅 H5 构建将 public/ 下的静态文件（robots.txt、sitemap.xml）复制到产物根目录，
  // 供搜索引擎与 sitemap 抓取；小程序（mp-weixin）构建不设置 publicDir，完全不受影响。
  const isH5 = process.env.UNI_PLATFORM === 'h5'
  return {
    plugins: [uni(), removeUnusedAssetsForMpWeixin()],
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
