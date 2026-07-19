-- 用户角色字段迁移（增量）
-- 在共享用户库 wuzuniao_yonghu.users 表增加 role 字段
-- 角色：0-普通用户（默认），7-管理员
-- 说明：管理员身份在登录时由 JWT 判定，不按 role 查库，故不建索引

USE `wuzuniao_yonghu`;

ALTER TABLE `users`
  ADD COLUMN `role` TINYINT NOT NULL DEFAULT 0
    COMMENT '角色：0-普通用户（默认），7-管理员'
  AFTER `status`;
