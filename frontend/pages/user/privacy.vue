<template>
  <view :data-theme="themeKey" class="privacy-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="privacy-page__container">
      <!-- 标题区 -->
      <view class="privacy-page__heading">
        <text class="privacy-page__title">隐私政策</text>
      </view>

      <!-- 前言 -->
      <view class="privacy-page__intro">
        <text class="privacy-page__intro-text">欢迎您使用「无足鸟按时吃药打卡」（以下简称"本产品"或"我们"）。本产品是一款通用打卡计划提醒与记录工具，提供微信小程序、Android App、iOS App、HarmonyOS App 及网页（H5）版本。我们深知个人信息对您的重要性，并会尽全力保护您的个人信息安全可靠。

请您在使用本产品前，仔细阅读并充分理解本《隐私政策》全文，特别是以深色加粗字体标识的条款。您在注册或登录页勾选同意本政策，或继续使用本产品，即表示您已充分理解并同意我们按照本政策处理您的个人信息。如您不同意本政策的任何内容，请立即停止使用本产品。

本政策适用于本产品的全部客户端形态。因平台能力差异，部分条款仅适用于特定端（已在文中注明）。<text class="privacy-page__em">本产品的服务器位于中华人民共和国境内；若您在中国境外使用本产品，请特别阅读第九条「中国境外用户特别说明」。</text></text>
      </view>

      <!-- 主内容卡片 -->
      <view class="privacy-page__card">
        <!-- 一、适用范围与个人信息处理者 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">一、适用范围与个人信息处理者</text>
          <text class="privacy-page__para">本产品的个人信息处理者为「无足鸟」团队，联系邮箱 xpg@wuzuniao.com。本政策适用于我们通过以下形态向您提供的全部服务：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">微信小程序「无足鸟按时吃药打卡」；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">Android 与 iOS 移动应用（应用包名 com.wuzuniao.yao）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">HarmonyOS（鸿蒙）移动应用（应用包名 com.wuzuniao.yao）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">网页版（H5）。</text>
            </view>
          </view>
          <text class="privacy-page__para">本产品的核心功能为：制定打卡计划、按设定时间接收提醒、完成打卡并查看历史记录。除实现上述功能及保障账号与运行安全所必需外，我们不会收集与之无关的个人信息。</text>
        </view>

        <!-- 二、我们如何收集和使用您的个人信息 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">二、我们如何收集和使用您的个人信息</text>
          <text class="privacy-page__para">我们仅会出于本政策所述的以下目的，遵循合法、正当、必要与诚信原则，收集和使用您的个人信息。以下逐项说明收集的信息种类、目的、方式与必要性。</text>

          <text class="privacy-page__sub-title">1. 账号注册（必要功能）</text>
          <text class="privacy-page__para">当您注册本产品账号时，您需要主动提供以下信息：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">用户名：用于创建账号、作为您的身份标识与展示昵称，全平台唯一；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">密码：用于验证您的身份、保障账号安全。密码在传输后经 bcrypt 算法加盐哈希后存储，我们仅保存不可逆的哈希值，无法获知、也不会向任何人提供您的明文密码；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">电子邮箱：作为您的主账号标识，用于接收注册验证码、找回密码、变更邮箱验证以及（在您开启邮件提醒时）接收打卡提醒；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">邮箱验证码：为验证邮箱归属权，我们会向您填写的邮箱发送一次性验证码，并在服务端临时保存以完成校验，校验完成或超时后即失效。</text>
            </view>
          </view>
          <text class="privacy-page__para">若您不提供上述信息，将无法完成注册与使用打卡提醒等核心功能。</text>

          <text class="privacy-page__sub-title">2. 账号登录与登录状态维持（必要功能）</text>
          <text class="privacy-page__para">本产品提供以下登录方式，您可自主选择其一：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">账号密码登录：需提供用户名（或邮箱）与密码；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">微信一键登录（仅微信小程序端）：在您点击授权后，我们通过微信官方 wx.login 接口获取临时登录凭证 code，并由服务端向微信服务器换取您在本小程序下的 OpenID 与 session_key，用于识别您的账号身份。<text class="privacy-page__em">我们不会获取您的微信昵称、头像、性别、地区、手机号、通讯录或好友关系</text>；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">指纹（生物识别）一键登录（仅 App 端，含 Android／iOS／HarmonyOS，可选）：详见本条第 3 项。</text>
            </view>
          </view>
          <text class="privacy-page__para">登录成功后，我们会向您的设备下发一个有效期 7 天的登录令牌（JWT Access Token），保存在设备本地，用于免除重复登录。当令牌剩余有效期不足 1 天且您仍在活跃使用时，客户端会自动为其静默续期，以免您在使用过程中被中断。您主动退出登录、修改密码、重置密码或申请注销账号时，服务端将使您全部设备上的既有令牌立即失效。</text>
          <text class="privacy-page__para">在您成功登录并同意本政策之前，我们不会向服务器发送除登录请求本身以外的任何个人信息。</text>

          <text class="privacy-page__sub-title">3. 指纹（生物识别）一键登录（仅 App 端，含 Android／iOS／HarmonyOS，可选功能）</text>
          <text class="privacy-page__para">若您的设备支持生物识别（Android／HarmonyOS 指纹、iOS Touch ID／Face ID）且已在系统中录入，您可自主开启一键登录。开启后：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text"><text class="privacy-page__em">生物特征本身由您的设备操作系统在安全区域内完成采集、存储与比对，我们既不采集、也不接触、更不会上传或存储您的任何生物特征数据。</text>我们仅通过系统接口获知"本次验证是否通过"这一结果；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">设备标识（device_id）：首次登录时由 App 在本地随机生成的一串 UUID，与您的硬件序列号、IMEI 等无关，用于将登录凭证绑定到本台设备，防止凭证被复制到其他设备使用；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">生物识别登录凭证（biometric token）：一串由服务端生成的高熵随机字符串，有效期 31 天，与您的账号和上述设备标识绑定，存储于本应用私有存储区（应用沙箱），其他应用通常无法访问；该凭证同时与设备标识绑定，仅在本设备有效，复制到其他设备无法使用；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">机型与系统版本：不上传服务器。</text>
            </view>
          </view>
          <text class="privacy-page__para">您可随时在个人信息页关闭指纹登录，关闭仅切换是否默认使用指纹登录的开关，不会清除本地凭证、也不会作废服务端凭证记录，便于您再次开启时无需重新账号密码登录。退出登录时同样保留指纹凭证，便于下次使用指纹一键登录；仅在注销账号时，服务端会一并作废您全部设备的生物识别凭证。</text>

          <text class="privacy-page__sub-title">4. 打卡计划与打卡记录（核心功能）</text>
          <text class="privacy-page__para">为实现按时提醒与记录，我们会收集并存储由您主动填写与产生的以下内容：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">计划名称、备注/描述：由您自行命名与填写；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">计划起止日期、每日一个或多个提醒时刻、优先级、计划状态（进行中/暂停/已结束）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">打卡记录：每次打卡对应的计划、提醒时间点与实际打卡时间戳，用于生成日历与统计。</text>
            </view>
          </view>
          <text class="privacy-page__para"><text class="privacy-page__em">特别提示：</text>本产品为通用打卡工具，计划名称与备注为自由文本，其内容完全由您自主决定。请您审慎填写——<text class="privacy-page__em">我们不主动要求、也不建议您在其中填写药品名称、病历、诊断结论、症状等健康医疗信息或其他敏感个人信息</text>。若您自行填写此类内容，视为您自愿提供并同意我们仅为向您展示计划、生成提醒文案与打卡记录之目的存储与使用，我们不会对其进行任何分析、画像、二次利用或对外提供。</text>
          <text class="privacy-page__para">当提醒触发时，计划名称与备注会作为提醒正文的组成部分，随您选择的通知渠道下发（例如出现在邮件正文、站内信或推送通知栏中）。请您在选择通知渠道时一并知悉这一点。</text>

          <text class="privacy-page__sub-title">5. 提醒通知渠道配置（可选功能，由您逐项开启）</text>
          <text class="privacy-page__para">本产品提供四种提醒渠道，均需您主动配置后才会启用：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">站内信：默认渠道，仅在本产品内部投递，不涉及向外部传输，内容为提醒文案与您的账号 ID；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">邮件提醒：需您填写用于发信的 SMTP 服务器地址、端口、邮箱账号及<text class="privacy-page__em">客户端专用密码/授权码</text>。该密码属于敏感凭据，我们在服务端以 AES-256-GCM 算法加密存储，接口返回时一律以掩码呈现、绝不回传明文，且仅在为您投递提醒邮件时于内存中解密使用。我们强烈建议您使用邮箱服务商签发的"客户端专用密码/授权码"，而非邮箱登录密码；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">微信订阅消息（仅微信小程序端）：需您通过微信官方授权弹窗逐次授权。我们仅记录您的订阅额度（已授权次数与已消耗次数），并使用第 2 项中获取的 OpenID 通过微信官方接口下发消息。微信订阅消息为"一次性订阅"，额度用尽后需您再次授权；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">App 推送通知（仅 App 端，含 Android／iOS／HarmonyOS）：需您在通知方式页主动添加。届时我们会收集由推送服务生成的<text class="privacy-page__em">设备推送标识（Device Token）</text>及设备平台类型（android／ios／harmony），用于将提醒定向下发到您的这台设备。详见本政策第三条与第五条。</text>
            </view>
          </view>
          <text class="privacy-page__para">您可随时在「设置 - 通知方式」中新增、修改或删除除站内信外的任一渠道；删除后对应配置信息（含加密的邮箱密码、设备推送标识）将从我们的服务器一并删除。</text>

          <text class="privacy-page__sub-title">6. 通知发送记录</text>
          <text class="privacy-page__para">为便于您在站内信中回看历史提醒、支持已读状态与失败重试，我们会记录每次提醒的：所属计划、使用的渠道、提醒时间点、实际发送时间、发送状态（成功/失败/未读）、触发类型（准时/超时催办）及失败时的错误摘要。该记录仅您本人可见。</text>

          <text class="privacy-page__sub-title">7. 系统公告的接收与展示</text>
          <text class="privacy-page__para">我们会在首页向全体用户展示由管理员发布的系统公告（如版本更新、服务调整、政策变更提示）。公告内容由我们统一编写，<text class="privacy-page__em">不含任何用户的个人信息</text>，也不针对特定用户投放。公告的"已读"状态仅记录在您的设备本地，不会上传服务器。</text>

          <text class="privacy-page__sub-title">8. 分享功能（仅微信小程序端）</text>
          <text class="privacy-page__para">当您主动使用微信右上角菜单将本小程序页面「转发给朋友」或「分享到朋友圈」时，我们会向微信提供页面标题与页面路径。<text class="privacy-page__em">分享链接中不包含您的账号标识，也不携带您的任何计划、打卡记录或个人资料</text>。接收方打开后进入的是未登录状态的公共页面。</text>
          <text class="privacy-page__para">需要特别说明的是：微信在生成分享卡片时，默认会截取分享时刻的<text class="privacy-page__em">当前页面画面作为封面快照</text>。由于本小程序所有含您个人数据的页面均需登录后方可查看，且分享链接本身进入的是未登录公共页面，因此该快照里出现的仅为页面自身的通用结构（如本政策页的条款文字、首页的引导卡片），不会出现您的账号、计划或打卡记录等个人数据。若您在被登录态下截取了含有个人内容的页面进行分享，该画面快照将随之被微信用于生成分享卡片封面。分享行为由微信客户端完成，适用微信的相关规则，您可随时在微信内删除已发出的分享。</text>

          <text class="privacy-page__sub-title">9. 个人资料完善（可选功能）</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">个性签名：由您自愿填写，仅用于在设置页展示；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">头像：<text class="privacy-page__em">仅支持从本产品内置的若干张预设图案中选择</text>，我们仅记录您所选图案的标识。本产品不会访问您的相册、摄像头，也不会上传任何您本地的图片文件。</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">10. 保障服务正常运行与安全（必要）</text>
          <text class="privacy-page__para">本产品基于 DCloud uni-app 框架开发。为保障应用运行、进行统计分析、优化性能及排查错误，运行期间可能收集以下信息：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">设备与系统信息：设备型号、操作系统及版本、屏幕分辨率与安全区域尺寸（用于适配刘海屏、状态栏与微信胶囊按钮位置）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">设备唯一识别码：包括 IMEI、Android ID、DEVICE_ID、IDFA、OAID、OpenUDID、GUID、SIM 卡 IMSI 等（由框架与推送 SDK 依所在平台与系统授权情况采集，用于设备去重与统计分析）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">网络状态信息：网络连接类型与状态、IP 地址（IP 地址由服务端在接收请求时自动获知，用于访问频率限制与安全防护）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">应用启动数据及异常错误日志；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">最后登录时间：记录于您的账号，用于账号安全审计。</text>
            </view>
          </view>
          <text class="privacy-page__para">上述信息用于提升服务质量、防范恶意注册与暴力破解等安全风险。我们已在应用中关闭 uni 统计（uniStatistics）功能，并在 iOS 端关闭 IDFA 采集。相关第三方 SDK 均已做延迟初始化处理，<text class="privacy-page__em">在您同意本政策之前不会启动、不会采集任何设备信息</text>。</text>
          <text class="privacy-page__para">依据框架方要求特别声明：我们的产品基于 DCloud uni-app 开发，应用运行期间需要收集您的设备唯一识别码（IMEI／Android ID／DEVICE_ID／IDFA、SIM 卡 IMSI 信息、OAID）以提供统计分析服务，并通过应用启动数据及异常错误日志分析改进性能和用户体验，为用户提供更好的服务。详见《DCloud App 引擎隐私政策》：dcloud.io/license/appprivacy.html。</text>

          <text class="privacy-page__sub-title">11. 敏感个人信息说明</text>
          <text class="privacy-page__para">根据《个人信息保护法》，敏感个人信息是一旦泄露或被非法使用容易导致人格尊严受到侵害或人身、财产安全受到危害的个人信息。就本产品而言：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">生物识别信息：<text class="privacy-page__em">我们不收集、不存储、不传输您的任何生物识别特征数据</text>，指纹验证全程在您的设备安全区域内由操作系统完成；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">健康医疗信息：我们不主动收集。本产品名称虽含"吃药"，但功能上为通用打卡工具，我们不设置任何药品、病症、剂量等结构化字段，也不要求您填写此类信息；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">若您自行在计划名称或备注中填入敏感个人信息，则视为您在充分知悉本条提示后作出的<text class="privacy-page__em">单独同意</text>，我们将仅按第 4 项所述目的处理并采取加密传输、访问隔离等保护措施。您可随时编辑或删除该内容；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">我们不收集身份证件号码、人脸、行踪轨迹、金融账户、宗教信仰等其他任何敏感个人信息。</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">12. 无需您同意即可处理的情形</text>
          <text class="privacy-page__para">根据《中华人民共和国个人信息保护法》第十三条，在下列情形下，我们处理您的个人信息无需取得您的单独同意：为订立、履行您作为一方当事人的合同所必需；为履行法定职责或者法定义务所必需；为应对突发公共卫生事件，或者紧急情况下为保护自然人的生命健康和财产安全所必需；在合理的范围内处理您自行公开或者其他已经合法公开的个人信息；法律、行政法规规定的其他情形。</text>
        </view>

        <!-- 三、我们如何调用系统权限 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">三、我们如何调用设备权限</text>
          <text class="privacy-page__para">本产品坚持权限最小化原则。以下为我们在各端申请的全部权限及其用途，除此之外我们不会申请任何其他权限。您可随时在系统设置中撤回已授予的权限。</text>

          <text class="privacy-page__sub-title">1. Android 端申请的权限</text>
          <!-- Android 权限表格（横向滚动，避免窄屏截断） -->
          <scroll-view scroll-x class="privacy-page__table-scroll">
            <view class="privacy-page__table">
              <view class="privacy-page__table-row privacy-page__table-row--header">
                <text class="privacy-page__table-cell privacy-page__table-cell--name">权限</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info">用途</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose">拒绝后的影响</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">INTERNET 网络访问</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">与服务器通信，同步计划与打卡数据</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">无法使用任何联网功能</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">ACCESS_NETWORK_STATE / ACCESS_WIFI_STATE 网络状态</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">判断网络连通性，在断网时给出提示并暂停重试</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">断网提示可能不准确</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">POST_NOTIFICATIONS 通知栏</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">在通知栏展示打卡提醒</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">无法收到 App 推送提醒</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">VIBRATE 震动</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">提醒到达时震动提示</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">提醒无震动，其余不受影响</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">RECEIVE_BOOT_COMPLETED 开机启动</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">设备重启后恢复推送服务连接，避免漏收提醒</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">重启后需手动打开一次 App 才能恢复推送</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">WAKE_LOCK 保持唤醒</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">由推送 SDK 声明，接收提醒时短暂唤醒设备以完成消息处理</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">息屏状态下提醒可能延迟</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">C2DM_RECEIVE / 魅族 PUSH 接收</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">由推送 SDK 声明，用于接收系统级推送消息</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">对应通道不可用，可改用其他提醒渠道</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">指纹识别（系统生物识别）</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">您主动开启指纹一键登录时调用系统验证</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">无法使用指纹登录，可改用账号密码登录</text>
              </view>
            </view>
          </scroll-view>
          <text class="privacy-page__para">其中 WAKE_LOCK、C2DM_RECEIVE、魅族 PUSH 三项由推送 SDK 在打包时自动合并声明，<text class="privacy-page__em">仅服务于提醒消息的接收，不会用于任何其他目的</text>。</text>

          <text class="privacy-page__sub-title">2. iOS 端申请的权限</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">通知权限：用于展示打卡提醒，首次需要时由系统弹窗询问；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">Touch ID / Face ID：仅在您主动开启指纹一键登录时调用；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">我们已明确关闭 IDFA（广告标识符）采集。</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">3. HarmonyOS（鸿蒙）端申请的权限</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">ohos.permission.ACCESS_BIOMETRIC（生物识别）：仅在您主动开启指纹一键登录时调用，用途说明为"用于指纹快速登录，验证您的身份"；拒绝后可改用账号密码登录；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">ohos.permission.INTERNET（网络访问）与 ohos.permission.GET_NETWORK_INFO（网络状态）：与服务器通信、判断网络连通性；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">ohos.permission.APP_TRACKING_CONSENT（广告标识符 OAID）：由推送 SDK 声明并自动合并，用于推送消息的设备标识与统计分析；<text class="privacy-page__em">您可在系统设置中随时关闭，关闭不影响提醒功能的正常使用</text>；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">通知权限：用于在通知栏展示打卡提醒，由系统在首次需要时询问。</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">4. 我们明确不会调用的权限与能力</text>
          <text class="privacy-page__para">经全面核查，本产品<text class="privacy-page__em">不会</text>申请或调用以下权限与能力：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">地理位置（GPS / 基站 / Wi-Fi 定位）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">摄像头、相册、麦克风与录音；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">通讯录、通话记录、短信与电话拨打；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">日历、健康数据、运动与计步数据；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">已安装应用列表、运行中进程信息；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">外部存储的读写（不读取、不写入您手机中的任何文件）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">微信头像、昵称、性别、地区、手机号与好友关系；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">扫码、蓝牙、NFC 与剪贴板读取。</text>
            </view>
          </view>
          <text class="privacy-page__para">说明：在「帮助中心」与首页的部分操作中，我们会在您主动点击后<text class="privacy-page__em">写入</text>剪贴板（例如复制联系邮箱），此为单向写入，我们不会读取您剪贴板中的任何已有内容。</text>
        </view>

        <!-- 四、我们如何使用 Cookie 及同类技术（本地存储） -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">四、本地存储与同类技术</text>
          <text class="privacy-page__para">为实现免登录、提升响应速度与记住您的偏好，我们会在您的设备本地（小程序 Storage / App 应用私有存储 / 浏览器 localStorage）保存少量数据。这些数据存放于您的设备上，除下表注明外不会上传服务器：</text>

          <!-- 本地存储明细表（横向滚动） -->
          <scroll-view scroll-x class="privacy-page__table-scroll">
            <view class="privacy-page__table">
              <view class="privacy-page__table-row privacy-page__table-row--header">
                <text class="privacy-page__table-cell privacy-page__table-cell--name">存储项</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info">内容</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose">用途</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">登录令牌</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">有效期 7 天的 JWT 字符串</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">维持登录状态，免除重复登录</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">用户信息缓存</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">用户名、邮箱、签名、头像标识、角色</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">离线展示个人资料，减少请求</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">主题偏好</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">您所选配色方案的标识</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">下次打开时保持您的界面配色</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">公告已读标记</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">公告 ID 与已读时的版本时间</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">避免重复展示已读公告</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">指纹登录相关（仅 App）</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">本地生成的设备标识 UUID、加密后的生物识别凭证、开关状态</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">支持指纹一键登录；设备标识会随登录请求上传用于绑定校验</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">新手引导标记</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">是否已完成引导</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">避免重复弹出新手引导</text>
              </view>
            </view>
          </scroll-view>

          <text class="privacy-page__para">本产品<text class="privacy-page__em">不使用任何广告类、追踪类 Cookie 或第三方数据分析代码</text>，不进行跨站/跨应用追踪，不构建用户画像，不做个性化广告推送。您可通过退出登录或清除应用数据（小程序端为"删除小程序"，App 端为系统设置中的"清除数据"）删除上述本地数据，删除后需重新登录。</text>
        </view>

        <!-- 五、我们如何共享您的信息 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">五、我们如何共享、转让、公开披露您的信息</text>
          <text class="privacy-page__para"><text class="privacy-page__em">我们不会向任何第三方出售您的个人信息，也不会将其用于本政策未载明的用途。</text>为实现本产品的基本运行与您主动选择的功能，我们仅在必要范围内与以下第三方共享必要信息。共享的第三方及其收集的信息类型如下：</text>

          <!-- 第三方共享信息表格（横向滚动，避免窄屏截断） -->
          <scroll-view scroll-x class="privacy-page__table-scroll">
            <view class="privacy-page__table">
              <view class="privacy-page__table-row privacy-page__table-row--header">
                <text class="privacy-page__table-cell privacy-page__table-cell--name">第三方名称</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info">涉及个人信息</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose">使用目的与说明</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">DCloud uni-app 引擎
