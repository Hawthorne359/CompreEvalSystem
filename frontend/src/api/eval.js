/**
 * 测评模块 API：测评周期、项目、指标、权重规则、评审规则。
 * 使用 src/api/axios.js 的 api 实例（baseURL 已为 /api/v1，token 已自动带）。
 */
import api from './axios'

/**
 * 测评周期列表
 * @returns {Promise<Array>} 周期列表
 */
export function getSeasons() {
  return api.get('/seasons/').then((res) => (Array.isArray(res.data) ? res.data : res.data?.results ?? []))
}

/**
 * 更新测评周期
 * @param {number} seasonId
 * @param {Object} body - { name?, academic_year?, semester?, status?, start_time?, end_time? }
 * @returns {Promise<Object>}
 */
export function updateSeason(seasonId, body) {
  return api.patch(`/seasons/${seasonId}/`, body).then((res) => res.data)
}

/**
 * 创建测评周期
 * @param {Object} body - { name, academic_year, semester, status?, start_time?, end_time? }
 * @returns {Promise<Object>}
 */
export function createSeason(body) {
  return api.post('/seasons/', body).then((res) => res.data)
}

/**
 * 删除测评周期（需超管权限 + 密码确认 token）
 * @param {number} seasonId
 * @param {Object} body - { confirm_token, reason }
 * @returns {Promise<Object>}
 */
export function deleteSeason(seasonId, body) {
  return api.delete(`/seasons/${seasonId}/delete/`, { data: body }).then((res) => res.data)
}

/**
 * 批量修改测评周期状态
 * @param {number[]} seasonIds
 * @param {'draft'|'ongoing'|'closed'} status
 * @returns {Promise<Object>}
 */
export function batchUpdateSeasonsStatus(seasonIds, status) {
  return api.post('/seasons/batch-status/', { season_ids: seasonIds, status }).then((res) => res.data)
}

/**
 * 批量删除测评周期（需超管权限 + 密码确认 token）
 * @param {number[]} seasonIds
 * @param {Object} body - { confirm_token, reason }
 * @returns {Promise<Object>}
 */
export function batchDeleteSeasons(seasonIds, body) {
  return api.post('/seasons/batch-delete/', { season_ids: seasonIds, ...body }).then((res) => res.data)
}

/**
 * 某周期下的项目列表
 * @param {number} seasonId
 * @returns {Promise<Array>}
 */
export function getSeasonProjects(seasonId) {
  return api.get(`/seasons/${seasonId}/projects/`).then((res) => (Array.isArray(res.data) ? res.data : res.data?.results ?? []))
}

/**
 * 在某周期下创建项目
 * @param {number} seasonId
 * @param {Object} body - { name, description?, status?, allow_late_submit?, late_submit_deadline? }
 * @returns {Promise<Object>}
 */
export function createProject(seasonId, body) {
  return api.post(`/seasons/${seasonId}/projects/`, body).then((res) => res.data)
}

/**
 * 项目详情
 * @param {number} projectId
 * @returns {Promise<Object>}
 */
export function getProject(projectId) {
  return api.get(`/projects/${projectId}/`).then((res) => res.data)
}

/**
 * 更新项目
 * @param {number} projectId
 * @param {Object} body - 同创建字段
 * @returns {Promise<Object>}
 */
export function updateProject(projectId, body) {
  return api.patch(`/projects/${projectId}/`, body).then((res) => res.data)
}

/**
 * 删除测评项目（需超管权限 + 密码确认 token）
 * @param {number} projectId
 * @param {Object} body - { confirm_token, reason }
 * @returns {Promise<Object>}
 */
export function deleteProject(projectId, body) {
  return api.delete(`/projects/${projectId}/delete/`, { data: body }).then((res) => res.data)
}

/**
 * 批量修改测评项目状态
 * @param {number[]} projectIds
 * @param {'draft'|'ongoing'|'closed'} status
 * @returns {Promise<Object>}
 */
