/**
 * 审核与评分 API：待审列表、审核详情、初审、打分、仲裁、批量导入。
 * 使用 src/api/axios.js 的 api 实例（baseURL 已为 /api/v1，token 已自动带）。
 */
import api from './axios'

/**
 * 审核任务列表
 * @param {Object} [params] - { status?: string, category?: 'all'|'disputed' }
 * @returns {Promise<Array>} 提交列表（含 has_score_dispute 标记）
 */
export function getReviewTasks(params = {}) {
  return api.get('/review/tasks/', { params }).then((res) => {
    const data = res.data
    return Array.isArray(data) ? data : (data?.results ?? [])
  })
}

/**
 * 某条提交的审核视图（含详情、佐证）
 * @param {number} id - 提交 ID
 * @returns {Promise<Object>}
 */
export function getReviewSubmission(id) {
  return api.get(`/review/submissions/${id}/`).then((res) => res.data)
}

/**
 * 获取审核题目化列表
 * @param {number} id - 提交 ID
 * @returns {Promise<Array>}
 */
export function getReviewQuestions(id) {
  return api.get(`/review/submissions/${id}/questions/`).then((res) => {
    const data = res.data
    return Array.isArray(data) ? data : (data?.results ?? [])
  })
}

/**
 * 辅导员初审（将状态改为 under_review）
 * @param {number} id - 提交 ID
 * @returns {Promise<Object>} 更新后的提交
 */
export function initialReview(id) {
  return api.post(`/review/submissions/${id}/initial/`).then((res) => res.data)
}

/**
 * 当前用户可见的评分列表
 * @param {number} id - 提交 ID
 * @returns {Promise<Array>} 评分记录列表
 */
export function getReviewScores(id) {
  return api.get(`/review/submissions/${id}/scores/`).then((res) => {
    const data = res.data
    return Array.isArray(data) ? data : (data?.results ?? [])
  })
}

/**
 * 评审教师打分（双评自动区分 round_type）
 * @param {number} id - 提交 ID
 * @param {Object} body - { indicator_id: number, score: number, comment?: string }
 * @returns {Promise<Object>} 评分记录
 */
export function createReviewScore(id, body) {
  return api.post(`/review/submissions/${id}/scores/`, body).then((res) => res.data)
}

/**
 * 仲裁打分
 * @param {number} id - 提交 ID
 * @param {Object} body - { indicator_id: number, score: number, comment?: string }
 * @returns {Promise<Object>} 仲裁记录
 */
export function arbitrateScore(id, body) {
  return api.post(`/review/submissions/${id}/arbitrate/`, body).then((res) => res.data)
}

/**
 * 整套仲裁（批量）
 * @param {number} id - 提交 ID
 * @param {Object} body - { confirm_token: string, scores: Array<{indicator_id, score, comment?}> }
 * @returns {Promise<Object>} { detail, submitted, skipped }
 */
export function batchArbitrateScore(id, body) {
  return api.post(`/review/submissions/${id}/batch-arbitrate/`, body).then((res) => res.data)
}

/**
 * 导入预检：解析 Excel 但不写库，返回阻断性错误和非阻断警告。
 * 预检通过（无阻断错误）时后端会返回 preview_token，有效期 15 分钟。
 * @param {FormData} formData - 含 project_id（number）和 file（Excel 文件）
 * @returns {Promise<{total_rows:number, errors:Array, warnings:Array, has_errors:boolean, preview_token:string|null}>}
 */
