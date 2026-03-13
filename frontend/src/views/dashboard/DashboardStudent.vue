<template>
  <div class="space-y-5">
    <!-- 顶部：统计卡片 + 进度环 -->
    <div class="grid gap-4 md:grid-cols-3">
      <div class="md:col-span-2 grid grid-cols-2 gap-3">
        <div class="stat-card">
          <div class="stat-icon bg-amber-100 text-amber-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
          </div>
          <div>
            <div class="stat-value text-amber-600">{{ data.pending_submission_count ?? '—' }}</div>
            <div class="stat-label">待提交测评</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-blue-100 text-blue-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
          </div>
          <div>
            <div class="stat-value text-blue-600">{{ underReviewCount }}</div>
            <div class="stat-label">审核中</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-green-100 text-green-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
          </div>
          <div>
            <div class="stat-value text-green-600">{{ approvedCount }}</div>
            <div class="stat-label">已通过</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-red-100 text-red-500">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
          </div>
          <div>
            <div class="stat-value text-red-500">{{ appealingCount }}</div>
            <div class="stat-label">申诉中</div>
          </div>
        </div>
      </div>

      <!-- 提交进度环形图 -->
      <div class="dash-section flex flex-col items-center justify-center py-5 px-4">
        <RingChart
          :percentage="submitPct"
          color="#3b82f6"
          track-color="#dbeafe"
          :size="120"
          :stroke-width="14"
        />
        <p class="mt-3 text-sm font-medium text-slate-700">提交进度</p>
        <p class="mt-0.5 text-xs text-slate-400">
          {{ data.submitted_count ?? 0 }} / {{ data.total_task_count ?? 0 }}
        </p>
      </div>
    </div>

    <!-- 截止日期提醒 -->
    <div
      v-if="data.upcoming_deadlines?.length"
      class="dash-section"
    >
      <div class="dash-section__header">
        <span>即将截止</span>
        <svg class="h-4 w-4 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
      </div>
      <div class="divide-y divide-slate-100">
        <div
          v-for="(dl, idx) in data.upcoming_deadlines"
          :key="idx"
          class="flex items-center justify-between px-4 py-3"
        >
          <div class="min-w-0">
            <div class="text-sm font-medium text-slate-800">{{ dl.project_name }}</div>
            <div class="mt-0.5 text-xs text-slate-400">{{ formatDeadline(dl.end_time) }}</div>
          </div>
          <span
            class="flex-shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold"
            :class="dl.days_left <= 3 ? 'bg-red-100 text-red-700' : dl.days_left <= 7 ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'"
          >
            {{ dl.days_left <= 0 ? '今天截止' : `剩${dl.days_left}天` }}
          </span>
        </div>
      </div>
    </div>

    <!-- 最近动态 -->
    <div class="dash-section">
      <div class="dash-section__header">最近提交动态</div>
      <div v-if="!data.recent_submissions?.length" class="px-4 py-8 text-center text-sm text-slate-400">
        暂无提交记录
      </div>
      <ul v-else class="divide-y divide-slate-100">
        <li
          v-for="sub in data.recent_submissions"
          :key="sub.id"
          class="flex items-center justify-between px-4 py-3"
        >
          <div>
            <div class="text-sm font-medium text-slate-800">{{ sub.project_name }}</div>
            <div class="mt-0.5 text-xs text-slate-400">{{ formatTime(sub.updated_at) }}</div>
          </div>
          <div class="flex items-center gap-3">
            <span v-if="sub.final_score !== null" class="text-sm font-bold text-brand-600">
              {{ sub.final_score }} 分
            </span>
            <StatusBadge :text="statusLabel(sub)" :tone="statusTone(sub)" />
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
/**
 * @description 学生工作台组件。
 * @props {Object} data - Dashboard API 返回的学生数据
 */
import { computed } from 'vue'
import StatusBadge from '@/components/StatusBadge.vue'
import RingChart from '@/components/charts/RingChart.vue'
import { formatTime } from '@/utils/format'
import { deriveSubmissionDisplayStatus } from '@/utils/submissionStatus'

const props = defineProps({
  data: { type: Object, required: true },
})

const counts = computed(() => props.data.status_counts ?? {})
const underReviewCount = computed(() => (counts.value.submitted ?? 0) + (counts.value.under_review ?? 0))
const approvedCount = computed(() => counts.value.approved ?? 0)
const appealingCount = computed(() => counts.value.appealing ?? 0)

/** @returns {number} 提交完成百分比 */
const submitPct = computed(() => {
  const total = props.data.total_task_count ?? 0
  const done = props.data.submitted_count ?? 0
  return total ? Math.round((done / total) * 100) : 0
})

/**
 * @param {Object} sub
 * @returns {string}
 */
function statusLabel(sub) { return deriveSubmissionDisplayStatus(sub).label }
/**
 * @param {Object} sub
 * @returns {string}
 */
function statusTone(sub) { return deriveSubmissionDisplayStatus(sub).tone }

/**
 * @param {string} ts
 * @returns {string}
 */
function formatDeadline(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' })
}
</script>
