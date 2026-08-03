# xtf-umengpush

`xtf-umengpush` 是一个面向 `uni-app` / `uni-app x` 的友盟推送插件，当前重点支持 App 端的 `Android`、`iOS`、`Harmony`。

这份文档重点解决 4 件事：

- 如何配置 Android、iOS、鸿蒙三端参数
- 如何在 `uni-app` 和 `uni-app x` 中初始化与监听推送
- 每个公开方法怎么调用，哪些写法可以合并
- Android、iOS、鸿蒙每一端有哪些必须提前知道的注意事项

## 支持范围

| 平台 | 支持情况 | 说明 |
| --- | --- | --- |
| `uni-app` App Android | 支持 | 适合友盟主链路和厂商通道联调 |
| `uni-app` App iOS | 支持 | 依赖 APNs 能力、证书和签名环境 |
| `uni-app` App Harmony | 支持 | 依赖鸿蒙 `AbilityStage` 预初始化 |
| `uni-app x` App Android | 支持 | 推荐优先使用 |
| `uni-app x` App iOS | 支持 | 推荐配合真机和自定义基座验证 |
| `uni-app x` App Harmony | 支持 | 需要按本文档配置 `resources/rawfile/umconfig.json` |
| H5 / 各类小程序 | 不支持 | 本插件当前不是这些端的推送方案 |

## 文档约定

- 如果 `uni-app` 和 `uni-app x` 的方法调用完全一致，这里只写一份“通用写法”
- 如果两者只是脚本语言不同，文档会同时给 `uni-app` 和 `uni-app x` 两段示例
- 本插件公开 API 主要是同步调用 + 监听回调，页面里更适合放在 `onLoad` / `onUnload`、`onMounted` / `onUnmounted` 或 `App` 生命周期中使用
- 事件监听目前是“单监听器模型”：同一类事件只保留最后一次注册的那个回调，新注册会覆盖旧注册

## 目录结构与配置文件

### Android / iOS 统一配置文件

项目主要通过下面这个文件维护 Android / iOS / 厂商通道配置：

- Android：`uni_modules/xtf-umengpush/utssdk/app-android/assets/umeng-push-config.json`
- iOS：`uni_modules/xtf-umengpush/utssdk/app-ios/Resources/umeng-push-config.json`

说明：

- 插件根目录下旧的 `umeng-push-config.json`、`umeng-push-config.uts`、`umconfig.json` 已删除
- 现在不再从插件根目录读取配置，而是每个平台直接读取自己的资源文件
- 业务代码统一从 `@/uni_modules/xtf-umengpush` 导入 `createUmengPushInitOptions()`，不再从旧的 `/umeng-push-config` 入口导入
- 如果修改了 Android `assets/umeng-push-config.json` 中的内容，需要重新打 Android 自定义基座或重新安装新的运行包，旧基座里的 assets 不会自动更新
- 如果修改了 iOS `Resources/umeng-push-config.json` 中的内容，普通授权基座、试用基座、自定义基座都需要重新打包或重新重签后再安装，已安装基座里的 bundle 资源不会自动更新

主要字段：

- `android`：Android 包名、渠道、最低版本等
- `ios`：iOS `bundleId`、渠道、APNs 环境说明
- `android_umeng`：Android 友盟 `appKey`、`messageSecret`
- `ios_umeng`：iOS 友盟 `appKey`、`messageSecret`
- `vendors`：华为、荣耀、小米、OPPO、vivo、魅族、FCM 等厂商参数
- `advanced`：前台展示、通知角标、自定义资源、通知渠道名等高级配置

### 鸿蒙唯一维护源

鸿蒙配置只维护这一份：

- `uni_modules/xtf-umengpush/utssdk/app-harmony/resources/rawfile/umconfig.json`

这个文件当前承载：

- `bundleName`
- `appName`
- `channel`
- `appKey`
- `appMessageSecret`
- `debug`

说明：

- 鸿蒙端只维护这一份配置源
- 插件初始化会直接读取 rawfile 里的 `umconfig.json`

### 鸿蒙桥接文件说明

下面两个路径都不是新的独立配置源：

- `harmony-configs/AppScope/resources/rawfile/umconfig.json`

说明：

- `harmony-configs/AppScope/resources/rawfile/umconfig.json` 仅供鸿蒙应用级 rawfile 读取
- 鸿蒙插件配置以 `utssdk/app-harmony/resources/rawfile/umconfig.json` 为准
- 不要把它们改成另一份独立内容，否则后续很容易出现编译通过但配置不一致的问题

## 快速开始

### 1. 先填配置

至少先补这些字段：

- Android：`android.applicationId`、`android_umeng.appKey`、`android_umeng.messageSecret`
- iOS：`ios.bundleId`、`ios_umeng.appKey`、`ios_umeng.messageSecret`
- Harmony：`utssdk/app-harmony/resources/rawfile/umconfig.json` 中的 `appKey`、`appMessageSecret`、`channel`

iOS 特别注意：

- `umeng-push-config.json` 里的 `ios.apsEnvironment` 只是配置说明字段，不会给应用增加 `aps-environment` entitlement
- 真正决定 APNs 能否注册成功的是 Apple Developer 后台 capability、Provisioning Profile 和重签后的运行包 entitlements

