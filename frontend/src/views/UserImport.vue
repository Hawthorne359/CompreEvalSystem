<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <!-- 面包屑 -->
    <div class="flex items-center gap-2">
      <router-link
        v-if="isSuperAdmin"
        :to="{ name: 'Users' }"
        class="text-slate-600 hover:text-slate-900"
      >用户管理</router-link>
      <router-link
        v-else
        :to="{ name: 'Dashboard' }"
        class="text-slate-600 hover:text-slate-900"
      >工作台</router-link>
      <span class="text-slate-400">/</span>
      <h2 class="text-xl font-semibold text-slate-800">批量导入用户</h2>
    </div>

    <!-- 权限范围提示 -->
    <div
      v-if="scopeHint"
      class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
    >
      <span class="font-medium">导入范围说明：</span>{{ scopeHint }}
    </div>

    <!-- 导入流程说明 -->
    <div class="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
      <p class="font-medium">导入流程（必须按步骤操作）</p>
      <ol class="mt-1 list-decimal list-inside text-xs space-y-1">
        <li>选择 Excel 文件后，必须先点「预检」，系统将检查文件格式与权限范围。</li>
        <li>预检完成后查看结果：可对每条错误/警告点「排除此行」跳过该行。</li>
        <li>若预检存在未知组织项（院系/班级等），在下方面板处理后可再次预检。</li>
        <li>确认无阻断性错误后，点「确认导入」正式写入数据库。</li>
      </ol>
    </div>

    <!-- 导入表单 -->
    <div class="rounded border border-slate-200 bg-white p-6 space-y-5">
      <h3 class="text-base font-medium text-slate-800">上传 Excel 文件</h3>
      <p class="text-sm text-slate-500">
        支持 Excel 格式（.xlsx/.xls）。模板含多张工作表（{{ studentRoleLabel }}导入、{{ assistantRoleLabel }}导入、{{ counselorRoleLabel }}导入、{{ directorRoleLabel }}导入），各表第一行为表头，从第二行起填写数据。
      </p>

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

      <!-- 操作按钮区 -->
      <div class="flex items-center gap-3 flex-wrap">
        <button
          type="button"
          class="app-btn app-btn-primary disabled:opacity-50"
          :disabled="uploading || previewing || importing || !selectedFile"
          @click="doPreview"
        >
          {{ previewing ? '预检中…' : '预检' }}
        </button>
        <button
          type="button"
          class="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
          :disabled="uploading || previewing || importing || !previewToken || precheckHasBlockingErrors"
          :title="precheckHasBlockingErrors ? '存在阻断性错误，请修正后重新预检' : ''"
          @click="doCommitFromPreview"
        >
          {{ uploading ? '提交中…' : '确认导入' }}
        </button>
        <button
          type="button"
          class="rounded border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          :disabled="templateDownloading || uploading || previewing || importing"
          @click="doDownloadTemplate"
        >
          {{ templateDownloading ? '生成中…' : '下载导入模板' }}
        </button>
        <p v-if="uploadError" class="text-sm text-red-600">{{ uploadError }}</p>
        <p v-if="templateError" class="text-sm text-red-600">{{ templateError }}</p>
      </div>

      <!-- 密码哈希迭代次数选择器 -->
      <div v-if="previewToken && !importing" class="rounded border border-slate-200 bg-slate-50 p-4 space-y-2">
        <label class="block text-sm font-medium text-slate-700">密码哈希迭代次数</label>
        <select
          v-model="hashIterations"
          class="rounded border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="default">默认（120 万次，安全最高）</option>
          <option value="10000">10000 次（较快）</option>
          <option value="1000">1000 次（快速）</option>
          <option value="100">100 次（极速，仅限测试环境）</option>
        </select>
        <p v-if="hashIterations !== 'default'" class="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          降低迭代次数将大幅加快导入速度，但初始密码安全性较低。用户首次登录后修改密码时，密码将自动升级为标准安全强度。
        </p>
        <p v-else class="text-xs text-slate-500">
          使用 Django 默认安全强度。若数据量大（5000+），建议降低迭代次数以加快速度。
        </p>
        <div class="mt-3 flex items-center gap-2">
          <input id="forceChangePwd" v-model="forceChangePassword" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
          <label for="forceChangePwd" class="text-sm text-slate-700">要求用户首次登录后强制修改密码</label>
        </div>
        <p class="text-xs text-slate-500">
          {{ forceChangePassword ? '导入的用户首次登录后将被强制要求修改密码。' : '导入的用户首次登录后无需修改密码，将直接使用导入时设置的初始密码。' }}
        </p>
      </div>

      <!-- 异步导入进度条 -->
      <div v-if="importing" class="rounded border border-blue-200 bg-blue-50 p-5 space-y-3">
        <h4 class="text-sm font-medium text-blue-800">导入进行中…</h4>
        <div class="relative h-5 w-full overflow-hidden rounded-full bg-blue-100">
          <div
            class="absolute inset-y-0 left-0 rounded-full bg-blue-500 transition-all duration-300"
            :style="{ width: importPercent + '%' }"
          ></div>
          <span class="absolute inset-0 flex items-center justify-center text-xs font-medium"
                :class="importPercent > 50 ? 'text-white' : 'text-blue-800'">
            {{ importPercent }}%
          </span>
        </div>
        <div class="flex items-center justify-between text-xs text-blue-700">
          <span>已处理 {{ importProgress.current }} / {{ importProgress.total }}</span>
          <span>成功 {{ importProgress.successCount }} 条</span>
          <span v-if="importEta">预计剩余 {{ importEta }}</span>
        </div>
      </div>

      <p v-if="!previewToken && importResult?.status === 'preview'" class="text-xs text-amber-600">
        预检 token 已过期（15分钟有效期），请重新预检后再确认导入。
      </p>
      <p v-if="precheckHasBlockingErrors" class="text-xs text-red-600">
        预检存在阻断性错误（{{ blockingErrorCount }} 条），请排除或修正问题行后重新预检，再确认导入。
      </p>
      <p v-if="excludedRows.size > 0" class="text-xs text-slate-600">
        已排除 {{ excludedRows.size }} 行，确认导入时将跳过这些行。
      </p>

      <!-- 使用说明（树形分表） -->
      <div class="rounded bg-slate-50 border border-slate-200 p-4 text-sm text-slate-700">
        <h4 class="font-medium text-slate-800 mb-2">使用说明（树形分表导入）</h4>
        <ul class="list-disc list-inside space-y-1 text-xs">
          <li>模板包含 4 张数据工作表，每张表对应一种角色，只需填写需要的表</li>
          <li><b>{{ studentRoleLabel }}导入</b>：填写完整个人信息（用户名、学号、院系、班级等）</li>
          <li><b>{{ assistantRoleLabel }}导入</b>：仅填学号，从已有学生中提拔，默认负责自身所在班级；跨班评审由评审规则控制</li>
          <li><b>{{ counselorRoleLabel }}导入</b>：填写用户名、工号等信息 + 院系名称 + 负责专业/班级列表</li>
          <li><b>{{ directorRoleLabel }}导入</b>：填写用户名、工号等信息 + 负责院系名称，系统自动继承该院系下所有{{ counselorRoleLabel }}的负责班级</li>
          <li>系统按 {{ studentRoleLabel }} → {{ assistantRoleLabel }} → {{ counselorRoleLabel }} → {{ directorRoleLabel }} 顺序自动处理</li>
          <li>下载模板会按当前账号权限动态生成可导入角色的 sheet</li>
          <li>学号/工号必须全局唯一，不能与已有用户重复</li>
          <li>院系/班级/专业名称需与系统中现有名称完全一致</li>
          <li>初始密码留空则默认为 123456</li>
          <li>不允许通过导入创建超级管理员角色</li>
          <li v-if="!isSuperAdmin" class="text-amber-700 font-medium">
            非超级管理员导入的用户默认为未激活状态，需超级管理员审批后方可登录
          </li>
        </ul>
      </div>
    </div>

    <!-- 非超管激活提示 -->
    <div
      v-if="importResult?.notice"
      class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
    >
      {{ importResult.notice }}
    </div>

    <!-- 未知组织项修复面板 -->
    <div
      v-if="importResult?.status === 'preview' && hasUnknownEntities"
      class="rounded border border-amber-200 bg-amber-50 p-5 space-y-4"
    >
      <div class="flex items-center justify-between">
        <h3 class="text-base font-medium text-amber-800">未知组织项修复面板</h3>
        <label class="flex items-center gap-2 text-xs text-amber-900">
          <input v-model="autoCreateMissing" type="checkbox" />
          提交时自动创建"标记为创建"的未知项
        </label>
      </div>
      <p class="text-xs text-amber-800">
        你可以逐条选择「映射到已有项」或「创建新项」。建议先配置后再次点击「预检」确认。
      </p>
      <div class="space-y-3 text-xs">
        <template v-for="item in unknownEntityItems" :key="item.key">
          <div class="rounded border border-amber-200 bg-white px-3 py-2 space-y-2">
            <p class="text-slate-700">
              {{ item.label }}
              <span class="text-slate-500">（行: {{ item.rows.join(', ') }}）</span>
            </p>
            <div class="flex flex-wrap items-center gap-2">
              <select v-model="unknownActions[item.key].action" class="rounded border border-slate-300 px-2 py-1">
                <option value="create">创建新项</option>
                <option value="map">映射到已有项</option>
                <option value="ignore">先忽略</option>
              </select>
              <input
                v-if="unknownActions[item.key].action === 'map'"
                v-model="unknownActions[item.key].mapTo"
                class="rounded border border-slate-300 px-2 py-1 min-w-[260px]"
                :placeholder="item.mapPlaceholder"
              />
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 导入结果 + 行级排除操作 -->
    <div v-if="importResult && importResult.status !== 'processing'" class="rounded border border-slate-200 bg-white p-6 space-y-4">
      <h3 class="text-base font-medium text-slate-800">
        {{ importResult.status === 'preview' ? '预检结果' : '导入结果' }}
      </h3>
      <dl class="grid grid-cols-1 gap-2 text-sm sm:grid-cols-4">
        <div>
          <dt class="text-slate-500">文件名</dt>
          <dd class="text-slate-800">{{ importResult.file_name }}</dd>
        </div>
        <div>
          <dt class="text-slate-500">状态</dt>
          <dd>
            <span
              class="rounded px-2 py-0.5 text-xs"
              :class="importResult.status === 'completed'
                ? 'bg-green-100 text-green-800'
                : (importResult.status === 'preview' ? 'bg-blue-100 text-blue-800' : 'bg-red-100 text-red-800')"
            >
              {{ importResult.status === 'completed' ? '导入成功' : (importResult.status === 'preview' ? '预检结果（未写库）' : '导入失败') }}
            </span>
          </dd>
        </div>
        <div>
          <dt class="text-slate-500">总行数</dt>
          <dd class="text-slate-800">{{ importResult.row_count ?? '—' }}</dd>
        </div>
        <div>
          <dt class="text-slate-500">成功数</dt>
          <dd class="text-slate-800">{{ importResult.success_count ?? '—' }}</dd>
        </div>
        <div>
          <dt class="text-slate-500">错误数</dt>
          <dd class="text-slate-800">{{ importResult.error_count ?? importResult.error_log?.length ?? 0 }}</dd>
        </div>
      </dl>

      <!-- 依赖关系图摘要 -->
      <template v-if="importResult.status === 'preview' && importResult.dependency_graph">
        <div class="rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <h4 class="text-sm font-medium text-blue-800">依赖关系图摘要（预检）</h4>
          <ul class="list-disc list-inside space-y-1 text-xs text-blue-800">
            <li v-for="(item, idx) in importResult.dependency_graph.preconditions || []" :key="`pre-${idx}`">
              {{ item }}
            </li>
          </ul>
          <div class="grid grid-cols-1 gap-2 text-xs sm:grid-cols-2">
            <div class="rounded border border-blue-100 bg-white px-3 py-2">
              <p class="font-medium text-slate-700">节点统计</p>
              <p class="text-slate-600">{{ studentRoleLabel }}：{{ importResult.dependency_graph.nodes?.student ?? 0 }}</p>
              <p class="text-slate-600">{{ assistantRoleLabel }}：{{ importResult.dependency_graph.nodes?.student_assistant ?? 0 }}</p>
              <p class="text-slate-600">{{ counselorRoleLabel }}：{{ importResult.dependency_graph.nodes?.counselor ?? 0 }}</p>
              <p class="text-slate-600">{{ directorRoleLabel }}：{{ importResult.dependency_graph.nodes?.director ?? 0 }}</p>
            </div>
            <div class="rounded border border-blue-100 bg-white px-3 py-2">
              <p class="font-medium text-slate-700">关系边统计</p>
              <p class="text-slate-600">{{ studentRoleLabel }} -> 班级：{{ importResult.dependency_graph.edges?.student_to_class ?? 0 }}</p>
              <p class="text-slate-600">{{ assistantRoleLabel }} -> 班级：{{ importResult.dependency_graph.edges?.assistant_to_class ?? 0 }}</p>
              <p class="text-slate-600">{{ counselorRoleLabel }} -> 班级：{{ importResult.dependency_graph.edges?.counselor_to_class ?? 0 }}</p>
              <p class="text-slate-600">{{ directorRoleLabel }} -> 院系：{{ importResult.dependency_graph.edges?.director_to_dept ?? 0 }}</p>
            </div>
          </div>
          <div v-if="importResult.dependency_graph.samples?.length">
            <p class="mb-1 text-xs font-medium text-slate-700">关系样例（最多 20 条）</p>
            <div class="max-h-44 overflow-y-auto rounded border border-blue-100 bg-white px-3 py-2 text-xs text-slate-700">
              <p v-for="(line, idx) in importResult.dependency_graph.samples" :key="`sample-${idx}`">{{ line }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- 预检排除摘要 -->
      <div v-if="importResult.status === 'preview' && (importResult.error_log?.length || importResult.warnings?.length)" class="text-xs text-slate-600">
        <span v-if="excludedRows.size > 0" class="text-amber-700">已排除 {{ excludedRows.size }} 行，</span>
        将导入 {{ (importResult.row_count ?? 0) - excludedRows.size }} 行。
      </div>

      <!-- 错误详情（含行级排除按钮） -->
      <template v-if="importResult.error_log?.length">
        <h4 class="text-sm font-medium text-red-700">
          错误详情（{{ importResult.error_log.length }} 条，阻断性）
        </h4>
        <div class="max-h-64 overflow-y-auto rounded border border-red-200 bg-red-50">
          <table class="min-w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-red-200">
                <th class="px-3 py-2 text-left font-medium text-red-700 w-28">来源工作表</th>
                <th class="px-3 py-2 text-left font-medium text-red-700 w-16">行号</th>
                <th class="px-3 py-2 text-left font-medium text-red-700">错误信息</th>
                <th v-if="importResult.status === 'preview'" class="px-3 py-2 text-left font-medium text-red-700 w-24">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(err, idx) in importResult.error_log"
                :key="idx"
                class="border-b border-red-100"
                :class="rowKey(err) && excludedRows.has(rowKey(err)) ? 'opacity-40 line-through' : ''"
              >
                <td class="px-3 py-1.5 text-red-800 text-xs">{{ err.sheet || '—' }}</td>
                <td class="px-3 py-1.5 text-red-800">{{ err.row ?? '—' }}</td>
                <td class="px-3 py-1.5 text-red-700">{{ err.message }}</td>
                <td v-if="importResult.status === 'preview'" class="px-3 py-1.5">
                  <button
                    v-if="rowKey(err) && !excludedRows.has(rowKey(err))"
                    type="button"
                    class="rounded border border-red-300 px-2 py-0.5 text-xs text-red-700 hover:bg-red-100"
                    @click="toggleExcludeRow(rowKey(err))"
                  >排除此行</button>
                  <button
                    v-else-if="rowKey(err) && excludedRows.has(rowKey(err))"
                    type="button"
                    class="rounded border border-slate-300 px-2 py-0.5 text-xs text-slate-500 hover:bg-slate-100"
                    @click="toggleExcludeRow(rowKey(err))"
                  >撤销排除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- 警告详情（含行级排除按钮） -->
      <template v-if="importResult.status === 'preview' && importResult.warnings?.length">
        <h4 class="text-sm font-medium text-amber-700">
          警告（{{ importResult.warnings.length }} 条，非阻断性）
        </h4>
        <div class="max-h-48 overflow-y-auto rounded border border-amber-200 bg-amber-50">
          <table class="min-w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-amber-200">
                <th class="px-3 py-2 text-left font-medium text-amber-700 w-28">来源工作表</th>
                <th class="px-3 py-2 text-left font-medium text-amber-700 w-16">行号</th>
                <th class="px-3 py-2 text-left font-medium text-amber-700">提示</th>
                <th class="px-3 py-2 text-left font-medium text-amber-700 w-24">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(w, idx) in importResult.warnings"
                :key="idx"
                class="border-b border-amber-100"
                :class="rowKey(w) && excludedRows.has(rowKey(w)) ? 'opacity-40 line-through' : ''"
              >
                <td class="px-3 py-1.5 text-amber-800 text-xs">{{ w.sheet || '—' }}</td>
                <td class="px-3 py-1.5 text-amber-800">{{ w.row ?? '—' }}</td>
                <td class="px-3 py-1.5 text-amber-700">{{ w.message }}</td>
                <td class="px-3 py-1.5">
                  <button
                    v-if="rowKey(w) && !excludedRows.has(rowKey(w))"
                    type="button"
                    class="rounded border border-amber-300 px-2 py-0.5 text-xs text-amber-700 hover:bg-amber-100"
                    @click="toggleExcludeRow(rowKey(w))"
                  >排除此行</button>
                  <button
                    v-else-if="rowKey(w) && excludedRows.has(rowKey(w))"
                    type="button"
                    class="rounded border border-slate-300 px-2 py-0.5 text-xs text-slate-500 hover:bg-slate-100"
                    @click="toggleExcludeRow(rowKey(w))"
                  >撤销排除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <p v-if="importResult.status === 'completed' && !importResult.error_log?.length" class="text-sm text-green-600">
        全部行导入成功，无错误。
      </p>
    </div>
  </div>
</template>

<script setup>
/**
 * 批量导入用户：强制预检流程（移除直接导入），展示预检结果与行级排除操作。
 * 流程：上传文件 → 「预检」→ 查看结果/排除问题行 → 「确认导入」。
 * 接口：POST /api/v1/users/import/（form-data: file / dry_run=1 / preview_token）
 * 模板：GET /api/v1/users/import/template/
 */
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRoleMetaStore } from '@/stores/roles'
import api from '@/api/axios'
import { commitUsersImportFromPreview, getImportProgress } from '@/api/users'
import { onSSE, offSSE } from '@/composables/useEventStream'