export function batchUpdateProjectsStatus(projectIds, status) {
  return api.post('/projects/batch-status/', { project_ids: projectIds, status }).then((res) => res.data)
}

/**
 * 批量删除测评项目（需超管权限 + 密码确认 token）
 * @param {number[]} projectIds
 * @param {Object} body - { confirm_token, reason }
 * @returns {Promise<Object>}
 */
export function batchDeleteProjects(projectIds, body) {
  return api.post('/projects/batch-delete/', { project_ids: projectIds, ...body }).then((res) => res.data)
}

/**
 * 项目指标树形结构（一级指标嵌套子项，只读）
 * @param {number} projectId
 * @returns {Promise<Array>} 一级指标数组，每项含 children 子数组
 */
export function getIndicatorTree(projectId) {
  return api.get(`/projects/${projectId}/indicators/tree/`).then((res) => (Array.isArray(res.data) ? res.data : res.data?.results ?? []))
}

/**
 * 创建指标（一级或二级）
 * @param {number} projectId
 * @param {Object} body - { name, category?, parent?, max_score?, weight?, agg_formula?, score_source?, description?, order? }
 * @returns {Promise<Object>}
 */
export function createIndicator(projectId, body) {
  return api.post(`/projects/${projectId}/indicators/`, body).then((res) => res.data)
}

/**
 * 更新指标
 * @param {number} projectId
 * @param {number} indicatorId
 * @param {Object} body
 * @returns {Promise<Object>}
 */
export function updateIndicator(projectId, indicatorId, body) {
  return api.patch(`/projects/${projectId}/indicators/${indicatorId}/`, body).then((res) => res.data)
}

/**
 * 删除指标（删除一级指标会级联删除其所有子项）
 * @param {number} projectId
 * @param {number} indicatorId
 * @returns {Promise<void>}
 */
export function deleteIndicator(projectId, indicatorId) {
  return api.delete(`/projects/${projectId}/indicators/${indicatorId}/`)
}

/**
 * 总分权重规则（GET 可能自动创建）
 * @param {number} projectId
 * @returns {Promise<Object>} { formula_type, formula_config, ... }
 */
export function getWeightRule(projectId) {
  return api.get(`/projects/${projectId}/weight-rule/`).then((res) => res.data)
}

/**
 * 更新总分权重规则
 * @param {number} projectId
 * @param {Object} body - { formula_type?, formula_config? } 如 formula_config: { "A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2 }
 * @returns {Promise<Object>}
 */
export function updateWeightRule(projectId, body) {
  return api.patch(`/projects/${projectId}/weight-rule/`, body).then((res) => res.data)
}

/**
 * 双评/仲裁规则
 * @param {number} projectId
 * @returns {Promise<Object>}
 */
export function getReviewRule(projectId) {
  return api.get(`/projects/${projectId}/review-rule/`).then((res) => res.data)
}

/**
 * 更新双评/仲裁规则
 * @param {number} projectId
 * @param {Object} body - { dual_review_enabled?, single_review_mode?, score_diff_threshold?, overall_score_diff_threshold?, module_diff_thresholds?, final_score_rule?, allow_view_other_scores?, require_arbitration_above_threshold? }
 *   final_score_rule: 'average'|'max'|'first'
 * @returns {Promise<Object>}
 */
export function updateReviewRule(projectId, body) {
  return api.patch(`/projects/${projectId}/review-rule/`, body).then((res) => res.data)
}

/**
 * 获取项目配置模板列表
 * @returns {Promise<Array>}
 */
export function getProjectConfigTemplates() {
  return api.get('/project-config-templates/').then((res) => (Array.isArray(res.data) ? res.data : res.data?.results ?? []))
}

/**
 * 更新模板元信息（名称/可见范围）
 * @param {number} templateId
 * @param {Object} body - { name?, visibility? }
 * @returns {Promise<Object>}
 */
