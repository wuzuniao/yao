-- ======================================================
-- 增量变更：新增 user_biometric_tokens 表
-- 用途：存储用户生物识别（指纹）登录凭证，支持 App 端指纹一键登录
--       凭证 31 天有效、可多次使用、每次需带新鲜 SOTER 签名、绑定 device_id
-- 执行顺序：在 create_user_db.sql 之后执行
-- ======================================================

USE `wuzuniao_yonghu`;

CREATE TABLE IF NOT EXISTS `user_biometric_tokens` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` BIGINT NOT NULL COMMENT '关联 users.id',
  `token` VARCHAR(64) NOT NULL COMMENT '生物识别凭证（高熵随机串）',
  `device_id` VARCHAR(64) NOT NULL COMMENT '设备标识（前端首次登录生成的 UUID）',
  `expire_at` DATETIME NOT NULL COMMENT '过期时间（默认 31 天）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_token` (`token`),
  INDEX `idx_user_device` (`user_id`, `device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户生物识别登录凭证（指纹一键登录）';
