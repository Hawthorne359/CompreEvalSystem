/**
 * 工作台（Dashboard）API。
 * GET /api/v1/dashboard/ 返回与当前角色 level 匹配的聚合数据。
 * 超管/院系主任可通过 params 传递下钻参数。
 */
import api from './axios'

/**
 * 获取当前角色对应的工作台数据
 * @param {Object} [params] - 可选查询参数（如 { department_id, major_id }）
 * @returns {Promise<Object>}
 */
export function getDashboard(params = {}) {
  return api.get('/dashboard/', { params }).then((res) => res.data)
}

/**
 * 获取缺交名单数据（独立分页 + 筛选）
 * @param {Object} [params] - 查询参数
 * @param {string}  params.type       - unfilled | unsubmitted
 * @param {number}  [params.department] - 院系ID
 * @param {number}  [params.major]      - 专业ID
 * @param {number}  [params.class_obj]  - 班级ID
 * @param {string}  [params.search]     - 模糊搜索（姓名/学号）
 * @param {number}  [params.page]       - 页码
 * @param {number}  [params.page_size]  - 每页条数
 * @returns {Promise<Object>}
 */
export function getMissingSubmissionList(params = {}) {
  return api.get('/dashboard/missing-list/', { params }).then((res) => res.data)
}
