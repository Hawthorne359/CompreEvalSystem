<template>
  <div class="space-y-4">
    <!-- 概要卡片 -->
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="stat-card">
        <div class="stat-icon bg-slate-100 text-slate-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>
        </div>
        <div>
          <div class="stat-value text-slate-700">{{ summary.total_scope_students ?? 0 }}</div>
          <div class="stat-label">范围学生数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-blue-100 text-blue-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>
        </div>
        <div>
          <div class="stat-value text-blue-600">{{ summary.ongoing_project_count ?? 0 }}</div>
          <div class="stat-label">进行中项目</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-red-100 text-red-500">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="12" y1="18" x2="12" y2="12" /></svg>
        </div>
        <div>
          <div class="stat-value text-red-500">{{ summary.unfilled_count ?? 0 }}</div>
          <div class="stat-label">未填写</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-amber-100 text-amber-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
        </div>
        <div>
          <div class="stat-value text-amber-600">{{ summary.unsubmitted_count ?? 0 }}</div>
          <div class="stat-label">未提交</div>
        </div>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="dash-section">
      <div class="px-4 py-3">
        <button
          type="button"
          class="flex items-center gap-1.5 text-sm text-slate-600 md:hidden"
          @click="filterExpanded = !filterExpanded"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" /></svg>
          {{ filterExpanded ? '收起筛选' : '展开筛选' }}
        </button>

        <div :class="['gap-3', filterExpanded ? 'grid' : 'hidden md:grid', 'mt-3 md:mt-0']"
             :style="filterGridStyle">
          <!-- 院系（仅超管） -->
          <label v-if="showDepartmentFilter" class="flex flex-col gap-1 text-sm text-slate-600">
            <span>院系</span>
            <select v-model="filterDept" class="app-input" @change="onDeptChange">
              <option value="">全部院系</option>
              <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </label>

          <!-- 专业（超管+院系主任） -->
          <label v-if="showMajorFilter" class="flex flex-col gap-1 text-sm text-slate-600">
            <span>专业</span>
            <select v-model="filterMajor" class="app-input" @change="onMajorChange">
              <option value="">全部专业</option>
              <option v-for="m in majors" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </label>

          <!-- 班级 -->
          <label class="flex flex-col gap-1 text-sm text-slate-600">
            <span>班级</span>
            <select v-model="filterClass" class="app-input">
              <option value="">全部班级</option>
              <option v-for="c in classes" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </label>

          <!-- 关键字 -->
          <label class="flex flex-col gap-1 text-sm text-slate-600">
            <span>关键字</span>
            <input v-model="filterSearch" type="text" placeholder="姓名 / 学号" class="app-input" @keydown.enter="doSearch" />
          </label>

          <button
            type="button"
            class="inline-flex h-10 w-auto min-w-20 self-end items-center justify-center rounded bg-brand-600 px-4 text-sm text-white hover:bg-brand-700 disabled:opacity-50"
            :disabled="loading"
            @click="doSearch"
          >
            查询
          </button>
        </div>
      </div>
    </div>

    <!-- 子Tab：未填写 / 未提交 -->
    <div class="flex items-center gap-2">
      <button
        type="button"
        class="rounded-full px-4 py-1.5 text-sm font-medium transition-colors"
        :class="activeType === 'unfilled' ? 'bg-slate-800 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        @click="switchType('unfilled')"
      >
        未填写
        <span v-if="summary.unfilled_count != null" class="ml-1 text-xs opacity-75">({{ summary.unfilled_count }})</span>
      </button>
      <button
        type="button"
        class="rounded-full px-4 py-1.5 text-sm font-medium transition-colors"
        :class="activeType === 'unsubmitted' ? 'bg-slate-800 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        @click="switchType('unsubmitted')"
      >
        未提交
        <span v-if="summary.unsubmitted_count != null" class="ml-1 text-xs opacity-75">({{ summary.unsubmitted_count }})</span>
      </button>
    </div>

    <!-- 列表 -->
    <div class="dash-section relative">
      <div v-if="paginating" class="absolute inset-0 z-10 flex items-center justify-center bg-white/60 rounded-xl">
        <span class="text-sm text-slate-400">加载中...</span>
      </div>
      <div v-if="initialLoading" class="px-4 py-12 text-center text-sm text-slate-400">加载中...</div>
      <div v-else-if="errorMsg" class="px-4 py-8 text-center text-sm text-red-500">{{ errorMsg }}</div>
      <div v-else-if="!items.length" class="px-4 py-12 text-center text-sm text-slate-400">当前无名单数据</div>

      <!-- PC 表格 -->
      <div v-else class="hidden md:block overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-100 text-left text-xs text-slate-500">
              <th class="px-4 py-2.5 font-medium">学号</th>
              <th class="px-4 py-2.5 font-medium">姓名</th>
              <th class="px-4 py-2.5 font-medium">班级</th>
              <th class="px-4 py-2.5 font-medium">专业</th>
              <th class="px-4 py-2.5 font-medium">院系</th>
              <th class="px-4 py-2.5 font-medium">项目</th>
              <th class="px-4 py-2.5 font-medium">{{ activeType === 'unsubmitted' ? '最后保存' : '截止时间' }}</th>
              <th v-if="activeType === 'unsubmitted'" class="px-4 py-2.5 font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-50">
            <tr v-for="(item, idx) in items" :key="`${activeType}-${idx}`" class="hover:bg-slate-50/50">
              <td class="px-4 py-2.5 text-slate-700">{{ item.student_no || '—' }}</td>
              <td class="px-4 py-2.5 font-medium text-slate-800">{{ item.student_name }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ item.class_name }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ item.major_name }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ item.department_name }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ item.project_name }}</td>
              <td class="px-4 py-2.5 text-slate-400 text-xs whitespace-nowrap">{{ formatTime(activeType === 'unsubmitted' ? item.updated_at : item.end_time) }}</td>
              <td v-if="activeType === 'unsubmitted'" class="px-4 py-2.5">
                <router-link
                  v-if="item.submission_id"
                  :to="{ name: 'ReviewDetail', params: { id: item.submission_id } }"
                  class="rounded bg-brand-50 px-2 py-1 text-xs text-brand-700 hover:bg-brand-100"
                >查看</router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 移动端卡片 -->
      <div v-if="items.length" class="md:hidden divide-y divide-slate-100">
        <div v-for="(item, idx) in items" :key="`m-${activeType}-${idx}`" class="px-4 py-3">
          <div class="flex items-start justify-between">
            <div>
              <div class="text-sm font-medium text-slate-800">{{ item.student_name }}</div>
              <div class="mt-0.5 text-xs text-slate-500">{{ item.student_no || '—' }}</div>
            </div>
            <router-link
              v-if="activeType === 'unsubmitted' && item.submission_id"
              :to="{ name: 'ReviewDetail', params: { id: item.submission_id } }"
              class="rounded bg-brand-50 px-2 py-1 text-xs text-brand-700 hover:bg-brand-100"
            >查看</router-link>
          </div>
          <div class="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-slate-500">
            <span>{{ item.class_name }}</span>
            <span>{{ item.major_name }}</span>
            <span>{{ item.department_name }}</span>
          </div>
          <div class="mt-1 text-xs text-slate-400">
            {{ item.project_name }}
            <span v-if="activeType === 'unsubmitted' && item.updated_at"> · 保存于 {{ formatTime(item.updated_at) }}</span>
            <span v-else-if="item.end_time"> · 截止 {{ formatTime(item.end_time) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-between px-1">
      <span class="text-xs text-slate-400">共 {{ total }} 条，第 {{ page }} / {{ totalPages }} 页</span>
      <div class="flex items-center gap-1">
        <button
          type="button"
          class="rounded border border-slate-200 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-40"
          :disabled="page <= 1 || loading"
          @click="goPage(page - 1)"
        >上一页</button>
        <template v-if="totalPages <= 7">
          <button
            v-for="p in totalPages"
            :key="p"
            type="button"
            class="rounded px-2.5 py-1 text-xs"
            :class="p === page ? 'bg-brand-600 text-white' : 'border border-slate-200 text-slate-600 hover:bg-slate-50'"
            :disabled="loading"
            @click="goPage(p)"
          >{{ p }}</button>
        </template>
        <template v-else>
          <button
            v-for="p in paginationRange"
            :key="p"
            type="button"
            class="rounded px-2.5 py-1 text-xs"
            :class="p === page ? 'bg-brand-600 text-white' : p === '...' ? 'text-slate-400 cursor-default' : 'border border-slate-200 text-slate-600 hover:bg-slate-50'"
            :disabled="p === '...' || loading"
            @click="p !== '...' && goPage(p)"
          >{{ p }}</button>
        </template>
        <button
          type="button"
          class="rounded border border-slate-200 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-40"
          :disabled="page >= totalPages || loading"
          @click="goPage(page + 1)"
        >下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * @description 缺交名单独立Tab组件。
 * 支持按角色权限筛选院系/专业/班级、模糊搜索、分页。
 * PC端显示表格，移动端显示卡片列表。
 */
import { ref, computed, onMounted, watch } from 'vue'
import { getMissingSubmissionList } from '@/api/dashboard'
import { formatTime } from '@/utils/format'
import { ROLE_LEVEL_COUNSELOR, ROLE_LEVEL_DIRECTOR, ROLE_LEVEL_SUPERADMIN } from '@/constants/roles'
import api from '@/api/axios'

const props = defineProps({
  /** @type {number} */
  roleLevel: { type: Number, required: true },
  /** @type {number[]} */
  responsibleClassIds: { type: Array, default: () => [] },
})

const initialLoading = ref(true)
const paginating = ref(false)
const errorMsg = ref('')
const activeType = ref('unfilled')
const filterExpanded = ref(false)

const filterDept = ref('')
const filterMajor = ref('')
const filterClass = ref('')
const filterSearch = ref('')

const departments = ref([])
const majors = ref([])
const classes = ref([])

const summary = ref({})
const items = ref([])
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const pageSize = 20

const showDepartmentFilter = computed(() => props.roleLevel >= ROLE_LEVEL_SUPERADMIN)
const showMajorFilter = computed(() => props.roleLevel >= ROLE_LEVEL_DIRECTOR)

const filterGridStyle = computed(() => {
  let cols = 2
  if (showDepartmentFilter.value) cols += 1
  if (showMajorFilter.value) cols += 1
  return { gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }
})

/** @returns {Array<number|string>} */
const paginationRange = computed(() => {
  const tp = totalPages.value
  const cp = page.value
  const range = []
  range.push(1)
  if (cp > 3) range.push('...')
  for (let i = Math.max(2, cp - 1); i <= Math.min(tp - 1, cp + 1); i++) {
    range.push(i)
  }
  if (cp < tp - 2) range.push('...')
  if (tp > 1) range.push(tp)
  return range
})

async function loadDepartments() {
  try {
    const res = await api.get('/departments/', { params: { tree: 1 } })
    departments.value = Array.isArray(res.data) ? res.data : (res.data?.results ?? [])
  } catch { departments.value = [] }
}

async function loadMajors() {
  try {
    const params = {}
    if (filterDept.value) params.department = filterDept.value
    const res = await api.get('/majors/', { params })
    majors.value = Array.isArray(res.data) ? res.data : (res.data?.results ?? [])
  } catch { majors.value = [] }
}

async function loadClasses() {
  try {
    const params = {}
    if (filterDept.value) params.department = filterDept.value
    if (filterMajor.value) params.major = filterMajor.value
    if (props.roleLevel < ROLE_LEVEL_DIRECTOR && props.responsibleClassIds.length) {
      params.ids = props.responsibleClassIds.join(',')
    }
    const res = await api.get('/classes/', { params })
    classes.value = Array.isArray(res.data) ? res.data : (res.data?.results ?? [])
  } catch { classes.value = [] }
}

function onDeptChange() {
  filterMajor.value = ''
  filterClass.value = ''
  loadMajors()
  loadClasses()
}

function onMajorChange() {
  filterClass.value = ''
  loadClasses()
}

/** @param {string} type */
function switchType(type) {
  activeType.value = type
  page.value = 1
  fetchData()
}

function doSearch() {
  page.value = 1
  fetchData()
}

/** @param {number} p */
function goPage(p) {
  page.value = p
  fetchData(true)
}

/**
 * @param {boolean} [soft=false] - 翻页时使用软加载，保留现有内容不跳转
 */
async function fetchData(soft = false) {
  if (soft) {
    paginating.value = true
  } else {
    initialLoading.value = true
  }
  errorMsg.value = ''
  try {
    const params = {
      type: activeType.value,
      page: page.value,
      page_size: pageSize,
    }
    if (filterDept.value) params.department = filterDept.value
    if (filterMajor.value) params.major = filterMajor.value
    if (filterClass.value) params.class_obj = filterClass.value
    if (filterSearch.value.trim()) params.search = filterSearch.value.trim()

    const data = await getMissingSubmissionList(params)
    summary.value = data.summary ?? {}
    items.value = data.items ?? []
    page.value = data.page ?? 1
    total.value = data.total ?? 0
    totalPages.value = data.total_pages ?? 1
  } catch (e) {
    errorMsg.value = e.response?.data?.detail ?? '加载失败'
    items.value = []
  } finally {
    initialLoading.value = false
    paginating.value = false
  }
}

onMounted(async () => {
  const tasks = [fetchData()]
  if (showDepartmentFilter.value) tasks.push(loadDepartments())
  if (showMajorFilter.value) tasks.push(loadMajors())
  tasks.push(loadClasses())
  await Promise.all(tasks)
})

watch(() => props.responsibleClassIds, () => {
  if (props.roleLevel < ROLE_LEVEL_DIRECTOR) loadClasses()
})
</script>
