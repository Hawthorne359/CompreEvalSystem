<template>
  <span :class="badgeClass"><slot>{{ text }}</slot></span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  tone: { type: String, default: 'neutral' },
})

/**
 * @description 状态徽章统一样式，支持中性色/成功/警告/错误/信息。
 * @returns {string}
 */
const badgeClass = computed(() => {
  const tones = {
    neutral: 'bg-slate-100 text-slate-700',
    success: 'bg-emerald-100 text-emerald-700',
    warning: 'bg-amber-100 text-amber-700',
    danger: 'bg-red-100 text-red-700',
    info: 'bg-blue-100 text-blue-700',
    purple: 'bg-purple-100 text-purple-700',
  }
  return `inline-flex rounded px-2 py-0.5 text-xs font-medium ${tones[props.tone] || tones.neutral}`
})
</script>
