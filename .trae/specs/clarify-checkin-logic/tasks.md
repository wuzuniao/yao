# Tasks

基于 spec.md 定义的新规范逻辑，对首页打卡状态机进行实施，核心为修复 `checkinState` 计算属性的判定优先级顺序。

- [x] Task 1: 修复 `checkinState` 判定优先级顺序
  - [x] SubTask 1.1: 读取 `frontend/src/pages/index/index.vue` 中 `checkinState` 计算属性现有逻辑（L245-L278），确认当前判定顺序为 disabled → waiting(时间窗口) → forceActive → isIntervalChecked → active
  - [x] SubTask 1.2: 调整判定顺序为 disabled → forceActive → isIntervalChecked → waiting(时间窗口) → active，确保匹配区间内已有打卡记录时优先返回 `done`，不受 `nowMinutes < t_1 - 120` 阻断
  - [x] SubTask 1.3: 合并原有的两处 `forceActive` 分支为顶部统一判断（forceActive 优先级最高，允许从 done/waiting 重新打卡）
  - [x] SubTask 1.4: 更新 `checkinState` 上方注释，标注新的优先级顺序

# Task Dependencies
- 无（Task 1 为单文件单点修改，无外部依赖）
