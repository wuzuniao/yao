<template>
  <view class="privacy-page">
    <!-- 顶部通知按钮（复用项目通知组件，非导航栏） -->
    <NoticeButton :has-notification="hasNotification" />

    <view class="privacy-page__container">
      <!-- 标题区 -->
      <view class="privacy-page__heading">
        <text class="privacy-page__title">隐私政策</text>
      </view>

      <!-- 前言 -->
      <view class="privacy-page__intro">
        <text class="privacy-page__intro-text">欢迎您使用本微信小程序。我们深知个{{ '\n' }}人信息对您的重要性，并会尽全力保护{{ '\n' }}您的个人信息安全可靠。请您在使用本{{ '\n' }}小程序前，仔细阅读并充分理解本《隐{{ '\n' }}私政策》。</text>
      </view>

      <!-- 主内容卡片 -->
      <view class="privacy-page__card">
        <!-- 一、我们如何收集和使用您的个人信息 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">一、我们如何收集和使用您{{ '\n' }}的个人信息</text>
          <text class="privacy-page__para">我们仅会出于本政策所述的以下目的，收集{{ '\n' }}和使用您的个人信息：</text>

          <text class="privacy-page__sub-title">1. 账号注册与登录</text>
          <text class="privacy-page__para">当您注册或登录本小程序时，您需要主动提{{ '\n' }}供以下信息：</text>

          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">用户名：用于创建您的账号及身份标识；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">密码：用于验证您的身份，保障账号安全{{ '\n' }}（密码将经过不可逆加密处理后存储，我{{ '\n' }}们无法获知您的明文密码）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">邮箱：用于账号绑定、密码找回及接收与{{ '\n' }}本小程序相关的重要通知。</text>
            </view>
          </view>

          <text class="privacy-page__para">以上信息由您自愿提供，若您不提供，则无{{ '\n' }}法使用注册登录功能，但您仍可以浏览小程{{ '\n' }}序的部分公开内容。</text>

          <text class="privacy-page__sub-title">2. 保障小程序的正常运行</text>
          <text class="privacy-page__para">本小程序基于 DCloud uni-app 框架开发。{{ '\n' }}为提供统计分析服务、优化性能及修复错{{ '\n' }}误，我们会自动收集以下设备信息：</text>

          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">设备唯一识别码（包括 IMEI、Android{{ '\n' }}ID、DEVICE_ID、IDFA）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">SIM 卡 IMSI 信息；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">OAID（匿名设备标识符）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">网络状态信息；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">应用启动数据及异常错误日志。</text>
            </view>
          </view>

          <text class="privacy-page__para">上述信息仅用于提升服务质量和用户体验，{{ '\n' }}不会与您的个人身份信息关联。</text>
        </view>

        <!-- 二、我们如何共享您的信息 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">二、我们如何共享您的信息</text>
          <text class="privacy-page__para">我们不会向任何第三方出售或非法共享您的{{ '\n' }}个人信息。为实现小程序的基本运行和功{{ '\n' }}能，我们可能会与以下第三方共享必要的技{{ '\n' }}术信息：</text>

          <!-- 第三方共享信息表格（横向滚动，避免窄屏截断） -->
          <scroll-view scroll-x class="privacy-page__table-scroll">
            <view class="privacy-page__table">
              <view class="privacy-page__table-row privacy-page__table-row--header">
                <text class="privacy-page__table-cell privacy-page__table-cell--name">第三方名称</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info">涉及个人信息</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose">使用目的</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">DCloud uni-{{ '\n' }}app 引擎</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">设备唯一识别码（IMEI、Android{{ '\n' }}ID、IDFA 等）、OAID、SIM 卡{{ '\n' }}IMSI</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">提供应用运行框架支持，进{{ '\n' }}行统计分析、性能优化和故{{ '\n' }}障排查</text>
              </view>
            </view>
          </scroll-view>

          <text class="privacy-page__para">除上述情况外，未经您的明确同意，我们不{{ '\n' }}会向其他任何第三方提供您的个人信息。</text>
        </view>

        <!-- 三、我们如何存储和保护您的信息 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">三、我们如何存储和保护您{{ '\n' }}的信息</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">存储地点：您的个人信息将存储于中华人{{ '\n' }}民共和国境内。</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">存储期限：我们仅在实现本政策所述目的{{ '\n' }}所必需的最短时间内保留您的信息，超出{{ '\n' }}期限后将进行删除或匿名化处理。</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">安全措施：我们采用加密传输、访问控{{ '\n' }}制、数据脱敏等技术手段，确保您的数据{{ '\n' }}安全。</text>
            </view>
          </view>
        </view>

        <!-- 四、您的权利 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">四、您的权利</text>
          <text class="privacy-page__para">您对您的个人信息享有以下权利：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">查询与更正：您可以在小程序内查看您的{{ '\n' }}用户名和邮箱，并随时修改邮箱地址；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">删除：您可以联系客服删除您的账号及个{{ '\n' }}人信息；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">撤回同意：您可以在设备系统设置中关闭{{ '\n' }}对我们收集设备信息的授权，但可能影响{{ '\n' }}小程序的正常使用；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">注销账号：您可以联系我们申请注销账{{ '\n' }}号，我们将在十五个工作日内完成处理。</text>
            </view>
          </view>
          <text class="privacy-page__para">如您需行使上述权利，可通过文末联系方式{{ '\n' }}与我们沟通。</text>
        </view>

        <!-- 五、未成年人保护 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">五、未成年人保护</text>
          <text class="privacy-page__para">根据相关法律法规，若您未满 14 周岁，请{{ '\n' }}您在监护人陪同下阅读本政策，并在征得监{{ '\n' }}护人明示同意后再使用本小程序。</text>
        </view>

        <!-- 六、本政策的更新 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">六、本政策的更新</text>
          <text class="privacy-page__para">我们可能适时修订本政策。如有重大变更{{ '\n' }}（如个人信息收集范围、使用目的等），我{{ '\n' }}们将通过小程序内的显著弹窗或公告方式通{{ '\n' }}知您。</text>
        </view>

        <!-- 七、如何联系我们 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">七、如何联系我们</text>
          <text class="privacy-page__para">如您对本政策有任何疑问、意见或建议，请{{ '\n' }}通过以下方式联系我们：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">电子邮箱：xpg@wuzuniao.com</text>
            </view>
          </view>
          <text class="privacy-page__para privacy-page__para--footer">我们将尽快在十五个工作日内回复您的问{{ '\n' }}题。</text>
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
 *  - 标题区：隐私政策标题 + 最后更新日期
 *  - 政策正文：引言、信息收集、信息使用、信息共享（含可横向滚动表格）、
 *    信息保护、Cookie 与同类技术、您的权利、儿童隐私、政策变更、联系我们等章节
 *  - 纯展示页面，无交互逻辑（除表格横向滚动外）
 */
