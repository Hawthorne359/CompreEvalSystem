/**
 * Axios 实例：baseURL、JWT 注入、SSO session_key 注入、刷新与 401 处理。
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  // 将缓存的公网 IP 注入自定义头，由后端中间件写入 external_ip 字段
  const publicIp = localStorage.getItem('publicIp')
  if (publicIp) config.headers['X-Client-Public-IP'] = publicIp
  // 注入 SSO 会话令牌，后端 SSOMiddleware 用于单点登录踢出校验
  const sessionKey = localStorage.getItem('sessionKey')
  if (sessionKey) config.headers['X-Session-Key'] = sessionKey
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    const status = err.response?.status
    const code = err.response?.data?.code

    // 单点登录踢出：账号已在其他设备登录，当前会话失效
    if (status === 401 && code === 'SESSION_REPLACED') {
      // 清除本地认证信息，防止重复触发
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      localStorage.removeItem('sessionKey')
      // 通过 sessionReplacedBus 通知全局弹窗组件显示安全提醒
      import('@/utils/sessionBus').then(({ sessionBus }) => {
        sessionBus.emit('session-replaced')
      })
      return Promise.reject(err)
    }

    if (status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh')
      if (refresh) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh/', { refresh })
          localStorage.setItem('access', data.access)
          original.headers.Authorization = `Bearer ${data.access}`
          return api(original)
        } catch (_) {
          localStorage.removeItem('access')
          localStorage.removeItem('refresh')
          localStorage.removeItem('sessionKey')
          window.location.href = '/login'
        }
      } else {
        if (!original.url?.includes('/auth/login')) window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
