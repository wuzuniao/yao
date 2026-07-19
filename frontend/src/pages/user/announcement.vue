<template>
  <view class="announcement-page">
    <!-- 顶部返回按钮（次级页面统一返回组件） -->
    <BackButton />

    <view class="announcement-page__main">
      <!-- 页面标题区 -->
      <view class="announcement-page__header">
        <text class="announcement-page__title">公告管理</text>
        <text class="announcement-page__desc">发布与管理全站公告，仅管理员可操作。</text>
      </view>

      <!-- 发布公告入口卡（点击后切换为发布表单，隐藏已有公告列表） -->
      <view class="announcement-page__new-entry" v-if="!showForm && !editingId" @click="handleNewEntry">
        <image class="announcement-page__new-entry-icon" :src="jiaJihuaIcon" mode="aspectFit" />
        <text class="announcement-page__new-entry-text">发布公告</text>
      </view>

      <!-- 发布表单（默认隐藏，点击"发布公告"后显示，已有列表全部隐藏） -->
      <view class="announcement-page__form-wrap" v-if="showForm">
        <view class="announcement-page__form announcement-page__form--fade-in">
          <text class="announcement-page__form-heading">发布新公告</text>

          <!-- 公告标题 -->
          <view class="announcement-page__field">
            <text class="announcement-page__label">公告标题</text>
            <input
              class="announcement-page__input"
              v-model="form.title"
              placeholder="请输入公告标题"
              placeholder-class="announcement-page__placeholder"
              :placeholder-style="phStyle('title')"
              :maxlength="titleLimit.max"
              @input="e => form.title = titleLimit.handleInput(e)"
              @focus="onFocus('title')"
              @blur="onBlur"
            />
            <text v-if="titleLimit.limitReached" class="announcement-page__limit-text">{{ titleLimit.limitHint }}</text>
          </view>

          <!-- 公告内容 -->
          <view class="announcement-page__field">
            <text class="announcement-page__label">公告内容</text>
            <textarea
              class="announcement-page__textarea"
              v-model="form.content"
              placeholder="请输入公告内容"
              placeholder-class="announcement-page__placeholder"
              :placeholder-style="phStyle('content')"
              :maxlength="contentLimit.max"
              @input="e => form.content = contentLimit.handleInput(e)"
              @focus="onFocus('content')"
              @blur="onBlur"
            />
            <text v-if="contentLimit.limitReached" class="announcement-page__limit-text">{{ contentLimit.limitHint }}</text>
          </view>

          <!-- 取消 / 提交 -->
          <view class="announcement-page__actions">
            <view class="announcement-page__cancel" @click="cancelForm">
              <text class="announcement-page__cancel-text">取消</text>
            </view>
            <view class="announcement-page__save" @click="handlePublish">
              <text class="announcement-page__save-text">提交</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 已有公告列表（从数据库动态加载，点击卡片就地展开编辑表单） -->
      <view class="announcement-page__list" v-if="!showForm && announcements.length > 0">
        <view
          v-for="item in announcements"
          :key="item.id"
          class="announcement-page__card-wrapper"
        >
          <!-- 公告卡片（点击展开/收起编辑表单） -->
          <view
            class="announcement-page__card"
            :class="{ 'announcement-page__card--editing': editingId === item.id }"
            @click="toggleEdit(item)"
          >
            <view class="announcement-page__card-body">
              <view class="announcement-page__card-head">
                <view class="announcement-page__card-title-group">
                  <text class="announcement-page__card-title">{{ item.title }}</text>
                  <text class="announcement-page__card-subtitle">{{ item.content }}</text>
                </view>
                <view class="announcement-page__card-delete" @click.stop="handleDelete(item.id)">
                  <image class="announcement-page__card-delete-icon" :src="shanchuIcon" mode="aspectFit" />
                </view>
              </view>
            </view>
          </view>

          <!-- 编辑表单（就地展开，无标题，从卡片延伸出来） -->
          <view v-if="editingId === item.id" class="announcement-page__card-edit announcement-page__form--fade-in">
            <view class="announcement-page__field">
              <text class="announcement-page__label">公告标题</text>
              <input
                class="announcement-page__input"
                v-model="editingForm.title"
                placeholder="请输入公告标题"
                placeholder-class="announcement-page__placeholder"
                :maxlength="editTitleLimit.max"
                @input="e => editingForm.title = editTitleLimit.handleInput(e)"
              />
              <text v-if="editTitleLimit.limitReached" class="announcement-page__limit-text">{{ editTitleLimit.limitHint }}</text>
            </view>

            <view class="announcement-page__field">
              <text class="announcement-page__label">公告内容</text>
              <textarea
                class="announcement-page__textarea"
                v-model="editingForm.content"
                placeholder="请输入公告内容"
                placeholder-class="announcement-page__placeholder"
                :maxlength="editContentLimit.max"
                @input="e => editingForm.content = editContentLimit.handleInput(e)"
              />
              <text v-if="editContentLimit.limitReached" class="announcement-page__limit-text">{{ editContentLimit.limitHint }}</text>
            </view>

            <!-- 取消 / 更新 -->
            <view class="announcement-page__actions">
              <view class="announcement-page__cancel" @click="cancelEdit">
                <text class="announcement-page__cancel-text">取消</text>
              </view>
              <view class="announcement-page__save" @click="handleUpdate(item.id)">
                <text class="announcement-page__save-text">更新</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 公告管理页（announcement.vue，分包 pages/user 下）
 * --------------------------------------------------------------------------
 * 功能：全站公告的发布 / 更新 / 删除（仅管理员可进入，前端角色 + 后端守卫双重校验）
 *  - 发布公告：点击"发布公告"入口卡后显示表单（标题 + 内容 + 取消/提交）
 *  - 公告列表：从数据库加载全部公告，按创建时间倒序（后端已排序）
 *  - 就地展开编辑：点击公告卡片在卡片下方展开编辑表单（标题 + 内容 + 取消/更新）
 *  - 删除：点击卡片右上角垃圾桶图标（@click.stop 防误触展开）二次确认后删除
 *  - onLoad 角色守卫：非管理员（role !== 7）提示无权限并退回设置页
 */
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import BackButton from '../../components/BackButton.vue'
import { usePlaceholder } from '../../composables/usePlaceholder'
import { useInputLimit } from '../../composables/useInputLimit'
import { useUserStore } from '../../store/modules/user'
import {
  getAnnouncements,
  publishAnnouncement,
  updateAnnouncement,
  deleteAnnouncement
} from '../../api/modules/announcement'
import jiaJihuaIcon from '../../assets/images/jia_jihua.png'
import shanchuIcon from '../../assets/images/shanchu.png'
import { useShare } from '../../composables/useShare'

