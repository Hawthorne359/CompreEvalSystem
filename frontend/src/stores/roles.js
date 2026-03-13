/**
 * 角色元数据缓存：按 level 提供动态角色名称。
 */
import { defineStore } from 'pinia'
import { getRoles } from '@/api/users'

export const useRoleMetaStore = defineStore('roleMeta', {
  state: () => ({
    roleNameByLevel: {},
    loading: false,
    loaded: false,
  }),
  actions: {
    /**
     * 拉取角色字典并按 level 合并到本地缓存。
     */
    async ensureLoaded() {
      if (this.loaded || this.loading) return
      this.loading = true
      try {
        const roles = await getRoles()
        const map = {}
        for (const role of roles) {
          if (role?.name && role?.level != null) {
            map[role.level] = role.name
          }
        }
        this.roleNameByLevel = map
        this.loaded = true
      } finally {
        this.loading = false
      }
    },
    /**
     * 根据 level 获取角色显示名。
     * @param {number} level
     * @param {string} fallback
     * @returns {string}
     */
    nameByLevel(level, fallback = '') {
      if (this.roleNameByLevel[level]) return this.roleNameByLevel[level]
      if (fallback) return fallback
      if (level === null || level === undefined || Number.isNaN(Number(level))) return '未命名角色'
      return `等级${level}角色`
    },
  },
})
