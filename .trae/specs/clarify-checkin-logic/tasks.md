# Tasks

本 spec 为纯文档梳理任务，不涉及代码改动，任务聚焦于逻辑梳理的覆盖度与准确性。所有梳理工作已完成。

- [x] Task 1: 通读 `frontend/src/pages/index/index.vue` 打卡相关代码，提取状态机判定逻辑、时间窗口算法、图标与文字映射、刷新机制。
  - [x] SubTask 1.1: 读取 `index.vue` 模板与 `<script setup>`，定位 `checkinState`、`isCheckinDone`、`isWaiting`、`isButtonDisabled`、`checkinText`、`checkinIcon` 等计算属性
  - [x] SubTask 1.2: 分析 `checkinState` 的四种状态（disabled/waiting/active/done）判定条件与时间窗口算法
  - [x] SubTask 1.3: 分析 `handleCheckin`、`handleLongPress`、`loadTodayCheckins`、定时器、`onShow` 等交互与刷新机制
  - [x] SubTask 1.4: 分析任务切换（`handleSecondaryClick`、`handleSelectTask`）对打卡状态的联动影响
- [x] Task 2: 以文字形式在 `spec.md` 中描述以下内容：
  - [x] SubTask 2.1: 按钮四种状态的视觉表现（背景色、图标、文字、可点击性）——**修正 waiting 不显示图标**
  - [x] SubTask 2.2: 七种用户场景下的按钮状态（未登录、已登录无任务、不在日期范围、无提醒时间、未到打卡时间、可打卡、已完成）
  - [x] SubTask 2.3: 允许打卡的时间窗口定义——**修正为"开始打卡时间"模型：从 t-60 持续到用户打卡为止，超过 t 仍未打卡仍为 active**
  - [x] SubTask 2.4: 打卡成功后按钮状态变化（即时转绿、不弹窗、单击拦截）
  - [x] SubTask 2.5: "已打卡（done）"状态的持续时长——**持续到下一次提醒开始打卡时间或当日 24:00 后重置为 waiting**
  - [x] SubTask 2.6: 图标状态自动刷新机制（每分钟定时器、时间流逝与重算关系、长按 3 秒重置、onShow 刷新）
  - [x] SubTask 2.7: 任务切换对打卡状态的联动影响
- [x] Task 3: 补充"打卡记录匹配判定"规则（新增 Requirement）：
  - [x] SubTask 3.1: 单条提醒时间——全天有任意一条打卡记录即视为已打卡
  - [x] SubTask 3.2: 多条提醒时间——提醒时间前后各 1 小时 `[t-60, t+60]` 内有记录视为该提醒已打卡
- [x] Task 4: 修正情况 7（小间隔前半段）的语义：
  - [x] SubTask 4.1: 前半段 `[t-60, midpoint)` 判定"前一个提醒是否已打卡"：已打卡 → done；未打卡 → active（保持未打卡可补打卡）
  - [x] SubTask 4.2: 后半段 `[midpoint, ...]` 判定"当前提醒是否已打卡"：已打卡 → done；未打卡 → active
- [x] Task 5: 在 spec.md 中以 `⚠️ 当前实现差异` 标注期望行为与当前代码实现不一致之处，作为后续代码修改输入。

# Task Dependencies
- Task 2/3/4 依赖 Task 1（需先完成代码通读）
- Task 5 贯穿 Task 2/3/4（标注差异）
