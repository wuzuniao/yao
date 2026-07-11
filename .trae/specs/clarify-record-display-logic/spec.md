# 打卡记录页（record.vue）显示逻辑梳理 Spec

## Why

记录页（`frontend/src/pages/index/record.vue`）的打卡记录显示逻辑涉及日历小绿点标注、每日打卡明细展示、提醒时间与打卡记录的匹配等多条规则。现有实现与本次给出的新要求存在多处冲突。本文档先梳理现有显示逻辑，再按本次给出的新要求修订，形成统一的逻辑基准，作为后续代码修改的输入。

> **重要**：本 spec 以用户本次给出的新要求为准。若与现有代码逻辑存在冲突，一律以本 spec 为准。

## What Changes

- 本 spec 为**纯文档梳理 + 修订**，不修改任何代码。
- 输出：完整描述记录页的显示逻辑（含现有逻辑梳理 + 新要求覆盖的修订点）。
- 与现有逻辑的**关键冲突点**（已以新逻辑覆盖）：
  - **无计划当天行为**：旧显示"当天暂无打卡记录"空状态 → 新不显示每日打卡明细
  - **多次打卡展示**：旧每条记录单独占一行 → 新同一提醒时间合并为一行，最多显示第一次和最后一次打卡时间，次数 ≤ 2 时不显示总次数，> 2 时以数字显示
  - **孤儿记录处理**：旧单独展示未匹配到提醒时间的打卡记录 → 新不独立显示，打卡时间显示前提是必须有对应的提醒时间
  - **明细行数据结构**：旧单字段 `actual_time` → 新含首次打卡时间、末次打卡时间、总次数；移除 `plan_id` 字段

## Impact

