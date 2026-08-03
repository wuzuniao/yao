import common from '@ohos.app.ability.common'
import Want from '@ohos.app.ability.Want'
import { Callback } from '@ohos.base'
import { init, setLogEnabled } from '@umeng/analytics'
import { PushAgent, MsgContent } from '@umeng/push'

type PushRecordValue = string | number | boolean | null | Array<string>
type PushCallbackRecord = Record<string, PushRecordValue>

interface RuntimeEventPayload {
  type : string
  receivedAt : number
  source : string | null
  action : string | null
  online : boolean | null
  registered : boolean | null
  payload : string | null
  deviceToken : string | null
  registrationId : string | null
  registerErrorCode : string | null
  registerErrorMessage : string | null
  message : string | null
}

interface PermissionCallbackPayload {
  success : boolean
  granted : boolean
  requested : boolean
  notificationEnabled : boolean
  code : string
  message : string
}

interface TokenSnapshotPayload {
  huawei : string
  harmony : string
  registrationId : string
  initialized : boolean
  registered : boolean
}

export class UmengPushNative {
  private static initialized : boolean = false
  private static initReady : boolean = false
  private static registered : boolean = false
  private static callbacksBound : boolean = false
  private static badgeNum : number = 0
  private static lastInitMessage : string = 'push not initialized'
  private static deviceToken : string | null = null
  private static thirdToken : string | null = null
  private static registrationId : string | null = null
  private static registerErrorCode : string | null = null
  private static registerErrorMessage : string | null = null
  private static lastReceivedPushPayload : string | null = null
  private static lastInAppMessagePayload : string | null = null
  private static lastClickPayload : string | null = null
  private static connectStateOnline : boolean | null = null
  private static lastOperationSuccess : boolean = false
  private static lastOperationCode : string = 'IDLE'
  private static lastOperationMessage : string = 'no operation yet'
  private static lastOperationPayload : string | null = null
  private static lastRegisterStateEventJson : string | null = null
  private static lastNotificationClickEventJson : string | null = null
  private static onPushPayloadReceivedListener : ((payload : string) => void) | null = null
  private static onRuntimeEventListener : ((eventJson : string) => void) | null = null

  static initializePush(appKey : string | null, messageSecret : string | null, channel : string | null, debug : boolean, uiAbilityContext : common.UIAbilityContext | null) : boolean {
    const safeAppKey = UmengPushNative.trimText(appKey)
    const safeSecret = UmengPushNative.trimText(messageSecret)
    const safeChannel = UmengPushNative.trimText(channel)
    if (safeAppKey.length == 0) {
      UmengPushNative.initialized = false
      UmengPushNative.lastInitMessage = 'initialize failed: appKey is empty'
      UmengPushNative.registerErrorCode = 'INIT_INVALID_APPKEY'
      UmengPushNative.registerErrorMessage = UmengPushNative.lastInitMessage
      UmengPushNative.recordOperation(false, 'INIT_INVALID_APPKEY', UmengPushNative.lastInitMessage, null)
      UmengPushNative.dispatchRegisterStateRuntimeEvent('initialize-validate')
      return false
    }
    if (safeSecret.length == 0) {
      UmengPushNative.initialized = false
      UmengPushNative.lastInitMessage = 'initialize failed: messageSecret is empty'
      UmengPushNative.registerErrorCode = 'INIT_INVALID_SECRET'
      UmengPushNative.registerErrorMessage = UmengPushNative.lastInitMessage
      UmengPushNative.recordOperation(false, 'INIT_INVALID_SECRET', UmengPushNative.lastInitMessage, null)
      UmengPushNative.dispatchRegisterStateRuntimeEvent('initialize-validate')
      return false
    }
    if (safeChannel.length == 0) {
      UmengPushNative.initialized = false
      UmengPushNative.lastInitMessage = 'initialize failed: channel is empty'
      UmengPushNative.registerErrorCode = 'INIT_INVALID_CHANNEL'
      UmengPushNative.registerErrorMessage = UmengPushNative.lastInitMessage
      UmengPushNative.recordOperation(false, 'INIT_INVALID_CHANNEL', UmengPushNative.lastInitMessage, null)
      UmengPushNative.dispatchRegisterStateRuntimeEvent('initialize-validate')
      return false
    }

    if (uiAbilityContext == null) {
      UmengPushNative.initialized = false
      UmengPushNative.lastInitMessage = 'initialize failed: UIAbilityContext unavailable'
      UmengPushNative.registerErrorCode = 'INIT_CONTEXT_UNAVAILABLE'
      UmengPushNative.registerErrorMessage = UmengPushNative.lastInitMessage
      UmengPushNative.recordOperation(false, 'INIT_CONTEXT_UNAVAILABLE', UmengPushNative.lastInitMessage, null)
      UmengPushNative.dispatchRegisterStateRuntimeEvent('initialize-context')
      return false
    }

    if (!UmengPushNative.initialized) {
      UmengPushNative.resetRuntimeState()
    }
    UmengPushNative.initReady = false
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'initialize request submitted', null)

