<template>
  <div class="page-shell">
    <h2 class="app-page-title">我的操作记录</h2>
    <p class="mt-1 text-sm text-slate-500">
      仅显示当前账号的操作历史。如需查看其他账号的记录，请联系管理员通过后台查询。
    </p>

    <!-- 筛选栏 -->
    <div class="app-surface p-3 md:p-4">
      <div class="app-filter-wrap !lg:grid-cols-4">
        <label class="flex min-w-0 flex-col gap-1 text-xs text-slate-500">
          <span>等级</span>
          <select
            v-model="filter.level"
            class="app-select min-w-0"
          >
            <option value="">全部等级</option>
            <option value="INFO">一般</option>
            <option value="NOTICE">关键</option>
            <option value="WARNING">敏感</option>
            <option value="CRITICAL">高危</option>
          </select>
        </label>
        <label class="flex min-w-0 flex-col gap-1 text-xs text-slate-500">
          <span>模块</span>
          <select
            v-model="filter.module"
            class="app-select min-w-0"
          >
            <option value="">全部模块</option>
            <option value="auth">认证</option>
            <option value="users">用户管理</option>
            <option value="org">组织架构</option>
            <option value="eval">测评管理</option>
            <option value="submission">材料提交</option>
            <option value="scoring">评分</option>
            <option value="appeal">申诉</option>
            <option value="report">报表</option>
            <option value="system">系统</option>
          </select>
        </label>
        <label class="flex min-w-0 flex-col gap-1 text-xs text-slate-500">
          <span>开始日期</span>
          <input
            v-model="filter.dateFrom"
            type="date"
            class="app-input min-w-0 date-input-fix"
            title="开始日期"
          />
        </label>
        <label class="flex min-w-0 flex-col gap-1 text-xs text-slate-500">
          <span>结束日期</span>
          <input
            v-model="filter.dateTo"
            type="date"
            class="app-input min-w-0 date-input-fix"
            title="结束日期"
          />
        </label>
        <button
          type="button"
          class="app-btn app-btn-primary app-btn-sm"
          @click="onSearch"
        >
          查询
        </button>
        <button
          type="button"
          class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
          @click="onReset"
        >
          重置
        </button>
      </div>
    </div>

    <div class="app-surface mt-4 overflow-hidden relative">
      <div v-if="state.paginating" class="absolute inset-0 z-10 flex items-center justify-center bg-white/60">
        <span class="text-sm text-slate-400">加载中…</span>
      </div>
      <div v-if="state.initialLoading" class="p-8 text-center text-slate-500">加载中…</div>
      <div v-else-if="state.error" class="p-6 text-sm text-red-600">{{ state.error }}</div>
      <div v-else-if="state.logs.length === 0" class="p-8 text-center text-slate-400">暂无操作记录</div>
      <template v-else>

      <!-- 移动端：微信风格列表 -->
      <div class="mobile-log-list md:hidden">
        <router-link
          v-for="log in state.logs"
          :key="`m-${log.id}`"
          :to="{ name: 'MyOperationLogDetail', params: { id: log.id } }"
          class="mobile-log-item"
          :class="log.is_abnormal ? 'mobile-log-item--danger' : ''"
        >
          <div class="mobile-log-icon" :class="moduleIconClass(log.module)">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <template v-if="log.module === 'auth'"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0110 0v4" /></template>
              <template v-else-if="log.module === 'scoring'"><path d="M12 20V10" /><path d="M18 20V4" /><path d="M6 20v-4" /></template>
              <template v-else-if="log.module === 'submission'"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></template>
              <template v-else-if="log.module === 'appeal'"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" /></template>
              <template v-else><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" /></template>
            </svg>
          </div>
          <div class="mobile-log-content">
            <div class="mobile-log-top">
              <span class="mobile-log-title">{{ log.action_label }}</span>
              <span class="mobile-log-time">{{ relativeTime(log.created_at) }}</span>
            </div>
            <div class="mobile-log-sub">{{ log.module_label }} · {{ simpleTarget(log) }}</div>
          </div>
          <svg class="mobile-log-arrow" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
        </router-link>
      </div>

      <!-- 桌面端：表格 -->
      <div class="hidden md:block">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-slate-200 bg-slate-50 text-left">
            <th class="px-4 py-3 font-medium text-slate-600">时间</th>
            <th class="px-4 py-3 font-medium text-slate-600">等级</th>
            <th class="px-4 py-3 font-medium text-slate-600">模块</th>
            <th class="px-4 py-3 font-medium text-slate-600">操作</th>
            <th class="px-4 py-3 font-medium text-slate-600">目标</th>
            <th class="px-4 py-3 font-medium text-slate-600">详情</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="log in state.logs"
            :key="log.id"
            class="border-b border-slate-100 last:border-0 hover:bg-slate-50"
            :class="log.is_abnormal ? 'bg-red-50' : ''"
          >
            <td class="px-4 py-3 text-slate-600 whitespace-nowrap">{{ formatTime(log.created_at) }}</td>
            <td class="px-4 py-3">
              <span class="rounded px-1.5 py-0.5 text-xs font-medium" :class="levelClass(log.level)">
                {{ log.level_label }}
              </span>
            </td>
            <td class="px-4 py-3 text-slate-600">{{ log.module_label }}</td>
            <td class="px-4 py-3 text-slate-700">{{ log.action_label }}</td>
            <td class="max-w-xs px-4 py-3 relative group">
              <span class="block truncate text-slate-600 text-xs cursor-default">
                {{ targetSummary(log) }}
              </span>
              <div
                v-if="log.target_repr || log.extra?.changed"
                class="pointer-events-none absolute left-0 top-full z-30 mt-0.5 hidden w-72 rounded border border-slate-200 bg-white p-2.5 text-xs shadow-lg group-hover:block"
              >
                <div v-if="log.target_repr" class="font-medium text-slate-700 break-all mb-1">
                  {{ log.target_repr }}
                </div>
                <template v-if="log.extra?.changed && Object.keys(log.extra.changed).length">
                  <div class="text-slate-500 mb-0.5">变更字段：</div>
                  <div
                    v-for="(v, k) in log.extra.changed"
                    :key="k"
                    class="text-slate-600 leading-relaxed"
                  >
                    <span class="font-medium">{{ k }}</span>：{{ v.old || '（空）' }} → {{ v.new || '（空）' }}
                  </div>
                </template>
              </div>
            </td>
            <td class="px-4 py-3">
              <button
                type="button"
                class="text-xs text-brand-600 underline hover:text-brand-800"
                @click="openDetail(log.id)"
              >
                详情
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      </template>

      <!-- 分页 -->
      <div v-if="state.totalCount > pageSize" class="flex flex-col gap-2 border-t border-slate-200 px-4 py-3 md:flex-row md:items-center md:justify-between">
        <span class="text-sm text-slate-500">共 {{ state.totalCount }} 条</span>
        <div class="flex gap-2">
          <button
            type="button"
            :disabled="page <= 1"
            class="rounded border border-slate-300 px-3 py-1 text-sm disabled:opacity-40"
            @click="changePage(page - 1)"
          >
            上一页
          </button>
          <span class="self-center text-sm text-slate-600">{{ page }} / {{ totalPages }}</span>
          <button
            type="button"
            :disabled="page >= totalPages"
            class="rounded border border-slate-300 px-3 py-1 text-sm disabled:opacity-40"
            @click="changePage(page + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 桌面端详情弹窗 -->
    <div
      v-if="detail.show"
      class="fixed inset-0 z-30 flex items-center justify-center bg-black/30"
      @click.self="detail.show = false"
    >
      <div class="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-lg border border-slate-200 bg-white p-4 shadow-xl md:p-6">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-semibold text-slate-800">操作记录详情</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600" @click="detail.show = false">✕</button>
        </div>
        <div v-if="detail.loading" class="mt-4 text-center text-slate-500">加载中…</div>
        <div v-else-if="detail.data" class="mt-4 space-y-3 text-sm">
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <span class="text-slate-500">时间：</span>
              <span class="text-slate-800">{{ formatTime(detail.data.created_at) }}</span>
            </div>
            <div>
              <span class="text-slate-500">等级：</span>
              <span class="font-medium" :class="levelTextClass(detail.data.level)">{{ detail.data.level_label }}</span>
            </div>
            <div>
              <span class="text-slate-500">模块：</span>
              <span class="text-slate-800">{{ detail.data.module_label }}</span>
            </div>
            <div>
              <span class="text-slate-500">操作：</span>
              <span class="text-slate-800">{{ detail.data.action_label }}</span>
            </div>
            <div class="col-span-2">
              <span class="text-slate-500">操作目标：</span>
              <span class="text-slate-800">{{ detail.data.target_repr || '—' }}</span>
            </div>
            <div>
              <span class="text-slate-500">浏览器标识：</span>
              <span class="break-all text-slate-600 text-xs">{{ detail.data.user_agent || '—' }}</span>
            </div>
          </div>
          <div v-if="detail.data.reason">
            <span class="text-slate-500">操作理由：</span>
            <span class="text-slate-800">{{ detail.data.reason }}</span>
          </div>
          <div v-if="detail.data.extra_pretty">
            <div class="text-slate-500 mb-1">附加信息：</div>
            <pre class="rounded bg-slate-100 p-3 text-xs text-slate-700 overflow-x-auto">{{ detail.data.extra_pretty }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * @description 我的操作记录：当前登录用户查看自己的操作日志，支持等级/模块/日期筛选。
 * 移动端采用微信风格列表 + 路由详情页，桌面端保留表格 + 弹窗。
 */
import { reactive, ref, computed, onMounted } from 'vue'
import { getMyLogs, getMyLogDetail } from '@/api/admin'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatTime } from '@/utils/format'