const auth = useAuthStore()
const roleMeta = useRoleMetaStore()
const currentLevel = computed(() => auth.user?.current_role?.level ?? -1)
const isSuperAdmin = computed(() => currentLevel.value >= 5)
const isDirector = computed(() => currentLevel.value === 3)
const isCounselor = computed(() => currentLevel.value === 2)
const studentRoleLabel = computed(() => roleMeta.nameByLevel(0))
const assistantRoleLabel = computed(() => roleMeta.nameByLevel(1))
const counselorRoleLabel = computed(() => roleMeta.nameByLevel(2))
const directorRoleLabel = computed(() => roleMeta.nameByLevel(3))

/** 根据角色生成导入范围提示文字 */
const scopeHint = computed(() => {
  if (isSuperAdmin.value) return ''
  if (isDirector.value) {
    return `作为${directorRoleLabel.value}，您只能导入本院系的用户，可导入${studentRoleLabel.value}、${assistantRoleLabel.value}、${counselorRoleLabel.value}。`
  }
  if (isCounselor.value) {
    return `作为${counselorRoleLabel.value}，您只能导入负责班级内的${studentRoleLabel.value}/${assistantRoleLabel.value}账号。`
  }
  return ''
})

const selectedFile = ref(null)
const fileInputRef = ref(null)
const uploading = ref(false)
const previewing = ref(false)
const uploadError = ref('')
const importResult = ref(null)
const templateDownloading = ref(false)
const templateError = ref('')
const previewToken = ref('')
const autoCreateMissing = ref(true)
const unknownActions = reactive({})
const hashIterations = ref('default')
const forceChangePassword = ref(true)

