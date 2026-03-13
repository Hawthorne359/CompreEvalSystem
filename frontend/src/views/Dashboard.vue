<template>
  <div class="mx-auto max-w-6xl">
    <!-- 页面标题 -->
    <div class="mb-5 flex items-center justify-between">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">工作台</h2>
        <p class="mt-0.5 text-sm text-slate-500">
          {{ greeting }}，{{ displayName }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
          {{ user?.current_role?.name || '未选择角色' }}
        </span>
        <button
          type="button"
          class="rounded-lg border border-slate-200 p-1.5 text-slate-400 hover:text-slate-600"
          title="刷新工作台"
          @click="refresh"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-20"
    >
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      <span class="ml-3 text-sm text-slate-500">加载工作台数据…</span>
    </div>

    <!-- 加载失败 -->
    <div
      v-else-if="error"
      class="rounded-xl border border-red-200 bg-red-50 px-5 py-4"
    >
      <p class="text-sm text-red-700">{{ error }}</p>
      <button
        type="button"
        class="mt-2 text-xs text-red-600 underline"
        @click="refresh"
      >重试</button>
    </div>

    <!-- 角色工作台（按 level 渲染） -->
    <template v-else-if="dashData">
      <DashboardStudent v-if="currentLevel === ROLE_LEVEL_STUDENT" :data="dashData" />
      <DashboardAssistant v-else-if="currentLevel === ROLE_LEVEL_ASSISTANT" :data="dashData" />
      <DashboardCounselor v-else-if="currentLevel === ROLE_LEVEL_COUNSELOR" :data="dashData" @refresh="loadDashboard({}, true)" />
      <DashboardDirector v-else-if="currentLevel === ROLE_LEVEL_DIRECTOR" :data="dashData" @drill="handleDrill" />
      <DashboardSuperAdmin v-else-if="currentLevel >= ROLE_LEVEL_SUPERADMIN" :data="dashData" @drill="handleDrill" />
      <div v-else class="rounded-xl border border-slate-200 bg-white px-6 py-10 text-center text-slate-500">
        暂无适配当前角色的工作台，请从导航栏选择功能。
      </div>
    </template>
  </div>
</template>

<script setup>
/**
 * @description 工作台主页：按当前角色 level 动态渲染对应仪表盘组件。
 * 支持子组件通过 drill 事件传递下钻参数重新加载数据。
 */
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getDashboard } from '@/api/dashboard'
import DashboardStudent from './dashboard/DashboardStudent.vue'
import DashboardAssistant from './dashboard/DashboardAssistant.vue'
import DashboardCounselor from './dashboard/DashboardCounselor.vue'
import DashboardDirector from './dashboard/DashboardDirector.vue'
import DashboardSuperAdmin from './dashboard/DashboardSuperAdmin.vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import {
  ROLE_LEVEL_STUDENT,
  ROLE_LEVEL_ASSISTANT,
  ROLE_LEVEL_COUNSELOR,
  ROLE_LEVEL_DIRECTOR,
  ROLE_LEVEL_SUPERADMIN,
} from '@/constants/roles'

const auth = useAuthStore()
const user = computed(() => auth.user)

const currentLevel = computed(() => user.value?.current_role?.level ?? -1)

const displayName = computed(() => {
  const u = user.value
  if (!u) return ''
  return u.name || u.username || ''
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const dashData = ref(null)
const loading = ref(true)
const error = ref('')

/**
 * @param {Object} [params] - 下钻查询参数
 * @param {boolean} [silent=false] - 静默刷新（不显示 loading 动画）
 */
async function loadDashboard(params = {}, silent = false) {
  if (!silent) loading.value = true
  error.value = ''
  try {
    dashData.value = await getDashboard(params)
  } catch (e) {
    if (!silent) error.value = e.response?.data?.detail ?? '工作台数据加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function refresh() {
  loadDashboard()
}

/**
 * @param {Object} params - 子组件传递的下钻参数
 */
function handleDrill(params) {
  loadDashboard(params)
}

useRealtimeRefresh(
  ['user', 'submission', 'appeal', 'score', 'project', 'season', 'review_assignment', 'department', 'major', 'class'],
  () => loadDashboard({}, true),
)

onMounted(() => loadDashboard())
</script>
