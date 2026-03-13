<template>
  <div class="space-y-5">
    <!-- Tab 切换栏 -->
    <div class="flex justify-center overflow-x-auto scrollbar-hide">
      <div ref="tabNavRef" class="liquid-glass-nav">
        <div class="liquid-glass-slider" :style="tabSliderStyle"></div>
        <button
          v-for="(tab, idx) in tabs"
          :key="tab.key"
          :ref="el => setTabPillRef(el, idx)"
          type="button"
          class="liquid-glass-pill"
          :class="activeTab === tab.key ? 'is-sliding-active' : ''"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- ==================== Tab 1: 概览 ==================== -->
    <template v-if="activeTab === 'overview'">
    <!-- 核心数据卡片 第1排 -->
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="stat-card">
        <div class="stat-icon bg-amber-100 text-amber-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
        </div>
        <div>
          <div class="stat-value text-amber-600">{{ data.pending_review_count ?? '—' }}</div>
          <div class="stat-label">待审核提交</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-red-100 text-red-500">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" /></svg>
        </div>
        <div>
          <div class="stat-value text-red-500">{{ data.pending_appeal_count ?? '—' }}</div>
          <div class="stat-label">待处理申诉</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-green-100 text-green-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
        </div>
        <div>
          <div class="stat-value text-green-600">{{ data.completion_rate ?? '—' }}%</div>
          <div class="stat-label">整体完成率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-brand-100 text-brand-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="4" height="8" rx="0.5" /><rect x="10" y="7" width="4" height="13" rx="0.5" /><rect x="17" y="3" width="4" height="17" rx="0.5" /></svg>
        </div>
        <div>
          <div class="stat-value text-brand-600">{{ data.avg_score ?? '—' }}</div>
          <div class="stat-label">平均分</div>
        </div>
      </div>
    </div>

    <!-- 助理提交待审提示 -->
    <div v-if="data.assistant_submissions_pending" class="rounded-xl border border-amber-200 bg-amber-50 p-4">
      <div class="flex items-start gap-3">
        <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
        </div>
        <div class="min-w-0 flex-1">
          <h3 class="text-sm font-semibold text-amber-800">助理提交待审</h3>
          <p class="mt-1 text-xs text-amber-700">
            您负责的班级中有 <strong>{{ data.assistant_submissions_pending }}</strong> 份学生助理的提交尚未审核。助理提交需评审老师亲自确认，请前往审核任务的"异议/分差上报"分类查看。
          </p>
          <div class="mt-2">
            <router-link
              :to="{ name: 'Review' }"
              class="inline-block rounded bg-amber-600 px-3 py-1.5 text-xs text-white hover:bg-amber-700"
            >
              前往审核
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 评阅进度区域 -->
    <div class="grid gap-4 md:grid-cols-2">
      <!-- 评阅进度 -->
      <div class="dash-section">
        <div class="dash-section__header">评阅进度</div>
        <div class="p-4 space-y-4">
          <div>
            <div class="flex items-center justify-between text-sm mb-1.5">
              <span class="text-slate-600">评阅完成</span>
              <span class="font-semibold text-slate-800">
                {{ gp.completed }} / {{ gp.total_assignments }}
              </span>
            </div>
            <div class="h-3 rounded-full bg-slate-100 overflow-hidden">
              <div
                class="h-3 rounded-full bg-green-500 transition-all"
                :style="{ width: `${gradingPct}%` }"
              />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-lg bg-blue-50 p-3 text-center">
              <div class="text-lg font-bold text-blue-600">{{ data.round_stats?.round_1_completed ?? 0 }}</div>
              <div class="text-xs text-blue-700">一评完成</div>
            </div>
            <div class="rounded-lg bg-indigo-50 p-3 text-center">
              <div class="text-lg font-bold text-indigo-600">{{ data.round_stats?.round_2_completed ?? 0 }}</div>
              <div class="text-xs text-indigo-700">二评完成</div>
            </div>
            <div class="rounded-lg bg-green-50 p-3 text-center">
              <div class="text-lg font-bold text-green-600">{{ gp.valid_final_scores }}</div>
              <div class="text-xs text-green-700">有效成绩</div>
            </div>
            <div class="rounded-lg bg-amber-50 p-3 text-center">
              <div class="text-lg font-bold text-amber-600">{{ gp.arbitration_needed }}</div>
              <div class="text-xs text-amber-700">需仲裁</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 完成率 + 评审率双环形图 -->
      <div class="dash-section">
        <div class="flex items-center justify-around py-5 px-4">
          <div class="flex flex-col items-center">
            <RingChart
              :percentage="data.completion_rate ?? 0"
              color="#059669"
              track-color="#d1fae5"
              :size="100"
              :stroke-width="12"
            />
            <p class="mt-2 text-xs font-medium text-slate-700">完成率</p>
          </div>
          <div class="flex flex-col items-center">
            <RingChart
              :percentage="data.review_rate ?? 0"
              color="#3b82f6"
              track-color="#dbeafe"
              :size="100"
              :stroke-width="12"
            />
            <p class="mt-2 text-xs font-medium text-slate-700">评审率</p>
          </div>
        </div>
        <p class="px-4 pb-3 text-center text-xs text-slate-400">负责 {{ data.responsible_class_count ?? 0 }} 个班级</p>
      </div>
    </div>

    <!-- 分班级完成度 -->
    <div class="dash-section">
      <div class="dash-section__header">
        分班级完成情况
        <span class="text-xs font-normal text-slate-400">{{ data.responsible_class_count ?? 0 }} 个班级</span>
      </div>
      <div v-if="!data.class_completion_stats?.length" class="px-4 py-8 text-center text-sm text-slate-400">
        暂无班级数据
      </div>
      <div v-else class="divide-y divide-slate-100">
        <div
          v-for="cls in data.class_completion_stats"
          :key="cls.class_id"
          class="flex items-center gap-3 px-4 py-3"
        >
          <RingChart
            :percentage="cls.completion_rate"
            :color="cls.completion_rate >= 80 ? '#059669' : cls.completion_rate >= 50 ? '#3b82f6' : '#f59e0b'"
            :track-color="cls.completion_rate >= 80 ? '#d1fae5' : cls.completion_rate >= 50 ? '#dbeafe' : '#fef3c7'"
            :size="42"
            :stroke-width="5"
            :show-unit="false"
            class="flex-shrink-0"
          >
            <span class="text-xs font-bold text-slate-700">{{ cls.completion_rate }}%</span>
          </RingChart>
          <div class="min-w-0 flex-1">
            <div class="text-sm font-medium text-slate-800">{{ cls.class_name }}</div>
            <div class="mt-0.5 text-xs text-slate-400">
              已交 {{ cls.submitted }} · 已通过 {{ cls.approved }} · 共 {{ cls.total }} 人
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 各班级平均分对比 -->
    <div v-if="classScoreItems.length" class="dash-section">
      <div class="dash-section__header">各班级平均分对比</div>
      <div class="p-4">
        <MiniBarChart
          :items="classScoreItems"
          :max-value="100"
          suffix="分"
          default-color="#6366f1"
        />
      </div>
    </div>

    <!-- 双评策略概况 -->
    <div class="dash-section">
      <div class="dash-section__header">双评策略概况</div>
      <div class="grid grid-cols-2 gap-3 p-4 md:grid-cols-4">
        <div class="rounded-lg border border-slate-100 bg-slate-50 p-3 text-center">
          <div class="text-lg font-bold text-slate-800">{{ data.assignment_summary?.total_assigned ?? 0 }}</div>
          <div class="text-xs text-slate-500">总分配</div>
        </div>
        <div class="rounded-lg border border-slate-100 bg-slate-50 p-3 text-center">
          <div class="text-lg font-bold text-blue-600">{{ data.assignment_summary?.assistant_assigned ?? 0 }}</div>
          <div class="text-xs text-slate-500">助理任务</div>
        </div>
        <div class="rounded-lg border border-slate-100 bg-slate-50 p-3 text-center">
          <div class="text-lg font-bold text-amber-600">{{ data.assignment_summary?.counselor_assigned ?? 0 }}</div>
          <div class="text-xs text-slate-500">老师任务</div>
        </div>
        <div class="rounded-lg border border-slate-100 bg-slate-50 p-3 text-center">
          <div class="text-xs text-slate-700">
            {{ (data.assignment_summary?.strategy_modes || []).join(' / ') || '未生成任务' }}
          </div>
          <div class="mt-1 text-xs text-slate-500">策略模式</div>
        </div>
      </div>
    </div>

    <!-- 评审任务分发提示：仅当有可放行的 dispatch 任务时显示 -->
    <div v-if="data.pending_dispatch_count" class="rounded-xl border border-amber-200 bg-amber-50 p-4">
      <div class="flex items-start gap-3">
        <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
        </div>
        <div class="min-w-0 flex-1">
          <h3 class="text-sm font-semibold text-amber-800">评审任务待分发</h3>
          <p class="mt-1 text-xs text-amber-700">
            您有 <strong>{{ data.pending_dispatch_count }}</strong> 个待分发任务。
            可将任务下发给{{ assistantLabel }}完成初评，也可自行审核。
          </p>
          <div class="mt-3 flex flex-wrap items-center gap-2">
            <router-link
              :to="{ name: 'Review' }"
              class="rounded bg-amber-600 px-3 py-1.5 text-xs text-white hover:bg-amber-700"
            >
              前往审核列表下发
            </router-link>
            <button
              v-if="releaseProjectIds.length"
              type="button"
              class="rounded border border-amber-400 px-3 py-1.5 text-xs text-amber-700 hover:bg-amber-100 disabled:opacity-50"
              :disabled="quickReleasing"
              @click="quickReleaseAll"
            >
              {{ quickReleasing ? '下发中…' : `一键全部下发给${assistantLabel}` }}
            </button>
          </div>
          <p v-if="quickReleaseResult" class="mt-2 text-xs" :class="quickReleaseError ? 'text-red-600' : 'text-green-700'">{{ quickReleaseResult }}</p>
        </div>
      </div>
    </div>

    <!-- 助理管理入口 -->
    <div ref="assistantRef">
      <AssistantManage
        :responsible-classes="responsibleClasses"
        :class-students="classStudents"
        @class-change="onClassChange"
      />
    </div>

    <!-- 最近待审提交 + 申诉 -->
    <div class="grid gap-5 md:grid-cols-2">
      <div class="dash-section">
        <div class="dash-section__header">最近待审提交</div>
        <div v-if="!data.recent_submissions?.length" class="px-4 py-8 text-center text-sm text-slate-400">
          暂无待审提交
        </div>
        <ul v-else class="divide-y divide-slate-100">
          <li
            v-for="sub in data.recent_submissions"
            :key="sub.id"
            class="flex items-center justify-between px-4 py-3"
          >
            <div>
              <div class="text-sm font-medium text-slate-800">{{ sub.student_name }}</div>
              <div class="mt-0.5 text-xs text-slate-500">{{ sub.project_name }}</div>
              <div class="mt-0.5 text-xs text-slate-400">{{ formatTime(sub.submitted_at) }}</div>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="sub.project_id && data.pending_dispatch_count"
                type="button"
                class="rounded border border-amber-300 bg-amber-50 px-2 py-1 text-xs text-amber-700 hover:bg-amber-100 disabled:opacity-50"
                :disabled="quickReleasing"
                @click.stop="quickReleaseSingle(sub.project_id, sub.id)"
              >
                下发{{ assistantLabel }}
              </button>
              <router-link
                :to="{ name: 'ReviewDetail', params: { id: sub.id } }"
                class="rounded bg-brand-50 px-2 py-1 text-xs text-brand-700 hover:bg-brand-100"
              >
                去审核
              </router-link>
            </div>
          </li>
        </ul>
      </div>

      <div class="dash-section">
        <div class="dash-section__header">最近申诉</div>
        <div v-if="!data.recent_appeals?.length" class="px-4 py-8 text-center text-sm text-slate-400">
          暂无待处理申诉
        </div>
        <ul v-else class="divide-y divide-slate-100">
          <li
            v-for="appeal in data.recent_appeals"
            :key="appeal.id"
            class="flex items-center justify-between px-4 py-3"
          >
            <div>
              <div class="text-sm font-medium text-slate-800">{{ appeal.student_name }}</div>
              <div class="mt-0.5 text-xs text-slate-500">{{ appeal.project_name }}</div>
              <div class="mt-0.5 text-xs text-slate-400 line-clamp-1">{{ appeal.reason }}</div>
            </div>
            <router-link
              :to="{ name: 'AppealDetail', params: { id: appeal.id } }"
              class="rounded bg-amber-50 px-2 py-1 text-xs text-amber-700 hover:bg-amber-100"
            >
              处理
            </router-link>
          </li>
        </ul>
      </div>
    </div>
    </template>

    <!-- ==================== Tab 2: 缺交名单 ==================== -->
    <template v-if="activeTab === 'missing'">
      <MissingSubmissionTab :role-level="ROLE_LEVEL_COUNSELOR" :responsible-class-ids="responsibleClassIds" />
    </template>
  </div>