const pageSize = 20
const page = ref(1)

const filter = reactive({
  level: '',
  module: '',
  dateFrom: '',
  dateTo: '',
})

const state = reactive({
  initialLoading: false,
  paginating: false,
  error: '',
  logs: [],
  totalCount: 0,
})

const detail = reactive({
  show: false,
  loading: false,
  data: null,
})

const totalPages = computed(() => Math.max(1, Math.ceil(state.totalCount / pageSize)))

/** @returns {Object} 查询参数 */
function buildParams() {
  const params = { page: page.value }
  if (filter.level) params.level = filter.level
  if (filter.module) params.module = filter.module
  if (filter.dateFrom) params.date_from = filter.dateFrom
  if (filter.dateTo) params.date_to = filter.dateTo
  return params
}

/**
 * @param {boolean} [soft=false] - 翻页时使用软加载，保留现有内容
 */
async function loadLogs(soft = false) {
  if (soft) {
    state.paginating = true
  } else {
    state.initialLoading = true
  }
  state.error = ''
  try {
    const data = await getMyLogs(buildParams())
    if (Array.isArray(data)) {
      state.logs = data
      state.totalCount = data.length
    } else {
      state.logs = data.results ?? []
      state.totalCount = data.count ?? state.logs.length
    }
  } catch (e) {
    state.error = e.response?.data?.detail ?? '加载失败，请重试'
    state.logs = []
  } finally {
    state.initialLoading = false
    state.paginating = false
  }
}

