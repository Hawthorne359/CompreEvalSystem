<template>
  <div class="page-shell">
    <!-- 桌面端：面包屑导航 -->
    <div class="hidden md:block">
      <div class="app-breadcrumb mb-4">
        <router-link :to="{ name: 'MyOperationLog' }" class="hover:text-brand-600">操作记录</router-link>
        <span>/</span>
        <span class="app-breadcrumb-current">记录详情</span>
      </div>
    </div>

    <!-- 移动端：顶部返回栏 -->
    <div class="flex items-center gap-3 md:hidden mb-4">
      <button
        type="button"
        class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/60 text-slate-600 active:scale-95 transition-transform"
        @click="goBack"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
      </button>
      <h2 class="text-lg font-semibold text-slate-800">操作详情</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      <span class="ml-3 text-sm text-slate-500">加载中…</span>
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="rounded-xl border border-red-200 bg-red-50 px-5 py-4">
      <p class="text-sm text-red-700">{{ error }}</p>
      <button type="button" class="mt-2 text-xs text-red-600 underline" @click="load">重试</button>
    </div>

    <!-- 详情内容 -->
    <template v-else-if="logData">
      <!-- 概览卡片 -->
      <div class="glass-card p-4 md:app-surface-strong md:p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl" :class="moduleIconClass(logData.module)">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <template v-if="logData.module === 'auth'"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0110 0v4" /></template>
              <template v-else-if="logData.module === 'scoring'"><path d="M12 20V10" /><path d="M18 20V4" /><path d="M6 20v-4" /></template>
              <template v-else-if="logData.module === 'submission'"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></template>
              <template v-else><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" /></template>
            </svg>
          </div>
          <div>
            <h3 class="text-base font-semibold text-slate-800">{{ logData.action_label }}</h3>
            <p class="mt-0.5 text-xs text-slate-400">{{ formatTime(logData.created_at) }}</p>
          </div>
        </div>

        <div class="space-y-3">
          <div class="detail-row">
            <span class="detail-label">操作等级</span>
            <span class="rounded px-2 py-0.5 text-xs font-medium" :class="levelClass(logData.level)">
              {{ logData.level_label }}
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">所属模块</span>
            <span class="detail-value">{{ logData.module_label }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">操作目标</span>
            <span class="detail-value">{{ logData.target_repr || '—' }}</span>
          </div>
          <div v-if="logData.reason" class="detail-row">
            <span class="detail-label">操作理由</span>
            <span class="detail-value">{{ logData.reason }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">浏览器</span>
            <span class="detail-value text-xs break-all">{{ logData.user_agent || '—' }}</span>
          </div>
        </div>
      </div>

      <!-- 附加信息 -->
      <div v-if="logData.extra_pretty" class="glass-card p-4 md:app-surface-strong md:p-6 mt-4">
        <h4 class="text-sm font-semibold text-slate-700 mb-2">附加信息</h4>
        <pre class="rounded-lg bg-slate-50 p-3 text-xs text-slate-700 overflow-x-auto leading-relaxed">{{ logData.extra_pretty }}</pre>
      </div>

      <!-- 变更详情 -->
      <div v-if="logData.extra?.changed && Object.keys(logData.extra.changed).length" class="glass-card p-4 md:app-surface-strong md:p-6 mt-4">
        <h4 class="text-sm font-semibold text-slate-700 mb-3">变更记录</h4>
        <div class="space-y-2">
          <div
            v-for="(v, k) in logData.extra.changed"
            :key="k"
            class="rounded-lg bg-slate-50 p-3"
          >
            <div class="text-xs font-medium text-slate-600 mb-1">{{ k }}</div>
            <div class="flex items-center gap-2 text-xs">
              <span class="rounded bg-red-50 px-1.5 py-0.5 text-red-600 line-through">{{ v.old || '（空）' }}</span>
              <svg class="h-3 w-3 text-slate-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6" /></svg>
              <span class="rounded bg-green-50 px-1.5 py-0.5 text-green-600">{{ v.new || '（空）' }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
/**
 * @description 操作日志详情页。手机端从列表页跳转进入，桌面端也可直接访问。
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { getMyLogDetail } from '@/api/admin'
import { formatTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const logData = ref(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    logData.value = await getMyLogDetail(route.params.id)
  } catch (e) {
    error.value = e.response?.data?.detail ?? '加载失败'
  } finally {
    loading.value = false
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push({ name: 'MyOperationLog' })
  }
}

/**
 * @param {string} mod
 * @returns {string}
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

function levelClass(level) {
  const map = {
    INFO: 'bg-slate-100 text-slate-600',
    NOTICE: 'bg-blue-100 text-blue-700',
    WARNING: 'bg-amber-100 text-amber-700',
    CRITICAL: 'bg-red-100 text-red-700',
  }
  return map[level] ?? 'bg-slate-100 text-slate-600'
}

onMounted(load)

useRealtimeRefresh('audit_log', load, {
  filter: (data) => !data.id || data.id === Number(route.params.id),
})
</script>

<style scoped>
.detail-row {
  @apply flex items-start justify-between gap-4 py-1;
}

.detail-label {
  @apply flex-shrink-0 text-sm text-slate-500;
  min-width: 70px;
}

.detail-value {
  @apply text-sm text-slate-800 text-right;
}
</style>
