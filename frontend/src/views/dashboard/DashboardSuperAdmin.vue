<template>
  <div class="space-y-5">
    <!-- Tab 切换栏（滑块动画） -->
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
      <!-- 核心指标卡片 -->
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div class="stat-card">
          <div class="stat-icon bg-brand-100 text-brand-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>
          </div>
          <div>
            <div class="stat-value text-brand-600">{{ data.total_users ?? '—' }}</div>
            <div class="stat-label">系统总用户</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-green-100 text-green-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
          </div>
          <div>
            <div class="stat-value text-green-600">{{ data.completion_rate ?? '—' }}%</div>
            <div class="stat-label">全校完成率</div>
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
          <div class="stat-icon bg-amber-100 text-amber-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
          </div>
          <div>
            <div class="stat-value text-amber-600">{{ data.avg_score ?? '—' }}</div>
            <div class="stat-label">全校平均分</div>
          </div>
        </div>
      </div>

      <!-- 第二行指标 -->
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div class="stat-card">
          <div class="stat-icon bg-green-100 text-green-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
          </div>
          <div>
            <div class="stat-value text-green-600">{{ data.active_users ?? '—' }}</div>
            <div class="stat-label">激活用户</div>
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
          <div class="stat-icon bg-indigo-100 text-indigo-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
          </div>
          <div>
            <div class="stat-value text-indigo-600">{{ data.valid_final_scores ?? '—' }}</div>
            <div class="stat-label">有效成绩数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-slate-100 text-slate-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" /><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" /></svg>
          </div>
          <div>
            <div class="stat-value text-slate-700">{{ data.recent_login_users_30d ?? '—' }}</div>
            <div class="stat-label">近30天活跃</div>
          </div>
        </div>
      </div>

      <!-- 完成率 + 评审率 双环形图 -->
      <div class="grid gap-4 md:grid-cols-2">
        <div class="dash-section flex flex-col items-center justify-center py-6 px-4">
          <RingChart
            :percentage="data.completion_rate ?? 0"
            color="#059669"
            track-color="#d1fae5"
            :size="120"
            :stroke-width="14"
          />
          <p class="mt-3 text-sm font-medium text-slate-700">全校完成率</p>
          <p class="mt-0.5 text-xs text-slate-400">
            已通过 {{ data.total_approved ?? 0 }} / {{ data.total_submissions ?? 0 }}
          </p>
        </div>
        <div class="dash-section flex flex-col items-center justify-center py-6 px-4">
          <RingChart
            :percentage="data.review_rate ?? 0"
            color="#3b82f6"
            track-color="#dbeafe"
            :size="120"
            :stroke-width="14"
          />
          <p class="mt-3 text-sm font-medium text-slate-700">评审完成率</p>
          <p class="mt-0.5 text-xs text-slate-400">
            待审核 {{ data.pending_review_count ?? 0 }}
          </p>
        </div>
      </div>

      <!-- 用户激活率 + 测评周期状态 -->
      <div class="grid gap-4 md:grid-cols-2">
        <div class="dash-section">
          <div class="dash-section__header">用户激活率</div>
          <div class="flex items-center justify-center gap-6 px-4 py-5">
            <RingChart
              :percentage="activeUserPct"
              color="#059669"
              track-color="#d1fae5"
              :size="100"
              :stroke-width="12"
            />
            <div class="space-y-2 text-sm">
              <div class="flex items-center gap-2">
                <span class="h-2.5 w-2.5 rounded-full bg-green-500" />
                <span class="text-slate-600">激活 {{ data.active_users ?? 0 }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="h-2.5 w-2.5 rounded-full bg-slate-200" />
                <span class="text-slate-600">未激活 {{ (data.total_users ?? 0) - (data.active_users ?? 0) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="dash-section">
          <div class="dash-section__header">测评周期状态</div>
          <div class="grid grid-cols-3 gap-3 px-4 py-5">
            <div class="rounded-lg bg-green-50 p-3 text-center">
              <div class="text-xl font-bold text-green-600">{{ data.season_status_counts?.ongoing ?? 0 }}</div>
              <div class="mt-0.5 text-xs text-green-700">进行中</div>
            </div>
            <div class="rounded-lg bg-slate-50 p-3 text-center">
              <div class="text-xl font-bold text-slate-600">{{ data.season_status_counts?.draft ?? 0 }}</div>
              <div class="mt-0.5 text-xs text-slate-500">草稿</div>
            </div>
            <div class="rounded-lg bg-blue-50 p-3 text-center">
              <div class="text-xl font-bold text-blue-600">{{ data.season_status_counts?.closed ?? 0 }}</div>
              <div class="mt-0.5 text-xs text-blue-700">已结束</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近高级别操作日志 -->
      <div class="dash-section">
        <div class="dash-section__header">
          最近高级别操作记录（WARNING / CRITICAL）
        </div>
        <div v-if="!data.recent_logs?.length" class="px-4 py-8 text-center text-sm text-slate-400">
          暂无记录
        </div>
        <ul v-else class="divide-y divide-slate-100">
          <li
            v-for="log in data.recent_logs"
            :key="log.id"
            class="flex items-start justify-between gap-2 px-4 py-3"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span
                  class="rounded px-1.5 py-0.5 text-xs font-medium"
                  :class="log.level === 'CRITICAL' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'"
                >{{ log.level }}</span>
                <span class="truncate text-sm text-slate-800">{{ log.username_snapshot }}</span>
              </div>
              <div class="mt-0.5 text-xs text-slate-500">
                {{ log.module }} · {{ log.action }}
                <span v-if="log.target_repr"> → {{ log.target_repr }}</span>
              </div>
              <div v-if="log.is_abnormal" class="mt-0.5 text-xs text-red-500">⚠ 异常操作</div>
            </div>
            <span class="shrink-0 text-xs text-slate-400 whitespace-nowrap">{{ formatTime(log.created_at) }}</span>
          </li>
        </ul>
      </div>
    </template>

    <!-- ==================== Tab 2: 院系分析 ==================== -->
    <template v-if="activeTab === 'department'">
      <!-- 下钻面包屑 -->
      <div v-if="drillBreadcrumb.length > 1" class="app-breadcrumb">
        <template v-for="(crumb, idx) in drillBreadcrumb" :key="idx">
          <button
            v-if="idx < drillBreadcrumb.length - 1"
            type="button"
            class="text-brand-600 hover:underline"
            @click="navigateDrill(crumb)"
          >{{ crumb.label }}</button>
          <span v-else class="app-breadcrumb-current">{{ crumb.label }}</span>
          <span v-if="idx < drillBreadcrumb.length - 1" class="text-slate-300">/</span>
        </template>
      </div>

      <!-- 无下钻时：院系概览 -->
      <template v-if="!data.drill_type">
        <!-- 雷达图：各院系完成率对比 -->
        <div v-if="deptStatsValid" class="dash-section">
          <div class="dash-section__header">各院系完成率对比</div>
          <div class="p-4">
            <RadarChart
              :indicators="radarIndicators"
              :series-data="radarSeries"
              :height="300"
            />
          </div>
        </div>

        <!-- 柱状图：各院系平均分 -->
        <div v-if="deptStatsValid" class="dash-section">
          <div class="dash-section__header">各院系平均分对比</div>
          <div class="p-4">
            <BarChart
              :categories="deptBarCategories"
              :series-data="deptBarSeries"
              suffix="分"
              :height="260"
            />
          </div>
        </div>

        <!-- 院系卡片列表（可点击下钻） -->
        <div class="dash-section">
          <div class="dash-section__header">各院系统计详情</div>
          <div v-if="!data.department_stats?.length" class="px-4 py-8 text-center text-sm text-slate-400">
            暂无院系数据
          </div>
          <div v-else class="divide-y divide-slate-100">
            <button
              v-for="dept in data.department_stats"
              :key="dept.department_id"
              type="button"
              class="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-slate-50"
              @click="drillIntoDept(dept)"
            >
              <div class="min-w-0 flex-1">
                <div class="text-sm font-medium text-slate-800">{{ dept.department_name }}</div>
                <div class="mt-1 flex items-center gap-3 text-xs text-slate-500">
                  <span>提交 {{ dept.total_submissions }}</span>
                  <span>通过 {{ dept.approved }}</span>
                  <span v-if="dept.avg_score">均分 {{ dept.avg_score }}</span>
                </div>
                <div class="mt-1.5 h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    class="h-2 rounded-full transition-all"
                    :class="dept.completion_rate >= 80 ? 'bg-green-500' : dept.completion_rate >= 50 ? 'bg-blue-500' : 'bg-amber-500'"
                    :style="{ width: `${Math.min(dept.completion_rate, 100)}%` }"
                  />
                </div>
              </div>
              <div class="text-right flex-shrink-0">
                <div class="text-sm font-bold" :class="dept.completion_rate >= 80 ? 'text-green-600' : dept.completion_rate >= 50 ? 'text-blue-600' : 'text-amber-600'">
                  {{ dept.completion_rate }}%
                </div>
                <div class="mt-0.5 text-xs text-slate-400">完成率</div>
              </div>
              <svg class="h-4 w-4 flex-shrink-0 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
            </button>
          </div>
        </div>
      </template>

      <!-- 下钻后：专业/班级列表 -->
      <template v-if="data.drill_type === 'department'">
        <div class="dash-section">
          <div class="dash-section__header">各专业统计</div>
          <div v-if="!data.drill_data?.length" class="px-4 py-8 text-center text-sm text-slate-400">
            暂无数据
          </div>
          <div v-else class="divide-y divide-slate-100">
            <button
              v-for="item in data.drill_data"
              :key="item.major_id"
              type="button"
              class="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-slate-50"
              @click="drillIntoMajor(item)"
            >
              <div class="min-w-0 flex-1">
                <div class="text-sm font-medium text-slate-800">{{ item.major_name }}</div>
                <div class="mt-1 flex items-center gap-3 text-xs text-slate-500">
                  <span>提交 {{ item.total }}</span>
                  <span>通过 {{ item.approved }}</span>
                  <span v-if="item.avg_score">均分 {{ item.avg_score }}</span>
                </div>
                <div class="mt-1.5 h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    class="h-2 rounded-full transition-all"
                    :class="item.completion_rate >= 80 ? 'bg-green-500' : item.completion_rate >= 50 ? 'bg-blue-500' : 'bg-amber-500'"
                    :style="{ width: `${Math.min(item.completion_rate, 100)}%` }"
                  />
                </div>
              </div>
              <div class="text-right flex-shrink-0">
                <div class="text-sm font-bold" :class="item.completion_rate >= 80 ? 'text-green-600' : item.completion_rate >= 50 ? 'text-blue-600' : 'text-amber-600'">
                  {{ item.completion_rate }}%
                </div>
              </div>
              <svg class="h-4 w-4 flex-shrink-0 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
            </button>
          </div>
        </div>
      </template>

      <template v-if="data.drill_type === 'major'">
        <div class="dash-section">
          <div class="dash-section__header">各班级统计</div>
          <div v-if="!data.drill_data?.length" class="px-4 py-8 text-center text-sm text-slate-400">
            暂无数据
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div
              v-for="item in data.drill_data"
              :key="item.class_id"
              class="flex items-center gap-3 px-4 py-3"
            >
              <div class="min-w-0 flex-1">
                <div class="text-sm font-medium text-slate-800">{{ item.class_name }}</div>
                <div class="mt-1 flex items-center gap-3 text-xs text-slate-500">
                  <span>提交 {{ item.total }}</span>
                  <span>通过 {{ item.approved }}</span>
                  <span v-if="item.avg_score">均分 {{ item.avg_score }}</span>
                </div>
                <div class="mt-1.5 h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    class="h-2 rounded-full transition-all"
                    :class="item.completion_rate >= 80 ? 'bg-green-500' : item.completion_rate >= 50 ? 'bg-blue-500' : 'bg-amber-500'"
                    :style="{ width: `${Math.min(item.completion_rate, 100)}%` }"
                  />
                </div>
              </div>
              <div class="text-right flex-shrink-0">
                <div class="text-sm font-bold" :class="item.completion_rate >= 80 ? 'text-green-600' : item.completion_rate >= 50 ? 'text-blue-600' : 'text-amber-600'">
                  {{ item.completion_rate }}%
                </div>
                <div class="text-xs text-slate-400">{{ item.approved }}/{{ item.total }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- ==================== Tab 3: 评审进度 ==================== -->
    <template v-if="activeTab === 'review'">
      <!-- 全校评审仪表盘 -->
      <div class="grid gap-4 md:grid-cols-2">
        <div class="dash-section flex flex-col items-center justify-center py-6">
          <GaugeChart
            :value="data.completion_rate ?? 0"
            title="全校完成率"
            color="#059669"
            :height="200"
          />
        </div>
        <div class="dash-section flex flex-col items-center justify-center py-6">
          <GaugeChart
            :value="data.review_rate ?? 0"
            title="评审完成率"
            color="#3b82f6"
            :height="200"
          />
        </div>
      </div>

      <!-- 全校评审关键数据 -->
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div class="rounded-xl border border-slate-200 bg-white p-4 text-center">
          <div class="text-2xl font-bold text-blue-600">{{ data.total_submissions ?? 0 }}</div>
          <div class="mt-1 text-xs text-slate-500">总提交数</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4 text-center">
          <div class="text-2xl font-bold text-green-600">{{ data.total_approved ?? 0 }}</div>
          <div class="mt-1 text-xs text-slate-500">已通过</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4 text-center">
          <div class="text-2xl font-bold text-amber-600">{{ data.pending_review_count ?? 0 }}</div>
          <div class="mt-1 text-xs text-slate-500">待审核</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4 text-center">
          <div class="text-2xl font-bold text-red-500">{{ data.pending_appeal_count ?? 0 }}</div>
          <div class="mt-1 text-xs text-slate-500">待处理申诉</div>
        </div>
      </div>

      <!-- 各院系评审完成情况 -->
      <div class="dash-section">
        <div class="dash-section__header">各院系评审完成情况</div>
        <div v-if="!data.dept_review_stats?.length" class="px-4 py-8 text-center text-sm text-slate-400">
          暂无数据
        </div>
        <div v-else class="divide-y divide-slate-100">
          <div
            v-for="dept in data.dept_review_stats"
            :key="dept.department_id"
            class="flex items-center gap-3 px-4 py-3"
          >
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between text-sm mb-1">
                <span class="font-medium text-slate-800">{{ dept.department_name }}</span>
                <span class="text-slate-500">{{ dept.completed }} / {{ dept.total_assignments }}</span>
              </div>
              <div class="h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div
                  class="h-2.5 rounded-full bg-blue-500 transition-all"
                  :style="{ width: `${Math.min(dept.review_rate, 100)}%` }"
                />
              </div>
            </div>
            <div class="text-sm font-bold text-blue-600 flex-shrink-0 w-14 text-right">
              {{ dept.review_rate }}%
            </div>
          </div>
        </div>
      </div>

      <!-- 各院系完成率柱状图 -->
      <div v-if="deptStatsValid" class="dash-section">
        <div class="dash-section__header">各院系完成率柱状图</div>
        <div class="p-4">
          <BarChart
            :categories="deptBarCategories"
            :series-data="[{
              name: '完成率',
              data: (data.department_stats ?? []).map(d => d.completion_rate),
              color: '#059669',
            }]"
            suffix="%"
            :height="260"
          />
        </div>
      </div>
    </template>

    <!-- ==================== Tab 4: 缺交名单 ==================== -->
    <template v-if="activeTab === 'missing'">
      <MissingSubmissionTab :role-level="ROLE_LEVEL_SUPERADMIN" />
    </template>
  </div>
</template>

<script setup>
/**
 * @description 超级管理员工作台组件。
 * 包含四个 Tab 视图：概览、院系分析、评审进度、缺交名单。
 * 支持院系 → 专业 → 班级三级下钻。
 */
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import RingChart from '@/components/charts/RingChart.vue'
import RadarChart from '@/components/charts/RadarChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import GaugeChart from '@/components/charts/GaugeChart.vue'
import MissingSubmissionTab from './MissingSubmissionTab.vue'
import { formatTime } from '@/utils/format'
import { ROLE_LEVEL_SUPERADMIN } from '@/constants/roles'

const props = defineProps({
  data: { type: Object, required: true },
})

const emit = defineEmits(['drill'])

const tabs = [
  { key: 'overview', label: '概览' },
  { key: 'department', label: '院系分析' },
  { key: 'review', label: '评审进度' },
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

/** @returns {number} 用户激活百分比 */
const activeUserPct = computed(() => {
  const total = props.data.total_users ?? 0
  const active = props.data.active_users ?? 0
  return total ? Math.round((active / total) * 100) : 0
})

const deptStatsValid = computed(() => (props.data.department_stats ?? []).length > 0)

/** @returns {Array} 雷达图维度 */
const radarIndicators = computed(() =>
  (props.data.department_stats ?? []).map((d) => ({
    name: d.department_name,
    max: 100,
  }))
)

/** @returns {Array} 雷达图数据系列 */
const radarSeries = computed(() => {
  const stats = props.data.department_stats ?? []
  if (!stats.length) return []
  return [
    {
      name: '完成率',
      values: stats.map((d) => d.completion_rate),
      color: '#059669',
    },
  ]
})

/** @returns {Array<string>} 柱状图 X 轴标签 */
const deptBarCategories = computed(() =>
  (props.data.department_stats ?? []).map((d) => d.department_name)
)

/** @returns {Array} 柱状图平均分系列 */
const deptBarSeries = computed(() => [{
  name: '平均分',
  data: (props.data.department_stats ?? []).map((d) => d.avg_score ?? 0),
}])

// --- 下钻逻辑 ---

const drillStack = ref([])

const drillBreadcrumb = computed(() => {
  const crumbs = [{ label: '全校', params: {} }]
  for (const item of drillStack.value) {
    crumbs.push(item)
  }
  return crumbs
})

/** @param {{ department_id: number, department_name: string }} dept */
function drillIntoDept(dept) {
  drillStack.value = [
    { label: dept.department_name, params: { department_id: dept.department_id } },
  ]
  emit('drill', { department_id: dept.department_id })
}

/** @param {{ major_id: number, major_name: string }} major */
function drillIntoMajor(major) {
  const deptParam = drillStack.value[0]?.params ?? {}
  drillStack.value = [
    drillStack.value[0],
    { label: major.major_name, params: { ...deptParam, major_id: major.major_id } },
  ]
  emit('drill', { ...deptParam, major_id: major.major_id })
}

/** @param {{ label: string, params: Object }} crumb */
function navigateDrill(crumb) {
  if (!crumb.params || !Object.keys(crumb.params).length) {
    drillStack.value = []
    emit('drill', {})
  } else {
    const idx = drillStack.value.findIndex((s) => s.label === crumb.label)
    if (idx >= 0) drillStack.value = drillStack.value.slice(0, idx + 1)
    emit('drill', crumb.params)
  }
}

</script>