/** 异步导入进度相关 */
const importing = ref(false)
const importBatchId = ref(null)
const importProgress = reactive({ current: 0, total: 0, successCount: 0 })
const importStartTime = ref(null)
let _pollTimer = null
let _lastProgressValue = -1
let _staleCount = 0
const _STALE_THRESHOLD = 10

const _IMPORT_STATE_KEY = 'user_import_active'

/**
 * 将进行中的导入状态写入 sessionStorage，以便离开页面后恢复。
 */
function _saveImportState() {
  try {
    sessionStorage.setItem(_IMPORT_STATE_KEY, JSON.stringify({
      batchId: importBatchId.value,
      total: importProgress.total,
      startTime: importStartTime.value,
      fileName: importResult.value?.file_name || '',
    }))
  } catch { /* quota exceeded 等异常静默忽略 */ }
}

/**
 * 清除 sessionStorage 中的导入状态。
 */
function _clearImportState() {
  try { sessionStorage.removeItem(_IMPORT_STATE_KEY) } catch { /* ignore */ }
}

/**
 * 页面挂载时检查是否有尚未完成的导入任务，如有则恢复进度条和追踪。
 */
async function _resumeActiveImport() {
  let raw
  try { raw = sessionStorage.getItem(_IMPORT_STATE_KEY) } catch { return }
  if (!raw) return
  let state
  try { state = JSON.parse(raw) } catch { _clearImportState(); return }
  if (!state?.batchId) { _clearImportState(); return }

  const MAX_IMPORT_AGE_MS = 2 * 60 * 60 * 1000
  if (state.startTime && Date.now() - state.startTime > MAX_IMPORT_AGE_MS) {
    _clearImportState()
    return
  }

  try {
    const data = await getImportProgress(state.batchId)
    if (data.status === 'processing') {
      importBatchId.value = state.batchId
      importProgress.current = data.current ?? 0
      importProgress.total = data.total ?? state.total ?? 0
      importProgress.successCount = data.success_count ?? 0
      importStartTime.value = state.startTime || Date.now()
      importing.value = true
      importResult.value = {
        status: 'processing',
        file_name: state.fileName || '',
        row_count: data.total ?? state.total ?? 0,
      }
      _startImportTracking()
    } else if (data.status === 'completed' || data.status === 'failed') {
      _clearImportState()
      importBatchId.value = state.batchId
      importResult.value = {
        status: data.status,
        file_name: state.fileName || '',
        row_count: data.total,
        success_count: data.success_count,
        error_count: data.error_count,
        warning_count: data.warning_count,
        error_log: data.error_log || [],
        warning_log: data.warning_log || [],
      }
    } else {
      _clearImportState()
    }
  } catch {
    _clearImportState()
  }
}

