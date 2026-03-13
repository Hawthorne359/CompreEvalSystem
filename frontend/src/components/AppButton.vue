<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="btnClass"
  >
    <span v-if="loading">处理中…</span>
    <span v-else><slot /></span>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'button' },
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  block: { type: Boolean, default: false },
})

/**
 * @description 统一按钮视觉样式，按 variant/size 输出 class。
 * @returns {string}
 */
const btnClass = computed(() => {
  const byVariant = {
    primary: 'bg-brand-500 text-white hover:bg-brand-600',
    secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
    success: 'bg-emerald-600 text-white hover:bg-emerald-700',
    danger: 'bg-red-600 text-white hover:bg-red-700',
    ghost: 'bg-slate-100 text-slate-700 hover:bg-slate-200',
  }
  const bySize = {
    sm: 'px-2.5 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-sm',
  }
  const width = props.block ? 'w-full' : ''
  return [
    'rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50',
    byVariant[props.variant] || byVariant.primary,
    bySize[props.size] || bySize.md,
    width,
  ].join(' ')
})
</script>
