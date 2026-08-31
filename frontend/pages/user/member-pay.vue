<template>
  <view :data-theme="themeKey" class="pay-page">
    <!-- 返回按钮：定位规则与 BackButton 组件一致；图标为 fanhui.png 保形换色浅色版，适配固定近黑背景 -->
    <view class="pay-page__back" :style="{ top: backTop }" @click="goBack">
      <image class="pay-page__back-icon" :src="fanhuiLight" mode="aspectFit" />
    </view>

    <!-- 主内容：标题区 / 权益卡 / 价格区（垂直居中于剩余空间） -->
    <view class="pay-page__main">
      <view class="pay-page__heading">
        <text class="pay-page__title">{{ $t('pay.title') }}</text>
        <text class="pay-page__subtitle">{{ $t('pay.subtitle') }}</text>
      </view>

      <view class="pay-page__perks">
        <view class="pay-page__perk">
          <text class="pay-page__perk-title">{{ $t('pay.perk1Title') }}</text>
          <text class="pay-page__perk-text">{{ $t('pay.perk1Text') }}</text>
        </view>
        <view class="pay-page__perk">
          <text class="pay-page__perk-title">{{ $t('pay.perk2Title') }}</text>
          <text class="pay-page__perk-text">{{ $t('pay.perk2Text') }}</text>
        </view>
      </view>

      <view class="pay-page__pricing">
        <view class="pay-page__price-row">
          <text class="pay-page__price">{{ $t('pay.price') }}</text>
          <text class="pay-page__price-unit">{{ $t('pay.priceUnit') }}</text>
        </view>
        <view class="pay-page__price-meta">
          <text class="pay-page__price-origin">{{ $t('pay.priceOrigin') }}</text>
          <view class="pay-page__pill">
            <text class="pay-page__pill-text">{{ $t('pay.pill') }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部操作区（含 iOS 安全区适配）；仅前端展示，未接入支付逻辑 -->
    <view class="pay-page__action">
      <view class="pay-page__btn" hover-class="pay-page__btn--hover" :hover-stay-time="70">
        <text class="pay-page__btn-text">{{ $t('pay.subscribe') }}</text>
      </view>
      <text class="pay-page__safe-tip">{{ $t('pay.safeTip') }}</text>
    </view>
  </view>
</template>

<script setup>
/**
 * 会员支付页（member-pay.vue）
 * --------------------------------------------------------------------------
 * 功能：Pro 会员订阅支付页（设计稿：科技深色转化版，Figma node 3-88）
 *  - 纯前端静态展示：权益卡、价格与限时胶囊、订阅按钮（未接入任何支付后端逻辑）
 *  - 入口：设置页会员卡片「立即抢购」按钮（settings.vue goMemberPay）；
 *    会员卡片仅「谷歌商店（Android google 渠道包）/鸿蒙商店」分发渠道显示，
 *    小程序/H5/其他安卓商店/iOS 端无此入口
 *  - 固定深色皮肤：页面颜色全部引用 --color-pay-* 语义令牌，不随主题换肤
 *  - 返回按钮：页面为固定近黑背景、fanhui.png 深绿图标不可辨，使用其保形换色浅色版
 *    fanhui_light.png（#acf67c），定位规则（状态栏高度驱动）与 BackButton 组件保持一致
 */
import { computed } from 'vue'
import { useShare } from '../../composables/useShare'
import { t } from '../../locale'
import fanhuiLight from '../../assets/images/fanhui_light.png'

useShare({ title: t('share.memberPay') })

// 返回按钮 top：与 BackButton 组件一致的定位规则（状态栏高度 - 5px + 0.6vh）
const backTop = computed(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    const statusBarHeight = sysInfo.statusBarHeight || 44
    return `calc(${statusBarHeight - 5}px + 0.6vh)`
  } catch (e) {
    return 'calc(45px + 0.6vh)'
  }
})

// 返回上一页：页面栈为空（如分享直达）时回退首页（与 BackButton 行为一致）
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack({ delta: 1 })
  } else {
    uni.reLaunch({ url: '/pages/index/index' })
  }
}
</script>

<style lang="scss">
/* ==========================================================================
 * 响应式单位说明（px → rpx 转换）
 * --------------------------------------------------------------------------
 * 基准：375px 设计稿，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * 转 rpx：width/height/padding/margin/gap/font-size/line-height/border-radius
 * 保留 px：box-shadow 偏移/模糊、border 1px 级描边、calc 中的状态栏/安全区高度
 * 平板/折叠屏断点：≥768px 锁定关键尺寸为 px，避免 rpx 过度放大
 * ========================================================================== */
.pay-page {
  min-height: 100vh;
  box-sizing: border-box;
  background: var(--color-pay-bg);
  display: flex;
  flex-direction: column;
}

/* ===== 返回按钮 ===== */
.pay-page__back {
  position: absolute;
  left: 48rpx;
  z-index: 10;
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 浅色返回图标（尺寸与 BackButton 组件图标一致） */
.pay-page__back-icon {
  width: 80rpx;
  height: 80rpx;
  display: block;
}

/* ===== 主内容 ===== */
.pay-page__main {
  flex: 1;
  box-sizing: border-box;
  /* padding-top 180rpx：返回按钮 top约39px + 高40px = 底部约79px，留约11px 间隙（对齐其他子页
     canvas 210rpx 的避让惯例）；底部与区块间距适度收紧，使整页在常规机型（812px 视口）内
     恰好一屏不出现滚动条，同时保持留白不过度紧凑 */
  padding: 180rpx 48rpx 48rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 48rpx;
}

/* 标题区：大标题 + 副标题（底距与区块 gap 合计 48px，兼顾一屏高度） */
.pay-page__heading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
  padding-bottom: 48rpx;
}

