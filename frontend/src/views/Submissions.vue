<template>
  <div class="page-shell" @click="clearHighlight">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <h2 class="app-page-title">进行中的测评任务</h2>
      <AppButton variant="secondary" @click="loadTasks">刷新任务</AppButton>
    </div>

    <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
      <div class="app-surface p-4">
        <div class="text-xs text-slate-500">当前可见任务</div>
        <div class="mt-1 text-lg font-semibold text-slate-800">{{ allTasks.length }}</div>
      </div>
      <div class="app-surface p-4">
        <div class="text-xs text-slate-500">待你处理</div>
        <div class="mt-1 text-lg font-semibold text-amber-700">{{ pendingCount }}</div>
      </div>
      <div class="app-surface p-4">
        <div class="text-xs text-slate-500">已进入评审/完成</div>
        <div class="mt-1 text-lg font-semibold text-emerald-700">{{ doneCount }}</div>
      </div>
    </div>

    <div class="app-surface p-3 md:p-4">
      <div class="app-filter-wrap">
        <label class="flex flex-col gap-1 text-sm text-slate-600">
          <span>周期</span>
        <select
          v-model="filterSeason"
            class="app-select"
        >
          <option value="">全部</option>
          <option v-for="s in seasonOptions" :key="`season-${s.id}`" :value="s.id">{{ s.name }}</option>
        </select>
      </label>
        <label class="flex flex-col gap-1 text-sm text-slate-600">
          <span>状态</span>
        <select
          v-model="filterState"
            class="app-select"
        >
          <option value="">全部</option>
          <option v-for="s in stateOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </label>
      <input
        v-model.trim="filterKeyword"
        type="text"
          class="app-input"
        placeholder="输入项目关键词"
        @keydown.enter="loadTasks"
      />
        <AppButton variant="ghost" @click="loadTasks">查询</AppButton>
      </div>
    </div>

    <div v-if="loading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="listError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ listError }}</div>
    <div v-else class="space-y-3">
      <div class="mobile-card-list">
        <div
          v-for="task in filteredTasks"
          :key="`mobile-${task.project_id}`"
          class="mobile-card-link"
          :class="task.project_id === lastHighlightId ? 'bg-blue-50' : ''"
          @click="goTask(task)"
        >
          <div class="mobile-card-body">
            <div class="flex items-center gap-2">
              <span class="mobile-card-title">{{ task.project_name || '—' }}</span>
              <StatusBadge :text="displayStatusLabel(task)" :tone="displayStatusTone(task)" />
            </div>
            <div class="mobile-card-sub">{{ task.season_name || '未分配周期' }}</div>
            <div class="mobile-card-meta">{{ formatDateTime(task.start_time) }} — {{ formatDateTime(task.end_time) }}</div>
          </div>
          <svg class="mobile-card-arrow" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
        </div>
        <div v-if="filteredTasks.length === 0" class="app-surface px-4 py-8 text-center text-sm text-slate-500">
          当前暂无需要处理的测评任务
        </div>
      </div>

      <div class="app-table-wrap hidden md:block">
        <table class="app-table">
        <thead>
          <tr class="border-b border-slate-200 bg-slate-50">
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">周期 / 项目</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">任务状态</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">时间窗口</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">我的记录</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="task in filteredTasks"
            :key="task.project_id"
            class="border-b border-slate-100"
            :class="task.project_id === lastHighlightId ? 'bg-blue-50' : 'hover:bg-slate-50'"
          >
            <td class="px-4 py-2.5 text-slate-800">
              <div class="text-xs text-slate-500">{{ task.season_name || '未分配周期' }}</div>
              <div class="font-medium">{{ task.project_name || '—' }}</div>
            </td>
            <td class="px-4 py-2.5">
              <StatusBadge :text="displayStatusLabel(task)" :tone="displayStatusTone(task)" />
            </td>
            <td class="px-4 py-2.5 text-xs text-slate-600">
              <div>开：{{ formatDateTime(task.start_time) }}</div>
              <div>关：{{ formatDateTime(task.end_time) }}</div>
              <div v-if="task.late_submit_deadline">迟交至：{{ formatDateTime(task.late_submit_deadline) }}</div>
            </td>
            <td class="px-4 py-2.5 text-slate-600">
              <div v-if="task.submission_id" class="space-y-0.5 text-xs">
                <div>ID：{{ task.submission_id }}</div>
                <div>提交：{{ formatDateTime(task.submitted_at) }}</div>
              </div>
              <span v-else class="text-xs text-slate-400">尚未开始</span>
            </td>
            <td class="px-4 py-2.5">
              <AppButton
                size="sm"
                variant="secondary"
                :disabled="actionLoadingProjectId === task.project_id"
                @click="goTask(task)"
              >
                {{ actionLoadingProjectId === task.project_id ? '处理中…' : task.action_label }}
              </AppButton>
            </td>
          </tr>
          <tr v-if="filteredTasks.length === 0">
            <td colspan="5" class="px-4 py-8 text-center text-slate-500">当前暂无需要处理的测评任务</td>
          </tr>
        </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 学生任务中心：展示进行中的测评任务，并提供“开始填写/继续填写/查看记录”动作。
 * 接口：GET /api/v1/submission-tasks/
 */
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useHighlightStore } from '@/stores/highlight'
import { getSubmissionTasks, createSubmission } from '@/api/submissions'
import AppButton from '@/components/AppButton.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatDateTime } from '@/utils/format'
import { deriveSubmissionDisplayStatus } from '@/utils/submissionStatus'

