import AbilityStage from '@ohos.app.ability.AbilityStage';
import { preInit, InternalPlugin } from '@umeng/analytics';
import { PushPlugin } from '@umeng/push';
import util from '@ohos.util';

// 鸿蒙（HarmonyOS）端友盟预初始化桥接文件
// 路径约定（xtf-umengpush 插件硬性要求）：harmony-configs/entry/src/main/ets/abilityStage/MyAbilityStage.ets
// 作用：在应用进程启动最早阶段（AbilityStage.onCreate）预初始化友盟统计与推送组件，
//      否则冷启动时推送通道可能尚未就绪，导致离线推送消息下发失败。
// 注意：
//  1. appMessageSecret 取自与 xtf-umengpush 插件同源的 rawfile/umconfig.json，切勿硬编码；
//     该值须为友盟后台的「Umeng Message Secret」（不是 App Master Secret）。
//  2. 本文件需在 entry 的 module.json5 通过 module.srcEntry 注册为 AbilityStage 才会被加载执行，
//     注册方式须遵循 DCloud 官方 harmony-configs 机制（自定义 AbilityStage 需继承 uni 运行时基类，
//     否则可能覆盖 uni 初始化导致应用启动失败），请在 DevEco Studio 真机编译时验证。
export default class MyAbilityStage extends AbilityStage {
  onCreate(): void {
    try {
      const appContext = this.context.getApplicationContext();
      const raw: Uint8Array = appContext.resourceManager.getRawFileContentSync('umconfig.json');
      const jsonText: string = util.TextDecoder.create('utf-8', { ignoreBom: true }).decodeToString(raw);
      const cfg = JSON.parse(jsonText) as Record<string, Object>;
      preInit({
        context: appContext,
        enableLog: true,
        plugins: [
          new InternalPlugin(),
          new PushPlugin({ appMessageSecret: cfg['appMessageSecret'] as string })
        ]
      });
    } catch (e) {
      console.error('[MyAbilityStage] 友盟 preInit 失败：' + (e as Error).message);
    }
  }
}