.pay-page__title {
  color: var(--color-pay-title);
  font-size: 96rpx;
  line-height: 104rpx;
  font-weight: 700;
  text-align: center;
}

.pay-page__subtitle {
  color: var(--color-pay-text);
  font-size: 40rpx;
  line-height: 60rpx;
  font-weight: 400;
  text-align: center;
}

/* ===== 权益卡 ===== */
.pay-page__perks {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.pay-page__perk {
  box-sizing: border-box;
  padding: 32rpx;
  border-radius: 24rpx;
  background: var(--color-pay-card);
  box-shadow: inset 0 0 0 1px var(--color-pay-card-border);
  display: flex;
  flex-direction: column;
}

.pay-page__perk-title {
  color: var(--color-pay-accent);
  font-size: 40rpx;
  line-height: 64rpx;
  font-weight: 600;
  padding-bottom: 8rpx;
}

.pay-page__perk-text {
  color: var(--color-pay-text);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
}

/* ===== 价格区 ===== */
.pay-page__pricing {
  padding: 32rpx 0;
  display: flex;
  flex-direction: column;
}

.pay-page__price-row {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: flex-end;
  gap: 16rpx;
}

.pay-page__price {
  color: var(--color-pay-accent);
  font-size: 128rpx;
  line-height: 128rpx;
  font-weight: 700;
}

.pay-page__price-unit {
  color: var(--color-pay-text);
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 400;
  padding-bottom: 4rpx;
}

/* 价格下行：原价（删除线）+ 限时胶囊 */
.pay-page__price-meta {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 16rpx;
  padding-top: 16rpx;
}

.pay-page__price-origin {
  color: var(--color-pay-muted);
  font-size: 28rpx;
  line-height: 28rpx;
  font-weight: 400;
  text-decoration: line-through;
}

.pay-page__pill {
  height: 56rpx;
  box-sizing: border-box;
  padding: 0 24rpx;
  border-radius: 9999px;
  background: var(--color-pay-pill);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pay-page__pill-text {
  color: var(--color-pay-accent);
  font-size: 26rpx;
  line-height: 32rpx;
  font-weight: 400;
}

/* ===== 底部操作区（含 iOS 安全区适配；底距仅保留小间距 + 系统安全区） ===== */
.pay-page__action {
  padding: 32rpx 48rpx;
  padding-bottom: calc(24rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.pay-page__btn {
  height: 128rpx;
  border-radius: 24rpx;
  background: var(--color-pay-accent);
  box-shadow: 0 0 40px -10px var(--color-pay-glow);
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s ease-in-out, transform 0.1s ease-in-out;
}

/* 按压态（hover-class）：对应设计稿 hover opacity 0.8 / click scale 0.95 */
.pay-page__btn--hover {
  opacity: 0.8;
  transform: scale(0.95);
}

.pay-page__btn-text {
  color: var(--color-pay-accent-text);
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 400;
}

.pay-page__safe-tip {
  color: var(--color-pay-muted);
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 400;
  text-align: center;
}

/* ===== 平板/折叠屏断点（≥768px）===== */
@media screen and (min-width: 768px) {
  .pay-page__back {
    left: 24px;
    width: 40px;
    height: 40px;
  }
  .pay-page__back-icon {
    width: 40px;
    height: 40px;
  }
  .pay-page__main {
    padding: 90px 24px 24px;
    gap: 24px;
  }
  .pay-page__heading {
    gap: 12px;
    padding-bottom: 24px;
  }
  .pay-page__title {
    font-size: 48px;
    line-height: 52px;
  }
  .pay-page__subtitle {
    font-size: 20px;
    line-height: 30px;
  }
  .pay-page__perks {
    gap: 12px;
  }
  .pay-page__perk {
    padding: 16px;
    border-radius: 12px;
  }
  .pay-page__perk-title {
    font-size: 20px;
    line-height: 32px;
    padding-bottom: 4px;
  }
  .pay-page__perk-text {
    font-size: 16px;
    line-height: 24px;
  }
  .pay-page__pricing {
    padding: 16px 0;
  }
  .pay-page__price-row {
    gap: 8px;
  }
  .pay-page__price {
    font-size: 64px;
    line-height: 64px;
  }
  .pay-page__price-unit {
    font-size: 24px;
    line-height: 32px;
    padding-bottom: 2px;
  }
  .pay-page__price-meta {
    gap: 8px;
    padding-top: 8px;
  }
  .pay-page__price-origin {
    font-size: 14px;
    line-height: 14px;
  }
  .pay-page__pill {
    height: 28px;
    padding: 0 12px;
  }
  .pay-page__pill-text {
    font-size: 13px;
    line-height: 16px;
  }
  .pay-page__action {
    padding: 16px 24px;
    padding-bottom: calc(12px + constant(safe-area-inset-bottom));
    padding-bottom: calc(12px + env(safe-area-inset-bottom));
    gap: 16px;
  }
  .pay-page__btn {
    height: 64px;
    border-radius: 12px;
  }
  .pay-page__btn-text {
    font-size: 24px;
    line-height: 32px;
  }
  .pay-page__safe-tip {
    font-size: 12px;
    line-height: 16px;
  }
}
</style>
