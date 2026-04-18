<template>
  <div class="page-shell" @click="clearHighlight">
    <nav class="app-breadcrumb">
      <router-link :to="{ name: 'Seasons' }" class="text-brand-600 hover:underline">测评周期</router-link>
      <span>/</span>
      <span class="app-breadcrumb-current">{{ seasonName || '加载中…' }}</span>
    </nav>

    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <h3 class="app-page-title">项目列表</h3>
      <button
        type="button"
        class="app-btn app-btn-primary app-btn-sm"
        @click="openCreate"
      >
        新建项目
      </button>
    </div>

    <div v-if="loading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="loadError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ loadError }}</div>
    <div v-else class="space-y-2">
      <div
        v-if="bulkActionVisible"
        class="hidden md:flex items-center gap-2 rounded border border-blue-200 bg-blue-50 px-3 py-2 text-sm"
      >
        <span class="text-slate-700">
          已选 <span class="font-semibold text-slate-900">{{ selectedCount }}</span> 个项目
        </span>
        <button
          type="button"
          class="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
          @click="doBatchSetStatus('draft', '设为草稿')"
        >
          批量设为草稿
        </button>
        <button
          type="button"
          class="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
          @click="doBatchSetStatus('ongoing', '设为进行中')"
        >
          批量设为进行中
        </button>
        <button
          type="button"
          class="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
          @click="doBatchSetStatus('closed', '设为已结束')"
        >
          批量设为已结束
        </button>
        <button
          type="button"
          class="ml-auto rounded border border-red-200 bg-white px-2.5 py-1 text-xs text-red-600 hover:bg-red-50"
          @click="openBatchDeleteDialog"
        >
          批量删除
        </button>
      </div>
      <div class="mobile-card-list">
        <div
          v-for="p in projects"
          :key="`mobile-${p.id}`"
          class="mobile-card-link"
          :class="p.id === lastHighlightId ? 'bg-blue-50' : ''"
          @click="goToConfig(p.id)"
        >
          <div class="mobile-card-body">
            <div class="flex items-center gap-2">
              <span class="mobile-card-title">{{ p.name }}</span>
              <span class="flex-shrink-0 rounded px-1.5 py-0.5 text-[10px]" :class="projectStatusClass(p.status)">
                {{ projectStatusLabel(p.status) }}
              </span>
            </div>
            <div class="mobile-card-sub">{{ p.description || '—' }}</div>
            <div class="mobile-card-meta">{{ formatDateTime(p.start_time) }} — {{ formatDateTime(p.end_time) }}</div>
          </div>
          <svg class="mobile-card-arrow" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
        </div>
      </div>
      <div class="app-table-wrap hidden md:block">
      <table class="app-table min-w-[960px]">
        <thead>
          <tr class="border-b border-slate-200 bg-slate-50">
            <th class="px-4 py-2.5 text-left font-medium text-slate-700 w-12">
              <input
                type="checkbox"
                class="rounded border-slate-300"
                :checked="allSelected"
                :disabled="projects.length === 0"
                @click.stop
                @change="toggleSelectAllProjects($event.target.checked)"
              />
            </th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">项目名称</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">描述</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">状态</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">开始时间</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">结束时间</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">评定截止</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">允许迟交</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="p in projects"
            :key="p.id"
            class="border-b border-slate-100 cursor-pointer"
            :class="p.id === lastHighlightId ? 'bg-blue-50' : 'hover:bg-slate-50'"
            @click="goToConfig(p.id)"
          >
            <td class="px-4 py-2.5" @click.stop>
              <input
                type="checkbox"
                class="rounded border-slate-300"
                :checked="isProjectSelected(p.id)"
                @change="toggleProjectSelection(p.id, $event.target.checked)"
              />
            </td>
            <td class="px-4 py-2.5 text-slate-800 whitespace-nowrap">{{ p.name }}</td>
            <td class="max-w-xs truncate px-4 py-2.5 text-slate-600" :title="p.description">{{ p.description || '—' }}</td>
            <td class="px-4 py-2.5 whitespace-nowrap">
              <span class="rounded px-2 py-0.5 text-xs" :class="projectStatusClass(p.status)">
                {{ projectStatusLabel(p.status) }}
              </span>
            </td>
            <td class="px-4 py-2.5 text-slate-600 whitespace-nowrap">{{ formatDateTime(p.start_time) }}</td>
            <td class="px-4 py-2.5 text-slate-600 whitespace-nowrap">{{ formatDateTime(p.end_time) }}</td>
            <td class="px-4 py-2.5 text-slate-600 whitespace-nowrap">{{ formatDateTime(p.review_end_time) }}</td>
            <td class="px-4 py-2.5 text-slate-600 whitespace-nowrap">{{ p.allow_late_submit ? '是' : '否' }}</td>
            <td class="px-4 py-2.5 whitespace-nowrap" @click.stop>
              <div class="flex items-center gap-3">
                <router-link
                  :to="{ name: 'ProjectConfig', params: { projectId: p.id } }"
                  class="app-action app-action-primary"
                  @click="highlightStore.set('SeasonProjects', p.id)"
                >
                  配置
                </router-link>
                <button
                  class="app-action app-action-danger"
                  @click="askDeleteProject(p)"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="projects.length === 0">
            <td colspan="9" class="px-4 py-8 text-center text-slate-500">暂无项目，请点击「新建项目」添加</td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <!-- 密码确认弹窗（删除项目） -->
    <PasswordConfirmDialog
      v-model:visible="showDeleteDialog"
      title="删除测评项目"
      :message="`确认要永久删除测评项目「${pendingDeleteProject?.name ?? ''}」吗？此操作无法撤销。`"
      confirm-text="确认删除"
      :password-label="`${superAdminLabel}密码`"
      @confirmed="doDeleteProject"
    />
    <PasswordConfirmDialog
      v-model:visible="showBatchDeleteDialog"
      title="批量删除测评项目"
      :message="`确认要永久删除已选中的 ${selectedCount} 个测评项目吗？此操作无法撤销。`"
      confirm-text="确认批量删除"
      :password-label="`${superAdminLabel}密码`"
      @confirmed="doBatchDeleteProject"
    />

    <!-- 新建项目弹窗 -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-20 flex items-center justify-center bg-black/30"
      @click.self="closeModal"
    >
      <div class="w-full max-w-lg rounded-lg border border-slate-200 bg-white p-6 shadow max-h-[90vh] overflow-y-auto">
        <h4 class="text-base font-medium text-slate-800">新建项目</h4>
        <!-- 周期时间提示 -->
        <p v-if="currentSeason" class="mt-1 text-xs text-slate-500">
          所属周期：{{ currentSeason.name }}
          <span v-if="currentSeason.start_time || currentSeason.end_time">
            （{{ formatDateTime(currentSeason.start_time) }} — {{ formatDateTime(currentSeason.end_time) }}）
          </span>
        </p>
        <form class="mt-4 space-y-3" @submit.prevent="submitForm">
          <label class="block text-sm text-slate-700">
            项目名称
            <input
              v-model="form.name"
              type="text"
              required
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如：综合素质测评"
            />
          </label>
          <label class="block text-sm text-slate-700">
            描述（选填）
            <textarea
              v-model="form.description"
              rows="2"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="项目说明"
            />
          </label>
          <label class="block text-sm text-slate-700">
            状态
            <select
              v-model="form.status"
              class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="draft">草稿</option>
              <option value="ongoing">进行中</option>
              <option value="closed">已结束</option>
            </select>
          </label>

          <!-- 项目时间配置 -->
          <div class="rounded border border-slate-100 bg-slate-50 p-3 space-y-3">
            <p class="text-xs font-medium text-slate-600">项目时间（需在测评周期时间范围内）</p>
            <label class="block text-sm text-slate-700">
              开始时间（学生提交开放，选填）
              <input
                v-model="form.start_time"
                type="datetime-local"
                :min="seasonMinDatetime"
                :max="form.end_time || seasonMaxDatetime"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              />
            </label>
            <label class="block text-sm text-slate-700">
              结束时间（学生提交截止，选填）
              <input
                v-model="form.end_time"
                type="datetime-local"
                :min="form.start_time || seasonMinDatetime"
                :max="seasonMaxDatetime"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              />
            </label>
            <label class="block text-sm text-slate-700">
              成绩评定截止时间（选填，可晚于项目结束时间）
              <input
                v-model="form.review_end_time"
                type="datetime-local"
                :min="form.end_time || form.start_time || seasonMinDatetime"
                :max="seasonMaxDatetime"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              />
            </label>
          </div>

          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input v-model="form.allow_late_submit" type="checkbox" class="rounded border-slate-300" />
            允许迟交
          </label>
          <label v-if="form.allow_late_submit" class="block text-sm text-slate-700">
            迟交截止时间（必须晚于项目结束时间且不晚于评定截止时间）
            <input
              v-model="form.late_submit_deadline"
              type="datetime-local"
              :min="form.end_time || undefined"
              :max="form.review_end_time || seasonMaxDatetime"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </label>
          <p v-if="modalError" class="text-sm text-red-600">{{ modalError }}</p>
          <div class="mt-4 flex justify-end gap-2">
            <button
              type="button"
              class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
              @click="closeModal"
            >
              取消
            </button>
            <button
              type="submit"
              class="app-btn app-btn-primary app-btn-sm disabled:opacity-50"
              :disabled="submitLoading"
            >
              {{ submitLoading ? '提交中…' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getSeasons,
  getSeasonProjects,
  createProject,
  deleteProject,
  batchUpdateProjectsStatus,
  batchDeleteProjects,
} from '@/api/eval'
import { useHighlightStore } from '@/stores/highlight'
import { useRoleMetaStore } from '@/stores/roles'
import PasswordConfirmDialog from '@/components/PasswordConfirmDialog.vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatDateTime } from '@/utils/format'
import { openAlert, openConfirm } from '@/utils/dialog'

const route = useRoute()
const highlightStore = useHighlightStore()
const roleMeta = useRoleMetaStore()
roleMeta.ensureLoaded()
const superAdminLabel = computed(() => roleMeta.nameByLevel(5))
const lastHighlightId = ref(null)
const router = useRouter()
const seasonId = computed(() => Number(route.params.seasonId))

const loading = ref(false)
const loadError = ref('')
const projects = ref([])
const seasonList = ref([])
const selectedProjectIds = ref([])
const showBatchDeleteDialog = ref(false)
const selectedCount = computed(() => selectedProjectIds.value.length)
const bulkActionVisible = computed(() => selectedCount.value >= 2)
const allSelected = computed(() => projects.value.length > 0 && selectedProjectIds.value.length === projects.value.length)

const currentSeason = computed(() => seasonList.value.find((s) => s.id === seasonId.value) ?? null)
const seasonName = computed(() => currentSeason.value?.name ?? '')

/** Converts ISO string to 'YYYY-MM-DDTHH:mm' for datetime-local :min/:max */
function toLocalDatetimeStr(isoStr) {
  if (!isoStr) return undefined
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return undefined
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const seasonMinDatetime = computed(() => toLocalDatetimeStr(currentSeason.value?.start_time))
const seasonMaxDatetime = computed(() => toLocalDatetimeStr(currentSeason.value?.end_time))

// 删除项目
const showDeleteDialog = ref(false)
const pendingDeleteProject = ref(null)

function askDeleteProject(project) {
  pendingDeleteProject.value = project
  showDeleteDialog.value = true
}

async function doDeleteProject({ confirmToken, reason }) {
  if (!pendingDeleteProject.value) return
  try {
    await deleteProject(pendingDeleteProject.value.id, { confirm_token: confirmToken, reason })
    pendingDeleteProject.value = null
    loadProjects()
  } catch (e) {
    await openAlert({
      title: '删除失败',
      message: e.response?.data?.detail ?? '删除失败，请重试',
      danger: true,
    })
  }
}

/**
 * 判断项目是否已勾选。
 * @param {number} projectId
 * @returns {boolean}
 */
function isProjectSelected(projectId) {
  return selectedProjectIds.value.includes(projectId)
}

/**
 * 勾选/取消勾选单个项目。
 * @param {number} projectId
 * @param {boolean} checked
 */
function toggleProjectSelection(projectId, checked) {
  if (checked) {
    if (!selectedProjectIds.value.includes(projectId)) {
      selectedProjectIds.value = [...selectedProjectIds.value, projectId]
    }
    return
  }
  selectedProjectIds.value = selectedProjectIds.value.filter((id) => id !== projectId)
}

/**
 * 全选/取消全选当前周期下项目。
 * @param {boolean} checked
 */
function toggleSelectAllProjects(checked) {
  if (checked) {
    selectedProjectIds.value = projects.value.map((item) => item.id)
    return
  }
  selectedProjectIds.value = []
}

function openBatchDeleteDialog() {
  if (selectedCount.value < 2) return
  showBatchDeleteDialog.value = true
}

async function doBatchDeleteProject({ confirmToken, reason }) {
  if (selectedCount.value < 2) return
  try {
    await batchDeleteProjects(selectedProjectIds.value, { confirm_token: confirmToken, reason })
    selectedProjectIds.value = []
    await loadProjects()
    await openAlert({
      title: '操作成功',
      message: '批量删除测评项目成功',
    })
  } catch (e) {
    await openAlert({
      title: '批量删除失败',
      message: e.response?.data?.detail ?? '批量删除测评项目失败，请重试',
      danger: true,
    })
  }
}

/**
 * 批量修改项目状态。
 * @param {'draft'|'ongoing'|'closed'} status
 * @param {string} label
 */
async function doBatchSetStatus(status, label) {
  if (selectedCount.value < 2) return
  const { confirmed } = await openConfirm({
    title: '批量操作确认',
    message: `确定将选中的 ${selectedCount.value} 个项目${label}吗？`,
    confirmText: '确认执行',
  })
  if (!confirmed) return
  try {
    await batchUpdateProjectsStatus(selectedProjectIds.value, status)
    await loadProjects()
    await openAlert({
      title: '操作成功',
      message: `批量${label}成功`,
    })
  } catch (e) {
    await openAlert({
      title: '操作失败',
      message: e.response?.data?.detail ?? `批量${label}失败`,
      danger: true,
    })
  }
}

const showModal = ref(false)
const submitLoading = ref(false)
const modalError = ref('')
const form = ref({
  name: '',
  description: '',
  status: 'draft',
  start_time: '',
  end_time: '',
  review_end_time: '',
  allow_late_submit: false,
  late_submit_deadline: '',
})

function projectStatusLabel(s) {
  const map = { draft: '草稿', ongoing: '进行中', closed: '已结束' }
  return map[s] ?? s
}

function projectStatusClass(s) {
  const map = { draft: 'bg-slate-200 text-slate-700', ongoing: 'bg-green-100 text-green-800', closed: 'bg-red-100 text-red-700' }
  return map[s] ?? 'bg-slate-100 text-slate-600'
}

function openCreate() {
  form.value = {
    name: '',
    description: '',
    status: 'draft',
    start_time: '',
    end_time: '',
    review_end_time: '',
    allow_late_submit: false,
    late_submit_deadline: '',
  }
  modalError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

function extractError(e) {
  const d = e.response?.data
  if (!d) return '创建失败'
  return (
    d.start_time?.[0] ??
    d.end_time?.[0] ??
    d.review_end_time?.[0] ??
    d.late_submit_deadline?.[0] ??
    d.status?.[0] ??
    d.detail ??
    d.name?.[0] ??
    '创建失败'
  )
}

async function submitForm() {
  modalError.value = ''
  // 前端基本时间顺序校验
  const { start_time, end_time, review_end_time, late_submit_deadline, allow_late_submit } = form.value
  if (start_time && end_time && new Date(end_time) <= new Date(start_time)) {
    modalError.value = '项目结束时间必须晚于开始时间'
    return
  }
  if (end_time && review_end_time && new Date(review_end_time) < new Date(end_time)) {
    modalError.value = '成绩评定截止时间不得早于项目结束时间'
    return
  }
  if (allow_late_submit && late_submit_deadline && end_time && new Date(late_submit_deadline) <= new Date(end_time)) {
    modalError.value = '迟交截止时间必须晚于项目结束时间'
    return
  }

  submitLoading.value = true
  const payload = {
    season: seasonId.value,
    name: form.value.name,
    description: form.value.description || undefined,
    status: form.value.status,
    allow_late_submit: form.value.allow_late_submit,
  }
  if (form.value.start_time) payload.start_time = new Date(form.value.start_time).toISOString()
  if (form.value.end_time) payload.end_time = new Date(form.value.end_time).toISOString()
  if (form.value.review_end_time) payload.review_end_time = new Date(form.value.review_end_time).toISOString()
  if (form.value.allow_late_submit && form.value.late_submit_deadline) {
    payload.late_submit_deadline = new Date(form.value.late_submit_deadline).toISOString()
  }
  try {
    const created = await createProject(seasonId.value, payload)
    closeModal()
    if (created?.id != null) lastHighlightId.value = created.id
    loadProjects()
  } catch (e) {
    modalError.value = extractError(e)
  } finally {
    submitLoading.value = false
  }
}

function goToConfig(projectId) {
  highlightStore.set('SeasonProjects', projectId)
  router.push({ name: 'ProjectConfig', params: { projectId } })
}

/** 清除行高亮（点击页面任意处触发） */
function clearHighlight() {
  if (lastHighlightId.value !== null) lastHighlightId.value = null
}

async function loadProjects() {
  if (!seasonId.value) return
  loading.value = true
  loadError.value = ''
  try {
    projects.value = await getSeasonProjects(seasonId.value)
    const idSet = new Set(projects.value.map((item) => item.id))
    selectedProjectIds.value = selectedProjectIds.value.filter((id) => idSet.has(id))
  } catch (e) {
    loadError.value = e.response?.data?.detail ?? '加载项目列表失败'
    projects.value = []
    selectedProjectIds.value = []
  } finally {
    loading.value = false
  }
}

async function loadSeasons() {
  try {
    seasonList.value = await getSeasons()
  } catch {
    seasonList.value = []
  }
}

useRealtimeRefresh('project', loadProjects)

onMounted(() => {
  lastHighlightId.value = highlightStore.pop('SeasonProjects')
  loadSeasons()
  loadProjects()
})

watch(seasonId, () => {
  selectedProjectIds.value = []
  loadProjects()
})
</script>
