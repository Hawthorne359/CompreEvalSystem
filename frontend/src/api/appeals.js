/**
 * 申诉模块 API。
 * 使用 src/api/axios.js 的 api 实例（baseURL 已为 /api/v1，token 已自动带）。
 */
import api from './axios'

/**
 * 发起整份提交申诉（原有接口，保持兼容）
 * @param {number} submissionId - 提交 ID
 * @param {string} reason - 申诉理由
 * @returns {Promise<Object>} 申诉记录
 */
export function createAppeal(submissionId, reason) {
  return api.post(`/submissions/${submissionId}/appeal/`, { reason }).then((res) => res.data)
}

/**
 * 发起整份提交申诉（支持附件）。
 * @param {number} submissionId - 提交 ID
 * @param {string} reason - 申诉理由
 * @param {File[]} files - 附件文件数组
 * @returns {Promise<Object>}
 */
export function createAppealWithFiles(submissionId, reason, files = []) {
  const form = new FormData()
  form.append('reason', reason)
  for (const file of files) form.append('files', file)
  return api.post(`/submissions/${submissionId}/appeal/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 发起指标级别申诉（针对统一导入或评审打分类型的具体指标）
 * @param {number} submissionId - 提交 ID
 * @param {number} indicatorId - 指标 ID
 * @param {string} reason - 申诉理由
 * @returns {Promise<Object>} 申诉记录
 */
export function createIndicatorAppeal(submissionId, indicatorId, reason) {
  return api
    .post(`/submissions/${submissionId}/appeal/`, { reason, indicator_id: indicatorId })
    .then((res) => res.data)
}

/**
 * 发起指标级申诉（支持附件）。
 * @param {number} submissionId - 提交 ID
 * @param {number} indicatorId - 指标 ID
 * @param {string} reason - 申诉理由
 * @param {File[]} files - 附件文件数组
 * @returns {Promise<Object>}
 */
export function createIndicatorAppealWithFiles(submissionId, indicatorId, reason, files = []) {
  const form = new FormData()
  form.append('reason', reason)
  form.append('indicator_id', String(indicatorId))
  for (const file of files) form.append('files', file)
  return api.post(`/submissions/${submissionId}/appeal/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 申诉列表（学生只看自己的，管理员/辅导员/主任看全部）
 * @param {Object} params - { status?: string, page?: number }
 * @returns {Promise<{ results: Array, count: number } | Array>}
 */
export function getAppeals(params = {}) {
  return api.get('/appeals/', { params }).then((res) => res.data)
}

/**
 * 申诉详情
 * @param {number} id - 申诉 ID
 * @returns {Promise<Object>}
 */
export function getAppeal(id) {
  return api.get(`/appeals/${id}/`).then((res) => res.data)
}

/**
 * 修改申诉理由（仅 pending 状态可修改）
 * @param {number} id - 申诉 ID
 * @param {string} reason - 新的申诉理由
 * @returns {Promise<Object>}
 */
export function updateAppealReason(id, reason) {
  return api.patch(`/appeals/${id}/`, { reason }).then((res) => res.data)
}

/**
 * 撤回申诉（删除申诉记录，仅 pending）
 * @param {number} id - 申诉 ID
 * @returns {Promise<void>}
 */
export function deleteAppeal(id) {
  return api.delete(`/appeals/${id}/`).then((res) => res.data)
}

/**
 * 评审老师处理申诉（通过/驳回/上报院系主任）
 * @param {number} id - 申诉 ID
 * @param {{ action: 'approved'|'rejected'|'escalate', handle_comment?: string }} body
 * @returns {Promise<Object>}
 */
export function handleAppeal(id, body) {
  return api.post(`/appeals/${id}/handle/`, body).then((res) => res.data)
}

/**
 * 院系主任处理上报申诉（通过/驳回）
 * @param {number} id - 申诉 ID
 * @param {{ action: 'approved'|'rejected', escalate_comment?: string }} body
 * @returns {Promise<Object>}
 */
export function handleEscalatedAppeal(id, body) {
  return api.post(`/appeals/${id}/escalate-handle/`, body).then((res) => res.data)
}

/**
 * 超级管理员处理上报申诉（终裁，可含评分覆盖）
 * @param {number} id - 申诉 ID
 * @param {{ action: 'approved'|'rejected', admin_comment?: string, score_overrides?: Array<{indicator_id:number, score:number, comment?:string}> }} body
 * @returns {Promise<Object>}
 */
export function handleAdminEscalatedAppeal(id, body) {
  return api.post(`/appeals/${id}/admin-handle/`, body).then((res) => res.data)
}

/**
 * 上传申诉附件（pending 且申诉人）。
 * @param {number} id - 申诉 ID
 * @param {File[]} files - 附件列表
 * @returns {Promise<Array>}
 */
export function uploadAppealAttachments(id, files = []) {
  const form = new FormData()
  for (const file of files) form.append('files', file)
  return api.post(`/appeals/${id}/attachments/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 删除申诉附件。
 * @param {number} id - 申诉 ID
 * @param {number} attachmentId - 附件 ID
 * @returns {Promise<Object>}
 */
export function deleteAppealAttachment(id, attachmentId) {
  return api.delete(`/appeals/${id}/attachments/${attachmentId}/`).then((res) => res.data)
}
