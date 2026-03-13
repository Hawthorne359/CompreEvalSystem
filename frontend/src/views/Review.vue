<template>
  <div class="page-shell" @click="clearHighlight">
    <div class="flex items-center justify-between gap-3">
      <h2 class="app-page-title">{{ isReadonly ? '提交监控' : '审核任务' }}</h2>
      <div class="flex items-center gap-2">
        <button
          v-if="canOperate && pendingProjectIds.length"
          type="button"
          class="shrink-0 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs text-amber-700 hover:bg-amber-100 md:text-sm disabled:opacity-50"
          :disabled="releasing"
          @click="showReleasePanel = !showReleasePanel"
        >
          放行任务到{{ assistantLabel }}
        </button>
        <router-link
          v-if="canOperate"
          :to="{ name: 'ScoreImport' }"
          class="shrink-0 rounded-lg bg-brand-500 px-3 py-1.5 text-xs text-white hover:bg-brand-600 md:text-sm"
        >
          批量导入成绩
        </router-link>
      </div>
    </div>

    <!-- 监督视角提示 -->
    <div v-if="isReadonly" class="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm text-blue-700">
      当前为监督视角，仅可查看提交与评分情况。如需评分裁定，请前往
      <router-link :to="{ name: 'Appeals' }" class="font-medium underline">申诉模块</router-link> 处理。
    </div>

    <div v-if="showReleasePanel && canOperate" class="app-surface p-4">
      <h3 class="mb-2 text-sm font-medium text-slate-800">放行待分发任务到{{ assistantLabel }}</h3>
      <p class="mb-3 text-xs text-slate-500">将待分发任务批量放行给{{ assistantLabel }}评审。放行后{{ assistantLabel }}即可在"待评分任务"中查看。</p>
      <div class="flex flex-wrap items-center gap-2">
        <button
          v-for="pid in pendingProjectIds"
          :key="pid"
          type="button"
          class="rounded border border-amber-300 px-3 py-1.5 text-xs text-amber-700 hover:bg-amber-50 disabled:opacity-50"
          :disabled="releasing"
          @click="doRelease(pid)"
        >
          放行「{{ projectNameMap[pid] || `项目${pid}` }}」
        </button>
        <button
          v-if="pendingProjectIds.length > 1"
          type="button"
          class="rounded bg-amber-600 px-3 py-1.5 text-xs text-white hover:bg-amber-700 disabled:opacity-50"
          :disabled="releasing"
          @click="doReleaseAll"
        >
          {{ releasing ? '放行中…' : '全部放行' }}
        </button>
      </div>
      <p v-if="releaseResult" class="mt-2 text-xs" :class="releaseError ? 'text-red-600' : 'text-green-600'">{{ releaseResult }}</p>
    </div>

    <div class="app-surface p-3 md:p-4">
      <div class="flex flex-col gap-3 md:flex-row md:items-center">
        <!-- 主分类 Tab -->
        <div class="flex items-center gap-2">
          <button
            v-for="tab in categoryTabs"
            :key="tab.value"
            type="button"
            class="rounded px-3 py-1.5 text-sm transition-colors"
            :class="activeCategory === tab.value
              ? 'bg-brand-500 text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            @click="switchCategory(tab.value)"
          >
            {{ tab.label }}
            <span v-if="tab.value === 'disputed' && disputedCount > 0" class="ml-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] text-white">{{ disputedCount }}</span>
          </button>
        </div>
        <!-- 二级筛选 -->
        <div class="flex items-center gap-2 md:ml-auto">
          <button
            v-for="tab in subTabOptions"
            :key="tab.value"
            type="button"
            class="rounded px-2.5 py-1 text-xs transition-colors"
            :class="activeSubTab === tab.value
              ? 'bg-slate-700 text-white'
              : 'bg-slate-100 text-slate-500 hover:bg-slate-200'"
            @click="switchSubTab(tab.value)"
          >
            {{ tab.label }}
          </button>
          <select
            v-if="activeCategory !== 'disputed'"
            v-model="filterStatus"
            class="app-select ml-2"
            @change="applyFilters"
          >
            <option value="">全部状态</option>
            <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
          <select
            v-else
            v-model="objectionFilterStatus"
            class="app-select ml-2"
            @change="applyFilters"
          >
            <option value="">全部状态</option>
            <option v-for="s in objectionStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="rounded border border-slate-200 bg-white py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="listError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ listError }}</div>

    <div v-else class="space-y-3">
      <template v-if="activeCategory !== 'disputed'">
      <div class="mobile-card-list">
        <div
          v-for="item in filteredList"
          :key="`mobile-${item.id}`"
          class="mobile-card-link"
          :class="item.id === lastHighlightId ? 'bg-blue-50' : ''"
          @click="highlightStore.set('Review', item.id); router.push({ name: 'ReviewDetail', params: { id: item.id } })"
        >
          <div class="mobile-card-body">
            <div class="flex items-center gap-2">
              <span class="mobile-card-title">{{ item.project_name || '—' }}</span>
              <StatusBadge :text="statusLabel(item)" :tone="statusTone(item)" />
              <span v-if="item.is_assistant_submission" class="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-700">助理提交</span>
              <span v-if="item.has_score_dispute" class="rounded bg-red-100 px-1.5 py-0.5 text-[10px] text-red-700">分差异议</span>
            </div>
            <div class="mobile-card-sub">{{ studentDisplay(item) }} · {{ studentOrgDisplay(item) }} · 得分：{{ item.final_score != null ? item.final_score : '—' }}</div>
            <div class="mobile-card-meta">{{ formatDateTime(item.submitted_at) }}</div>
          </div>
          <svg class="mobile-card-arrow" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
        </div>
        <div v-if="filteredList.length === 0" class="rounded border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
          {{ emptyHint(activeCategory) }}
        </div>
      </div>

      <div class="app-table-wrap hidden md:block">
        <table class="app-table">
        <thead>
          <tr class="border-b border-slate-200 bg-slate-50">
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">项目名称</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">学生</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">班级 / 学院</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">状态</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">提交时间</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">最终得分</th>
            <th v-if="activeCategory === 'all' || activeCategory === 'disputed'" class="px-4 py-2.5 text-left font-medium text-slate-700">{{ activeCategory === 'disputed' ? '异常原因' : '标记' }}</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in filteredList"
            :key="item.id"
            class="border-b border-slate-100"
            :class="item.id === lastHighlightId ? 'bg-blue-50' : 'hover:bg-slate-50'"
          >
            <td class="px-4 py-2.5 text-slate-800">{{ item.project_name || '—' }}</td>
            <td class="px-4 py-2.5 text-slate-800">{{ studentDisplay(item) }}</td>
            <td class="px-4 py-2.5 text-slate-500 text-xs">{{ studentOrgDisplay(item) }}</td>
            <td class="px-4 py-2.5">
              <StatusBadge :text="statusLabel(item)" :tone="statusTone(item)" />
            </td>
            <td class="px-4 py-2.5 text-slate-600">{{ formatDateTime(item.submitted_at) }}</td>
            <td class="px-4 py-2.5 text-slate-800">{{ item.final_score != null ? item.final_score : '—' }}</td>
            <td v-if="activeCategory === 'all' || activeCategory === 'disputed'" class="px-4 py-2.5">
              <span class="flex flex-wrap gap-1">
                <span v-if="item.is_assistant_submission" class="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700">助理提交</span>
                <span v-if="item.has_score_dispute" class="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700">分差异议</span>
                <span v-if="!item.has_score_dispute && !item.is_assistant_submission" class="text-slate-400">—</span>
              </span>
            </td>
            <td class="px-4 py-2.5">
              <router-link
                :to="{ name: 'ReviewDetail', params: { id: item.id } }"
                class="app-action app-action-primary"
                @click="highlightStore.set('Review', item.id)"
              >
                {{ isReadonly ? '查看' : '审核' }}
              </router-link>
            </td>
          </tr>
          <tr v-if="filteredList.length === 0">
            <td :colspan="(activeCategory === 'all' || activeCategory === 'disputed') ? 7 : 6" class="px-4 py-8 text-center text-slate-500">
              {{ emptyHint(activeCategory) }}
            </td>
          </tr>
        </tbody>
        </table>
      </div>
      </template>

      <template v-else>
        <div class="mobile-card-list">
          <div
            v-for="item in filteredObjections"
            :key="`obj-mobile-${item.id}`"
            class="rounded border border-slate-200 bg-white p-3"
          >
            <div class="flex items-center justify-between gap-2">
              <p class="text-sm font-medium text-slate-800">工单 #{{ item.id }} · {{ item.indicator_name }}</p>
              <span class="rounded bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">{{ objectionStatusLabel(item.status) }}</span>
            </div>
            <p class="mt-1 text-xs text-slate-500">提交 #{{ item.submission_id }} · 发起人 {{ item.raised_by_name }}</p>
            <p class="mt-1 text-xs text-slate-700 line-clamp-2">{{ item.reason }}</p>
            <div v-if="canHandleObjection(item)" class="mt-2 flex flex-wrap gap-2">
              <button type="button" class="rounded bg-green-600 px-2 py-1 text-xs text-white" @click="doHandleObjection(item, 'resolve')">裁定通过</button>
              <button type="button" class="rounded bg-red-600 px-2 py-1 text-xs text-white" @click="doHandleObjection(item, 'reject')">驳回</button>
              <button v-if="item.status === 'pending_counselor' && currentLevel >= 2" type="button" class="rounded border border-amber-400 px-2 py-1 text-xs text-amber-700" @click="doHandleObjection(item, 'escalate_director')">上报主任</button>
              <button v-if="item.status === 'escalated_to_director' && currentLevel >= 3" type="button" class="rounded border border-orange-400 px-2 py-1 text-xs text-orange-700" @click="doHandleObjection(item, 'escalate_admin')">上报超管</button>
            </div>
          </div>
          <div v-if="filteredObjections.length === 0" class="rounded border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
            暂无异议工单
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
/**
 * 审核任务列表：
 * - LV2 评审老师：分"学生提交总览"和"异议/分差上报"两个分类，可操作
 * - LV3 院系主任 / LV5 超管：监督视角，只读查看
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getReviewTasks, getReviewObjections, handleReviewObjection, releaseAssignments } from '@/api/review'
import { useAuthStore } from '@/stores/auth'
import { useHighlightStore } from '@/stores/highlight'
import { useRoleMetaStore } from '@/stores/roles'
import StatusBadge from '@/components/StatusBadge.vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatDateTime } from '@/utils/format'
import { ROLE_LEVEL_ASSISTANT, ROLE_LEVEL_COUNSELOR, ROLE_LEVEL_DIRECTOR } from '@/constants/roles'
import {
  deriveWorkflowSubmissionStatus,
  isDoneSubmission,
  isPendingSubmission,
} from '@/utils/submissionStatus'

const router = useRouter()

const auth = useAuthStore()
const highlightStore = useHighlightStore()
const roleMeta = useRoleMetaStore()
roleMeta.ensureLoaded()
const assistantLabel = computed(() => roleMeta.nameByLevel(ROLE_LEVEL_ASSISTANT))
const lastHighlightId = ref(null)

const currentLevel = computed(() => auth.user?.current_role?.level ?? -1)

/**
 * @description 用户所有角色中的最高 level
 * @type {import('vue').ComputedRef<number>}
 */