useShare({ title: '公告管理' })

const userStore = useUserStore()

// 公告列表（从数据库加载，后端已按 created_at 倒序）
const announcements = ref([])
// 卡片切换：默认显示"发布公告"入口卡，点击后切换为发布表单
const showForm = ref(false)
// 当前展开编辑的公告ID（null 表示无展开）
const editingId = ref(null)
// 表单提交中标志位（防止重复提交）
const isSubmitting = ref(false)

// 发布表单
const form = reactive({ title: '', content: '' })
// 编辑表单（点击公告卡片时填充）
const editingForm = reactive({ title: '', content: '' })

// 输入框 placeholder 聚焦交互
const { onFocus, onBlur, phStyle } = usePlaceholder()
// 输入框字符限制（与后端字段限制匹配：标题200，内容5000）
const titleLimit = useInputLimit(200)
const contentLimit = useInputLimit(5000)
const editTitleLimit = useInputLimit(200)
const editContentLimit = useInputLimit(5000)

onLoad(() => {
  // 角色守卫：非管理员禁止进入（服务端接口另有 get_current_admin 兜底）
  if (!userStore.userInfo || userStore.userInfo.role !== 7) {
    uni.showToast({ title: '无权限访问', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 800)
    return
  }
  loadAnnouncements()
})

// 加载公告列表
async function loadAnnouncements() {
  try {
    const res = await getAnnouncements()
    if (res.code === 0 && res.data) {
      announcements.value = res.data
    }
  } catch (e) {
    console.warn('加载公告列表失败', e)
  }
}

// 删除公告（点击垃圾桶图标后二次确认）
function handleDelete(announcementId) {
  uni.showModal({
    title: '提示',
    content: '确定要删除该公告吗？',
    confirmText: '删除',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const r = await deleteAnnouncement(announcementId)
        if (r.code === 0) {
          uni.showToast({ title: '删除成功', icon: 'success' })
          if (editingId.value === announcementId) {
            editingId.value = null
          }
          await loadAnnouncements()
        }
      } catch (e) {
        uni.showToast({ title: e.message || '删除失败', icon: 'none' })
      }
    }
  })
}

// 点击公告卡片：就地展开/收起编辑表单
function toggleEdit(item) {
  if (editingId.value === item.id) {
    editingId.value = null
    return
  }
  editingId.value = item.id
  showForm.value = false
  editingForm.title = item.title || ''
  editingForm.content = item.content || ''
}