    try {
      setLogEnabled(debug)
      UmengPushNative.bindPushCallbacks(uiAbilityContext)
      init().then(() => {
        UmengPushNative.initReady = true
        UmengPushNative.lastInitMessage = 'initialize ready'
        UmengPushNative.recordOperation(true, 'INIT_READY', UmengPushNative.lastInitMessage, null)
        UmengPushNative.refreshThirdToken()
        UmengPushNative.dispatchRegisterStateRuntimeEvent('initialize-ready')
      }).catch((error : Object) => {
        UmengPushNative.initialized = false
        UmengPushNative.initReady = false
        UmengPushNative.registered = false
        UmengPushNative.registerErrorCode = 'INIT_ERROR'
        UmengPushNative.registerErrorMessage = UmengPushNative.errorMessage(error)
        UmengPushNative.lastInitMessage = 'initialize failed: ' + (UmengPushNative.registerErrorMessage as string)
        UmengPushNative.recordOperation(false, 'INIT_ERROR', UmengPushNative.lastInitMessage, null)
        UmengPushNative.dispatchRegisterStateRuntimeEvent('initialize-promise')
      })

      UmengPushNative.initialized = true
      UmengPushNative.lastInitMessage = 'initialize submitted'
      UmengPushNative.recordOperation(true, 'INIT_SUBMITTED', UmengPushNative.lastInitMessage, null)
      return true
    } catch (error) {
      UmengPushNative.initialized = false
      UmengPushNative.initReady = false
      UmengPushNative.registered = false
      UmengPushNative.registerErrorCode = 'INIT_ERROR'
      UmengPushNative.registerErrorMessage = UmengPushNative.errorMessage(error)
      UmengPushNative.lastInitMessage = 'initialize failed: ' + (UmengPushNative.registerErrorMessage as string)
      UmengPushNative.recordOperation(false, 'INIT_ERROR', UmengPushNative.lastInitMessage, null)
      UmengPushNative.dispatchRegisterStateRuntimeEvent('initialize-exception')
      return false
    }
  }

  static readRawFileText(fileName : string, uiAbilityContext : common.UIAbilityContext | null) : string | null {
    if (uiAbilityContext == null) {
      return null
    }
    try {
      const content = uiAbilityContext.resourceManager.getRawFileContentSync(fileName)
      return UmengPushNative.decodeRawText(content)
    } catch (error) {
      console.error('[xtf-umengpush][harmony-native] read rawfile failed:', UmengPushNative.errorMessage(error))
      return null
    }
  }

  static isInitialized() : boolean {
    return UmengPushNative.initialized
  }

  static isInitReady() : boolean {
    return UmengPushNative.initReady
  }

  static isRegistered() : boolean {
    return UmengPushNative.registered
  }

  static getLastInitMessage() : string {
    return UmengPushNative.lastInitMessage
  }

  static getDeviceToken() : string | null {
    return UmengPushNative.deviceToken
  }

  static getRegistrationId() : string | null {
    return UmengPushNative.registrationId
  }

  static getRegisterErrorCode() : string | null {
    return UmengPushNative.registerErrorCode
  }

  static getRegisterErrorMessage() : string | null {
    return UmengPushNative.registerErrorMessage
  }

  static getVendorTokenSnapshot() : string {
    const payload : TokenSnapshotPayload = {
      huawei: UmengPushNative.thirdToken == null ? '' : UmengPushNative.thirdToken as string,
      harmony: UmengPushNative.deviceToken == null ? '' : UmengPushNative.deviceToken as string,
      registrationId: UmengPushNative.registrationId == null ? '' : UmengPushNative.registrationId as string,
      initialized: UmengPushNative.initialized,
      registered: UmengPushNative.registered
    }
    return JSON.stringify(payload)
  }

  static getLastReceivedPushPayload() : string | null {
    return UmengPushNative.lastReceivedPushPayload
  }

  static getLastInAppMessagePayload() : string | null {
    return UmengPushNative.lastInAppMessagePayload
  }

  static getLastClickPayload() : string | null {
    return UmengPushNative.lastClickPayload
  }

  static clearLastClickPayload() : void {
    UmengPushNative.lastClickPayload = null
    UmengPushNative.lastNotificationClickEventJson = null
  }

  static getConnectStateOnline() : boolean | null {
    return UmengPushNative.connectStateOnline
  }

  static wasLastOperationSuccess() : boolean {
    return UmengPushNative.lastOperationSuccess
  }

  static getLastOperationCode() : string {
    return UmengPushNative.lastOperationCode
  }

  static getLastOperationMessage() : string {
    return UmengPushNative.lastOperationMessage
  }

  static getLastOperationPayload() : string | null {
    return UmengPushNative.lastOperationPayload
  }

  static requestNotificationPermission(uiAbilityContext : common.UIAbilityContext | null, callback : (resultJson : string) => void) : void {
    if (uiAbilityContext == null) {
      const failPayload : PermissionCallbackPayload = {
        success: false,
        granted: false,
        requested: false,
        notificationEnabled: false,
        code: 'CONTEXT_UNAVAILABLE',
        message: 'UIAbilityContext unavailable'
      }
      UmengPushNative.recordOperation(false, failPayload.code, failPayload.message, null)
      callback(JSON.stringify(failPayload))
      return
    }

    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'request notification permission submitted', null)
    PushAgent.enableNotification(uiAbilityContext, (result : PushCallbackRecord) => {
      PushAgent.isNotificationEnabled().then((status : Record<string, string | number | boolean>) => {
        const enabled = UmengPushNative.readBooleanValue(status['data']) || UmengPushNative.readBooleanValue(status['enabled'])
        const message = UmengPushNative.readStringValue(result['msg'])
        const code = UmengPushNative.readCodeValue(result['code'], enabled)
        const rawPayload = UmengPushNative.stringifyDebugPayload(result, status)
        UmengPushNative.debugLog('permission callback', rawPayload)
        const payload : PermissionCallbackPayload = {
          success: enabled,
          granted: enabled,
          requested: true,
          notificationEnabled: enabled,
          code,
          message: message.length > 0 ? message : (enabled ? 'notification permission granted' : 'notification permission denied')
        }
        UmengPushNative.recordOperation(payload.success, payload.code, payload.message, rawPayload)
        callback(JSON.stringify(payload))
      }).catch((error : Object) => {
        const rawPayload = UmengPushNative.stringifyDebugPayload(result, UmengPushNative.errorMessage(error))
        UmengPushNative.debugLog('permission callback error', rawPayload)
        const payload : PermissionCallbackPayload = {
          success: false,
          granted: false,
          requested: true,
          notificationEnabled: false,
          code: 'REQUEST_PERMISSION_ERROR',
          message: UmengPushNative.errorMessage(error)
        }
        UmengPushNative.recordOperation(false, payload.code, payload.message, rawPayload)
        callback(JSON.stringify(payload))
      })
    })
  }

  static enablePush() : void {
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'enable push submitted', null)
    PushAgent.enable((result : Record<string, string | number>) => {
      UmengPushNative.handlePushSwitchCallback('enable', result)
    })
  }

  static disablePush() : void {
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'disable push submitted', null)
    PushAgent.disable((result : Record<string, string | number>) => {
      UmengPushNative.handlePushSwitchCallback('disable', result)
    })
  }

  static setBadgeNum(num : number) : void {
    UmengPushNative.badgeNum = num
      PushAgent.setBadge(num).then((result) => {
        UmengPushNative.recordOperation(true, 'SET_BADGE_OK', result.msg, '' + num)
      }).catch((error : Object) => {
      UmengPushNative.recordOperation(false, 'SET_BADGE_ERROR', UmengPushNative.errorMessage(error), '' + num)
    })
  }

  static changeBadgeNum(num : number) : void {
    const nextValue = UmengPushNative.badgeNum + num
    UmengPushNative.setBadgeNum(nextValue < 0 ? 0 : nextValue)
  }

  static getTags() : void {
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'get tags submitted', null)
    PushAgent.getTags((result : Record<string, string | number | Array<string>>) => {
      const tagsJson = UmengPushNative.extractArrayJson(result['data'])
      const message = UmengPushNative.readStringValue(result['msg'])
      const code = UmengPushNative.readCodeValue(result['code'], tagsJson != null)
      UmengPushNative.recordOperation(UmengPushNative.isSuccessCode(code), code, message.length > 0 ? message : 'get tags finished', tagsJson)
    })
  }

  static addTags(tagsCsv : string) : void {
    const tags = UmengPushNative.createTags(tagsCsv)
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'add tags submitted', tagsCsv)
    PushAgent.addTags(tags, (result : Record<string, string>) => {
      UmengPushNative.recordCallbackRecord('add tags finished', result, tagsCsv)
    })
  }

  static deleteTags(tagsCsv : string) : void {
    const tags = UmengPushNative.createTags(tagsCsv)
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'delete tags submitted', tagsCsv)
    PushAgent.deleteTags(tags, (result : Record<string, string>) => {
      UmengPushNative.recordCallbackRecord('delete tags finished', result, tagsCsv)
    })
  }

  static addAlias(alias : string, aliasType : string) : void {
    const payload = JSON.stringify({ alias, aliasType })
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'add alias submitted', payload)
    PushAgent.addAlias(alias, aliasType, (result : Record<string, string>) => {
      UmengPushNative.recordCallbackRecord('add alias finished', result, payload)
    })
  }

  static setAlias(alias : string, aliasType : string) : void {
    const payload = JSON.stringify({ alias, aliasType })
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'set alias submitted', payload)
    PushAgent.setAlias(alias, aliasType, (result : Record<string, string>) => {
      UmengPushNative.recordCallbackRecord('set alias finished', result, payload)
    })
  }

  static deleteAlias(alias : string, aliasType : string) : void {
    const payload = JSON.stringify({ alias, aliasType })
    UmengPushNative.recordOperation(true, 'REQUEST_SUBMITTED', 'delete alias submitted', payload)
    PushAgent.deleteAlias(alias, aliasType, (result : Record<string, string>) => {
      UmengPushNative.recordCallbackRecord('delete alias finished', result, payload)
    })
  }

  static setOnPushPayloadReceivedListener(listener : ((payload : string) => void) | null) : void {
    UmengPushNative.onPushPayloadReceivedListener = listener
    if (listener != null && UmengPushNative.lastReceivedPushPayload != null) {
      listener(UmengPushNative.lastReceivedPushPayload as string)
    }
  }

  static clearOnPushPayloadReceivedListener() : void {
    UmengPushNative.onPushPayloadReceivedListener = null
  }

  static setOnRuntimeEventListener(listener : ((eventJson : string) => void) | null) : void {
    UmengPushNative.onRuntimeEventListener = listener
    if (listener == null) {
      return
    }
    if (UmengPushNative.lastRegisterStateEventJson != null) {
      listener(UmengPushNative.lastRegisterStateEventJson as string)
    }
    if (UmengPushNative.connectStateOnline != null) {
      listener(UmengPushNative.buildRuntimeEventJson('connect-state', null, 'cached-connect-state', null, UmengPushNative.connectStateOnline == true ? 'connected' : 'disconnected'))
    }
    if (UmengPushNative.lastInAppMessagePayload != null) {
      listener(UmengPushNative.buildRuntimeEventJson('inapp-message', 'replay', 'cached-inapp-message', UmengPushNative.lastInAppMessagePayload, null))
    }
    if (UmengPushNative.lastNotificationClickEventJson != null) {
      listener(UmengPushNative.lastNotificationClickEventJson as string)
    }
  }

  static clearOnRuntimeEventListener() : void {
    UmengPushNative.onRuntimeEventListener = null
  }

  static handleAppWant(want : Want) : void {
    const payload = UmengPushNative.stringifyWantPayload(want)
    if (!UmengPushNative.isNotificationClickWantPayload(payload)) {
      return
    }
    PushAgent.onNewWant(want).catch((error : Object) => {
      UmengPushNative.recordOperation(false, 'ON_NEW_WANT_ERROR', UmengPushNative.errorMessage(error), payload)
    })
    if (payload != null) {
      UmengPushNative.lastClickPayload = payload
      UmengPushNative.lastNotificationClickEventJson = UmengPushNative.buildRuntimeEventJson('notification-click', 'onClick', 'want', payload, null)
      UmengPushNative.dispatchRuntimeEventJson(UmengPushNative.lastNotificationClickEventJson as string)
    }
  }

  private static bindPushCallbacks(uiAbilityContext : common.UIAbilityContext) : void {
    if (UmengPushNative.callbacksBound) {
      return
    }
    UmengPushNative.callbacksBound = true

    PushAgent.initCallback((result : PushCallbackRecord) => {
      const rawPayload = UmengPushNative.stringifyDebugPayload(result, null)
      UmengPushNative.debugLog('init callback', rawPayload)
      UmengPushNative.syncConnectStateFromInitResult(result)
      const token = UmengPushNative.readStringValue(result['data'])
      const code = UmengPushNative.readCodeValue(result['code'], token.length > 0)
      const message = UmengPushNative.readStringValue(result['msg'])
      if (token.length > 0) {
        UmengPushNative.deviceToken = token
        UmengPushNative.registrationId = token
        UmengPushNative.registered = true
        UmengPushNative.registerErrorCode = null
        UmengPushNative.registerErrorMessage = null
        UmengPushNative.lastInitMessage = message.length > 0 ? message : 'register success'
        UmengPushNative.recordOperation(true, 'REGISTER_OK', UmengPushNative.lastInitMessage, UmengPushNative.stringifyDebugPayload(token, rawPayload))
        UmengPushNative.refreshThirdToken()
      } else {
        UmengPushNative.registered = false
        UmengPushNative.registerErrorCode = UmengPushNative.hasMeaningfulResult(result) ? code : 'REGISTER_CALLBACK_EMPTY'
        UmengPushNative.registerErrorMessage = UmengPushNative.buildRegisterFailureMessage(UmengPushNative.registerErrorCode as string, message, UmengPushNative.hasMeaningfulResult(result))
        UmengPushNative.lastInitMessage = UmengPushNative.registerErrorMessage as string
        UmengPushNative.recordOperation(false, UmengPushNative.registerErrorCode as string, UmengPushNative.lastInitMessage, rawPayload)
      }
      UmengPushNative.dispatchRegisterStateRuntimeEvent('init-callback')
    })

    PushAgent.onNotificationMessage((msg : MsgContent, callback : Callback<MsgContent>) => {
      const payload = UmengPushNative.buildMessageCallbackPayload('notification', msg)
      UmengPushNative.dispatchPushPayload(payload)
      UmengPushNative.debugLog('notification message', payload)
      callback(msg)
    })

    PushAgent.onClickMessage((result : Record<string, string>) => {
      const payload = UmengPushNative.buildClickCallbackPayload('click-message', result)
      UmengPushNative.lastClickPayload = payload
      UmengPushNative.lastNotificationClickEventJson = UmengPushNative.buildRuntimeEventJson('notification-click', 'onClick', 'click-message', payload, null)
      UmengPushNative.dispatchRuntimeEventJson(UmengPushNative.lastNotificationClickEventJson as string)
    })

    PushAgent.onCustomMessage((msg : MsgContent) => {
      const payload = UmengPushNative.buildMessageCallbackPayload('custom', msg)
      UmengPushNative.dispatchPushPayload(payload)
      UmengPushNative.lastInAppMessagePayload = payload
      UmengPushNative.dispatchRuntimeEventJson(UmengPushNative.buildRuntimeEventJson('inapp-message', 'onShow', 'custom-message', payload, null))
    })

  }

  private static refreshThirdToken() : void {
    PushAgent.getThirdToken().then((result) => {
      const token = UmengPushNative.trimText(result.data == null ? null : result.data)
      if (token.length > 0) {
        UmengPushNative.thirdToken = token
      }
    }).catch((_error : Object) => {
    })
  }

  private static handlePushSwitchCallback(action : string, result : Record<string, string | number>) : void {
    PushAgent.isNotificationEnabled().then((status : Record<string, string | number | boolean>) => {
      UmengPushNative.refreshThirdToken()
      const enabled = UmengPushNative.readBooleanValue(status['data']) || UmengPushNative.readBooleanValue(status['enabled'])
      const callbackCode = UmengPushNative.readStringValue(result['code'])
      const callbackMessage = UmengPushNative.readStringValue(result['msg'])
      const rawPayload = UmengPushNative.stringifyDebugPayload(result, status)
      UmengPushNative.debugLog(action + ' callback', rawPayload)
      const callbackFailed = UmengPushNative.containsFailureHint(callbackMessage)
      let success = action == 'enable' ? enabled : !enabled
      if (callbackFailed) {
        success = false
      }
      let code = callbackCode.length > 0 ? callbackCode : (action == 'enable' ? (enabled ? 'ENABLE_STATE_ON' : 'ENABLE_STATE_OFF') : (!enabled ? 'DISABLE_STATE_OFF' : 'DISABLE_STATE_ON'))
      let message = callbackMessage.length > 0 ? callbackMessage : (action + ' push callback finished')
      if (!UmengPushNative.hasMeaningfulResult(result) && callbackMessage.length == 0) {
        code = action == 'enable' ? 'PUSH_SWITCH_CALLBACK_EMPTY' : 'PUSH_SWITCH_CALLBACK_EMPTY'
        message = action + ' push callback returned empty result'
      }
      if (callbackFailed && callbackCode.length == 0) {
        code = action == 'enable' ? 'ENABLE_CALLBACK_REPORTED_ERROR' : 'DISABLE_CALLBACK_REPORTED_ERROR'
      }
      UmengPushNative.recordOperation(success, code, message, rawPayload)
      if (action == 'enable' && success) {
        UmengPushNative.lastInitMessage = message
      }
      if (!success) {
        UmengPushNative.lastInitMessage = message
        UmengPushNative.registerErrorCode = code
        UmengPushNative.registerErrorMessage = message
      }
      UmengPushNative.dispatchRegisterStateRuntimeEvent(action + '-callback')
    }).catch((error : Object) => {
      const rawPayload = UmengPushNative.stringifyDebugPayload(result, UmengPushNative.errorMessage(error))
      UmengPushNative.debugLog(action + ' callback error', rawPayload)
      const code = action == 'enable' ? 'ENABLE_STATUS_ERROR' : 'DISABLE_STATUS_ERROR'
      const message = action + ' push status query failed: ' + UmengPushNative.errorMessage(error)
      UmengPushNative.recordOperation(false, code, message, rawPayload)
      UmengPushNative.registerErrorCode = code
      UmengPushNative.registerErrorMessage = message
      UmengPushNative.dispatchRegisterStateRuntimeEvent(action + '-status')
    })
  }

  private static recordCallbackRecord(fallbackMessage : string, result : Record<string, string | number>, payload : string | null = null) : void {
    const message = UmengPushNative.readStringValue(result['msg'])
    const code = UmengPushNative.readCodeValue(result['code'], true)
    UmengPushNative.recordOperation(UmengPushNative.isSuccessCode(code), code, message.length > 0 ? message : fallbackMessage, payload)
  }

  private static dispatchRegisterStateRuntimeEvent(source : string) : void {
    UmengPushNative.lastRegisterStateEventJson = UmengPushNative.buildRuntimeEventJson('register-state', null, source, null, UmengPushNative.lastInitMessage)
    UmengPushNative.dispatchRuntimeEventJson(UmengPushNative.lastRegisterStateEventJson as string)
  }

  private static dispatchPushPayload(payload : string) : void {
    UmengPushNative.lastReceivedPushPayload = payload
    const listener = UmengPushNative.onPushPayloadReceivedListener
    if (listener != null) {
      listener(payload)
    }
  }

  private static syncConnectStateFromInitResult(result : PushCallbackRecord) : void {
    const connectResult = UmengPushNative.readStringValue(result['connect_result'])
    if (connectResult.length == 0) {
      return
    }
    const online = connectResult == 'connected'
    UmengPushNative.connectStateOnline = online
    UmengPushNative.dispatchRuntimeEventJson(UmengPushNative.buildRuntimeEventJson('connect-state', null, 'init-callback', null, connectResult))
  }

  private static buildRuntimeEventJson(type : string, action : string | null, source : string | null, payload : string | null, message : string | null) : string {
    const event : RuntimeEventPayload = {
      type,
      receivedAt: Date.now(),
      source,
      action,
      online: UmengPushNative.connectStateOnline,
      registered: UmengPushNative.registered,
      payload,
      deviceToken: UmengPushNative.deviceToken,
      registrationId: UmengPushNative.registrationId,
      registerErrorCode: UmengPushNative.registerErrorCode,
      registerErrorMessage: UmengPushNative.registerErrorMessage,
      message
    }
    return JSON.stringify(event)
  }

  private static dispatchRuntimeEventJson(eventJson : string) : void {
    const listener = UmengPushNative.onRuntimeEventListener
    if (listener != null) {
      listener(eventJson)
    }
  }

  private static stringifyMsgContent(msg : MsgContent) : string {
    try {
      return JSON.stringify(msg)
    } catch (_error) {
      return '{"raw":"[msg stringify failed]"}'
    }
  }

  private static stringifyWantPayload(want : Want) : string | null {
    try {
      return JSON.stringify(want.parameters)
    } catch (_error) {
      try {
        return JSON.stringify(want)
      } catch (_wantError) {
        return null
      }
    }
  }

  private static buildMessageCallbackPayload(source : string, msg : MsgContent) : string {
    return JSON.stringify({
      source,
      message: msg
    })
  }

  private static buildClickCallbackPayload(source : string, result : Record<string, string>) : string {
    return JSON.stringify({
      source,
      extra: result
    })
  }

  private static decodeRawText(bytes : Uint8Array) : string {
    let text = ''
    for (let i = 0; i < bytes.length; i++) {
      text += String.fromCharCode(bytes[i])
    }
    return text
  }

  private static createTags(tagsCsv : string) : Array<string> {
    const tags : Array<string> = []
    tagsCsv.split(',').forEach((tag) => {
      const value = UmengPushNative.trimText(tag)
      if (value.length > 0) {
        tags.push(value)
      }
    })
    return tags
  }

  private static extractArrayJson(value : PushRecordValue) : string | null {
    if (value == null) {
      return null
    }
    if (Array.isArray(value)) {
      return JSON.stringify(value)
    }
    return null
  }

  private static stringifyDebugPayload(primary : Object | string | null, secondary : Object | string | null) : string | null {
    try {
      return JSON.stringify({
        primary,
        secondary
      })
    } catch (_error) {
      return null
    }
  }

  private static debugLog(label : string, payload : string | null) : void {
    console.log('[xtf-umengpush][harmony-native] ' + label + ':', payload == null ? 'null' : payload)
  }

  private static hasMeaningfulResult(result : PushCallbackRecord) : boolean {
    const code = UmengPushNative.readStringValue(result['code'])
    const message = UmengPushNative.readStringValue(result['msg'])
    const data = UmengPushNative.readStringValue(result['data'])
    return code.length > 0 || message.length > 0 || data.length > 0
  }

  private static containsFailureHint(message : string) : boolean {
    return message.indexOf('错误') >= 0 || message.indexOf('失败') >= 0 || message.indexOf('请检查') >= 0
  }

  private static isNotificationClickWantPayload(payload : string | null) : boolean {
    if (payload == null) {
      return false
    }
    return payload.indexOf('"msg_id"') >= 0 ||
      payload.indexOf('"tunnel_message_id"') >= 0 ||
      payload.indexOf('_push_notifyid') >= 0 ||
      payload.indexOf('"display_type"') >= 0 ||
      payload.indexOf('"extra"') >= 0
  }

  private static isHarmonyAuthFailure(code : string, message : string) : boolean {
    if (code == '1004') {
      return true
    }
    return message.indexOf('init tunnel connect callback error') >= 0
  }

  private static buildRegisterFailureMessage(code : string, message : string, hasMeaningfulResult : boolean) : string {
    if (UmengPushNative.isHarmonyAuthFailure(code, message)) {
      return '友盟在线通道鉴权失败(code=1004)，请核对鸿蒙应用的 appKey、appMessageSecret、bundleName 与友盟后台配置是否完全一致'
    }
    if (message.length > 0) {
      return message
    }
    return hasMeaningfulResult ? 'register failed' : 'register callback returned empty result'
  }

  private static readStringValue(value : PushRecordValue | undefined) : string {
    if (value == null) {
      return ''
    }
    if (typeof value == 'string') {
      return value
    }
    return '' + value
  }

  private static readBooleanValue(value : PushRecordValue | undefined) : boolean {
    if (typeof value == 'boolean') {
      return value
    }
    if (typeof value == 'number') {
      return value > 0
    }
    if (typeof value == 'string') {
      return value == 'true' || value == '1' || value == '200' || value == 'ok'
    }
    return false
  }

  private static readCodeValue(value : PushRecordValue | undefined, fallbackSuccess : boolean) : string {
    const code = UmengPushNative.readStringValue(value)
    if (code.length > 0) {
      return code
    }
    return fallbackSuccess ? 'OK' : 'ERROR'
  }

  private static resetRuntimeState() : void {
    UmengPushNative.registered = false
    UmengPushNative.initReady = false
    UmengPushNative.deviceToken = null
    UmengPushNative.thirdToken = null
    UmengPushNative.registrationId = null
    UmengPushNative.registerErrorCode = null
    UmengPushNative.registerErrorMessage = null
    UmengPushNative.lastReceivedPushPayload = null
    UmengPushNative.lastInAppMessagePayload = null
    UmengPushNative.lastClickPayload = null
    UmengPushNative.connectStateOnline = null
    UmengPushNative.lastRegisterStateEventJson = null
    UmengPushNative.lastNotificationClickEventJson = null
  }

  private static recordOperation(success : boolean, code : string, message : string, payload : string | null) : void {
    const safeCode = UmengPushNative.trimText(code)
    UmengPushNative.lastOperationSuccess = success
    UmengPushNative.lastOperationCode = safeCode.length == 0 ? 'UNKNOWN' : safeCode
    UmengPushNative.lastOperationMessage = UmengPushNative.messageOrDefault(message, UmengPushNative.lastOperationCode)
    UmengPushNative.lastOperationPayload = payload
  }

  private static trimText(value : string | null) : string {
    if (value == null) {
      return ''
    }
    return value.trim()
  }

  private static errorMessage(error : Object) : string {
    return JSON.stringify(error)
  }

  private static messageOrDefault(message : string | null, fallback : string) : string {
    const safeMessage = UmengPushNative.trimText(message)
    return safeMessage.length > 0 ? safeMessage : fallback
  }

  private static isSuccessCode(code : string) : boolean {
    return code == '0' || code == '200' || code == 'OK' || code == 'SUCCESS'
  }
}
