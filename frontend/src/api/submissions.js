/**
 * 学生提交与佐证 API。
 * 使用 src/api/axios.js 的 api 实例（baseURL 已为 /api/v1，token 已自动带）。
 */
import api from './axios'

/**
 * 进行中的测评任务列表（学生任务中心）
 * @returns {Promise<Array>}
 */
export function getSubmissionTasks() {
  return api.get('/submission-tasks/').then((res) => {
    const data = res.data
    return Array.isArray(data) ? data : (data?.results ?? [])
  })
}

/**
 * 创建草稿
 * @param {Object} body - { project: number, self_score?: object, remark?: string }
 * @returns {Promise<Object>}
 */
export function createSubmission(body) {
  return api.post('/submissions/', body).then((res) => res.data)
}

/**
 * 提交详情（含 evidences、project_name 等）
 * @param {number} id - 提交 ID
 * @returns {Promise<Object>}
 */
export function getSubmission(id) {
  return api.get(`/submissions/${id}/`).then((res) => res.data)
}

/**
 * 正式提交（将状态改为 submitted）
 * @param {number} id - 提交 ID
 * @returns {Promise<Object>}
 */
export function submitSubmission(id) {
  return api.post(`/submissions/${id}/submit/`).then((res) => res.data)
}

/**
 * 上传佐证（form-data）
 * @param {number} submissionId - 提交 ID
 * @param {FormData} formData - 含 file（必填）, category?, name?, indicator_id?
 * @returns {Promise<Object>} 佐证记录
 */
export function uploadEvidence(submissionId, formData) {
  return api.post(`/submissions/${submissionId}/evidences/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 删除佐证（软删除）
 * @param {number} submissionId - 提交 ID
 * @param {number} evidenceId - 佐证 ID
 * @returns {Promise<Object>}
 */
export function deleteEvidence(submissionId, evidenceId) {
  return api.delete(`/submissions/${submissionId}/evidences/${evidenceId}/`).then((res) => res.data)
}

/**
 * 获取题目化作答列表（模块/题目维度）。
 * @param {number} submissionId - 提交 ID
 * @returns {Promise<Array>}
 */
export function getSubmissionQuestions(submissionId) {
  return api.get(`/submissions/${submissionId}/questions/`).then((res) => {
    const data = res.data
    return Array.isArray(data) ? data : (data?.results ?? [])
  })
}

/**
 * 保存单题作答（分数 + 过程记录）。
 * @param {number} submissionId - 提交 ID
 * @param {number} indicatorId - 指标/题目 ID
 * @param {Object} body - { self_score?: number|string|null, process_record?: string }
 * @returns {Promise<Object>}
 */
export function saveSubmissionQuestion(submissionId, indicatorId, body) {
  return api.patch(`/submissions/${submissionId}/questions/${indicatorId}/`, body).then((res) => res.data)
}

/**
 * 学生发起补交申请（支持可选附件，向后端发送 form-data）。
 * @param {number} submissionId - 提交 ID
 * @param {string} reason - 申请理由（必填）
 * @param {File[]} [files=[]] - 可选附件列表
 * @returns {Promise<Object>} 补交申请记录
 */
export function requestLateSubmit(submissionId, reason, files = []) {
  const form = new FormData()
  form.append('reason', reason)
  for (const file of files) {
    form.append('files', file)
  }
  return api.post(`/submissions/${submissionId}/late-request/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 查询当前提交的补交通道状态
 * @param {number} submissionId - 提交 ID
 * @returns {Promise<{
 *   project_open: boolean,
 *   channel_active: boolean,
 *   channel_expires_at: string|null,
 *   channel_id: number|null,
 *   pending_request: boolean,
 *   pending_request_id: number|null
 * }>}
 */
export function getLateStatus(submissionId) {
  return api.get(`/submissions/${submissionId}/late-status/`).then((res) => res.data)
}
