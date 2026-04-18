<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/35 p-4">
    <div class="flex max-h-[94vh] w-full max-w-[1320px] flex-col rounded-3xl border border-white/70 bg-white/75 shadow-2xl backdrop-blur">
      <header class="flex items-center justify-between border-b border-white/60 px-6 py-4">
        <div>
          <h3 class="text-lg font-semibold text-slate-900">导出模板与映射配置</h3>
          <p class="mt-0.5 text-xs text-slate-600">先选任务，再选映射，再配字段，最后保存并导出</p>
        </div>
        <button type="button" class="rounded-lg px-3 py-1.5 text-sm text-slate-600 hover:bg-white/70 hover:text-slate-900" @click="requestCloseWorkspace">
          关闭
        </button>
      </header>

      <div class="grid flex-1 min-h-0 grid-cols-12 gap-4 overflow-hidden p-4">
        <div class="col-span-12 min-h-0 overflow-y-auto xl:col-span-3">
          <TaskSidebar
            :active-task-type="activeTaskType"
            :word-pdf-format="wordPdfFormat"
            @update:active-task-type="handleTaskTypeChange"
            @update:word-pdf-format="handleWordPdfFormatChange"
          />
          <div class="mt-4">
            <ExportReviewPanel
              :task-type="activeTaskType"
              :word-pdf-format="wordPdfFormat"
              :mapping-name="mappingDraft.name"
              :template-name="selectedTemplateName"
              :excel-column-count="mappingDraft.config.excel_columns?.length || 0"
              :word-placeholder-count="mappingDraft.config.word_placeholders?.length || 0"
              :computed-field-count="computedVirtualFields.length"
              :word-usable-computed-count="computedVirtualFields.length"
              :multi-file="configExportGroupFileMode === 'per_student_file'"
              :group-by="configExportGroupBy"
              :group-file-mode="configExportGroupFileMode"
              :allowed-group-by-options="allowedGroupByOptions"
              :reviewer-signature-source="mappingDraft.config.reviewer_signature_policy?.source || 'actual_scored'"
              :include-arbitration-in-signature="!!mappingDraft.config.reviewer_signature_policy?.include_arbitration"
              :saving="savingMapping"
              :exporting="exporting"
              :notice="configNotice"
              :error="configError"
              @save="saveMapping"
              @export="doConfiguredExport"
              @update:multi-file="(v) => (configExportGroupFileMode = v ? 'per_student_file' : 'single_file')"
              @update:group-by="(v) => (configExportGroupBy = v)"
              @update:group-file-mode="(v) => (configExportGroupFileMode = v)"
              @update:reviewer-signature-source="(v) => {
                mappingDraft.config.reviewer_signature_policy.source = v
                if (v !== 'actual_scored') mappingDraft.config.reviewer_signature_policy.include_arbitration = false
              }"
              @update:include-arbitration-in-signature="(v) => (mappingDraft.config.reviewer_signature_policy.include_arbitration = !!v)"
            />
          </div>
        </div>

        <div class="col-span-12 min-h-0 space-y-4 overflow-y-auto xl:col-span-9">
          <MappingPanel
            :mapping-list="taskScopedMappings"
            :selected-mapping-id="selectedMappingId"
            :draft="mappingDraft"
            @new="handleCreateNewMapping"
            @save-as="handleSaveAsNewMapping"
            @select="handleSelectMapping"
            @update:name="(v) => (mappingDraft.name = v)"
            @update:is-default="(v) => (mappingDraft.is_default = v)"
          />

          <TemplatePanel
            :templates="templateList"
            :selected-template-id="selectedTemplateId"
            :template-form="templateForm"
            :task-template-type="taskTemplateType"
            :uploading-template="uploadingTemplate"
            :file-input-key="templateFileInputKey"
            :is-director-or-admin="isDirectorOrAdmin"
            @update:name="(v) => (templateForm.name = v)"
            @update:type="(v) => (templateForm.template_type = v)"
            @update:visibility="(v) => (templateForm.visibility = v)"
            @pick-file="onTemplateFileChange"
            @upload="uploadTemplate"
            @select-template="(id) => (selectedTemplateId = id)"
            @rename-template="renameTemplate"
            @delete-template="removeTemplate"
          />

          <section class="rounded-2xl border border-white/70 bg-white/85 shadow-sm">
            <div class="flex border-b border-slate-200 px-4 pt-3">
              <button
                v-for="tab in editTabs"
                :key="tab.id"
                type="button"
                class="mr-4 border-b-2 pb-2 text-sm font-medium"
                :class="editorTab === tab.id ? 'border-brand-600 text-brand-700' : 'border-transparent text-slate-500 hover:text-slate-800'"
                @click="editorTab = tab.id"
              >
                {{ tab.label }}
              </button>
            </div>

            <div v-show="editorTab === 'fields'" class="p-4">
              <div class="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
                <input v-model.trim="fieldKeyword" type="text" class="w-56 rounded border px-2 py-1.5 text-sm" placeholder="搜索字段名称/编码…" />
                <label class="flex items-center gap-1.5 text-xs text-slate-600">
                  <input v-model="showAdvancedFields" type="checkbox" />
                  显示全部字段（含导入/评审/仲裁）
                </label>
                <button
                  type="button"
                  class="rounded border border-brand-500 px-2 py-1.5 text-xs text-brand-700 hover:bg-brand-50"
                  @click="addAllProjectCommonFieldsToCurrentTarget"
                >
                  一键加入全部常用
                </button>
                <button
                  type="button"
                  class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-700 hover:bg-white"
                  @click="clearFieldSelection"
                >
                  清空已选
                </button>
              </div>

              <div class="mt-3 rounded-lg border border-slate-200 bg-white">
                <div v-if="summaryFields.length > 0" class="border-b border-slate-200">
                  <div class="flex items-center justify-between bg-slate-700 px-4 py-2 text-white">
                    <span class="text-sm font-semibold">综合汇总字段</span>
                    <span class="text-xs text-white/75">{{ summaryFields.length }} 个</span>
                  </div>
                  <div class="divide-y divide-slate-100">
                    <button
                      v-for="f in summaryFields"
                      :key="f.key"
                      type="button"
                      class="flex w-full items-center justify-between px-4 py-1.5 text-left text-sm hover:bg-slate-50"
                      :class="selectedFieldKeys.has(f.key) ? 'bg-brand-50' : ''"
                      @click="onTreeToggleField(f.key)"
                    >
                      <span class="flex min-w-0 items-center gap-2">
                        <span
                          v-if="f.is_common"
                          class="rounded bg-green-100 px-1 text-xs text-green-700"
                        >常用</span>
                        <span class="truncate text-slate-700">{{ f.label }}</span>
                      </span>
                      <span class="ml-2 flex shrink-0 items-center gap-1">
                        <button
                          type="button"
                          class="rounded px-1 py-0.5 text-xs"
                          :class="f.is_common ? 'bg-amber-100 text-amber-700 hover:bg-amber-200' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'"
                          @click.stop="toggleFieldCommonPreference(f.key)"
                        >{{ f.is_common ? '取消常用' : '设为常用' }}</button>
                        <code class="rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-500">{{ f.key }}</code>
                      </span>
                    </button>
                  </div>
                </div>

                <div v-if="computedVirtualFields.length > 0" class="border-b border-slate-200">
                  <div class="flex items-center justify-between bg-violet-700 px-4 py-2 text-white">
                    <span class="text-sm font-semibold">自定义统计字段</span>
                    <span class="text-xs text-white/75">{{ computedVirtualFields.length }} 个</span>
                  </div>
                  <div class="divide-y divide-slate-100">
                    <button
                      v-for="f in computedVirtualFields"
                      :key="f.key"
                      type="button"
                      class="flex w-full items-center justify-between px-4 py-1.5 text-left text-sm hover:bg-violet-50"
                      :class="selectedFieldKeys.has(f.key) ? 'bg-violet-50' : ''"
                      @click="onTreeToggleField(f.key)"
                    >
                      <span class="flex min-w-0 items-center gap-2">
                        <span class="rounded bg-violet-100 px-1 text-xs text-violet-700">统计</span>
                        <span class="truncate text-slate-700">{{ f.label }}</span>
                      </span>
                      <code class="rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-500">{{ f.key }}</code>
                    </button>
                  </div>
                </div>

                <ExportFieldTreeNode
                  v-for="rootNode in filteredFieldTree"
                  :key="rootNode.id"
                  :node="rootNode"
                  :depth="0"
                  :selected-keys="selectedFieldKeys"
                  @toggle-field="onTreeToggleField"
                  @add-common="addAllNodeCommonFields"
                  @toggle-common="toggleFieldCommonPreference"
                />
                <p v-if="filteredFieldTree.length === 0" class="py-8 text-center text-sm text-slate-400">暂无匹配字段</p>
              </div>

              <div class="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                <span class="text-sm text-slate-600">已选 <b class="text-brand-700">{{ selectedFieldKeys.size }}</b> 个字段</span>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="rounded border border-slate-300 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-white disabled:opacity-40"
                    :disabled="selectedFieldKeys.size === 0"
                    @click="batchAddToExcelColumns"
                  >
                    加入 Excel 列
                  </button>
                  <button
                    type="button"
                    class="rounded border border-slate-300 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-white disabled:opacity-40"
                    :disabled="selectedFieldKeys.size === 0"
                    @click="batchAddToWordPlaceholders"
                  >
                    加入 Word 占位符
                  </button>
                </div>
              </div>
            </div>

            <div v-show="editorTab === 'task'" class="p-4">
              <ExcelMappingEditor
                v-if="activeTaskType === 'xlsx'"
                :config="mappingDraft.config"
                :grouped-display-fields="groupedDisplayFields"
                @add-column="addExcelColumnMapping"
                @remove-column="removeExcelColumnMapping"
                @update-column="updateExcelColumnMapping"
                @add-static="addStaticCellMapping"
                @remove-static="removeStaticCellMapping"
                @update-static="updateStaticCellMapping"
                @add-computed="addComputedField"
                @remove-computed="removeComputedField"
                @update-computed="updateComputedField"
                @update:data-start-row="updateDataStartRow"
                @update:write-header="updateWriteHeader"
              />
              <WordPlaceholderEditor
                v-else
                :config="mappingDraft.config"
                :grouped-display-fields="groupedDisplayFields"
                :format-token-preview="formatTokenPreview"
                :get-field-display-name="getFieldDisplayName"
                @add-row="addWordPlaceholderMapping"
                @remove-row="removeWordPlaceholderMapping"
                @update-row="updateWordPlaceholderMapping"
                @copy="copyTokenPreview"
                @update:zip-pattern="(v) => (mappingDraft.config.zip_filename_pattern = v)"
              />
            </div>
          </section>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  getExportFields,
  getExportCommonFields,
  updateExportCommonFields,
  getExportTemplates,
  createExportTemplate,
  updateExportTemplate,
  deleteExportTemplate,
  getExportMappings,
  createExportMapping,
  updateExportMapping,
  exportReportWithCompat,
} from '@/api/report'
import { openConfirm } from '@/utils/dialog'
import ExportFieldTreeNode from '@/views/ExportFieldTreeNode.vue'
import TaskSidebar from './TaskSidebar.vue'
import MappingPanel from './MappingPanel.vue'
import TemplatePanel from './TemplatePanel.vue'
import ExcelMappingEditor from './ExcelMappingEditor.vue'
import WordPlaceholderEditor from './WordPlaceholderEditor.vue'
import ExportReviewPanel from './ExportReviewPanel.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  projectId: { type: [Number, String], default: '' },
  projectName: { type: String, default: '' },
  isDirectorOrAdmin: { type: Boolean, default: false },
  filterParams: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close', 'mappings-updated'])
