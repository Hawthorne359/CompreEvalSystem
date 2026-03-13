<template>
  <div class="page-shell max-w-3xl">
    <div class="flex items-center gap-2 text-sm">
      <router-link :to="{ name: 'Appeals' }" class="text-slate-600 hover:text-slate-900">申诉列表</router-link>
      <span class="text-slate-400">/</span>
      <span class="font-medium text-slate-800">申诉详情</span>
    </div>

    <div v-if="loading" class="rounded border border-slate-200 bg-white py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="pageError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ pageError }}</div>

    <template v-else-if="appeal">
      <!-- 申诉基本信息 -->
      <div class="app-surface p-4 md:p-6">
        <h3 class="mb-4 text-base font-medium text-slate-800">申诉信息</h3>
        <dl class="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt class="text-slate-500">申诉 ID</dt>
            <dd class="text-slate-800">#{{ appeal.id }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">状态</dt>
            <dd>
              <span class="rounded px-2 py-0.5 text-xs" :class="appealStatusClass(appeal.status)">
                {{ appealStatusLabel(appeal.status) }}
              </span>
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">关联提交</dt>
            <dd>
              <router-link :to="`/submissions/${appeal.submission}`" class="app-link">
                提交 #{{ appeal.submission }}{{ appeal.submission_detail?.project_name ? `（${appeal.submission_detail.project_name}）` : '' }}
              </router-link>
            </dd>
          </div>
          <div v-if="appeal.indicator_name">
            <dt class="text-slate-500">申诉指标</dt>
            <dd class="font-medium text-slate-800">{{ appeal.indicator_name }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">申诉人</dt>
            <dd class="text-slate-800">{{ appeal.submission_detail?.student_name || '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">申诉时间</dt>
            <dd class="text-slate-800">{{ formatDateTime(appeal.created_at) }}</dd>
          </div>
          <div v-if="appeal.updated_at && appeal.updated_at !== appeal.created_at">
            <dt class="text-slate-500">最后修改</dt>
            <dd class="text-slate-800">{{ formatDateTime(appeal.updated_at) }}</dd>
          </div>
          <div v-if="appeal.is_escalated">
            <dt class="text-slate-500">已上报至</dt>
            <dd class="text-slate-800">{{ appeal.escalated_to_name || directorLabel }}</dd>
          </div>
          <div v-if="appeal.escalated_to_admin">
            <dt class="text-slate-500">已上报至</dt>
            <dd class="text-slate-800">{{ appeal.escalated_to_admin_name || adminLabel }}</dd>
          </div>
        </dl>
      </div>

      <!-- 申诉理由 -->
      <div class="app-surface p-4 md:p-6">
        <h3 class="mb-3 text-base font-medium text-slate-800">申诉理由</h3>
        <p class="whitespace-pre-wrap text-sm text-slate-700">{{ appeal.reason || '（未填写理由）' }}</p>

        <template v-if="!isReviewer && appeal.status === 'pending'">
          <div v-if="!editingReason" class="mt-4">
            <button
              type="button"
              class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
              @click="startEditReason"
            >
              修改理由
            </button>
          </div>
          <div v-else class="mt-4 space-y-2">
            <textarea
              v-model="editReasonText"
              rows="4"
              class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="请填写申诉理由…"
            />
            <p v-if="editReasonError" class="text-sm text-red-600">{{ editReasonError }}</p>
            <div class="flex gap-2">
              <button type="button" class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50" @click="editingReason = false">取消</button>
              <button type="button" class="app-btn app-btn-primary app-btn-sm disabled:opacity-50" :disabled="editReasonLoading" @click="saveReason">
                {{ editReasonLoading ? '保存中…' : '保存修改' }}
              </button>
            </div>
          </div>
        </template>
      </div>

      <div class="app-surface p-4 md:p-6">
        <h3 class="mb-3 text-base font-medium text-slate-800">申诉附件</h3>
        <div v-if="appeal.attachments?.length" class="space-y-2">
          <div
            v-for="att in appeal.attachments"
            :key="att.id"
            class="flex items-center justify-between rounded border border-slate-200 px-3 py-2 text-sm"
          >
            <a :href="att.file" target="_blank" rel="noopener noreferrer" class="text-brand-600 hover:underline">
              {{ att.name || `附件#${att.id}` }}
            </a>
            <button
              v-if="!isReviewer && appeal.status === 'pending'"
              type="button"
              class="rounded border border-red-300 px-2 py-1 text-xs text-red-600 hover:bg-red-50"
              @click="removeAttachment(att.id)"
            >
              删除
            </button>
          </div>
        </div>
        <p v-else class="text-sm text-slate-500">暂无附件</p>
        <div v-if="!isReviewer && appeal.status === 'pending'" class="mt-3">
          <input type="file" multiple class="text-xs" :disabled="attachmentLoading" @change="onUploadAttachments" />
        </div>
        <p v-if="attachmentError" class="mt-2 text-sm text-red-600">{{ attachmentError }}</p>
      </div>

      <!-- 评审老师初步处理意见（已处理/已上报时展示） -->
      <div v-if="appeal.status !== 'pending'" class="app-surface p-4 md:p-6">
        <h3 class="mb-3 text-base font-medium text-slate-800">
          {{ appeal.is_escalated || appeal.escalated_to_admin ? `${counselorLabel}处理意见` : '处理结果' }}
        </h3>
        <dl class="space-y-2 text-sm">
          <div>
            <dt class="text-slate-500">结果</dt>
            <dd>
              <span class="rounded px-2 py-0.5 text-xs" :class="appealStatusClass(appeal.status)">
                {{ appealStatusLabel(appeal.status) }}
              </span>
            </dd>
          </div>
          <div v-if="appeal.handler_name || appeal.handler">
            <dt class="text-slate-500">处理人</dt>
            <dd class="text-slate-800">{{ appeal.handler_name || appeal.handler }}</dd>
          </div>
          <div v-if="appeal.handle_comment">
            <dt class="text-slate-500">处理意见</dt>
            <dd class="mt-1 whitespace-pre-wrap rounded bg-slate-50 px-3 py-2 text-slate-700">{{ appeal.handle_comment }}</dd>
          </div>
          <div v-else>
            <dt class="text-slate-500">处理意见</dt>
            <dd class="text-slate-500">（无意见）</dd>
          </div>
        </dl>
      </div>

      <!-- 院系主任处理结果（已上报且已有 escalate_comment 时） -->
      <div v-if="appeal.is_escalated && (appeal.status === 'approved' || appeal.status === 'rejected' || appeal.status === 'escalated_to_admin') && appeal.escalate_comment" class="app-surface p-4 md:p-6">
        <h3 class="mb-3 text-base font-medium text-slate-800">{{ directorLabel }}处理意见</h3>
        <p class="whitespace-pre-wrap text-sm text-slate-700">{{ appeal.escalate_comment }}</p>
      </div>

      <!-- 超管处理结果（已上报超管且已有 admin_comment 时） -->
      <div v-if="appeal.escalated_to_admin && (appeal.status === 'approved' || appeal.status === 'rejected') && appeal.admin_comment" class="app-surface p-4 md:p-6">
        <h3 class="mb-3 text-base font-medium text-slate-800">{{ adminLabel }}处理意见</h3>
        <p class="whitespace-pre-wrap text-sm text-slate-700">{{ appeal.admin_comment }}</p>
      </div>

      <!-- ====== 评审老师处理区（level=2，pending 状态） ====== -->
      <div v-if="isLevel2 && appeal.status === 'pending'" class="rounded border border-blue-100 bg-blue-50 p-6">
        <h3 class="mb-4 text-base font-medium text-slate-800">处理申诉</h3>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm text-slate-700">处理意见（选填）</label>
            <textarea
              v-model="handleComment"
              rows="4"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="请输入处理意见，可留空…"
            />
          </div>
          <p v-if="handleError" class="text-sm text-red-600">{{ handleError }}</p>
          <div class="flex flex-wrap gap-3">
            <button
              type="button"
              class="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              :disabled="handleLoading"
              @click="doHandle('approved')"
            >
              {{ handleLoading && handleAction === 'approved' ? '处理中…' : '通过' }}
            </button>
            <button
              type="button"
              class="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              :disabled="handleLoading"
              @click="doHandle('rejected')"
            >
              {{ handleLoading && handleAction === 'rejected' ? '处理中…' : '驳回' }}
            </button>
            <button
              type="button"
              class="rounded border border-amber-400 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700 hover:bg-amber-100 disabled:opacity-50"
              :disabled="handleLoading"
              @click="doHandle('escalate')"
            >
              {{ handleLoading && handleAction === 'escalate' ? '上报中…' : `上报${directorLabel}` }}
            </button>
          </div>
        </div>
      </div>

      <!-- ====== 院系主任直接处理区（level=3，pending 状态，跳过上报直接裁定） ====== -->
      <div v-if="isLevel3 && !isAdmin && appeal.status === 'pending'" class="rounded border border-purple-100 bg-purple-50 p-6">
        <h3 class="mb-2 text-base font-medium text-slate-800">处理申诉</h3>
        <p class="mb-4 text-xs text-slate-500">作为{{ directorLabel }}，您可直接对此申诉做出裁定。</p>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm text-slate-700">处理意见（选填）</label>
            <textarea
              v-model="handleComment"
              rows="4"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="请输入裁定意见，可留空…"
            />
          </div>
          <p v-if="handleError" class="text-sm text-red-600">{{ handleError }}</p>
          <div class="flex flex-wrap gap-3">
            <button
              type="button"
              class="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              :disabled="handleLoading"
              @click="doHandle('approved')"
            >
              {{ handleLoading && handleAction === 'approved' ? '处理中…' : '通过' }}
            </button>
            <button
              type="button"
              class="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              :disabled="handleLoading"
              @click="doHandle('rejected')"
            >
              {{ handleLoading && handleAction === 'rejected' ? '处理中…' : '驳回' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ====== 院系主任处理上报申诉区（level=3，escalated 状态） ====== -->
      <div v-if="isLevel3 && !isAdmin && appeal.status === 'escalated'" class="rounded border border-purple-100 bg-purple-50 p-6">
        <h3 class="mb-2 text-base font-medium text-slate-800">处理上报申诉</h3>
        <p class="mb-4 text-xs text-slate-500">此申诉已由{{ counselorLabel }}上报，请您做裁定。如无法裁定可继续上报{{ adminLabel }}。</p>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm text-slate-700">处理意见（选填）</label>
            <textarea
              v-model="escalateComment"
              rows="4"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="请输入裁定意见，可留空…"
            />
          </div>
          <p v-if="escalateError" class="text-sm text-red-600">{{ escalateError }}</p>
          <div class="flex flex-wrap gap-3">
            <button
              type="button"
              class="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              :disabled="escalateLoading"
              @click="doEscalateHandle('approved')"
            >
              {{ escalateLoading && escalateAction === 'approved' ? '处理中…' : '通过' }}
            </button>
            <button
              type="button"
              class="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              :disabled="escalateLoading"
              @click="doEscalateHandle('rejected')"
            >
              {{ escalateLoading && escalateAction === 'rejected' ? '处理中…' : '驳回' }}
            </button>
            <button
              type="button"
              class="rounded border border-orange-400 bg-orange-50 px-4 py-2 text-sm font-medium text-orange-700 hover:bg-orange-100 disabled:opacity-50"
              :disabled="escalateLoading"
              @click="doEscalateHandle('escalate_admin')"
            >
              {{ escalateLoading && escalateAction === 'escalate_admin' ? '上报中…' : `上报${adminLabel}` }}
            </button>
          </div>
        </div>
      </div>

      <!-- ====== 超管处理上报申诉区（level=5，escalated_to_admin 状态） ====== -->
      <div v-if="isAdmin && appeal.status === 'escalated_to_admin'" class="rounded border border-indigo-100 bg-indigo-50 p-6">
        <h3 class="mb-2 text-base font-medium text-slate-800">处理上报申诉（终裁）</h3>
        <p class="mb-4 text-xs text-slate-500">此申诉已由{{ directorLabel }}上报，请做最终裁定。通过时可附带评分覆盖。</p>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm text-slate-700">处理意见（选填）</label>
            <textarea
              v-model="adminCommentText"
              rows="4"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="请输入终裁意见，可留空…"
            />
          </div>
          <p v-if="adminHandleError" class="text-sm text-red-600">{{ adminHandleError }}</p>
          <div class="flex flex-wrap gap-3">
            <button
              type="button"
              class="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              :disabled="adminHandleLoading"
              @click="doAdminHandle('approved')"
            >
              {{ adminHandleLoading && adminHandleAction === 'approved' ? '处理中…' : '通过（终裁）' }}
            </button>
            <button
              type="button"
              class="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              :disabled="adminHandleLoading"
              @click="doAdminHandle('rejected')"
            >
              {{ adminHandleLoading && adminHandleAction === 'rejected' ? '处理中…' : '驳回（终裁）' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ====== 超管直接处理 pending / escalated 申诉（终裁权限） ====== -->
      <div v-if="isAdmin && (appeal.status === 'pending' || appeal.status === 'escalated')" class="rounded border border-indigo-100 bg-indigo-50 p-6">
        <h3 class="mb-2 text-base font-medium text-slate-800">处理申诉（{{ adminLabel }}）</h3>
        <p class="mb-4 text-xs text-slate-500">作为{{ adminLabel }}，您可直接对此申诉做出终裁。</p>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm text-slate-700">处理意见（选填）</label>
            <textarea
              v-model="handleComment"
              rows="4"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="请输入处理意见，可留空…"
            />
          </div>
          <p v-if="handleError" class="text-sm text-red-600">{{ handleError }}</p>
          <div class="flex flex-wrap gap-3">
            <button
              type="button"
              class="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              :disabled="handleLoading"
              @click="doHandle('approved')"
            >
              {{ handleLoading && handleAction === 'approved' ? '处理中…' : '通过' }}
            </button>
            <button
              type="button"
              class="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              :disabled="handleLoading"
              @click="doHandle('rejected')"
            >
              {{ handleLoading && handleAction === 'rejected' ? '处理中…' : '驳回' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 学生 pending：撤回入口 -->
      <div v-if="!isReviewer && appeal.status === 'pending'" class="app-surface p-4 md:p-6">
        <h3 class="mb-3 text-base font-medium text-slate-800">撤回申诉</h3>
        <p class="mb-3 text-sm text-slate-600">撤回后申诉将被删除且无法恢复。</p>
        <button
          type="button"
          class="rounded border border-red-300 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
          :disabled="withdrawLoading"
          @click="doWithdraw"
        >
          {{ withdrawLoading ? '撤回中…' : '撤回申诉' }}
        </button>
        <p v-if="withdrawError" class="mt-2 text-sm text-red-600">{{ withdrawError }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
/**
 * 申诉详情/处理页：
 * - 学生：查看详情、pending 时可修改理由或撤回。
 * - 评审老师（level=2）：pending 时可通过/驳回/上报院系主任。
 * - 院系主任（level=3）：escalated 时可通过/驳回/上报超管。
 * - 超管（level=5）：escalated_to_admin 时做最终裁定（可附带评分覆盖）。
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import {
  getAppeal, updateAppealReason, deleteAppeal,
  handleAppeal, handleEscalatedAppeal, handleAdminEscalatedAppeal,
  uploadAppealAttachments, deleteAppealAttachment,
} from '@/api/appeals'
import { formatDateTime } from '@/utils/format'
import { useRoleMetaStore } from '@/stores/roles'
import { getAppealStatusClass, getAppealStatusLabel } from '@/utils/submissionStatus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const roleMeta = useRoleMetaStore()

const userLevel = computed(() => auth.user?.current_role?.level ?? -1)
const counselorLabel = computed(() => roleMeta.nameByLevel(2))
const directorLabel = computed(() => roleMeta.nameByLevel(3))
const adminLabel = computed(() => roleMeta.nameByLevel(5))
const isReviewer = computed(() => userLevel.value >= 2)
const isLevel2 = computed(() => userLevel.value >= 2 && userLevel.value < 3)
const isLevel3 = computed(() => userLevel.value >= 3)
const isAdmin = computed(() => userLevel.value >= 5)

const loading = ref(true)
const pageError = ref('')
const appeal = ref(null)
const attachmentError = ref('')
const attachmentLoading = ref(false)

/* ── 修改理由 ── */
const editingReason = ref(false)
const editReasonText = ref('')
const editReasonLoading = ref(false)
const editReasonError = ref('')

function startEditReason() {
  editReasonText.value = appeal.value?.reason ?? ''
  editReasonError.value = ''
  editingReason.value = true
}

async function saveReason() {
  if (!editReasonText.value.trim()) {
    editReasonError.value = '理由不能为空'
    return
  }
  editReasonLoading.value = true
  editReasonError.value = ''
  try {
    appeal.value = await updateAppealReason(appeal.value.id, editReasonText.value.trim())
    editingReason.value = false
  } catch (e) {
    editReasonError.value = e.response?.data?.detail ?? e.response?.data?.reason?.[0] ?? '保存失败'
  } finally {
    editReasonLoading.value = false
  }
}

/**
 * 上传申诉附件（仅 pending 且申诉人）。
 * @param {Event} e
 */
async function onUploadAttachments(e) {
  const files = Array.from(e.target?.files || [])
  if (!files.length || !appeal.value?.id) return
  attachmentLoading.value = true
  attachmentError.value = ''
  try {
    await uploadAppealAttachments(appeal.value.id, files)
    appeal.value = await getAppeal(appeal.value.id)
  } catch (err) {
    attachmentError.value = err.response?.data?.detail ?? '上传附件失败'
  } finally {
    attachmentLoading.value = false
    if (e.target) e.target.value = ''
  }
}

/**
 * 删除申诉附件。
 * @param {number} attachmentId
 */
async function removeAttachment(attachmentId) {
  if (!appeal.value?.id) return
  attachmentError.value = ''
  try {
    await deleteAppealAttachment(appeal.value.id, attachmentId)
    appeal.value = await getAppeal(appeal.value.id)
  } catch (err) {
    attachmentError.value = err.response?.data?.detail ?? '删除附件失败'
  }
}

/* ── 撤回申诉 ── */
const withdrawLoading = ref(false)
const withdrawError = ref('')

async function doWithdraw() {
  if (!confirm('确定要撤回该申诉吗？撤回后无法恢复。')) return
  withdrawLoading.value = true
  withdrawError.value = ''
  try {
    await deleteAppeal(appeal.value.id)
    router.push({ name: 'Appeals' })
  } catch (e) {
    withdrawError.value = e.response?.data?.detail ?? '撤回失败'
  } finally {
    withdrawLoading.value = false
  }
}

/* ── 评审老师/超管直接处理申诉 ── */
const handleComment = ref('')
const handleLoading = ref(false)
const handleError = ref('')
const handleAction = ref('')

/**
 * @param {'approved'|'rejected'|'escalate'} action
 */
async function doHandle(action) {
  handleLoading.value = true
  handleError.value = ''
  handleAction.value = action
  try {
    appeal.value = await handleAppeal(appeal.value.id, {
      action,
      handle_comment: handleComment.value.trim() || undefined,
    })
  } catch (e) {
    handleError.value = e.response?.data?.detail ?? '处理失败，请重试'
  } finally {
    handleLoading.value = false
    handleAction.value = ''
  }
}

/* ── 院系主任处理上报申诉 ── */
const escalateComment = ref('')
const escalateLoading = ref(false)
const escalateError = ref('')
const escalateAction = ref('')

/**
 * @param {'approved'|'rejected'|'escalate_admin'} action
 */
async function doEscalateHandle(action) {
  escalateLoading.value = true
  escalateError.value = ''
  escalateAction.value = action
  try {
    appeal.value = await handleEscalatedAppeal(appeal.value.id, {
      action,
      escalate_comment: escalateComment.value.trim() || undefined,
    })
  } catch (e) {
    escalateError.value = e.response?.data?.detail ?? '处理失败，请重试'
  } finally {
    escalateLoading.value = false
    escalateAction.value = ''
  }
}

/* ── 超管处理上报申诉（终裁） ── */
const adminCommentText = ref('')
const adminHandleLoading = ref(false)
const adminHandleError = ref('')
const adminHandleAction = ref('')

/**
 * @param {'approved'|'rejected'} action
 */
async function doAdminHandle(action) {
  adminHandleLoading.value = true
  adminHandleError.value = ''
  adminHandleAction.value = action
  try {
    appeal.value = await handleAdminEscalatedAppeal(appeal.value.id, {
      action,
      admin_comment: adminCommentText.value.trim() || undefined,
    })
  } catch (e) {
    adminHandleError.value = e.response?.data?.detail ?? '处理失败，请重试'
  } finally {
    adminHandleLoading.value = false
    adminHandleAction.value = ''
  }
}

/**
 * @param {string} status
 * @returns {string}
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
    superAdminLabel: adminLabel.value,
  })
}

async function loadAppeal() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  pageError.value = ''
  try {
    appeal.value = await getAppeal(id)
  } catch (e) {
    pageError.value = e.response?.data?.detail ?? '加载失败'
    appeal.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAppeal()
})

useRealtimeRefresh('appeal', loadAppeal, {
  filter: (data) => !data.id || data.id === Number(route.params.id),
})
</script>
