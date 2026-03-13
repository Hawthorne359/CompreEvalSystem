<template>
  <div class="page-shell" @click="clearHighlight">
    <div class="flex items-center justify-between">
      <h2 class="app-page-title">待评分任务</h2>
      <span class="rounded-full bg-brand-50 px-3 py-1 text-sm text-brand-700 font-medium">
        {{ assistantLabel }}
      </span>
    </div>

    <!-- 加载/错误状态 -->
    <div v-if="loading" class="rounded border border-slate-200 bg-white py-12 text-center text-slate-500">
      加载中…
    </div>
    <div v-else-if="error" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ error }}
    </div>

    <!-- 空状态 -->
    <div
      v-else-if="tasks.length === 0"
      class="rounded-xl border border-slate-200 bg-white py-16 text-center"
    >
      <div class="text-4xl">📋</div>
      <p class="mt-3 text-slate-500">暂无待评分任务</p>
      <p class="mt-1 text-sm text-slate-400">{{ counselorLabel }}分配评分任务后，将在此处显示</p>
    </div>

    <!-- 任务列表 -->
    <div v-else class="space-y-3">
      <!-- 统计卡片行 -->
      <div class="grid grid-cols-2 gap-3 md:grid-cols-3">
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="text-2xl font-bold text-brand-600">{{ tasks.length }}</div>
          <div class="mt-1 text-sm text-slate-500">待评任务总数</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="text-2xl font-bold text-amber-600">{{ submittedCount }}</div>
          <div class="mt-1 text-sm text-slate-500">已提交待初审</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="text-2xl font-bold text-blue-600">{{ underReviewCount }}</div>
          <div class="mt-1 text-sm text-slate-500">审核中</div>
        </div>
      </div>

      <!-- 提交列表 -->
      <div class="app-surface overflow-hidden">
        <div class="border-b border-slate-200 px-4 py-3 text-sm font-medium text-slate-700">
          提交列表（{{ tasks.length }} 条）
        </div>
        <!-- 移动端卡片 -->
        <div class="mobile-card-list md:hidden">
          <div
            v-for="item in tasks"
            :key="item.id"
            class="mobile-card-link"
            :class="item.id === lastHighlightId ? 'bg-blue-50' : ''"
            @click="goToDetail(item.id)"
          >
            <div class="mobile-card-body">
              <div class="flex items-center gap-2">
                <span class="mobile-card-title">{{ item.project_name || '—' }}</span>
                <StatusBadge :text="statusLabel(item)" :tone="statusTone(item)" />
              </div>
              <div class="mobile-card-sub">{{ item.user_name || '—' }}</div>
              <div class="mobile-card-meta">{{ formatTime(item.submitted_at) }}</div>
            </div>
            <svg class="mobile-card-arrow" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
          </div>
        </div>
        <!-- PC 端表格 -->
        <table class="hidden w-full text-sm md:table">
          <thead class="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th class="px-4 py-3 text-left font-medium">测评项目</th>
              <th class="px-4 py-3 text-left font-medium">学生姓名/学号</th>
              <th class="px-4 py-3 text-left font-medium">提交时间</th>
              <th class="px-4 py-3 text-left font-medium">状态</th>
              <th class="px-4 py-3 text-left font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="item in tasks"
              :key="item.id"
              :class="item.id === lastHighlightId ? 'bg-blue-50' : 'hover:bg-slate-50'"
            >
              <td class="px-4 py-3 font-medium text-slate-800">{{ item.project_name || '—' }}</td>
              <td class="px-4 py-3 text-slate-600">
                <div>{{ item.user_name || item.user_username || '—' }}</div>
                <div class="text-xs text-slate-400">{{ item.user_student_no || '' }}</div>
              </td>
              <td class="px-4 py-3 text-slate-500">{{ formatTime(item.submitted_at) }}</td>
              <td class="px-4 py-3">
                <StatusBadge :text="statusLabel(item)" :tone="statusTone(item)" />
              </td>
              <td class="px-4 py-3">
                <button
                  type="button"
                  class="rounded bg-brand-500 px-3 py-1 text-xs text-white hover:bg-brand-600"
                  @click="goToDetail(item.id)"
                >
                  去评分
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 学生助理（评卷助理）待评分任务列表页。
 * 展示助理负责班级中所有处于 submitted/under_review 状态的提交。
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useHighlightStore } from '@/stores/highlight'
import StatusBadge from '@/components/StatusBadge.vue'
import { getAssistantTasks } from '@/api/review'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatTime } from '@/utils/format'
import { useRoleMetaStore } from '@/stores/roles'
import { deriveWorkflowSubmissionStatus } from '@/utils/submissionStatus'

const router = useRouter()
const roleMeta = useRoleMetaStore()
const assistantLabel = computed(() => roleMeta.nameByLevel(1))
const counselorLabel = computed(() => roleMeta.nameByLevel(2))
const highlightStore = useHighlightStore()
const lastHighlightId = ref(null)

const tasks = ref([])
const loading = ref(true)
const error = ref('')

/** 已提交待初审的数量 */
const submittedCount = computed(() => tasks.value.filter((t) => t.status === 'submitted').length)
/** 审核中的数量 */
const underReviewCount = computed(() => tasks.value.filter((t) => t.status === 'under_review').length)

/**
 * @param {Object} task - 提交任务
 * @returns {string}
 */
function statusLabel(task) { return deriveWorkflowSubmissionStatus(task).label }
/**
 * @param {Object} task - 提交任务
 * @returns {string}
 */
function statusTone(task) { return deriveWorkflowSubmissionStatus(task).tone }

/**
 * 跳转到评分详情页（复用审核详情页）
 * @param {number} id - 提交 ID
 */
function goToDetail(id) {
  highlightStore.set('AssistantTasks', id)
  router.push({ name: 'ReviewDetail', params: { id } })
}

/**
 * 点击页面任意处清除高亮
 */
function clearHighlight() {
  if (lastHighlightId.value !== null) lastHighlightId.value = null
}

/** 加载助理任务列表 */
async function loadTasks() {
  try {
    loading.value = true
    tasks.value = await getAssistantTasks()
  } catch (e) {
    error.value = e.response?.data?.detail ?? '加载任务失败，请刷新重试'
  } finally {
    loading.value = false
  }
}

useRealtimeRefresh(['score', 'submission'], loadTasks)

onMounted(() => {
  lastHighlightId.value = highlightStore.pop('AssistantTasks')
  loadTasks()
})
</script>