export function precheckImport(formData) {
  return api.post('/scoring/import/precheck/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 基于 preview_token 正式提交成绩导入（两阶段提交，推荐）。
 * 后端从缓存取预检快照直接写库，同时跳过 excluded_rows 指定的行。
 * @param {Object} options
 * @param {number} options.projectId - 项目 ID
 * @param {string} options.previewToken - 预检返回的 token
 * @param {number[]} [options.excludedRows=[]] - 要跳过的行号数组
 * @returns {Promise<Object>} 导入批次结果（含 error_log）
 */
export function commitScoreImport({ projectId, previewToken, excludedRows = [] }) {
  const formData = new FormData()
  formData.append('project_id', String(projectId))
  formData.append('preview_token', previewToken)
  formData.append('excluded_rows', JSON.stringify(excludedRows))
  return api.post('/scoring/import/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 下载成绩导入 Excel 模板（根据项目 import_config 动态生成）
 * @param {number} projectId - 项目 ID
 * @param {string} projectName - 项目名称（用于文件名）
 */
export async function downloadImportTemplate(projectId, projectName) {
  const resp = await api.get('/scoring/import/template/', {
    params: { project_id: projectId },
    responseType: 'blob',
  })
  const url = URL.createObjectURL(new Blob([resp.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = `导入模板_${projectName || projectId}.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}

// ---------------------------------------------------------------------------
// 学生助理（评卷助理）相关 API
// ---------------------------------------------------------------------------

/**
 * 查询某班级的学生助理列表（评审老师及以上）
 * @param {number} classId - 班级 ID
 * @returns {Promise<Object>} { class_id, assistants: [] }
 */
export function getAssistantList(classId) {
  return api.get('/review/assistant/list/', { params: { class_id: classId } }).then((res) => res.data)
}

/**
 * 指派学生为班级助理（评审老师及以上）
 * @param {Object} body - { student_id: number, class_id: number }
 * @returns {Promise<Object>}
 */
export function assignAssistant(body) {
  return api.post('/review/assistant/assign/', body).then((res) => res.data)
}

/**
 * 撤销学生助理身份（评审老师及以上）
 * @param {Object} body - { student_id: number, class_id: number }
 * @returns {Promise<Object>}
 */
export function revokeAssistant(body) {
  return api.delete('/review/assistant/revoke/', { data: body }).then((res) => res.data)
}

/**
 * 学生助理查看待评分任务列表
 * @returns {Promise<Array>}
 */
export function getAssistantTasks() {
  return api.get('/review/assistant-tasks/').then((res) => {
    const data = res.data
    return Array.isArray(data) ? data : (data?.results ?? [])
  })
}

/**
 * 生成项目双评任务分配
 * @param {number} projectId - 项目 ID
 * @returns {Promise<Object>}
 */
export function generateReviewAssignments(projectId) {
  return api.post('/review/assignments/generate/', { project_id: projectId }).then((res) => res.data)
}

/**
 * 获取项目分配概览
 * @param {number} projectId
 * @returns {Promise<Object>}
 */
export function getProjectAssignmentSummary(projectId) {
  return api.get('/review/assignments/summary/', { params: { project_id: projectId } }).then((res) => res.data)
}

/**
 * 辅导员放行任务到学生助理
 * @param {Object} payload
 * @param {number} payload.project_id - 项目 ID
 * @param {number[]} [payload.submission_ids] - 指定提交 ID（不传则放行全部）
 * @param {number[]} [payload.assistant_user_ids] - 指定助理用户（不传则自动选择）
 * @param {boolean} [payload.reuse_latest] - 复用上次分配的助理
 * @param {boolean} [payload.force_reassign] - 强制覆盖已有助理任务
 * @returns {Promise<Object>}
 */
export function releaseAssignments(payload) {
  return api.post('/review/assignments/release/', payload).then((res) => res.data)
}

/**
 * 发起模块异议上报（审核模块）。
 * @param {number} submissionId - 提交 ID
 * @param {number} indicatorId - 指标 ID
 * @param {string} reason - 异议理由
 * @param {File[]} files - 附件列表
 * @returns {Promise<Object>}
 */
export function createReviewObjection(submissionId, indicatorId, reason, files = []) {
  const form = new FormData()
  form.append('indicator_id', String(indicatorId))
  form.append('reason', reason)
  for (const file of files) {
    form.append('files', file)
  }
  return api.post(`/review/submissions/${submissionId}/objections/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 获取审核异议工单列表。
 * @param {Object} params - 过滤参数
 * @returns {Promise<Array>}
 */
export function getReviewObjections(params = {}) {
  return api.get('/review/objections/', { params }).then((res) => {
    const data = res.data
    return Array.isArray(data) ? data : (data?.results ?? [])
  })
}

/**
 * 获取审核异议工单详情。
 * @param {number} id - 工单 ID
 * @returns {Promise<Object>}
 */
export function getReviewObjection(id) {
  return api.get(`/review/objections/${id}/`).then((res) => res.data)
}

/**
 * 处理审核异议工单。
 * @param {number} id - 工单 ID
 * @param {{action:string,resolved_score?:number,resolution_comment?:string}} body - 处理请求体
 * @returns {Promise<Object>}
 */
export function handleReviewObjection(id, body) {
  return api.post(`/review/objections/${id}/handle/`, body).then((res) => res.data)
}
