<script>
	import { useUserStore } from './store/modules/user'
	import { useAppPush } from './composables/useAppPush'
	import { useTokenRefresh } from './composables/useTokenRefresh'
	import { useThemeStore } from './store/modules/theme'
	export default {
		// 在 setup 中暴露主题 store，使根节点可绑定 :data-theme 实现全站换肤
		setup() {
			const themeStore = useThemeStore()
			return { themeStore }
		},
		onLaunch: function() {
			// App 端：注册通知栏点击跳转监听并初始化友盟推送 SDK
			// 隐私合规：原生隐私弹窗（app-plus.privacy=template）会在用户同意前
			// 自动拦截三方 SDK 的设备信息采集；此处进一步将 SDK 初始化推迟到
			// 用户点击「同意」之后，避免在隐私同意前采集设备标识（Device Token）。
			// #ifdef APP-PLUS
			const appPush = useAppPush()
			if (typeof uni.onAgreePrivacy === 'function') {
				// 监听隐私同意事件，同意后再初始化推送（未同意则不上报设备信息）
				uni.onAgreePrivacy(() => {
					appPush.registerPushClick()
				})
			} else {
				appPush.registerPushClick()
			}
			// #endif
		},
		onShow: function() {
			// 应用回到前台时，若账号处于待删除状态，验证账号是否已被后端删除
			const userStore = useUserStore()
			if (userStore.userInfo && userStore.userInfo.status === 0) {
				userStore.verifyUserExists()
			}
			// 已登录态临近过期时静默续期（多端一致，不跳页）
			useTokenRefresh().tryRefresh()
		},
		onHide: function() {}
	}
</script>

<template>
	<!-- 应用根容器：挂载 data-theme 使 global.scss 的配色方案覆盖全站 CSS 变量
	     （小程序端 page 自身亦匹配 page[data-theme]，App 端由本根 view 命中 [data-theme]） -->
	<view class="app-root" :data-theme="themeStore.current">
		<router-view />
	</view>
</template>

<style lang="scss">
/* ===== 单位转换说明（px → rpx）=====
 * 设计稿基准 375px 宽，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * App.vue 仅全局引入 global.scss，自身无尺寸样式，故无 rpx 转换内容与断点锁定。
 * 全局 CSS 变量的转换在 global.scss 中完成，具体尺寸的宽屏断点锁定由各页面/组件级样式处理。
 */
.app-root {
	min-height: 100vh;
	width: 100%;
	/* 承载主题背景：自身带 data-theme，故 var(--page-bg-color) 解析为当前方案色，
	   避免 App/H5 端 page 根（默认绿主题令牌）透出绿底与墨黑主题内容冲突 */
	background-color: var(--page-bg-color);
}

@import './assets/styles/global.scss';
</style>