// 发布入口：点击"发布公告"，隐藏列表，显示发布表单
function handleNewEntry() {
  showForm.value = true
  editingId.value = null
  form.title = ''
  form.content = ''
}

// 取消发布表单
function cancelForm() {
  showForm.value = false
}

// 取消编辑
function cancelEdit() {
  editingId.value = null
}

// 发布新公告
async function handlePublish() {
  if (isSubmitting.value) return
  if (!userStore.userInfo) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  if (!form.title.trim()) {
    uni.showToast({ title: '请输入公告标题', icon: 'none' })
    return
  }
  if (!form.content.trim()) {
    uni.showToast({ title: '请输入公告内容', icon: 'none' })
    return
  }
  isSubmitting.value = true
  try {
    const res = await publishAnnouncement({ title: form.title, content: form.content })
    if (res.code === 0) {
      uni.showToast({ title: '公告发布成功', icon: 'success' })
      showForm.value = false
      await loadAnnouncements()
    }
  } catch (e) {
    uni.showToast({ title: e.message || '发布失败', icon: 'none' })
  } finally {
    isSubmitting.value = false
  }
}

// 更新公告
async function handleUpdate(announcementId) {
  if (isSubmitting.value) return
  if (!userStore.userInfo) return
  if (!editingForm.title.trim()) {
    uni.showToast({ title: '请输入公告标题', icon: 'none' })
    return
  }
  if (!editingForm.content.trim()) {
    uni.showToast({ title: '请输入公告内容', icon: 'none' })
    return
  }
  isSubmitting.value = true
  try {
    const res = await updateAnnouncement(announcementId, {
      title: editingForm.title,
      content: editingForm.content
    })
    if (res.code === 0) {
      uni.showToast({ title: '公告更新成功', icon: 'success' })
      await loadAnnouncements()
      editingId.value = null
    }
  } catch (e) {
    uni.showToast({ title: e.message || '更新失败', icon: 'none' })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style lang="scss">
/* ==========================================================================
 * 响应式单位说明（px → rpx 转换，基准 750rpx = 屏宽）
 * 保留 px：1px 边框、box-shadow、9999px、百分比、z-index
 * 平板/折叠屏断点：≥768px 锁定关键尺寸为 px，避免 rpx 过度放大
 * ========================================================================== */
.announcement-page {
  min-height: 100vh;
  background-color: var(--page-bg-color);
  position: relative;
  box-sizing: border-box;
}

.announcement-page__main {
  padding: 210rpx 48rpx 64rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 64rpx;
}

/* ===== 页面标题区 ===== */
.announcement-page__header {
  padding: 0 16rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.announcement-page__title {
  color: #0e0f0c;
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 600;
}

.announcement-page__desc {
  color: #454745;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  padding-top: 8rpx;
  white-space: pre-line;
}

/* ===== 发布公告入口卡 ===== */
.announcement-page__new-entry {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 16rpx;
  height: 192rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #c1cab5;
}

.announcement-page__new-entry-icon {
  width: 28rpx;
  height: 28rpx;
  display: block;
}

.announcement-page__new-entry-text {
  color: #2f6c00;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 发布/编辑表单 ===== */
.announcement-page__form-wrap {
  padding-top: 0;
}

.announcement-page__form {
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

/* 卡片切换淡入过渡 */
.announcement-page__form--fade-in {
  animation: announcement-page-fade-in 0.3s ease-out;
}

@keyframes announcement-page-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.announcement-page__form-heading {
  color: #0e0f0c;
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
  padding-bottom: 16rpx;
}

.announcement-page__field {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.announcement-page__label {
  color: #454745;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 400;
}

.announcement-page__placeholder {
  color: #868685;
  font-size: 32rpx;
}

.announcement-page__input {
  height: 82rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 82rpx;
}

/* 字符限制提示文字 */
.announcement-page__limit-text {
  color: #d97706;
  font-size: 24rpx;
  line-height: 32rpx;
  margin-top: 8rpx;
}

.announcement-page__textarea {
  width: 100%;
  /* 高度 264rpx = 5行 × 48rpx line-height + 上下 padding 各 16rpx，内容默认显示5行 */
  height: 264rpx;
  padding: 16rpx 24rpx;
  box-sizing: border-box;
  background: #f9f9f9;
  border-radius: 12rpx;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
}

/* ===== 取消 / 提交 / 更新 按钮 ===== */
.announcement-page__actions {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
  margin-top: 32rpx;
}

.announcement-page__cancel {
  flex: 1;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
}

.announcement-page__cancel-text {
  color: #454745;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

.announcement-page__save {
  flex: 1;
  height: 96rpx;
  padding: 24rpx 0;
  box-sizing: border-box;
  border-radius: 9999px;
  background: #2f6c00;
  box-shadow: 0 4px 6px -4px rgba(0, 0, 0, 0.1), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
}

.announcement-page__save-text {
  color: #ffffff;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
}

/* ===== 公告列表 ===== */
.announcement-page__list {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.announcement-page__card-wrapper {
  display: flex;
  flex-direction: column;
}

.announcement-page__card {
  position: relative;
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* 编辑态卡片：底部圆角去除，与下方编辑表单衔接 */
.announcement-page__card--editing {
  border-radius: 24rpx 24rpx 0 0;
}

.announcement-page__card-body {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  position: relative;
}

.announcement-page__card-head {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: flex-start;
}

.announcement-page__card-title-group {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex: 1;
  min-width: 0;
}

.announcement-page__card-title {
  color: #0e0f0c;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.announcement-page__card-subtitle {
  color: #454745;
  font-size: 32rpx;
  line-height: 48rpx;
  font-weight: 400;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.announcement-page__card-delete {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.announcement-page__card-delete-icon {
  width: 32rpx;
  height: 36rpx;
  display: block;
}

/* ===== 就地展开编辑表单（从卡片延伸，无标题） ===== */
.announcement-page__card-edit {
  padding: 32rpx;
  box-sizing: border-box;
  border-radius: 0 0 24rpx 24rpx;
  background: #ffffff;
  box-shadow: inset 0 0 0 1px #e8ebe6, 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

/* ===== 平板/折叠屏断点（≥768px）===== */
@media screen and (min-width: 768px) {
  .announcement-page__main {
    padding: 105px 24px 32px;
    gap: 32px;
  }
  .announcement-page__header {
    padding: 0 8px;
    gap: 8px;
  }
  .announcement-page__title {
    font-size: 32px;
    line-height: 36px;
  }
  .announcement-page__desc {
    font-size: 16px;
    line-height: 24px;
    padding-top: 4px;
  }
  .announcement-page__new-entry {
    gap: 8px;
    height: 96px;
    border-radius: 12px;
  }
  .announcement-page__new-entry-icon {
    width: 14px;
    height: 14px;
  }
  .announcement-page__new-entry-text {
    font-size: 16px;
    line-height: 24px;
  }
  .announcement-page__form {
    padding: 16px;
    border-radius: 12px;
    gap: 16px;
  }
  .announcement-page__form-heading {
    font-size: 18px;
    line-height: 24px;
    padding-bottom: 8px;
  }
  .announcement-page__field {
    gap: 4px;
  }
  .announcement-page__label {
    font-size: 14px;
    line-height: 20px;
  }
  .announcement-page__placeholder {
    font-size: 16px;
  }
  .announcement-page__input {
    height: 41px;
    padding: 0 12px;
    border-radius: 6px;
    font-size: 16px;
    line-height: 41px;
  }
  .announcement-page__limit-text {
    font-size: 12px;
    line-height: 16px;
    margin-top: 4px;
  }
  .announcement-page__textarea {
    height: 132px;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 16px;
    line-height: 24px;
  }
  .announcement-page__actions {
    gap: 8px;
    margin-top: 16px;
  }
  .announcement-page__cancel {
    height: 48px;
    padding: 12px 0;
    border-radius: 9999px;
  }
  .announcement-page__cancel-text {
    font-size: 16px;
    line-height: 24px;
  }
  .announcement-page__save {
    height: 48px;
    padding: 12px 0;
    border-radius: 9999px;
  }
  .announcement-page__save-text {
    font-size: 16px;
    line-height: 24px;
  }
  .announcement-page__list {
    gap: 16px;
  }
  .announcement-page__card {
    padding: 16px;
    border-radius: 12px;
  }
  .announcement-page__card--editing {
    border-radius: 12px 12px 0 0;
  }
  .announcement-page__card-body {
    gap: 8px;
  }
  .announcement-page__card-title-group {
    gap: 4px;
  }
  .announcement-page__card-title {
    font-size: 16px;
    line-height: 24px;
  }
  .announcement-page__card-subtitle {
    font-size: 16px;
    line-height: 24px;
  }
  .announcement-page__card-delete {
    width: 32px;
    height: 32px;
  }
  .announcement-page__card-delete-icon {
    width: 16px;
    height: 18px;
  }
  .announcement-page__card-edit {
    padding: 16px;
    border-radius: 0 0 12px 12px;
    gap: 16px;
  }
}
</style>
