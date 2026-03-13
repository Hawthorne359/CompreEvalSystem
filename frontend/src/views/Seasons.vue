<template>
  <div class="page-shell" @click="clearHighlight">
    <div class="flex items-center justify-between">
      <h3 class="app-page-title hidden md:block">测评周期</h3>
      <button
        type="button"
        class="app-btn app-btn-primary app-btn-sm w-full md:w-auto"
        @click="openCreate"
      >
        新建周期
      </button>
    </div>

    <div v-if="loading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="error" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ error }}</div>
    <div v-else class="space-y-2">
      <div
        v-if="bulkActionVisible"
        class="hidden md:flex items-center gap-2 rounded border border-brand-200 bg-brand-50 px-3 py-2 text-sm"
      >
        <span class="text-slate-700">
          已选 <span class="font-semibold text-slate-900">{{ selectedCount }}</span> 个周期
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
          v-for="s in seasons"
          :key="`mobile-${s.id}`"
          class="mobile-card"
          :class="{ 'bg-blue-50': s.id === lastHighlightId }"
        >
          <div class="flex items-start gap-3" @click="goToProjects(s.id)">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="mobile-card-title">{{ s.name }}</span>
                <span class="flex-shrink-0 rounded px-1.5 py-0.5 text-[10px]" :class="statusClass(s.status)">
                  {{ statusLabel(s.status) }}
                </span>
              </div>
              <div class="mobile-card-sub">{{ s.academic_year || '—' }} {{ s.semester || '' }}</div>
              <div class="mobile-card-meta">{{ formatDateTime(s.start_time) }} — {{ formatDateTime(s.end_time) }}</div>
            </div>
            <svg class="mobile-card-arrow mt-1" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
          </div>
          <div class="mt-2 flex gap-2 border-t border-slate-100 pt-2">
            <button type="button" class="app-action app-action-primary flex-1" @click.stop="goToProjects(s.id)">管理项目</button>
            <button type="button" class="app-action app-action-default flex-1" @click.stop="openEdit(s)">编辑</button>
            <button type="button" class="app-action app-action-danger flex-1" @click.stop="askDeleteSeason(s)">删除</button>
          </div>
        </div>
      </div>
      <div class="app-table-wrap hidden md:block">
      <table class="app-table">
        <thead>
          <tr class="border-b border-slate-200 bg-slate-50">
            <th class="px-4 py-2.5 text-left font-medium text-slate-700 w-12">
              <input
                type="checkbox"
                class="rounded border-slate-300"
                :checked="allSelected"
                :disabled="seasons.length === 0"
                @click.stop
                @change="toggleSelectAllSeasons($event.target.checked)"
              />
            </th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">名称</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">学年</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">学期</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">状态</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">开始时间</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">结束时间</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in seasons"
            :key="s.id"
            class="border-b border-slate-100 cursor-pointer transition-colors"
            :class="s.id === lastHighlightId ? 'bg-blue-50' : 'hover:bg-slate-50'"
            @click="goToProjects(s.id)"
          >
            <td class="px-4 py-2.5" @click.stop>
              <input
                type="checkbox"
                class="rounded border-slate-300"
                :checked="isSeasonSelected(s.id)"
                @change="toggleSeasonSelection(s.id, $event.target.checked)"
              />
            </td>
            <td class="px-4 py-2.5 text-slate-800">{{ s.name }}</td>
            <td class="px-4 py-2.5 text-slate-600">{{ s.academic_year || '—' }}</td>
            <td class="px-4 py-2.5 text-slate-600">{{ s.semester || '—' }}</td>
            <td class="px-4 py-2.5">
              <span
                class="rounded px-2 py-0.5 text-xs"
                :class="statusClass(s.status)"
              >
                {{ statusLabel(s.status) }}
              </span>
            </td>
            <td class="px-4 py-2.5 text-slate-600">{{ formatDateTime(s.start_time) }}</td>
            <td class="px-4 py-2.5 text-slate-600">{{ formatDateTime(s.end_time) }}</td>
            <td class="px-4 py-2.5 flex items-center gap-3" @click.stop>
              <router-link
                :to="{ name: 'SeasonProjects', params: { seasonId: s.id } }"
                class="app-action app-action-primary"
                @click="highlightStore.set('Seasons', s.id)"
              >
                管理项目
              </router-link>
              <button
                class="app-action app-action-default"
                @click="openEdit(s)"
              >
                编辑
              </button>
              <button
                class="app-action app-action-danger"
                @click="askDeleteSeason(s)"
              >
                删除
              </button>
            </td>
          </tr>
          <tr v-if="seasons.length === 0">
            <td colspan="8" class="px-4 py-8 text-center text-slate-500">暂无测评周期，请点击「新建周期」添加</td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <!-- 密码确认弹窗（删除周期） -->
    <PasswordConfirmDialog
      v-model:visible="showDeleteDialog"
      title="删除测评周期"
      :message="`确认要永久删除测评周期「${pendingDeleteSeason?.name ?? ''}」吗？该操作将同时删除其下所有项目，无法撤销。`"
      confirm-text="确认删除"
      :password-label="`${superAdminLabel}密码`"
      @confirmed="doDeleteSeason"
    />
    <PasswordConfirmDialog
      v-model:visible="showBatchDeleteDialog"
      title="批量删除测评周期"
      :message="`确认要永久删除已选中的 ${selectedCount} 个测评周期吗？该操作将同时删除其下所有项目，无法撤销。`"
      confirm-text="确认批量删除"
      :password-label="`${superAdminLabel}密码`"
      @confirmed="doBatchDeleteSeason"
    />

    <!-- 新建/编辑周期弹窗 -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-20 flex items-center justify-center bg-black/30"
    >
      <div class="app-modal w-full max-w-md p-6">
        <h4 class="text-base font-medium text-slate-800">{{ editingSeasonId ? '编辑测评周期' : '新建测评周期' }}</h4>
        <form class="mt-4 space-y-3" @submit.prevent="submitForm">
          <label class="block text-sm text-slate-700">
            名称
            <input
              v-model="form.name"
              type="text"
              required
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如：2024-2025学年第一学期"
            />
          </label>
          <label class="block text-sm text-slate-700">
            学年
            <select
              v-model="form.academic_year"
              required
              class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="autoFillName"
            >
              <option value="" disabled>请选择学年</option>
              <option v-for="y in academicYearOptions" :key="y" :value="y">{{ y }}</option>
            </select>
          </label>
          <label class="block text-sm text-slate-700">
            学期
            <select
              v-model="form.semester"
              class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="autoFillName"
            >
              <option value="">不指定</option>
              <option value="第一学期">第一学期</option>
              <option value="第二学期">第二学期</option>
            </select>
          </label>
          <div class="block text-sm text-slate-700">
            状态
            <select
              v-model="form.status"
              class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="draft">草稿</option>
              <option value="ongoing" :disabled="!canSeasonBeOngoing">进行中{{ canSeasonBeOngoing ? '' : '（不可用）' }}</option>
              <option value="closed">已结束</option>
            </select>
            <p v-if="!canSeasonBeOngoing" class="mt-1 text-xs text-amber-600">
              测评周期结束时间已过，"进行中"不可选。请先将结束时间修改到未来后再更改状态。
            </p>
          </div>
          <label class="block text-sm text-slate-700">
            开始时间（选填）
            <input
              v-model="form.start_time"
              type="datetime-local"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </label>
          <label class="block text-sm text-slate-700">
            结束时间（选填）
            <input
              v-model="form.end_time"
              type="datetime-local"
              :min="form.start_time || undefined"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </label>
          <p v-if="modalError" class="text-sm text-red-600">{{ modalError }}</p>
          <div v-if="editingSeasonId" class="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
            注意：修改结束时间可能导致"进行中"的关联项目被自动设为"已结束"。
          </div>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getSeasons, createSeason, updateSeason, deleteSeason, batchUpdateSeasonsStatus, batchDeleteSeasons } from '@/api/eval'