const auth = useAuthStore()

const configError = ref('')
const configNotice = ref('')
const exporting = ref(false)
const uploadingTemplate = ref(false)
const savingMapping = ref(false)
const templateFileInputKey = ref(0)

const exportFields = ref([])
const allExportFields = ref([])
const fieldGroups = ref([])
const fieldTree = ref([])

const activeTaskType = ref('xlsx')
const wordPdfFormat = ref('word')
const editorTab = ref('fields')

const selectedFieldKeys = ref(new Set())
const fieldKeyword = ref('')
const showAdvancedFields = ref(false)
const userCommonKeys = ref(new Set())

const templateList = ref([])
const mappingList = ref([])
const selectedTemplateId = ref(null)
const selectedMappingId = ref(null)
const configExportGroupFileMode = ref('single_file')
const configExportGroupBy = ref('')
const writeHeaderTouched = ref(false)
const cleanSnapshot = ref('')

const templateForm = ref({
  name: '',
  template_type: 'excel',
  visibility: 'private',
  file: null,
})

function defaultMappingConfig() {
  return {
    token_mode: 'prefix_token',
    token_prefix: '@',
    field_version: 2,
    field_view_mode: 'template_common_first',
    common_profile_version: 1,
    header_row: 1,
    data_start_row: 2,
    write_header: true,
    static_cells: [],
    excel_columns: [
      { column: 'A', field_key: 'rank', header: '排名' },
      { column: 'B', field_key: 'student_no', header: '学号' },
      { column: 'C', field_key: 'real_name', header: '姓名' },
      { column: 'D', field_key: 'class_name', header: '班级' },
      { column: 'E', field_key: 'final_score', header: '总分' },
    ],
    word_placeholders: [],
    zip_filename_pattern: '',
    computed_fields: [],
    reviewer_signature_policy: {
      source: 'actual_scored',
      include_arbitration: false,
    },
  }
}