</template>

<script setup>
/**
 * @description 评审老师（辅导员）工作台组件。
 * 包含两个 Tab：概览、缺交名单。
 * @props {Object} data - Dashboard API 返回的辅导员数据
 */
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import AssistantManage from '@/components/AssistantManage.vue'
import RingChart from '@/components/charts/RingChart.vue'
import MiniBarChart from '@/components/charts/MiniBarChart.vue'
import MissingSubmissionTab from './MissingSubmissionTab.vue'
import api from '@/api/axios'
import { releaseAssignments } from '@/api/review'
import { useRoleMetaStore } from '@/stores/roles'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatTime } from '@/utils/format'
import { ROLE_LEVEL_COUNSELOR } from '@/constants/roles'

const props = defineProps({
  data: { type: Object, required: true },
})
const emit = defineEmits(['refresh'])

const tabs = [
  { key: 'overview', label: '概览' },
  { key: 'missing', label: '缺交名单' },
]
const activeTab = ref('overview')

/* ── Tab 滑块跟踪 ── */
const tabNavRef = ref(null)
const tabPillEls = {}
const tabSliderStyle = ref({ opacity: '0' })
let tabSliderInit = false

/** @param {Element|null} el */
function setTabPillRef(el, idx) {
  if (el) tabPillEls[idx] = el
}

