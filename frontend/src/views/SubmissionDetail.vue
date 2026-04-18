<template>
  <div class="page-shell">
    <div class="app-breadcrumb">
      <router-link :to="{ name: 'Submissions' }" class="text-brand-600 hover:underline">进行中的测评任务</router-link>
      <span class="text-slate-400">/</span>
      <h2 class="app-breadcrumb-current">题目化作答</h2>
    </div>

    <div v-if="loading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="detailError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ detailError }}</div>

    <template v-else-if="detail">
      <div class="app-surface p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="text-sm text-slate-500">{{ detail.project_name || '—' }}</div>
            <div class="mt-1">
              <StatusBadge :text="statusLabel(detail)" :tone="statusTone(detail)" />
            </div>
          </div>
          <div class="text-sm text-slate-600">
            已完成 {{ completedCount }} / {{ selfQuestionCount }} 题（自评模块）
          </div>
        </div>
      </div>

      <div class="app-surface p-4">
        <!-- 手机端：上一题/下一题 -->
        <div class="mb-3 flex items-center justify-between md:hidden">
          <button type="button" class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50" :disabled="currentQuestionIdx <= 0" @click="switchQuestion(currentQuestionIdx - 1)">上一题</button>
          <span class="text-xs text-slate-500">{{ currentQuestionIdx + 1 }} / {{ questionList.length }}</span>
          <button type="button" class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50" :disabled="currentQuestionIdx >= questionList.length - 1" @click="switchQuestion(currentQuestionIdx + 1)">下一题</button>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-[260px_1fr]">
          <!-- 电脑端：题号导航 -->
          <aside class="hidden rounded-xl border border-slate-200 bg-slate-50/80 p-3 md:block">
            <h3 class="mb-2 text-sm font-medium text-slate-700">模块导航</h3>
            <div ref="navScrollRef" class="max-h-[520px] overflow-auto pr-1">
              <template v-for="(q, idx) in questionList" :key="q.indicator_id">
                <div
                  v-if="idx === 0 || q.section_name !== questionList[idx - 1].section_name || q.subsection_name !== questionList[idx - 1].subsection_name"
                  class="mt-2 mb-1 px-2 text-xs font-semibold text-slate-500"
                  :class="{ 'mt-0': idx === 0 }"
                >
                  <span>{{ q.section_name || '未分组' }}</span>
                  <span v-if="q.subsection_name" class="font-normal text-slate-400"> / {{ q.subsection_name }}</span>
                </div>
                <button
                  type="button"
                  class="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs hover:bg-white"
                  :class="[
                    idx === currentQuestionIdx ? 'bg-white text-blue-700 ring-1 ring-blue-200' : (q.score_source === 'self' ? 'text-slate-700' : 'text-slate-400'),
                    q.subsection_name ? 'pl-4' : 'pl-2',
                  ]"
                  @click="switchQuestion(idx)"
                >
                  <span class="truncate">{{ idx + 1 }}. {{ q.indicator_name }}</span>
                  <span v-if="q.score_source === 'self'" :class="q.is_completed ? 'text-green-600' : 'text-amber-600'">{{ q.is_completed ? '已完成' : '待填写' }}</span>
                  <span v-else-if="q.score_source === 'import'" class="text-slate-400">导入</span>
                  <span v-else-if="q.score_source === 'reviewer'" class="text-slate-400">评分</span>
                </button>
              </template>
            </div>
          </aside>

          <!-- 当前题目 -->
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
                <span v-else-if="currentQuestion.score_source === 'reviewer'" class="rounded bg-purple-50 px-1.5 py-0.5 text-xs text-purple-600">老师评分</span>
              </div>
              <div class="mt-1 text-xs text-slate-500">满分：{{ currentQuestion.max_score }}</div>
            </div>

            <!-- ① 学生自评模块 -->
            <template v-if="currentQuestion.score_source === 'self'">
              <div
                v-if="currentGroupSumCappedInfo"
                class="rounded border px-3 py-2 text-xs"
                :class="currentGroupSumCappedInfo.overCap ? 'border-red-200 bg-red-50 text-red-700' : 'border-amber-200 bg-amber-50 text-amber-700'"
              >
                <span>
                  父项封顶满分 <strong>{{ currentGroupSumCappedInfo.cap }}</strong> 分，
                  其他子项已用 <strong>{{ currentGroupSumCappedInfo.siblingsUsed }}</strong> 分，
                  当前剩余可用 <strong>{{ currentGroupSumCappedInfo.remaining }}</strong> 分
                </span>
                <span v-if="currentGroupSumCappedInfo.overCap" class="ml-1 font-medium">
                  （已超出封顶，最终将被截断至 {{ currentGroupSumCappedInfo.cap }} 分）
                </span>
              </div>
              <div class="grid grid-cols-1 gap-3">
                <div>
                  <label class="mb-1 block text-sm text-slate-700">模块自评分</label>
                  <input
                    v-model="currentScore"
                    type="number"
                    min="0"
                    :max="currentGroupSumCappedInfo ? currentGroupSumCappedInfo.remaining : Number(currentQuestion.max_score)"
                    step="0.01"
                    class="app-input"
                    :disabled="!isDraft"
                  />
                </div>
                <div>
                  <label class="mb-1 block text-sm text-slate-700">
                    过程记录
                    <span v-if="!currentQuestion.require_process_record" class="ml-1 text-xs font-normal text-slate-400">（选填）</span>
                  </label>
                  <textarea
                    v-model="currentProcessRecord"
                    rows="5"
                    class="app-textarea"
                    :disabled="!isDraft"
                    :placeholder="currentQuestion.require_process_record ? '请写清楚该模块分数如何得出...' : '过程记录（选填，可不填写）'"
                  />
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-3">
                <button
                  v-if="isDraft"
                  type="button"
                  class="app-btn app-btn-primary app-btn-sm disabled:opacity-50"
                  :disabled="saveQuestionLoading"
                  @click="saveCurrentQuestion"
                >
                  {{ saveQuestionLoading ? '保存中…' : '保存本模块' }}
                </button>
                <span class="text-xs text-slate-500">{{ currentQuestion.is_completed ? '该模块已完成' : '该模块未完成' }}</span>
                <span v-if="questionError" class="text-xs text-red-600">{{ questionError }}</span>
              </div>

              <div class="rounded-xl border border-slate-200 bg-slate-50/80 p-3">
                <h4 class="text-sm font-medium text-slate-700">本模块佐证材料</h4>
                <AttachmentPreviewList
                  v-if="currentEvidenceList.length"
                  class="mt-2"
                  :items="currentEvidenceList"
                  :show-delete="isDraft"
                  @delete="deleteCurrentEvidence"
                />
                <p v-else class="mt-2 text-xs text-slate-500">本模块暂无附件</p>

                <div v-if="isDraft" class="mt-3 space-y-2">
                  <div class="flex flex-col items-stretch gap-2 sm:flex-row sm:items-end">
                    <input ref="fileInputRef" type="file" multiple class="text-xs" @change="onFileChange" />
                    <button
                      type="button"
                      class="rounded border border-blue-300 px-3 py-1 text-xs text-blue-700 hover:bg-blue-50 disabled:opacity-50"
                      :disabled="uploading || !selectedFiles.length"
                      @click="uploadCurrentEvidence"
                    >
                      {{ uploading ? `上传中（${uploadProgress}）…` : `上传${selectedFiles.length > 1 ? selectedFiles.length + '个' : ''}附件` }}
                    </button>
                  </div>
                  <p v-if="selectedFiles.length > 1" class="text-xs text-slate-500">已选择 {{ selectedFiles.length }} 个文件</p>
                  <span v-if="uploadError" class="text-xs text-red-600">{{ uploadError }}</span>
                </div>
              </div>
            </template>

            <!-- ② 统一导入模块（只读） -->
            <template v-else-if="currentQuestion.score_source === 'import'">
              <div v-if="currentQuestion.imported_score == null" class="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                <div class="flex items-center gap-2">
                  <svg class="h-4 w-4 shrink-0 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>此模块成绩将由学院统一导入，导入后将在此显示，无需填写。</span>
                </div>
              </div>
              <div v-else class="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-slate-600">已导入成绩</span>
                  <span class="text-xl font-bold text-slate-700">{{ currentQuestion.imported_score }}</span>
                </div>
                <div v-if="detail.status === 'approved'" class="mt-3 border-t border-slate-200 pt-3">
                  <button
                    type="button"
                    class="rounded border border-amber-300 px-3 py-1.5 text-xs text-amber-700 hover:bg-amber-50"
                    @click="openIndicatorAppeal(currentQuestion)"
                  >
                    对此成绩有异议？申诉
                  </button>
                </div>
              </div>
            </template>

            <!-- ③ 老师评分模块（只读） -->
            <template v-else-if="currentQuestion.score_source === 'reviewer'">
              <div v-if="currentQuestion.reviewer_score == null" class="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                <div class="flex items-center gap-2">
                  <svg class="h-4 w-4 shrink-0 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                  <span>此模块由老师评分，评阅完成后将在此显示成绩。</span>
                </div>
              </div>
              <div v-else class="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-slate-600">老师评分</span>
                  <span class="text-xl font-bold text-slate-700">{{ currentQuestion.reviewer_score }}</span>
                </div>
                <div v-if="detail.status === 'approved'" class="mt-3 border-t border-slate-200 pt-3">
                  <button
                    type="button"
                    class="rounded border border-amber-300 px-3 py-1.5 text-xs text-amber-700 hover:bg-amber-50"
                    @click="openIndicatorAppeal(currentQuestion)"
                  >
                    对此成绩有异议？申诉
                  </button>
                </div>
              </div>
            </template>

            <!-- 桌面端：上一题/下一题 -->
            <div class="hidden items-center justify-between border-t border-slate-200 pt-3 md:flex">
              <button
                type="button"
                class="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                :disabled="currentQuestionIdx <= 0"
                @click="switchQuestion(currentQuestionIdx - 1)"
              >
                ← 上一题
              </button>
              <span class="text-xs text-slate-500">{{ currentQuestionIdx + 1 }} / {{ questionList.length }}</span>
              <button
                type="button"
                class="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                :disabled="currentQuestionIdx >= questionList.length - 1"
                @click="switchQuestion(currentQuestionIdx + 1)"
              >
                下一题 →
              </button>
            </div>
          </section>
        </div>
      </div>

      <div v-if="isDraft" class="app-surface p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="text-sm text-slate-600">
            全卷进度：{{ completedCount }} / {{ selfQuestionCount }}（未完成 {{ Math.max(0, selfQuestionCount - completedCount) }} 题）
          </div>
          <button
            type="button"
            class="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
            :disabled="submitLoading"
            @click="doSubmit"
          >
            {{ submitLoading ? '提交中…' : '提交整张试卷' }}
          </button>
        </div>
        <p v-if="submitError" class="mt-2 text-sm text-red-600">{{ submitError }}</p>
      </div>

      <!-- 补交申请 -->
      <div v-if="lateStatus && !lateStatus.project_open && detail.status === 'draft'" class="app-surface p-5">
        <h3 class="mb-3 text-base font-medium text-slate-800">补交申请</h3>
        <div v-if="lateStatus.channel_active" class="rounded border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <strong>补交通道已开启</strong>，有效期至 <strong>{{ formatDateTime(lateStatus.channel_expires_at) }}</strong>。
        </div>
        <div v-else-if="lateStatus.pending_request" class="rounded border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          您的补交申请正在等待管理员审核。
        </div>
        <template v-else>
          <textarea v-model="lateReason" rows="4" class="app-textarea" placeholder="请详细说明补交原因…" />
          <div class="mt-3">
            <label class="mb-1 block text-xs text-slate-500">可选：上传补交申请附件（可多选）</label>
            <input ref="lateFileInputRef" type="file" multiple class="text-xs" @change="onLateFilesChange" />
            <p v-if="lateFiles.length" class="mt-1 text-xs text-slate-500">已选择 {{ lateFiles.length }} 个文件</p>
          </div>
          <p v-if="lateError" class="mt-2 text-sm text-red-600">{{ lateError }}</p>
          <button type="button" class="mt-3 app-btn app-btn-primary disabled:opacity-50" :disabled="lateLoading" @click="doRequestLate">
            {{ lateLoading ? '提交中…' : '提交补交申请' }}
          </button>
        </template>
      </div>

      <!-- 申诉（整份提交） -->
      <div v-if="detail.status === 'rejected' || detail.status === 'appealing'" class="app-surface p-5">
        <h3 class="mb-4 text-base font-medium text-slate-800">申诉</h3>
        <template v-if="detail.status === 'appealing'">
          <div class="rounded border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            申诉处理中，请等待审核结果。
            <router-link :to="{ name: 'Appeals' }" class="ml-2 underline">查看我的申诉</router-link>
          </div>
        </template>
        <template v-else>
          <textarea v-model="appealReason" rows="4" class="app-textarea" placeholder="请详细说明申诉理由…" />
          <div class="mt-3">
            <label class="mb-1 block text-xs text-slate-500">可选：上传申诉凭证（可多选）</label>
            <input ref="appealFileInputRef" type="file" multiple class="text-xs" @change="onAppealFilesChange" />
            <p v-if="appealFiles.length" class="mt-1 text-xs text-slate-500">已选择 {{ appealFiles.length }} 个文件</p>
          </div>
          <p v-if="appealError" class="mt-2 text-sm text-red-600">{{ appealError }}</p>
          <button type="button" class="mt-3 rounded bg-purple-600 px-4 py-2 text-sm text-white hover:bg-purple-700 disabled:opacity-50" :disabled="appealLoading" @click="doAppeal">
            {{ appealLoading ? '提交中…' : '提交申诉' }}
          </button>
        </template>
      </div>
    </template>

    <!-- 指标级别申诉弹窗 -->
    <div v-if="indicatorAppealModal.show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div class="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
        <h3 class="mb-1 text-base font-semibold text-slate-800">对「{{ indicatorAppealModal.indicatorName }}」申诉</h3>
        <p class="mb-3 text-xs text-slate-500">申诉将发送给负责老师审核，请详细说明异议原因。</p>
        <textarea
          v-model="indicatorAppealModal.reason"
          rows="4"
          class="app-textarea"
          placeholder="请说明成绩有误的原因..."
        />
        <div class="mt-2">
          <label class="mb-1 block text-xs text-slate-500">可选：上传申诉凭证（可多选）</label>
          <input type="file" multiple class="text-xs" @change="onIndicatorAppealFilesChange" />
          <p v-if="indicatorAppealModal.files?.length" class="mt-1 text-xs text-slate-500">已选择 {{ indicatorAppealModal.files.length }} 个文件</p>
        </div>
        <p v-if="indicatorAppealModal.error" class="mt-2 text-xs text-red-600">{{ indicatorAppealModal.error }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-50" @click="indicatorAppealModal.show = false">取消</button>
          <button
            type="button"
            class="rounded bg-purple-600 px-4 py-1.5 text-sm text-white hover:bg-purple-700 disabled:opacity-50"
            :disabled="indicatorAppealModal.loading"
            @click="submitIndicatorAppeal"
          >
            {{ indicatorAppealModal.loading ? '提交中…' : '提交申诉' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 题目化提交页：
 * - PC：左侧模块导航 + 右侧当前题目编辑
 * - 移动端：上一题/下一题单题浏览
 * - 草稿支持单题保存、模块级附件上传、最终整卷提交
 */
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import {
  getSubmission,
  getSubmissionQuestions,
  saveSubmissionQuestion,
  submitSubmission,
  uploadEvidence as apiUploadEvidence,
  deleteEvidence as apiDeleteEvidence,
  requestLateSubmit,
  getLateStatus,
} from '@/api/submissions'
import {
  createAppeal,
  createAppealWithFiles,
  createIndicatorAppeal,
  createIndicatorAppealWithFiles,
} from '@/api/appeals'
import AttachmentPreviewList from '@/components/AttachmentPreviewList.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'
import { deriveSubmissionDisplayStatus } from '@/utils/submissionStatus'
import { openConfirm } from '@/utils/dialog'

const route = useRoute()
const loading = ref(true)
const detailError = ref('')
const detail = ref(null)
const questionList = ref([])
const currentQuestionIdx = ref(0)
const currentScore = ref('')
const currentProcessRecord = ref('')
const saveQuestionLoading = ref(false)
const questionError = ref('')
const submitLoading = ref(false)
const submitError = ref('')
const fileInputRef = ref(null)
const uploading = ref(false)
const uploadError = ref('')
const uploadProgress = ref('')
const selectedFiles = ref([])
const deletingEvidenceId = ref(null)
const navScrollRef = ref(null)
const _initialLoaded = ref(false)

const isDraft = computed(() => detail.value?.status === 'draft')
const currentQuestion = computed(() => questionList.value[currentQuestionIdx.value] || null)

/**
 * @description 当前题目是否有未保存的修改（分数或过程记录与已保存值不同）
 */
const isDirty = computed(() => {
  const q = currentQuestion.value
  if (!q || q.score_source !== 'self') return false
  const savedScore = q.self_score == null ? '' : String(q.self_score)
  const savedRecord = q.process_record || ''
  return currentScore.value !== savedScore || currentProcessRecord.value !== savedRecord
})

/**
 * @description 封顶求和校验：当前题目所在封顶组的 cap、已用、剩余可用分。
 * @returns {{ cap: number, siblingsUsed: number, remaining: number, overCap: boolean } | null}
 */
const currentGroupSumCappedInfo = computed(() => {
  const q = currentQuestion.value
  if (!q || q.parent_agg_formula !== 'sum_capped' || !q.parent_indicator_id) return null
  const pid = q.parent_indicator_id
  const cap = Number(q.parent_max_score)
  const siblingsUsed = questionList.value
    .filter((i) => i.parent_indicator_id === pid && i.indicator_id !== q.indicator_id)
    .reduce((sum, i) => sum + (Number(i.self_score) || 0), 0)
  const currentUsed = currentScore.value === '' ? 0 : (Number(currentScore.value) || 0)
  return {
    cap,
    siblingsUsed,
    remaining: Math.max(0, cap - siblingsUsed),
    totalUsed: siblingsUsed + currentUsed,
    overCap: siblingsUsed + currentUsed > cap,
  }
})
/** 只统计 self 类型指标的完成数 */
const selfQuestionCount = computed(() => questionList.value.filter((q) => q.score_source === 'self').length)
const completedCount = computed(() => questionList.value.filter((q) => q.score_source === 'self' && q.is_completed).length)
const evidenceByIndicator = computed(() => {
  const map = {}
  for (const ev of (detail.value?.evidences || [])) {
    if (!ev.indicator) continue
    if (!map[ev.indicator]) map[ev.indicator] = []
    map[ev.indicator].push(ev)
  }
  return map
})
const currentEvidenceList = computed(() => {
  const indicatorId = currentQuestion.value?.indicator_id
  if (!indicatorId) return []
  return evidenceByIndicator.value[indicatorId] || []
})

function statusLabel(submission) {
  return deriveSubmissionDisplayStatus(submission || {}).label
}


/**
 * @description 提交状态映射到全站统一徽章颜色。
 * @param {string} status
 * @returns {string}
 */
function statusTone(submission) {
  return deriveSubmissionDisplayStatus(submission || {}).tone
}

function syncCurrentEditor() {
  const q = currentQuestion.value
  if (!q) {
    currentScore.value = ''
    currentProcessRecord.value = ''
    return
  }
  currentScore.value = q.self_score == null ? '' : String(q.self_score)
  currentProcessRecord.value = q.process_record || ''
}

/**
 * @description 滚动导航侧栏使当前题目可见
 */
function scrollNavToActive() {
  nextTick(() => {
    const container = navScrollRef.value
    if (!container) return
    const active = container.querySelector('.ring-blue-200')
    if (active) active.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

async function switchQuestion(idx) {
  if (idx < 0 || idx >= questionList.value.length) return
  if (isDirty.value) {
    const { confirmed } = await openConfirm({
      title: '未保存修改',
      message: '当前题目有未保存的修改，是否放弃并切换？',
      confirmText: '放弃并切换',
      danger: true,
    })
    if (!confirmed) return
  }
  currentQuestionIdx.value = idx
  questionError.value = ''
  uploadError.value = ''
  syncCurrentEditor()
  scrollNavToActive()
}

async function loadQuestions() {
  if (!detail.value?.id) return
  questionList.value = await getSubmissionQuestions(detail.value.id)
  if (currentQuestionIdx.value >= questionList.value.length) currentQuestionIdx.value = 0
  syncCurrentEditor()
  scrollNavToActive()
}

async function loadDetail() {
  if (_initialLoaded.value) {
    await silentRefresh()
    return
  }
  const id = route.params.id
  if (!id) return
  loading.value = true
  detailError.value = ''
  try {
    detail.value = await getSubmission(id)
    await loadQuestions()
    await loadLateStatus(id)
    _initialLoaded.value = true
  } catch (e) {
    detailError.value = e.response?.data?.detail ?? '加载失败'
    detail.value = null
    questionList.value = []
  } finally {
    loading.value = false
  }
}

watch(() => route.params.id, () => {
  _initialLoaded.value = false
  loadDetail()
})

/**
 * @description 静默刷新：不触发 loading 状态，并保留导航栏和页面滚动位置
 */
async function silentRefresh() {
  const id = route.params.id
  if (!id) return
  const savedNavScroll = navScrollRef.value?.scrollTop ?? 0
  const savedPageScroll = window.scrollY
  try {
    detail.value = await getSubmission(id)
    questionList.value = await getSubmissionQuestions(detail.value.id)
    if (currentQuestionIdx.value >= questionList.value.length) currentQuestionIdx.value = 0
    syncCurrentEditor()
  } catch (_) { /* 静默刷新失败不覆盖当前内容 */ }
  nextTick(() => {
    if (navScrollRef.value) navScrollRef.value.scrollTop = savedNavScroll
    window.scrollTo(0, savedPageScroll)
  })
}

async function saveCurrentQuestion() {
  if (!detail.value?.id || !currentQuestion.value) return
  saveQuestionLoading.value = true
  questionError.value = ''
  try {
    const payload = {
      self_score: currentScore.value === '' ? null : Number(currentScore.value),
      process_record: currentProcessRecord.value,
    }
    const result = await saveSubmissionQuestion(detail.value.id, currentQuestion.value.indicator_id, payload)
    const idx = currentQuestionIdx.value
    const q = questionList.value[idx]
    q.self_score = result.self_score
    q.process_record = result.process_record
    q.is_completed = result.is_completed
  } catch (e) {
    questionError.value = e.response?.data?.detail ?? '保存失败，请检查输入'
  } finally {
    saveQuestionLoading.value = false
  }
}

function onFileChange(e) {
  selectedFiles.value = e.target?.files ? Array.from(e.target.files) : []
}

async function uploadCurrentEvidence() {
  if (!detail.value?.id || !currentQuestion.value || !selectedFiles.value.length) {
    uploadError.value = '请先选择文件'
    return
  }
  uploadError.value = ''
  uploading.value = true
  const total = selectedFiles.value.length
  let done = 0
  const errors = []
  try {
    for (const file of selectedFiles.value) {
      done++
      uploadProgress.value = `${done}/${total}`
      const formData = new FormData()
      formData.append('file', file)
      formData.append('indicator_id', String(currentQuestion.value.indicator_id))
      formData.append('name', file.name)
      try {
        await apiUploadEvidence(detail.value.id, formData)
      } catch (err) {
        errors.push(`${file.name}: ${err.response?.data?.detail ?? '上传失败'}`)
      }
    }
    selectedFiles.value = []
    if (fileInputRef.value) fileInputRef.value.value = ''
    await silentRefresh()
    if (errors.length) {
      uploadError.value = errors.join('；')
    }
  } catch (e) {
    uploadError.value = e.response?.data?.detail ?? '上传失败'
  } finally {
    uploading.value = false
    uploadProgress.value = ''
  }
}

/**
 * 删除当前模块附件（软删除）。
 * @param {{id:number}} evidence
 */
async function deleteCurrentEvidence(evidence) {
  if (!detail.value?.id || !evidence?.id) return
  if (deletingEvidenceId.value === evidence.id) return
  uploadError.value = ''
  deletingEvidenceId.value = evidence.id
  try {
    await apiDeleteEvidence(detail.value.id, evidence.id)
    await silentRefresh()
  } catch (e) {
    uploadError.value = e.response?.data?.detail ?? '删除失败'
  } finally {
    deletingEvidenceId.value = null
  }
}

async function doSubmit() {
  if (!detail.value?.id) return
  submitError.value = ''
  submitLoading.value = true
  try {
    detail.value = await submitSubmission(detail.value.id)
    await loadDetail()
  } catch (e) {
    const missing = e.response?.data?.missing_indicators
    if (Array.isArray(missing) && missing.length > 0) {
      submitError.value = `${e.response?.data?.detail || '存在未完成模块'}：${missing.join('、')}`
    } else {
      submitError.value = e.response?.data?.detail ?? '提交失败'
    }
  } finally {
    submitLoading.value = false
  }
}

/* ——— 补交申请 ——— */
const lateStatus = ref(null)
const lateReason = ref('')
const lateLoading = ref(false)
const lateError = ref('')
const lateFileInputRef = ref(null)
const lateFiles = ref([])

async function loadLateStatus(submissionId) {
  try {
    lateStatus.value = await getLateStatus(submissionId)
  } catch {
    lateStatus.value = null
  }
}

/**
 * 选择补交申请附件（支持多文件）。
 * @param {Event} e
 */
function onLateFilesChange(e) {
  lateFiles.value = Array.from(e.target?.files || [])
}

async function doRequestLate() {
  if (!lateReason.value.trim()) {
    lateError.value = '请填写申请理由'
    return
  }
  if (!detail.value?.id) return
  lateError.value = ''
  lateLoading.value = true
  try {
    await requestLateSubmit(detail.value.id, lateReason.value.trim(), lateFiles.value)
    lateReason.value = ''
    lateFiles.value = []
    if (lateFileInputRef.value) lateFileInputRef.value.value = ''
    await loadLateStatus(detail.value.id)
  } catch (e) {
    lateError.value = e.response?.data?.detail ?? '提交申请失败，请重试'
  } finally {
    lateLoading.value = false
  }
}

/* ——— 申诉 ——— */
const appealReason = ref('')
const appealLoading = ref(false)
const appealError = ref('')
const appealFiles = ref([])
const appealFileInputRef = ref(null)

/**
 * 选择整份申诉附件。
 * @param {Event} e
 */
function onAppealFilesChange(e) {
  appealFiles.value = Array.from(e.target?.files || [])
}

async function doAppeal() {
  if (!appealReason.value.trim()) {
    appealError.value = '请填写申诉理由'
    return
  }
  if (!detail.value?.id) return
  appealError.value = ''
  appealLoading.value = true
  try {
    if (appealFiles.value.length) {
      await createAppealWithFiles(detail.value.id, appealReason.value.trim(), appealFiles.value)
    } else {
      await createAppeal(detail.value.id, appealReason.value.trim())
    }
    appealReason.value = ''
    appealFiles.value = []
    if (appealFileInputRef.value) appealFileInputRef.value.value = ''
    await loadDetail()
  } catch (e) {
    appealError.value = e.response?.data?.detail ?? e.response?.data?.reason?.[0] ?? '提交申诉失败'
  } finally {
    appealLoading.value = false
  }
}

/* ——— 指标级别申诉 ——— */
const indicatorAppealModal = ref({
  show: false,
  indicatorId: null,
  indicatorName: '',
  reason: '',
  loading: false,
  error: '',
  files: [],
})

/**
 * 打开指标申诉弹窗。
 * @param {{ indicator_id: number, indicator_name: string }} question
 */
function openIndicatorAppeal(question) {
  indicatorAppealModal.value = {
    show: true,
    indicatorId: question.indicator_id,
    indicatorName: question.indicator_name,
    reason: '',
    loading: false,
    error: '',
    files: [],
  }
}

/**
 * 选择指标申诉附件。
 * @param {Event} e
 */
function onIndicatorAppealFilesChange(e) {
  indicatorAppealModal.value.files = Array.from(e.target?.files || [])
}

async function submitIndicatorAppeal() {
  const modal = indicatorAppealModal.value
  if (!modal.reason.trim()) {
    modal.error = '请填写申诉理由'
    return
  }
  if (!detail.value?.id) return
  modal.error = ''
  modal.loading = true
  try {
    if (modal.files.length) {
      await createIndicatorAppealWithFiles(detail.value.id, modal.indicatorId, modal.reason.trim(), modal.files)
    } else {
      await createIndicatorAppeal(detail.value.id, modal.indicatorId, modal.reason.trim())
    }
    modal.show = false
    await loadDetail()
  } catch (e) {
    modal.error = e.response?.data?.detail ?? '提交申诉失败，请重试'
  } finally {
    modal.loading = false
  }
}

onMounted(() => {
  loadDetail()
})

useRealtimeRefresh('submission', loadDetail, {
  filter: (data) => !data.id || data.id === Number(route.params.id),
})
</script>
