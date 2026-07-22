<template>
  <!-- 密码显隐眼睛图标（纯 CSS 绘制，不依赖任何图片资源） -->
  <view class="pwd-eye">
    <!-- 睁眼：完整眼形轮廓 + 瞳孔（密码明文可见） -->
    <view v-if="visible" class="pwd-eye__open">
      <view class="pwd-eye__pupil"></view>
    </view>
    <!-- 闭眼：向下弯曲的闭合弧线（密码隐藏） -->
    <view v-else class="pwd-eye__closed"></view>
  </view>
</template>

<script setup>
/**
 * PasswordEye.vue —— 密码显隐切换眼睛图标（纯展示组件）
 * --------------------------------------------------------------------------
 * 纯 CSS 绘制，替代原 mima_1.png 图片资源，兼容微信小程序（不支持内联 SVG）。
 * 两种状态视觉差异明显，便于用户识别当前密码是否明文：
 *  - visible=false（默认）：闭眼（向下弯曲的闭合弧线），表示密码已隐藏
 *  - visible=true：睁眼（完整眼形 + 瞳孔），表示密码明文可见
 * 点击切换由父组件（包裹本组件的眼睛容器）处理，本组件仅负责绘制。
 */
defineProps({
  visible: { type: Boolean, default: false }
})
</script>

<style lang="scss">
.pwd-eye {
  position: relative;
  width: 48rpx;
  height: 32rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* ===== 睁眼：上平下圆的眼形轮廓 + 中心瞳孔 ===== */
.pwd-eye__open {
  width: 44rpx;
  height: 28rpx;
  border: 3rpx solid #454745;
  border-radius: 50% / 58% 58% 42% 42%;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 瞳孔：实心圆点 */
.pwd-eye__pupil {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #454745;
}

/* ===== 闭眼：向下弯曲的闭合弧线（仅下边框 + 下圆角）
   垂直半径用 70%（非 100%），让弧线更平缓、弧度更小，左右对称 */
.pwd-eye__closed {
  width: 44rpx;
  height: 22rpx;
  border: 3rpx solid #454745;
  border-top: none;
  border-radius: 0 0 50% 50% / 0 0 70% 70%;
  box-sizing: border-box;
}

/* 平板/折叠屏断点（≥768px）：锁定关键尺寸为 px，避免 rpx 过度放大 */
@media screen and (min-width: 768px) {
  .pwd-eye {
    width: 24px;
    height: 16px;
  }

  .pwd-eye__open {
    width: 22px;
    height: 14px;
    border-width: 1.5px;
  }

  .pwd-eye__pupil {
    width: 7px;
    height: 7px;
  }

  .pwd-eye__closed {
    width: 22px;
    height: 11px;
    border-width: 1.5px;
  }
}
</style>