function onSearch() {
  page.value = 1
  loadLogs()
}

function onReset() {
  filter.level = ''
  filter.module = ''
  filter.dateFrom = ''
  filter.dateTo = ''
  page.value = 1
  loadLogs()
}

function changePage(p) {
  page.value = p
  loadLogs(true)
}

/** 桌面端弹窗详情 */
async function openDetail(id) {
  detail.show = true
  detail.loading = true
  detail.data = null
  try {
    detail.data = await getMyLogDetail(id)
  } catch {
    detail.show = false
  } finally {
    detail.loading = false
  }
}

/**
 * @param {string} iso - ISO 时间字符串
 * @returns {string} 相对时间（刚刚/N分钟前/N小时前/昨天/日期）
 */
function relativeTime(iso) {
  if (!iso) return '—'
  const now = Date.now()
  const ts = new Date(iso).getTime()
  const diff = Math.floor((now - ts) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 172800) return '昨天'
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

/**
 * @param {string} mod - 模块名
 * @returns {string} 图标圆的 CSS class
 */
function moduleIconClass(mod) {
  const map = {
    auth: 'bg-rose-100 text-rose-600',
    users: 'bg-blue-100 text-blue-600',
    org: 'bg-purple-100 text-purple-600',
    eval: 'bg-indigo-100 text-indigo-600',
    submission: 'bg-green-100 text-green-600',
    scoring: 'bg-amber-100 text-amber-600',
    appeal: 'bg-orange-100 text-orange-600',
    report: 'bg-cyan-100 text-cyan-600',
    system: 'bg-slate-100 text-slate-600',
  }
  return map[mod] ?? 'bg-slate-100 text-slate-600'
}

/**
 * @param {Object} log
 * @returns {string} 简短目标摘要（移动端用）
 */
function simpleTarget(log) {
  return log.target_repr || '—'
}

function levelClass(level) {
  const map = {
    INFO: 'bg-slate-100 text-slate-600',
    NOTICE: 'bg-blue-100 text-blue-700',
    WARNING: 'bg-amber-100 text-amber-700',
    CRITICAL: 'bg-red-100 text-red-700',
  }
  return map[level] ?? 'bg-slate-100 text-slate-600'
}

function targetSummary(log) {
  const repr = log.target_repr || (log.target_type ? `${log.target_type}#${log.target_id}` : '—')
  const changed = log.extra?.changed
  if (changed && Object.keys(changed).length) {
    return `${repr}（改: ${Object.keys(changed).join('、')}）`
  }
  return repr
}

function levelTextClass(level) {
  const map = {
    INFO: 'text-slate-600',
    NOTICE: 'text-blue-700',
    WARNING: 'text-amber-700',
    CRITICAL: 'text-red-700',
  }
  return map[level] ?? 'text-slate-600'
}

useRealtimeRefresh('audit_log', loadLogs)

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
/**
 * @description 修复 iOS Safari 日期输入控件在小屏下超出容器的问题。
 */
.date-input-fix {
  box-sizing: border-box !important;
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  inline-size: 100% !important;
  min-inline-size: 0 !important;
  max-inline-size: 100% !important;
  display: block !important;
  -webkit-appearance: none;
  appearance: none;
  overflow: hidden;
  height: 44px !important;
  padding: 0 12px !important;
  line-height: 44px !important;
  font-size: 14px;
  color: #334155;
  background-color: rgba(255, 255, 255, 0.92);
}

.date-input-fix::-webkit-date-and-time-value {
  display: inline-block;
  min-height: 44px;
  line-height: 44px;
  text-align: left;
}

.date-input-fix:invalid::-webkit-datetime-edit {
  color: #94a3b8;
}

.date-input-fix::-webkit-calendar-picker-indicator {
  margin: 0;
  padding: 0;
}

/* 移动端微信风格日志列表 */
.mobile-log-list {
  padding: 4px 0;
}

.mobile-log-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  text-decoration: none;
  transition: background-color 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.mobile-log-item:active {
  background-color: rgba(0, 0, 0, 0.03);
}

.mobile-log-item--danger {
  background-color: rgba(254, 202, 202, 0.15);
}

.mobile-log-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-log-content {
  flex: 1;
  min-width: 0;
}

.mobile-log-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.mobile-log-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-log-time {
  flex-shrink: 0;
  font-size: 11px;
  color: #94a3b8;
}

.mobile-log-sub {
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-log-arrow {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  color: #cbd5e1;
}
</style>
