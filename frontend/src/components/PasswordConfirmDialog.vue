<template>
  <!-- 遮罩层 -->
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @mousedown.self="cancel"
    >
      <div class="app-modal w-full max-w-md">
        <!-- 标题栏 -->
        <div class="flex items-center justify-between border-b border-slate-200/50 px-6 py-4">
          <h3 class="text-base font-semibold text-slate-800">
            <span class="mr-2 text-red-600">⚠</span>{{ title }}
          </h3>
          <button
            class="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            @click="cancel"
          >
            ✕
          </button>
        </div>

        <!-- 正文 -->
        <div class="px-6 py-5 space-y-4">
          <!-- 提示信息 -->
          <p class="text-sm text-slate-600">{{ message }}</p>

          <!-- 删除理由 -->
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">
              操作理由 <span class="text-red-500">*</span>
            </label>
            <textarea
              v-model="form.reason"
              rows="2"
              class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="请填写操作理由，将记入审计日志…"
            />
            <p v-if="errors.reason" class="mt-1 text-xs text-red-600">{{ errors.reason }}</p>
          </div>

          <!-- 密码确认 -->
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700">
              {{ passwordLabel }} <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="请输入登录密码"
              @keyup.enter="confirm"
            />
            <p v-if="errors.password" class="mt-1 text-xs text-red-600">{{ errors.password }}</p>
          </div>

          <!-- 全局错误 -->
          <p v-if="errors.global" class="text-sm text-red-600">{{ errors.global }}</p>
        </div>

        <!-- 按钮区 -->
        <div class="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
          <button
            class="rounded border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
            :disabled="loading"
            @click="cancel"
          >
            取消
          </button>
          <button
            class="rounded bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-50"
            :disabled="loading"
            @click="confirm"
          >
            {{ loading ? '验证中…' : confirmText }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
/**
 * PasswordConfirmDialog — 高危操作密码确认弹窗
 *
 * 用法示例::
 *
 *   <PasswordConfirmDialog
 *     v-model:visible="showDialog"
 *     title="删除测评周期"
 *     message="此操作将永久删除该测评周期及其所有项目，无法撤销。"
 *     @confirmed="doDelete"
 *   />
 *
 *   // 父组件监听 confirmed 事件，回调参数：{ confirmToken, reason }
 *   async function doDelete({ confirmToken, reason }) {
 *     await api.deleteSeason(seasonId, { confirm_token: confirmToken, reason })
 *   }
 */
import { ref, watch } from 'vue'
import { verifyPassword } from '@/api/admin'

const props = defineProps({
  /** 是否显示弹窗（v-model:visible） */
  visible: {
    type: Boolean,
    default: false,
  },
  /** 弹窗标题 */
  title: {
    type: String,
    default: '危险操作确认',
  },
  /** 说明文字 */
  message: {
    type: String,
    default: '此操作不可撤销，请输入密码确认。',
  },
  /** 确认按钮文字 */
  confirmText: {
    type: String,
    default: '确认执行',
  },
  /** 密码输入框标签 */
  passwordLabel: {
    type: String,
    default: '登录密码',
  },
})

const emit = defineEmits(['update:visible', 'confirmed', 'cancelled'])

const form = ref({ password: '', reason: '' })
const errors = ref({ password: '', reason: '', global: '' })
const loading = ref(false)

/** 重置表单 */
function reset() {
  form.value = { password: '', reason: '' }
  errors.value = { password: '', reason: '', global: '' }
  loading.value = false
}

watch(() => props.visible, (val) => {
  if (val) reset()
})

function cancel() {
  emit('update:visible', false)
  emit('cancelled')
}

async function confirm() {
  errors.value = { password: '', reason: '', global: '' }

  if (!form.value.reason.trim()) {
    errors.value.reason = '操作理由不能为空'
    return
  }
  if (!form.value.password) {
    errors.value.password = '请输入密码'
    return
  }

  loading.value = true
  try {
    const { data } = await verifyPassword(form.value.password)
    emit('update:visible', false)
    emit('confirmed', {
      confirmToken: data.confirm_token,
      reason: form.value.reason.trim(),
    })
  } catch (err) {
    const msg = err?.response?.data?.detail || '密码验证失败，请重试'
    errors.value.global = msg
  } finally {
    loading.value = false
  }
}
</script>
