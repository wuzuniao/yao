# Tasks

本 spec 为纯文档梳理任务，不涉及代码改动，任务聚焦于逻辑梳理的覆盖度与准确性。所有梳理工作以用户本次给出的逻辑为准，覆盖与旧 spec 的冲突点。

- [x] Task 1: 通读 `frontend/src/pages/index/index.vue` 打卡相关代码，提取现有状态机判定逻辑、时间窗口算法、图标与文字映射、刷新机制，作为对比基准。
  - [x] SubTask 1.1: 读取 `index.vue` 模板与 `<script setup>`，定位 `checkinState`、`isCheckinDone`、`isWaiting`、`isButtonDisabled`、`checkinText`、`checkinIcon` 等计算属性
  - [x] SubTask 1.2: 分析 `checkinState` 的四种状态（disabled/waiting/active/done）判定条件与现有时间窗口算法（旧 `t-60` 逻辑）
  - [x] SubTask 1.3: 分析 `handleCheckin`、`handleLongPress`、`loadTodayCheckins`、定时器、`onShow` 等交互与刷新机制
  - [x] SubTask 1.4: 分析任务切换（`handleSecondaryClick`、`handleSelectTask`）对打卡状态的联动影响
- [x] Task 2: 以用户本次给出的逻辑为准，在 `spec.md` 中完整描述以下内容：
  - [x] SubTask 2.1: 按钮四种状态的视觉表现（背景色、图标、文字、可点击性）
  - [x] SubTask 2.2: 三种"无打卡任务"（disabled）场景：未登录、未创建计划、不在打卡日期范围
  - [x] SubTask 2.3: 匹配区间划分规则——**新逻辑：开始打卡时间 = t1-120（前 2 小时），第一个提醒匹配区间从 0:00 开始，最后一个到 24:00 结束**
  - [x] SubTask 2.4: 打卡记录匹配判定——按匹配区间判定，第一个提醒从 0 点开始匹配，最后一个到 24 点
  - [x] SubTask 2.5: 一天时间流程图——单提醒（12 点）、双提醒（8 点+20 点）、多提醒通用规则
  - [x] SubTask 2.6: 打卡成功后按钮状态变化（即时转绿、不弹窗、单击拦截）
  - [x] SubTask 2.7: "已打卡"状态持续时长——到匹配区间结束或 24:00
  - [x] SubTask 2.8: 长按 3 秒重置机制（waiting/done → active）
  - [x] SubTask 2.9: 打卡防抖规则（新增：同一任务 3 秒内只允许点击一次）
  - [x] SubTask 2.10: 图标状态自动刷新机制（每分钟定时器、时间流逝边界说明、onShow 刷新）
- [x] Task 3: 描述任务卡片交互逻辑：
  - [x] SubTask 3.1: 打卡只针对主要卡片任务
  - [x] SubTask 3.2: 点击主要卡片无反应
  - [x] SubTask 3.3: 点击次要卡片互换，再次点击再互换
  - [x] SubTask 3.4: 点击次要卡片"..."展开任务列表，选择任务替换到主要卡片
- [x] Task 4: 描述任务卡片默认显示顺序：
  - [x] SubTask 4.1: 只显示进行中任务（当前时间在打卡日期范围内）
  - [x] SubTask 4.2: 1 个任务只显示主要卡片；2 个任务显示主要+次要不显示"..."；3+任务显示主要+次要+"..."
  - [x] SubTask 4.3: 主要卡片优先级规则——当前时间在提醒时间前后 2 小时范围内的优先；都在范围内时优先级高的为主；优先级相同时先创建的为主
- [x] Task 5: 在 `spec.md` 附录中列出新旧逻辑冲突点对照表，明确以新逻辑为准。
- [x] Task 6: 根据用户反馈修正打卡记录匹配区间规则：
  - [x] SubTask 6.1: 第一次提醒匹配区间从 **0:00** 开始（因之前无其他提醒）
  - [x] SubTask 6.2: 第二次提醒匹配区间起始：间隔>4h 为 t2-120；间隔≤4h 为中点的后半部分
  - [x] SubTask 6.3: 最后一次提醒匹配区间到 **24:00** 结束（因之后无其他提醒）
  - [x] SubTask 6.4: 间隔>4h 时相邻匹配区间之间可能存在间隙，间隙内状态为 active（可补打卡）
- [x] Task 7: 补充多提醒通用规则的"每分钟检查"说明，参考双提醒时间示例
- [x] Task 8: 补充"用户不在线时不检查"规则：
  - [x] SubTask 8.1: 页面 `onHide` 时清除 `refreshTimer`，停止定时刷新
  - [x] SubTask 8.2: 用户重新回到页面（`onShow`）时重启定时器并立即同步一次打卡记录
  - [x] SubTask 8.3: 在附录对照表中标注刷新机制差异
- [x] Task 9: 统一按相邻中点划分匹配区间，确保全天无留白（最终修正）：
  - [x] SubTask 9.1: 移除"间隔>4h"和"间隔≤4h"的区分逻辑，匹配区间一律按相邻提醒的中点划分
  - [x] SubTask 9.2: 第一次提醒匹配区间 = [0:00, midpoint(t1, t2)]；最后一次 = [midpoint(t_{n-1}, t_n), 24:00]；中间 = [midpoint, midpoint]
  - [x] SubTask 9.3: 更新 spec.md 顶部 What Changes、done 状态持续时长、示例 2、附录对照表，全部统一为按中点划分
  - [x] SubTask 9.4: 更新 checklist.md，移除"间隔>4h 存在间隙"的检查点，改为"全天无留白"
  - [x] SubTask 9.5: 更新 tasks.md，增加 Task 9 记录本次修正

# Task Dependencies
- Task 2/3/4 依赖 Task 1（需先通读代码理解现有逻辑作为对比基准）
- Task 5 贯穿 Task 2/3/4（对照表汇总冲突点）
- Task 6/7/8 为用户反馈后的修正，依赖 Task 2 已完成
- Task 9 为最终修正，统一按中点划分，依赖 Task 6 已完成（Task 6 的间隔区分逻辑被 Task 9 覆盖）
