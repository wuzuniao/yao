# Tasks

- [x] Task 1: 修改后端 `list_znx_by_user` 查询逻辑（返回所有站内信 + 未读判定打卡记录 + 自动标记已读 + 精简字段）
  - [ ] SubTask 1.1: 在 `NotificationLogService.list_znx_by_user` 中先扫描该用户所有 `status=2` 的站内信记录
  - [ ] SubTask 1.2: 对每条未读记录关联 `plan_time_id` → 查询对应计划的提醒时间列表，复用 `CheckinService._get_match_intervals` 计算匹配区间
  - [ ] SubTask 1.3: 按 `notify_date` 查询该计划当天 `checkin_records`，判断匹配区间内是否有打卡记录
  - [ ] SubTask 1.4: 有打卡记录的未读记录批量更新 `status=0`（自动标记已读），commit
  - [ ] SubTask 1.5: 返回该用户所有站内信（已读 + 剩余未读），JOIN notification_channels 过滤站内信，LEFT JOIN checkin_plans 获取计划名称/备注，按 send_time 倒序分页
  - [ ] SubTask 1.6: 处理 `plan_time_id` 为 NULL 或计划已删除的边界情况（视为无打卡记录，保持 status=2 未读状态返回）
  - [ ] SubTask 1.7: 精简返回字段，每条 item 只包含 `id`/`plan_name`/`plan_remark`/`send_time`/`is_unread`，移除 `plan_id`/`channel_id`/`status`
  - [ ] SubTask 1.8: 确保 `unread_count` 反映自动标记已读后的真实未读数量（= items 中 is_unread=true 的数量）

- [x] Task 2: 新增后端"全部已读"API
  - [ ] SubTask 2.1: 在 `notification_logs.py` 路由中新增 PUT `/api/v1/notification-logs/read-all` 接口
  - [ ] SubTask 2.2: 在 `NotificationLogService` 中新增 `mark_all_as_read(user_id)` 方法，批量更新该用户所有 `status=2` 的站内信为 `status=0`
  - [ ] SubTask 2.3: 接口返回 `{ code: 0, msg: "已全部标记为已读", data: { updated_count: <int> } }`
  - [ ] SubTask 2.4: 无未读记录时返回 `updated_count=0`，不报错

- [x] Task 3: 前端 `message.js` 新增"全部已读"API 函数
  - [ ] SubTask 3.1: 新增 `markAllMessagesRead()` 函数，调用 PUT `/api/v1/notification-logs/read-all`

- [x] Task 4: 前端 `messages.vue` 列表展示调整
  - [ ] SubTask 4.1: 列表展示所有站内信（已读 + 未读），未读卡片带高亮，已读卡片无高亮（后端已返回 is_unread 字段）
  - [ ] SubTask 4.2: 单条标记已读后，`item.is_unread = false`，卡片保留在列表中（仅移除高亮，不从列表移除）
  - [ ] SubTask 4.3: 移除前端对 `item.status` 的直接引用（后端不再返回 status 字段，统一用 `is_unread`）

- [x] Task 5: 前端 `messages.vue` 新增"全部已读"按钮
  - [ ] SubTask 5.1: 在 PageHeader 下方或同级添加"全部已读"按钮（文本按钮或带边框按钮，样式与页面风格一致）
  - [ ] SubTask 5.2: 按钮显示条件：列表中存在 `is_unread=true` 的卡片且非加载中/分页加载中（无未读消息或加载中时隐藏/置灰）
  - [ ] SubTask 5.3: 点击按钮调用 `markAllMessagesRead()`，成功后将列表中所有卡片的 `is_unread` 置为 `false`（移除全部高亮，卡片保留），`userStore.setUnreadCount(0)`，显示成功 toast
  - [ ] SubTask 5.4: 失败时显示错误 toast，列表与未读数量保持原状
  - [ ] SubTask 5.5: 添加按钮防抖（点击后立即置灰，避免重复点击）

- [x] Task 6: 前端轮询逻辑调整
  - [ ] SubTask 6.1: 将轮询间隔从 30000ms 改为 60000ms（每分钟）
  - [ ] SubTask 6.2: 轮询发现未读数量增加时，重新加载列表（`loadMessages(true)` 会再次触发后端自动标记已读）
  - [ ] SubTask 6.3: 轮询发现未读数量减少时，同步 `setUnreadCount(newCount)`，并重新加载列表 `loadMessages(true)` 以保持列表与未读数量一致性

- [x] Task 7: 同步更新项目文档
  - [ ] SubTask 7.1: 更新 `目录结构.json`（如无新增文件则仅注明修改）
  - [ ] SubTask 7.2: 在 `更新记录.md` 追加本次变更说明（日期、变更类型、内容、影响范围）

# Task Dependencies
- [Task 2] 与 [Task 1] 可并行（均为后端修改，但无依赖）
- [Task 3] 依赖 [Task 2]（前端 API 函数对应后端接口）
- [Task 4] 依赖 [Task 1]（前端展示调整依赖后端查询逻辑与字段变更）
- [Task 5] 依赖 [Task 3]（前端按钮调用 API 函数）
- [Task 6] 依赖 [Task 1]（轮询调整依赖列表查询逻辑）
- [Task 7] 依赖 [Task 1]-[Task 6] 全部完成