function syncTabSlider() {
  const idx = tabs.findIndex(t => t.key === activeTab.value)
  const el = tabPillEls[idx]
  if (idx < 0 || !el || !tabNavRef.value) return
  const style = {
    left: `${el.offsetLeft}px`,
    top: `${el.offsetTop}px`,
    width: `${el.offsetWidth}px`,
    height: `${el.offsetHeight}px`,
    opacity: '1',
  }
  if (!tabSliderInit) {
    tabSliderInit = true
    style.transition = 'none'
    tabSliderStyle.value = style
    requestAnimationFrame(() => {
      tabSliderStyle.value = { ...tabSliderStyle.value, transition: '' }
    })
  } else {
    tabSliderStyle.value = style
  }
}

watch(activeTab, () => nextTick(syncTabSlider))
onMounted(() => nextTick(() => setTimeout(syncTabSlider, 60)))

const roleMeta = useRoleMetaStore()
roleMeta.ensureLoaded()
const assistantLabel = computed(() => roleMeta.nameByLevel(1))

const responsibleClasses = ref([])
const classStudents = ref([])
const assistantRef = ref(null)
const _activeClassId = ref(null)

/** @returns {number[]} */
const responsibleClassIds = computed(() => responsibleClasses.value.map(c => c.id))

/** @returns {Object} 评阅进度快捷访问 */
const gp = computed(() => props.data.grading_progress ?? {
  total_assignments: 0, completed: 0, pending: 0, valid_final_scores: 0, arbitration_needed: 0,
})