import { useHighlightStore } from '@/stores/highlight'
import { useRoleMetaStore } from '@/stores/roles'
import PasswordConfirmDialog from '@/components/PasswordConfirmDialog.vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const roleMeta = useRoleMetaStore()
roleMeta.ensureLoaded()
const superAdminLabel = computed(() => roleMeta.nameByLevel(5))
const loading = ref(false)
const error = ref('')
const seasons = ref([])
const selectedSeasonIds = ref([])
const showBatchDeleteDialog = ref(false)
const selectedCount = computed(() => selectedSeasonIds.value.length)
const bulkActionVisible = computed(() => selectedCount.value >= 2)
const allSelected = computed(() => seasons.value.length > 0 && selectedSeasonIds.value.length === seasons.value.length)

/**
 * 判断周期是否已被勾选。
 * @param {number} seasonId
 * @returns {boolean}
 */
function isSeasonSelected(seasonId) {
  return selectedSeasonIds.value.includes(seasonId)
}

/**
 * 勾选/取消勾选单个周期。
 * @param {number} seasonId
 * @param {boolean} checked
 */
function toggleSeasonSelection(seasonId, checked) {
  if (checked) {
    if (!selectedSeasonIds.value.includes(seasonId)) {
      selectedSeasonIds.value = [...selectedSeasonIds.value, seasonId]
    }
    return
  }
  selectedSeasonIds.value = selectedSeasonIds.value.filter((id) => id !== seasonId)
}

