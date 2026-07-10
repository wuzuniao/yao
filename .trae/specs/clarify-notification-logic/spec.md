# 后端打卡通知逻辑梳理 Spec

## Why

后端定时通知派发逻辑（`backend/app/services/scheduler_service.py` 中的 `NotificationDispatcher`）当前以「5分钟/30分钟/1小时」三档固定催办 + 「打卡记录数 < 提醒时间数」准时触发实现。用户本次给出新的通知逻辑规则，需将其梳理成文档，作为后续代码调整的基准。

> **重要**：本 spec 完全以用户本次给出的逻辑为准。若与现有代码存在冲突，一律以本 spec 为准。

## What Changes

- 本 spec 为**纯文档梳理**，不修改任何代码。
- 输出：完整描述后端打卡任务通知派发的期望行为，覆盖触发条件、催办档位、防重去重、站内信/邮件发送方式。
- 与现有代码的**关键冲突点**（已以新逻辑覆盖）：
  - **催办档位**：旧 5分钟/30分钟/1小时（三档固定）→ 新 10分钟 + 「1小时 与 下一次提醒中点 择先到达者」（两档）
  - **第二档动态化**：旧第二档固定 30 分钟 → 新为 `min(提醒时间+1小时, 与下一次提醒的中点)`；末次提醒（无下一次）第二档固定为 1 小时
  - **trigger_type 语义变更**：旧 0/1/2/3 四值（准时/超5分/超30分/超1小时）→ 新 0/1/2 三值（准时/超10分钟/1小时或中点催办）
  - **FOLLOWUP_OFFSETS 结构变更**：旧为固定偏移列表 `[(1,5),(2,30),(3,60)]` → 新需按提醒时间点动态计算第二档触发时间
  - **触发判定对象变更**：旧准时触发用「计划当天总打卡记录数 < 提醒时间数」、旧催办用「该提醒时间点（plan_time_id）当天无打卡记录」→ 新统一改为「该提醒时间对应匹配区间内打卡记录数 < 1（无打卡记录）」，每个提醒时间独立按匹配区间判定（匹配区间定义同 `clarify-checkin-logic` spec）

## Impact

