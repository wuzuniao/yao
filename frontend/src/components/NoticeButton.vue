<template>
  <view class="notice-button" @click="handleClick">
    <image class="notice-button__icon" :src="iconSrc" mode="aspectFit" />
  </view>
</template>

<script setup>
import { computed } from 'vue'
import noticeInactiveIcon from '../assets/images/tongzhi_0.png'
import noticeActiveIcon from '../assets/images/tongzhi_1.png'

const props = defineProps({
  hasNotification: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const iconSrc = computed(() => {
  return props.hasNotification ? noticeActiveIcon : noticeInactiveIcon
})

function handleClick() {
  emit('click')
}
</script>

<style lang="scss" scoped>
.notice-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notice-button__icon {
  width: 40px;
  height: 40px;
  display: block;
}
</style>