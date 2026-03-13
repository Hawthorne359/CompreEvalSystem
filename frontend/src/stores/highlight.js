/**
 * 通用行高亮 store。
 * 用于跨页面传递"最近操作的条目 ID"：
 * - 跳转详情/配置页前调用 set()，返回时在 onMounted 中调用 get() 读取并高亮
 * - 弹窗编辑场景可直接用组件本地 ref，无需此 store
 *
 * @module stores/highlight
 */
import { defineStore } from 'pinia'

export const useHighlightStore = defineStore('highlight', {
  state: () => ({
    /** @type {Record<string, number|string|null>} 按页面路由名存储高亮 ID */
    items: {},
  }),

  actions: {
    /**
     * 跳转前设置要高亮的条目 ID。
     * @param {string} page - 目标列表页的路由名或自定义 key
     * @param {number|string} id - 要高亮的条目 ID
     */
    set(page, id) {
      this.items[page] = id
    },

    /**
     * 读取并清除高亮 ID（一次性消费）。
     * @param {string} page
     * @returns {number|string|null}
     */
    pop(page) {
      const id = this.items[page] ?? null
      delete this.items[page]
      return id
    },
  },
})
