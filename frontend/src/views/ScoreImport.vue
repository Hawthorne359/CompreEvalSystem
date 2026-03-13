<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <!-- 面包屑 -->
    <div class="flex items-center gap-2">
      <router-link :to="{ name: 'Review' }" class="text-slate-600 hover:text-slate-900">审核任务</router-link>
      <span class="text-slate-400">/</span>
      <h2 class="text-xl font-semibold text-slate-800">批量导入成绩</h2>
    </div>

    <!-- 流程说明 -->
    <div class="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
      <p class="font-medium">导入流程（必须按步骤操作）</p>
      <ol class="mt-1 list-decimal list-inside text-xs space-y-1">
        <li>选择测评周期和测评项目，下载导入模板，按模板格式填写成绩。</li>
        <li>选择填写好的 Excel 文件后，必须先点「预检」，系统检查权限范围与数据格式。</li>
        <li>预检完成后查看结果，对每条错误/警告可点「排除此行」跳过该行。</li>
        <li>无阻断性错误（或已全部排除）后，点「确认导入」正式写入数据库。</li>
      </ol>
    </div>

    <!-- 导入表单 -->
    <div class="rounded border border-slate-200 bg-white p-6 space-y-5">
      <h3 class="text-base font-medium text-slate-800">上传 Excel 文件</h3>

      <!-- 第一步：选择测评周期 -->
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">测评周期</label>
        <select
          v-model="selectedSeason"
          class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none sm:w-80"
        >
          <option :value="null" disabled>请选择周期</option>
          <option v-for="s in seasonOptions" :key="s.id" :value="s.id">
            {{ s.name }}
            <template v-if="s.status === 'closed'">（已结束）</template>
            <template v-else-if="s.status === 'draft'">（草稿）</template>
          </option>
        </select>
        <p v-if="seasonsLoading" class="mt-1 text-xs text-slate-500">加载周期列表…</p>
      </div>

      <!-- 第二步：选择测评项目（依赖周期） -->
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">测评项目</label>
        <select
          v-model="selectedProject"
          :disabled="!selectedSeason || projectsLoading"
          class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100 sm:w-96"
        >
          <option :value="null" disabled>{{ selectedSeason ? '请选择项目' : '请先选择周期' }}</option>
          <option
            v-for="p in projectOptions"
            :key="p.id"
            :value="p.id"
            :disabled="p.status === 'closed'"
            :class="p.status === 'closed' ? 'text-slate-400' : ''"
          >
            {{ p.name }}{{ p.status === 'closed' ? '（已结束）' : p.status === 'draft' ? '（草稿）' : '' }}
          </option>
        </select>
        <p v-if="projectsLoading" class="mt-1 text-xs text-slate-500">加载项目列表…</p>
        <p v-if="selectedSeason && !projectsLoading && projectOptions.length === 0" class="mt-1 text-xs text-slate-500">
          该周期暂无项目。
        </p>
      </div>

      <!-- 统一导入配置只读展示 -->
      <div v-if="selectedProject" class="rounded border border-slate-200 bg-slate-50 p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-sm font-medium text-slate-800">统一导入配置（只读，来源于项目指标设置）</h4>
          <button
            type="button"
            class="rounded border border-slate-300 px-2.5 py-1 text-xs text-slate-700 hover:bg-white disabled:opacity-50"
            :disabled="configLoading"
            @click="loadProjectImportConfig"
          >
            {{ configLoading ? '加载中…' : '刷新配置' }}
          </button>
        </div>
        <p class="text-xs text-slate-600">
          以下为本项目中标记为"统一导入"的指标，下载模板后按列填写对应指标分数即可。
        </p>

        <!-- 可统一导入指标树（支持任意深度嵌套） -->
        <div v-if="importableIndicators.length" class="space-y-2">
          <div
            v-for="group in flatImportGroups"
            :key="group.id"
            class="rounded border border-slate-200 bg-white px-3 py-2 text-xs"
          >
            <div class="flex items-center gap-2 font-medium text-slate-800">
              <span v-if="group.category" class="rounded bg-blue-100 px-1.5 py-0.5 text-blue-700">{{ group.category }}</span>
              <span>{{ group.name }}</span>
              <template v-if="group.is_import">
                <span v-if="group.max_score != null" class="text-slate-500 font-normal">满分 {{ group.max_score }}</span>
                <span v-else class="text-slate-400 font-normal">无上限</span>
                <span class="rounded bg-emerald-100 px-1.5 py-0.5 text-emerald-700 font-normal">统一导入</span>
              </template>
            </div>
            <div v-if="group.flatChildren.length" class="mt-2 space-y-1">
              <div
                v-for="item in group.flatChildren"
                :key="item.id"
                class="flex items-center gap-2 text-slate-700"
                :style="{ paddingLeft: (item.depth * 16) + 'px' }"
              >
                <span class="text-slate-400">└─</span>
                <span class="font-medium">{{ item.name }}</span>
                <template v-if="item.is_import">
                  <span v-if="item.max_score != null" class="text-slate-500">满分 {{ item.max_score }}</span>
                  <span v-else class="text-slate-400">无上限</span>
                  <span class="rounded bg-emerald-100 px-1.5 py-0.5 text-emerald-700">统一导入</span>
                </template>
              </div>
            </div>
          </div>
        </div>
        <p v-else-if="!configLoading" class="text-xs text-slate-500">
          该项目暂无标记为"统一导入"的指标，无法使用批量导入功能。
        </p>
        <p v-if="configError" class="text-xs text-red-600">{{ configError }}</p>
      </div>

      <!-- 选择文件 -->
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Excel 文件</label>
        <input
          ref="fileInputRef"
          type="file"
          accept=".xlsx,.xls"
          class="rounded border border-slate-300 text-sm text-slate-800"
          @change="onFileChange"
        />
        <p v-if="selectedFile" class="mt-1 text-xs text-slate-500">已选择: {{ selectedFile.name }}</p>
      </div>

      <!-- 操作按钮区（强制预检流程，无 preview_token 则「确认导入」禁用） -->
      <div class="flex items-center gap-3 flex-wrap">
        <button
          type="button"
          class="app-btn app-btn-primary disabled:opacity-50"
          :disabled="!selectedProject || !selectedFile || precheckLoading || uploading"
          @click="doPrecheck"
        >
          {{ precheckLoading ? '检查中…' : '预检' }}
        </button>
        <button
          type="button"
          class="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
          :disabled="uploading || precheckLoading || !previewToken || precheckHasBlockingErrors"
          :title="!previewToken ? '请先完成预检' : precheckHasBlockingErrors ? '存在阻断性错误，请排除问题行后重新预检' : ''"
          @click="doCommit"
        >
          {{ uploading ? '导入中…' : '确认导入' }}
        </button>
        <button
          type="button"
          class="rounded border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          :disabled="!selectedProject || templateDownloading"
          @click="doDownloadTemplate"
        >
          {{ templateDownloading ? '生成中…' : '下载导入模板' }}
        </button>
      </div>

      <!-- 状态提示 -->
      <div class="space-y-1">
        <p v-if="!previewToken && !precheckLoading && selectedFile" class="text-xs text-amber-600">
          请先点「预检」，验证通过后方可确认导入。
        </p>
        <p v-if="previewToken && precheckHasBlockingErrors" class="text-xs text-red-600">
          预检存在 {{ blockingErrorCount }} 条阻断性错误（未排除），请排除这些行或修正 Excel 后重新预检。
        </p>
        <p v-if="previewToken && !precheckHasBlockingErrors" class="text-xs text-emerald-700">
          预检通过，可点「确认导入」正式写入数据库。
          <span v-if="excludedRows.size > 0">（已排除 {{ excludedRows.size }} 行）</span>
        </p>
        <p v-if="precheckError" class="text-xs text-red-600">{{ precheckError }}</p>
        <p v-if="uploadError" class="text-xs text-red-600">{{ uploadError }}</p>
        <p v-if="templateError" class="text-xs text-red-600">{{ templateError }}</p>
      </div>
    </div>

    <!-- 预检结果（含行级排除操作） -->
    <div
      v-if="precheckResult"
      class="rounded border p-4 space-y-4"
      :class="precheckHasBlockingErrors ? 'border-red-300 bg-red-50' : precheckResult.warnings.length ? 'border-amber-300 bg-amber-50' : 'border-emerald-300 bg-emerald-50'"
    >
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium"
          :class="precheckHasBlockingErrors ? 'text-red-700' : precheckResult.warnings.length ? 'text-amber-700' : 'text-emerald-700'"
        >
          预检结果
        </span>
        <span class="text-xs text-slate-600">
          共 {{ precheckResult.total_rows }} 行数据
          <span v-if="excludedRows.size > 0">，已排除 {{ excludedRows.size }} 行</span>
          <span v-if="previewToken && !precheckHasBlockingErrors">，将导入 {{ precheckResult.total_rows - excludedRows.size }} 行</span>
        </span>
      </div>

      <!-- 阻断性错误（含行级排除） -->
      <div v-if="precheckResult.errors.length" class="space-y-1">
        <p class="text-xs font-medium text-red-700">
          阻断性错误（{{ precheckResult.errors.length }} 条）：可点「排除此行」跳过，全部排除后方可确认导入。
        </p>
        <div class="max-h-48 overflow-y-auto rounded border border-red-200 bg-white">
          <table class="min-w-full border-collapse text-xs">
            <thead>
              <tr class="border-b border-red-200">
                <th class="px-3 py-1.5 text-left font-medium text-red-700 w-14">行号</th>
                <th class="px-3 py-1.5 text-left font-medium text-red-700">错误信息</th>
                <th class="px-3 py-1.5 text-left font-medium text-red-700 w-20">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(e, idx) in precheckResult.errors"
                :key="idx"
                class="border-b border-red-100"
                :class="e.row && excludedRows.has(e.row) ? 'opacity-40' : ''"
              >
                <td class="px-3 py-1 text-red-800">{{ e.row ?? '—' }}</td>
                <td class="px-3 py-1 text-red-700" :class="e.row && excludedRows.has(e.row) ? 'line-through' : ''">{{ e.message }}</td>
                <td class="px-3 py-1">
                  <button
                    v-if="e.row && !excludedRows.has(e.row)"
                    type="button"
                    class="rounded border border-red-300 px-1.5 py-0.5 text-xs text-red-700 hover:bg-red-100"
                    @click="toggleExcludeRow(e.row)"
                  >排除此行</button>
                  <button
                    v-else-if="e.row && excludedRows.has(e.row)"
                    type="button"
                    class="rounded border border-slate-300 px-1.5 py-0.5 text-xs text-slate-500 hover:bg-slate-100"
                    @click="toggleExcludeRow(e.row)"
                  >撤销排除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 非阻断警告（含行级排除） -->
      <div v-if="precheckResult.warnings.length" class="space-y-1">
        <p class="text-xs font-medium text-amber-700">
          警告（{{ precheckResult.warnings.length }} 条，不影响导入但请确认）：
        </p>
        <div class="max-h-40 overflow-y-auto rounded border border-amber-200 bg-white">
          <table class="min-w-full border-collapse text-xs">
            <thead>
              <tr class="border-b border-amber-200">
                <th class="px-3 py-1.5 text-left font-medium text-amber-700 w-14">行号</th>
                <th class="px-3 py-1.5 text-left font-medium text-amber-700">提示</th>
                <th class="px-3 py-1.5 text-left font-medium text-amber-700 w-20">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(w, idx) in precheckResult.warnings"
                :key="idx"
                class="border-b border-amber-100"
                :class="w.row && excludedRows.has(w.row) ? 'opacity-40' : ''"
              >
                <td class="px-3 py-1 text-amber-800">{{ w.row ?? '—' }}</td>
                <td class="px-3 py-1 text-amber-700" :class="w.row && excludedRows.has(w.row) ? 'line-through' : ''">{{ w.message }}</td>
                <td class="px-3 py-1">
                  <button
                    v-if="w.row && !excludedRows.has(w.row)"
                    type="button"
                    class="rounded border border-amber-300 px-1.5 py-0.5 text-xs text-amber-700 hover:bg-amber-100"
                    @click="toggleExcludeRow(w.row)"
                  >排除此行</button>
                  <button
                    v-else-if="w.row && excludedRows.has(w.row)"
                    type="button"
                    class="rounded border border-slate-300 px-1.5 py-0.5 text-xs text-slate-500 hover:bg-slate-100"
                    @click="toggleExcludeRow(w.row)"
                  >撤销排除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <p v-if="!precheckResult.has_errors && !precheckResult.warnings.length" class="text-xs text-emerald-700">
        预检通过，所有 {{ precheckResult.total_rows }} 行数据均在权限范围内，可直接确认导入。
      </p>
    </div>

    <!-- 导入结果 -->
    <div v-if="importResult" class="rounded border border-slate-200 bg-white p-6 space-y-4">
      <h3 class="text-base font-medium text-slate-800">导入结果</h3>
      <dl class="grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
        <div>
          <dt class="text-slate-500">文件名</dt>
          <dd class="text-slate-800">{{ importResult.file_name }}</dd>
        </div>
        <div>
          <dt class="text-slate-500">状态</dt>
          <dd>
            <span
              class="rounded px-2 py-0.5 text-xs"
              :class="importResult.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
            >
              {{ importResult.status === 'completed' ? '导入成功' : '导入失败' }}
            </span>
          </dd>
        </div>
        <div>
          <dt class="text-slate-500">总行数</dt>
          <dd class="text-slate-800">{{ importResult.row_count ?? '—' }}</dd>
        </div>
      </dl>

      <template v-if="importResult.error_log?.length">
        <h4 class="text-sm font-medium text-red-700">错误详情（{{ importResult.error_log.length }} 条）</h4>
        <div class="max-h-64 overflow-y-auto rounded border border-red-200 bg-red-50">
          <table class="min-w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-red-200">
                <th class="px-3 py-2 text-left font-medium text-red-700">行号</th>
                <th class="px-3 py-2 text-left font-medium text-red-700">错误信息</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(err, idx) in importResult.error_log" :key="idx" class="border-b border-red-100">
                <td class="px-3 py-1.5 text-red-800">{{ err.row ?? '—' }}</td>
                <td class="px-3 py-1.5 text-red-700">{{ err.message }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <p v-else class="text-sm text-green-600">全部行导入成功，无错误。</p>
    </div>
  </div>
</template>

<script setup>
/**
 * 批量导入成绩：强制预检 → 确认导入两步流程，支持行级排除。
 * 流程：选周期 → 选项目 → 下载模板 → 选文件 → 「预检」→ 查看/排除错误行 → 「确认导入」。
 * 接口（预检）：POST /api/v1/scoring/import/precheck/
 * 接口（导入）：POST /api/v1/scoring/import/（携带 preview_token + excluded_rows）
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { getSeasons, getSeasonProjects, getProjectImportConfig } from '@/api/eval'
import { downloadImportTemplate, precheckImport, commitScoreImport } from '@/api/review'

/** 周期列表 */
const seasonOptions = ref([])
const seasonsLoading = ref(false)
const selectedSeason = ref(null)

/** 项目列表（依赖周期） */
const projectOptions = ref([])
const projectsLoading = ref(false)
const selectedProject = ref(null)

/** 当前选中的项目对象 */
const selectedProjectObj = computed(() => projectOptions.value.find((p) => p.id === selectedProject.value) ?? null)

const selectedFile = ref(null)
const fileInputRef = ref(null)

/** 预检相关 */
const precheckLoading = ref(false)
const precheckError = ref('')
/** @type {import('vue').Ref<{total_rows:number,errors:Array,warnings:Array,has_errors:boolean,preview_token:string|null}|null>} */
const precheckResult = ref(null)
/** preview_token：预检通过后由后端返回，确认导入时携带 */
const previewToken = ref('')

/** 行级排除集合：存放用户手动标记为"排除"的行号 */
const excludedRows = ref(new Set())

/** 导入相关 */
const uploading = ref(false)
const uploadError = ref('')
const importResult = ref(null)

const templateDownloading = ref(false)
const templateError = ref('')

/** 可统一导入的指标树 */
const importableIndicators = ref([])
const configLoading = ref(false)
const configError = ref('')

/**
 * 将嵌套树扁平化用于模板渲染，每个节点带 depth 表示缩进层级。
 */
const flatImportGroups = computed(() => {
  return importableIndicators.value.map(group => {
    const items = []
    function walk(nodes, depth) {
      for (const node of nodes) {
        items.push({ id: node.id, name: node.name, max_score: node.max_score, is_import: node.is_import, depth })
        if (node.children?.length) walk(node.children, depth + 1)
      }
    }
    if (group.children?.length) walk(group.children, 1)
    return { ...group, flatChildren: items }
  })
})

/**
 * 切换某行的排除状态。
 * @param {number} rowNum
 */
function toggleExcludeRow(rowNum) {
  const s = new Set(excludedRows.value)
  if (s.has(rowNum)) {
    s.delete(rowNum)
  } else {
    s.add(rowNum)
  }
  excludedRows.value = s
}

/**
 * 预检结果中是否还存在未被排除的阻断性错误。
 */
const precheckHasBlockingErrors = computed(() => {
  if (!precheckResult.value) return false
  const errors = precheckResult.value.errors ?? []
  return errors.some((e) => !e.row || !excludedRows.value.has(e.row))
})

/** 未被排除的阻断性错误数 */
const blockingErrorCount = computed(() => {
  if (!precheckResult.value) return 0
  const errors = precheckResult.value.errors ?? []
  return errors.filter((e) => !e.row || !excludedRows.value.has(e.row)).length
})

function onFileChange(e) {
  selectedFile.value = e.target?.files?.[0] || null
  // 换文件后清空上次预检状态
  precheckResult.value = null
  precheckError.value = ''
  previewToken.value = ''
  excludedRows.value = new Set()
  uploadError.value = ''
}

/** 加载测评周期列表 */
async function loadSeasons() {
  seasonsLoading.value = true
  try {
    const data = await getSeasons()
    seasonOptions.value = Array.isArray(data) ? data : []
  } catch {
    seasonOptions.value = []
  } finally {
    seasonsLoading.value = false
  }
}

/** 加载当前周期下的项目列表 */
async function loadProjects(seasonId) {
  projectsLoading.value = true
  projectOptions.value = []
  selectedProject.value = null
  try {
    const data = await getSeasonProjects(seasonId)
    projectOptions.value = Array.isArray(data) ? data : []
  } catch {
    projectOptions.value = []
  } finally {
    projectsLoading.value = false
  }
}

/**
 * 执行导入预检：不写库，返回权限/格式检查结果和 preview_token。
 */
async function doPrecheck() {
  if (!selectedProject.value || !selectedFile.value) return
  precheckLoading.value = true
  precheckError.value = ''
  precheckResult.value = null
  previewToken.value = ''
  excludedRows.value = new Set()
  try {
    const formData = new FormData()
    formData.append('project_id', selectedProject.value)
    formData.append('file', selectedFile.value)
    const result = await precheckImport(formData)
    precheckResult.value = result
    // 预检通过时后端会返回 preview_token
    previewToken.value = result.preview_token || ''
  } catch (e) {
    precheckError.value = e.response?.data?.detail ?? '预检失败，请稍后重试'
  } finally {
    precheckLoading.value = false
  }
}

/**
 * 确认导入：携带 preview_token 和 excluded_rows 正式写库（两阶段提交）。
 */
async function doCommit() {
  if (!previewToken.value || !selectedProject.value) return
  uploading.value = true
  uploadError.value = ''
  importResult.value = null
  try {
    importResult.value = await commitScoreImport({
      projectId: selectedProject.value,
      previewToken: previewToken.value,
      excludedRows: Array.from(excludedRows.value),
    })
    selectedFile.value = null
    previewToken.value = ''
    precheckResult.value = null
    excludedRows.value = new Set()
    if (fileInputRef.value) fileInputRef.value.value = ''
  } catch (e) {
    const data = e.response?.data
    if (data?.batch) {
      importResult.value = data.batch
      uploadError.value = data.detail || '导入过程中出现错误'
    } else {
      uploadError.value = data?.detail ?? '导入失败'
    }
  } finally {
    uploading.value = false
  }
}

/** 下载当前项目的导入模板 */
async function doDownloadTemplate() {
  if (!selectedProject.value) return
  templateDownloading.value = true
  templateError.value = ''
  try {
    const proj = selectedProjectObj.value
    await downloadImportTemplate(selectedProject.value, proj?.name ?? String(selectedProject.value))
  } catch (e) {
    templateError.value = e.response?.data?.detail ?? '模板下载失败，请稍后重试'
  } finally {
    templateDownloading.value = false
  }
}

/**
 * 加载项目导入配置，从后端获取可统一导入的指标树。
 */
async function loadProjectImportConfig() {
  if (!selectedProject.value) return
  configLoading.value = true
  configError.value = ''
  try {
    const data = await getProjectImportConfig(selectedProject.value)
    importableIndicators.value = Array.isArray(data.importable_indicators) ? data.importable_indicators : []
  } catch (e) {
    configError.value = e.response?.data?.detail ?? '加载导入配置失败'
  } finally {
    configLoading.value = false
  }
}

onMounted(() => {
  loadSeasons()
})

useRealtimeRefresh(['season', 'project'], loadSeasons)

/** 切换周期时重置项目和预检状态 */
watch(selectedSeason, (val) => {
  selectedProject.value = null
  projectOptions.value = []
  importableIndicators.value = []
  configError.value = ''
  precheckResult.value = null
  previewToken.value = ''
  excludedRows.value = new Set()
  if (val) loadProjects(val)
})

/** 切换项目时重置预检状态，并加载导入配置 */
watch(selectedProject, () => {
  importableIndicators.value = []
  configError.value = ''
  precheckResult.value = null
  previewToken.value = ''
  excludedRows.value = new Set()
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
  if (!selectedProject.value) return
  loadProjectImportConfig()
})
</script>