function deepClone(value) {
  return JSON.parse(JSON.stringify(value))
}

function makeWorkspaceSnapshot() {
  return JSON.stringify({
    activeTaskType: activeTaskType.value,
    wordPdfFormat: wordPdfFormat.value,
    selectedTemplateId: selectedTemplateId.value,
    selectedMappingId: selectedMappingId.value,
    configExportGroupFileMode: configExportGroupFileMode.value || 'single_file',
    configExportGroupBy: configExportGroupBy.value || '',
    mappingDraft: {
      name: String(mappingDraft.value.name || ''),
      is_default: !!mappingDraft.value.is_default,
      config: deepClone(mappingDraft.value.config || {}),
    },
  })
}

function markWorkspaceClean() {
  cleanSnapshot.value = makeWorkspaceSnapshot()
}

function normalizeMappingConfig(cfg = {}) {
  const fallback = defaultMappingConfig()
  const normalizedStaticCells = Array.isArray(cfg.static_cells)
    ? cfg.static_cells.map((item = {}) => ({
      ...(function normalizeStaticItem() {
        const cell = String(item.cell || '').trim().toUpperCase()
        let fieldKey = String(item.field_key || '').trim()
        let aggregation = String(item.aggregation || 'first').trim()
        const template = String(item.template || '')
        // 兼容旧配置：统一收敛为“单值字段写入(first)”或“模板拼接(template)”
        if (aggregation === 'count') {
          fieldKey = fieldKey || 'scope_valid_submission_count'
          aggregation = 'first'
        } else if (aggregation === 'count_valid_submissions') {
          fieldKey = fieldKey || 'scope_valid_submission_count'
          aggregation = 'first'
        } else if (aggregation === 'count_missing_submissions') {
          fieldKey = fieldKey || 'scope_missing_submission_count'
          aggregation = 'first'
        } else if (aggregation === 'computed' || aggregation === 'first_non_empty') {
          aggregation = 'first'
        } else if (aggregation !== 'first' && aggregation !== 'template') {
          aggregation = 'first'
        }
        if (fieldKey === '_count') fieldKey = 'scope_valid_submission_count'
        return {
          cell,
          field_key: fieldKey,
          aggregation,
          template,
        }
      }()),
    }))
    : []
  const normalizedComputed = Array.isArray(cfg.computed_fields) ? cfg.computed_fields.map((item = {}) => ({
    key: String(item.key || '').trim(),
    fn: String(item.fn || 'count').trim(),
    target: String(item.target || 'valid_rows').trim(),
    field_key: String(item.field_key || '').trim(),
    precision: item.precision === '' || item.precision === null || item.precision === undefined
      ? ''
      : Number(item.precision),
    sep: String(item.sep || '、'),
    role: String(item.role || '').trim(),
  })) : []
  return {
    ...fallback,
    ...cfg,
    static_cells: normalizedStaticCells,
    excel_columns: Array.isArray(cfg.excel_columns) && cfg.excel_columns.length ? cfg.excel_columns : fallback.excel_columns,
    word_placeholders: Array.isArray(cfg.word_placeholders) ? cfg.word_placeholders : [],
    computed_fields: normalizedComputed,
    reviewer_signature_policy: {
      source: String(cfg.reviewer_signature_policy?.source || fallback.reviewer_signature_policy.source),
      include_arbitration: !!cfg.reviewer_signature_policy?.include_arbitration,
    },
  }
}

const mappingDraft = ref({
  name: '',
  is_default: false,
  config: normalizeMappingConfig(),
})

const currentOutputFormat = computed(() => {
  if (activeTaskType.value === 'xlsx') return 'xlsx'
  return wordPdfFormat.value === 'pdf' ? 'pdf' : 'word'
})

const taskTemplateType = computed(() => (activeTaskType.value === 'xlsx' ? 'excel' : 'word'))

