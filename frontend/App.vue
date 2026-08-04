<script>
	import { useUserStore } from './store/modules/user'
	import { useAppPush } from './composables/useAppPush'
	import { useTokenRefresh } from './composables/useTokenRefresh'
	export default {
		onLaunch: function() {
			// App 端：先初始化友盟推送 SDK，再注册通知栏点击跳转监听
			// #ifdef APP-PLUS
			const appPush = useAppPush()
			appPush.registerPushClick()
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

<style lang="scss">
/* ===== 单位转换说明（px → rpx）=====
 * 设计稿基准 375px 宽，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * App.vue 仅全局引入 global.scss，自身无尺寸样式，故无 rpx 转换内容与断点锁定。
 * 全局 CSS 变量的转换在 global.scss 中完成，具体尺寸的宽屏断点锁定由各页面/组件级样式处理。
 */
@import './assets/styles/global.scss';
</style>
