/**
 * uni-app CLI 启动包装脚本
 * --------------------------------------------------------------------------
 * 背景：
 *   工程已改为 HBuilderX 标准布局（源码直接位于 frontend/ 根目录，无 src 层），
 *   以便使用 HBuilderX 发行 App / iOS / 多端小程序。
 *   而 uni-app CLI 默认把输入目录写死为 <项目根>/src（见 vite-plugin-uni 的
 *   cli/build.js: `const inputDir = process.env.UNI_INPUT_DIR`，未设置时由 CLI
 *   默认填充为 src），会导致 CLI 构建报 "ENOENT: ... src/manifest.json"。
 *
 * 作用：
 *   在调用 uni CLI 前把 UNI_INPUT_DIR 指向项目根目录，使 CLI 与 HBuilderX
 *   共用同一套目录结构，两种构建方式并存。
 *
 * 用法（由 package.json scripts 调用）：
 *   node scripts/run-uni.js <dev|build> <platform>
 *   例：node scripts/run-uni.js build mp-weixin
 *
 * 跨平台：使用 Node 设置环境变量，避免引入 cross-env 依赖，Windows/Linux 通用。
 */
const { spawn } = require('node:child_process')
const path = require('node:path')

const [, , mode, platform] = process.argv

if (!mode || !platform) {
  console.error('用法: node scripts/run-uni.js <dev|build> <platform>')
  process.exit(1)
}

if (mode !== 'dev' && mode !== 'build') {
  console.error(`不支持的模式: ${mode}（仅支持 dev 或 build）`)
  process.exit(1)
}

// 项目根目录即源码目录（HBuilderX 布局）
const projectRoot = path.resolve(__dirname, '..')

// uni CLI 参数：dev 模式无子命令，build 模式为 `build`
const args = mode === 'build' ? ['uni', 'build', '-p', platform] : ['uni', '-p', platform]

const child = spawn('npx', args, {
  cwd: projectRoot,
  stdio: 'inherit',
  shell: true,
  env: {
    ...process.env,
    UNI_INPUT_DIR: projectRoot,
  },
})

child.on('exit', (code) => process.exit(code ?? 0))
