# Tasks

本 spec 为纯文档梳理 + 修订任务，不涉及代码改动，任务聚焦于逻辑梳理的覆盖度与准确性。所有梳理工作以用户本次给出的新要求为准，覆盖与现有代码的冲突点。

- [ ] Task 1: 通读 `frontend/src/pages/index/record.vue` 现有显示逻辑，提取日历小绿点标注、每日打卡明细展示、数据加载触发的现有实现，作为对比基准。
  - [ ] SubTask 1.1: 读取 `record.vue` 模板与 `<script setup>`，定位 `checkedDays`、`dayRecords`、`loadMonthCheckins`、`loadDayCheckins`、`calendarDays` 等核心逻辑
  - [ ] SubTask 1.2: 分析现有小绿点标注依据（基于 `checkin_records` 表的 `listMonthCheckins` 返回值）
  - [ ] SubTask 1.3: 分析现有每日打卡明细展示规则（`listDayCheckins` 返回的明细行结构、已打卡/未打卡/空状态的视觉表现）
  - [ ] SubTask 1.4: 分析现有孤儿记录处理逻辑（后端 `list_day_detail` 的 3b 分支）

- [ ] Task 2: 通读后端 `backend/app/services/checkin_service.py` 的 `list_by_month` 与 `list_day_detail` 实现，提取现有查询逻辑与匹配区间算法，作为对比基准。
  - [ ] SubTask 2.1: 读取 `list_by_month` 方法，确认小绿点依据为 `checkin_records` 表查询
  - [ ] SubTask 2.2: 读取 `list_day_detail` 方法，确认明细行结构为每记录一行 + 孤儿记录单独展示
  - [ ] SubTask 2.3: 读取 `_get_match_intervals` 方法，确认匹配区间算法（按相邻中点划分，全天 0:00-24:00 无留白）

- [ ] Task 3: 以用户本次给出的新要求为准，在 `spec.md` 中完整描述以下内容：
  - [ ] SubTask 3.1: 页面打开时的数据加载触发时机（每次打开都查询 `checkin_plans` 与 `checkin_records`）
  - [ ] SubTask 3.2: 日历小绿点标注规则——保持基于 `checkin_records` 表当天有打卡记录（与现有逻辑一致，不变更）
  - [ ] SubTask 3.3: 每日打卡明细展示规则——有计划时展示每个提醒时间一行；无计划时不显示明细卡片
  - [ ] SubTask 3.4: 打卡记录与提醒时间的匹配区间——参考首页打卡逻辑的匹配区间算法（中点划分，全天无留白）
  - [ ] SubTask 3.5: 多次打卡的展示规则——同一提醒时间合并为一行，最多显示首末两次打卡时间，次数 ≤ 2 时不显示总次数，> 2 时以数字显示
  - [ ] SubTask 3.6: 打卡时间显示前提——必须有对应提醒时间，孤儿记录不独立显示
  - [ ] SubTask 3.7: 明细行数据结构——新增 `first_actual_time`、`last_actual_time`、`checkin_count` 字段，移除 `plan_id` 字段

- [ ] Task 4: 在 `spec.md` 附录中列出新旧逻辑冲突点对照表，明确以新逻辑为准。
  - [ ] SubTask 4.1: 对照表标注小绿点标注依据保持不变（基于 `checkin_records` 表）
  - [ ] SubTask 4.2: 对照表包含无计划当天行为差异
  - [ ] SubTask 4.3: 对照表包含多次打卡展示差异（次数 ≤ 2 不显示，> 2 显示）
  - [ ] SubTask 4.4: 对照表包含孤儿记录处理差异
  - [ ] SubTask 4.5: 对照表包含明细行数据结构差异（移除 `plan_id`）
  - [ ] SubTask 4.6: 对照表标注匹配区间算法与数据加载触发保持不变

# 实施任务

- [x] Task 5: 修改后端 `backend/app/services/checkin_service.py` 的 `list_day_detail` 方法
  - [x] SubTask 5.1: 简化记录查询（移除 outer join，仅查询 CheckinRecord）
  - [x] SubTask 5.2: 同一提醒时间的多条打卡记录合并为一行，返回 first_actual_time、last_actual_time、checkin_count
  - [x] SubTask 5.3: 移除 plan_id 字段，移除 actual_time 字段
  - [x] SubTask 5.4: 移除孤儿记录展示逻辑（3b 分支）及 matched_record_ids 集合
  - [x] SubTask 5.5: 按 notification_time 升序排序

- [x] Task 6: 修改前端 `frontend/src/pages/index/record.vue`
  - [x] SubTask 6.1: 更新 `selectedDayDetail` 计算属性，无计划时隐藏明细卡片
  - [x] SubTask 6.2: 移除"当天暂无打卡记录"空状态 HTML 块及对应 CSS
  - [x] SubTask 6.3: 更新明细行模板：使用 first_actual_time/last_actual_time，次数>2 时显示"共N次"
  - [x] SubTask 6.4: 新增次数显示的 CSS 样式（含平板断点）
  - [x] SubTask 6.5: 更新 JSDoc 注释

- [x] Task 7: 更新 `更新记录.md`

# Task Dependencies
- Task 2 依赖 Task 1（需先理解前端现有逻辑作为对比基准）
- Task 3 依赖 Task 1 与 Task 2（需先通读前后端现有逻辑）
- Task 4 贯穿 Task 3（对照表汇总冲突点）
- Task 5 与 Task 6 可并行（后端与前端独立修改）
- Task 7 依赖 Task 5 与 Task 6 完成
