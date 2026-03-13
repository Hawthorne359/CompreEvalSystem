<template>
  <div class="space-y-5">
    <!-- 顶部：统计卡片 + 进度环 -->
    <div class="grid gap-4 md:grid-cols-3">
      <div class="md:col-span-2 grid grid-cols-2 gap-3">
        <div class="stat-card">
          <div class="stat-icon bg-amber-100 text-amber-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
          </div>
          <div>
            <div class="stat-value text-amber-600">{{ data.pending_tasks ?? '—' }}</div>
            <div class="stat-label">待评任务</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-green-100 text-green-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
          </div>
          <div>
            <div class="stat-value text-green-600">{{ data.completed_tasks ?? '—' }}</div>
            <div class="stat-label">已完成评分</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-blue-100 text-blue-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
          </div>
          <div>
            <div class="stat-value text-blue-600">{{ data.total_tasks ?? '—' }}</div>
            <div class="stat-label">任务总数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-slate-100 text-slate-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>
          </div>
          <div>
            <div class="stat-value text-slate-600">{{ data.responsible_class_count ?? '—' }}</div>
            <div class="stat-label">负责班级数</div>
          </div>
        </div>
      </div>

      <!-- 评分进度环形图 -->
      <div class="dash-section flex flex-col items-center justify-center py-5 px-4">
        <RingChart
          :percentage="data.completion_rate ?? 0"
          color="#3b82f6"
          track-color="#dbeafe"
          :size="120"
          :stroke-width="14"
        />
        <p class="mt-3 text-sm font-medium text-slate-700">评分完成率</p>
        <p class="mt-0.5 text-xs text-slate-400">
          {{ data.completed_tasks ?? 0 }} / {{ data.total_tasks ?? 0 }}
        </p>
      </div>
    </div>

    <!-- 最近分配的任务 -->
    <div class="dash-section">
      <div class="dash-section__header">最新待评任务</div>
      <div v-if="!data.recent_tasks?.length" class="px-4 py-8 text-center text-sm text-slate-400">
        暂无待评任务
      </div>
      <ul v-else class="divide-y divide-slate-100">
        <li
          v-for="task in data.recent_tasks"
          :key="task.id"
          class="flex items-center justify-between px-4 py-3"
        >
          <div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-slate-800">{{ task.project_name }}</span>
            </div>
            <div class="mt-0.5 text-xs text-slate-500">学生：{{ task.student_name }}</div>
            <div class="mt-0.5 text-xs text-slate-400">{{ formatTime(task.updated_at) }}</div>
          </div>
          <div class="flex items-center gap-2">
            <StatusBadge :text="taskStatusLabel(task)" :tone="taskStatusTone(task)" />
            <span
              v-if="task.already_scored"
              class="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700"
            >已评</span>
            <router-link
              :to="{ name: 'ReviewDetail', params: { id: task.id } }"
              class="rounded bg-brand-50 px-2 py-1 text-xs text-brand-700 hover:bg-brand-100"
            >
              {{ task.already_scored ? '查看' : '去评分' }}
            </router-link>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
/**
 * @description 学生助理工作台组件。
 * @props {Object} data - Dashboard API 返回的助理数据
 */
import RingChart from '@/components/charts/RingChart.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatTime } from '@/utils/format'
import { deriveWorkflowSubmissionStatus } from '@/utils/submissionStatus'

defineProps({
  data: { type: Object, required: true },
})

/**
 * @param {Object} task
 * @returns {string}
 */
function taskStatusLabel(task) {
  return deriveWorkflowSubmissionStatus(task).label
}

/**
 * @param {Object} task
 * @returns {string}
 */
function taskStatusTone(task) {
  return deriveWorkflowSubmissionStatus(task).tone
}

</script>
