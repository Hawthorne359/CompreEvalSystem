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
    <!-- 顶部：统计卡片 + 环形图 -->
    <div class="grid gap-4 md:grid-cols-3">
      <!-- 左侧统计卡片 -->
      <div class="md:col-span-2 grid grid-cols-2 gap-3">
        <div class="stat-card">
          <div class="stat-icon bg-green-100 text-green-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
          </div>
          <div>
            <div class="stat-value text-green-600">{{ data.completion_rate ?? '—' }}%</div>
            <div class="stat-label">全院完成率</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-blue-100 text-blue-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
          </div>
          <div>
            <div class="stat-value text-blue-600">{{ data.review_rate ?? '—' }}%</div>
            <div class="stat-label">评审完成率</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-red-100 text-red-500">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
          </div>
          <div>
            <div class="stat-value text-red-500">{{ data.pending_appeal_count ?? '—' }}</div>
            <div class="stat-label">待处理申诉</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-amber-100 text-amber-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
          </div>
          <div>
            <div class="stat-value text-amber-600">{{ data.avg_score ?? '—' }}</div>
            <div class="stat-label">全院平均分</div>
          </div>
        </div>
      </div>

      <!-- 右侧完成率环形图 -->
      <div class="dash-section flex flex-col items-center justify-center py-5 px-4">
        <RingChart
          :percentage="data.completion_rate ?? 0"
          color="#059669"
          track-color="#d1fae5"
          :size="130"
          :stroke-width="14"
        />
        <p class="mt-3 text-xs text-slate-500">
          已通过 {{ data.total_approved ?? 0 }} / {{ data.total_submissions ?? 0 }}
        </p>
      </div>
    </div>

    <!-- 第二行指标 -->
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="stat-card">
        <div class="stat-icon bg-blue-100 text-blue-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
          </div>
        <div>
          <div class="stat-value text-blue-600">{{ data.total_submissions ?? '—' }}</div>
          <div class="stat-label">总提交数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-indigo-100 text-indigo-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
          </div>
        <div>
          <div class="stat-value text-indigo-600">{{ data.valid_final_scores ?? '—' }}</div>
          <div class="stat-label">有效成绩数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-amber-100 text-amber-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
          </div>
        <div>
          <div class="stat-value text-amber-600">{{ data.pending_review_count ?? '—' }}</div>
          <div class="stat-label">待审核</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-slate-100 text-slate-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
          </div>
        <div>
          <div class="stat-value text-slate-700">{{ data.appeal_rate ?? '—' }}%</div>
          <div class="stat-label">申诉率</div>
        </div>
      </div>
    </div>

    <!-- 评阅进度区域 -->
    <div class="grid gap-4 md:grid-cols-2">
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
                class="h-3 rounded-full bg-blue-500 transition-all"
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

      <!-- 评审率环形图 -->
      <div class="dash-section flex flex-col items-center justify-center py-5 px-4">
        <RingChart
          :percentage="data.review_rate ?? 0"
          color="#3b82f6"
          track-color="#dbeafe"
          :size="120"
          :stroke-width="14"
        />
        <p class="mt-3 text-sm font-medium text-slate-700">评审完成率</p>
        <p class="mt-0.5 text-xs text-slate-400">待评 {{ gp.pending }} 个任务</p>
      </div>
    </div>

    <!-- 各专业完成率雷达图 -->
    <div v-if="majorStatsValid" class="dash-section">
      <div class="dash-section__header">
        各专业完成率雷达图
        <span v-if="data.department_name" class="text-xs font-normal text-slate-400">
          {{ data.department_name }}
        </span>
      </div>
      <div class="p-4">
        <RadarChart
          :indicators="majorRadarIndicators"
          :series-data="majorRadarSeries"
          :height="280"
        />
      </div>
    </div>

    <!-- 各专业成绩分布（柱状图）+ 下钻 -->
    <div class="dash-section">
      <div class="dash-section__header">
        各专业成绩分布
        <span v-if="data.department_name" class="text-xs font-normal text-slate-400">
          {{ data.department_name }}
        </span>
      </div>
      <div class="p-4">
        <MiniBarChart
          :items="majorBarItems"
          :max-value="100"
          suffix="分"
          default-color="#6366f1"
        />
      </div>
      <!-- 可展开专业详情 -->
      <div v-if="data.major_stats?.length" class="border-t border-slate-100">
        <button
          v-for="major in data.major_stats"
          :key="major.major_id"
          type="button"
          class="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm transition-colors hover:bg-slate-50"
          @click="drillIntoMajor(major)"
        >
          <div>
            <span class="font-medium text-slate-800">{{ major.major_name }}</span>
            <span class="ml-2 text-xs text-slate-400">
              完成率 {{ major.completion_rate }}% · 均分 {{ major.avg_score }}
            </span>
          </div>
          <svg class="h-4 w-4 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
        </button>
      </div>
    </div>

    <!-- 下钻结果：专业内的班级 -->
    <div v-if="data.drill_data" class="dash-section">
      <div class="dash-section__header">
        班级详情
        <button
          type="button"
          class="text-xs text-brand-600 hover:underline"
          @click="emit('drill', {})"
        >返回</button>
      </div>
      <div v-if="!data.drill_data.length" class="px-4 py-8 text-center text-sm text-slate-400">
        暂无数据
      </div>
      <div v-else class="divide-y divide-slate-100">
        <div
          v-for="cls in data.drill_data"
          :key="cls.class_id"
          class="flex items-center gap-3 px-4 py-3"
        >
          <div class="min-w-0 flex-1">
            <div class="text-sm font-medium text-slate-800">{{ cls.class_name }}</div>
            <div class="mt-1 flex items-center gap-3 text-xs text-slate-500">
              <span>提交 {{ cls.total }}</span>
              <span>通过 {{ cls.approved }}</span>
              <span v-if="cls.avg_score">均分 {{ cls.avg_score }}</span>
            </div>
            <div class="mt-1.5 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                class="h-2 rounded-full transition-all"
                :class="cls.completion_rate >= 80 ? 'bg-green-500' : cls.completion_rate >= 50 ? 'bg-blue-500' : 'bg-amber-500'"
                :style="{ width: `${Math.min(cls.completion_rate, 100)}%` }"
              />
            </div>
          </div>
          <div class="text-right flex-shrink-0">
            <div class="text-sm font-bold" :class="cls.completion_rate >= 80 ? 'text-green-600' : cls.completion_rate >= 50 ? 'text-blue-600' : 'text-amber-600'">
              {{ cls.completion_rate }}%
            </div>
            <div class="text-xs text-slate-400">{{ cls.approved }}/{{ cls.total }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 各班级完成进度（无下钻时显示） -->
    <div v-if="!data.drill_data" class="dash-section">
      <div class="dash-section__header">各班级完成进度</div>
      <div v-if="!data.class_completion_stats?.length" class="px-4 py-8 text-center text-sm text-slate-400">
        暂无班级数据
      </div>
      <div v-else class="divide-y divide-slate-100">
        <div
          v-for="(cls, idx) in data.class_completion_stats"
          :key="`cls-${idx}`"
          class="flex items-center gap-3 px-4 py-3"
        >
          <div class="min-w-0 flex-1">
            <div class="text-sm font-medium text-slate-800">{{ cls.class_name }}</div>
            <div class="mt-1 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                class="h-2 rounded-full transition-all"
                :class="cls.completion_rate >= 80 ? 'bg-green-500' : cls.completion_rate >= 50 ? 'bg-blue-500' : 'bg-amber-500'"
                :style="{ width: `${Math.min(cls.completion_rate, 100)}%` }"
              />
            </div>
          </div>
          <div class="text-right flex-shrink-0">
            <div class="text-sm font-bold" :class="cls.completion_rate >= 80 ? 'text-green-600' : cls.completion_rate >= 50 ? 'text-blue-600' : 'text-amber-600'">
              {{ cls.completion_rate }}%
            </div>
            <div class="text-xs text-slate-400">{{ cls.approved }}/{{ cls.total }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 待处理申诉 -->
    <div class="dash-section">
      <div class="dash-section__header">待处理申诉</div>
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

    </template>

    <!-- ==================== Tab 2: 缺交名单 ==================== -->
    <template v-if="activeTab === 'missing'">
      <MissingSubmissionTab :role-level="ROLE_LEVEL_DIRECTOR" />
    </template>
  </div>
</template>

<script setup>
/**
 * @description 院系主任工作台组件。
 * 包含两个 Tab：概览（完成率/评审率、评阅进度、专业→班级下钻）、缺交名单。
 */
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import RingChart from '@/components/charts/RingChart.vue'
import MiniBarChart from '@/components/charts/MiniBarChart.vue'
import RadarChart from '@/components/charts/RadarChart.vue'
import MissingSubmissionTab from './MissingSubmissionTab.vue'
import { ROLE_LEVEL_DIRECTOR } from '@/constants/roles'

const props = defineProps({
  data: { type: Object, required: true },
})

const emit = defineEmits(['drill'])

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

const gp = computed(() => props.data.grading_progress ?? {
  total_assignments: 0, completed: 0, pending: 0,
  valid_final_scores: 0, arbitration_needed: 0,
})

const gradingPct = computed(() => {
  const total = gp.value.total_assignments
  return total ? Math.round((gp.value.completed / total) * 100) : 0
})

const majorStatsValid = computed(() => (props.data.major_stats ?? []).length >= 3)

/** @returns {Array} 专业雷达图维度 */
const majorRadarIndicators = computed(() =>
  (props.data.major_stats ?? []).map((m) => ({
    name: m.major_name,
    max: 100,
  }))
)

/** @returns {Array} 专业雷达图数据系列 */
const majorRadarSeries = computed(() => {
  const stats = props.data.major_stats ?? []
  if (!stats.length) return []
  return [
    {
      name: '完成率',
      values: stats.map((m) => m.completion_rate ?? 0),
      color: '#059669',
    },
  ]
})

/** @returns {Array} 专业柱状图数据 */
const majorBarItems = computed(() => {
  return (props.data.major_stats ?? []).map((m) => ({
    label: m.major_name,
    value: m.avg_score,
    color: m.avg_score >= 80 ? '#059669' : m.avg_score >= 60 ? '#3b82f6' : '#f59e0b',
  }))
})
/** @param {{ major_id: number }} major */
function drillIntoMajor(major) {
  if (major.major_id) {
    emit('drill', { major_id: major.major_id })
  }
}
</script>