鸿蒙特别注意：

- `appMessageSecret` 必须填写友盟后台的 `Umeng Message Secret`
- 不能误填 `App Master Secret`

### 2. 在 `App` 生命周期里初始化

#### `uni-app` 示例

```vue
<script>
import {
  initializeUmengPush,
  requestNotificationPermission
} from '@/uni_modules/xtf-umengpush'
import { createUmengPushInitOptions } from '@/uni_modules/xtf-umengpush'

export default {
  onLaunch() {
    const initResult = initializeUmengPush(createUmengPushInitOptions())
    console.log('友盟初始化结果', initResult)

    requestNotificationPermission({
      success(res) {
        console.log('通知权限申请成功', res)
      },
      fail(err) {
        console.error('通知权限申请失败', err)
      }
    })
  }
}
</script>
```

#### `uni-app x` 示例

```vue
<script setup lang="uts">
import {
  initializeUmengPush,
  requestNotificationPermission
} from '@/uni_modules/xtf-umengpush'
import { createUmengPushInitOptions } from '@/uni_modules/xtf-umengpush'

onLaunch(() => {
  const initResult = initializeUmengPush(createUmengPushInitOptions())
  console.log('友盟初始化结果', initResult)

  requestNotificationPermission({
    success: (res) => {
      console.log('通知权限申请成功', res)
    },
    fail: (err) => {
      console.error('通知权限申请失败', err)
    }
  })
})
</script>
```

### 3. 在页面里监听消息与运行时事件

#### `uni-app` 示例

```vue
<script>
import {
  onUmengPushMessage,
  offUmengPushMessage,
  onUmengPushRuntimeEvent,
  offUmengPushRuntimeEvent
} from '@/uni_modules/xtf-umengpush'

export default {
  data() {
    return {
      pushMessageListenerId: null,
      runtimeEventListenerId: null
    }
  },
  onLoad() {
    this.pushMessageListenerId = onUmengPushMessage((message) => {
      console.log('收到正式消息', message)
    })

    this.runtimeEventListenerId = onUmengPushRuntimeEvent((event) => {
      console.log('收到运行时事件', event)
    })
  },
  onUnload() {
    if (this.pushMessageListenerId != null) {
      offUmengPushMessage(this.pushMessageListenerId)
      this.pushMessageListenerId = null
    }
    if (this.runtimeEventListenerId != null) {
      offUmengPushRuntimeEvent(this.runtimeEventListenerId)
      this.runtimeEventListenerId = null
    }
  }
}
</script>
```

#### `uni-app x` 示例

```vue
<script setup lang="uts">
import {
  onUmengPushMessage,
  offUmengPushMessage,
  onUmengPushRuntimeEvent,
  offUmengPushRuntimeEvent
} from '@/uni_modules/xtf-umengpush'

let pushMessageListenerId : number | null = null
let runtimeEventListenerId : number | null = null

onLoad(() => {
  pushMessageListenerId = onUmengPushMessage((message) => {
    console.log('收到正式消息', message)
  })

  runtimeEventListenerId = onUmengPushRuntimeEvent((event) => {
    console.log('收到运行时事件', event)
  })
})

onUnload(() => {
  if (pushMessageListenerId != null) {
    offUmengPushMessage(pushMessageListenerId as number)
    pushMessageListenerId = null
  }
  if (runtimeEventListenerId != null) {
    offUmengPushRuntimeEvent(runtimeEventListenerId as number)
    runtimeEventListenerId = null
  }
})
</script>
```

## 推荐导入方式

### 主插件 API

```js
import {
  initializeUmengPush,
  requestNotificationPermission,
  getPushDeviceInfo,
  refreshLaunchPushClickInfo,
  getLastPushClickInfo,
  clearLastPushClickInfo,
  onUmengPushMessage,
  offUmengPushMessage,
  onUmengPushRuntimeEvent,
  offUmengPushRuntimeEvent,
  getUmengPushDebugState,
  getLastUmengPushOperationState,
  openUmengNotificationSettings,
  enableUmengPush,
  disableUmengPush,
  setUmengPushBadgeNum,
  changeUmengPushBadgeNum,
  addUmengPushTags,
  deleteUmengPushTags,
  getUmengPushTags,
  addUmengPushAlias,
  setUmengPushAlias,
  deleteUmengPushAlias
} from '@/uni_modules/xtf-umengpush'
```

### 配置辅助函数

```js
import {
  createUmengPushInitOptions,
  getUmengPushConfigHint,
  getUmengPushConfigSourceName
} from '@/uni_modules/xtf-umengpush'
```

## 事件模型

### `onUmengPushMessage` 负责什么

它表示“正式消息到达”，常见来源包括：

- Android：通知消息、自定义消息等原生回流
- iOS：前台通知、`AppDelegate` 收到远程通知
- Harmony：通知消息、自定义消息

返回对象 `UmengPushMessage` 关键字段：

- `source`：消息来源字符串，例如 `foreground-notification`、`custom-message`
- `title`：标题
- `body`：正文
- `payload`：原始 JSON 文本或拼装后的载荷文本
- `receivedAt`：接收时间戳