/**
 * 行级排除集合：存放 "sheet_name:row_num" 格式字符串。
 * @type {import('vue').Ref<Set<string>>}
 */
const excludedRows = ref(new Set())

/**
 * 从错误/警告对象生成唯一行键（"sheet:row" 格式）。
 * @param {{ sheet?: string, row?: number }} item
 * @returns {string|null}
 */
function rowKey(item) {
  if (!item || item.row == null) return null
  return `${item.sheet || ''}:${item.row}`
}

/**
 * 切换某行的排除状态。
 * @param {string} key - "sheet_name:row_num" 格式
 */
function toggleExcludeRow(key) {
  if (!key) return
  const s = new Set(excludedRows.value)
  if (s.has(key)) {
    s.delete(key)
  } else {
    s.add(key)
  }
  excludedRows.value = s
}

/**
 * 预检是否存在未被排除的阻断性错误。
 * @type {import('vue').ComputedRef<boolean>}
 */
const precheckHasBlockingErrors = computed(() => {
  if (importResult.value?.status !== 'preview') return false
  const errors = importResult.value?.error_log ?? []
  return errors.some((e) => {
    const k = rowKey(e)
    return !k || !excludedRows.value.has(k)
  })
})

/**
 * 未被排除的阻断性错误数量。
 * @type {import('vue').ComputedRef<number>}
 */