- 受影响代码（仅作为梳理对象，不改动）：
  - [scheduler_service.py](file:///d:/wuzuniao/yao/backend/app/services/scheduler_service.py)（`NotificationDispatcher` 派发器）
  - [notification_log.py schema](file:///d:/wuzuniao/yao/backend/app/schemas/notification_log.py)（触发类型常量 `TRIGGER_*`、`FOLLOWUP_OFFSETS`、`TRIGGER_DESC`）
  - [email_service.py](file:///d:/wuzuniao/yao/backend/app/services/email_service.py)（`send_notification`）
  - [notification_channel_service.py](file:///d:/wuzuniao/yao/backend/app/services/notification_channel_service.py)（`parse_email_channel_value`）
- 受影响能力：定时通知派发、催办触发判定、防重去重、站内信写入、邮件发送。

---

## ADDED Requirements

### Requirement: 通知派发总体规则

系统 SHALL 按以下规则为每个进行中（status=1）且当日有效（start_date ≤ today ≤ end_date）的打卡计划派发通知：

1. 遍历计划的所有提醒时间点（plan_notification_times）
2. 对每个提醒时间点，按「准时触发」与「催办触发」两类检查
3. 通过计划绑定的通知渠道（plan_notification_channels → notification_channels）发送
4. 渠道 `enabled=false` 时跳过该渠道

#### Scenario: 计划当日有效
- **WHEN** 计划 status=1 且 start_date ≤ today ≤ end_date
- **THEN** 该计划的提醒时间点参与当日通知派发

#### Scenario: 计划不在有效期
- **WHEN** 计划 status≠1 或 today 不在 [start_date, end_date]
- **THEN** 跳过该计划，不派发通知

### Requirement: 匹配区间定义

系统 SHALL 按 `clarify-checkin-logic` spec 的「打卡记录匹配判定」定义每个提醒时间的匹配区间，用于通知触发的打卡记录数判定。匹配区间按相邻提醒的中点划分，覆盖全天 0:00-24:00，无间隙、无留白：

- 第一次提醒 `t_1` 的匹配区间：`[0:00, midpoint(t_1, t_2)]`
- 中间提醒 `t_i` 的匹配区间：`[midpoint(t_{i-1}, t_i), midpoint(t_i, t_{i+1})]`
- 最后一次提醒 `t_n` 的匹配区间：`[midpoint(t_{n-1}, t_n), 24:00]`

> 中点 = (本次提醒时间 + 相邻提醒时间) / 2。单提醒时间时匹配区间为 `[0:00, 24:00]`（全天）。每个提醒时间独立拥有一个匹配区间，通知触发判定均以「该提醒时间对应匹配区间内的打卡记录数」为依据。

#### Scenario: 单提醒时间的匹配区间
- **GIVEN** 计划只有 1 个提醒时间 `t_1`
- **THEN** `t_1` 的匹配区间 = `[0:00, 24:00]`（全天）

#### Scenario: 多提醒时间的匹配区间
- **GIVEN** 计划有提醒时间 `t_1 < t_2 < ... < t_n`
- **THEN** 每个 `t_i` 独立拥有一个匹配区间，相邻区间在中点处分界，全天无留白

### Requirement: 站内信发送方式

接收方式为站内信时，系统 SHALL 在 `notification_logs` 表写入一条记录：
- `channel_id` = 该用户站内信渠道 ID
- `status` = 未读（2）
- 不调用任何外部服务，写库即视为「发送完成」

#### Scenario: 站内信发送
- **WHEN** 触发通知且渠道为站内信
- **THEN** 在 notification_logs 插入记录（status=2 未读），不调用外部服务

### Requirement: 邮件发送方式

接收方式为邮件时，系统 SHALL：
1. 从 `notification_channels.channel_value`（JSON）读取 SMTP 配置（`smtp_host`、`smtp_port`、`email`、加密的 `password`）
2. 以 `channel_value.email` 作为 SMTP 登录账号与发件邮箱（即 SMTP 服务器和源邮箱）
3. 从 `users` 表读取该用户 `email` 作为收件邮箱
4. 解密 `password`（AES-256-GCM）
5. 通过 SMTP 发送（端口 465 走 SSL，其他端口走 STARTTLS）
6. 将发送结果（成功/失败 + 错误信息）记录到 `notification_logs`

#### Scenario: 邮件发送成功
- **WHEN** 触发通知且渠道为邮件，SMTP 发送成功
- **THEN** notification_logs 记录 status=0（成功），error_msg 为空

#### Scenario: 邮件发送失败
- **WHEN** SMTP 发送抛出异常
- **THEN** notification_logs 记录 status=1（失败），error_msg 为错误信息（截断 255 字符）

#### Scenario: 用户未绑定邮箱
- **WHEN** 渠道为邮件但 users.email 为空
- **THEN** 不发送，notification_logs 记录 status=1，error_msg 记录「用户未绑定邮箱」

#### Scenario: 邮件渠道配置解析失败
- **WHEN** channel_value JSON 解析失败
- **THEN** 不发送，notification_logs 记录 status=1，error_msg 记录「邮件渠道配置解析失败」

---

## MODIFIED Requirements

### Requirement: 准时触发条件

到达打卡计划的提醒时间时，系统 SHALL 按以下条件判定是否发送准时通知（trigger_type=0）：
- **该提醒时间对应匹配区间内打卡记录数 < 1**（即匹配区间内无打卡记录）→ 发送
- 每个提醒时间独立判定，互不影响

> 说明：旧逻辑为「计划当天总打卡记录数 < 提醒时间数」，新逻辑改为按「对应匹配区间内无打卡记录」判定，与首页打卡匹配区间一致。单提醒时间时匹配区间为全天，即「当天未打卡」。

#### Scenario: 匹配区间内无打卡记录
- **WHEN** 当前时间命中某提醒时间，且该提醒时间对应匹配区间内无打卡记录
- **THEN** 发送准时通知

#### Scenario: 匹配区间内已有打卡记录
- **WHEN** 当前时间命中某提醒时间，但该提醒时间对应匹配区间内已有打卡记录
- **THEN** 不发送准时通知

#### Scenario: 多提醒时间各自独立判定
- **WHEN** 计划有 3 个提醒时间，第 1 个匹配区间内已有打卡记录，第 2 个匹配区间内无打卡记录
- **AND** 当前时间命中第 2 个提醒时间
- **THEN** 第 1 个提醒时间不发送（匹配区间已有记录），第 2 个提醒时间发送准时通知

### Requirement: 催办触发条件（两档）

系统 SHALL 在提醒时间过后，按以下两档催办规则检查并发送通知。**前提**：该提醒时间对应匹配区间内无打卡记录（匹配区间内打卡记录数 < 1）。

**档位1（trigger_type=1）：超过提醒时间 10 分钟**
- 触发时间点 = 提醒时间 + 10 分钟
- 条件：该提醒时间对应匹配区间内无打卡记录

**档位2（trigger_type=2）：1小时 与 下一次提醒中点 择先到达者**
- 若存在下一次提醒时间：档位2触发时间点 = `min(提醒时间+1小时, (本次提醒时间+下一次提醒时间)/2 中点)`
- 若为末次提醒（无下一次）：档位2触发时间点 = 提醒时间 + 1 小时
- 条件：该提醒时间对应匹配区间内无打卡记录
- 去重：档位2当天对同一提醒时间点同一渠道只发一次（先到达者触发后，另一个候选时间不再触发）

> 中点定义：(本次提醒时间 + 下一次提醒时间) / 2，与首页打卡匹配区间划分的中点概念一致。

#### Scenario: 中点早于 1 小时
- **WHEN** 提醒时间 8:00，下一次 9:30，中点 8:45，1 小时为 9:00
- **THEN** 档位2在 8:45 触发（先到达），9:00 不再触发档位2

#### Scenario: 1 小时早于中点
- **WHEN** 提醒时间 8:00，下一次 12:00，中点 10:00，1 小时为 9:00
- **THEN** 档位2在 9:00 触发（先到达），10:00 不再触发档位2

#### Scenario: 1 小时与中点重合
- **WHEN** 提醒时间 8:00，下一次 10:00，中点 9:00，1 小时为 9:00
- **THEN** 档位2在 9:00 触发一次

#### Scenario: 末次提醒无中点
- **WHEN** 提醒时间是该计划最后一次提醒，无下一次
- **THEN** 档位2 = 提醒时间 + 1 小时，无中点催办

#### Scenario: 催办时匹配区间已有打卡记录
- **WHEN** 催办时间点到达，但该提醒时间对应匹配区间内已有打卡记录
- **THEN** 不发送催办

### Requirement: 防重去重

系统 SHALL 以 `(plan_time_id, trigger_type, notify_date, channel_id)` 为去重键，当日同一提醒时间点同一触发档位同一渠道只发送一次通知（含失败记录也占去重位）。

#### Scenario: 已发送过
- **WHEN** 当日该提醒时间点该档位该渠道已存在 notification_logs 记录
- **THEN** 跳过，不重复发送

---

## REMOVED Requirements

### Requirement: 5 分钟固定催办
**Reason**: 第一档催办从 5 分钟改为 10 分钟。
**Migration**: `trigger_type=1` 语义从「超时 5 分钟」变更为「超时 10 分钟」。

### Requirement: 30 分钟固定催办
**Reason**: 新催办逻辑将第二档改为「1 小时与中点择先到达者」，不再有固定 30 分钟催办。
**Migration**: `trigger_type=2` 语义从「超时 30 分钟」变更为「1 小时或中点催办」；旧 `trigger_type=3`（超时 1 小时）合并入新 `trigger_type=2`，`FOLLOWUP_OFFSETS` 由固定偏移列表改为按提醒时间点动态计算。

### Requirement: 按计划当天总打卡记录数判定准时触发
**Reason**: 准时触发判定从「计划当天总打卡记录数 < 提醒时间数」改为「该提醒时间对应匹配区间内无打卡记录」，每个提醒时间独立判定。
**Migration**: 准时触发查询从 `_count_checkins`（计划维度总数）改为按匹配区间查询打卡记录数；催办查询从 `_has_checkin_for_slot`（plan_time_id 维度）改为按匹配区间查询，与准时触发统一判定维度。
