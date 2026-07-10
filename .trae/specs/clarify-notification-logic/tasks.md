# Tasks

- [x] Task 1: 梳理后端现有通知派发逻辑
  - 阅读 `backend/app/services/scheduler_service.py`（NotificationDispatcher）
  - 阅读 `backend/app/schemas/notification_log.py`（触发类型常量、FOLLOWUP_OFFSETS）
  - 阅读 `backend/app/services/email_service.py`（send_notification）
  - 阅读 `backend/app/services/notification_channel_service.py`（parse_email_channel_value）
  - 梳理：准时触发条件、三档催办（5/30/60分钟）、防重键、站内信/邮件发送流程

- [x] Task 2: 对比用户给出的通知逻辑与现有代码，标注冲突点
  - 准时触发：旧「计划当天总记录数<提醒时间数」→ 新「对应匹配区间内无打卡记录」，每个提醒时间独立判定（含催办统一改匹配区间）
  - 催办档位：旧 5/30/60 分钟三档固定 → 新 10分钟 + 「1小时与中点择先到达者」两档
  - trigger_type 语义：旧 0/1/2/3 四值 → 新 0/1/2 三值
  - 末次提醒催办：无中点，档位2固定为 1 小时
  - 站内信/邮件发送方式：与现有代码一致，仅澄清表述

- [x] Task 3: 形成本 spec.md 文档
  - 匹配区间定义（引用 clarify-checkin-logic spec）
  - 准时触发条件（按匹配区间判定，每个提醒时间独立）
  - 两档催办触发条件（10分钟 + 1小时或中点择先，前提为匹配区间内无打卡记录）
  - 防重去重键
  - 站内信写入方式（status=未读）
  - 邮件发送方式（channel_value 作 SMTP、users.email 收件、结果入 logs）
  - REMOVED：5分钟/30分钟固定催办、按计划当天总记录数判定准时触发

- [x] Task 4: 同步更新 `目录结构.json` 与 `更新记录.md`
  - `目录结构.json`：新增 `.trae/specs/clarify-notification-logic/` 目录说明
  - `更新记录.md`：追加本次通知逻辑文档梳理的变更记录

- [x] Task 5: 修正触发判定为匹配区间（用户追加）
  - 准时触发：从「计划当天总打卡记录数 < 提醒时间数」改为「该提醒时间对应匹配区间内打卡记录数 < 1」
  - 催办触发前提：从「该提醒时间点（plan_time_id）当天无打卡记录」改为「该提醒时间对应匹配区间内无打卡记录」
  - 新增「匹配区间定义」Requirement（引用 clarify-checkin-logic spec）
  - REMOVED 新增「按计划当天总打卡记录数判定准时触发」

- [x] Task 6: 修改 notification_log schema 常量
  - trigger_type：0=准时、1=超10分钟、2=1小时或中点催办（移除旧 3=超1小时）
  - FOLLOWUP_OFFSETS 重构：档位1固定10分钟，档位2动态（移除固定偏移列表）
  - TRIGGER_DESC 更新

- [x] Task 7: 重写 scheduler_service.py NotificationDispatcher
  - 准时触发：按匹配区间查询打卡记录数 < 1
  - 档位1：提醒时间+10分钟，按匹配区间查询
  - 档位2：min(提醒+1小时, 中点) 择先，末次为提醒+1小时；按匹配区间查询
  - 跨天档位2处理（末次提醒+1小时跨天映射）
  - 复用 checkin_service._get_match_intervals 逻辑
  - 移除 _count_checkins / _has_checkin_for_slot，改为按匹配区间查询

- [x] Task 8: 更新 scheduler_service.py 模块文档字符串
  - 反映新的两档催办与匹配区间判定

- [x] Task 9: 同步更新目录结构.json 与更新记录.md
  - 目录结构.json：更新 scheduler_service.py 与 notification_log schema 描述
  - 更新记录.md：追加本次通知逻辑重写的变更记录

# Task Dependencies
- Task 3 depends on Task 1, Task 2
- Task 5 depends on Task 3
- Task 4 depends on Task 5
- Task 7 depends on Task 6
- Task 8 depends on Task 7
- Task 9 depends on Task 8