### `onUmengPushRuntimeEvent` 负责什么

它表示“运行时状态事件”，当前 `type` 主要包括：

- `register-state`：注册状态变化
- `connect-state`：连接状态变化
- `inapp-message`：应用内消息或相关事件
- `notification-click`：点击通知
- `notification-dismiss`：通知被删除或关闭

其中 `action` 可能出现：

- `onShow`
- `onClick`
- `onDismiss`
- `replay`
- `will-present`

说明：

- Android 事件最完整
- iOS 当前 `notification-dismiss` 只能尽量对齐，不保证与 Android 完全等价
- Harmony 当前没有和 Android 完全对等的通知删除事件集合，部分能力只能 best-effort

## 公开方法详解

下面按“配置辅助 -> 初始化 -> 状态读取 -> 监听 -> 操作接口”的顺序说明。

### 1. `createUmengPushInitOptions()`

用途：

- 从插件配置文件自动生成当前平台可直接传给 `initializeUmengPush` 的参数

通用写法：

```js
import { createUmengPushInitOptions } from '@/uni_modules/xtf-umengpush'

const options = createUmengPushInitOptions()
console.log('初始化参数', options)
```

适合场景：

- 配置都写在插件配置文件里，不想在业务代码手写 `appKey`、`messageSecret`

平台注意事项：

- Android 会读取 `uni_modules/xtf-umengpush/utssdk/app-android/assets/umeng-push-config.json`
- iOS 会读取 `uni_modules/xtf-umengpush/utssdk/app-ios/Resources/umeng-push-config.json`
- Harmony 会读取 `uni_modules/xtf-umengpush/utssdk/app-harmony/resources/rawfile/umconfig.json`

### 2. `getUmengPushConfigHint()`

用途：

- 获取当前插件建议填写的配置提示文案

通用写法：

```js
import { getUmengPushConfigHint } from '@/uni_modules/xtf-umengpush'

console.log(getUmengPushConfigHint())
```

适合场景：

- 在调试页、空状态页提示开发同学先补配置

### 3. `getUmengPushConfigSourceName()`

用途：

- 获取当前平台实际使用的配置源路径文案

通用写法：

```js
import { getUmengPushConfigSourceName } from '@/uni_modules/xtf-umengpush'

console.log('当前配置源', getUmengPushConfigSourceName())
```

平台注意事项：

- Android 返回 `uni_modules/xtf-umengpush/utssdk/app-android/assets/umeng-push-config.json`
- iOS 返回 `uni_modules/xtf-umengpush/utssdk/app-ios/Resources/umeng-push-config.json`
- Harmony 返回 `uni_modules/xtf-umengpush/utssdk/app-harmony/resources/rawfile/umconfig.json`

### 4. `initializeUmengPush(options)`

用途：

- 初始化友盟推送主链路
- 读取注册状态、DeviceToken、RegistrationId、最近一次启动点击信息

#### 通用写法

```js
import { initializeUmengPush } from '@/uni_modules/xtf-umengpush'
import { createUmengPushInitOptions } from '@/uni_modules/xtf-umengpush'

const result = initializeUmengPush(createUmengPushInitOptions())
console.log('初始化结果', result)
```

#### 手写参数示例

```js
import { initializeUmengPush } from '@/uni_modules/xtf-umengpush'

const result = initializeUmengPush({
  androidPackageName: 'uni.app.demo',
  appKey: '你的友盟 appKey',
  messageSecret: '你的友盟 messageSecret',
  channel: 'official',
  debug: true,
  vendorConfigs: [],
  advancedOptions: {
    notificationOnForeground: true,
    displayNotificationNumber: 5,
    resourcePackageName: null,
    pushCheck: true,
    smartEnable: false,
    muteDurationSeconds: 0,
    noDisturbMode: {
      enabled: false,
      startHour: 23,
      startMinute: 0,
      endHour: 7,
      endMinute: 0
    },
    playSoundMode: 'server',
    playLightsMode: 'server',
    playVibrateMode: 'server',
    notificationChannelName: null,
    notificationSilenceChannelName: null,
    customNotificationStyleEnabled: false,
    customMessageServiceEnabled: false,
    smallIconResourceName: null,
    largeIconResourceName: null,
    soundResourceName: null
  }
})
```

返回结果 `UmengPushInitResult` 重点字段：

- `success`：本次初始化调用是否成功触发
- `initialized`：当前插件是否已经完成初始化
- `isConfigured`：参数是否完整
- `registered`：是否注册成功
- `deviceToken`：设备 token
- `registrationId`：友盟注册 id
- `registerErrorCode` / `registerErrorMessage`：注册失败时的原生错误
- `missingKeys`：缺少的关键配置项
- `clickInfo`：启动点击信息

平台注意事项：