import NoticeButton from '../../components/NoticeButton.vue'

// 设计稿顶栏图标为绿色无红点态
const hasNotification = false
</script>

<style lang="scss">
.privacy-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

/* ===== 主容器（对应设计稿 Container 390x3005）===== */
/* padding-top 100px：通知按钮 top45px + 高40px = 底部85px，留 15px 间隙避免与标题重叠 */
.privacy-page__container {
  padding: 100px 16px 48px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* ===== 标题区（对应设计稿 Heading 1）===== */
.privacy-page__heading {
  padding: 8px 0 16px;
}

.privacy-page__title {
  color: #0e0f0c;
  font-size: 32px;
  line-height: 36px;
  font-weight: 600;
}

/* ===== 前言（对应设计稿前言段落）===== */
.privacy-page__intro {
  padding-bottom: 24px;
}

.privacy-page__intro-text {
  color: #0e0f0c;
  font-size: 20px;
  line-height: 32.6px;
  font-weight: 400;
  white-space: pre-line;
}

/* ===== 主内容卡片（对应设计稿 Main Content Card）===== */
.privacy-page__card {
  padding: 24px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ===== 章节（对应设计稿 Section）===== */
.privacy-page__section {
  display: flex;
  flex-direction: column;
}

/* 章节标题（对应 Heading 3，24px/32px #0e0f0c） */
.privacy-page__section-title {
  color: #0e0f0c;
  font-size: 24px;
  line-height: 32px;
  font-weight: 600;
  padding-bottom: 12px;
  white-space: pre-line;
}

/* 普通段落（对应 Container，16px/24px #454745，padding-bottom 16px） */
.privacy-page__para {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
  padding-bottom: 16px;
  white-space: pre-line;
}

.privacy-page__para--footer {
  padding-top: 16px;
}

/* 子标题（对应 Heading 4，16px/24px #0e0f0c，padding-bottom 8px） */
.privacy-page__sub-title {
  color: #0e0f0c;
  font-size: 16px;
  line-height: 24px;
  font-weight: 600;
  padding-bottom: 8px;
}

/* ===== 列表（对应设计稿 List，padding-left 20px，gap 8px）===== */
.privacy-page__list {
  padding: 0 0 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.privacy-page__list-item {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
}

.privacy-page__bullet {
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  width: 7px;
  flex-shrink: 0;
}

.privacy-page__list-text {
  flex: 1;
  color: #454745;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
  white-space: pre-line;
}

/* ===== 表格（对应设计稿 Table，横向滚动）===== */
/* scroll-view 横向滚动容器：宽度 100%，内部表格固定 600px 触发滚动 */
.privacy-page__table-scroll {
  margin-bottom: 16px;
  width: 100%;
  white-space: nowrap;
}

.privacy-page__table {
  /* 三列总宽 114.48 + 266.95 + 218.57 ≈ 600px，超出卡片内容区（310px）触发横向滚动 */
  width: 600px;
  border: 1px solid #c1cab5;
  border-radius: 0;
  display: flex;
  flex-direction: column;
}

.privacy-page__table-row {
  display: flex;
  flex-direction: row;
  border-bottom: 1px solid #c1cab5;
}

.privacy-page__table-row:last-child {
  border-bottom: none;
}

.privacy-page__table-row--header {
  background: transparent;
}

.privacy-page__table-cell {
  padding: 12px 8px;
  font-size: 16px;
  line-height: 24px;
  border-right: 1px solid #c1cab5;
  box-sizing: border-box;
}

.privacy-page__table-cell:last-child {
  border-right: none;
}

/* 列宽：第三方名称 114.48 / 涉及个人信息 266.95 / 使用目的 218.56（总宽 600） */
.privacy-page__table-cell--name {
  width: 114.48px;
  flex-shrink: 0;
}

.privacy-page__table-cell--info {
  width: 266.95px;
  flex-shrink: 0;
}

.privacy-page__table-cell--purpose {
  width: 218.57px;
  flex-shrink: 0;
}

.privacy-page__table-cell--data {
  color: #454745;
  font-weight: 400;
  white-space: pre-line;
}

/* 表头单元格文字颜色 #0e0f0c */
.privacy-page__table-row--header .privacy-page__table-cell {
  color: #0e0f0c;
  font-weight: 600;
}
</style>
