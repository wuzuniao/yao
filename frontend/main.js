import App from './App.vue'

// #ifndef VUE3
import Vue from 'vue'
Vue.config.productionTip = false
App.mpType = 'app'
const app = new Vue({
  ...App
})
app.$mount()
// #endif

// #ifdef VUE3
import { createSSRApp } from 'vue'
import pinia from './store'
import { useThemeStore } from './store/modules/theme'

// 主题同步 mixin：为所有组件提供响应式 themeKey（= themeStore.current）。
// 页面根 view 绑 :data-theme="themeKey" 即可全端换肤。
// 必要性：小程序端 App.vue 的 template 不会渲染进页面，[data-theme] 选择器无元素匹配，
// 故需在每个页面根 view 绑定 data-theme；本 mixin 自动提供响应式 themeKey，页面无需重复 import。
const themeMixin = {
  computed: {
    themeKey() {
      return useThemeStore().current
    }
  }
}

export function createApp() {
  const app = createSSRApp(App)
  app.use(pinia)
  app.mixin(themeMixin)
  return {
    app
  }
}
// #endif