- Android：厂商参数不完整时，友盟主体初始化可能成功，但对应厂商通道不会正常工作
- iOS：是否真正拿到 APNs token 还取决于 `Push Notifications` capability、`aps-environment` 和签名环境
- iOS：修改 `umeng-push-config.json` 中的 `apsEnvironment` 不会修复 entitlement 缺失；如果日志提示“未找到应用程序的 `aps-environment` 授权字符串”，应检查证书、描述文件和重签基座
- Harmony：如果窗口还没就绪，可能先返回 `UMENG_PUSH_INIT_DEFERRED`，随后延迟到窗口阶段完成初始化，这属于正常行为

### 5. `requestNotificationPermission(options)`

用途：

- 申请或检查通知权限

#### 通用写法

```js
import { requestNotificationPermission } from '@/uni_modules/xtf-umengpush'

requestNotificationPermission({
  success(res) {
    console.log('通知权限结果', res)
  },
  fail(err) {
    console.error('通知权限失败', err)
  },
  complete(res) {
    console.log('通知权限 complete', res)
  }
})
```

返回结果 `UmengPushPermissionResult` 重点字段：

- `granted`：是否授权
- `requested`：本次是否真的发起了系统权限弹窗
- `notificationEnabled`：系统通知开关是否开启
- `permission`：权限名
- `sdkInt`：当前系统版本标识

平台注意事项：

- Android：Android 13+ 会处理 `POST_NOTIFICATIONS`，低版本可能直接返回“无需单独申请”
- iOS：用户拒绝后，插件会通过 `fail` 回调表现出来，后续通常需要引导用户去系统设置开启
- Harmony：需要先完成插件初始化再申请，否则可能直接失败

### 6. `getPushDeviceInfo()`

用途：

- 获取当前设备、通知权限、系统通知开关和预期支持厂商列表

通用写法：

```js
import { getPushDeviceInfo } from '@/uni_modules/xtf-umengpush'

const deviceInfo = getPushDeviceInfo()
console.log('设备信息', deviceInfo)
```

返回结果 `UmengPushDeviceInfo` 重点字段：

- `brand`
- `manufacturer`
- `model`
- `packageName`
- `notificationPermissionGranted`
- `systemNotificationEnabled`
- `supportedVendors`

### 7. `refreshLaunchPushClickInfo()`

用途：

- 主动刷新“最近一次通知点击信息”缓存

通用写法：

```js
import { refreshLaunchPushClickInfo } from '@/uni_modules/xtf-umengpush'

const clickInfo = refreshLaunchPushClickInfo()
console.log('最新点击信息', clickInfo)
```

适合场景：

- 页面打开后，想立即确认当前 App 是否是被通知点击拉起的

### 8. `getLastPushClickInfo()`

用途：

- 读取插件内当前缓存的最近一次点击信息，不强制刷新原生侧

通用写法：

```js
import { getLastPushClickInfo } from '@/uni_modules/xtf-umengpush'

const clickInfo = getLastPushClickInfo()
console.log('缓存点击信息', clickInfo)
```

### 9. `clearLastPushClickInfo()`

用途：

- 清空最近一次通知点击缓存

通用写法：

```js
import { clearLastPushClickInfo } from '@/uni_modules/xtf-umengpush'

const cleared = clearLastPushClickInfo()
console.log('是否清空成功', cleared)
```

适合场景：

- 调试页反复验证点击回流时，希望每次从空状态开始

### 10. `onUmengPushMessage(callback)`

用途：

- 监听正式消息到达
- 返回监听器 id，后续用 `offUmengPushMessage` 注销

通用写法：

```js
import { onUmengPushMessage } from '@/uni_modules/xtf-umengpush'

const listenerId = onUmengPushMessage((message) => {
  console.log('正式消息', message)
  console.log('消息来源', message.source)
  console.log('原始载荷', message.payload)
})
```

平台注意事项：

- Android：通知消息、自定义消息都可能进入这里，具体取决于友盟消息类型和原生回调路径
- iOS：前台通知与 `AppDelegate` 收到的远程通知已经接通到这里
- Harmony：通知消息与自定义消息都会回流到这里
- 当前同一时刻只保留一个消息监听器，新注册会覆盖旧注册

### 11. `offUmengPushMessage(listenerId)`

用途：

- 注销 `onUmengPushMessage` 返回的监听器

通用写法：

```js
import { offUmengPushMessage } from '@/uni_modules/xtf-umengpush'

const removed = offUmengPushMessage(listenerId)
console.log('注销消息监听结果', removed)
```

注意事项：

- 必须传入 `onUmengPushMessage` 返回的那个 `listenerId`
- 传错 id 会返回 `false`

### 12. `onUmengPushRuntimeEvent(callback)`

用途：

- 监听注册状态、连接状态、通知点击、通知删除、应用内消息等运行时事件

通用写法：

```js
import { onUmengPushRuntimeEvent } from '@/uni_modules/xtf-umengpush'

const listenerId = onUmengPushRuntimeEvent((event) => {
  console.log('运行时事件', event)

  if (event.type === 'register-state') {
    console.log('注册状态变化', event.registered, event.deviceToken)
  }

  if (event.type === 'notification-click') {
    console.log('通知点击 payload', event.payload)
  }

  if (event.type === 'inapp-message') {
    console.log('应用内消息动作', event.action)
  }
})
```

平台注意事项：

