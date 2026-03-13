/**
 * sessionBus：轻量事件总线，用于 Axios 拦截器与 Vue 组件之间的解耦通信。
 * 主要用途：SSO 单点登录踢出时，从 Axios 层触发全局安全提醒弹窗。
 */

/** @type {Map<string, Set<Function>>} */
const _listeners = new Map()

export const sessionBus = {
  /**
   * 注册事件监听器。
   * @param {string} event
   * @param {Function} handler
   */
  on(event, handler) {
    if (!_listeners.has(event)) _listeners.set(event, new Set())
    _listeners.get(event).add(handler)
  },
  /**
   * 注销事件监听器。
   * @param {string} event
   * @param {Function} handler
   */
  off(event, handler) {
    _listeners.get(event)?.delete(handler)
  },
  /**
   * 触发事件。
   * @param {string} event
   * @param {...any} args
   */
  emit(event, ...args) {
    _listeners.get(event)?.forEach((handler) => handler(...args))
  },
}