const maxRoleLevel = computed(() => {
  const roles = (auth.user?.user_roles ?? []).map((ur) => ur.role?.level ?? -1)
  return roles.length ? Math.max(...roles) : -1
})

/**
 * @description 是否为降权状态（最高角色 level 高于当前 level）
 * @type {import('vue').ComputedRef<boolean>}
 */
const isDelegated = computed(() => maxRoleLevel.value > currentLevel.value)

/** @type {import('vue').ComputedRef<boolean>} LV2 评审老师才能操作 */
const canOperate = computed(() => currentLevel.value === ROLE_LEVEL_COUNSELOR)
/** @type {import('vue').ComputedRef<boolean>} LV3/LV5 只读监督 */
const isReadonly = computed(() => currentLevel.value >= ROLE_LEVEL_DIRECTOR)

/**
 * @description 空列表提示文案，区分降级用户与普通用户。
 * @param {'all'|'disputed'} category
 * @returns {string}
 */
function emptyHint(category) {
  if (category === 'disputed') return '暂无异议/上报/助理提交待审任务'
  if (isDelegated.value) {
    return '您当前以「' + (auth.user?.current_role?.name ?? roleMeta.nameByLevel(ROLE_LEVEL_COUNSELOR)) + '」身份查看。如需介入评分，请进入详情页通过仲裁通道操作。'
  }
  if (canOperate.value && list.value.length === 0) {
    return '当前账号暂无分配的审核任务。如需评审，请联系管理员分配任务或通过项目配置页补充分配。'
  }
  return '暂无审核任务'
}

