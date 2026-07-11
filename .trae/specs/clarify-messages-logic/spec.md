# 站内信页前后端显示逻辑梳理与修改 Spec

## Why

站内信页（`frontend/src/pages/user/messages.vue`）当前的前后端显示逻辑与用户本次给出的交互规则存在多处差异：现状返回所有站内信但不对"已有打卡记录的未读消息"做自动标记已读，且缺少"全部已读"按钮；新规则要求返回该用户所有站内信（含已读与未读），只将未读且对应提醒时间匹配区间内无打卡记录的消息展示为未读，对"已有打卡记录的未读消息"自动标记已读，已读消息保留在列表中（仅移除高亮）；同时新增"全部已读"按钮、轮询调整为每分钟、后端接口精简返回字段。为避免实现偏差，先将现有前后端显示逻辑梳理成文档，再按本次给出的规则进行修改，差异处一律以本次需求为准。

> **重要**：本 spec 完全以用户本次给出的逻辑为准。若与现有代码存在冲突，一律以本 spec 为准。

## What Changes

- 本 spec 包含两部分：
  1. **梳理**：以文字描述现有 `messages.vue` 页面前后端显示逻辑（数据来源、查询条件、卡片字段、交互、轮询、分页、未读数量同步）。
  2. **修改**：按本次需求对前后端逻辑进行调整，差异点以新需求覆盖。
- 与现状的**关键冲突点**（已以新逻辑覆盖）：
  - **自动标记已读**：旧无此逻辑 → 新打开站内信页时，对未读但匹配区间内已有打卡记录的消息，后端自动将 status 置为 0（已读），该条以已读状态保留在列表中（移除高亮）
  - **全部已读按钮**：旧无 → 新增"全部已读"按钮 + 后端批量标记 API
  - **打卡范围联合查询**：旧不查询打卡记录 → 新联合查询 `checkin_records`，按 `clarify-checkin-logic` spec 的匹配区间判定（仅用于未读消息的自动标记已读判定，不影响已读消息的展示）
  - **轮询频率**：旧 30 秒 → 新每分钟（60 秒）
  - **后端接口返回字段**：旧返回 `id`/`plan_id`/`plan_name`/`plan_remark`/`channel_id`/`send_time`/`status`/`is_unread` → 新只返回前端显示字段与必要关联字段（`id`/`plan_name`/`plan_remark`/`send_time`/`is_unread`），移除 `plan_id`/`channel_id`/`status` 等无关字段
- 保留不变的逻辑（新需求未变，维持现状）：
  - **列表查询范围**：返回该用户所有站内信（含已读与未读），按 `send_time` 倒序分页（现状已如此，新需求维持）
  - **已读消息展示**：已读消息保留在列表中，仅移除高亮（现状已如此，新需求维持）
  - 卡片内容必须包含"计划名称"和"备注说明"两个字段（现状已含 `plan_name` + `plan_remark` + `send_time`）
  - 未读卡片左侧颜色高亮标识（现状已实现：绿色竖条 + 浅绿背景）
  - 点击未读卡片触发 API 更新 status 为 0，前端实时移除高亮（卡片保留在列表中）
  - 未读数量同步到全局 store，驱动 NoticeButton 图标切换（现状已实现）

## Impact

