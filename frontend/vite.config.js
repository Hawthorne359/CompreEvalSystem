import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        /**
         * 将 Vite 收到的原始客户端 IP（局域网 IP）注入 X-Forwarded-For / X-Real-IP，
         * 使 Django 中间件能记录真实访问者 IP 而非 127.0.0.1。
         */
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            const raw = req.socket?.remoteAddress ?? ''
            // 去掉 IPv4-mapped IPv6 前缀 "::ffff:"
            const clientIp = raw.replace(/^::ffff:/, '')
            if (clientIp) {
              proxyReq.setHeader('X-Forwarded-For', clientIp)
              proxyReq.setHeader('X-Real-IP', clientIp)
            }
          })
        },
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
