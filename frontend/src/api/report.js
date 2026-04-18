/**
 * 成绩报表 API。
 * 使用 src/api/axios.js 的 api 实例（baseURL 已为 /api/v1，token 已自动带）。
 */
import api from './axios'

/**
 * @description 将 blob 错误体解析为可读错误消息。
 * @param {any} error
 * @returns {Promise<string>}
 */
async function resolveBlobErrorMessage(error) {
  const detail = error?.response?.data?.detail
  if (detail) return String(detail)
  const blob = error?.response?.data
  if (!(blob instanceof Blob)) {
    if (error?.response?.status === 404) {
      return '未找到对应导出资源：可能是项目、映射或模板已失效，请重新选择后再试'
    }
    return '导出失败，请稍后重试'
  }
  try {
    const text = await blob.text()
    if (!text) return '导出失败，请稍后重试'
    const parsed = JSON.parse(text)
    const normalized = parsed?.detail || text
    if (String(normalized).trim().toLowerCase() === 'not found') {
      return '未找到对应导出资源：可能是项目、映射或模板已失效，请重新选择后再试'
    }
    return normalized
  } catch {
    return '导出失败，请稍后重试'
  }
}

/**
 * 本人各项目得分与明细（学生视角）
 * @returns {Promise<Array<{submission: Object, final_score: number|null, score_detail: Object|null}>>}
 */
export function getMyReport() {
  return api.get('/report/student/me/').then((res) => res.data)
}

/**
 * 学生端单份提交的模块化成绩详情。
 * @param {number} submissionId - 提交 ID
 * @returns {Promise<{
 *  submission:Object,
 *  final_score:number|null,
 *  global_evidences:Array<{id:number,name:string,file:string,category:string,indicator_id:number|null}>,
 *  items:Array<{
 *    indicator_id:number,
 *    indicator_name:string,
 *    score_source:string,
 *    is_record_only:boolean,
 *    section_name:string,
 *    subsection_name:string,
 *    max_score:string|null,
 *    self_score:string|null,
 *    imported_score:string|null,
 *    reviewer_score:string|null,
 *    arbitration_score:string|null,
 *    final_adopted_score:string|null,
 *    is_arbitrated:boolean,
 *    score_records:Array<{
 *      logical_round_label:string,
 *      score:string,
 *      reviewer_name:string,
 *      score_channel:string,
 *      created_at:string|null
 *    }>,
 *    evidences:Array<{id:number,name:string,file:string,category:string,indicator_id:number|null}>
 *  }>
 * }>}
 */
export function getStudentSubmissionReportDetail(submissionId) {
  return api.get(`/report/student/submissions/${submissionId}/detail/`).then((res) => res.data)
}

export function getStudentSubmissionRanking(submissionId) {
  return api.get(`/report/student/submissions/${submissionId}/ranking/`).then((res) => res.data)
}

/**
 * 某项目按班级等汇总（主任/管理员）
 * @param {number} projectId - 测评项目 ID
 * @returns {Promise<{project_id: number, project_name: string, by_class: Object, total_count: number}>}
 */
export function getProjectSummary(projectId, filters = {}) {
  return api.get(`/report/project/${projectId}/summary/`, { params: filters }).then((res) => res.data)
}

/**
 * 某项目排名列表（分页，主任/管理员）
 * @param {number} projectId - 测评项目 ID
 * @param {number} [page=1] - 页码
 * @param {number} [pageSize=20] - 每页条数
 * @returns {Promise<{total: number, page: number, page_size: number, results: Array}>}
 */
export function getProjectRanking(projectId, page = 1, pageSize = 20, filters = {}) {
  return api
    .get(`/report/project/${projectId}/ranking/`, {
      params: { page, page_size: pageSize, ...filters },
    })
    .then((res) => res.data)
}

/**
 * 获取院系列表（用于报表筛选）。
 * @returns {Promise<Array>}
 */
export function getDepartments() {
  return api.get('/departments/').then((res) => res.data)
}

/**
 * 获取专业列表（可按院系筛选）。
 * @param {Object} params
 * @returns {Promise<Array>}
 */
export function getMajors(params = {}) {
  return api.get('/majors/', { params }).then((res) => res.data)
}

/**
 * 获取班级列表（可按院系/专业筛选）。
 * @param {Object} params
 * @returns {Promise<Array>}
 */
export function getClasses(params = {}) {
  return api.get('/classes/', { params }).then((res) => res.data)
}

/**
 * 从 Content-Disposition 响应头提取文件名，优先使用 UTF-8 编码的 filename*。
 * @param {Object} headers - axios 响应头对象
 * @returns {string|null}
 */
function _extractFilenameFromHeaders(headers) {
  const cd = headers['content-disposition'] || ''
  const utf8Match = cd.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match) {
    try {
      return decodeURIComponent(utf8Match[1])
    } catch {
      // fallthrough
    }
  }
  const plainMatch = cd.match(/filename="?([^";]+)"?/i)
  if (plainMatch) return plainMatch[1].trim()
  return null
}

