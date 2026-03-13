/**
 * 用户管理 API：列表（分页/筛选/搜索）、详情、创建、更新；角色列表；批量导入。
 * 使用 src/api/axios.js 的 api 实例（baseURL 已为 /api/v1，token 已自动带）。
 */
import api from './axios'

/**
 * 角色列表（只读，供新建/编辑用户时选择；不含超级管理员时由前端过滤）
 * @returns {Promise<Array<{ id, code, name, level, description }>>}
 */
export function getRoles() {
  return api.get('/roles/').then((res) => {
    const data = res.data
    return Array.isArray(data) ? data : (data?.results ?? [])
  })
}

/**
 * 用户列表（分页）
 * @param {Object} params - { page?, page_size?, is_active?, department?, class_obj?, role?, search? }
 * @returns {Promise<{ count: number, results: Array, next: string|null, previous: string|null }>}
 */
export function getUsers(params = {}) {
  return api.get('/users/', { params }).then((res) => res.data)
}

/**
 * 用户详情（含 user_roles）
 * @param {number} id - 用户 ID
 * @returns {Promise<Object>}
 */
export function getUser(id) {
  return api.get(`/users/${id}/`).then((res) => res.data)
}

/**
 * 创建用户
 * @param {Object} body - { username, password?, email?, ..., role_ids? } 含 role_ids 时可指定角色（不含超级管理员）
 * @returns {Promise<Object>}
 */
export function createUser(body) {
  return api.post('/users/', body).then((res) => res.data)
}

/**
 * 更新用户（含可选密码、角色修改）
 * @param {number} id - 用户 ID
 * @param {Object} body - 同创建字段，password、role_ids 可选
 * @returns {Promise<Object>}
 */
export function updateUser(id, body) {
  return api.patch(`/users/${id}/`, body).then((res) => res.data)
}

/**
 * 删除单个用户。
 * @param {number} id - 用户 ID
 * @returns {Promise<void>}
 */
export function deleteUser(id) {
  return api.delete(`/users/${id}/`).then(() => undefined)
}

/**
 * 批量启用/禁用用户。
 * @param {Array<number>} userIds - 用户 ID 列表
 * @param {boolean} isActive - 目标状态
 * @returns {Promise<{affected_count:number}>}
 */
export function batchSetUserActive(userIds, isActive) {
  return api.post('/users/batch/set-active/', {
    user_ids: userIds,
    is_active: isActive,
  }).then((res) => res.data)
}

/**
 * 批量重置用户密码。
 * @param {Array<number>} userIds - 用户 ID 列表
 * @param {string} newPassword - 新密码
 * @returns {Promise<{affected_count:number}>}
 */
export function batchResetUserPassword(userIds, newPassword) {
  return api.post('/users/batch/reset-password/', {
    user_ids: userIds,
    new_password: newPassword,
  }).then((res) => res.data)
}

/**
 * 批量重设角色（同一套角色覆盖应用到所有选中用户）。
 * @param {Array<number>} userIds - 用户 ID 列表
 * @param {Array<number>} roleIds - 角色 ID 列表
 * @param {Array<number>} responsibleClassIds - 负责班级 ID 列表（非学生角色生效）
 * @returns {Promise<{affected_count:number}>}
 */
export function batchSetUserRole(userIds, roleIds, responsibleClassIds = []) {
  return api.post('/users/batch/set-role/', {
    user_ids: userIds,
    role_ids: roleIds,
    responsible_class_ids: responsibleClassIds,
  }).then((res) => res.data)
}

/**
 * 批量删除用户。
 * @param {Array<number>} userIds - 用户 ID 列表
 * @returns {Promise<{affected_count:number}>}
 */
export function batchDeleteUsers(userIds) {
  return api.post('/users/batch/delete/', {
    user_ids: userIds,
  }).then((res) => res.data)
}

/**
 * 根据预检会话正式提交导入（后端异步执行，返回 202）。
 * @param {Object} payload
 * @param {string} payload.previewToken - 预检会话 token
 * @param {boolean} [payload.autoCreateMissing] - 是否自动创建缺失组织项
 * @param {Object} [payload.resolutionPayload] - 未知项映射
 * @param {Array<string>} [payload.excludedRows] - 排除行标识
 * @param {number|string} [payload.hashIterations] - 密码哈希迭代次数（空/default=默认120万）
 * @returns {Promise<Object>}
 */
export function commitUsersImportFromPreview(payload) {
  const formData = new FormData()
  formData.append('preview_token', payload.previewToken)
  if (payload.autoCreateMissing) {
    formData.append('auto_create_missing', '1')
  }
  if (payload.resolutionPayload && Object.keys(payload.resolutionPayload).length > 0) {
    formData.append('resolution_payload', JSON.stringify(payload.resolutionPayload))
  }
  if (payload.excludedRows && payload.excludedRows.length > 0) {
    formData.append('excluded_rows', JSON.stringify(payload.excludedRows))
  }
  if (payload.hashIterations && payload.hashIterations !== 'default') {
    formData.append('hash_iterations', String(payload.hashIterations))
  }
  if (payload.forceChangePassword === false) {
    formData.append('force_change_password', '0')
  }
  return api.post('/users/import/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 查询导入批次进度（SSE 断线降级方案）。
 * @param {number} batchId
 * @returns {Promise<Object>}
 */
export function getImportProgress(batchId) {
  return api.get(`/users/import/progress/${batchId}/`).then((res) => res.data)
}