const taskScopedMappings = computed(() =>
  (mappingList.value || []).filter((item) => {
    if (activeTaskType.value === 'xlsx') return item.output_format === 'xlsx'
    return item.output_format === 'word' || item.output_format === 'pdf'
  })
)

const selectedTemplateName = computed(() => {
  const hit = (templateList.value || []).find((t) => t.id === selectedTemplateId.value)
  return hit?.name || ''
})

const editTabs = computed(() => [
  { id: 'fields', label: '字段选择' },
  { id: 'task', label: activeTaskType.value === 'xlsx' ? 'Excel 列映射' : 'Word/PDF 占位符' },
])

const hasUnsavedChanges = computed(() => {
  if (!cleanSnapshot.value) return false
  return makeWorkspaceSnapshot() !== cleanSnapshot.value
})

const currentLevel = computed(() => auth.user?.current_role?.level ?? -1)
const allowedGroupByOptions = computed(() => {
  if (currentLevel.value >= 5) return ['class', 'major', 'department']
  if (currentLevel.value >= 3) return ['class', 'major']
  if (currentLevel.value >= 2) return ['class']
  return []
})

const groupedDisplayFields = computed(() => {
  const keyword = fieldKeyword.value.trim().toLowerCase()
  const sourceFields = showAdvancedFields.value
    ? allSelectableFields.value
    : selectedSelectableFields.value
  const groupsMap = new Map((fieldGroups.value || []).map((g) => [g.id, { ...g, fields: [] }]))
  if (!groupsMap.has('computed_custom')) {
    groupsMap.set('computed_custom', {
      id: 'computed_custom',
      label: '自定义统计字段',
      order: 35,
      fields: [],
    })
  }
  for (const field of sourceFields || []) {
    if (keyword) {
      const hit = String(field.label || '').toLowerCase().includes(keyword) || String(field.key || '').toLowerCase().includes(keyword)
      if (!hit) continue
    }
    const gid = field.category_id || 'other'
    if (!groupsMap.has(gid)) groupsMap.set(gid, { id: gid, label: field.category_label || gid, order: 999, fields: [] })
    groupsMap.get(gid).fields.push(field)
  }
  return Array.from(groupsMap.values())
    .filter((g) => g.fields.length > 0)
    .sort((a, b) => (a.order ?? 999) - (b.order ?? 999))
})

const summaryFields = computed(() => {
  const keyword = fieldKeyword.value.trim().toLowerCase()
  return (allSelectableFields.value || []).filter((f) => {
    if (f.category_id !== 'submission' || f.key === 'submission_id') return false
    if (!keyword) return true
    return String(f.label || '').toLowerCase().includes(keyword) || String(f.key || '').toLowerCase().includes(keyword)
  })
})

const computedVirtualFields = computed(() => {
  const rows = mappingDraft.value.config.computed_fields || []
  return rows
    .filter((item) => String(item?.key || '').trim())
    .map((item, idx) => {
      const key = String(item.key || '').trim()
      const fn = String(item.fn || 'count').trim()
      const target = String(item.target || 'valid_rows').trim()
      return {
        key,
        label: `${key}（统计：${fn}/${target}）`,
        category_id: 'computed_custom',
        category_label: '自定义统计字段',
        order: 2000 + idx,
        is_common: true,
      }
    })
})

const allSelectableFields = computed(() => [...(allExportFields.value || []), ...computedVirtualFields.value])
const selectedSelectableFields = computed(() => [...(exportFields.value || []), ...computedVirtualFields.value])

const filteredFieldTree = computed(() => {
  const keyword = fieldKeyword.value.trim().toLowerCase()
  function filterNode(node) {
    const matchedFields = (node.fields || []).filter((f) => {
      if (!keyword) return true
      return String(f.label || '').toLowerCase().includes(keyword) || String(f.key || '').toLowerCase().includes(keyword)
    })
    const filteredChildren = (node.children || []).map(filterNode).filter(Boolean)
    if (matchedFields.length === 0 && filteredChildren.length === 0 && keyword) return null
    return { ...node, fields: matchedFields, children: filteredChildren }
  }
  return (fieldTree.value || []).map(filterNode).filter(Boolean)
})

function markFieldCommonMeta(field) {
  if (!field) return field
  const isUserCommon = userCommonKeys.value.has(field.key)
  const systemFromServer = field.is_system_common
  const isSystemCommon = systemFromServer === undefined ? !!field.is_common : !!systemFromServer
  field.is_user_common = isUserCommon
  field.is_system_common = isSystemCommon
  field.is_common = !!field.is_system_common || !!field.is_user_common
  return field
}

function syncUserCommonFlags() {
  for (const field of exportFields.value || []) markFieldCommonMeta(field)
  for (const field of allExportFields.value || []) markFieldCommonMeta(field)
  function walk(nodes) {
    for (const node of nodes || []) {
      for (const field of node.fields || []) markFieldCommonMeta(field)
      walk(node.children || [])
    }
  }
  walk(fieldTree.value || [])
}

async function confirmDiscardIfNeeded(actionText = '继续操作') {
  if (!hasUnsavedChanges.value) return true
  const result = await openConfirm({
    title: '存在未保存更改',
    message: '当前映射有未保存修改，继续操作会丢失这些更改。是否继续？',
    confirmText: actionText,
    cancelText: '返回编辑',
    danger: true,
  })
  return !!result?.confirmed
}

async function requestCloseWorkspace() {
  const ok = await confirmDiscardIfNeeded('仍要关闭')
  if (!ok) return
  emit('close')
}

async function handleTaskTypeChange(nextTaskType) {
  if (nextTaskType === activeTaskType.value) return
  const ok = await confirmDiscardIfNeeded('切换任务')
  if (!ok) return
  activeTaskType.value = nextTaskType
}