/**
 * 导出报表（Excel / Word / PDF），触发浏览器下载。
 * 通过 axios 以 blob 方式请求，携带 JWT，再用 <a> 标签触发本地下载。
 * @param {number} projectId - 测评项目 ID
 * @param {'xlsx'|'pdf'|'word'} [format='xlsx'] - 导出格式
 * @param {string} projectName - 项目名称（用于文件名备用）
 * @param {Object} [extraParams] - 扩展参数（mapping_id/template_id/筛选等）
 * @returns {Promise<void>}
 */
export function exportReport(projectId, format = 'xlsx', projectName = '', extraParams = {}) {
  return api
    .get(`/report/project/${projectId}/export/`, {
      params: { output_format: format, ...extraParams },
      responseType: 'blob',
    })
    .then((res) => {
      // 优先使用后端 Content-Disposition 中的文件名
      const serverFilename = _extractFilenameFromHeaders(res.headers)
      const safeName = projectName.replace(/[\\/:*?"<>|]/g, '_') || String(projectId)
      const ext = format === 'word' ? 'docx' : format
      const filename = serverFilename || `成绩报表_${safeName}.${ext}`
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    })
    .catch(async (error) => {
      const message = await resolveBlobErrorMessage(error)
      const normalized = error || new Error(message)
      normalized.response = normalized.response || {}
      normalized.response.data = { detail: message }
      throw normalized
    })
}

/**
 * 兼容式导出入口：
 * - 统一格式取值（word/pdf/xlsx）
 * - 仅携带 output_format（避免 DRF 将 format=word 误判为渲染器格式导致 404）
 * @param {{
 *  projectId:number|string,
 *  format:string,
 *  projectName?:string,
 *  extraParams?:Object
 * }} options
 * @returns {Promise<void>}
 */
export function exportReportWithCompat(options) {
  const projectId = options?.projectId
  const projectName = options?.projectName || ''
  const extraParams = options?.extraParams || {}
  const normalized = String(options?.format || extraParams.output_format || extraParams.format || 'xlsx').toLowerCase()
  const finalFormat = normalized === 'word' || normalized === 'pdf' ? normalized : 'xlsx'
  return exportReport(projectId, finalFormat, projectName, {
    ...extraParams,
    output_format: finalFormat,
  })
}

/**
 * 获取项目可映射字段。
 * @param {number} projectId
 * @param {Object} [params]
 * @returns {Promise<{project_id:number,project_name:string,fields:Array,all_fields:Array,field_groups:Array}>}
 */
export function getExportFields(projectId, params = {}) {
  return api.get(`/report/project/${projectId}/export/fields/`, { params }).then((res) => res.data)
}

/**
 * 获取当前用户在项目下的常用字段偏好。
 * @param {number} projectId
 * @returns {Promise<Object>}
 */
export function getExportCommonFields(projectId) {
  return api.get(`/report/project/${projectId}/export/common-fields/`).then((res) => res.data)
}

/**
 * 更新当前用户在项目下的常用字段偏好。
 * payload 支持：
 * - { common_field_keys: string[] } 全量覆盖
 * - { add_keys: string[], remove_keys: string[] } 增量更新
 * @param {number} projectId
 * @param {Object} payload
 * @returns {Promise<Object>}
 */
export function updateExportCommonFields(projectId, payload) {
  return api.patch(`/report/project/${projectId}/export/common-fields/`, payload).then((res) => res.data)
}

/**
 * 获取导出模板列表。
 * @param {Object} params
 * @returns {Promise<Array>}
 */
export function getExportTemplates(params = {}) {
  return api.get('/report/export/templates/', { params }).then((res) => res.data)
}

/**
 * 上传导出模板。
 * @param {FormData} formData
 * @returns {Promise<Object>}
 */
export function createExportTemplate(formData) {
  return api.post('/report/export/templates/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}

/**
 * 更新导出模板。
 * @param {number} id
 * @param {Object|FormData} payload
 * @returns {Promise<Object>}
 */
export function updateExportTemplate(id, payload) {
  return api.patch(`/report/export/templates/${id}/`, payload).then((res) => res.data)
}

/**
 * 删除导出模板。
 * @param {number} id
 * @returns {Promise<void>}
 */
export function deleteExportTemplate(id) {
  return api.delete(`/report/export/templates/${id}/`).then(() => {})
}

/**
 * 获取映射配置列表。
 * @param {Object} params
 * @returns {Promise<Array>}
 */
export function getExportMappings(params = {}) {
  return api.get('/report/export/mappings/', { params }).then((res) => res.data)
}

/**
 * 创建映射配置。
 * @param {Object} payload
 * @returns {Promise<Object>}
 */
export function createExportMapping(payload) {
  return api.post('/report/export/mappings/', payload).then((res) => res.data)
}

/**
 * 更新映射配置。
 * @param {number} id
 * @param {Object} payload
 * @returns {Promise<Object>}
 */
export function updateExportMapping(id, payload) {
  return api.patch(`/report/export/mappings/${id}/`, payload).then((res) => res.data)
}