- Android：事件类型最完整，最适合作为联调主参考
- iOS：`notification-dismiss` 能力存在系统侧限制，不要假设一定与 Android 完全一致
- Harmony：`connect-state` 可能保持未知，通知删除事件也不如 Android 完整
- 当前同一时刻只保留一个 runtime event 监听器，新注册会覆盖旧注册

### 13. `offUmengPushRuntimeEvent(listenerId)`

用途：

- 注销 `onUmengPushRuntimeEvent` 返回的监听器

通用写法：

```js
import { offUmengPushRuntimeEvent } from '@/uni_modules/xtf-umengpush'

const removed = offUmengPushRuntimeEvent(listenerId)
console.log('注销运行时事件监听结果', removed)
```

### 14. `getUmengPushDebugState()`

用途：

- 读取当前调试态快照，适合做诊断面板

通用写法：

```js
import { getUmengPushDebugState } from '@/uni_modules/xtf-umengpush'

const debugState = getUmengPushDebugState()
console.log('调试态', debugState)
```

返回结果 `UmengPushDebugState` 重点字段：

- `initialized`
- `isConfigured`
- `registered`
- `connectStateOnline`
- `deviceToken`
- `registrationId`
- `registerErrorCode`
- `registerErrorMessage`
- `vendorTokenSnapshot`
- `lastReceivedPushPayload`
- `lastInAppMessagePayload`
- `deviceInfo`
- `clickInfo`

适合场景：

- 联调页面一屏展示所有关键状态
- 排查“为什么注册了但没消息”“为什么点击通知没回流”

### 15. `getLastUmengPushOperationState()`

用途：

- 获取最近一次标签、别名、角标、开关推送等操作的结果快照

通用写法：

```js
import { getLastUmengPushOperationState } from '@/uni_modules/xtf-umengpush'

const state = getLastUmengPushOperationState()
console.log('最近一次操作结果', state)
```

返回结果 `UmengPushOperationState` 重点字段：

- `success`
- `code`
- `message`
- `payload`

### 16. `openUmengNotificationSettings()`

用途：

- 尝试打开系统通知设置页

通用写法：

```js
import { openUmengNotificationSettings } from '@/uni_modules/xtf-umengpush'

const result = openUmengNotificationSettings()
console.log('打开通知设置结果', result)
```

平台注意事项：

- Android：已封装跳转系统通知设置
- iOS：已封装跳转系统通知设置
- Harmony：当前未封装对应设置页跳转，会返回不支持结果，需要用户手动去系统设置开启

### 17. `enableUmengPush()`

用途：

- 开启友盟推送

通用写法：

```js
import { enableUmengPush } from '@/uni_modules/xtf-umengpush'

const result = enableUmengPush()
console.log('开启推送结果', result)
```

注意事项：

- 该接口是推送开关，不等于系统通知权限授权
- 如果系统通知关闭，开启推送也不代表通知一定会显示

### 18. `disableUmengPush()`

用途：

- 关闭友盟推送

通用写法：

```js
import { disableUmengPush } from '@/uni_modules/xtf-umengpush'

const result = disableUmengPush()
console.log('关闭推送结果', result)
```

### 19. `setUmengPushBadgeNum(num)`

用途：

- 直接把角标设置为指定值

通用写法：

```js
import { setUmengPushBadgeNum } from '@/uni_modules/xtf-umengpush'

const result = setUmengPushBadgeNum(3)
console.log('设置角标结果', result)
```

平台注意事项：

- Android：不同 ROM 对角标支持差异较大
- iOS：角标表现受系统通知和推送载荷影响
- Harmony：请结合真机验证最终桌面角标表现

### 20. `changeUmengPushBadgeNum(num)`

用途：

- 在现有角标基础上增减指定值

通用写法：

```js
import { changeUmengPushBadgeNum } from '@/uni_modules/xtf-umengpush'

const result = changeUmengPushBadgeNum(1)
console.log('变更角标结果', result)
```

### 21. `addUmengPushTags(tags)`

用途：

- 追加标签

通用写法：

```js
import { addUmengPushTags } from '@/uni_modules/xtf-umengpush'

const result = addUmengPushTags(['vip', 'beijing'])
console.log('添加标签结果', result)
```

注意事项：

- 空字符串标签会被过滤
- 建议业务侧自己维护标签命名规范，避免混乱

### 22. `deleteUmengPushTags(tags)`

用途：

- 删除指定标签

通用写法：

```js
import { deleteUmengPushTags } from '@/uni_modules/xtf-umengpush'

const result = deleteUmengPushTags(['vip'])
console.log('删除标签结果', result)
```

### 23. `getUmengPushTags()`

用途：

- 读取当前标签列表

通用写法：

```js
import { getUmengPushTags } from '@/uni_modules/xtf-umengpush'

const result = getUmengPushTags()
console.log('标签读取结果', result)
console.log('标签列表', result.tags)
```

返回结果 `UmengPushTagsResult` 重点字段：

- `success`
- `code`
- `message`
- `tags`

### 24. `addUmengPushAlias(alias, aliasType)`

用途：

- 追加别名

通用写法：