/** @returns {number} 评阅完成百分比 */
const gradingPct = computed(() => {
  const total = gp.value.total_assignments
  return total ? Math.round((gp.value.completed / total) * 100) : 0
})

/** @returns {Array} 各班级平均分对比数据 */
const classScoreItems = computed(() => {
  return (props.data.avg_score_by_class ?? [])
    .filter((c) => c.avg_score != null)
    .map((c) => ({
      label: c.class_name,
      value: c.avg_score,
      color: c.avg_score >= 80 ? '#059669' : c.avg_score >= 60 ? '#3b82f6' : '#f59e0b',
    }))
})
/**
 * @param {number|string} classId
 */
async function onClassChange(classId) {
  _activeClassId.value = classId || null
  if (!classId) {
    classStudents.value = []
    return
  }
  try {
    const res = await api.get(`/classes/${classId}/students/`)
    classStudents.value = res.data?.students ?? []
  } catch {
    classStudents.value = []
  }
}

async function loadResponsibleClasses() {
  try {
    const meRes = await api.get('/users/me/')
    const me = meRes.data
    const classIds = me.responsible_class_ids ?? []
    if (classIds.length) {
      const clsRes = await api.get('/classes/', { params: { ids: classIds.join(',') } })
      const all = Array.isArray(clsRes.data) ? clsRes.data : (clsRes.data?.results ?? [])
      responsibleClasses.value = all.filter((c) => classIds.includes(c.id))
    }
  } catch {
    responsibleClasses.value = []
  }
}