（数字天堂 · 北京网络技术有限公司）</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">设备唯一识别码（IMEI、Android ID、DEVICE_ID、IDFA）、OAID、SIM 卡 IMSI、网络状态、应用启动数据与异常错误日志</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">提供应用运行框架支持，进行统计分析、性能优化与故障排查。隐私政策：dcloud.io/license/appprivacy.html</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">友盟+ U-Push 消息推送 SDK
（友盟同欣（北京）科技有限公司）
仅 App 端（Android／iOS／HarmonyOS）且您开启 App 推送后</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">设备信息（Android ID、IDFA、IDFV、OAID、OpenUDID、GUID，可选 IMEI/IMSI/ICCID/MAC）、网络信息、IP 地址、设备推送标识（Device Token）</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">生成并维护设备推送标识，将打卡提醒定向下发到您的设备。我们已关闭其位置信息与应用列表采集。隐私政策：umeng.com/page/policy</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">微信（腾讯）开放平台
仅微信小程序端</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">登录临时凭证 code、OpenID、订阅消息模板内容（含计划名称等提醒文案）</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">实现微信一键登录与订阅消息下发。此外微信平台自身收集的信息适用其《微信隐私保护指引》</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">您自行指定的邮件服务商
仅您开启邮件提醒后</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">您的收件邮箱地址、邮件正文（含计划名称、备注、提醒时间等）</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">通过您填写的 SMTP 服务器投递提醒邮件。该服务商由您自行选择，其信息处理适用其自身隐私政策</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">腾讯企业邮 SMTP
仅注册/找回密码时</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">您填写的邮箱地址、验证码邮件内容</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">向您发送注册、找回密码、变更邮箱所需的一次性验证码</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">手机厂商推送通道
（华为/荣耀/小米/OPPO/vivo/魅族）
仅 Android 端</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">当前版本<text class="privacy-page__em">未配置启用，不向厂商通道下发消息、不共享任何信息</text></text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">相关代码虽随推送 SDK 一并集成于安装包内，但因未配置厂商密钥而不会运行。如后续版本启用，我们将更新本政策并另行告知</text>
              </view>
              <view class="privacy-page__table-row">
                <text class="privacy-page__table-cell privacy-page__table-cell--name privacy-page__table-cell--data">Google Firebase 云消息（FCM）