const showReleasePanel = ref(false)
const releasing = ref(false)
const releaseResult = ref('')
const releaseError = ref(false)

/** @type {import('vue').ComputedRef<number[]>} */
const pendingProjectIds = computed(() => {
  const ids = new Set()
  for (const item of list.value) {
    if (isPendingSubmission(item)) {
      ids.add(item.project)
    }
  }
  return [...ids]
})

const projectNameMap = computed(() => {
  const map = {}
  for (const item of list.value) {
    if (item.project && item.project_name) map[item.project] = item.project_name
  }
  return map
})

/**
 * @param {number} projectId
 */
async function doRelease(projectId) {
  releasing.value = true
  releaseResult.value = ''
  releaseError.value = false
  try {
    const res = await releaseAssignments({ project_id: projectId })
    releaseResult.value = `放行完成：已下发 ${res.created_assistant_tasks ?? 0} 个${assistantLabel.value}任务`
    if (res.skipped?.length) {
      releaseResult.value += `，跳过 ${res.skipped.length} 个（${assistantLabel.value}不足）`
    }
    await loadList()
  } catch (e) {
    releaseError.value = true
    releaseResult.value = e.response?.data?.detail ?? '放行失败'
  } finally {
    releasing.value = false
  }
}

async function doReleaseAll() {
  releasing.value = true
  releaseResult.value = ''
  releaseError.value = false
  let totalCreated = 0
  let totalSkipped = 0
  const errors = []
  for (const pid of pendingProjectIds.value) {
    try {
      const res = await releaseAssignments({ project_id: pid })
      totalCreated += res.created_assistant_tasks ?? 0
      totalSkipped += res.skipped?.length ?? 0
    } catch (e) {
      errors.push(projectNameMap.value[pid] || `项目${pid}`)
    }
  }
  if (errors.length) {
    releaseError.value = true
    releaseResult.value = `部分放行失败：${errors.join('、')}；已下发 ${totalCreated} 个${assistantLabel.value}任务`
  } else {
    releaseResult.value = `全部放行完成：已下发 ${totalCreated} 个${assistantLabel.value}任务`
    if (totalSkipped) releaseResult.value += `，跳过 ${totalSkipped} 个`
  }
  await loadList()
  releasing.value = false
}

