<!--
  PageHeader —— 页面标题区复用组件
  ==========================================================================
  适用场景：plan.vue / notification.vue / profile.vue / help.vue / contact.vue
    共 5 个页面的标题区结构完全一致（标题 + 副标题/描述），仅文案不同。

  视觉规范（对照 Figma 设计稿）：
    - 标题：32px / 行高 36px / 600 / #0e0f0c
    - 副标题：16px / 行高 24px / 400 / #454745 / 自动换行（容器边界换行）
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
 * @prop {string} desc - 页面副标题/描述（可选，自动换行）
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
/* ===== 单位转换说明（px → rpx）=====
 * 设计稿基准 375px 宽，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * 已转换属性：padding/gap/font-size/line-height 等
 * 保留 px 的情况：本文件无 1px 边框 / box-shadow / 9999px / 百分比等需保留项
 */
/* 标题区容器：左侧留 8px 内边距与页面边缘对齐，flex column 排列标题与描述 */
.page-header {
  padding: 0 16rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.page-header__title {
  color: var(--color-text-primary);
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
}

.page-header__desc {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  /* 默认 normal：文本根据容器边界自动换行 */
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为原 px 值
 */
@media screen and (min-width: 768px) {
  .page-header {
    padding: 0 8px;
    gap: 8px;
  }
  .page-header__title {
    font-size: 32px;
    line-height: 36px;
  }
  .page-header__desc {
    font-size: 16px;
    line-height: 24px;
  }
}
</style>