/**
 * 全选/取消全选当前列表周期。
 * @param {boolean} checked
 */
function toggleSelectAllSeasons(checked) {
  if (checked) {
    selectedSeasonIds.value = seasons.value.map((item) => item.id)
    return
  }
  selectedSeasonIds.value = []
}

// 删除周期
const showDeleteDialog = ref(false)
const pendingDeleteSeason = ref(null)
const deleteError = ref('')

function askDeleteSeason(season) {
  pendingDeleteSeason.value = season
  deleteError.value = ''
  showDeleteDialog.value = true
}

async function doDeleteSeason({ confirmToken, reason }) {
  if (!pendingDeleteSeason.value) return
  try {
    await deleteSeason(pendingDeleteSeason.value.id, { confirm_token: confirmToken, reason })
    pendingDeleteSeason.value = null
    loadSeasons()
  } catch (e) {
    deleteError.value = e.response?.data?.detail ?? '删除失败，请重试'
    alert(deleteError.value)
  }
}

function openBatchDeleteDialog() {
  if (selectedCount.value < 2) return
  showBatchDeleteDialog.value = true
}

async function doBatchDeleteSeason({ confirmToken, reason }) {
  if (selectedCount.value < 2) return
  try {
    await batchDeleteSeasons(selectedSeasonIds.value, { confirm_token: confirmToken, reason })
    selectedSeasonIds.value = []
    await loadSeasons()
    window.alert('批量删除测评周期成功')
  } catch (e) {
    window.alert(e.response?.data?.detail ?? '批量删除测评周期失败，请重试')
  }
}

/**
 * 批量修改周期状态。
 * @param {'draft'|'ongoing'|'closed'} status
 * @param {string} label
 */
async function doBatchSetStatus(status, label) {
  if (selectedCount.value < 2) return
  if (!window.confirm(`确定将选中的 ${selectedCount.value} 个周期${label}吗？`)) return
  try {
    await batchUpdateSeasonsStatus(selectedSeasonIds.value, status)
    await loadSeasons()
    window.alert(`批量${label}成功`)
  } catch (e) {
    window.alert(e.response?.data?.detail ?? `批量${label}失败`)
  }
}

const showModal = ref(false)
const submitLoading = ref(false)
const modalError = ref('')
const editingSeasonId = ref(null)
const form = ref({
  name: '',
  academic_year: '',
  semester: '',
  status: 'draft',
  start_time: '',
  end_time: '',
})

const highlightStore = useHighlightStore()
const lastHighlightId = ref(null)

/**
 * 在编辑模态框中判断"进行中"是否可选：
 * 若已设置了结束时间且当前时间已超过，则不可设置为进行中。
 */
const canSeasonBeOngoing = computed(() => {
  const endStr = form.value.end_time
  if (!endStr) return true  // 未设置结束时间，不限制
  const endDate = new Date(endStr)
  if (isNaN(endDate.getTime())) return true
  return endDate > new Date()
})

/**
 * 动态生成学年选项列表（当前年份前后各 10 年），格式为 "YYYY-(YYYY+1)"。
 * @returns {string[]}
 */
const academicYearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const options = []
  for (let y = currentYear - 10; y <= currentYear + 10; y++) {
    options.push(`${y}-${y + 1}`)
  }
  return options
})

