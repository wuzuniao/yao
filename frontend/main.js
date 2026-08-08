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
import { useLanguageStore } from './store/modules/language'
import { t } from './locale'

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

// 国际化 mixin：为所有组件提供 $t（翻译函数）与 langKey（当前语言）。
// 必要性与 themeMixin 同理——小程序端 App.vue 的 template 不渲染进页面，且各页面独立编译，
// 通过全局 mixin 注入可让 14 个页面与 7 个组件的模板直接使用 $t(...)，无需逐个 import。
// 响应式关键：$t 声明为 computed，其内部读取 languageStore.current 建立依赖，
// 语言切换时该 computed 失效并重算，返回新的翻译函数引用，
// 从而使模板中所有 $t(...) 调用重新求值，实现全站即时切换（无需刷新页面）。
const langMixin = {
  computed: {
    langKey() {
      return useLanguageStore().current
    },
    $t() {
      const locale = useLanguageStore().current
      return (key, params) => t(key, params, locale)
    }
  }
}

export function createApp() {
  const app = createSSRApp(App)
  app.use(pinia)
  app.mixin(themeMixin)
  app.mixin(langMixin)
  return {
    app
  }
}
// #endif