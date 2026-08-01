import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// 工程已改为 HBuilderX 标准布局（源码位于项目根目录，无 src 层），
// CLI 构建与 HBuilderX「运行/发行」共用同一套目录结构。
export default defineConfig(({ mode }) => {
  // 仅 H5 构建将 public/ 下的静态文件（robots.txt、sitemap.xml）复制到产物根目录，
  // 供搜索引擎与 sitemap 抓取；小程序（mp-weixin）构建不设置 publicDir，完全不受影响。
  const isH5 = process.env.UNI_PLATFORM === 'h5'
  return {
    plugins: [uni()],
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
