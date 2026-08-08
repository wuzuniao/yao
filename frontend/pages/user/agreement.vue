<template>
  <view :data-theme="themeKey" class="privacy-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="privacy-page__container">
      <!-- 标题区 -->
      <view class="privacy-page__heading">
        <text class="privacy-page__title">服务协议</text>
      </view>

      <!-- 前言 -->
      <view class="privacy-page__intro">
        <text class="privacy-page__intro-text">欢迎您使用「无足鸟按时吃药打卡」（以下简称"本服务"或"我们"）。<text class="privacy-page__em">本服务是一款通用的打卡、提醒与记录工具</text>，提供微信小程序、Android App、iOS App、HarmonyOS App 及网页（H5）版本；"按时吃药打卡"仅为众多适用场景之一，您也可用于任何需要定时提醒与记录的日常计划。在您注册、登录及使用本服务前，请仔细阅读并充分理解本协议全文，特别是以深色加粗字体标识的条款。

您点击注册或登录页的同意按钮，或开始使用本服务，即<text class="privacy-page__em">表示您已阅读、理解并同意接受本协议全部条款，本协议在您与我们之间成立并生效</text>。如您不同意本协议的任何内容，请勿注册或使用本服务。

本协议与《隐私政策》共同构成您使用本服务的重要文件，二者互为补充、互不替代。其中《隐私政策》说明我们如何收集、使用、存储和保护您的个人信息；本协议说明您与我们之间的服务关系、使用规则与权利义务。</text>
      </view>

      <!-- 主内容卡片 -->
      <view class="privacy-page__card">
        <!-- 一、协议的确认与接纳 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">一、协议的确认与接纳</text>
          <text class="privacy-page__para">本协议是您与无足鸟运营方之间就您注册、登录及使用本服务所订立的契约。您确认，在注册本服务账号时，您已具备相应的民事行为能力，能够独立承担法律责任。</text>
          <text class="privacy-page__para">一旦出现下列情形之一，即<text class="privacy-page__em">视为您已同意并接受本协议约束</text>：（1）您点击页面上的"同意"或"注册"按钮完成注册；（2）您以其他方式实际使用本服务。若您为未成年人，应在监护人陪同下阅读本协议并在其明示同意后方可使用。</text>
          <text class="privacy-page__para">如我们对本协议进行修订，您在本协议修订后继续使用本服务，即<text class="privacy-page__em">视为接受修订后的协议</text>；若您不同意修订内容，应停止使用本服务。</text>
        </view>

        <!-- 二、账号注册与使用资格 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">二、账号注册与使用资格</text>
          <text class="privacy-page__para">您需使用合法、真实、未被占用的用户名注册，并<text class="privacy-page__em">妥善保管您的账号、密码及绑定邮箱</text>。因您账号保管不善导致的信息泄露、丢失或被他人使用，相关责任由您自行承担。</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">一个账号仅供一名用户使用；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">密码在传输后经 bcrypt 算法加盐哈希后存储，我们<text class="privacy-page__em">仅保存不可逆的哈希值，无法获知也不会向任何人提供您的明文密码</text>；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">我们保留对长期未登录（超过冷静期或依规则判定为休眠）的账号进行清理或回收的权利，清理前将依照《隐私政策》相关约定处理您的个人信息。</text>
            </view>
          </view>
        </view>

        <!-- 三、服务内容与形式 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">三、服务内容与形式</text>
          <text class="privacy-page__para">本服务是一款<text class="privacy-page__em">通用的打卡、提醒与记录工具</text>，核心能力包括：创建计划、设置提醒时间、接收提醒通知（站内信、邮件、微信订阅消息、App 推送）、记录打卡与查看历史。部分功能受平台能力限制，仅在特定端可用：微信一键登录与微信订阅消息仅微信小程序端提供，指纹（生物识别）登录与 App 推送通知仅 App 端（Android／iOS／HarmonyOS）提供。前述能力适用于各类需要定时提醒与记录的场景，例如按时吃药、饮水、运动、学习等，"按时吃药打卡"仅是其中一项适用场景，而非本服务的全部或主要限定用途。</text>
          <text class="privacy-page__para">我们可能根据运营需要，对服务功能、界面、资费（如有）进行调整、优化或终止部分功能，并在合理范围内提前通知。重大调整将以公告或应用内提示方式告知。</text>
          <text class="privacy-page__para"><text class="privacy-page__em">重要提示：</text>本服务仅提供通用的提醒与记录功能，<text class="privacy-page__em">不构成任何专业领域的建议或指导</text>（包括但不限于医疗、健康、法律、财务等）。如您将本服务用于用药等健康相关场景，相关方案请以医生或专业医疗人员的指导为准，我们对您依据提醒所做的任何安排不承担责任。</text>
        </view>

        <!-- 四、用户行为规范 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">四、用户行为规范</text>
          <text class="privacy-page__para">您承诺在使用本服务过程中遵守中华人民共和国相关法律法规，<text class="privacy-page__em">不得利用本服务从事任何违法、违规或侵犯他人合法权益的行为</text>，包括但不限于：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">传播违法不良信息、干扰服务正常运行、攻击或侵入系统；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">滥用提醒功能干扰他人，或对第三方进行骚扰、诽谤；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">对本服务进行反向工程、反向汇编、反编译，或试图提取源代码、移除知识产权声明或技术保护措施。</text>
            </view>
          </view>
          <text class="privacy-page__para">您对其在本服务中发布、上传的内容（如计划备注、反馈信息）的<text class="privacy-page__em">真实性、合法性负责</text>。我们不对用户生成内容的准确性、完整性作任何明示或默示担保。</text>
        </view>

        <!-- 五、知识产权 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">五、知识产权</text>
          <text class="privacy-page__para">本服务及其相关软件、界面设计、文字、图形、商标、标识、数据等内容的<text class="privacy-page__em">知识产权均归我们或相关权利人所有</text>，受《商标法》《著作权法》《专利法》等法律及相关国际条约保护。</text>
          <text class="privacy-page__para">我们授予您一项<text class="privacy-page__em">个人、非独占、不可转让、可撤销的有限使用权</text>，仅用于您在本服务授权范围内使用。未经书面许可，您不得复制、修改、传播、出售或将其用于商业目的。</text>
          <text class="privacy-page__para">您理解：您在本服务中录入的计划、备注等个人数据<text class="privacy-page__em">归您本人所有</text>；您授权我们在为您提供服务所必需的范围内存储、处理并使用上述数据。</text>
        </view>

        <!-- 六、个人信息保护 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">六、个人信息保护</text>
          <text class="privacy-page__para">我们高度重视您的个人信息保护。关于我们如何收集、使用、共享、存储您的个人信息，以及您所享有的查阅、更正、删除、注销等权利，<text class="privacy-page__em">请详见《隐私政策》</text>。您使用本服务即表示您已同时阅读并理解《隐私政策》的相关内容，并同意我们按照该政策处理您的个人信息。</text>
        </view>

        <!-- 七、免责声明 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">七、免责声明</text>
          <text class="privacy-page__para">本服务<text class="privacy-page__em">按"现状"提供</text>。因不可抗力、网络故障、设备兼容、第三方服务异常等非我们可控因素导致的服务中断、数据延迟或丢失，<text class="privacy-page__em">我们不承担责任</text>。</text>
          <text class="privacy-page__para">您理解并同意：提醒通知可能因网络、设备、系统拦截等原因延迟或未能送达，<text class="privacy-page__em">我们不对因此造成的任何后果承担责任</text>；若您将本服务用于健康相关场景，请以专业医疗人员指导为准。</text>
          <text class="privacy-page__para">在法律允许的最大范围内，我们就本服务的使用<text class="privacy-page__em">不提供任何明示或默示担保</text>；因使用本服务所产生的直接或间接损失，我们仅在因故意或重大过失导致时承担相应责任。</text>
        </view>

        <!-- 八、违约处理 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">八、违约处理</text>
          <text class="privacy-page__para">如您违反本协议或相关法律法规，我们<text class="privacy-page__em">有权根据情节轻重采取警示、限制功能、暂停或终止您的账号及服务使用</text>，并保留追究法律责任的权利。</text>
          <text class="privacy-page__para">因您的行为给我们或第三方造成损失的，<text class="privacy-page__em">您应依法承担相应赔偿责任</text>。</text>
        </view>

        <!-- 九、服务的变更、中断与终止 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">九、服务的变更、中断与终止</text>
          <text class="privacy-page__para">为维护服务安全与质量，我们可能定期进行系统维护或升级，由此造成的临时性服务中断，我们将尽力提前告知并尽快恢复。</text>
          <text class="privacy-page__para">出现下列情形之一时，我们<text class="privacy-page__em">有权终止向您提供部分或全部服务</text>：您主动注销账号；您严重违反本协议；法律法规或监管要求；其他依约定或法律应终止的情形。服务终止后，我们将依照《隐私政策》处理您的个人信息。</text>
          <text class="privacy-page__para">您有权随时主动终止本协议：在应用内「设置 - 个人信息」页点击「删除账号」，或直接访问网页版 yao.wuzuniao.com/pages/user/profile 登录后操作。关于账号删除与数据处理的免登录说明详见 yao.wuzuniao.com/pages/user/delete-account 。<text class="privacy-page__em">经 24 小时冷静期后，您的账号与全部数据将被彻底删除且不可恢复</text>，具体删除范围详见《隐私政策》第七条第 5 项。</text>
        </view>

        <!-- 十、第三方服务 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">十、第三方服务</text>
          <text class="privacy-page__para">为向您提供提醒通知等功能，本服务接入了必要的第三方服务，包括 DCloud uni-app 运行框架、友盟+ U-Push 消息推送 SDK（仅 App 端）、微信开放平台（仅微信小程序端）以及邮件服务商。您使用相关功能即视为同意相关第三方按其规则处理必要信息，各第三方收集的信息类型与用途<text class="privacy-page__em">详见《隐私政策》第五条</text>。我们对第三方服务的<text class="privacy-page__em">可用性及数据保护不承担责任</text>。</text>
        </view>

        <!-- 十一、协议变更 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">十一、协议变更</text>
          <text class="privacy-page__para">我们可能适时修订本协议，修订后的协议将在应用内或官方渠道公布并注明生效日期。<text class="privacy-page__em">若您继续使用本服务，即视为接受修订后的协议</text>；若您不同意修订内容，应停止使用本服务。</text>
        </view>

        <!-- 十二、争议解决与管辖 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">十二、争议解决与管辖</text>
          <text class="privacy-page__para">本协议的订立、效力、解释、履行及争议解决<text class="privacy-page__em">均适用中华人民共和国法律</text>（不含冲突法规则）。因本协议引起的或与本协议有关的任何争议，双方应友好协商解决；协商不成的，<text class="privacy-page__em">任一方均可向有管辖权的人民法院提起诉讼</text>。</text>
          <text class="privacy-page__para">若您在中国境外使用本服务，<text class="privacy-page__em">您所在国家或地区法律赋予您的强制性消费者权利不受本条影响</text>。本服务的服务器位于中国境内，跨境传输相关说明详见《隐私政策》第九条。</text>
        </view>

        <!-- 十三、联系我们 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">十三、联系我们</text>
          <text class="privacy-page__para">如您对本协议有任何疑问，请通过以下方式联系我们：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">电子邮箱：xpg@wuzuniao.com</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">其他联系方式（微信公众号、QQ 交流群）详见「设置 - 联系我们」页面。</text>
            </view>
          </view>
          <text class="privacy-page__para privacy-page__para--footer">本协议自公示之日起生效。</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 服务协议页面（agreement.vue）
 * --------------------------------------------------------------------------
 * 功能：展示《服务协议》全文，与隐私政策页（privacy.vue）布局完全一致。
 *  - 覆盖端：微信小程序 / H5 / App（Android、iOS、HarmonyOS）共 5 个发行版本
 *  - 标题区 + 前言（同意机制说明）
 *  - 协议正文共 13 章：协议确认与接纳、账号注册与使用资格、服务内容与形式、
 *    用户行为规范、知识产权、个人信息保护、免责声明、违约处理、
 *    服务的变更中断与终止、第三方服务、协议变更、争议解决与管辖、联系我们
 *  - 纯展示页面，无交互逻辑
 *  - 布局与类名完全复用 privacy.vue，仅文案不同；重点条款用嵌套
 *    <text class="privacy-page__em"> 加粗强调（微信小程序不支持 HTML 加粗标签）
 *  - themeKey 由 main.js 全局 mixin 注入，模板直接绑定 :data-theme
 */
import BackButton from '../../components/BackButton.vue'
import { useShare } from '../../composables/useShare'

useShare({ title: '服务协议' })
</script>

<style lang="scss">
/* 样式完全复用 privacy.vue 的 .privacy-page 同名规则，确保两页视觉一致 */
.privacy-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.privacy-page__container {
  padding: 210rpx 32rpx 96rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.privacy-page__heading {
  padding: 16rpx 0 32rpx;
}

.privacy-page__title {
  color: var(--color-text-primary);
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
}

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

/* 微信小程序端：主内容卡片外侧加留白，避免与导航胶囊/状态栏顶栏过近 */
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

.privacy-page__section {
  display: flex;
  flex-direction: column;
}

.privacy-page__section-title {
  color: var(--color-text-primary);
  font-size: 48rpx;
  line-height: 64rpx;
  font-weight: 600;
  padding-bottom: 24rpx;
  white-space: pre-line;
}

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

.privacy-page__em {
  color: var(--color-text-primary);
  font-weight: 600;
}

.privacy-page__sub-title {
  color: var(--color-text-primary);
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
}

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

/* 平板/折叠屏断点（≥768px）：rpx 会过度放大，关键尺寸锁定为 px */
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
}
</style>
