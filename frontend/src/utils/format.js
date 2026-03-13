/**
 * @module format
 * @description 统一的日期/时间格式化工具函数，消除各页面重复定义。
 */

/**
 * 格式化为完整日期时间（如 2026/03/09 14:30:00）。
 * @param {string|Date|null} val - ISO 时间字符串或 Date 对象
 * @returns {string}
 */
export function formatDateTime(val) {
  if (val == null || val === '') return '—'
  try {
    const d = new Date(val)
    if (Number.isNaN(d.getTime())) return String(val)
    return d.toLocaleString('zh-CN', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  } catch {
    return String(val)
  }
}

/**
 * 格式化为紧凑日期时间（如 2026/3/9 14:30），用于仪表盘等空间较小的场景。
 * @param {string|Date|null} ts - ISO 时间字符串或 Date 对象
 * @returns {string}
 */
export function formatTime(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN', { hour12: false })
}

/**
 * 格式化为纯日期（如 2026-03-09）。
 * @param {string|null} isoStr - ISO 日期/时间字符串
 * @returns {string}
 */
export function formatDate(isoStr) {
  if (!isoStr) return '—'
  return String(isoStr).slice(0, 10)
}
