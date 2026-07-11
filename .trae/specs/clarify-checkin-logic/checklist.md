# Checklist

验证 `index.vue` 的 `checkinState` 计算属性是否按 spec.md 定义的状态判定优先级顺序实现。

## checkinState 判定优先级顺序
- [x] disabled 前置校验在前（未登录 / 无进行中计划 / 不在打卡日期范围 / 无提醒时间）
- [x] forceActive 判定在 disabled 之后、isIntervalChecked 之前（允许从 done/waiting 重新打卡）
- [x] isIntervalChecked 判定在 forceActive 之后、时间窗口判断之前（匹配区间内有记录即返回 done）
- [x] 时间窗口判断在最后（`nowMinutes < t_1.minutes - 120` → waiting；否则 → active）
- [x] 禁止在未检查 isIntervalChecked 前，仅凭 `nowMinutes < t_1 - 120` 直接返回 waiting

## Bug 修复验证
- [x] waiting 时段长按重置强制打卡后，打卡记录入本地列表，checkinState 重算返回 done（而非 waiting）
- [x] done 状态下定时器触发刷新，匹配区间内仍有记录时保持 done（不被刷新为 active/waiting）
- [x] done 状态下长按 3 秒，forceActive 生效，返回 active（允许重新打卡）
- [x] 匹配区间结束（进入下一个中点）后，新区间无记录则返回 active/waiting

## 其他已实现功能回归验证（不受本次改动影响）
- [x] 防抖：同一任务 3 秒内只允许点击一次
- [x] onHide 清除 refreshTimer，onShow 重启定时器并立即同步
- [x] 长按 3 秒重置仅在 waiting/done 状态生效，disabled/active 不可重置