async function handleWordPdfFormatChange(nextFormat) {
  if (nextFormat === wordPdfFormat.value) return
  wordPdfFormat.value = nextFormat
}

async function handleCreateNewMapping() {
  const ok = await confirmDiscardIfNeeded('新建映射')
  if (!ok) return
  createNewMapping(activeTaskType.value)
  markWorkspaceClean()
}

async function handleSaveAsNewMapping() {
  const ok = await confirmDiscardIfNeeded('继续另存为')
  if (!ok) return
  saveAsNewMapping()
}

async function handleSelectMapping(value) {
  const nextId = value ? Number(value) : null
  if (nextId === selectedMappingId.value) return
  const ok = await confirmDiscardIfNeeded('切换映射')
  if (!ok) return
  selectMapping(value)
  markWorkspaceClean()
}

watch(
  () => props.visible,
  (val) => {
    if (val) loadWorkspace()
  }
)

watch(
  () => props.projectId,
  () => {
    if (props.visible) loadWorkspace()
  }
)

watch(allowedGroupByOptions, (allowed) => {
  if (configExportGroupBy.value && !allowed.includes(configExportGroupBy.value)) {
    configExportGroupBy.value = ''
    configNotice.value = '当前角色不支持该分组维度，已自动重置为不分组'
  }
})

watch(activeTaskType, (task) => {
  templateForm.value.template_type = task === 'xlsx' ? 'excel' : 'word'
  if (task === 'xlsx' && configExportGroupFileMode.value === 'per_student_file') {
    configExportGroupFileMode.value = 'single_file'
  }
  if (task === 'xlsx') {
    const prefer = taskScopedMappings.value.find((x) => x.id === selectedMappingId.value) || taskScopedMappings.value[0]
    if (!prefer) {
      createNewMapping('xlsx')
      return
    }
    if (selectedMappingId.value !== prefer.id) {
      selectedMappingId.value = prefer.id
      applySelectedMapping(prefer)
    }
  } else {
    const prefer = taskScopedMappings.value.find((x) => x.id === selectedMappingId.value) || taskScopedMappings.value[0]
    if (!prefer) {
      createNewMapping('word_pdf')
      return
    }
    if (selectedMappingId.value !== prefer.id) {
      selectedMappingId.value = prefer.id
      applySelectedMapping(prefer)
    }
  }
})

watch(selectedTemplateId, (newId) => {
  if (activeTaskType.value !== 'xlsx') return
  if (writeHeaderTouched.value) return
  mappingDraft.value.config.write_header = !newId
})

function setTaskTypeByOutputFormat(outputFormat) {
  if (outputFormat === 'xlsx') {
    activeTaskType.value = 'xlsx'
  } else {
    activeTaskType.value = 'word_pdf'
    wordPdfFormat.value = outputFormat === 'pdf' ? 'pdf' : 'word'
  }
}

async function loadWorkspace() {
  configError.value = ''
  configNotice.value = ''
  if (!props.projectId) return
  selectedFieldKeys.value = new Set()
  editorTab.value = 'fields'
  try {
    const [fieldResp, templates, mappings, prefResp] = await Promise.all([
      getExportFields(props.projectId, { view_mode: 'template_common_first' }),
      getExportTemplates({ project_id: props.projectId }),
      getExportMappings({ project_id: props.projectId }),
      getExportCommonFields(props.projectId),
    ])
    exportFields.value = fieldResp.fields || []
    allExportFields.value = fieldResp.all_fields || fieldResp.fields || []
    fieldGroups.value = fieldResp.field_groups || []
    fieldTree.value = fieldResp.field_tree || []
    userCommonKeys.value = new Set(prefResp?.common_field_keys || fieldResp.user_common_keys || [])
    syncUserCommonFlags()
    templateList.value = templates || []
    mappingList.value = mappings || []
    emit('mappings-updated', mappingList.value)
    bootstrapDefaultSelection()
    markWorkspaceClean()
  } catch (e) {
    configError.value = e.response?.data?.detail ?? '加载导出配置失败'
  }
}

function bootstrapDefaultSelection() {
  if (!mappingList.value.length) {
    createNewMapping(activeTaskType.value)
    return
  }
  const byTaskDefault = taskScopedMappings.value.find((x) => x.is_default) || taskScopedMappings.value[0] || mappingList.value[0]
  if (!byTaskDefault) {
    createNewMapping(activeTaskType.value)
    return
  }
  selectedMappingId.value = byTaskDefault.id
  applySelectedMapping(byTaskDefault)
}

function createNewMapping(taskType = activeTaskType.value) {
  selectedMappingId.value = null
  setTaskTypeByOutputFormat(taskType === 'xlsx' ? 'xlsx' : 'word')
  mappingDraft.value = {
    name: '',
    is_default: false,
    config: normalizeMappingConfig(),
  }
  selectedTemplateId.value = null
  configExportGroupFileMode.value = 'single_file'
  configExportGroupBy.value = ''
  writeHeaderTouched.value = false
  markWorkspaceClean()
}

function saveAsNewMapping() {
  selectedMappingId.value = null
  if (mappingDraft.value.name?.trim()) {
    mappingDraft.value.name = `${mappingDraft.value.name.trim()}_副本`
  }
}

function selectMapping(value) {
  const id = value ? Number(value) : null
  selectedMappingId.value = id
  if (!id) {
    createNewMapping(activeTaskType.value)
    return
  }
  const selected = mappingList.value.find((x) => x.id === id)
  if (!selected) return
  applySelectedMapping(selected)
}

function applySelectedMapping(selected) {
  setTaskTypeByOutputFormat(selected.output_format)
  mappingDraft.value = {
    name: selected.name || '',
    is_default: !!selected.is_default,
    config: normalizeMappingConfig(selected.config),
  }
  ensureExcelColumnsHaveColumnLetters()
  selectedTemplateId.value = selected.template || null
  configExportGroupFileMode.value = 'single_file'
  configExportGroupBy.value = ''
  writeHeaderTouched.value = false
  markWorkspaceClean()
}

