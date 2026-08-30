-- ======================================================
-- 增量脚本：计划重复规则 + 结束方式 + 提醒次数/间隔（2026-08-28）
-- 说明：
--   1. checkin_plans 新增重复星期位掩码（repeat_weekdays）、结束方式（end_mode）、
--      目标打卡总次数（total_target_count）三列
--   2. plan_notification_times 新增提醒总次数（followup_count）与自定义间隔
--      （followup_interval_min）两列，实现每个提醒时间点独立的催办配置
--   3. priority 优先级范围由 0-7 收窄为 0-3，存量 >3 的值统一迁移为 3
-- 存量兼容：新列默认值（127/0/NULL/3/10）与既有行为完全一致，无需数据迁移
-- 生产环境按 create_*.sql → add_*.sql（按时间顺序）执行
-- ======================================================

USE `wuzuniao_yao`;

-- ------------------------------------------------------
-- checkin_plans：重复规则与结束方式
-- ------------------------------------------------------
ALTER TABLE `checkin_plans`
  ADD COLUMN `repeat_weekdays` TINYINT NOT NULL DEFAULT 127 COMMENT '重复星期位掩码：bit0=周一…bit6=周日，127=每天，31=工作日，96=周末' AFTER `end_date`,
  ADD COLUMN `end_mode` TINYINT NOT NULL DEFAULT 0 COMMENT '结束方式：0-按end_date，1-按打卡总次数，2-长期不结束（end_date存9999-12-31哨兵）' AFTER `repeat_weekdays`,
  ADD COLUMN `total_target_count` INT NULL COMMENT '目标打卡总次数（end_mode=1时生效，累计按时间点+日期去重计数，达标后自动置status=0）' AFTER `end_mode`;

-- ------------------------------------------------------
-- plan_notification_times：提醒次数与间隔
-- ------------------------------------------------------
ALTER TABLE `plan_notification_times`
  ADD COLUMN `followup_count` INT NOT NULL DEFAULT 3 COMMENT '提醒总次数（含准时）：3=默认三段式（准时+10分钟+1小时或中点），1/2=自定义等间隔' AFTER `notification_time`,
  ADD COLUMN `followup_interval_min` INT NOT NULL DEFAULT 10 COMMENT '自定义等间隔分钟（5-60，followup_count=3时不生效）' AFTER `followup_count`;

-- ------------------------------------------------------
-- priority 范围收窄（0-7 → 0-3）：存量 >3 统一归到 3（最低优先级，排序不变）
-- ------------------------------------------------------
UPDATE `checkin_plans` SET `priority` = 3 WHERE `priority` > 3;