const router = useRouter()
const highlightStore = useHighlightStore()
const lastHighlightId = ref(null)

const stateOptions = [
  { value: 'pending', label: '待提交' },
  { value: 'late_open', label: '补交窗口开放' },
  { value: 'draft', label: '草稿' },
  { value: 'submitted', label: '已提交' },
  { value: 'under_review', label: '审核中' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
  { value: 'appealing', label: '申诉中' },
]

const loading = ref(false)
const listError = ref('')
const allTasks = ref([])
const filterSeason = ref('')
const filterState = ref('')
const filterKeyword = ref('')
const actionLoadingProjectId = ref(null)

const seasonOptions = computed(() => {
  const map = new Map()
  for (const task of allTasks.value) {
    if (!task.season_id) continue
    map.set(task.season_id, { id: task.season_id, name: task.season_name })
  }
  return [...map.values()]
})

const filteredTasks = computed(() => {
  return allTasks.value.filter((task) => {
    if (filterSeason.value && String(task.season_id) !== String(filterSeason.value)) return false
    if (filterState.value && task.entry_state !== filterState.value) return false
    if (filterKeyword.value && !String(task.project_name || '').includes(filterKeyword.value)) return false
    return true
  })
})

const pendingCount = computed(() => allTasks.value.filter((task) => ['pending', 'late_open', 'draft'].includes(task.entry_state)).length)
const doneCount = computed(() => allTasks.value.filter((task) => ['submitted', 'under_review', 'approved', 'rejected', 'appealing'].includes(task.entry_state)).length)

/** 任务状态样式。 */
function stateClass(status) {
  const map = {
    pending: 'bg-amber-100 text-amber-800',
    late_open: 'bg-orange-100 text-orange-700',
    draft: 'bg-slate-100 text-slate-700',
    submitted: 'bg-blue-100 text-blue-700',
    under_review: 'bg-amber-100 text-amber-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    appealing: 'bg-purple-100 text-purple-800',
  }
  return map[status] ?? 'bg-slate-100 text-slate-600'
}

/**
 * @description 将任务状态映射到统一徽章语义色。
 * @param {string} status
 * @returns {string}
 */
function stateTone(status) {
  const map = {
    pending: 'warning',
    late_open: 'warning',
    draft: 'neutral',
    submitted: 'info',
    under_review: 'warning',
    approved: 'success',
    rejected: 'danger',
    appealing: 'purple',
  }
  return map[status] ?? 'neutral'
}

/**
 * @description 任务外显状态文案，优先使用后端派生展示态。
 * @param {Object} task
 * @returns {string}
 */
function displayStatusLabel(task) {
  if (task?.display_status) return task.display_status
  return deriveSubmissionDisplayStatus({
    status: task?.submission_status,
    final_score: task?.final_score,
    is_arbitrated: task?.is_arbitrated,
  }).label
}

/**
 * @description 任务外显状态色调，优先使用后端派生展示态。
 * @param {Object} task
 * @returns {string}
 */
function displayStatusTone(task) {
  if (task?.display_tone) return task.display_tone
  if (!task?.submission_status) return stateTone(task?.entry_state)
  return deriveSubmissionDisplayStatus({
    status: task?.submission_status,
    final_score: task?.final_score,
    is_arbitrated: task?.is_arbitrated,
  }).tone
}

/** 加载任务列表。 */
async function loadTasks() {
  loading.value = true
  listError.value = ''
  try {
    allTasks.value = await getSubmissionTasks()
  } catch (e) {
    listError.value = e.response?.data?.detail ?? '加载任务列表失败'
    allTasks.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 进入任务：start 会自动创建草稿，continue/view 直接跳详情。
 * @param {Object} task
 */
async function goTask(task) {
  actionLoadingProjectId.value = task.project_id
  highlightStore.set('Submissions', task.project_id)
  try {
    if (task.submission_id) {
      router.push({ name: 'SubmissionDetail', params: { id: task.submission_id } })
      return
    }
    const created = await createSubmission({ project: task.project_id, self_score: {}, remark: '' })
    router.push({ name: 'SubmissionDetail', params: { id: created.id } })
  } catch (e) {
    // 并发下如果刚被创建，刷新任务后自动进入已存在草稿。
    await loadTasks()
    const existing = allTasks.value.find((it) => it.project_id === task.project_id && it.submission_id)
    if (existing?.submission_id) {
      router.push({ name: 'SubmissionDetail', params: { id: existing.submission_id } })
      return
    }
    listError.value = e.response?.data?.detail ?? '进入任务失败，请稍后重试'
  } finally {
    actionLoadingProjectId.value = null
  }
}

/**
 * 点击页面任意处清除高亮
 */
function clearHighlight() {
  if (lastHighlightId.value !== null) lastHighlightId.value = null
}

useRealtimeRefresh('submission', loadTasks)

onMounted(() => {
  lastHighlightId.value = highlightStore.pop('Submissions')
  loadTasks()
})
</script>
