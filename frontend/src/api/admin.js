/**
 * 系统管理模块 API：补交通道、操作日志、管理员改分、密码验证。
 * 使用 src/api/axios.js 的 api 实例（baseURL 已为 /api/v1，token 已自动带）。
 */
import api from './axios'

/**
 * 验证当前用户密码，返回有效期 5 分钟的一次性确认 token。
 * 用于高危操作（删除测评周期/项目）的二次鉴权。
 * @param {string} password - 用户密码
 * @returns {Promise<{ confirm_token: string }>}
 */
export function verifyPassword(password) {
  return api.post('/auth/verify-password/', { password })
}

/**
 * 当前用户修改自己的密码。
 * @param {string} oldPassword - 旧密码
 * @param {string} newPassword - 新密码
 * @returns {Promise<{ detail: string }>}
 */
export function changePassword(oldPassword, newPassword) {
  return api.post('/auth/change-password/', { old_password: oldPassword, new_password: newPassword }).then((res) => res.data)
}

/**
 * 获取操作日志列表（原审计日志）
 * @param {Object} [params] - 查询参数
 * @param {0|1} [params.is_abnormal] - 仅查异常：1；正常：0
 * @param {0|1} [params.is_audit_event] - 仅查审计事件：1
 * @param {string} [params.level] - INFO / NOTICE / WARNING / CRITICAL
 * @param {string} [params.module] - auth / users / org / eval / submission / scoring / appeal / report / system
 * @param {string} [params.action] - 操作码（模糊匹配）
 * @param {string} [params.username] - 用户名（模糊匹配）
 * @param {string} [params.date_from] - YYYY-MM-DD
 * @param {string} [params.date_to] - YYYY-MM-DD
 * @param {number} [params.page]
 * @returns {Promise<{results: Array, count: number}|Array>}
 */
export function getAuditLogs(params = {}) {
  return api.get('/audit/logs/', { params }).then((res) => res.data)
}

/**
 * 获取单条操作日志详情
 * @param {number} id - 日志 ID
 * @returns {Promise<Object>}
 */
export function getAuditLogDetail(id) {
  return api.get(`/audit/logs/${id}/`).then((res) => res.data)
}

/**
 * 导出操作日志（CSV 文件下载）
 * @param {Object} [params] - 与列表接口相同的查询参数
 * @returns {Promise<Blob>}
 */
export function exportAuditLogs(params = {}) {
  return api.get('/audit/logs/export/', {
    params,
    responseType: 'blob',
  })
}

/**
 * 获取当前登录用户自己的操作日志列表（所有角色均可访问）
 * @param {Object} [params]
 * @param {string} [params.level] - INFO / NOTICE / WARNING / CRITICAL
 * @param {string} [params.module] - auth / users / org / eval / submission / scoring / appeal / report / system
 * @param {string} [params.date_from] - YYYY-MM-DD
 * @param {string} [params.date_to] - YYYY-MM-DD
 * @param {number} [params.page]
 * @returns {Promise<{results: Array, count: number}|Array>}
 */
export function getMyLogs(params = {}) {
  return api.get('/audit/my-logs/', { params }).then((res) => res.data)
}

/**
 * 获取当前用户自己的操作日志单条详情
 * @param {number} id - 日志 ID
 * @returns {Promise<Object>}
 */
export function getMyLogDetail(id) {
  return api.get(`/audit/my-logs/${id}/`).then((res) => res.data)
}

/**
 * 管理员改分（写 CRITICAL 级审计日志），支持上传凭证文件
 * @param {Object} body
 * @param {number|string} body.submission_id - 提交 ID
 * @param {number} body.final_score - 新分数
 * @param {string} body.reason - 改分理由（必填）
 * @param {File} [body.evidence_file] - 改分凭证文件（可选）
 * @returns {Promise<Object>}
 */