function onTemplateFileChange(e) {
  const file = e.target?.files?.[0]
  templateForm.value.file = file || null
}

async function uploadTemplate() {
  configError.value = ''
  if (!props.projectId) return
  if (!templateForm.value.name || !templateForm.value.file) {
    configError.value = '请填写模板名称并选择文件'
    return
  }
  uploadingTemplate.value = true
  try {
    const fd = new FormData()
    fd.append('name', templateForm.value.name)
    fd.append('template_type', templateForm.value.template_type)
    fd.append('visibility', templateForm.value.visibility)
    fd.append('project', props.projectId)
    fd.append('file', templateForm.value.file)
    const created = await createExportTemplate(fd)
    templateList.value.unshift(created)
    selectedTemplateId.value = created.id
    templateForm.value.name = ''
    templateForm.value.file = null
    templateFileInputKey.value += 1
  } catch (e) {
    configError.value = e.response?.data?.detail ?? '模板上传失败'
  } finally {
    uploadingTemplate.value = false
  }
}

async function renameTemplate(item) {
  const currentName = String(item?.name || '').trim()
  const next = window.prompt('请输入新的模板名称', currentName)
  if (next == null) return
  const newName = String(next).trim()
  if (!newName || newName === currentName) return
  try {
    const updated = await updateExportTemplate(item.id, { name: newName })
    const idx = templateList.value.findIndex((x) => x.id === updated.id)
    if (idx >= 0) templateList.value[idx] = updated
    configNotice.value = '模板名称已更新'
  } catch (e) {
    configError.value = e?.response?.data?.detail || '模板重命名失败'
  }
}

async function removeTemplate(item) {
  if (!item?.id) return
  const confirmed = window.confirm(`确认删除模板“${item.name}”吗？`)
  if (!confirmed) return
  try {
    await deleteExportTemplate(item.id)
    templateList.value = (templateList.value || []).filter((x) => x.id !== item.id)
    if (selectedTemplateId.value === item.id) selectedTemplateId.value = null
    configNotice.value = '模板已删除'
  } catch (e) {
    configError.value = e?.response?.data?.detail || '删除模板失败'
  }
}

async function saveMapping() {
  configError.value = ''
  configNotice.value = ''
  if (!props.projectId) return null
  const mappingName = String(mappingDraft.value.name || '').trim()
  if (!mappingName) {
    configError.value = '请填写映射名称'
    return null
  }
  if (taskTemplateType.value === 'word' && !selectedTemplateId.value) {
    configError.value = 'Word/PDF 导出必须先绑定 Word 模板'
    return null
  }
  const validationError = validateMappingDraftBeforeSave()
  if (validationError) {
    configError.value = validationError
    return null
  }
  savingMapping.value = true
  try {
    const payload = {
      name: mappingName,
      project: props.projectId,
      template: selectedTemplateId.value || null,
      output_format: currentOutputFormat.value,
      is_default: !!mappingDraft.value.is_default,
      config: mappingDraft.value.config,
    }
    let saved
    if (selectedMappingId.value) {
      saved = await updateExportMapping(selectedMappingId.value, payload)
      const idx = mappingList.value.findIndex((x) => x.id === saved.id)
      if (idx >= 0) mappingList.value[idx] = saved
    } else {
      saved = await createExportMapping(payload)
      mappingList.value.unshift(saved)
      selectedMappingId.value = saved.id
    }
    emit('mappings-updated', [...mappingList.value])
    configNotice.value = '映射已保存'
    markWorkspaceClean()
    return saved
  } catch (e) {
    configError.value = e.response?.data?.detail ?? '保存映射失败'
    return null
  } finally {
    savingMapping.value = false
  }
}

async function doConfiguredExport() {
  if (!props.projectId) return
  configError.value = ''
  configNotice.value = ''
  if (!selectedMappingId.value) {
    configError.value = '请先保存映射，再执行导出'
    return
  }
  if (configExportGroupBy.value && !allowedGroupByOptions.value.includes(configExportGroupBy.value)) {
    configExportGroupBy.value = ''
    configError.value = '当前角色不支持该分组维度，已自动重置为不分组'
    return
  }
  exporting.value = true
  try {
    await exportReportWithCompat({
      projectId: props.projectId,
      format: currentOutputFormat.value,
      projectName: props.projectName,
      extraParams: {
        mapping_id: selectedMappingId.value,
        group_file_mode: configExportGroupFileMode.value,
        multi_file: configExportGroupFileMode.value === 'per_student_file' ? 'true' : 'false',
        ...(configExportGroupBy.value
          ? { group_by: configExportGroupBy.value }
          : {}),
        ...(props.filterParams || {}),
      },
    })
  } catch (e) {
    configError.value = e?.response?.data?.detail || e?.message || '导出失败'
  } finally {
    exporting.value = false
  }
}

function onTreeToggleField(key, mode) {
  const s = new Set(selectedFieldKeys.value)
  if (mode === 'select') s.add(key)
  else if (mode === 'deselect') s.delete(key)
  else s.has(key) ? s.delete(key) : s.add(key)
  selectedFieldKeys.value = s
}

function clearFieldSelection() {
  selectedFieldKeys.value = new Set()
}

function toExcelColumnIndex(column) {
  const text = String(column || '').trim().toUpperCase()
  if (!/^[A-Z]{1,3}$/.test(text)) return 0
  let value = 0
  for (const ch of text) {
    value = value * 26 + (ch.charCodeAt(0) - 64)
  }
  return value
}

function fromExcelColumnIndex(index) {
  let n = Number(index || 0)
  if (n < 1) n = 1
  let out = ''
  while (n > 0) {
    const rem = (n - 1) % 26
    out = String.fromCharCode(65 + rem) + out
    n = Math.floor((n - 1) / 26)
  }
  return out || 'A'
}

