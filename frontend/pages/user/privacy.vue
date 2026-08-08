<template>
  <view :data-theme="themeKey" class="privacy-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="privacy-page__container">
      <!-- 标题区 -->
      <view class="privacy-page__heading">
        <text class="privacy-page__title">{{ $t('privacyDoc.title') }}</text>
      </view>

      <!-- 前言 -->
      <view class="privacy-page__intro">
        <text class="privacy-page__intro-text">{{ $t('privacyDoc.intro1') }}
{{ $t('privacyDoc.intro2') }}
{{ $t('privacyDoc.intro3') }}<text class="privacy-page__em">{{ $t('privacyDoc.intro3Em') }}</text></text>
      </view>

      <!-- 主内容卡片 -->
      <view class="privacy-page__card">
        <!-- 一、适用范围与个人信息处理者 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c1Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c1p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c1l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c1l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c1l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c1l4') }}</text>
            </view>
          </view>
          <text class="privacy-page__para">{{ $t('privacyDoc.c1p2') }}</text>
        </view>

        <!-- 二、我们如何收集和使用您的个人信息 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c2Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2p1') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s1Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s1p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s1l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s1l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s1l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s1l4') }}</text>
            </view>
          </view>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s1p2') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s2Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s2p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s2l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s2l2') }}<text class="privacy-page__em">{{ $t('privacyDoc.c2s2l2Em') }}</text>{{ $t('privacyDoc.c2s2l2b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s2l3') }}</text>
            </view>
          </view>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s2p2') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s2p3') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s3Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s3p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text"><text class="privacy-page__em">{{ $t('privacyDoc.c2s3l1Em') }}</text>{{ $t('privacyDoc.c2s3l1b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s3l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s3l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s3l4') }}</text>
            </view>
          </view>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s3p2') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s4Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s4p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s4l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s4l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s4l3') }}</text>
            </view>
          </view>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c2s4p2Em') }}</text>{{ $t('privacyDoc.c2s4p2b') }}<text class="privacy-page__em">{{ $t('privacyDoc.c2s4p2Em2') }}</text>{{ $t('privacyDoc.c2s4p2b2') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s4p3') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s5Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s5p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s5l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s5l2Em') }}{{ $t('privacyDoc.c2s5l2b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s5l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s5l4Em') }}{{ $t('privacyDoc.c2s5l4b') }}</text>
            </view>
          </view>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s5p2') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s6Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s6p1') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s7Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c2s7p1Em') }}</text>{{ $t('privacyDoc.c2s7p1b') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s8Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c2s8p1Em') }}</text>{{ $t('privacyDoc.c2s8p1b') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c2s8p2Em') }}</text>{{ $t('privacyDoc.c2s8p2b') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s9Title') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s8l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s8l2Em') }}{{ $t('privacyDoc.c2s8l2b') }}</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s10Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s9p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s9l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s9l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s9l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s9l4') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s9l5') }}</text>
            </view>
          </view>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c2s9p2Em') }}</text>{{ $t('privacyDoc.c2s9p2_extra') }}{{ $t('privacyDoc.c2s9p2b') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s9p3') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s11Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s10p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text"><text class="privacy-page__em">{{ $t('privacyDoc.c2s10l1Em') }}</text>{{ $t('privacyDoc.c2s10l1b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s10l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s10l3Em') }}{{ $t('privacyDoc.c2s10l3b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c2s10l4') }}</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c2s12Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c2s11p1') }}</text>
        </view>

        <!-- 三、我们如何调用系统权限 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c3Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c3p1') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c3s1Title') }}</text>
          <!-- Android 权限表格（横向滚动，避免窄屏截断） -->
          <scroll-view scroll-x class="privacy-page__table-scroll">
            <view class="privacy-page__table">
              <view class="privacy-page__table-row privacy-page__table-row--header">
                <text class="privacy-page__table-cell privacy-page__table-cell--name">{{ $t('privacyDoc.c3s1ThName') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info">{{ $t('privacyDoc.c3s1ThInfo') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose">{{ $t('privacyDoc.c3s1ThPurpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r1Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r1Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r1Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r2Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r2Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r2Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r3Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r3Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r3Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r4Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r4Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r4Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r5Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r5Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r5Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r6Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r6Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r6Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r7Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r7Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r7Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r8Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r8Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c3s1r8Purpose') }}</text>
              </view>
            </view>
          </scroll-view>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c3s1p2Em') }}</text>{{ $t('privacyDoc.c3s1p2b') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c3s2Title') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s2l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s2l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s2l3') }}</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c3s3Title') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s3l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s3l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s3l3Em') }}{{ $t('privacyDoc.c3s3l3b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s3l4') }}</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c3s4Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c3s4p1Em') }}</text>{{ $t('privacyDoc.c3s4p1b') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s4l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s4l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s4l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s4l4') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s4l5') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s4l6') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s4l7') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c3s4l8') }}</text>
            </view>
          </view>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c3s4p2Em') }}</text>{{ $t('privacyDoc.c3s4p2b') }}</text>
        </view>

        <!-- 四、本地存储与同类技术 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c4Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c4p1') }}</text>

          <!-- 本地存储明细表（横向滚动） -->
          <scroll-view scroll-x class="privacy-page__table-scroll">
            <view class="privacy-page__table">
              <view class="privacy-page__table-row privacy-page__table-row--header">
                <text class="privacy-page__table-cell privacy-page__table-cell--name">{{ $t('privacyDoc.c4ThName') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info">{{ $t('privacyDoc.c4ThInfo') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose">{{ $t('privacyDoc.c4ThPurpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c4r1Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c4r1Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c4r1Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c4r2Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c4r2Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c4r2Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c4r3Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c4r3Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c4r3Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c4r4Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c4r4Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c4r4Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c4r5Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c4r5Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c4r5Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c4r6Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c4r6Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c4r6Purpose') }}</text>
              </view>
            </view>
          </scroll-view>

          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c4p2Em') }}</text>{{ $t('privacyDoc.c4p2b') }}</text>
        </view>

        <!-- 五、共享、转让、公开披露 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c5Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c5p1Em') }}</text>{{ $t('privacyDoc.c5p1b') }}</text>

          <!-- 第三方共享信息表格（横向滚动，避免窄屏截断） -->
          <scroll-view scroll-x class="privacy-page__table-scroll">
            <view class="privacy-page__table">
              <view class="privacy-page__table-row privacy-page__table-row--header">
                <text class="privacy-page__table-cell privacy-page__table-cell--name">{{ $t('privacyDoc.c5ThName') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info">{{ $t('privacyDoc.c5ThInfo') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose">{{ $t('privacyDoc.c5ThPurpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c5r1Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c5r1Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c5r1Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c5r2Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c5r2Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c5r2Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c5r3Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c5r3Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c5r3Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c5r4Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c5r4Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c5r4Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c5r5Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c5r5Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c5r5Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c5r6Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data"><text class="privacy-page__em">{{ $t('privacyDoc.c5r6InfoEm') }}</text>{{ $t('privacyDoc.c5r6Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">{{ $t('privacyDoc.c5r6Purpose') }}</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">{{ $t('privacyDoc.c5r7Name') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">{{ $t('privacyDoc.c5r7Info') }}</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data"><text class="privacy-page__em">{{ $t('privacyDoc.c5r7PurposeEm') }}</text>{{ $t('privacyDoc.c5r7Purpose') }}</text>
              </view>
            </view>
          </scroll-view>

          <text class="privacy-page__para">{{ $t('privacyDoc.c5p2') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c5p3Em') }}</text>{{ $t('privacyDoc.c5p3b') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c5p4Em') }}</text>{{ $t('privacyDoc.c5p4b') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c5p5') }}</text>
        </view>

        <!-- 六、存储和保护 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c6Title') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c6s1Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c6s1p1Em') }}</text>{{ $t('privacyDoc.c6s1p1b') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c6s1p2Em') }}</text>{{ $t('privacyDoc.c6s1p2b') }}<text class="privacy-page__em">{{ $t('privacyDoc.c6s1p2Em2') }}</text>{{ $t('privacyDoc.c6s1p2b2') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c6s1p3Em') }}</text>{{ $t('privacyDoc.c6s1p3b') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c6s2Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c6s2p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s2l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s2l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s2l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s2l4') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s2l5') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s2l6') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s2l7') }}</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c6s3Title') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s3l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s3l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s3l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s3l4') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s3l5') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c6s3l6') }}</text>
            </view>
          </view>
          <text class="privacy-page__para">{{ $t('privacyDoc.c6s3p2') }}</text>
        </view>

        <!-- 七、您的权利 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c7Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c7p1') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c7s1Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c7s1p1') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c7s2Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c7s2p1') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c7s3Title') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s3l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s3l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s3l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s3l4') }}</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c7s4Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c7s4p1') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c7s5Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c7s5p1Em') }}</text>{{ $t('privacyDoc.c7s5p1b') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text"><text class="privacy-page__em">{{ $t('privacyDoc.c7s5l1Em') }}</text>{{ $t('privacyDoc.c7s5l1b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text"><text class="privacy-page__em">{{ $t('privacyDoc.c7s5l2Em') }}</text>{{ $t('privacyDoc.c7s5l2b') }}</text>
            </view>
          </view>
          <text class="privacy-page__para">{{ $t('privacyDoc.c7s5p2') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s5l3Em') }}{{ $t('privacyDoc.c7s5l3b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s5l4Em') }}{{ $t('privacyDoc.c7s5l4b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s5l5Em') }}{{ $t('privacyDoc.c7s5l5b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s5l6Em') }}{{ $t('privacyDoc.c7s5l6b') }}</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c7s6Title') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s6l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s6l2') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c7s6l3') }}</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c7s7Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c7s7p1') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c7s8Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c7s8p1Em') }}</text>{{ $t('privacyDoc.c7s8p1b') }}</text>
        </view>

        <!-- 八、未成年人保护 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c8Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c8p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c8l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c8l2Em') }}{{ $t('privacyDoc.c8l2b') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c8l3') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c8l4') }}</text>
            </view>
          </view>
        </view>

        <!-- 九、中国境外用户特别说明 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c9Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c9p1Em') }}</text>{{ $t('privacyDoc.c9p1b') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c9s1Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c9s1p1Em') }}</text>{{ $t('privacyDoc.c9s1p1b2') }}<text class="privacy-page__em">{{ $t('privacyDoc.c9s1p1Em2') }}</text>{{ $t('privacyDoc.c9s1p1b') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c9s1p2Em') }}</text>{{ $t('privacyDoc.c9s1p2b') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c9s2Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c9s2p1Em') }}</text>{{ $t('privacyDoc.c9s2p1b') }}</text>

          <text class="privacy-page__sub-title">{{ $t('privacyDoc.c9s3Title') }}</text>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c9s3p1Em') }}</text>{{ $t('privacyDoc.c9s3p1b') }}</text>
        </view>

        <!-- 十、开源与自建部署 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c10Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c10p1') }}</text>
        </view>

        <!-- 十一、本政策更新 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c11Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c11p1') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c11p2') }}</text>
        </view>

        <!-- 十二、如何联系我们 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">{{ $t('privacyDoc.c12Title') }}</text>
          <text class="privacy-page__para">{{ $t('privacyDoc.c12p1') }}</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c12l1') }}</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">{{ $t('privacyDoc.c12l2') }}</text>
            </view>
          </view>
          <text class="privacy-page__para"><text class="privacy-page__em">{{ $t('privacyDoc.c12p2Em') }}</text>{{ $t('privacyDoc.c12p2b') }}</text>
          <text class="privacy-page__para privacy-page__para--footer">{{ $t('privacyDoc.c12p3') }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 隐私政策页（privacy.vue）
 * --------------------------------------------------------------------------
 * 功能：展示应用隐私政策全文
 *  - 覆盖端：微信小程序 / H5 / App（Android、iOS、HarmonyOS）共 5 个发行版本
 *  - 标题区 + 前言（同意机制说明）
 *  - 政策正文共 12 章：适用范围与处理者、信息收集与使用（12 小节）、
 *    设备权限（Android/iOS/HarmonyOS 三端 + 不调用权限清单）、本地存储与同类技术（表格）、
 *    共享转让公开披露（第三方 SDK 表格）、存储与保护、您的权利、未成年人保护、
 *    中国境外用户特别说明（跨境传输，面向 Google Play 等境外分发）、
 *    开源与自建部署说明、政策更新、联系我们
 *  - 合规基线：数据存储于中国境内；注销账号提供「应用内 + 网页端」双入口
 *    （Google Play 账号删除政策要求），24 小时冷静期后物理删除
 *  - 纯展示页面，无交互逻辑（除三处表格横向滚动外）
 *  - 重点条款用嵌套 <text class="privacy-page__em"> 加粗强调
 *    （微信小程序不支持 HTML 加粗标签，故不使用 <b>/<strong>）
 */
import BackButton from '../../components/BackButton.vue'
import { useShare } from '../../composables/useShare'
import { t } from '../../locale'

useShare({ title: t('share.privacy') })
</script>

<style lang="scss">
/* ==========================================================================
 * 响应式单位说明（px → rpx 转换）
 * --------------------------------------------------------------------------
 * 基准：375px 设计稿，1px = 2rpx（uni-app 标准 750rpx = 屏宽）
 * 转 rpx：width/height/padding/margin/gap/font-size/line-height/border-radius/定位偏移
 * 保留 px：1px 边框、box-shadow 偏移/模糊、9999px、百分比、vh、z-index
 * 平板/折叠屏断点：≥768px 锁定关键尺寸为 px，避免 rpx 过度放大
 * ========================================================================== */
.privacy-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

/* ===== 主容器（对应设计稿 Container 390x3005）===== */
/* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与标题重叠 */
.privacy-page__container {
  padding: 210rpx 32rpx 96rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* ===== 标题区（对应设计稿 Heading 1）===== */
.privacy-page__heading {
  padding: 16rpx 0 32rpx;
}

.privacy-page__title {
  color: var(--color-text-primary);
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
}

/* ===== 前言（对应设计稿前言段落，参考 PageHeader desc 样式）===== */
.privacy-page__intro {
  padding-bottom: 32rpx;
}

.privacy-page__intro-text {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  white-space: pre-line;
}

/* ===== 主内容卡片（对应设计稿 Main Content Card）===== */
.privacy-page__card {
  padding: 48rpx;
  box-sizing: border-box;
  background: var(--color-card-bg);
  border-radius: 48rpx;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 64rpx;
}

/* ===== 章节（对应设计稿 Section）===== */
.privacy-page__section {
  display: flex;
  flex-direction: column;
}

/* 章节标题（对应 Heading 3，24px/32px var(--color-text-primary)） */
.privacy-page__section-title {
  color: var(--color-text-primary);
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 600;
  padding-bottom: 24rpx;
  white-space: pre-line;
}

/* 普通段落（对应 Container，16px/24px var(--color-text-secondary)，padding-bottom 16px） */
.privacy-page__para {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  padding-bottom: 32rpx;
  white-space: pre-line;
}

.privacy-page__para--footer {
  padding-top: 32rpx;
}

/* 强调文本（内联嵌套于段落/列表项内的 text，用于突出重点条款）
 * 说明：微信小程序不支持 HTML 加粗标签，跨端统一用嵌套 text 元素 + 加粗类实现 */
.privacy-page__em {
  color: var(--color-text-primary);
  font-weight: 600;
}

/* 子标题（对应 Heading 4，16px/24px var(--color-text-primary)，padding-bottom 8px） */
.privacy-page__sub-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
}

/* ===== 列表（对应设计稿 List，padding-left 20px，gap 8px）===== */
.privacy-page__list {
  padding: 0 0 32rpx 40rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.privacy-page__list-item {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
}

.privacy-page__bullet {
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  width: 14rpx;
  flex-shrink: 0;
}

.privacy-page__list-text {
  flex: 1;
  color: var(--color-text-secondary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  white-space: pre-line;
}

/* ===== 表格（对应设计稿 Table，横向滚动）===== */
/* scroll-view 横向滚动容器：宽度 100%，内部表格固定 600px 触发滚动 */
.privacy-page__table-scroll {
  margin-bottom: 32rpx;
  width: 100%;
  white-space: nowrap;
}

.privacy-page__table {
  /* 三列总宽 114.48 + 266.95 + 218.57 ≈ 600px，超出卡片内容区（310px）触发横向滚动 */
  width: 1200rpx;
  border: 1px solid var(--color-border-input);
  border-radius: 0;
  display: flex;
  flex-direction: column;
}

.privacy-page__table-row {
  display: flex;
  flex-direction: row;
  border-bottom: 1px solid var(--color-border-input);
}

.privacy-page__table-row:last-child {
  border-bottom: none;
}

.privacy-page__table-row--header {
  background: transparent;
}

.privacy-page__table-cell {
  padding: 24rpx 16rpx;
  font-size: 32rpx;
  line-height: 48rpx;
  border-right: 1px solid var(--color-border-input);
  box-sizing: border-box;
}

.privacy-page__table-cell:last-child {
  border-right: none;
}

/* 列宽：第三方名称 114.48 / 涉及个人信息 266.95 / 使用目的 218.56（总宽 600） */
.privacy-page__table-cell--name {
  width: 300rpx;
  flex-shrink: 0;
  word-break: break-all;
  overflow-wrap: anywhere;
}

.privacy-page__table-cell--info {
  width: 533.9rpx;
  flex-shrink: 0;
}

.privacy-page__table-cell--purpose {
  width: 437.14rpx;
  flex-shrink: 0;
}

.privacy-page__table-cell--data {
  color: var(--color-text-secondary);
  font-weight: 400;
  white-space: pre-line;
}

/* 表头单元格文字颜色 var(--color-text-primary) */
.privacy-page__table-row--header .privacy-page__table-cell {
  color: var(--color-text-primary);
  font-weight: 600;
}

/* ===== 平板/折叠屏断点（≥768px）=====
 * 在宽屏设备上 rpx 会过度放大，需将关键尺寸锁定为 px
 */
@media screen and (min-width: 768px) {
  .privacy-page__container {
    padding: 105px 16px 48px;
  }
  .privacy-page__heading {
    padding: 8px 0 16px;
  }
  .privacy-page__title {
    font-size: 32px;
    line-height: 36px;
  }
  .privacy-page__intro {
    padding-bottom: 16px;
  }
  .privacy-page__intro-text {
    font-size: 16px;
    line-height: 24px;
  }
  .privacy-page__card {
    padding: 24px;
    border-radius: 24px;
    gap: 32px;
  }
  .privacy-page__section-title {
    font-size: 24px;
    line-height: 32px;
    padding-bottom: 12px;
  }
  .privacy-page__para {
    font-size: 16px;
    line-height: 24px;
    padding-bottom: 16px;
  }
  .privacy-page__para--footer {
    padding-top: 16px;
  }
  .privacy-page__sub-title {
    font-size: 16px;
    line-height: 24px;
    padding-bottom: 8px;
  }
  .privacy-page__list {
    padding: 0 0 16px 20px;
    gap: 8px;
  }
  .privacy-page__bullet {
    font-size: 16px;
    line-height: 24px;
    width: 7px;
  }
  .privacy-page__list-text {
    font-size: 16px;
    line-height: 24px;
  }
  .privacy-page__table-scroll {
    margin-bottom: 16px;
  }
  .privacy-page__table {
    width: 600px;
  }
  .privacy-page__table-cell {
    padding: 12px 8px;
    font-size: 16px;
    line-height: 24px;
  }
  .privacy-page__table-cell--name {
    width: 150px;
    word-break: break-all;
    overflow-wrap: anywhere;
  }
  .privacy-page__table-cell--info {
    width: 266.95px;
  }
  .privacy-page__table-cell--purpose {
    width: 218.57px;
  }
}
</style>
