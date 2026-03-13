/**
 * @description 提交原始状态到标签/色调的统一映射。
 */
const SUBMISSION_STATUS_META = {
  draft: { label: '草稿', tone: 'neutral' },
  submitted: { label: '已提交', tone: 'info' },
  under_review: { label: '审核中', tone: 'warning' },
  approved: { label: '已通过', tone: 'success' },
  rejected: { label: '已驳回', tone: 'danger' },
  appealing: { label: '申诉中', tone: 'purple' },
}

/**
 * @description 展示态映射（由后端派生状态优先驱动）。
 */
const DISPLAY_STATUS_META = {
  已仲裁: { tone: 'purple' },
  已审核: { tone: 'success' },
}

/**
 * @description 获取原始提交状态标签。
 * @param {string} status
 * @returns {string}
 */
export function getSubmissionStatusLabel(status) {
  return SUBMISSION_STATUS_META[status]?.label ?? status ?? '—'
}

/**
 * @description 获取原始提交状态色调。
 * @param {string} status
 * @returns {string}
 */
export function getSubmissionStatusTone(status) {
  return SUBMISSION_STATUS_META[status]?.tone ?? 'neutral'
}

/**
 * @description 统一计算提交展示态（后端 display_status 优先，兼容前端兜底推导）。
 * @param {{
 *   status?: string,
 *   final_score?: number|null,
 *   finalScore?: number|null,
 *   is_arbitrated?: boolean,
 *   isArbitrated?: boolean,
 *   display_status?: string,
 *   displayStatus?: string,
 *   display_tone?: string,
 *   displayTone?: string
 * }} submission
 * @returns {{ label: string, tone: string }}
 */
export function deriveSubmissionDisplayStatus(submission = {}) {
  const displayStatus = submission.display_status ?? submission.displayStatus
  const displayTone = submission.display_tone ?? submission.displayTone
  if (displayStatus) {
    const fallbackTone = DISPLAY_STATUS_META[displayStatus]?.tone ?? getSubmissionStatusTone(submission.status)
    return { label: displayStatus, tone: displayTone || fallbackTone }
  }

  const isArbitrated = Boolean(submission.is_arbitrated ?? submission.isArbitrated)
  if (isArbitrated) return { label: '已仲裁', tone: 'purple' }

  const finalScore = submission.final_score ?? submission.finalScore
  if (finalScore !== null && finalScore !== undefined) return { label: '已审核', tone: 'success' }

  return {
    label: getSubmissionStatusLabel(submission.status),
    tone: getSubmissionStatusTone(submission.status),
  }
}

/**
 * @description 审核工作流专用展示态：仅信任后端 display 字段或原始 status，不使用 final_score 兜底推导。
 * @param {{
 *   status?: string,
 *   is_arbitrated?: boolean,
 *   isArbitrated?: boolean,
 *   display_status?: string,
 *   displayStatus?: string,
 *   display_tone?: string,
 *   displayTone?: string
 * }} submission
 * @returns {{ label: string, tone: string }}
 */
export function deriveWorkflowSubmissionStatus(submission = {}) {
  const displayStatus = submission.display_status ?? submission.displayStatus
  const displayTone = submission.display_tone ?? submission.displayTone
  if (displayStatus) {
    const fallbackTone = DISPLAY_STATUS_META[displayStatus]?.tone ?? getSubmissionStatusTone(submission.status)
    return { label: displayStatus, tone: displayTone || fallbackTone }
  }
  const isArbitrated = Boolean(submission.is_arbitrated ?? submission.isArbitrated)
  if (isArbitrated) return { label: '已仲裁', tone: 'purple' }
  return {
    label: getSubmissionStatusLabel(submission.status),
    tone: getSubmissionStatusTone(submission.status),
  }
}

/**
 * @description 是否处于待办审核状态。
 * @param {{ status?: string }} submission
 * @returns {boolean}
 */
export function isPendingSubmission(submission = {}) {
  return submission.status === 'submitted' || submission.status === 'under_review'
}

/**
 * @description 是否处于已办状态（统一口径：按业务状态判定）。
 * @param {{ status?: string }} submission
 * @returns {boolean}
 */
export function isDoneSubmission(submission = {}) {
  return submission.status === 'approved' || submission.status === 'rejected'
}

/**
 * @description 申诉状态样式映射（标签由函数动态生成，避免角色称呼写死）。
 */
const APPEAL_STATUS_META = {
  pending: { className: 'bg-amber-100 text-amber-800' },
  approved: { className: 'bg-green-100 text-green-800' },
  rejected: { className: 'bg-red-100 text-red-800' },
  escalated: { className: 'bg-purple-100 text-purple-800' },
  escalated_to_admin: { className: 'bg-indigo-100 text-indigo-800' },
}

/**
 * @description 获取申诉状态标签。
 * @param {string} status
 * @param {{directorLabel?: string, superAdminLabel?: string}} [roleLabels]
 * @returns {string}
 */
export function getAppealStatusLabel(status, roleLabels = {}) {
  const directorLabel = roleLabels.directorLabel || '等级3角色'
  const superAdminLabel = roleLabels.superAdminLabel || '等级5角色'
  const map = {
    pending: '待处理',
    approved: '已通过',
    rejected: '已驳回',
    escalated: `已上报${directorLabel}`,
    escalated_to_admin: `已上报${superAdminLabel}`,
  }
  return map[status] ?? status ?? '—'
}

/**
 * @description 获取申诉状态样式类。
 * @param {string} status
 * @returns {string}
 */
export function getAppealStatusClass(status) {
  return APPEAL_STATUS_META[status]?.className ?? 'bg-slate-100 text-slate-600'
}