/**
 * 学年和学期变更时自动填充名称字段（仅在名称为空或由自动生成逻辑产生时触发）。
 */
function autoFillName() {
  const ay = form.value.academic_year
  const sem = form.value.semester
  if (!ay) return
  const autoName = sem ? `${ay}学年${sem}` : `${ay}学年`
  const currentName = form.value.name
  if (!currentName || /^\d{4}-\d{4}学年/.test(currentName)) {
    form.value.name = autoName
  }
}

/** 状态显示文案 */
function statusLabel(status) {
  const map = { draft: '草稿', ongoing: '进行中', closed: '已结束' }
  return map[status] ?? status
}

/** 状态样式 */
function statusClass(status) {
  const map = { draft: 'bg-slate-200 text-slate-700', ongoing: 'bg-green-100 text-green-800', closed: 'bg-red-100 text-red-700' }
  return map[status] ?? 'bg-slate-100 text-slate-600'
}

/** 将 ISO 字符串转换为 datetime-local 输入格式（去掉秒和时区后缀） */
function toLocalDatetime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return ''
  // 格式：YYYY-MM-DDTHH:mm（datetime-local 要求）
  const pad = (n) => String(n).padStart(2, '0')
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  )
}

function openCreate() {
  editingSeasonId.value = null
  form.value = {
    name: '',
    academic_year: '',
    semester: '',
    status: 'draft',
    start_time: '',
    end_time: '',
  }
  modalError.value = ''
  showModal.value = true
}

function openEdit(season) {
  editingSeasonId.value = season.id
  form.value = {
    name: season.name,
    academic_year: season.academic_year || '',
    semester: season.semester || '',
    status: season.status,
    start_time: toLocalDatetime(season.start_time),
    end_time: toLocalDatetime(season.end_time),
  }
  modalError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingSeasonId.value = null
}

async function submitForm() {
  modalError.value = ''
  if (form.value.start_time && form.value.end_time) {
    const start = new Date(form.value.start_time).getTime()
    const end = new Date(form.value.end_time).getTime()
    if (end <= start) {
      modalError.value = '结束时间必须晚于开始时间'
      return
    }
  }
  submitLoading.value = true
  const payload = {
    name: form.value.name,
    academic_year: form.value.academic_year,
    semester: form.value.semester || undefined,
    status: form.value.status,
  }
  if (form.value.start_time) payload.start_time = new Date(form.value.start_time).toISOString()
  if (form.value.end_time) payload.end_time = new Date(form.value.end_time).toISOString()
  try {
    if (editingSeasonId.value) {
      const savedId = editingSeasonId.value
      await updateSeason(editingSeasonId.value, payload)
      closeModal()
      loadSeasons()
      lastHighlightId.value = savedId
    } else {
      const created = await createSeason(payload)
      closeModal()
      loadSeasons()
      lastHighlightId.value = created?.id ?? null
    }
  } catch (e) {
    const data = e.response?.data
    modalError.value =
      data?.end_time?.[0] ??
      data?.detail ??
      data?.name?.[0] ??
      (editingSeasonId.value ? '保存失败' : '创建失败')
  } finally {
    submitLoading.value = false
  }
}

function goToProjects(seasonId) {
  highlightStore.set('Seasons', seasonId)
  router.push({ name: 'SeasonProjects', params: { seasonId } })
}

/** 点击页面任意处时清除行高亮 */
function clearHighlight() {
  if (lastHighlightId.value !== null) {
    lastHighlightId.value = null
  }
}

async function loadSeasons() {
  loading.value = true
  error.value = ''
  try {
    seasons.value = await getSeasons()
    const idSet = new Set(seasons.value.map((item) => item.id))
    selectedSeasonIds.value = selectedSeasonIds.value.filter((id) => idSet.has(id))
  } catch (e) {
    error.value = e.response?.data?.detail ?? '加载测评周期失败'
    seasons.value = []
    selectedSeasonIds.value = []
  } finally {
    loading.value = false
  }
}

useRealtimeRefresh('season', loadSeasons)

onMounted(() => {
  loadSeasons()
  lastHighlightId.value = highlightStore.pop('Seasons')
})
</script>