function nextExcelColumnLabel() {
  const rows = mappingDraft.value.config.excel_columns || []
  const maxIdx = rows.reduce((max, row) => {
    const idx = toExcelColumnIndex(row?.column)
    return idx > max ? idx : max
  }, 0)
  return fromExcelColumnIndex(maxIdx + 1)
}

function ensureExcelColumnsHaveColumnLetters() {
  const rows = mappingDraft.value.config.excel_columns || []
  let cursor = 0
  for (const row of rows) {
    const current = toExcelColumnIndex(row?.column)
    if (current > 0) {
      cursor = Math.max(cursor, current)
      row.column = String(row.column || '').trim().toUpperCase()
      continue
    }
    cursor += 1
    row.column = fromExcelColumnIndex(cursor)
  }
}

function appendExcelColumnMapping(fieldKey = '', header = '') {
  ensureExcelColumnsHaveColumnLetters()
  const column = nextExcelColumnLabel()
  mappingDraft.value.config.excel_columns.push({ column, field_key: fieldKey, header })
}

function appendExcelFieldMapping(fieldKey) {
  const exists = (mappingDraft.value.config.excel_columns || []).some((row) => row.field_key === fieldKey)
  if (exists) return false
  appendExcelColumnMapping(fieldKey, getFieldDisplayName(fieldKey))
  return true
}

function batchAddToExcelColumns() {
  ensureExcelColumnsHaveColumnLetters()
  let added = 0
  for (const key of selectedFieldKeys.value) {
    if (appendExcelFieldMapping(key)) added += 1
  }
  selectedFieldKeys.value = new Set()
  configNotice.value = added > 0 ? `已加入 ${added} 个字段到 Excel 列映射` : '所选字段已存在，无需重复加入'
}

function batchAddToWordPlaceholders() {
  let added = 0
  for (const key of selectedFieldKeys.value) {
    if (addFieldToPlaceholder(key)) added += 1
  }
  selectedFieldKeys.value = new Set()
  configNotice.value = added > 0 ? `已加入 ${added} 个占位符` : '所选字段已存在，无需重复加入'
}

function addFieldToPlaceholder(fieldKey) {
  const rows = mappingDraft.value.config.word_placeholders || []
  const token = fieldKey
  const exists = rows.some((r) => r.field_key === fieldKey || String(r.placeholder || '').trim() === token)
  if (exists) return false
  rows.push({ placeholder: token, field_key: fieldKey })
  mappingDraft.value.config.word_placeholders = rows
  return true
}

function collectCommonKeysFromNode(node) {
  const keySet = new Set()
  function collect(n) {
    for (const f of n.fields || []) {
      if (f.is_common || f.split_type === 'agg_score') keySet.add(f.key)
    }
    for (const child of n.children || []) collect(child)
  }
  collect(node)
  return Array.from(keySet)
}

function addAllNodeCommonFields(node) {
  const commonKeys = collectCommonKeysFromNode(node)
  if (commonKeys.length === 0) {
    configNotice.value = '该节点下没有可加入的常用字段'
    return
  }
  if (activeTaskType.value === 'xlsx') {
    ensureExcelColumnsHaveColumnLetters()
    let added = 0
    for (const key of commonKeys) {
      if (appendExcelFieldMapping(key)) added += 1
    }
    configNotice.value = added > 0 ? `已加入 ${added} 个常用字段到 Excel 列映射` : '该节点常用字段已全部存在于 Excel 映射'
    return
  }
  let added = 0
  for (const key of commonKeys) {
    if (addFieldToPlaceholder(key)) added += 1
  }
  configNotice.value = added > 0 ? `已加入 ${added} 个常用字段到 Word 占位符` : '该节点常用字段已全部存在于 Word 占位符'
}

function addAllProjectCommonFieldsToCurrentTarget() {
  const commonKeys = Array.from(new Set(
    (allSelectableFields.value || [])
      .filter((f) => f.is_common || f.split_type === 'agg_score')
      .map((f) => f.key)
  ))
  if (activeTaskType.value === 'xlsx') {
    ensureExcelColumnsHaveColumnLetters()
    let added = 0
    for (const key of commonKeys) {
      if (appendExcelFieldMapping(key)) added += 1
    }
    configNotice.value = added > 0 ? `已加入 ${added} 个常用字段到 Excel 列映射` : '常用字段已全部存在于 Excel 映射'
    return
  }
  let added = 0
  for (const key of commonKeys) {
    if (addFieldToPlaceholder(key)) added += 1
  }
  configNotice.value = added > 0 ? `已加入 ${added} 个常用字段到 Word 占位符` : '常用字段已全部存在于 Word 占位符'
}

async function toggleFieldCommonPreference(fieldKey) {
  if (!props.projectId || !fieldKey) return
  const has = userCommonKeys.value.has(fieldKey)
  try {
    const updated = await updateExportCommonFields(props.projectId, {
      add_keys: has ? [] : [fieldKey],
      remove_keys: has ? [fieldKey] : [],
    })
    userCommonKeys.value = new Set(updated?.common_field_keys || [])
    syncUserCommonFlags()
    configNotice.value = has ? `已取消常用：${getFieldDisplayName(fieldKey)}` : `已设为常用：${getFieldDisplayName(fieldKey)}`
  } catch (e) {
    configError.value = e?.response?.data?.detail || '更新常用字段失败'
  }
}

