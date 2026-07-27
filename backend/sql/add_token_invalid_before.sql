-- ======================================================
-- 增量变更：users 表新增 token_invalid_before 字段
-- 用途：早于此时间签发的 JWT 一律失效（改密码/重置密码/删除账号/退出登录时设置）
-- 执行顺序：在 create_user_db.sql 之后执行
-- ======================================================

USE `wuzuniao_yonghu`;

ALTER TABLE `users`
  ADD COLUMN `token_invalid_before` DATETIME NULL COMMENT '早于此时间签发的 token 一律失效（改密码/重置密码/删除账号/退出登录后设置）';