- 受影响代码（修改对象）：
  - 前端：[messages.vue](file:///d:/wuzuniao/yao/frontend/src/pages/user/messages.vue)（列表展示、全部已读按钮、轮询调整）
  - 前端：[message.js](file:///d:/wuzuniao/yao/frontend/src/api/modules/message.js)（新增"全部已读"API 函数）
  - 后端：[notification_logs.py](file:///d:/wuzuniao/yao/backend/app/api/v1/notification_logs.py)（新增"全部已读"接口）
  - 后端：[notification_log_service.py](file:///d:/wuzuniao/yao/backend/app/services/notification_log_service.py)（修改 `list_znx_by_user` 查询条件、新增自动标记已读、新增 `mark_all_as_read`）
  - 后端：[notification_log.py schema](file:///d:/wuzuniao/yao/backend/app/schemas/notification_log.py)（如需新增请求 Schema）
- 受影响能力：站内信列表查询、未读消息自动标记已读、单条标记已读、全部已读、未读数量同步、NoticeButton 图标切换。

---

## 第一部分：现有前后端显示逻辑梳理

### Requirement: 现有前端列表加载与展示逻辑

现有 `messages.vue` 在 `onShow` 时调用 `loadMessages(true)` 重新加载第一页，并启动 30 秒轮询 `pollUnreadCount`。

#### Scenario: 列表数据来源
- **GIVEN** 用户已登录（`userStore.userInfo` 非空）
- **WHEN** 页面 `onShow` 触发
- **THEN** 调用 `listMessages(page, PAGE_SIZE)` → GET `/api/v1/notification-logs/list`
- **AND** 返回数据中 `items` 包含该用户**所有**站内信（含已读和未读），按 `send_time` 倒序
- **AND** 每条 `item` 字段：`id`、`plan_id`、`plan_name`、`plan_remark`、`channel_id`、`send_time`、`status`、`is_unread`
- **AND** 列表替换 `messages.value`，`has_more` 控制分页，`unread_count` 同步到 `userStore.setUnreadCount`

#### Scenario: 卡片展示字段
- **GIVEN** 列表数据已加载
- **THEN** 每张卡片展示：
  - `plan_name`（计划名称；计划已删除时显示"(已删除计划)"）
  - `plan_remark`（备注说明，为空时不显示该行）
  - `formatSendTime(send_time)`（发送时间，ISO 字符串 → "YYYY-MM-DD HH:MM"）
- **AND** 未读卡片（`is_unread=true`）左侧显示 8rpx 绿色竖条 + 浅绿背景 `#f1f8e8`
- **AND** 已读卡片白色背景，无竖条

#### Scenario: 加载状态反馈
- **WHEN** 初次加载中且列表为空 → 显示"加载中..."
- **WHEN** 初次加载失败且列表为空 → 显示"加载失败，点击重试"（点击重新加载）
- **WHEN** 列表为空且非加载/失败态 → 显示"暂无站内信消息"
- **WHEN** 分页加载中 → 显示"加载更多..."
- **WHEN** 无更多数据 → 显示"没有更多消息了"

### Requirement: 现有后端列表查询逻辑

现有 `NotificationLogService.list_znx_by_user` 查询逻辑：

#### Scenario: 查询条件
- **GIVEN** 当前登录用户 `user_id`
- **THEN** JOIN `notification_channels` 过滤 `channel_type='站内信'`
- **AND** LEFT JOIN `checkin_plans` 获取 `plan_name` / `plan_remark`（计划已删除时为 NULL，前端显示占位）
- **WHERE** `notification_logs.user_id = user_id` AND `notification_channels.channel_type = '站内信'`
- **ORDER BY** `notification_logs.send_time DESC`
- **LIMIT/OFFSET** 分页（page, limit）
- **AND** 不查询 `checkin_records`，不按打卡记录过滤
- **AND** 不区分 `status`（返回所有状态：0 已读、2 未读、1 失败）

#### Scenario: 返回结构
- **THEN** 返回 `{ items, total, page, limit, has_more, unread_count }`
- **AND** `unread_count` 由 `count_unread` 单独查询（status=2 的数量）

### Requirement: 现有单条标记已读逻辑

#### Scenario: 前端点击未读卡片
- **WHEN** 用户点击 `is_unread=true` 的卡片
- **THEN** 调用 `markMessageRead({ log_id: item.id })` → PUT `/api/v1/notification-logs/read`
- **AND** 返回 `code === 0` 后：`item.is_unread = false`、`item.status = 0`、`userStore.decrementUnread()`
- **AND** 卡片保留在列表中，仅移除高亮（背景变白、竖条消失）

#### Scenario: 后端标记已读
- **THEN** `NotificationLogService.mark_as_read(log_id, user_id)`
- **AND** 校验记录存在且 `user_id` 匹配；仅 `status=2` 可标记，已读记录直接返回
- **AND** 更新 `status = 0`（LOG_STATUS_SUCCESS），commit 后返回 log

### Requirement: 现有未读数量同步与轮询

#### Scenario: 全局未读数量同步
- **THEN** 列表加载成功后 `userStore.setUnreadCount(res.data.unread_count)`
- **AND** 单条标记已读后 `userStore.decrementUnread()`
- **AND** NoticeButton 组件通过 `userStore.unreadCount` 驱动图标切换（>0 显示 `tongzhi_1.png`，=0 显示 `tongzhi_0.png`）

#### Scenario: 30 秒轮询
- **WHEN** 页面 `onShow` → 启动 `setInterval(pollUnreadCount, 30000)`
- **THEN** `pollUnreadCount` 调用 `getUnreadCount()` → GET `/api/v1/notification-logs/unread-count`
- **AND** 若新数量 > `userStore.unreadCount`（有新消息）→ 重新加载列表 `loadMessages(true)`
- **AND** 否则仅同步 `setUnreadCount(newCount)`
- **AND** `onHide` 清除定时器

### Requirement: 现有分页加载

#### Scenario: 触底加载下一页
- **WHEN** `onReachBottom` 触发且 `hasMore && !loadingMore && !loading`
- **THEN** `page += 1`，调用 `loadMessages(false)` 追加下一页数据
- **AND** 分页失败静默，不显示错误态

### Requirement: 现有无"全部已读"功能

#### Scenario: 现状
- **THEN** 前端无"全部已读"按钮
- **AND** 后端无批量标记已读 API

---

## 第二部分：按本次需求修改

### ADDED Requirements

### Requirement: 列表查询条件（返回所有站内信 + 未读判定打卡记录）

打开站内信页时，后端 SHALL 按以下条件查询 `notification_logs` 表并返回列表：

1. `user_id` = 当前登录用户
2. JOIN `notification_channels` 且 `channel_type = '站内信'`
3. 返回该用户**所有**站内信记录（含已读 status=0 和未读 status=2），按 `send_time` 倒序分页
4. **对未读（status=2）记录联合查询 `checkin_records`**，判定是否需要自动标记已读：
   - 匹配区间定义同 `clarify-checkin-logic` spec：按相邻提醒时间的中点划分，覆盖全天 0:00-24:00 无间隙
     - 第一次提醒 `t_1` 的匹配区间：`[0:00, midpoint(t_1, t_2)]`
     - 中间提醒 `t_i`：`[midpoint(t_{i-1}, t_i), midpoint(t_i, t_{i+1})]`
     - 最后一次提醒 `t_n`：`[midpoint(t_{n-1}, t_n), 24:00]`
     - 单提醒时间：`[0:00, 24:00]`（全天）
   - "对应提醒时间" = `notification_logs.plan_time_id` 关联的提醒时间点
   - "打卡记录" = 该 `plan_id` 在 `notification_logs.notify_date` 当天、`actual_time` 落在该 `plan_time_id` 对应匹配区间内的 `checkin_records` 记录
   - 若未读记录的匹配区间内**已有打卡记录** → 后端自动将 `status` 更新为 0（已读），该条以已读状态返回（`is_unread=false`）
   - 若未读记录的匹配区间内**无打卡记录** → 保持 `status=2`，以未读状态返回（`is_unread=true`）
5. 已读（status=0）记录直接返回（`is_unread=false`），不参与打卡记录判定

#### Scenario: 未读且无打卡记录 → 以未读状态返回
- **WHEN** `notification_logs.status = 2` 且对应 `plan_time_id` 的匹配区间内无 `checkin_records`
- **THEN** 返回该条消息，`is_unread=true`，前端以未读卡片展示（带高亮）

#### Scenario: 未读但匹配区间内已有打卡记录 → 自动标记已读后以已读状态返回
- **WHEN** `notification_logs.status = 2` 但对应 `plan_time_id` 的匹配区间内已有 `checkin_records`
- **THEN** 后端在本次查询过程中将该条 `notification_logs.status` 更新为 0（已读）
- **AND** 该条仍返回展示，但 `is_unread=false`（已读状态，无高亮）
- **AND** 同步影响 `unread_count`（该条不再计入未读数量）

#### Scenario: 已读记录 → 直接返回
- **WHEN** `notification_logs.status = 0`（已读）
- **THEN** 直接返回，`is_unread=false`，不参与打卡记录判定

#### Scenario: plan_time_id 为 NULL 的处理
- **WHEN** `notification_logs.plan_time_id` 为 NULL（无法定位匹配区间）
- **THEN** 视为无对应打卡记录，保持 `status=2`，以未读状态返回展示（保守展示，避免误标记）

#### Scenario: 计划已删除的处理
- **WHEN** `notification_logs.plan_id` 关联的 `checkin_plans` 已删除
- **THEN** `plan_name` 显示"(已删除计划)"，`plan_remark` 为空
- **AND** 由于无法获取提醒时间列表，视为无对应打卡记录，保持 `status=2`，以未读状态返回展示

### Requirement: 自动标记已读的实现时机

系统 SHALL 在"打开站内信页加载列表"时执行自动标记已读逻辑，确保用户每次打开页面看到的未读消息都是真实需要提醒的。

#### Scenario: 打开页面时自动清理
- **WHEN** 前端调用列表接口（GET `/api/v1/notification-logs/list`）
- **THEN** 后端在返回列表前，先扫描该用户所有 `status=2` 的站内信记录
- **AND** 对每条记录判断对应匹配区间内是否有打卡记录
- **AND** 有打卡记录的记录批量更新 `status = 0`
- **AND** 再返回所有站内信（已读 + 剩余未读），已自动标记的记录以 `is_unread=false` 返回
- **AND** 返回的 `unread_count` 反映自动标记后的真实未读数量

### Requirement: 后端接口返回字段精简

后端列表接口 SHALL 只返回前端显示字段与必要关联字段，无关字段不返回。

#### Scenario: 返回字段范围
- **THEN** 每条 `item` 只包含以下字段：
  - `id`（消息记录ID，用于标记已读）
  - `plan_name`（计划名称，前端展示）
  - `plan_remark`（备注说明，前端展示，为空时前端隐藏该行）
  - `send_time`（发送时间，前端格式化展示）
  - `is_unread`（是否未读，前端判定高亮）
- **AND** **不**返回以下字段：`plan_id`、`channel_id`、`status`（前端只需 `is_unread` 布尔值即可判定高亮）

### Requirement: 卡片展示字段（保留现状）

每张卡片 SHALL 展示以下字段：
- 计划名称（`plan_name`）
- 备注说明（`plan_remark`，为空时隐藏该行）
- 发送时间（`send_time`，格式化为 "YYYY-MM-DD HH:MM"）

#### Scenario: 未读卡片高亮
- **THEN** 未读卡片（`is_unread=true`）左侧显示颜色高亮标识（绿色竖条 + 浅绿背景）
- **AND** 已读卡片（`is_unread=false`）白色背景，无竖条

### Requirement: 单条标记已读（保留卡片 + 移除高亮）

用户点击未读卡片后，系统 SHALL 触发 API 更新该记录 `status` 为 0，数据库成功后前端实时移除对应卡片的高亮状态，卡片保留在列表中。

#### Scenario: 点击未读卡片
- **WHEN** 用户点击未读卡片
- **THEN** 调用 PUT `/api/v1/notification-logs/read`（`log_id` 为该卡片 ID）
- **AND** 返回 `code === 0` 后：`item.is_unread = false`，卡片保留在列表中（背景变白、竖条消失）
- **AND** 同步 `userStore.decrementUnread()`

> 说明：与现状一致，卡片保留在列表中仅移除高亮，不从列表移除。

### Requirement: 新增"全部已读"按钮

系统 SHALL 在站内信页提供"全部已读"按钮，点击后批量将当前用户所有未读站内信标记为已读。

#### Scenario: 按钮位置与显示
- **THEN** "全部已读"按钮位于页面标题区附近（PageHeader 下方或同级，与列表卡片区分开）
- **AND** 按钮在列表中无未读消息（所有卡片 `is_unread=false`）时隐藏或置灰，避免无效点击
- **AND** 按钮在加载中、分页加载中时置灰，避免并发操作

#### Scenario: 点击"全部已读"
- **WHEN** 用户点击"全部已读"按钮
- **THEN** 调用后端批量标记 API（PUT `/api/v1/notification-logs/read-all`，user_id 由 JWT 提供）
- **AND** 返回 `code === 0` 后：前端将列表中所有卡片的 `is_unread` 置为 `false`（移除全部高亮，卡片保留在列表中）
- **AND** 同步 `userStore.setUnreadCount(0)`
- **AND** 显示成功提示（如 `uni.showToast({ title: '已全部标记为已读', icon: 'none' })`）

#### Scenario: 全部已读失败
- **WHEN** 后端返回非 0 或网络异常
- **THEN** 显示错误提示（如 `uni.showToast({ title: e.message || '操作失败，请重试', icon: 'none' })`）
- **AND** 列表与未读数量保持原状，不高亮状态不变

### Requirement: 后端"全部已读"API

系统 SHALL 提供批量标记当前用户所有未读站内信为已读的 API。

#### Scenario: API 定义
- **THEN** 路由：PUT `/api/v1/notification-logs/read-all`
- **AND** 认证：JWT 提供 `user_id`
- **AND** 请求体：无（user_id 由 JWT 提供）
- **AND** 响应：`{ code: 0, msg: "已全部标记为已读", data: { updated_count: <int> } }`

#### Scenario: 后端批量更新逻辑
- **THEN** `NotificationLogService.mark_all_as_read(user_id)`
- **AND** 查询该用户所有 `status=2` 的站内信记录（JOIN `notification_channels` 过滤 `channel_type='站内信'`）
- **AND** 批量更新 `status = 0`
- **AND** commit 后返回更新条数 `updated_count`
- **AND** 若无未读记录，返回 `updated_count = 0`，不报错

> 说明：全部已读按钮**不**再判断打卡记录，直接将所有 `status=2` 的站内信标记为已读（用户主动操作，视为已知晓）。

### Requirement: 未读数量同步调整

由于列表查询时会自动标记部分消息为已读，系统 SHALL 确保未读数量同步逻辑正确。

#### Scenario: 列表加载后同步未读数量
- **WHEN** 列表接口返回
- **THEN** `unread_count` 反映自动标记已读后的真实未读数量（= 返回 items 中 `is_unread=true` 的数量）
- **AND** 前端 `userStore.setUnreadCount(res.data.unread_count)`

#### Scenario: 全部已读后同步
- **WHEN** 全部已读 API 返回成功
- **THEN** 前端 `userStore.setUnreadCount(0)`
- **AND** NoticeButton 图标切换为 `tongzhi_0.png`

### Requirement: 轮询逻辑调整为每分钟

系统 SHALL 将轮询间隔从 30 秒调整为 60 秒（每分钟），用于检测新消息。

#### Scenario: 轮询间隔
- **WHEN** 页面 `onShow` → 启动 `setInterval(pollUnreadCount, 60000)`（60 秒）
- **AND** `onHide` 清除定时器

#### Scenario: 轮询检测新消息
- **WHEN** 轮询发现 `unread_count` 增加
- **THEN** 重新加载列表 `loadMessages(true)`（会再次触发自动标记已读逻辑）
- **AND** 列表返回所有站内信（已读 + 未读），新消息以未读状态展示

#### Scenario: 轮询发现未读数量减少
- **WHEN** 轮询发现 `unread_count` 减少（可能因其他端已读或自动标记已读）
- **THEN** 同步 `setUnreadCount(newCount)`
- **AND** 重新加载列表 `loadMessages(true)` 以保持列表与未读数量的一致性（确保已自动标记的消息在列表中更新为已读状态）

---

## MODIFIED Requirements

### Requirement: 列表查询返回字段

[原：返回 `id`/`plan_id`/`plan_name`/`plan_remark`/`channel_id`/`send_time`/`status`/`is_unread`]
[新：只返回 `id`/`plan_name`/`plan_remark`/`send_time`/`is_unread`，移除 `plan_id`/`channel_id`/`status` 等无关字段]

详见 ADDED Requirements 中的"后端接口返回字段精简"。

### Requirement: 轮询间隔

[原：30 秒轮询]
[新：每分钟（60 秒）轮询]

详见 ADDED Requirements 中的"轮询逻辑调整为每分钟"。

---

## REMOVED Requirements

### Requirement: 不查询打卡记录的列表查询
**Reason**: 新需求要求对未读消息联合查询 `checkin_records`，按匹配区间判定是否自动标记已读。
**Migration**: 后端 `list_znx_by_user` 需新增打卡记录联合查询与自动标记已读逻辑；复用 `checkin_service.py` 中的 `_get_match_intervals` 匹配区间计算逻辑。仅对未读（status=2）记录判定，已读记录不参与。

---

## 附录：差异对照表

| 项目 | 现状 | 新需求（以本次为准） |
|------|------|------|
| 列表查询范围 | 所有站内信（含已读和未读） | 保留：所有站内信（含已读和未读） |
| 已读消息展示 | 保留在列表，移除高亮 | 保留：保留在列表，移除高亮 |
| 自动标记已读 | 无 | 新增：未读但匹配区间内有打卡记录的消息自动标记已读，以已读状态保留在列表中 |
| 打卡记录联合查询 | 无 | 新增：联合查询 checkin_records，仅对未读消息判定匹配区间内是否有打卡记录 |
| 全部已读按钮 | 无 | 新增：按钮 + 后端批量 API，点击后移除所有高亮（卡片保留） |
| 后端返回字段 | id/plan_id/plan_name/plan_remark/channel_id/send_time/status/is_unread | 精简：id/plan_name/plan_remark/send_time/is_unread |
| 卡片字段 | plan_name + plan_remark + send_time | 保留 |
| 未读高亮 | 绿色竖条 + 浅绿背景 | 保留 |
| 单条点击标记已读 | API + 前端移除高亮（卡片保留） | 保留：API + 前端移除高亮（卡片保留） |
| 未读数量同步 | 列表加载/单条标记/轮询同步 | 保留 + 全部已读后置 0 |
| 轮询频率 | 30 秒 | 改为每分钟（60 秒） |
| 分页 | 触底加载下一页 | 保留 |