const blockingErrorCount = computed(() => {
  if (importResult.value?.status !== 'preview') return 0
  const errors = importResult.value?.error_log ?? []
  return errors.filter((e) => {
    const k = rowKey(e)
    return !k || !excludedRows.value.has(k)
  }).length
})

/**
 * 清空未知项动作配置。
 */
function resetUnknownActions() {
  Object.keys(unknownActions).forEach((k) => {
    delete unknownActions[k]
  })
}

/**
 * 从预检结果初始化未知项动作配置。
 * @param {Object} unknown - unknown_entities
 */
function initUnknownActions(unknown) {
  resetUnknownActions()
  const deps = unknown?.departments ?? []
  const majors = unknown?.majors ?? []
  const classes = unknown?.classes ?? []
  const grades = unknown?.grades ?? []
  deps.forEach((it) => {
    unknownActions[`department:${it.name}`] = { action: 'create', mapTo: '' }
  })
  majors.forEach((it) => {
    unknownActions[`major:${it.department_name}|${it.major_name}`] = { action: 'create', mapTo: '' }
  })
  classes.forEach((it) => {
    unknownActions[`class:${it.department_name}|${it.class_name}|${it.grade ?? ''}`] = { action: 'create', mapTo: '' }
  })
  grades.forEach((it) => {
    unknownActions[`class:${it.department_name}|${it.class_name}|${it.grade ?? ''}`] = unknownActions[`class:${it.department_name}|${it.class_name}|${it.grade ?? ''}`] || { action: 'create', mapTo: '' }
  })
}

