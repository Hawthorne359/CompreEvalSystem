/**
 * SSE 连接管理 composable：全局单例，管理 EventSource 长连接。
 *
 * 功能：
 * - 创建到 /api/v1/realtime/events/ 的 EventSource 连接
 * - JWT token 通过 query param 传递（EventSource 不支持自定义 header）
 * - 自动重连（EventSource 原生 + 手动 fallback）
 * - Token 过期时自动刷新并重连
 * - 收到 session_replaced 时触发 SSO 踢出弹窗
 * - 提供 on/off API 供页面级 composable 监听数据变化
 *
 * @module useEventStream
 */
import { sessionBus } from '@/utils/sessionBus'

const SSE_URL = '/api/v1/realtime/events/'
const RECONNECT_DELAY_BASE = 1000
const RECONNECT_DELAY_MAX = 30000

/** @type {EventSource|null} */
let _source = null
/** @type {Map<string, Set<Function>>} */
const _handlers = new Map()
let _reconnectTimer = null
let _reconnectAttempts = 0
let _stopped = false

/**
 * 注册事件监听器。
 *
 * @param {string} eventType - 事件类型（如 'data_changed', 'session_replaced'）
 * @param {Function} callback - 回调函数，参数为事件数据对象
 */
export function onSSE(eventType, callback) {
  if (!_handlers.has(eventType)) _handlers.set(eventType, new Set())
  _handlers.get(eventType).add(callback)
}

/**
 * 注销事件监听器。
 *
 * @param {string} eventType - 事件类型
 * @param {Function} callback - 要移除的回调函数
 */
export function offSSE(eventType, callback) {
  _handlers.get(eventType)?.delete(callback)
}

/**
 * 触发本地监听器。
 *
 * @param {string} eventType
 * @param {object} data
 */
function _dispatch(eventType, data) {
  _handlers.get(eventType)?.forEach((fn) => {
    try {
      fn(data)
    } catch (e) {
      console.error('[SSE] handler error:', e)
    }
  })
}

/**
 * 启动 SSE 连接。如果已有连接则先关闭。
 * 自动从 localStorage 读取 access token。
 */
export function startEventStream() {
  stopEventStream()
  _stopped = false

  const token = localStorage.getItem('access')
  if (!token) return

  const url = `${SSE_URL}?token=${encodeURIComponent(token)}`

  try {
    _source = new EventSource(url)
  } catch (e) {
    console.warn('[SSE] EventSource creation failed:', e)
    _scheduleReconnect()
    return
  }

  _source.onopen = () => {
    _reconnectAttempts = 0
  }

  _source.addEventListener('session_replaced', (e) => {
    let data = {}
    try { data = JSON.parse(e.data) } catch { /* ignore */ }
    stopEventStream()
    _dispatch('session_replaced', data)
    sessionBus.emit('session-replaced', data)
  })

  _source.addEventListener('data_changed', (e) => {
    let data = {}
    try { data = JSON.parse(e.data) } catch { /* ignore */ }
    _dispatch('data_changed', data)
  })

  _source.addEventListener('notification', (e) => {
    let data = {}
    try { data = JSON.parse(e.data) } catch { /* ignore */ }
    _dispatch('notification', data)
  })

  _source.addEventListener('import_progress', (e) => {
    let data = {}
    try { data = JSON.parse(e.data) } catch { /* ignore */ }
    _dispatch('import_progress', data)
  })

  _source.addEventListener('error', (e) => {
    let data = {}
    try { data = JSON.parse(e.data) } catch { /* ignore */ }
    if (data.detail === 'token invalid') {
      _tryRefreshAndReconnect()
      return
    }
  })

  _source.onerror = () => {
    if (_stopped) return
    _source?.close()
    _source = null
    _scheduleReconnect()
  }
}

/**
 * 停止 SSE 连接并清除重连定时器。
 */
export function stopEventStream() {
  _stopped = true
  if (_reconnectTimer) {
    clearTimeout(_reconnectTimer)
    _reconnectTimer = null
  }
  if (_source) {
    _source.close()
    _source = null
  }
  _reconnectAttempts = 0
}

/**
 * 调度重连：指数退避策略。
 */
function _scheduleReconnect() {
  if (_stopped) return
  if (_reconnectTimer) return
  const delay = Math.min(
    RECONNECT_DELAY_BASE * Math.pow(2, _reconnectAttempts),
    RECONNECT_DELAY_MAX,
  )
  _reconnectAttempts++
  _reconnectTimer = setTimeout(() => {
    _reconnectTimer = null
    if (!_stopped) startEventStream()
  }, delay)
}

/**
 * Token 过期时尝试刷新并重连。
 */
async function _tryRefreshAndReconnect() {
  const refresh = localStorage.getItem('refresh')
  if (!refresh) {
    stopEventStream()
    return
  }
  try {
    const resp = await fetch('/api/v1/auth/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!resp.ok) throw new Error('refresh failed')
    const data = await resp.json()
    localStorage.setItem('access', data.access)
    startEventStream()
  } catch {
    stopEventStream()
  }
}
