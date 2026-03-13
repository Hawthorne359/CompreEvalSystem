/**
 * 认证状态：用户信息、角色、登录/登出/切换角色。
 */
import { defineStore } from 'pinia'
import api from '@/api/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    refresh: null,
    /** SSO 会话令牌，登录时由后端签发，随每个请求携带以实现单点登录踢出 */
    sessionKey: localStorage.getItem('sessionKey') || null,
    /** 客户端公网 IP，由登录时通过 ipify.org 获取，null 表示未获取或无外网 */
    publicIp: localStorage.getItem('publicIp') || null,
    /** 登录态恢复中的 Promise（用于并发去重） */
    restorePromise: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    currentRole: (state) => state.user?.current_role?.code || null,
    /**
     * 当前角色数字等级，未登录或无角色返回 -1。
     * LV0=学生  LV1=学生助理  LV2=评审老师（辅导员）  LV3=院系主任  LV5=超级管理员
     */
    currentLevel: (state) => state.user?.current_role?.level ?? -1,
    /**
     * 判断当前角色等级是否 >= n，用于替代写死 code 字符串的权限判断。
     * @returns {(n: number) => boolean}
     */
    levelAtLeast: (state) => (n) => (state.user?.current_role?.level ?? -1) >= n,
    /**
     * 是否为超级管理员（level >= 5）。
     * 原 LV4 管理员角色已移除，isAdmin 等同于 isSuperAdmin。
     */
    isAdmin: (state) => (state.user?.current_role?.level ?? -1) >= 5,
    /** 是否为超级管理员（level >= 5） */
    isSuperAdmin: (state) => (state.user?.current_role?.level ?? -1) >= 5,
  },
  actions: {
    async login(username, password) {
      const { data } = await api.post('/auth/login/', { username, password })
      this.token = data.access
      this.refresh = data.refresh
      this.user = data.user
      this.sessionKey = data.session_key || null
      localStorage.setItem('access', data.access)
      localStorage.setItem('refresh', data.refresh)
      if (data.session_key) {
        localStorage.setItem('sessionKey', data.session_key)
      }
      // 异步获取公网 IP（失败不影响登录流程）
      this._fetchPublicIp()
      return data
    },
    logout() {
      this.user = null
      this.token = this.refresh = this.sessionKey = null
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      localStorage.removeItem('sessionKey')
    },
    /**
     * 通过 ipify.org 获取客户端公网 IP，存入 store 和 localStorage。
     * 无外网时静默失败，publicIp 保持上次缓存值或 null。
     */
    async _fetchPublicIp() {
      try {
        const res = await fetch('https://api.ipify.org?format=json', { signal: AbortSignal.timeout(1500) })
        const json = await res.json()
        if (json.ip) {
          this.publicIp = json.ip
          localStorage.setItem('publicIp', json.ip)
        }
      } catch {
        // 无外网或超时，静默处理
      }
    },
    async fetchMe() {
      const { data } = await api.get('/users/me/')
      this.user = data
      return data
    },
    /**
     * 切换当前角色。
     * 后端角色信息存于数据库，JWT 仅含用户 ID，切换角色后 token 继续有效。
     * 若后端未来返回新 token，此处一并更新。
     * 切到 admin/superadmin 时后端要求传 password 二次验证。
     * @param {number} roleId - 角色 ID
     * @param {string} [password=''] - 切换到管理员角色时的登录密码
     * @returns {Promise<{ user, current_role, detail }>}
     */
    async switchRole(roleId, password = '') {
      const { data } = await api.post('/auth/switch-role/', { role_id: roleId, password })
      // 更新用户信息（current_role 已在后端写入 DB）
      if (data.user) {
        this.user = data.user
      } else {
        // 后端未返回完整 user 时重新请求
        await this.fetchMe()
      }
      // 兼容未来后端返回新 token 的情况
      if (data.access) {
        this.token = data.access
        localStorage.setItem('access', data.access)
      }
      if (data.refresh) {
        this.refresh = data.refresh
        localStorage.setItem('refresh', data.refresh)
      }
      return data
    },
    /**
     * 确保登录态可用：从 localStorage 恢复 token，并在必要时请求用户信息。
     * 并发场景会复用同一个恢复 Promise，避免重复请求 /users/me/。
     * @returns {Promise<boolean>} 是否已恢复为有效登录态
     */
    async ensureSession() {
      const access = localStorage.getItem('access')
      if (!access) {
        return false
      }
      this.token = this.token || access
      this.refresh = this.refresh || localStorage.getItem('refresh')
      if (this.user) return true
      if (this.restorePromise) return this.restorePromise

      this.restorePromise = this.fetchMe()
        .then(() => true)
        .catch((err) => {
          const status = err?.response?.status
          if (status === 401 || status === 403) this.logout()
          return false
        })
        .finally(() => {
          this.restorePromise = null
        })
      return this.restorePromise
    },
    /**
     * 兼容旧调用：刷新页面后恢复登录态（内部转调 ensureSession）。
     */
    restoreFromStorage() {
      this.ensureSession()
    },
  },
})