```js
import { addUmengPushAlias } from '@/uni_modules/xtf-umengpush'

const result = addUmengPushAlias('user_1001', 'account')
console.log('追加别名结果', result)
```

### 25. `setUmengPushAlias(alias, aliasType)`

用途：

- 覆盖设置别名

通用写法：

```js
import { setUmengPushAlias } from '@/uni_modules/xtf-umengpush'

const result = setUmengPushAlias('user_1001', 'account')
console.log('设置别名结果', result)
```

适合场景：

- 登录成功后，用账号体系唯一标识覆盖当前设备对应别名

### 26. `deleteUmengPushAlias(alias, aliasType)`

用途：

- 删除指定别名

通用写法：

```js
import { deleteUmengPushAlias } from '@/uni_modules/xtf-umengpush'

const result = deleteUmengPushAlias('user_1001', 'account')
console.log('删除别名结果', result)
```

## `uni-app` 与 `uni-app x` 的推荐写法差异

### 初始化推荐位置

- `uni-app`：推荐放 `App.vue` 的 `onLaunch`
- `uni-app x`：推荐放 `App.uvue` 的 `onLaunch`，Harmony 可在首次 `onAppShow` 做补充联调

### 页面监听推荐位置

- `uni-app`：推荐 `onLoad` 注册、`onUnload` 注销
- `uni-app x`：推荐 `onLoad` 注册、`onUnload` 注销
- 如果页面不会被销毁而只是缓存，也可以按你的页面架构调整到 `onShow` / `onHide`

### 返回值处理方式

- `initializeUmengPush`、`getPushDeviceInfo`、`getUmengPushDebugState` 这类接口适合直接同步读取结果
- `requestNotificationPermission` 采用回调形式，建议同时处理 `success`、`fail`、`complete`
- 标签、别名、角标、开关推送等操作完成后，可以配合 `getLastUmengPushOperationState()` 做统一展示

## Android 端注意事项

- 标准基座下三方原生配置和 SDK 通常不能真实生效，请优先使用自定义基座
- 如果修改了 `uni_modules/xtf-umengpush/utssdk/app-android/assets/umeng-push-config.json`，需要重新打 Android 自定义基座或重新安装新的调试包，单纯热刷新页面不会更新基座内的 assets
- 厂商后台包名、签名必须与当前安装包完全一致
- 华为需要准备 `agconnect-services.json`
- FCM 需要准备 `google-services.json`
- 如果开启 `advanced.customNotificationStyleEnabled = true`，请在宿主 Android 资源中提供：
  - `res/drawable/umeng_push_notification_default_small_icon.png`
  - `res/drawable/umeng_push_notification_default_large_icon.png`
  - `res/raw/umeng_push_notification_default_sound.mp3`
- 如果还要走更接近友盟官方 demo 的自定义消息服务链路，可开启：
  - `advanced.customMessageServiceEnabled = true`
- `AndroidManifest.xml` 中厂商元数据仍需正确保留，例如：
  - `com.huawei.hms.client.appid`
  - `com.hihonor.push.app_id`
  - `com.vivo.push.api_key`
  - `com.vivo.push.app_id`

## iOS 端注意事项

- 必须在 Apple Developer 后台为对应 App ID 开启 `Push Notifications`
- 必须带上正确的 `aps-environment` 能力和匹配的 Provisioning Profile
- `uni_modules/xtf-umengpush/utssdk/app-ios/Resources/umeng-push-config.json` 中的 `ios.apsEnvironment` 仅用于记录当前期望环境，不能替代 iOS entitlements
- 如果修改了 `uni_modules/xtf-umengpush/utssdk/app-ios/Resources/umeng-push-config.json`，普通授权基座、试用基座、自定义基座都需要重新打基座或重新安装新的运行包，单纯重新打开页面不会更新 iOS bundle 资源
- 若运行时看到“未找到应用程序的 `aps-environment` 授权字符串”，这是签名与 capability 问题，不是 JS/UTS 调用问题
- 真正联调 APNs、友盟注册、点击通知回流时，建议使用真机和自定义基座
- `notification-dismiss` 在 iOS 侧只能尽量对齐，不要把它当成强保证事件

## Harmony 端注意事项

- 必须先执行 `harmony-configs/entry/src/main/ets/abilityStage/MyAbilityStage.ets` 里的 `preInit(...)`
- 鸿蒙参数唯一维护文件是：
  - `uni_modules/xtf-umengpush/utssdk/app-harmony/resources/rawfile/umconfig.json`
- 其中 `appMessageSecret` 一定要填 `Umeng Message Secret`
- `openUmengNotificationSettings()` 在鸿蒙端当前未封装系统设置跳转
- Harmony 当前没有和 Android 完全等价的通知删除 / 长连接在线状态体系，相关运行时事件要按“最佳努力”理解
- 普通启动 `want` 与通知点击 `want` 已做区分，但联调时仍建议结合真机日志确认

## 服务端推送 payload 样例

这部分不是友盟 HTTP API 的完整请求包，而是建议你在“通知内容”或“自定义业务字段”里统一携带的业务载荷结构。

建议统一字段：

