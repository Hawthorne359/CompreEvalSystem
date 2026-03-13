/**
 * 页面级实时刷新 composable：监听 SSE data_changed 事件，自动调用页面刷新函数。
 *
 * 采用 leading+trailing 节流策略：首次事件立即触发刷新，后续事件在节流窗口内
 * 合并，窗口结束时若有新事件则再触发一次。适用于批量导入等持续事件流场景。
 *
 * 使用方式（每个页面仅需 2-3 行）：
 *
 * ```js
 * import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
 * useRealtimeRefresh(['submission', 'score'], loadList)
 *
 * // 详情页可传入 filter 精确匹配当前记录，避免无关事件触发刷新
 * useRealtimeRefresh('submission', loadDetail, {
 *   filter: (data) => data.id === Number(route.params.id)
 * })
 * ```
 *
 * @module useRealtimeRefresh
 */
import { onUnmounted } from 'vue'
import { onSSE, offSSE } from '@/composables/useEventStream'

const DEFAULT_THROTTLE_MS = 300

/**
 * 为当前页面注册实时数据刷新。
 *
 * @param {string|string[]} modelNames - 要监听的模型名称（与后端 signal publish 的 model 字段对应）
 * @param {Function} refreshFn - 数据变化时调用的刷新函数（如 loadList, loadAppeals）
 * @param {object} [options] - 可选配置
 * @param {number} [options.throttle=300] - 节流间隔（毫秒）
 * @param {number} [options.debounce] - 向后兼容旧参数名，等价于 throttle
 * @param {Function} [options.filter] - 可选过滤函数，返回 true 时才触发刷新（用于详情页按 ID 过滤）
 */
export function useRealtimeRefresh(modelNames, refreshFn, options = {}) {
  const models = Array.isArray(modelNames) ? modelNames : [modelNames]
  const intervalMs = options.throttle ?? options.debounce ?? DEFAULT_THROTTLE_MS
  const filterFn = options.filter ?? null
  let timer = null
  let pendingEvent = false

  /**
   * 安全调用刷新函数。
   */
  function doRefresh() {
    try {
      refreshFn()
    } catch (e) {
      console.error('[RealtimeRefresh] refresh error:', e)
    }
  }

  /**
   * Leading+trailing 节流：首次立即执行，窗口期内事件合并，
   * 窗口结束时若有待处理事件则再执行一次。
   */
  function throttledRefresh() {
    if (timer) {
      pendingEvent = true
      return
    }
    doRefresh()
    timer = setTimeout(() => {
      timer = null
      if (pendingEvent) {
        pendingEvent = false
        throttledRefresh()
      }
    }, intervalMs)
  }

  /**
   * SSE 事件处理器：过滤目标模型（及可选 filter）后触发节流刷新。
   *
   * @param {object} data - SSE 事件数据
   */
  function handler(data) {
    if (data && data.model && models.includes(data.model)) {
      if (filterFn && !filterFn(data)) return
      throttledRefresh()
    }
  }

  onSSE('data_changed', handler)

  onUnmounted(() => {
    offSSE('data_changed', handler)
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    pendingEvent = false
  })
}