/** 是否存在未知组织项 */
const hasUnknownEntities = computed(() => {
  const unknown = importResult.value?.unknown_entities
  if (!unknown) return false
  return (unknown.departments?.length ?? 0) + (unknown.majors?.length ?? 0) + (unknown.classes?.length ?? 0) + (unknown.grades?.length ?? 0) > 0
})

/**
 * 未知项扁平化列表，用于渲染统一修复面板。
 */
const unknownEntityItems = computed(() => {
  const unknown = importResult.value?.unknown_entities || {}
  const items = []
  ;(unknown.departments || []).forEach((it) => {
    items.push({
      key: `department:${it.name}`,
      label: `未知院系：${it.name}`,
      rows: it.rows || [],
      mapPlaceholder: '请输入系统中已有院系名称',
    })
  })
  ;(unknown.majors || []).forEach((it) => {
    items.push({
      key: `major:${it.department_name}|${it.major_name}`,
      label: `未知专业：${it.department_name} / ${it.major_name}`,
      rows: it.rows || [],
      mapPlaceholder: '请输入该院系下已有专业名称',
    })
  })
  ;(unknown.classes || []).forEach((it) => {
    items.push({
      key: `class:${it.department_name}|${it.class_name}|${it.grade ?? ''}`,
      label: `未知班级：${it.department_name} / ${it.class_name} / ${it.grade || '无年级'}`,
      rows: it.rows || [],
      mapPlaceholder: '请输入该院系下已有班级名称',
    })
  })
  return items
})

