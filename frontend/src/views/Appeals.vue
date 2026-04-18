<template>
  <div class="page-shell max-w-5xl" @click="clearHighlight">
    <div class="flex items-center justify-between">
      <h2 class="app-page-title">申诉列表</h2>
      <button
        v-if="!isReviewer"
        type="button"
        class="rounded-lg bg-brand-500 px-3 py-1.5 text-sm text-white hover:bg-brand-600"
        @click="openNewAppealModal"
      >
        发起独立申诉
      </button>
    </div>

    <!-- 状态筛�?-->
    <div class="app-surface p-3 md:p-4">
    <div class="flex flex-col gap-2 md:flex-row md:flex-wrap md:items-center">
      <label class="text-sm text-slate-600">状态筛选：</label>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="opt in statusOptions"
          :key="opt.value"
          type="button"
          class="rounded px-3 py-1 text-sm transition-colors"
          :class="filterStatus === opt.value
            ? 'bg-brand-500 text-white shadow-sm'
            : 'bg-slate-100 text-slate-700 hover:bg-slate-200'"
          @click="filterStatus = opt.value; loadAppeals()"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ error }}</div>

    <!-- 加载中 -->
    <div v-if="loading" class="app-surface py-12 text-center text-slate-500">加载中…</div>

    <!-- 列表 -->
    <div v-if="!loading" class="relative">
      <div v-if="paginating" class="absolute inset-0 z-10 flex items-center justify-center bg-white/60 rounded-xl">
        <span class="text-sm text-slate-400">加载中…</span>
      </div>
      <div v-if="appeals.length === 0" class="app-surface py-12 text-center text-slate-500">
        暂无申诉记录
      </div>

      <div v-else class="space-y-2">
        <div class="mobile-card-list">
          <div
            v-for="appeal in appeals"
            :key="`mobile-${appeal.id}`"
            class="mobile-card-link"
            :class="appeal.id === lastHighlightId ? 'bg-blue-50' : ''"
            @click="goToAppealDetail(appeal)"
          >
              <div class="mobile-card-body">
              <div class="flex items-center gap-2">
                <span class="mobile-card-title">{{ appeal.title || appeal.submission_detail?.project_name || '—' }}</span>
                <span class="flex-shrink-0 rounded px-1.5 py-0.5 text-[10px]" :class="appealStatusClass(appeal.status)">
                  {{ appealStatusLabel(appeal.status) }}
                </span>
              </div>
              <div v-if="appeal.indicator_name" class="mt-0.5 text-xs text-blue-600">指标：{{ appeal.indicator_name }}</div>
              <div class="mobile-card-sub line-clamp-1">{{ appeal.reason || '—' }}</div>
              <div class="mobile-card-meta">{{ isReviewer && appeal.student_name ? appeal.student_name + ' · ' : '' }}{{ formatDateTime(appeal.created_at) }}</div>
            </div>
            <svg class="mobile-card-arrow" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
          </div>
        </div>
        <div class="app-table-wrap hidden md:block">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-600">
            <tr>
              <th class="px-4 py-3 text-left font-medium">提交 ID</th>
              <th class="px-4 py-3 text-left font-medium">项目</th>
              <th v-if="isReviewer" class="px-4 py-3 text-left font-medium">申诉人</th>
              <th class="px-4 py-3 text-left font-medium">申诉指标</th>
              <th class="px-4 py-3 text-left font-medium">申诉理由</th>
              <th class="px-4 py-3 text-left font-medium">状态</th>
              <th class="px-4 py-3 text-left font-medium">申诉时间</th>
              <th class="px-4 py-3 text-left font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="appeal in appeals" :key="appeal.id" :class="appeal.id === lastHighlightId ? 'bg-blue-50' : 'hover:bg-slate-50'">
              <td class="px-4 py-3 text-slate-700">
                <router-link
                  v-if="appeal.submission"
                  :to="`/submissions/${appeal.submission}`"
                  class="app-link"
                >
                  #{{ appeal.submission }}
                </router-link>
                <span v-else class="text-xs text-slate-400">独立申诉</span>
              </td>
              <td class="px-4 py-3 text-slate-700">{{ appeal.title || appeal.submission_detail?.project_name || '—' }}</td>
              <td v-if="isReviewer" class="px-4 py-3 text-slate-700">{{ appeal.user_name || appeal.student_name || '—' }}</td>
              <td class="px-4 py-3 text-slate-500 text-xs">{{ appeal.title ? '独立申诉' : (appeal.indicator_name || '整份提交') }}</td>
              <td class="max-w-xs px-4 py-3 text-slate-700">
                <span class="block truncate" :title="appeal.reason">{{ appeal.reason || '—' }}</span>
              </td>
              <td class="px-4 py-3">
                <span class="rounded px-2 py-0.5 text-xs" :class="appealStatusClass(appeal.status)">
                  {{ appealStatusLabel(appeal.status) }}
                </span>
              </td>
              <td class="px-4 py-3 text-slate-600">{{ formatDateTime(appeal.created_at) }}</td>
              <td class="px-4 py-3">
                <div class="flex gap-2">
                  <!-- 管理�?审核角色：进入处理页 -->
                  <router-link
                    v-if="isReviewer"
                    :to="`/appeals/${appeal.id}`"
                    class="app-action app-action-primary"
                    @click="highlightStore.set('Appeals', appeal.id)"
                  >
                    {{ appeal.status === 'pending' || appeal.status === 'escalated' || appeal.status === 'escalated_to_admin' ? '处理' : '查看' }}
                  </router-link>

                  <!-- 学生：pending 时可修改理由 -->
                  <button
                    v-if="!isReviewer && appeal.status === 'pending'"
                    type="button"
                    class="app-action app-action-default"
                    @click="openEditModal(appeal)"
                  >
                    修改理由
                  </button>

                  <!-- 学生：pending 时可撤回 -->
                  <button
                    v-if="!isReviewer && appeal.status === 'pending'"
                    type="button"
                    class="app-action app-action-danger"
                    @click="confirmWithdraw(appeal)"
                  >
                    撤回
                  </button>

                  <!-- 学生：非 pending 时查看详情 -->
                  <router-link
                    v-if="!isReviewer && appeal.status !== 'pending'"
                    :to="`/appeals/${appeal.id}`"
                    class="app-action app-action-primary"
                    @click="highlightStore.set('Appeals', appeal.id)"
                  >
                    查看
                  </router-link>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalCount > pageSize" class="flex items-center justify-between text-sm text-slate-600">
        <span>共 {{ totalCount }} 条</span>
        <div class="flex gap-2">
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1 hover:bg-slate-50 disabled:opacity-40"
            :disabled="page <= 1"
            @click="page--; loadAppeals(true)"
          >
            上一页
          </button>
          <span class="px-2 py-1">{{ page }} / {{ totalPages }}</span>
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1 hover:bg-slate-50 disabled:opacity-40"
            :disabled="page >= totalPages"
            @click="page++; loadAppeals(true)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 修改理由弹窗 -->
    <div
      v-if="editModal.show"
      class="fixed inset-0 z-20 flex items-center justify-center bg-black/30"
      @click.self="editModal.show = false"
    >
      <div class="app-modal w-full max-w-md p-6">
        <h3 class="mb-3 text-base font-medium text-slate-800">修改申诉理由</h3>
        <textarea
          v-model="editModal.reason"
          rows="4"
          class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          placeholder="请填写申诉理由…"
        />
        <p v-if="editModal.error" class="mt-2 text-sm text-red-600">{{ editModal.error }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
            @click="editModal.show = false"
          >
            取消
          </button>
          <button
            type="button"
            class="app-btn app-btn-primary app-btn-sm disabled:opacity-50"
            :disabled="editModal.loading"
            @click="submitEditReason"
          >
            {{ editModal.loading ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 撤回确认弹窗 -->
    <div
      v-if="withdrawModal.show"
      class="fixed inset-0 z-20 flex items-center justify-center bg-black/30"
      @click.self="withdrawModal.show = false"
    >
      <div class="app-modal w-full max-w-sm p-6">
        <h3 class="mb-2 text-base font-medium text-slate-800">确认撤回申诉</h3>
        <p class="text-sm text-slate-600">撤回后申诉将被删除，且无法恢复。确定撤回吗？</p>
        <p v-if="withdrawModal.error" class="mt-2 text-sm text-red-600">{{ withdrawModal.error }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
            @click="withdrawModal.show = false"
          >
            取消
          </button>
          <button
            type="button"
            class="rounded bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700 disabled:opacity-50"
            :disabled="withdrawModal.loading"
            @click="doWithdraw"
          >
            {{ withdrawModal.loading ? '撤回中…' : '确认撤回' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 独立申诉弹窗 -->
    <div
      v-if="newAppealModal.show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      @click.self="newAppealModal.show = false"
    >
      <div class="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
        <h3 class="mb-3 text-base font-semibold text-slate-800">发起独立申诉</h3>
        <label class="mb-2 block text-sm text-slate-700">
          申诉主题 <span class="text-red-500">*</span>
          <input
            v-model="newAppealModal.title"
            type="text"
            class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            placeholder="请填写申诉主题"
          />
        </label>
        <label class="mb-2 block text-sm text-slate-700">
          申诉内容 <span class="text-red-500">*</span>
          <textarea
            v-model="newAppealModal.reason"
            rows="4"
            class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            placeholder="请详细描述你的申诉内容..."
          />
        </label>
        <div class="mb-2">
          <label class="block text-xs text-slate-500">可选：上传附件（可多选）</label>
          <input type="file" multiple class="mt-1 text-xs" @change="onNewAppealFilesChange" />
          <p v-if="newAppealModal.files?.length" class="mt-1 text-xs text-slate-500">已选择 {{ newAppealModal.files.length }} 个文件</p>
        </div>
        <p v-if="newAppealModal.error" class="mb-2 text-xs text-red-600">{{ newAppealModal.error }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-50" @click="newAppealModal.show = false">取消</button>
          <button
            type="button"
            class="rounded bg-brand-500 px-4 py-1.5 text-sm text-white hover:bg-brand-600 disabled:opacity-50"
            :disabled="newAppealModal.loading"
            @click="submitNewAppeal"
          >
            {{ newAppealModal.loading ? '提交中…' : '提交申诉' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 申诉列表页：学生查看并管理自己的申诉（修改理由/撤回），
 * 管理员/辅导员/主任查看全部申诉并进入处理页。
 */
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHighlightStore } from '@/stores/highlight'
import { useRoleMetaStore } from '@/stores/roles'
import { getAppeals, updateAppealReason, deleteAppeal, createIndependentAppeal } from '@/api/appeals'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatDateTime } from '@/utils/format'
import { getAppealStatusClass, getAppealStatusLabel } from '@/utils/submissionStatus'
import { ROLE_LEVEL_COUNSELOR } from '@/constants/roles'

const router = useRouter()
const auth = useAuthStore()
const highlightStore = useHighlightStore()
const roleMeta = useRoleMetaStore()
roleMeta.ensureLoaded()
const lastHighlightId = ref(null)

/** 当前用户是否为审核角色（辅导员/主任/管理员） */
const isReviewer = computed(() => {
  const level = auth.user?.current_role?.level ?? -1
  return level >= ROLE_LEVEL_COUNSELOR
})

const loading = ref(false)
const paginating = ref(false)
const error = ref('')
const appeals = ref([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = 15
const filterStatus = ref('all')

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize)))

const directorLabel = computed(() => roleMeta.nameByLevel(3))
const superAdminLabel = computed(() => roleMeta.nameByLevel(5))
const statusOptions = computed(() => [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待处理' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
  { value: 'escalated', label: `已上报${directorLabel.value}` },
  { value: 'escalated_to_admin', label: `已上报${superAdminLabel.value}` },
])

/**
 * @param {string} status
 * @returns {string} Tailwind class
 */
function appealStatusClass(status) {
  return getAppealStatusClass(status)
}

/**
 * @param {string} status
 * @returns {string}
 */
function appealStatusLabel(status) {
  return getAppealStatusLabel(status, {
    directorLabel: directorLabel.value,
    superAdminLabel: superAdminLabel.value,
  })
}

/**
 * @param {boolean} [soft=false] - 翻页时使用软加载，保留现有内容
 */
async function loadAppeals(soft = false) {
  if (soft) {
    paginating.value = true
  } else {
    loading.value = true
  }
  error.value = ''
  try {
    const params = { page: page.value }
    if (filterStatus.value !== 'all') params.status = filterStatus.value
    const data = await getAppeals(params)
    if (Array.isArray(data)) {
      appeals.value = data
      totalCount.value = data.length
    } else {
      appeals.value = data.results ?? []
      totalCount.value = data.count ?? appeals.value.length
    }
  } catch (e) {
    error.value = e.response?.data?.detail ?? '加载失败'
    appeals.value = []
  } finally {
    loading.value = false
    paginating.value = false
  }
}

/* ── 修改理由弹窗 ── */
const editModal = reactive({
  show: false,
  appealId: null,
  reason: '',
  loading: false,
  error: '',
})

/**
 * @param {Object} appeal
 */
function openEditModal(appeal) {
  editModal.appealId = appeal.id
  editModal.reason = appeal.reason ?? ''
  editModal.error = ''
  editModal.show = true
}

async function submitEditReason() {
  if (!editModal.reason.trim()) {
    editModal.error = '理由不能为空'
    return
  }
  editModal.loading = true
  editModal.error = ''
  try {
    await updateAppealReason(editModal.appealId, editModal.reason.trim())
    lastHighlightId.value = editModal.appealId
    editModal.show = false
    await loadAppeals()
  } catch (e) {
    editModal.error = e.response?.data?.detail ?? e.response?.data?.reason?.[0] ?? '保存失败'
  } finally {
    editModal.loading = false
  }
}

/* ── 撤回确认弹窗 ── */
const withdrawModal = reactive({
  show: false,
  appealId: null,
  loading: false,
  error: '',
})

/**
 * @param {Object} appeal
 */
function confirmWithdraw(appeal) {
  withdrawModal.appealId = appeal.id
  withdrawModal.error = ''
  withdrawModal.show = true
}

async function doWithdraw() {
  withdrawModal.loading = true
  withdrawModal.error = ''
  try {
    await deleteAppeal(withdrawModal.appealId)
    withdrawModal.show = false
    await loadAppeals()
  } catch (e) {
    withdrawModal.error = e.response?.data?.detail ?? '撤回失败'
  } finally {
    withdrawModal.loading = false
  }
}

/**
 * 移动端卡片点击：进入申诉详情页。
 * @param {Object} appeal
 */
function goToAppealDetail(appeal) {
  highlightStore.set('Appeals', appeal.id)
  router.push(`/appeals/${appeal.id}`)
}

/**
 * 点击页面任意处清除高亮
 */
function clearHighlight() {
  if (lastHighlightId.value !== null) lastHighlightId.value = null
}

const newAppealModal = reactive({
  show: false,
  title: '',
  reason: '',
  files: [],
  loading: false,
  error: '',
})

function openNewAppealModal() {
  newAppealModal.show = true
  newAppealModal.title = ''
  newAppealModal.reason = ''
  newAppealModal.files = []
  newAppealModal.loading = false
  newAppealModal.error = ''
}

function onNewAppealFilesChange(e) {
  newAppealModal.files = Array.from(e.target?.files || [])
}

async function submitNewAppeal() {
  if (!newAppealModal.title.trim()) {
    newAppealModal.error = '请填写申诉主题'
    return
  }
  if (!newAppealModal.reason.trim()) {
    newAppealModal.error = '请填写申诉内容'
    return
  }
  newAppealModal.loading = true
  newAppealModal.error = ''
  try {
    await createIndependentAppeal(
      newAppealModal.title.trim(),
      newAppealModal.reason.trim(),
      newAppealModal.files,
    )
    newAppealModal.show = false
    loadAppeals()
  } catch (e) {
    newAppealModal.error = e.response?.data?.detail ?? '提交申诉失败'
  } finally {
    newAppealModal.loading = false
  }
}

useRealtimeRefresh('appeal', loadAppeals)

onMounted(() => {
  lastHighlightId.value = highlightStore.pop('Appeals')
  loadAppeals()
})
</script>
