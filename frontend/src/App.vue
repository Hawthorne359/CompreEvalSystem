<template>
  <router-view />
  <AppDialogHost />
  <!-- SSO 单点登录安全提醒弹窗：账号在其他设备登录时弹出 -->
  <Teleport to="body">
    <Transition name="sso-fade">
      <div
        v-if="showSSODialog"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sso-dialog-title"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden">
          <!-- 顶部警告色条 -->
          <div class="h-1.5 bg-gradient-to-r from-amber-400 to-red-500" />
          <div class="px-8 py-7">
            <!-- 图标 + 标题 -->
            <div class="flex items-center gap-3 mb-4">
              <span class="flex items-center justify-center w-10 h-10 rounded-full bg-amber-50">
                <svg class="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round"
                    d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                </svg>
              </span>
              <h2 id="sso-dialog-title" class="text-base font-semibold text-gray-800">
                账号安全提醒
              </h2>
            </div>
            <!-- 说明文字 -->
            <p class="text-sm text-gray-500 leading-relaxed mb-4">
              您的账号已在<span class="font-medium text-gray-700">其他设备</span>登录，
              当前会话已自动失效。
            </p>
            <!-- 新登录设备信息（如有） -->
            <div v-if="ssoDeviceInfo.device || ssoDeviceInfo.location" class="mb-4 px-4 py-3 rounded-xl bg-gray-50 border border-gray-100">
              <div v-if="ssoDeviceInfo.device" class="flex items-center gap-2 text-sm text-gray-600">
                <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25A2.25 2.25 0 015.25 3h13.5A2.25 2.25 0 0121 5.25z" />
                </svg>
                <span>{{ ssoDeviceInfo.device }}</span>
              </div>
              <div v-if="ssoDeviceInfo.location" class="flex items-center gap-2 text-sm text-gray-600 mt-1.5">
                <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                </svg>
                <span>{{ ssoDeviceInfo.location }}</span>
              </div>
              <div v-if="ssoDeviceInfo.ip" class="flex items-center gap-2 text-xs text-gray-400 mt-1.5">
                <svg class="w-3.5 h-3.5 text-gray-300 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 10.5a8.983 8.983 0 01-2.284 6.003" />
                </svg>
                <span>IP: {{ ssoDeviceInfo.ip }}</span>
              </div>
            </div>
            <p class="text-xs text-gray-400 mb-5">如非本人操作，请登录后立即修改密码。</p>
            <!-- 按钮 -->
            <button
              @click="handleSSOConfirm"
              class="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 text-white text-sm font-semibold
                     hover:from-amber-500 hover:to-orange-600 active:scale-95 transition-all duration-150 shadow-sm"
            >
              返回登录页
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
/**
 * 根组件：挂载时从 localStorage 恢复登录态。
 * 通过 SSE (Server-Sent Events) 实现毫秒级 SSO 踢出检测和全页面数据实时刷新。
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { sessionBus } from '@/utils/sessionBus'
import { startEventStream, stopEventStream } from '@/composables/useEventStream'
import AppDialogHost from '@/components/AppDialogHost.vue'

const showSSODialog = ref(false)
const ssoDeviceInfo = ref({ device: '', location: '', ip: '' })
const router = useRouter()

/**
 * 接收 SSO 踢出信号，关闭 SSE 并显示安全提醒弹窗。
 * @param {object} [data] - SSE 推送的设备信息（device, location, ip）
 */
function onSessionReplaced(data) {
  stopEventStream()
  ssoDeviceInfo.value = {
    device: data?.device || '',
    location: data?.location || '',
    ip: data?.ip || '',
  }
  showSSODialog.value = true
}

/** 用户点击「返回登录页」：清除登录态并跳转 */
function handleSSOConfirm() {
  showSSODialog.value = false
  ssoDeviceInfo.value = { device: '', location: '', ip: '' }
  useAuthStore().logout()
  router.replace({ name: 'Login' })
}

/**
 * 页面可见性变化：隐藏时断开 SSE 节省资源，恢复可见时重新连接并校验会话。
 * SSE 断开期间可能错过 session_replaced 事件，因此恢复时做一次快速校验。
 */
function onVisibilityChange() {
  if (document.hidden) {
    stopEventStream()
  } else if (localStorage.getItem('access') && !showSSODialog.value) {
    startEventStream()
    _checkSessionOnResume()
  }
}

/**
 * 页面恢复可见时快速校验会话有效性（防止 SSE 断开期间错过踢出事件）。
 */
async function _checkSessionOnResume() {
  try {
    const resp = await fetch('/api/v1/users/me/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access')}`,
        'X-Session-Key': localStorage.getItem('sessionKey') || '',
      },
    })
    if (resp.status === 401) {
      const data = await resp.json().catch(() => ({}))
      if (data.code === 'SESSION_REPLACED') {
        onSessionReplaced({})
      }
    }
  } catch { /* 网络异常忽略 */ }
}

/** 登录成功后启动 SSE 连接 */
function onLoginSuccess() {
  startEventStream()
}

onMounted(() => {
  useAuthStore().restoreFromStorage()
  sessionBus.on('session-replaced', onSessionReplaced)
  sessionBus.on('login-success', onLoginSuccess)
  document.addEventListener('visibilitychange', onVisibilityChange)
  if (localStorage.getItem('access')) {
    startEventStream()
  }
})

onUnmounted(() => {
  sessionBus.off('session-replaced', onSessionReplaced)
  sessionBus.off('login-success', onLoginSuccess)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  stopEventStream()
})
</script>

<style>
/* SSO 安全提醒弹窗淡入淡出动画 */
.sso-fade-enter-active,
.sso-fade-leave-active {
  transition: opacity 0.2s ease;
}
.sso-fade-enter-active .bg-white,
.sso-fade-leave-active .bg-white {
  transition: transform 0.25s ease, opacity 0.2s ease;
}
.sso-fade-enter-from,
.sso-fade-leave-to {
  opacity: 0;
}
.sso-fade-enter-from .bg-white {
  transform: scale(0.94);
}
</style>
