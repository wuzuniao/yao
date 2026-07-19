-- 全站公告表迁移（增量）
-- 在业务库 wuzuniao_yao 新建 announcements 表
-- 每条公告一行，用户侧投递后续实现

USE `wuzuniao_yao`;

CREATE TABLE `announcements` (
  `id`         BIGINT       NOT NULL AUTO_INCREMENT,
  `title`      VARCHAR(200) NOT NULL COMMENT '公告标题',
  `content`    TEXT         NOT NULL COMMENT '公告内容',
  `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='全站公告表（每条公告一行，用户侧投递后续实现）';
