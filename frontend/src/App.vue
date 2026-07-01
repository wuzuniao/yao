<script>
	import { useUserStore } from './store/modules/user'
	export default {
		onLaunch: function() {},
		onShow: function() {
			// 应用回到前台时，若账号处于待删除状态，验证账号是否已被后端删除
			const userStore = useUserStore()
			if (userStore.userInfo && userStore.userInfo.status === 0) {
				userStore.verifyUserExists()
			}
		},
		onHide: function() {}
	}
</script>

<style lang="scss">
@import './assets/styles/global.scss';
</style>
