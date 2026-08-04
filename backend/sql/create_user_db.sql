-- ======================================================
-- 数据库名称：wuzuniao_yonghu
-- 用途：存储多个小程序共用的用户认证信息与账户绑定关系
-- 字符集：utf8mb4，排序规则：utf8mb4_unicode_ci
-- ======================================================

-- 创建数据库（若已存在则跳过）
CREATE DATABASE IF NOT EXISTS `wuzuniao_yonghu`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `wuzuniao_yonghu`;

-- ------------------------------------------------------
-- 表：users（用户主表）
-- 说明：存储用户核心身份信息，邮箱作为跨小程序唯一主账号标识
-- ------------------------------------------------------
CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户内部ID（自增主键）',
  `username` VARCHAR(15) NULL COMMENT '展示昵称（可为空，前端自行处理占位）',
  `email` VARCHAR(100) NULL COMMENT '邮箱（跨小程序唯一主账号，业务层已验证）',
  `password_hash` VARCHAR(255) NULL COMMENT '密码哈希（微信登录用户为空）',
  `signature` VARCHAR(70) NULL COMMENT '个性签名',
  `avatar_url` VARCHAR(500) NULL COMMENT '头像URL',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-正常，0-待删除（后台任务1分钟后清理）',
  `role` TINYINT NOT NULL DEFAULT 0 COMMENT '角色：0-普通用户（默认），7-管理员',
  `last_login_at` DATETIME NULL COMMENT '最后登录时间',
  `token_invalid_before` DATETIME NULL COMMENT '早于此时间签发的 token 一律失效（改密码/重置密码/删除账号/退出登录后设置）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `idx_email` (`email`),
  UNIQUE INDEX `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户核心主表（邮箱作为主账号标识）';

-- ------------------------------------------------------
-- 表：user_miniapp_accounts（用户-小程序绑定关系表）
-- 说明：记录每个用户在不同小程序下的 openid 和 appid 映射
-- ------------------------------------------------------
CREATE TABLE `user_miniapp_accounts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` BIGINT NOT NULL COMMENT '关联 users.id',
  `app_id` VARCHAR(64) NOT NULL COMMENT '微信小程序 AppID',
  `openid` VARCHAR(100) NOT NULL COMMENT '该小程序下的 OpenID',
  `session_key` VARCHAR(255) NULL COMMENT '会话密钥（临时存储，用于解密数据）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次绑定时间',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_app_openid` (`app_id`, `openid`),
  INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户与小程序绑定关系（支持一个用户登录多个小程序）';

-- ------------------------------------------------------
-- 表：user_biometric_tokens（用户生物识别登录凭证表）
-- 说明：存储用户生物识别（指纹）登录凭证，支持 App 端指纹一键登录
--       凭证 31 天有效、可多次使用、每次需带新鲜 SOTER 签名、绑定 device_id
-- ------------------------------------------------------
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
