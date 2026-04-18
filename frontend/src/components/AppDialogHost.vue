<template>
  <teleport to="body">
    <div
      v-if="dialogState.visible"
      class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/45 p-4"
      @mousedown.self="onCancel"
    >
      <div class="app-modal w-full max-w-xl">
        <div class="border-b border-slate-200/60 px-6 py-4">
          <h3 class="text-xl font-semibold text-slate-800 md:text-2xl">{{ dialogState.title }}</h3>
        </div>
        <div class="space-y-4 px-6 py-5">
          <p v-if="dialogState.message" class="text-sm leading-6 text-slate-600 md:text-base">{{ dialogState.message }}</p>

          <div v-if="dialogState.mode === 'prompt'" class="space-y-1">
            <label v-if="dialogState.inputLabel" class="block text-sm font-medium text-slate-700">
              {{ dialogState.inputLabel }}
            </label>
            <input
              v-model="localInput"
              :type="dialogState.inputType"
              class="w-full rounded border border-slate-300 px-3 py-2 text-base text-slate-800 focus:border-brand-500 focus:outline-none"
              :placeholder="dialogState.inputPlaceholder"
              @keyup.enter="onConfirm"
            />
            <p v-if="dialogState.error" class="text-sm text-red-600">{{ dialogState.error }}</p>
          </div>
        </div>
        <div class="flex justify-end gap-3 border-t border-slate-200/60 px-6 py-4">
          <button
            v-if="dialogState.mode !== 'alert'"
            type="button"
            class="rounded-xl border border-slate-200 bg-slate-50 px-6 py-2 text-base font-medium text-slate-700 hover:bg-slate-100"
            @click="onCancel"
          >
            {{ dialogState.cancelText }}
          </button>
          <button
            type="button"
            class="rounded-xl px-6 py-2 text-base font-semibold text-white"
            :class="dialogState.danger ? 'bg-red-600 hover:bg-red-700' : 'bg-brand-600 hover:bg-brand-700'"
            @click="onConfirm"
          >
            {{ dialogState.confirmText }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { dialogState, closeDialog } from '@/utils/dialog'

const localInput = ref('')

watch(
  () => dialogState.visible,
  (visible) => {
    if (!visible) {
      localInput.value = ''
      return
    }
    localInput.value = String(dialogState.inputValue ?? '')
  },
)

function onCancel() {
  if (dialogState.mode === 'alert') {
    closeDialog({ confirmed: true })
    return
  }
  closeDialog({ confirmed: false, value: localInput.value })
}

function onConfirm() {
  dialogState.error = ''
  if (dialogState.mode === 'prompt') {
    const value = String(localInput.value ?? '')
    if (dialogState.inputRequired && !value.trim()) {
      dialogState.error = '该字段不能为空'
      return
    }
    if (dialogState.inputValidator) {
      const err = dialogState.inputValidator(value)
      if (err) {
        dialogState.error = String(err)
        return
      }
    }
    closeDialog({ confirmed: true, value })
    return
  }
  closeDialog({ confirmed: true })
}
</script>

