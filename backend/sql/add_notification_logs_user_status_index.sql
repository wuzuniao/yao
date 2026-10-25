-- ======================================================
-- 增量脚本：notification_logs 未读热路径复合索引（2026-10-25 性能优化）
-- ======================================================
-- 背景：站内信未读热路径均按 user_id + status 过滤——
--   1) _auto_mark_read_if_checked 未读扫描（unread-count / 列表接口每次触发）
--   2) count_unread 未读计数（通知图标切换，NoticeButton 每页 onShow 节流轮询）
--   3) mark_all_as_read 批量 UPDATE（user_id + status=2 过滤）
-- notification_logs 每提醒×渠道写一条，随时间线性增长，仅靠 idx_user_id 会
-- 扫描该用户全部历史日志。idx_user_status(user_id, status) 使上述查询只触达
-- 该用户的未读子集；原 idx_user_id(user_id) 为新索引最左前缀（冗余），
-- 一并删除以抵消新增索引带来的写放大（索引数量净不变）。
--
-- 生产环境按时间顺序执行：create_yao_db.sql → 各 add_*.sql → 本脚本。
-- 新环境直接执行回填后的 create_yao_db.sql 即含本索引，无需重复执行。

USE `wuzuniao_yao`;

ALTER TABLE `notification_logs`
  ADD INDEX `idx_user_status` (`user_id`, `status`),
  DROP INDEX `idx_user_id`;
