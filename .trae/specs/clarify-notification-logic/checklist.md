# Checklist

## 文档完整性
- [x] spec.md 已新增「匹配区间定义」Requirement，引用 clarify-checkin-logic spec
- [x] spec.md 已完整描述准时触发条件（按对应匹配区间内打卡记录数 < 1 判定，每个提醒时间独立）
- [x] spec.md 已完整描述两档催办：档位1=10分钟、档位2=1小时与中点择先到达者
- [x] spec.md 催办触发前提已改为「该提醒时间对应匹配区间内无打卡记录」
- [x] spec.md 已说明末次提醒（无下一次）档位2固定为 1 小时
- [x] spec.md 已说明中点定义 = (本次提醒 + 下一次提醒) / 2
- [x] spec.md 已描述防重去重键 (plan_time_id, trigger_type, notify_date, channel_id)
- [x] spec.md 已描述站内信发送方式（写 notification_logs，status=未读）
- [x] spec.md 已描述邮件发送方式（channel_value 作 SMTP 与源邮箱、users.email 收件、结果入 logs）
- [x] spec.md 已在 What Changes 标注与现有代码的关键冲突点（含触发判定对象变更）
- [x] spec.md 已在 REMOVED 标注移除的 5分钟/30分钟固定催办、按计划当天总记录数判定准时触发

## 冲突覆盖正确性
- [x] 催办档位以新逻辑为准（10分钟 + 1小时或中点择先），非旧的 5/30/60 分钟
- [x] trigger_type 语义变更已记录（0/1/2 三值）
- [x] 准时与催办触发判定均改为按匹配区间判定（非计划当天总数、非 plan_time_id 维度）
- [x] 所有冲突点均注明「以本 spec 为准」

## 与现有代码对齐
- [x] 站内信发送方式与现有 `scheduler_service.py` 中 `_send_via_channel` 站内信分支一致
- [x] 邮件发送方式与现有 `_send_email` 流程一致（解析配置→查收件人→解密密码→SMTP→记录日志）
- [x] 防重键与现有 `_already_sent` 查询字段一致
- [x] 匹配区间定义与 clarify-checkin-logic spec 及 checkin_service `_get_match_intervals` 一致