- 受影响代码（仅作为梳理对象，不改动）：
  - [record.vue](file:///d:/wuzuniao/yao/frontend/src/pages/index/record.vue)
  - [checkin.js](file:///d:/wuzuniao/yao/frontend/src/api/modules/checkin.js)
  - [checkins.py](file:///d:/wuzuniao/yao/backend/app/api/v1/checkins.py)
  - [checkin_service.py](file:///d:/wuzuniao/yao/backend/app/services/checkin_service.py)
- 受影响能力：记录页日历小绿点标注、每日打卡明细展示、提醒时间与打卡记录的匹配区间判定。

***

## 现有逻辑梳理（作为对比基准）

> 以下为现有代码的实现逻辑，仅作为对比基准。最终以"新要求"章节为准。

### 现有：页面打开时的数据加载

- `onShow` 时调用 `loadMonthCheckins()` 加载当月打卡记录日期列表。
- 若已登录且查看当前月份，自动选中今天并调用 `loadDayCheckins(today)` 加载当天详情。
- 其他日期需用户点击日期单元格才触发 `loadDayCheckins(day)`。

### 现有：日历小绿点标注

- 前端调用 `listMonthCheckins(year, month)` → 后端 `/api/v1/checkins/month`。
- 后端 `list_by_month` 查询 `checkin_records` 表，返回当月有打卡记录的日期（day of month）列表。
- 前端 `checkedDays` 数组中包含的日期显示小绿点。
- **依据**：`checkin_records` 表是否有记录。

### 现有：每日打卡明细展示

- 前端调用 `listDayCheckins(dateStr)` → 后端 `/api/v1/checkins/day`。
- 后端 `list_day_detail` 逻辑：
  1. 查询当天所有打卡记录（outer join 计划与提醒时间）。
  2. 查询当天有效的所有计划（`start_date <= day_date <= end_date`，不限制 status）。
  3. 对每个计划的每个提醒时间，按匹配区间判定是否已打卡：
     - 匹配区间内有打卡记录 → **每条记录单独占一行**，`checked=true` + `actual_time`。
     - 匹配区间内无打卡记录 → 单行 `checked=false`，`actual_time=null`。
  4. **孤儿记录**（计划已删除/不在当天有效计划/偏离所有匹配区间）→ 单独展示。
- 明细行字段：`{ plan_id, plan_name, plan_remark, notification_time, checked, actual_time }`。
- 前端展示规则：
  - 已打卡：绿点 + 提醒时间 + `→ HH:MM`（实际打卡时间）+ 计划名称/备注 + 完成图标。
  - 未打卡：灰点 + 提醒时间 + 计划名称/备注。
  - 无数据：显示"当天暂无打卡记录"。

### 现有：匹配区间算法（后端 `_get_match_intervals`）

- 按相邻提醒时间的中点划分，覆盖全天 0:00-24:00 无间隙、无留白。
- 第一次提醒：`[0:00, midpoint(t1, t2)]`。
- 中间提醒：`[midpoint(t_{i-1}, t_i), midpoint(t_i, t_{i+1})]`。
- 最后一次提醒：`[midpoint(t_{n-1}, t_n), 24:00]`。

***

## 新要求（以本章节为准）

## ADDED Requirements

### Requirement: 页面打开时的数据加载触发时机

系统 SHALL 在每次打开记录页面时，从 `checkin_plans` 表和 `checkin_records` 表查询数据并展示。

#### Scenario: 每次打开记录页面

- **WHEN** 用户每次打开记录页面（`onShow` 触发）
- **THEN** 从 `checkin_plans` 表查询打卡计划时间
- **AND** 从 `checkin_records` 表查询打卡记录
- **AND** 将在打卡日期范围内的打卡计划的每次提醒时间，展示在日历下方的每日打卡明细中
- **AND** 在对应日期以小绿点标注

***

### Requirement: 日历小绿点标注规则

系统 SHALL 以 `checkin_records` 表当天是否有打卡记录为依据标注小绿点（与现有逻辑保持一致）。

#### Scenario: 有打卡记录的日期显示小绿点

- **GIVEN** 某日期 `day_date`
- **WHEN** `checkin_records` 表中存在该日期的打卡记录
- **THEN** 该日期在日历上显示小绿点

#### Scenario: 无打卡记录的日期不显示小绿点

- **GIVEN** 某日期 `day_date`
- **WHEN** `checkin_records` 表中不存在该日期的打卡记录
- **THEN** 该日期在日历上**不显示**小绿点

> 说明：小绿点标注依据保持与现有逻辑一致（基于 `checkin_records` 表当天是否有打卡记录），不做变更。

***

### Requirement: 每日打卡明细展示规则

系统 SHALL 在日历下方的每日打卡明细区域，展示选中日期的所有有效计划提醒时间及其打卡情况。

#### Scenario: 选中日期有计划

- **GIVEN** 用户选中某日期 `day_date`
- **WHEN** 存在打卡计划满足 `start_date <= day_date <= end_date` 且有提醒时间
- **THEN** 展示每日打卡明细卡片
- **AND** 卡片中列出该日期所有有效计划的每个提醒时间，每个提醒时间占一行
- **AND** 每行包含：提醒时间、计划名称、计划备注
- **AND** 若该提醒时间的匹配区间内有打卡记录，额外显示打卡时间信息（见"多次打卡的展示规则"）
- **AND** 若该提醒时间的匹配区间内无打卡记录，仅显示提醒时间（不显示打卡时间）

#### Scenario: 选中日期无计划

- **GIVEN** 用户选中某日期 `day_date`
- **WHEN** 不存在任何打卡计划满足 `start_date <= day_date <= end_date`
- **OR** 满足日期范围的计划均无提醒时间
- **THEN** **不显示**每日打卡明细卡片

> ⚠️ 与旧逻辑冲突：旧逻辑在无数据时显示"当天暂无打卡记录"空状态；新逻辑在无计划时不显示明细区域。
> 说明：小绿点是否显示取决于 `checkin_records` 表是否有记录，与是否有计划无关。

***

### Requirement: 打卡记录与提醒时间的匹配区间

系统 SHALL 参考打卡逻辑（`index.vue` 与后端 `_get_match_intervals`）中的匹配区间算法，判定打卡记录是否属于某个提醒时间。

#### 核心定义

- 匹配区间按相邻提醒时间的中点划分，覆盖全天 0:00-24:00，无间隙、无留白。
- **第一次提醒**：匹配区间 = `[0:00, midpoint(t1, t2)]`（从 0 点到与第二次提醒的中点）。
- **中间提醒**：匹配区间 = `[midpoint(t_{i-1}, t_i), midpoint(t_i, t_{i+1})]`（从前一个中点到后一个中点）。
- **最后一次提醒**：匹配区间 = `[midpoint(t_{n-1}, t_n), 24:00]`（从前一个中点到 24 点）。
- 单条提醒时间：匹配区间 = `[0:00, 24:00]`（全天）。

#### Scenario: 判定打卡记录归属

- **GIVEN** 某提醒时间 `t_i` 的匹配区间 `[start, end]`
- **AND** 用户当天的打卡记录列表
- **WHEN** 打卡记录的实际时间（转换为当日分钟数）满足 `start <= minutes < end`
- **THEN** 该打卡记录归属于提醒时间 `t_i`
- **AND** 该提醒时间视为"已打卡"

#### Scenario: 匹配区间内无打卡记录

- **GIVEN** 某提醒时间 `t_i` 的匹配区间 `[start, end]`
- **WHEN** 匹配区间内无任何打卡记录
- **THEN** 该提醒时间视为"未打卡"
- **AND** 仅显示提醒时间，不显示打卡时间

> 说明：匹配区间算法与首页打卡逻辑（`clarify-checkin-logic` spec）完全一致，确保两边判定结果统一。

***

### Requirement: 多次打卡的展示规则

系统 SHALL 对同一提醒时间的匹配区间内有多条打卡记录时，合并为一行展示，最多显示第一次和最后一次打卡时间；次数 ≤ 2 时不显示总次数，> 2 时将总次数以数字显示。

#### Scenario: 匹配区间内有一条打卡记录

- **GIVEN** 某提醒时间 `t_i` 的匹配区间内有一条打卡记录
- **THEN** 该行显示：提醒时间 + 首次打卡时间（`→ HH:MM`）+ 计划名称/备注
- **AND** 不显示总次数（次数 ≤ 2 时不显示）

#### Scenario: 匹配区间内有两条打卡记录

- **GIVEN** 某提醒时间 `t_i` 的匹配区间内有两条打卡记录
- **THEN** 该行合并为一行显示：
  - 提醒时间
  - 首次打卡时间（`→ HH:MM`）
  - 末次打卡时间（`→ HH:MM`）
  - 计划名称/备注
- **AND** 不显示总次数（次数 ≤ 2 时不显示）

#### Scenario: 匹配区间内有多于两条打卡记录

- **GIVEN** 某提醒时间 `t_i` 的匹配区间内有多于两条（≥3）打卡记录
- **THEN** 该行合并为一行显示：
  - 提醒时间
  - 首次打卡时间（`→ HH:MM`）
  - 末次打卡时间（`→ HH:MM`）
  - 总次数（以数字显示，如"共 N 次"）
  - 计划名称/备注
- **AND** 最多只显示第一次和最后一次打卡时间，中间的打卡时间不显示

#### Scenario: 匹配区间内无打卡记录

- **GIVEN** 某提醒时间 `t_i` 的匹配区间内无打卡记录
- **THEN** 该行显示：提醒时间 + 计划名称/备注
- **AND** 不显示打卡时间
- **AND** 不显示次数

> ⚠️ 与旧逻辑冲突：旧逻辑每条打卡记录单独占一行；新逻辑同一提醒时间合并为一行，最多显示首末两次打卡时间，次数 ≤ 2 时不显示总次数，> 2 时以数字显示。

***

### Requirement: 打卡时间显示前提

系统 SHALL 仅在有对应提醒时间的前提下才显示打卡时间，不能独立显示打卡记录。

#### Scenario: 有对应提醒时间的打卡记录

- **GIVEN** 某打卡记录的实际时间落在某提醒时间 `t_i` 的匹配区间内
- **THEN** 该打卡记录依附于提醒时间 `t_i` 显示
- **AND** 打卡时间显示在提醒时间所在行

#### Scenario: 无对应提醒时间的打卡记录（孤儿记录）

- **GIVEN** 某打卡记录的实际时间不落在任何有效提醒时间的匹配区间内
- **OR** 该打卡记录所属的计划已删除/不在当天有效计划范围内
- **THEN** **不显示**该打卡记录
- **AND** 不在明细中独立展示

> ⚠️ 与旧逻辑冲突：旧逻辑将孤儿记录单独展示在明细末尾；新逻辑不显示孤儿记录，打卡时间必须依附于提醒时间。

***

### Requirement: 明细行数据结构（后端响应格式）

系统 SHALL 返回符合新展示规则的明细行数据结构，替代旧的每记录一行的结构。

#### Scenario: 明细行字段定义

- **THEN** 每个提醒时间对应一个明细行，字段包括：
  - `plan_name`：计划名称
  - `plan_remark`：计划备注
  - `notification_time`：提醒时间（`HH:MM` 格式）
  - `checked`：是否已打卡（布尔值）
  - `first_actual_time`：首次打卡时间（ISO 字符串，未打卡时为 `null`）
  - `last_actual_time`：末次打卡时间（ISO 字符串，单次打卡时与 `first_actual_time` 相同，未打卡时为 `null`）
  - `checkin_count`：匹配区间内打卡记录总数（整数，未打卡时为 0）

#### Scenario: 排序规则

- **THEN** 明细行按 `notification_time` 升序排序
- **AND** 同一提醒时间内无需再排序（已合并为一行）

***

## MODIFIED Requirements

无（本 spec 不修改任何既有功能要求，仅为文档梳理 + 修订；标注的差异作为后续代码修改的输入，不在本 spec 内实施）。

## REMOVED Requirements

无。

***

## 附录：新旧逻辑冲突点对照表

| 项目 | 旧逻辑（现有代码） | 新逻辑（以本次为准） |
| --- | --- | --- |
| 小绿点标注依据 | `checkin_records` 表当天有打卡记录 | 保持不变（基于 `checkin_records` 表当天有打卡记录） |
| 无计划当天行为 | 显示"当天暂无打卡记录"空状态 | 不显示每日打卡明细（小绿点仍依据 `checkin_records` 表） |
| 多次打卡展示 | 每条打卡记录单独占一行 | 同一提醒时间合并为一行，最多显示首末两次打卡时间，次数 ≤ 2 时不显示总次数，> 2 时以数字显示 |
| 孤儿记录处理 | 单独展示在明细末尾 | 不显示，打卡时间必须依附于提醒时间 |
| 明细行数据结构 | `{ plan_id, notification_time, checked, actual_time }` | `{ notification_time, checked, first_actual_time, last_actual_time, checkin_count }`（移除 `plan_id`） |
| 匹配区间算法 | 按相邻中点划分，全天 0:00-24:00 无留白 | 保持不变（与首页打卡逻辑一致） |
| 数据加载触发 | `onShow` 加载月度记录 + 自动选中今天 | 保持不变（每次打开页面都查询 `checkin_plans` 与 `checkin_records`） |