/**
 * @description 格式化学生显示信息：学号（姓名）
 * @param {Object} item
 * @returns {string}
 */
function studentDisplay(item) {
  const id = item.user_student_no || item.user_name || '—'
  return item.user_real_name ? `${id}（${item.user_real_name}）` : id
}

/**
 * @description 格式化学生所属信息：学院 / 班级
 * @param {Object} item
 * @returns {string}
 */
function studentOrgDisplay(item) {
  const parts = []
  if (item.user_department_name) parts.push(item.user_department_name)
  if (item.user_class_name) parts.push(item.user_class_name)
  return parts.join(' / ') || '—'
}

const categoryTabs = computed(() => [
  { value: 'all', label: canOperate.value ? '学生提交总览' : '提交总览' },
  { value: 'disputed', label: canOperate.value ? '异议/分差上报' : '异常监控' },
])

const subTabOptions = [
  { value: 'pending', label: '待办' },
  { value: 'done', label: '已办' },
]

const statusOptions = [
  { value: 'submitted', label: '已提交' },
  { value: 'under_review', label: '审核中' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
]

const loading = ref(false)
const listError = ref('')
const list = ref([])
const objectionList = ref([])
const activeCategory = ref('all')
const activeSubTab = ref('pending')
const filterStatus = ref('')
const objectionFilterStatus = ref('')

const disputedCount = computed(() =>
  objectionList.value.filter((i) =>
    ['pending_counselor', 'escalated_to_director', 'escalated_to_admin'].includes(i.status),
  ).length
)

const filteredList = computed(() => {
  let items = list.value
  if (activeCategory.value === 'disputed') {
    items = items.filter((i) => i.has_score_dispute || i.is_assistant_submission)
  }
  if (activeSubTab.value === 'pending') {
    if (activeCategory.value === 'disputed') {
      items = items.filter((i) => isPendingSubmission(i) && i.final_score == null)
    } else {
      items = items.filter((i) => isPendingSubmission(i))
    }
  } else {
    if (activeCategory.value === 'disputed') {
      items = items.filter((i) => isDoneSubmission(i))
    } else {
      items = items.filter((i) => isDoneSubmission(i))
    }
  }
  if (filterStatus.value) {
    items = items.filter((i) => i.status === filterStatus.value)
  }
  return items
})

const objectionStatusOptions = [
  { value: 'pending_counselor', label: '待辅导员处理' },
  { value: 'escalated_to_director', label: '待主任处理' },
  { value: 'escalated_to_admin', label: '待超管处理' },
  { value: 'resolved_by_counselor', label: '辅导员已处理' },
  { value: 'resolved_by_director', label: '主任已处理' },
  { value: 'resolved_by_admin', label: '超管已处理' },
  { value: 'rejected', label: '已驳回' },
]

const filteredObjections = computed(() => {
  let items = objectionList.value
  if (activeSubTab.value === 'pending') {
    items = items.filter((i) =>
      ['pending_counselor', 'escalated_to_director', 'escalated_to_admin'].includes(i.status),
    )
  } else {
    items = items.filter((i) =>
      ['resolved_by_counselor', 'resolved_by_director', 'resolved_by_admin', 'rejected'].includes(i.status),
    )
  }
  if (objectionFilterStatus.value) {
    items = items.filter((i) => i.status === objectionFilterStatus.value)
  }
  return items
})

/**
 * @param {string} status
 * @returns {string}
 */
function objectionStatusLabel(status) {
  const option = objectionStatusOptions.find((i) => i.value === status)
  return option?.label || status
}

/**
 * @param {Object} item
 * @returns {boolean}
 */
function canHandleObjection(item) {
  if (currentLevel.value >= 5 && item.status === 'escalated_to_admin') return true
  if (currentLevel.value >= 3 && item.status === 'escalated_to_director') return true
  if (currentLevel.value >= 2 && item.status === 'pending_counselor') return true
  return false
}

/**
 * @param {Object} item
 * @param {'resolve'|'reject'|'escalate_director'|'escalate_admin'} action
 */
async function doHandleObjection(item, action) {
  if (!canHandleObjection(item)) return
  let resolvedScore
  let resolutionComment = ''
  if (action === 'resolve') {
    const scoreText = window.prompt('请输入裁定分数：')
    if (scoreText == null) return
    const scoreNum = Number(scoreText)
    if (Number.isNaN(scoreNum)) {
      window.alert('分数格式不正确')
      return
    }
    resolvedScore = scoreNum
    resolutionComment = window.prompt('请输入处理意见（可留空）：') || ''
  } else {
    resolutionComment = window.prompt('请输入处理意见（可留空）：') || ''
  }
  try {
    await handleReviewObjection(item.id, {
      action,
      resolved_score: resolvedScore,
      resolution_comment: resolutionComment || undefined,
    })
    await Promise.all([loadList(), loadObjectionList()])
  } catch (e) {
    window.alert(e.response?.data?.detail ?? '处理失败')
  }
}

function statusLabel(submission) {
  return deriveWorkflowSubmissionStatus(submission).label
}

/**
 * @param {Object} submission
 * @returns {string}
 */
function statusTone(submission) {
  return deriveWorkflowSubmissionStatus(submission).tone
}

function switchCategory(cat) {
  activeCategory.value = cat
  filterStatus.value = ''
  objectionFilterStatus.value = ''
}

function switchSubTab(tab) {
  activeSubTab.value = tab
  filterStatus.value = ''
}

function applyFilters() { /* filterStatus is reactive, computed will recalculate */ }

async function loadList() {
  loading.value = true
  listError.value = ''
  try {
    list.value = await getReviewTasks()
  } catch (e) {
    listError.value = e.response?.data?.detail ?? '加载审核列表失败'
    list.value = []
  } finally {
    loading.value = false
  }
}

async function loadObjectionList() {
  try {
    objectionList.value = await getReviewObjections()
  } catch {
    objectionList.value = []
  }
}

function clearHighlight() {
  if (lastHighlightId.value !== null) lastHighlightId.value = null
}

useRealtimeRefresh(['submission', 'score'], async () => {
  await Promise.all([loadList(), loadObjectionList()])
})

onMounted(() => {
  lastHighlightId.value = highlightStore.pop('Review')
  Promise.all([loadList(), loadObjectionList()])
})
</script>
