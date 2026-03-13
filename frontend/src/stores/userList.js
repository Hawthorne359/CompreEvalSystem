/**
 * 用户列表状态持久化 store。
 * 用于从编辑页返回后恢复页码、筛选条件，并高亮刚编辑的行。
 */
import { defineStore } from 'pinia'

export const useUserListStore = defineStore('userList', {
  state: () => ({
    /** 是否需要从 store 恢复状态（从 UserForm 保存后返回时置为 true） */
    shouldRestore: false,
    /** 恢复的页码 */
    page: 1,
    /** 恢复的筛选条件 */
    filters: {
      isActive: '',
      department: '',
      major: '',
      grade: '',
      class_obj: '',
      role: '',
      search: '',
    },
    /** 刚编辑/创建的用户 ID，用于列表高亮 */
    lastEditedId: null,
  }),

  actions: {
    /**
     * 在跳转到编辑页前调用：保存当前页码与筛选，并标记需要恢复。
     * @param {number} page
     * @param {Object} filters
     */
    saveListState(page, filters) {
      this.page = page
      this.filters = { ...filters }
      this.shouldRestore = true
    },

    /**
     * 设置最近编辑/创建的用户 ID。
     * @param {number|null} id
     */
    setLastEdited(id) {
      this.lastEditedId = id
    },

    /** 高亮用完后清除，避免下次进入列表残留 */
    clearLastEdited() {
      this.lastEditedId = null
    },
  },
})
