import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// 工程已改为 HBuilderX 标准布局（源码位于项目根目录，无 src 层），
// CLI 构建与 HBuilderX「运行/发行」共用同一套目录结构。
export default defineConfig({
  plugins: [uni()],
  root: '.',
  resolve: {
    alias: {
      // 指向项目根目录（即源码目录），供 `@/utils/xxx` 等导入使用
      '@': fileURLToPath(new URL('.', import.meta.url)),
    },
  },
})