export function updateProjectConfigTemplate(templateId, body) {
  return api.patch(`/project-config-templates/${templateId}/`, body).then((res) => res.data)
}

/**
 * 删除模板
 * @param {number} templateId
 * @returns {Promise<Object>}
 */
export function deleteProjectConfigTemplate(templateId) {
  return api.delete(`/project-config-templates/${templateId}/`).then((res) => res.data)
}

/**
 * 将当前项目配置保存为模板
 * @param {number} projectId
 * @param {Object} body - { name, visibility?, sections? }
 * @returns {Promise<Object>}
 */
export function saveProjectConfigTemplate(projectId, body) {
  return api.post(`/projects/${projectId}/config-templates/save/`, body).then((res) => res.data)
}

/**
 * 将模板应用到项目
 * @param {number} projectId
 * @param {number} templateId
 * @param {Object} body - { sections? }
 * @returns {Promise<Object>}
 */
export function applyProjectConfigTemplate(projectId, templateId, body) {
  return api.post(`/projects/${projectId}/config-templates/${templateId}/apply/`, body).then((res) => res.data)
}

/**
 * 导出已保存的模板为 JSON 文件（返回 Blob）
 * @param {number} templateId
 * @returns {Promise<{blob: Blob, filename: string}>}
 */
export function exportProjectConfigTemplate(templateId) {
  return api
    .get(`/project-config-templates/${templateId}/export/`, { responseType: 'blob' })
    .then((res) => {
      const disposition = res.headers['content-disposition'] || ''
      const match = disposition.match(/filename\*?=(?:UTF-8'')?([^;]+)/i)
      const filename = match ? decodeURIComponent(match[1].replace(/"/g, '')) : `template_${templateId}.json`
      return { blob: res.data, filename }
    })
}

/**
 * 从 JSON 文件导入模板到模板库
 * @param {FormData} formData - 包含 file 字段（JSON 文件），可选 name 和 visibility 字段
 * @returns {Promise<Object>}
 */
export function importProjectConfigTemplate(formData) {
  return api
    .post('/project-config-templates/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((res) => res.data)
}

/**
 * 将当前项目配置直接导出为 JSON 文件，不入库（返回 Blob）
 * @param {number} projectId
 * @param {Object} body - { sections: string[], name?: string }
 * @returns {Promise<{blob: Blob, filename: string}>}
 */
export function exportCurrentProjectConfig(projectId, body) {
  return api
    .post(`/projects/${projectId}/config-templates/export/`, body, { responseType: 'blob' })
    .then((res) => {
      const disposition = res.headers['content-disposition'] || ''
      const match = disposition.match(/filename\*?=(?:UTF-8'')?([^;]+)/i)
      const filename = match ? decodeURIComponent(match[1].replace(/"/g, '')) : `project_${projectId}_config.json`
      return { blob: res.data, filename }
    })
}

/**
 * 获取项目统一导入配置。
 * @param {number} projectId
 * @returns {Promise<{project_id:number,project_name:string,import_config:Object,module_categories:string[]}>}
 */
export function getProjectImportConfig(projectId) {
  return api.get(`/projects/${projectId}/import-config/`).then((res) => res.data)
}

/**
 * 更新项目统一导入配置。
 * @param {number} projectId
 * @param {Object} importConfig
 * @returns {Promise<{detail:string, import_config:Object}>}
 */
export function updateProjectImportConfig(projectId, importConfig) {
  return api.patch(`/projects/${projectId}/import-config/`, { import_config: importConfig }).then((res) => res.data)
}

export function getReportVisibilityConfig(projectId) {
  return api.get(`/projects/${projectId}/report-visibility/`).then((res) => res.data)
}

export function updateReportVisibilityConfig(projectId, config) {
  return api.patch(`/projects/${projectId}/report-visibility/`, { report_visibility_config: config }).then((res) => res.data)
}

