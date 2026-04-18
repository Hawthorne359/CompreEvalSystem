<template>
  <aside class="rounded-2xl border border-white/70 bg-white/70 p-3 shadow-sm backdrop-blur">
    <h4 class="px-2 text-xs font-semibold uppercase tracking-wide text-slate-500">导出任务</h4>
    <div class="mt-2 space-y-1">
      <button
        v-for="item in taskItems"
        :key="item.id"
        type="button"
        class="w-full rounded-xl px-3 py-2 text-left text-sm transition"
        :class="activeTaskType === item.id ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
        @click="$emit('update:activeTaskType', item.id)"
      >
        <div class="font-medium">{{ item.label }}</div>
        <div class="mt-0.5 text-xs" :class="activeTaskType === item.id ? 'text-white/75' : 'text-slate-500'">{{ item.tip }}</div>
      </button>
    </div>

    <div v-if="activeTaskType === 'word_pdf'" class="mt-4 rounded-xl border border-slate-200 bg-white/90 p-3">
      <h5 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Word/PDF 输出</h5>
      <div class="mt-2 space-y-1.5 text-sm">
        <label class="flex cursor-pointer items-center gap-2">
          <input
            :checked="wordPdfFormat === 'word'"
            type="radio"
            name="word-pdf-format"
            class="cursor-pointer"
            @change="$emit('update:wordPdfFormat', 'word')"
          />
          Word（.docx）
        </label>
        <label class="flex cursor-pointer items-center gap-2">
          <input
            :checked="wordPdfFormat === 'pdf'"
            type="radio"
            name="word-pdf-format"
            class="cursor-pointer"
            @change="$emit('update:wordPdfFormat', 'pdf')"
          />
          PDF（由 Word 模板转换）
        </label>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  activeTaskType: { type: String, required: true },
  wordPdfFormat: { type: String, required: true },
})

defineEmits(['update:activeTaskType', 'update:wordPdfFormat'])

const taskItems = [
  { id: 'xlsx', label: 'Excel 批量导出', tip: '一行一条学生记录，适合班级/年级汇总' },
  { id: 'word_pdf', label: 'Word/PDF 单人表', tip: '按占位符模板生成每人成绩单' },
]
</script>
