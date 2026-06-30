-- ======================================================
-- 数据库名称：wuzuniao_yao
-- 用途：存储"无足鸟按时吃药打卡"小程序的计划、通知、打卡记录等业务数据
-- 字符集：utf8mb4，排序规则：utf8mb4_unicode_ci
-- ======================================================

-- 创建数据库（若已存在则跳过）
CREATE DATABASE IF NOT EXISTS `wuzuniao_yao`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `wuzuniao_yao`;

-- ------------------------------------------------------
-- 表：checkin_plans（打卡计划表）
-- 说明：用户创建的每个打卡计划，包含时间范围、状态等
-- ------------------------------------------------------
CREATE TABLE `checkin_plans` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '计划ID',
  `user_id` BIGINT NOT NULL COMMENT '创建者用户ID（关联 users.id）',
  `name` VARCHAR(100) NOT NULL COMMENT '计划名称',
  `remark` VARCHAR(255) NULL COMMENT '备注/描述',
  `start_date` DATE NOT NULL COMMENT '打卡开始日期',
  `end_date` DATE NOT NULL COMMENT '打卡结束日期',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-进行中，0-已结束',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='打卡计划主表';

-- ------------------------------------------------------
-- 表：plan_checkin_times（每日打卡时间点表）
-- 说明：每个计划可设置多个打卡时刻（如 08:00、20:00）
-- ------------------------------------------------------
CREATE TABLE `plan_checkin_times` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '时间点ID',
  `plan_id` BIGINT NOT NULL COMMENT '所属计划ID（关联 checkin_plans.id）',
  `checkin_time` TIME NOT NULL COMMENT '每日打卡时刻（HH:MM:SS）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  INDEX `idx_plan_id` (`plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每个计划的多个打卡时间点';

-- ------------------------------------------------------
-- 表：notification_channels（通知渠道配置表）
-- 说明：用户预配置的各种通知方式（邮件、短信、微信等）
-- ------------------------------------------------------
CREATE TABLE `notification_channels` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '渠道ID',
  `user_id` BIGINT NOT NULL COMMENT '所属用户ID（关联 users.id）',
  `channel_type` VARCHAR(20) NOT NULL COMMENT '通知类型（如 email、sms、wechat）',
  `channel_value` VARCHAR(255) NOT NULL COMMENT '接收地址（邮箱、手机号、openid等）',
  `enabled` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用（true-启用，false-停用）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_user_id` (`user_id`),
  UNIQUE INDEX `uk_user_type_value` (`user_id`, `channel_type`, `channel_value`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户通知渠道配置（可复用于多个计划）';

-- ------------------------------------------------------
-- 表：plan_notification_channels（计划-通知渠道关联表）
-- 说明：多对多关联，一个计划可绑定多个渠道，一个渠道可用于多个计划
-- ------------------------------------------------------
CREATE TABLE `plan_notification_channels` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '关联记录ID',
  `plan_id` BIGINT NOT NULL COMMENT '计划ID（关联 checkin_plans.id）',
  `channel_id` BIGINT NOT NULL COMMENT '渠道ID（关联 notification_channels.id）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关联创建时间',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_plan_channel` (`plan_id`, `channel_id`),
  INDEX `idx_plan_id` (`plan_id`),
  INDEX `idx_channel_id` (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='计划与通知渠道的绑定关系（多对多）';

-- ------------------------------------------------------
-- 表：notification_logs（通知发送记录表）
-- 说明：记录每次系统触发的通知发送结果，用于追踪和重试
-- ------------------------------------------------------
CREATE TABLE `notification_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `plan_id` BIGINT NOT NULL COMMENT '关联计划ID（checkin_plans.id）',
  `channel_id` BIGINT NOT NULL COMMENT '使用的渠道ID（notification_channels.id）',
  `user_id` BIGINT NOT NULL COMMENT '接收者用户ID（冗余，方便查询）',
  `send_time` DATETIME NOT NULL COMMENT '发送时间（实际触发时间）',
  `status` TINYINT NOT NULL COMMENT '发送状态：0-成功，1-失败，2-未读',
  `error_msg` VARCHAR(255) NULL COMMENT '失败时的错误信息',
  PRIMARY KEY (`id`),
  INDEX `idx_plan_id` (`plan_id`),
  INDEX `idx_channel_id` (`channel_id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_send_time` (`send_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知发送历史日志';

-- ------------------------------------------------------
-- 表：checkin_records（打卡记录表）
-- 说明：存储用户每次实际打卡的操作记录
-- ------------------------------------------------------
CREATE TABLE `checkin_records` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` BIGINT NOT NULL COMMENT '打卡用户ID（关联 users.id）',
  `plan_id` BIGINT NOT NULL COMMENT '所属计划ID（checkin_plans.id）',
  `plan_time_id` BIGINT NOT NULL COMMENT '对应的打卡时间点ID（plan_checkin_times.id）',
  `actual_time` DATETIME NOT NULL COMMENT '实际打卡时间戳',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_user_plan_time_day` (`user_id`, `plan_id`, `plan_time_id`, DATE(`actual_time`)) COMMENT '同一天同一时间点只能打卡一次',
  INDEX `idx_plan_id` (`plan_id`),
  INDEX `idx_plan_time_id` (`plan_time_id`),
  INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户打卡记录（支持多个时间点）';