export function scoreOverride({ submission_id, final_score, reason, evidence_file }) {
  const form = new FormData()
  form.append('submission_id', submission_id)
  form.append('final_score', final_score)
  form.append('reason', reason)
  if (evidence_file) form.append('evidence_file', evidence_file)
  return api
    .post('/admin/score-override/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((res) => res.data)
}

// ─────────────────────────── 补交申请管理 ────────────────────────────

/**
 * 管理员获取补交申请列表（含学生上传的佐证附件）
 * @param {Object} [params]
 * @param {string} [params.status] - pending / approved / rejected
 * @returns {Promise<Array>}
 */
export function getLateRequests(params = {}) {
  return api.get('/admin/late-requests/', { params }).then((res) => res.data)
}

/**
 * 管理员审批补交申请
 * @param {number} id - 申请 ID
 * @param {Object} body
 * @param {'approve'|'reject'} body.action - 操作
 * @param {string} body.comment - 处理意见/开启理由
 * @param {number} [body.hours] - 通道时长（approve 时必填，≥1）
 * @returns {Promise<Object>}
 */
export function handleLateRequest(id, body) {
  return api.post(`/admin/late-requests/${id}/handle/`, body).then((res) => res.data)
}

/**
 * 待推送中心：获取扁平化待推送补交记录列表（不按通道分组）。
 * @param {Object} [params]
 * @param {string} [params.keyword] - 学生姓名/学号关键词
 * @param {number|string} [params.season_id] - 周期 ID
 * @param {number|string} [params.project_id] - 项目 ID
 * @param {number|string} [params.department_id] - 院系 ID
 * @param {number|string} [params.major_id] - 专业 ID
 * @param {number|string} [params.class_id] - 班级 ID
 * @param {string} [params.date_from] - 起始日期（YYYY-MM-DD）
 * @param {string} [params.date_to] - 结束日期（YYYY-MM-DD）
 * @returns {Promise<Array>}
 */
export function getLatePendingSubmissions(params = {}) {
  return api.get('/admin/late-submissions/pending/', { params }).then((res) => res.data)
}

/**
 * 待推送中心：按提交记录批量推送到评审流程。
 * @param {number[]} submissionIds - 待推送提交 ID 列表
 * @returns {Promise<{ detail: string, pushed_count: number, invalid_count: number }>}
 */
export function batchPushPendingSubmissions(submissionIds) {
  return api.post('/admin/late-submissions/batch-push/', { submission_ids: submissionIds }).then((res) => res.data)
}

/**
 * 管理员获取补交通道列表
 * @param {Object} [params]
 * @param {'1'} [params.active_only] - 传 '1' 仅返回激活中的通道
 * @returns {Promise<Array>}
 */
export function getLateChannels(params = {}) {
  return api.get('/admin/late-channels/', { params }).then((res) => res.data)
}

/**
 * 管理员手动开启补交通道（针对个人或班级）
 * @param {Object} body
 * @param {'user'|'class'} body.scope_type - 范围类型
 * @param {string} [body.student_no] - 目标学号（scope_type=user 时至少提供其一）
 * @param {string} [body.username] - 目标用户名
 * @param {number} [body.user_id] - 目标用户 ID
 * @param {number} [body.class_id] - 目标班级 ID（scope_type=class 时必填）
 * @param {number} [body.project_id] - 限定项目 ID（可选）
 * @param {string} body.reason - 开启理由（必填）
 * @param {number} [body.hours=24] - 时长（≥1，默认 24）
 * @returns {Promise<Object>}
 */
export function createLateChannel(body) {
  return api.post('/admin/late-channels/', body).then((res) => res.data)
}

/**
 * 管理员手动关闭补交通道
 * @param {number} id - 通道 ID
 * @param {string} [comment] - 关闭说明（可选）
 * @returns {Promise<Object>}
 */
export function closeLateChannel(id, comment = '') {
  return api.post(`/admin/late-channels/${id}/close/`, { comment }).then((res) => res.data)
}

// ─────────────────────────── 个人中心 ────────────────────────────

/**
 * 获取当前用户最近 10 条登录记录
 * @returns {Promise<Array<{id:number, ip_address:string, external_ip:string, user_agent:string, created_at:string}>>}
 */
export function getLoginHistory() {
  return api.get('/users/me/login-history/').then((res) => res.data)
}

/**
 * 更新当前用户基本信息（仅 email、phone 可修改）
 * @param {{ email?: string, phone?: string }} data
 * @returns {Promise<Object>} 更新后的完整用户对象
 */
export function updateProfile(data) {
  return api.patch('/users/me/profile/', data).then((res) => res.data)
}