- `bizType`：业务类型，例如 `order`、`message`、`coupon`
- `bizId`：业务主键，例如订单号、消息 id
- `action`：前端收到后要做什么，例如 `open-page`、`open-webview`
- `route`：要跳转的页面路径
- `data`：业务附加数据对象

### 样例 1：通知消息推荐业务载荷

```json
{
  "title": "订单状态更新",
  "text": "您的订单已发货，点击查看物流详情",
  "payload": {
    "bizType": "order",
    "bizId": "A20260712001",
    "action": "open-page",
    "route": "/pages/order/detail?id=A20260712001",
    "data": {
      "status": "shipped",
      "trackingNo": "SF1234567890"
    }
  }
}
```

说明：

- `title`、`text` 适合作为通知标题和正文
- `payload` 是建议你服务端自行维护的业务对象
- 实际发给友盟时，可以把 `payload` 序列化后放进自定义字段里，例如 Android `extra`、iOS 自定义 `userInfo` 字段、鸿蒙消息扩展字段

### 样例 2：营销通知推荐业务载荷

```json
{
  "title": "会员优惠券到账",
  "text": "你有一张 20 元优惠券待领取",
  "payload": {
    "bizType": "coupon",
    "bizId": "CP20260712088",
    "action": "open-page",
    "route": "/pages/coupon/list",
    "data": {
      "couponId": "CP20260712088",
      "expireAt": "2026-07-31 23:59:59"
    }
  }
}
```

### 样例 3：自定义消息推荐业务载荷

```json
{
  "payload": {
    "bizType": "chat",
    "bizId": "MSG90001",
    "action": "refresh-list",
    "route": "/pages/message/index",
    "data": {
      "conversationId": "C10001",
      "unreadCount": 3
    }
  }
}
```

适合场景：

- 不一定展示系统通知
- 只希望前端收到后刷新列表、弹窗提醒或更新角标

### 服务端组织 payload 的建议

- 尽量三端统一业务字段命名，不要 Android、iOS、Harmony 三套字段完全不同
- `route` 建议直接给前端可用页面路径，减少前端再做复杂映射
- `data` 里只放业务必要字段，避免把整份敏感用户数据塞进通知
- 如果需要多语言，建议服务端分别生成 `title` / `text`，不要让前端收到后再拼装文案

## 前端收到后的字段说明

### `onUmengPushMessage` 回调字段

前端在 `onUmengPushMessage((message) => {})` 中收到的是 `UmengPushMessage`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source` | `string` | 消息来源，例如 `foreground-notification`、`custom-message`、`click-message` |
| `title` | `string \| null` | 标题，部分自定义消息可能为空 |
| `body` | `string \| null` | 正文，部分自定义消息可能为空 |
| `payload` | `string` | 原始载荷字符串，通常建议这里放业务 JSON |
| `receivedAt` | `number` | 接收时间戳 |

常见理解方式：

- `title` / `body` 主要用于展示
- `payload` 主要用于做业务跳转、刷新列表、打开详情页
- 如果你的服务端统一了 `bizType` / `route` / `data`，前端主要解析 `payload`

### `onUmengPushRuntimeEvent` 回调字段

前端在 `onUmengPushRuntimeEvent((event) => {})` 中收到的是 `UmengPushRuntimeEvent`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `type` | `string` | 事件类型：`register-state`、`connect-state`、`inapp-message`、`notification-click`、`notification-dismiss` |
| `receivedAt` | `number` | 事件时间戳 |
| `source` | `string \| null` | 事件来源 |
| `online` | `boolean \| null` | 长连接在线状态，主要用于 `connect-state` |
| `registered` | `boolean \| null` | 是否注册成功，主要用于 `register-state` |
| `action` | `string \| null` | 应用内消息动作，例如 `onShow`、`onClick`、`onDismiss`、`replay`、`will-present` |
| `payload` | `string \| null` | 事件携带的原始 payload |
| `deviceToken` | `string \| null` | 设备 token |
| `registrationId` | `string \| null` | 友盟注册 id |
| `registerErrorCode` | `string \| null` | 注册错误码 |
| `registerErrorMessage` | `string \| null` | 注册错误信息 |
| `message` | `string \| null` | 额外提示信息 |

建议这样理解：

- 想拿正式消息内容，用 `onUmengPushMessage`
- 想拿点击通知、注册状态、连接状态，用 `onUmengPushRuntimeEvent`
- 想排查为什么没收到消息，用 `getUmengPushDebugState()`

## 前端解析 payload 示例

### `uni-app` 示例

```vue
<script>
import { onUmengPushMessage } from '@/uni_modules/xtf-umengpush'

export default {
  onLoad() {
    onUmengPushMessage((message) => {
      let bizPayload = null
      try {
        bizPayload = JSON.parse(message.payload)
      } catch (e) {
        console.warn('payload 不是合法 JSON，按原始文本处理', message.payload)
      }

      if (bizPayload && bizPayload.action === 'open-page' && bizPayload.route) {
        uni.navigateTo({
          url: bizPayload.route
        })
      }
    })
  }
}
</script>
```

### `uni-app x` 示例

```vue
<script setup lang="uts">
import { onUmengPushMessage } from '@/uni_modules/xtf-umengpush'