仅 Android 端</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--info privacy-page__table-cell--data">设备实例标识、网络与设备基础信息</text>
                <text class="privacy-page__table-cell privacy-page__table-cell--purpose privacy-page__table-cell--data">随推送 SDK 集成于安装包，但本产品<text class="privacy-page__em">未配置启用且已关闭其自动初始化</text>，不会向境外 Google 服务器传输任何信息。隐私政策：firebase.google.com/support/privacy</text>
              </view>
            </view>
          </scroll-view>

          <text class="privacy-page__para">对于共享个人信息的第三方，我们会与其约定严格的数据保护义务，要求其按照本政策以及相应保密和安全措施来处理个人信息，不得将其用于任何其他用途。</text>
          <text class="privacy-page__para"><text class="privacy-page__em">转让：</text>我们不会将您的个人信息转让给任何公司、组织和个人，但因合并、分立、解散、被宣告破产等原因需要转让的除外。届时我们会要求接收方继续受本政策约束，否则将要求其重新征得您的授权同意。</text>
          <text class="privacy-page__para"><text class="privacy-page__em">公开披露：</text>我们不会公开披露您的个人信息，但取得您明确同意或依据法律法规、行政/司法机关强制性要求的情形除外。</text>
          <text class="privacy-page__para">此外，根据法律法规规定，在下列情形中我们可能会共享、转让、公开披露您的个人信息而无需事先征得您的授权同意：与国家安全、国防安全直接相关的；与公共安全、公共卫生、重大公共利益直接相关的；与犯罪侦查、起诉、审判和判决执行等直接相关的；出于维护您或其他个人的生命、财产等重大合法权益但又很难得到本人同意的；您自行向社会公众公开的；从合法公开披露的信息中收集的。</text>
        </view>

        <!-- 六、我们如何存储和保护您的信息 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">六、我们如何存储和保护您的信息</text>

          <text class="privacy-page__sub-title">1. 存储地点</text>
          <text class="privacy-page__para">本产品的服务器与数据库<text class="privacy-page__em">均位于中华人民共和国境内</text>。无论您身处何地，您的账号信息、打卡计划与打卡记录等个人信息都将存储和处理于中国境内。</text>
          <text class="privacy-page__para"><text class="privacy-page__em">若您在中国境外使用本产品（包括通过 Google Play 下载的版本），请您在使用前特别注意：</text>您的个人信息将被传输至中国境内并在中国境内接受处理，中国的数据保护法律制度可能与您所在国家或地区的法律制度存在差异。<text class="privacy-page__em">您继续注册与使用本产品，即表示您已知悉并同意这一跨境传输安排</text>。如您不接受，请勿注册或使用本产品。</text>
          <text class="privacy-page__para">我们不会主动将您的个人信息传输至中国境外的第三方。Android 端集成的 Google Firebase 云消息（FCM）推送通道<text class="privacy-page__em">未启用</text>（相关密钥为空，且我们已在应用内关闭其自动初始化），因此不会向境外 Google 服务器传输任何设备标识或个人信息。如未来因业务需要确需向境外提供个人信息，我们将事先取得您的单独同意，并履行相关法律法规规定的安全评估、认证或合同备案等程序。</text>

          <text class="privacy-page__sub-title">2. 存储期限</text>
          <text class="privacy-page__para">我们仅在实现本政策所述目的所必需的最短期间内保留您的个人信息：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">账号信息、计划与打卡记录：在您的账号存续期间持续保留，以便您随时查阅历史记录；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">邮箱验证码：仅在有效期内临时保存，校验完成或超时后立即失效；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">登录令牌：有效期 7 天；生物识别登录凭证：有效期 31 天，到期自动失效；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">设备推送标识：连续推送失败达 3 次后自动剔除该设备；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">您注销账号后：我们将在 24 小时冷静期届满后彻底删除您的全部数据（详见第七条第 5 项）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">访问日志：服务器在处理请求时会记录访问 IP 与时间，用于安全防护与故障排查；用于接口频率限制的 IP 记录仅在内存中保留 60 秒，不写入数据库；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">法律法规另有强制保存期限规定的，从其规定；超出保存期限后我们将予以删除。</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">3. 安全措施</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">传输加密：客户端与服务器之间的全部通信均通过 HTTPS（TLS）加密信道进行；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">存储加密：登录密码采用 bcrypt 加盐哈希不可逆存储；邮箱客户端密码等敏感凭据采用 AES-256-GCM 加密存储；生物识别凭证在设备端二次加密；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">访问控制：所有涉及个人数据的接口均需携带有效身份令牌，并在服务端以用户 ID 严格隔离数据，确保您只能访问自己的数据；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">输出脱敏：接口响应会自动剔除密码哈希、会话密钥、设备推送标识原文等敏感字段；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">风控措施：对注册、登录、发送验证码、重置密码等敏感接口实施频率限制，防范撞库与暴力破解；改密、重置密码、退出登录、注销账号后既有令牌立即失效；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">最小化原则：我们仅收集实现功能所必需的最少信息，且不做用户画像与自动化决策。</text>
            </view>
          </view>
          <text class="privacy-page__para">请您理解，互联网并非绝对安全的环境。请您妥善保管账号密码与验证码，不要向任何人透露。如不幸发生个人信息安全事件，我们将按法律法规要求，及时以推送通知、站内信或公告等方式将事件基本情况、可能影响、已采取的处置措施及您可自主防范的建议告知您，并按规定向监管部门报告。</text>
        </view>

        <!-- 七、您的权利 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">七、您的权利</text>
          <text class="privacy-page__para">按照《中华人民共和国个人信息保护法》等法律法规，您对您的个人信息享有以下权利，我们已在产品中为您提供便捷的行使途径：</text>

          <text class="privacy-page__sub-title">1. 知情权与决定权</text>
          <text class="privacy-page__para">您有权知悉并决定我们对您个人信息的处理方式，有权限制或者拒绝他人对您个人信息的处理。您可以随时通过本页面查阅本政策全文。</text>

          <text class="privacy-page__sub-title">2. 查阅与复制</text>
          <text class="privacy-page__para">您可以在「设置 - 个人信息」中查看您的用户名、邮箱、签名与头像；在「制定计划」中查看全部计划配置；在「打卡记录」中按日历查看全部历史打卡；在「站内信」中查看历史提醒记录。本产品暂未提供一键导出功能；如您需要以副本形式获取上述信息，请通过文末邮箱联系我们，我们将在核验身份后于十五个工作日内以电子文件形式向您提供。</text>

          <text class="privacy-page__sub-title">3. 更正与补充</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">用户名、个性签名、头像：在「设置 - 个人信息」中随时修改；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">密码：在「设置 - 个人信息」中修改；忘记密码可通过邮箱验证码重置；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">邮箱：在「设置 - 个人信息」中变更（需通过原邮箱与新邮箱两步验证）；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">计划与提醒配置：在「制定计划」与「通知方式」中随时增删改。</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">4. 删除</text>
          <text class="privacy-page__para">您可以在产品内自行删除单个打卡计划（同时删除其提醒时间点与渠道绑定）、删除通知渠道配置、清空或标记站内信。在处理目的已实现、我们停止提供服务、您撤回同意或我们违法处理个人信息等情形下，您有权要求我们删除您的个人信息；我们未删除的，您可以请求删除。</text>

          <text class="privacy-page__sub-title">5. 注销账号与删除数据</text>
          <text class="privacy-page__para">您可以通过以下<text class="privacy-page__em">任一途径</text>自助申请注销账号并删除全部数据，两条途径效果完全相同：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text"><text class="privacy-page__em">应用内：</text>打开本产品，进入「设置 - 个人信息」页面，点击底部的「删除账号」；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text"><text class="privacy-page__em">网页端：</text>无需安装应用，直接访问 yao.wuzuniao.com/pages/user/profile ，登录后点击「删除账号」即可。关于账号删除与数据处理的详细说明（含免登录访问）见 yao.wuzuniao.com/pages/user/delete-account 。</text>
            </view>
          </view>
          <text class="privacy-page__para">申请提交后：</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">您的账号立即被冻结，全部登录令牌立即失效，服务端的<text class="privacy-page__em">生物识别登录凭证当即被删除</text>；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">系统提供 <text class="privacy-page__em">24 小时冷静期</text>，期间您可以重新登录并撤销注销申请，撤销后账号恢复正常；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">冷静期届满后，后台任务将从数据库中<text class="privacy-page__em">物理删除</text>以下全部数据且不可恢复：账号主记录（用户名、邮箱、密码哈希、个性签名、头像标识）、微信绑定关系（OpenID）、全部打卡计划及其提醒时间点与渠道绑定、全部打卡记录、全部通知渠道配置（含加密的邮箱密码与设备推送标识）、全部通知发送记录；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">删除为直接物理删除，<text class="privacy-page__em">我们不保留您数据的备份副本或匿名化残留</text>；仅服务器访问日志中可能残留请求 IP 与时间戳，该日志不含您的账号内容。</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">6. 撤回同意</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">您可在「通知方式」中随时关闭或删除邮件、微信、App 推送等渠道；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">您可在手机系统设置中关闭本应用的通知、指纹等权限；也可在微信「设置 - 通用 - 授权管理」中取消小程序订阅消息授权；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">撤回同意不影响撤回前基于同意已进行的个人信息处理活动的效力，但可能导致相应功能无法继续使用。</text>
            </view>
          </view>

          <text class="privacy-page__sub-title">7. 解释权与逝者近亲属权利</text>
          <text class="privacy-page__para">您有权要求我们对本政策及个人信息处理规则进行解释说明。自然人死亡的，其近亲属为了自身合法、正当的利益，可以对死者的相关个人信息行使查阅、复制、更正、删除等权利，但死者生前另有安排的除外。</text>

          <text class="privacy-page__sub-title">8. 响应时限</text>
          <text class="privacy-page__para">如您需通过邮件行使上述权利，请通过文末联系方式与我们沟通。为保障账号安全，我们可能会先核验您的身份。我们将在<text class="privacy-page__em">十五个工作日内</text>予以答复。对于您合理的请求，我们原则上不收取费用；但对多次重复、超出合理限度的请求，我们可能视情收取一定成本费用。若我们决定不予响应，将说明理由。</text>
        </view>

        <!-- 八、未成年人保护 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">八、未成年人保护</text>
          <text class="privacy-page__para">我们非常重视对未成年人个人信息的保护。本产品主要面向成年人。</text>
          <view class="privacy-page__list">
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">若您未满 18 周岁，请务必在监护人陪同下阅读本政策，并在征得监护人明示同意后再使用本产品；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">若您未满 14 周岁，依据《个人信息保护法》，您的个人信息属于敏感个人信息。我们仅在取得您的父母或其他监护人<text class="privacy-page__em">单独同意</text>的前提下处理，并对相关信息采取更严格的保护措施；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">若您位于中国境外，适用您所在国家或地区法律规定的最低同意年龄（例如欧洲经济区为 16 周岁或成员国另行规定的 13 至 16 周岁，美国为 13 周岁）；低于该年龄的，须经父母或监护人同意后方可使用；</text>
            </view>
            <view class="privacy-page__list-item">
              <text class="privacy-page__bullet">·</text>
              <text class="privacy-page__list-text">我们不会有意收集低于前述年龄用户的个人信息。若您是监护人，且发现我们在未取得您同意的情况下收集了相关未成年人的个人信息，请通过文末邮箱联系我们，我们将核实后及时删除。</text>
            </view>
          </view>
        </view>

        <!-- 九、中国境外用户特别说明 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">九、中国境外用户特别说明</text>
          <text class="privacy-page__para">本产品面向全球用户提供，并通过 Google Play 等应用商店分发。<text class="privacy-page__em">我们的服务器与数据库位于中华人民共和国境内</text>，因此若您在中国境外使用本产品，您的个人信息将被传输至中国境内并在中国境内存储和处理。</text>

          <text class="privacy-page__sub-title">1. 跨境传输的法律依据</text>
          <text class="privacy-page__para">我们处理您个人信息的法律依据是<text class="privacy-page__em">履行与您之间的服务合同所必需</text>（提供打卡提醒与记录服务），以及在您主动开启邮件提醒、App 推送等可选功能时您所给予的<text class="privacy-page__em">明确同意</text>。您在注册时勾选同意本政策，即构成对上述跨境传输安排的知情同意。</text>
          <text class="privacy-page__para">您理解并知悉：中国的数据保护法律制度可能与您所在国家或地区（例如欧洲经济区、英国、美国等）的法律制度存在差异，中国目前<text class="privacy-page__em">未被欧盟委员会认定为具有充分保护水平的国家</text>。尽管如此，我们仍按照本政策第六条所述的加密传输、加密存储、访问隔离与最小化收集等措施保护您的个人信息。</text>

          <text class="privacy-page__sub-title">2. 您可行使的权利</text>
          <text class="privacy-page__para">无论您身处何地，您均可行使本政策第七条所列的全部权利，包括查阅、复制、更正、删除个人信息，撤回同意，以及<text class="privacy-page__em">随时自助注销账号并彻底删除全部数据</text>。若您位于欧洲经济区或英国，您还享有数据可携权，以及向您所在国家/地区数据保护监管机构投诉的权利。行使方式与响应时限见第七条。</text>

          <text class="privacy-page__sub-title">3. 如您不接受跨境传输</text>
          <text class="privacy-page__para">个人信息传输并存储至中国境内是本产品运行所必需，我们目前<text class="privacy-page__em">无法提供境外本地化存储的替代方案</text>。如您不接受这一安排，请勿注册或使用本产品；您也可以基于本项目的开源代码自行部署到您所在地区的服务器（详见第十条）。</text>
        </view>

        <!-- 十、开源与自建部署说明 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">十、开源与自建部署说明</text>
          <text class="privacy-page__para">本产品为开源项目。本政策仅适用于由「无足鸟」团队官方运营的服务实例。若第三方基于本项目源代码自行部署、修改并对外提供服务，其个人信息处理行为由该第三方独立负责，与我们无关，亦不适用本政策，请您以该服务提供者公示的隐私政策为准。</text>
        </view>

        <!-- 十一、本政策的更新 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">十一、本政策的更新</text>
          <text class="privacy-page__para">我们可能适时修订本政策。未经您明确同意，我们不会削减您按照本政策所应享有的权利。</text>
          <text class="privacy-page__para">对于重大变更（例如：服务模式发生重大变化；个人信息的收集范围、处理目的、使用方式发生变化；共享的第三方发生变更；您行使权利的方式发生重大变化；个人信息安全负责人及联系方式变更等），我们将通过应用内的显著弹窗、公告或站内信等方式向您显著告知，并在必要时重新征求您的同意。您继续使用本产品即视为接受修订后的政策。</text>
        </view>

        <!-- 十二、如何联系我们 -->
        <view class="privacy-page__section">
          <text class="privacy-page__section-title">十二、如何联系我们</text>
          <text class="privacy-page__para">如您对本政策有任何疑问、意见、建议或投诉，或需要行使个人信息相关权利，请通过以下方式联系我们：</text>
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
          <text class="privacy-page__para">我们将在十五个工作日内回复您的问题。如您对我们的回复不满意，特别是认为我们的个人信息处理行为损害了您的合法权益，您可以向网信、电信、公安及市场监管等主管部门投诉举报，或向有管辖权的人民法院提起诉讼；<text class="privacy-page__em">若您位于中国境外</text>，您还可以向您所在国家或地区的数据保护监管机构投诉。</text>
          <text class="privacy-page__para privacy-page__para--footer">本政策自公示之日起生效。</text>
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

useShare({ title: '隐私政策' })
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