/**
 * 生成提交给后端的修复映射载荷。
 * @returns {Object}
 */
function buildResolutionPayload() {
  const departmentMap = {}
  const majorMap = {}
  const classMap = {}
  Object.entries(unknownActions).forEach(([key, value]) => {
    if (!value || value.action !== 'map') return
    const target = (value.mapTo || '').trim()
    if (!target) return
    if (key.startsWith('department:')) {
      departmentMap[key.replace('department:', '')] = target
      return
    }
    if (key.startsWith('major:')) {
      majorMap[key.replace('major:', '')] = target
      return
    }
    if (key.startsWith('class:')) {
      classMap[key.replace('class:', '')] = target
    }
  })
  return { department_map: departmentMap, major_map: majorMap, class_map: classMap }
}

/** @type {import('vue').ComputedRef<number>} */
const importPercent = computed(() => {
  if (!importProgress.total) return 0
  return Math.min(100, Math.round((importProgress.current / importProgress.total) * 100))
})

/** @type {import('vue').ComputedRef<string>} */
const importEta = computed(() => {
  if (!importing.value || !importProgress.current || !importStartTime.value) return ''
  const elapsed = (Date.now() - importStartTime.value) / 1000
  const rate = importProgress.current / elapsed
  if (rate <= 0) return ''
  const remaining = (importProgress.total - importProgress.current) / rate
  if (remaining < 60) return `${Math.ceil(remaining)} 秒`
  return `${Math.floor(remaining / 60)} 分 ${Math.ceil(remaining % 60)} 秒`
})

/**
 * SSE 进度事件处理。
 * @param {Object} data
 */
function _onImportProgress(data) {
  if (data.batch_id !== importBatchId.value) return
  importProgress.current = data.current ?? importProgress.current
  importProgress.total = data.total ?? importProgress.total
  importProgress.successCount = data.success_count ?? importProgress.successCount

  if (data.status === 'completed' || data.status === 'failed') {
    _stopImportTracking()
    _clearImportState()
    importing.value = false
    _fetchFinalResult(data)
  }
}

/** 导入完成/失败后拉取最终结果。 */
async function _fetchFinalResult(sseData) {
  try {
    const result = await getImportProgress(importBatchId.value)
    importResult.value = {
      status: result.status,
      file_name: importResult.value?.file_name || '',
      row_count: result.total,
      success_count: result.success_count,
      error_count: result.error_count,
      warning_count: result.warning_count,
      error_log: result.error_log,
      warning_log: result.warning_log,
      notice: sseData?.notice || '',
    }
  } catch {
    importResult.value = {
      status: sseData?.status || 'completed',
      file_name: importResult.value?.file_name || '',
      row_count: importProgress.total,
      success_count: importProgress.successCount,
      error_count: sseData?.error_count ?? 0,
      warning_count: sseData?.warning_count ?? 0,
      error_log: [],
      warning_log: [],
      notice: sseData?.notice || '',
    }
  }
}

