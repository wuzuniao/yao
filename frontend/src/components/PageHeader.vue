<!--
  PageHeader —— 页面标题区复用组件
  ==========================================================================
  适用场景：plan.vue / notification.vue / profile.vue / help.vue / contact.vue
    共 5 个页面的标题区结构完全一致（标题 + 副标题/描述），仅文案不同。

  视觉规范（对照 Figma 设计稿）：
    - 标题：32px / 行高 36px / 600 / #0e0f0c
    - 副标题：16px / 行高 24px / 400 / #454745 / white-space: pre-line（支持 \n 换行）
    - 容器：padding 0 8px，flex column，gap 8px

  参考：
    - Vue 3 组件基础：https://cn.vuejs.org/guide/essentials/component-basics.html
    - uni-app 组件：https://uniapp.dcloud.net.cn/component/

  使用示例：
    <PageHeader title="制定计划" desc="合理规划您的用药..." />
-->
<template>
  <view class="page-header">
    <text class="page-header__title">{{ title }}</text>
    <text v-if="desc" class="page-header__desc">{{ desc }}</text>
  </view>
</template>

<script setup>
/**
 * Props
 * @prop {string} title - 页面主标题（必填）
 * @prop {string} desc - 页面副标题/描述（可选，支持 \n 换行）
 */
defineProps({
  title: {
    type: String,
    required: true
  },
  desc: {
    type: String,
    default: ''
  }
})
</script>

<style lang="scss">
/* 标题区容器：左侧留 8px 内边距与页面边缘对齐，flex column 排列标题与描述 */
.page-header {
  padding: 0 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-header__title {
  color: var(--color-text-primary);
  font-size: 32px;
  line-height: 36px;
  font-weight: 600;
}

.page-header__desc {
  color: var(--color-text-secondary);
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
  /* pre-line：保留文本中的 \n 换行，合并多余空白，符合设计稿多行描述排版 */
  white-space: pre-line;
}
</style>