function addExcelColumnMapping() {
  appendExcelColumnMapping('', '')
}
function removeExcelColumnMapping(idx) {
  mappingDraft.value.config.excel_columns.splice(idx, 1)
}
function updateExcelColumnMapping({ idx, key, value }) {
  const row = mappingDraft.value.config.excel_columns[idx]
  if (!row) return
  if (key === 'column') {
    row.column = String(value || '').trim().toUpperCase()
    return
  }
  if (key === 'field_key') {
    const prevField = row.field_key
    row.field_key = value
    const prevLabel = getFieldDisplayName(prevField)
    if (!String(row.header || '').trim() || row.header === prevLabel) {
      row.header = getFieldDisplayName(value)
    }
    return
  }
  row[key] = value
}
function addStaticCellMapping() {
  mappingDraft.value.config.static_cells.push({ cell: '', field_key: '', aggregation: 'first', template: '' })
}
function removeStaticCellMapping(idx) {
  mappingDraft.value.config.static_cells.splice(idx, 1)
}
function updateStaticCellMapping({ idx, key, value }) {
  const row = mappingDraft.value.config.static_cells[idx]
  if (!row) return
  row[key] = value
  if (key === 'aggregation' && value === 'template') {
    row.field_key = ''
    if (!String(row.template || '').trim()) row.template = '{major} {class_grade} 参评{scope_valid_submission_count}人'
  }
  if (key === 'aggregation' && value === 'first' && !String(row.field_key || '').trim()) {
    row.field_key = 'scope_valid_submission_count'
  }
}
function updateDataStartRow(val) {
  const headerRow = Number(mappingDraft.value.config.header_row || 1)
  const minStart = mappingDraft.value.config.write_header ? (headerRow + 1) : 1
  const next = Number(val || minStart)
  mappingDraft.value.config.data_start_row = Math.max(minStart, next)
}
function updateWriteHeader(val) {
  writeHeaderTouched.value = true
  const enabled = !!val
  mappingDraft.value.config.write_header = enabled
  if (enabled) {
    const headerRow = Number(mappingDraft.value.config.header_row || 1)
    const minStart = headerRow + 1
    const currentStart = Number(mappingDraft.value.config.data_start_row || minStart)
    if (currentStart <= headerRow) {
      mappingDraft.value.config.data_start_row = minStart
      configNotice.value = `已自动调整数据起始行到第 ${minStart} 行，避免覆盖表头`
    }
  }
}

function addWordPlaceholderMapping() {
  mappingDraft.value.config.word_placeholders.push({ placeholder: '', field_key: '' })
}
function removeWordPlaceholderMapping(idx) {
  mappingDraft.value.config.word_placeholders.splice(idx, 1)
}
function updateWordPlaceholderMapping({ idx, key, value }) {
  const row = mappingDraft.value.config.word_placeholders[idx]
  if (!row) return
  row[key] = value
}

function formatTokenPreview(raw) {
  const prefix = mappingDraft.value.config.token_prefix || '@'
  const token = String(raw || '').trim()
  if (!token) return `${prefix}token`
  return token.startsWith(prefix) ? token : `${prefix}${token}`
}

async function copyTokenPreview(raw) {
  const text = formatTokenPreview(raw)
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    configError.value = `复制失败，请手动复制：${text}`
  }
}

function getFieldDisplayName(fieldKey) {
  const all = allSelectableFields.value || []
  const hit = all.find((f) => f.key === fieldKey)
  return hit?.label || fieldKey
}

function validateMappingDraftBeforeSave() {
  const cfg = mappingDraft.value.config || {}
  const computedRows = cfg.computed_fields || []
  const selectable = new Set((allSelectableFields.value || []).map((f) => f.key))
  const keyRegex = /^[A-Za-z_][A-Za-z0-9_]*$/
  const computedKeys = new Set()
  for (const row of computedRows) {
    const key = String(row?.key || '').trim()
    if (!key) continue
    if (!keyRegex.test(key)) {
      return `统计字段 key 不合法：${key}（仅支持字母/数字/下划线，且不能数字开头）`
    }
    if (computedKeys.has(key)) {
      return `统计字段 key 重复：${key}`
    }
    computedKeys.add(key)
    const fn = String(row?.fn || '').trim().toLowerCase()
    const targetField = String(row?.field_key || '').trim()
    if (['sum', 'avg', 'min', 'max', 'join_distinct'].includes(fn) && targetField && !selectable.has(targetField) && !computedKeys.has(targetField)) {
      return `统计字段 ${key} 引用了不存在的字段：${targetField}`
    }
  }

  const assertExists = (fieldKey, label) => {
    const key = String(fieldKey || '').trim()
    if (!key) return null
    if (!selectable.has(key)) return `${label}引用了不存在的字段：${key}`
    return null
  }

  for (const row of cfg.excel_columns || []) {
    const err = assertExists(row?.field_key, 'Excel 列映射')
    if (err) return err
  }
  for (const row of cfg.word_placeholders || []) {
    const err = assertExists(row?.field_key, 'Word 占位符')
    if (err) return err
  }
  for (const row of cfg.static_cells || []) {
    const agg = String(row?.aggregation || 'first').trim()
    if (agg === 'template') {
      if (!String(row?.template || '').trim()) return '静态单元格使用模板拼接时，模板内容不能为空'
      continue
    }
    if (!String(row?.field_key || '').trim()) return '静态单元格“单值字段写入”模式必须选择字段'
    const err = assertExists(row?.field_key, '静态单元格')
    if (err) return err
  }
  return ''
}

function addComputedField() {
  const nextIndex = (mappingDraft.value.config.computed_fields || []).length + 1
  mappingDraft.value.config.computed_fields.push({
    key: `stat_${nextIndex}`,
    fn: 'count',
    target: 'valid_rows',
    field_key: '',
    precision: '',
    sep: '、',
  })
}

function removeComputedField(idx) {
  mappingDraft.value.config.computed_fields.splice(idx, 1)
}

function updateComputedField({ idx, key, value }) {
  const row = mappingDraft.value.config.computed_fields[idx]
  if (!row) return
  if (key === 'precision') {
    row.precision = value === '' ? '' : Number(value)
    return
  }
  row[key] = value
}
</script>