onLoad(() => {
  onUmengPushMessage((message) => {
    let payloadText = message.payload
    console.log('原始 payload', payloadText)

    // 如果你的服务端统一发送 JSON 文本，可以在这里按你的业务结构继续解析
    // 例如根据 route 做页面跳转，根据 bizType 做列表刷新。
  })
})
</script>
```

## 常见排查顺序

推荐按下面顺序排查：

1. 先看 `initializeUmengPush()` 的 `isConfigured`、`missingKeys`
2. 再看 `requestNotificationPermission()` 的 `granted`、`notificationEnabled`
3. 再看 `getUmengPushDebugState()` 里的 `registered`、`deviceToken`、`registrationId`
4. Android 继续看 `vendorTokenSnapshot`
5. 点击通知时看 `refreshLaunchPushClickInfo()` 和 `onUmengPushRuntimeEvent()`
6. 收到消息但页面没反应时看 `onUmengPushMessage()` 是否已注册且未被覆盖

## 常见问题

### 1. 为什么初始化成功了，但收不到通知？

可能原因：

- 系统通知权限没开
- 系统通知总开关没开
- Android 厂商参数不完整
- iOS APNs 能力或签名不对
- 标准基座下三方 SDK 没真实生效

### 2. 为什么点击通知后页面拿不到 payload？

优先检查：

- 是否调用过 `refreshLaunchPushClickInfo()`
- 是否监听了 `onUmengPushRuntimeEvent()` 并检查 `type === 'notification-click'`
- 是否在页面销毁前就把监听器注销了

### 3. 为什么鸿蒙编译报 `Packages cannot be imported`？

通常是把共享配置直接指到了平台专属资源目录。当前正确做法是：

- 真实鸿蒙配置维护在 `utssdk/app-harmony/resources/rawfile/umconfig.json`
- 共享导入入口已改为各平台从资源目录读取

## 最小联调示例

下面这个例子适合直接放到调试页面，快速验证初始化、权限、消息监听、点击回流：

### `uni-app` 示例

```vue
<script>
import {
  initializeUmengPush,
  requestNotificationPermission,
  onUmengPushMessage,
  offUmengPushMessage,
  onUmengPushRuntimeEvent,
  offUmengPushRuntimeEvent,
  getUmengPushDebugState
} from '@/uni_modules/xtf-umengpush'
import { createUmengPushInitOptions } from '@/uni_modules/xtf-umengpush'

export default {
  data() {
    return {
      messageListenerId: null,
      eventListenerId: null
    }
  },
  onLoad() {
    console.log('初始化结果', initializeUmengPush(createUmengPushInitOptions()))

    requestNotificationPermission({
      success(res) {
        console.log('权限成功', res)
      },
      fail(err) {
        console.error('权限失败', err)
      }
    })

    this.messageListenerId = onUmengPushMessage((message) => {
      console.log('正式消息', message)
    })

    this.eventListenerId = onUmengPushRuntimeEvent((event) => {
      console.log('运行时事件', event)
    })

    console.log('调试态', getUmengPushDebugState())
  },
  onUnload() {
    if (this.messageListenerId != null) {
      offUmengPushMessage(this.messageListenerId)
    }
    if (this.eventListenerId != null) {
      offUmengPushRuntimeEvent(this.eventListenerId)
    }
  }
}
</script>
```

### `uni-app x` 示例

```vue
<script setup lang="uts">
import {
  initializeUmengPush,
  requestNotificationPermission,
  onUmengPushMessage,
  offUmengPushMessage,
  onUmengPushRuntimeEvent,
  offUmengPushRuntimeEvent,
  getUmengPushDebugState
} from '@/uni_modules/xtf-umengpush'
import { createUmengPushInitOptions } from '@/uni_modules/xtf-umengpush'

let messageListenerId : number | null = null
let eventListenerId : number | null = null

onLoad(() => {
  console.log('初始化结果', initializeUmengPush(createUmengPushInitOptions()))

  requestNotificationPermission({
    success: (res) => {
      console.log('权限成功', res)
    },
    fail: (err) => {
      console.error('权限失败', err)
    }
  })

  messageListenerId = onUmengPushMessage((message) => {
    console.log('正式消息', message)
  })

  eventListenerId = onUmengPushRuntimeEvent((event) => {
    console.log('运行时事件', event)
  })

  console.log('调试态', getUmengPushDebugState())
})

onUnload(() => {
  if (messageListenerId != null) {
    offUmengPushMessage(messageListenerId as number)
    messageListenerId = null
  }
  if (eventListenerId != null) {
    offUmengPushRuntimeEvent(eventListenerId as number)
    eventListenerId = null
  }
})
</script>
```

## 结论

如果你只记住三件事，请记住：

- 初始化优先用 `createUmengPushInitOptions() + initializeUmengPush()`
- 联调优先看 `requestNotificationPermission()`、`getUmengPushDebugState()`、`onUmengPushRuntimeEvent()`
- 鸿蒙只维护一份 `utssdk/app-harmony/resources/rawfile/umconfig.json`，iOS 真正能不能注册 APNs 取决于 capability 与签名环境