/** 启动 SSE + 轮询双通道进度追踪。 */
function _startImportTracking() {
  _lastProgressValue = -1
  _staleCount = 0
  onSSE('import_progress', _onImportProgress)
  _pollTimer = setInterval(async () => {
    if (!importBatchId.value) return
    try {
      const data = await getImportProgress(importBatchId.value)
      importProgress.current = data.current
      importProgress.total = data.total
      importProgress.successCount = data.success_count
      if (data.status === 'completed' || data.status === 'failed') {
        _stopImportTracking()
        _clearImportState()
        importing.value = false
        _fetchFinalResult(data)
      } else if (data.current === _lastProgressValue) {
        _staleCount++
        if (_staleCount >= _STALE_THRESHOLD) {
          _stopImportTracking()
          _clearImportState()
          importing.value = false
          importResult.value = {
            status: 'failed',
            file_name: importResult.value?.file_name || '',
            row_count: importProgress.total,
            success_count: importProgress.successCount,
            error_count: 1,
            error_log: [{ row: null, sheet: '', message: '导入进度长时间无变化，可能因服务器重启而中断。已处理的数据已写入，请检查后决定是否重新导入。' }],
          }
        }
      } else {
        _lastProgressValue = data.current
        _staleCount = 0
      }
    } catch { /* SSE 仍在工作 */ }
  }, 3000)
}

/** 停止追踪。 */
function _stopImportTracking() {
  offSSE('import_progress', _onImportProgress)
  if (_pollTimer) {
    clearInterval(_pollTimer)
    _pollTimer = null
  }
}

function onFileChange(e) {
  selectedFile.value = e.target?.files?.[0] || null
  importResult.value = null
  previewToken.value = ''
  excludedRows.value = new Set()
  uploadError.value = ''
  resetUnknownActions()
}

/**
 * 预检导入文件（仅校验，不写库）。
 */
async function doPreview() {
  if (!selectedFile.value) return
  previewing.value = true
  uploadError.value = ''
  importResult.value = null
  previewToken.value = ''
  excludedRows.value = new Set()
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('dry_run', '1')
    const payload = buildResolutionPayload()
    if (Object.keys(payload.department_map).length || Object.keys(payload.major_map).length || Object.keys(payload.class_map).length) {
      formData.append('resolution_payload', JSON.stringify(payload))
    }
    const response = await api.post('/users/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importResult.value = response.data
    previewToken.value = response.data?.preview_token || ''
    initUnknownActions(response.data?.unknown_entities || {})
  } catch (e) {
    const data = e.response?.data
    if (data?.batch) {
      importResult.value = data.batch
      uploadError.value = data.detail || '预检过程中出现错误'
    } else {
      uploadError.value = data?.detail ?? '预检失败'
    }
  } finally {
    previewing.value = false
  }
}

/**
 * 基于预检 token 正式提交导入（后端异步执行）。
 */
async function doCommitFromPreview() {
  if (!previewToken.value) {
    uploadError.value = '请先预检，获取 preview_token'
    return
  }
  uploading.value = true
  uploadError.value = ''
  try {
    const payload = buildResolutionPayload()
    const data = await commitUsersImportFromPreview({
      previewToken: previewToken.value,
      autoCreateMissing: autoCreateMissing.value,
      resolutionPayload: payload,
      excludedRows: Array.from(excludedRows.value),
      hashIterations: hashIterations.value,
      forceChangePassword: forceChangePassword.value,
    })
    if (data.status === 'processing' && data.batch?.id) {
      importBatchId.value = data.batch.id
      importProgress.current = 0
      importProgress.total = data.batch.row_count || 0
      importProgress.successCount = 0
      importStartTime.value = Date.now()
      importing.value = true
      importResult.value = {
        status: 'processing',
        file_name: data.batch.file_name || '',
        row_count: data.batch.row_count || 0,
      }
      previewToken.value = ''
      selectedFile.value = null
      excludedRows.value = new Set()
      if (fileInputRef.value) fileInputRef.value.value = ''
      _saveImportState()
      _startImportTracking()
    } else {
      importResult.value = data
      previewToken.value = ''
      selectedFile.value = null
      excludedRows.value = new Set()
      if (fileInputRef.value) fileInputRef.value.value = ''
    }
  } catch (e) {
    const data = e.response?.data
    if (data?.batch) {
      importResult.value = data.batch
      uploadError.value = data.detail || '提交导入失败'
    } else {
      uploadError.value = data?.detail ?? '提交导入失败'
    }
  } finally {
    uploading.value = false
  }
}

async function doDownloadTemplate() {
  templateDownloading.value = true
  templateError.value = ''
  try {
    const response = await api.get('/users/import/template/', {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }))
    const a = document.createElement('a')
    a.href = url
    a.download = 'user_import_template.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    templateError.value = e.response?.data?.detail ?? '模板下载失败，请稍后重试'
  } finally {
    templateDownloading.value = false
  }
}

onMounted(async () => {
  roleMeta.ensureLoaded()
  await _resumeActiveImport()
})

onUnmounted(() => {
  _stopImportTracking()
})
</script>