/** @type {import('vue').ComputedRef<number[]>} */
const releaseProjectIds = computed(() => {
  const ids = new Set()
  for (const sub of props.data.recent_submissions ?? []) {
    if (sub.project_id) ids.add(sub.project_id)
  }
  return [...ids]
})
const quickReleasing = ref(false)
const quickReleaseResult = ref('')
const quickReleaseError = ref(false)

/**
 * @description 一键放行所有待审项目到助理。
 */
async function quickReleaseAll() {
  quickReleasing.value = true
  quickReleaseResult.value = ''
  quickReleaseError.value = false
  let totalCreated = 0
  const errors = []
  for (const pid of releaseProjectIds.value) {
    try {
      const res = await releaseAssignments({ project_id: pid })
      totalCreated += res.created_assistant_tasks ?? 0
    } catch (e) {
      errors.push(e.response?.data?.detail ?? `项目${pid}放行失败`)
    }
  }
  if (errors.length) {
    quickReleaseError.value = true
    quickReleaseResult.value = errors.join('；')
  } else {
    quickReleaseResult.value = totalCreated > 0
      ? `已下发 ${totalCreated} 个${assistantLabel.value}评审任务`
      : '暂无可下发的任务（可能尚未在项目配置中生成评审任务）'
  }
  quickReleasing.value = false
  emit('refresh')
}

/**
 * @param {number} projectId
 * @param {number} submissionId
 */
async function quickReleaseSingle(projectId, submissionId) {
  quickReleasing.value = true
  quickReleaseResult.value = ''
  quickReleaseError.value = false
  try {
    const res = await releaseAssignments({ project_id: projectId, submission_ids: [submissionId] })
    quickReleaseResult.value = `已下发 ${res.created_assistant_tasks ?? 0} 个${assistantLabel.value}评审任务`
  } catch (e) {
    quickReleaseError.value = true
    const msg = e.response?.data?.detail ?? '下发失败'
    quickReleaseResult.value = msg.includes('尚未生成任务')
      ? '项目尚未生成评审任务，请先在「项目配置 → 评审规则」中点击"生成评审任务"'
      : msg
  } finally {
    quickReleasing.value = false
  }
  emit('refresh')
}

onMounted(loadResponsibleClasses)

useRealtimeRefresh(['class', 'user'], () => {
  loadResponsibleClasses()
  if (_activeClassId.value) onClassChange(_activeClassId.value)
})
</script>
