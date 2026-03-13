<template>
  <div class="page-shell">
    <div class="app-breadcrumb">
      <router-link :to="{ name: 'Report' }" class="text-brand-600 hover:underline">成绩报表</router-link>
      <span class="text-slate-400">/</span>
      <h2 class="app-breadcrumb-current">提交详情（只读）</h2>
    </div>

    <div v-if="!isStudent" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      当前页面仅学生可访问。
    </div>
    <div v-else-if="loading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="detailError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ detailError }}</div>

    <template v-else-if="detail">
      <div class="app-surface p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="text-sm text-slate-500">{{ detail.submission?.project_name || '—' }}</div>
            <div class="mt-1 text-xs text-slate-500">提交时间：{{ formatDateTime(detail.submission?.submitted_at) }}</div>
          </div>
          <div class="text-right">
            <div class="text-xs text-slate-500">最终总分</div>
            <div class="text-2xl font-semibold" :class="detail.final_score != null ? 'text-brand-700' : 'text-slate-400'">
              {{ detail.final_score != null ? detail.final_score : '未评分' }}
            </div>
          </div>
        </div>
      </div>

      <div class="app-surface p-4">
        <div class="mb-3 flex items-center justify-between md:hidden">
          <button type="button" class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50" :disabled="currentQuestionIdx <= 0" @click="switchQuestion(currentQuestionIdx - 1)">上一题</button>
          <span class="text-xs text-slate-500">{{ currentQuestionIdx + 1 }} / {{ questionList.length }}</span>
          <button type="button" class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50" :disabled="currentQuestionIdx >= questionList.length - 1" @click="switchQuestion(currentQuestionIdx + 1)">下一题</button>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-[260px_1fr]">
          <aside class="hidden rounded-xl border border-slate-200 bg-slate-50/80 p-3 md:block">
            <h3 class="mb-2 text-sm font-medium text-slate-700">模块导航</h3>
            <div class="max-h-[520px] overflow-auto pr-1">
              <template v-for="(q, idx) in questionList" :key="q.indicator_id">
                <div
                  v-if="idx === 0 || q.section_name !== questionList[idx - 1].section_name || q.subsection_name !== questionList[idx - 1].subsection_name"
                  class="mb-1 mt-2 px-2 text-xs font-semibold text-slate-500"
                  :class="{ 'mt-0': idx === 0 }"
                >
                  <span>{{ q.section_name || '未分组' }}</span>
                  <span v-if="q.subsection_name" class="font-normal text-slate-400"> / {{ q.subsection_name }}</span>
                </div>
                <button
                  type="button"
                  class="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs hover:bg-white"
                  :class="idx === currentQuestionIdx ? 'bg-white text-blue-700 ring-1 ring-blue-200' : 'text-slate-700'"
                  @click="switchQuestion(idx)"
                >
                  <span class="truncate">{{ idx + 1 }}. {{ q.indicator_name }}</span>
                  <span class="text-[10px] text-slate-400">{{ moduleTypeLabel(q) }}</span>
                </button>
              </template>
            </div>
          </aside>

          <section v-if="currentQuestion" class="space-y-4 rounded-xl border border-slate-200 bg-white/90 p-4">
            <div>
              <div class="flex items-center gap-1 text-xs text-slate-500">
                <span>{{ currentQuestion.section_name || '未分组模块' }}</span>
                <template v-if="currentQuestion.subsection_name">
                  <span class="text-slate-300">/</span>
                  <span>{{ currentQuestion.subsection_name }}</span>
                </template>
              </div>
              <div class="mt-1 flex items-center gap-2">
                <h3 class="text-base font-semibold text-slate-800">{{ currentQuestion.indicator_name }}</h3>
                <span v-if="currentQuestion.score_source === 'import'" class="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-600">统一导入</span>
                <span v-else-if="currentQuestion.score_source === 'reviewer'" class="rounded bg-purple-50 px-1.5 py-0.5 text-xs text-purple-600">评审打分</span>
                <span v-else-if="currentQuestion.score_source === 'self'" class="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">学生自评</span>
                <span v-if="currentQuestion.is_record_only" class="rounded bg-emerald-100 px-1.5 py-0.5 text-xs text-emerald-700">仅记录</span>
                <span v-if="currentQuestion.is_arbitrated" class="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700">仲裁已采用</span>
              </div>
              <div class="mt-1 text-xs text-slate-500">
                满分：{{ currentQuestion.is_record_only && !currentQuestion.max_score ? '仅记录项（不设满分）' : scoreText(currentQuestion.max_score) }}
              </div>
            </div>

            <div v-if="currentQuestion.is_record_only" class="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 text-sm text-emerald-800">
              当前模块为仅记录项，用于留痕或辅助信息，不参与总分聚合；你仍可查看记录并发起申诉。
            </div>

            <div v-if="currentQuestion.score_source === 'import'" class="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div class="text-xs text-slate-500">统一导入成绩</div>
                <div class="mt-1 text-lg font-semibold text-slate-800">{{ scoreText(currentQuestion.imported_score) }}</div>
              </div>
              <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div class="text-xs text-slate-500">最终采用分</div>
                <div class="mt-1 text-lg font-semibold text-brand-700">{{ scoreText(currentQuestion.final_adopted_score) }}</div>
              </div>
            </div>
            <div v-else-if="currentQuestion.score_source === 'reviewer'" class="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div class="text-xs text-slate-500">评审最终分（非仲裁）</div>
                <div class="mt-1 text-lg font-semibold text-slate-800">{{ scoreText(currentQuestion.reviewer_score) }}</div>
              </div>
              <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div class="text-xs text-slate-500">最终采用分</div>
                <div class="mt-1 text-lg font-semibold text-brand-700">{{ scoreText(currentQuestion.final_adopted_score) }}</div>
              </div>
            </div>
            <div v-else class="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div class="text-xs text-slate-500">学生自评分</div>
                <div class="mt-1 text-lg font-semibold text-slate-800">{{ scoreText(currentQuestion.self_score) }}</div>
              </div>
              <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <div class="text-xs text-slate-500">最终采用分</div>
                <div class="mt-1 text-lg font-semibold text-brand-700">{{ scoreText(currentQuestion.final_adopted_score) }}</div>
              </div>
            </div>

            <div class="rounded-xl border border-slate-200 bg-white p-3">
              <h4 class="text-sm font-medium text-slate-700">{{ timelineTitle }}</h4>
              <div v-if="currentTimeline.length" class="mt-2 space-y-2">
                <div
                  v-for="(record, idx) in currentTimeline"
                  :key="`${currentQuestion.indicator_id}-record-${idx}`"
                  class="rounded border border-slate-200 bg-slate-50 px-3 py-2"
                >
                  <div class="flex flex-wrap items-center justify-between gap-2">
                    <div class="text-sm text-slate-700">
                      <span class="font-medium">{{ record.logical_round_label || '评审' }}</span>
                      <span v-if="record.reviewer_name" class="ml-2 text-xs text-slate-500">评分人：{{ record.reviewer_name }}</span>
                    </div>
                    <div class="text-sm font-semibold text-slate-800">{{ scoreText(record.score) }}</div>
                  </div>
                  <div class="mt-1 text-xs text-slate-500">
                    <span>通道：{{ channelLabel(record.score_channel) }}</span>
                    <span class="ml-3">时间：{{ formatDateTime(record.created_at) }}</span>
                  </div>
                </div>
              </div>
              <p v-else class="mt-2 text-xs text-slate-500">{{ timelineEmptyText }}</p>
            </div>

            <div class="rounded-xl border border-slate-200 bg-slate-50/80 p-3">
              <h4 class="text-sm font-medium text-slate-700">本模块佐证材料</h4>
              <div v-if="currentQuestion.evidences?.length" class="mt-2">
                <a
                  v-for="ev in currentQuestion.evidences"
                  :key="`ev-${ev.id}`"
                  class="mr-2 inline-block text-xs text-brand-600 hover:underline"
                  :href="ev.file"
                  target="_blank"
                  rel="noopener noreferrer"
                >{{ evidenceName(ev) }}</a>
              </div>
              <p v-else class="mt-2 text-xs text-slate-500">本模块暂无附件</p>
            </div>

            <div class="rounded-xl border border-amber-200 bg-amber-50/70 p-3">
              <div class="mb-2 text-sm font-medium text-amber-800">对当前模块有异议？</div>
              <button
                type="button"
                class="rounded bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
                @click="openAppealModal"
              >
                我要申诉
              </button>
            </div>
          </section>
        </div>
      </div>

      <div class="app-surface p-4">
        <h3 class="text-sm font-medium text-slate-700">提交级材料</h3>
        <div v-if="detail.global_evidences?.length" class="mt-2">
          <a
            v-for="ev in detail.global_evidences"
            :key="`global-${ev.id}`"
            class="mr-2 inline-block text-xs text-brand-600 hover:underline"
            :href="ev.file"
            target="_blank"
            rel="noopener noreferrer"
          >{{ evidenceName(ev) }}</a>
        </div>
        <p v-else class="mt-2 text-xs text-slate-500">暂无提交级材料</p>
      </div>
    </template>

    <div v-if="appealModal.show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div class="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
        <h3 class="mb-1 text-base font-semibold text-slate-800">模块申诉</h3>
        <p class="mb-3 text-xs text-slate-500">指标：{{ appealModal.indicatorName }}</p>
        <textarea
          v-model="appealModal.reason"
          rows="4"
          class="app-textarea"
          placeholder="请填写申诉理由..."
        />
        <div class="mt-2">
          <label class="mb-1 block text-xs text-slate-500">可选：上传申诉凭证（可多选）</label>
          <input type="file" multiple class="text-xs" @change="onAppealFilesChange" />
          <p v-if="appealModal.files?.length" class="mt-1 text-xs text-slate-500">已选择 {{ appealModal.files.length }} 个文件</p>
        </div>
        <p v-if="appealModal.error" class="mt-2 text-xs text-red-600">{{ appealModal.error }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-50" @click="appealModal.show = false">取消</button>
          <button
            type="button"
            class="rounded bg-purple-600 px-4 py-1.5 text-sm text-white hover:bg-purple-700 disabled:opacity-50"
            :disabled="appealModal.loading"
            @click="submitModuleAppeal"
          >
            {{ appealModal.loading ? '提交中…' : '提交申诉' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 学生成绩报表详情页（只读）：
 * - 左侧模块导航，右侧展示当前模块分数/评审时间线/附件；
 * - 每题下方固定“我要申诉”按钮，支持理由与附件上传。
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getStudentSubmissionReportDetail } from '@/api/report'
import { createIndicatorAppealWithFiles } from '@/api/appeals'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const detailError = ref('')
const detail = ref(null)
const currentQuestionIdx = ref(0)
const isStudent = computed(() => (auth.user?.current_role?.level ?? -1) <= 1)

const questionList = computed(() => Array.isArray(detail.value?.items) ? detail.value.items : [])
const currentQuestion = computed(() => questionList.value[currentQuestionIdx.value] || null)
const timelineTitle = computed(() => {
  if (!currentQuestion.value) return '记录时间线'
  if (currentQuestion.value.score_source === 'import') return '导入/处理记录'
  if (currentQuestion.value.score_source === 'reviewer') return '评审记录时间线'
  return '模块记录时间线'
})
const timelineEmptyText = computed(() => {
  if (!currentQuestion.value) return '暂无记录'
  if (currentQuestion.value.score_source === 'import') return '暂无导入记录'
  if (currentQuestion.value.score_source === 'reviewer') return '暂无评审记录'
  return '该模块当前暂无记录'
})
const currentTimeline = computed(() => {
  const records = Array.isArray(currentQuestion.value?.score_records) ? [...currentQuestion.value.score_records] : []
  const source = currentQuestion.value?.score_source
  const filtered = records.filter((record) => {
    if (source === 'import') return ['import', 'arbitration'].includes(record?.score_channel)
    if (source === 'reviewer') return ['assignment', 'arbitration'].includes(record?.score_channel)
    return ['arbitration'].includes(record?.score_channel)
  })
  filtered.sort((a, b) => {
    const ta = a?.created_at ? new Date(a.created_at).getTime() : 0
    const tb = b?.created_at ? new Date(b.created_at).getTime() : 0
    return ta - tb
  })
  return filtered
})

const appealModal = ref({
  show: false,
  reason: '',
  files: [],
  loading: false,
  error: '',
  indicatorId: null,
  indicatorName: '',
})

/**
 * @description 读取当前提交的报表详情。
 * @returns {Promise<void>}
 */
async function loadDetail() {
  if (!isStudent.value) return
  loading.value = true
  detailError.value = ''
  try {
    detail.value = await getStudentSubmissionReportDetail(Number(route.params.id))
    currentQuestionIdx.value = 0
  } catch (e) {
    detailError.value = e.response?.data?.detail ?? '加载报表详情失败'
    detail.value = null
  } finally {
    loading.value = false
  }
}

/**
 * @description 切换当前模块。
 * @param {number} idx
 * @returns {void}
 */
function switchQuestion(idx) {
  if (idx < 0 || idx >= questionList.value.length) return
  currentQuestionIdx.value = idx
}

/**
 * @description 分数字段格式化。
 * @param {number|string|null|undefined} score
 * @returns {string|number}
 */
function scoreText(score) {
  if (score === null || score === undefined || score === '') return '—'
  return score
}

/**
 * @description 评分通道展示文案。
 * @param {string} scoreChannel
 * @returns {string}
 */
function channelLabel(scoreChannel) {
  if (scoreChannel === 'assignment') return '评审'
  if (scoreChannel === 'arbitration') return '仲裁'
  if (scoreChannel === 'import') return '导入'
  return scoreChannel || '未知'
}

/**
 * @description 模块类型标签。
 * @param {{score_source?: string, is_record_only?: boolean}} question
 * @returns {string}
 */
function moduleTypeLabel(question) {
  if (question?.is_record_only) return '仅记录'
  if (question?.score_source === 'self') return '自评'
  if (question?.score_source === 'import') return '导入'
  if (question?.score_source === 'reviewer') return '评审'
  return '模块'
}

/**
 * @description 统一附件展示名。
 * @param {{name?:string,file?:string}} evidence
 * @returns {string}
 */
function evidenceName(evidence) {
  return evidence?.name || evidence?.file || '未命名附件'
}

/**
 * @description 打开当前模块申诉弹窗。
 * @returns {void}
 */
function openAppealModal() {
  if (!currentQuestion.value) return
  appealModal.value = {
    show: true,
    reason: '',
    files: [],
    loading: false,
    error: '',
    indicatorId: currentQuestion.value.indicator_id,
    indicatorName: currentQuestion.value.indicator_name,
  }
}

/**
 * @description 选择申诉附件。
 * @param {Event} e
 * @returns {void}
 */
function onAppealFilesChange(e) {
  appealModal.value.files = Array.from(e.target?.files || [])
}

/**
 * @description 提交模块申诉（理由+附件）。
 * @returns {Promise<void>}
 */
async function submitModuleAppeal() {
  const modal = appealModal.value
  if (!modal.reason.trim()) {
    modal.error = '请填写申诉理由'
    return
  }
  modal.loading = true
  modal.error = ''
  try {
    await createIndicatorAppealWithFiles(
      Number(route.params.id),
      modal.indicatorId,
      modal.reason.trim(),
      modal.files,
    )
    modal.show = false
    const shouldGotoAppeals = window.confirm('申诉已提交，是否跳转到申诉列表查看进度？')
    if (shouldGotoAppeals) router.push({ name: 'Appeals' })
  } catch (e) {
    modal.error = e.response?.data?.detail ?? '提交申诉失败'
  } finally {
    modal.loading = false
  }
}

onMounted(() => {
  loadDetail()
})
</script>
