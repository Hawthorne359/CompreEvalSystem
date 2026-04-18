<template>
  <section class="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm backdrop-blur">
    <div class="flex items-center justify-between gap-2">
      <h4 class="text-sm font-semibold text-slate-800">模板文件</h4>
      <span class="text-xs text-slate-500">{{ taskTemplateType === 'excel' ? '当前任务需要 Excel 模板' : '当前任务需要 Word 模板' }}</span>
    </div>

    <div class="mt-3 grid gap-2 sm:grid-cols-4">
      <input
        :value="templateForm.name"
        type="text"
        class="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm"
        placeholder="模板名称"
        @input="$emit('update:name', $event.target.value)"
      />
      <select
        :value="templateForm.template_type"
        class="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm"
        @change="$emit('update:type', $event.target.value)"
      >
        <option value="word">Word 模板</option>
        <option value="excel">Excel 模板</option>
      </select>
      <select
        :value="templateForm.visibility"
        class="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm"
        @change="$emit('update:visibility', $event.target.value)"
      >
        <option value="private">仅自己可见</option>
        <option v-if="isDirectorOrAdmin" value="department">院系可见</option>
        <option v-if="isDirectorOrAdmin" value="global">全局可见</option>
      </select>
      <input :key="fileInputKey" type="file" class="text-sm" @change="$emit('pick-file', $event)" />
    </div>

    <div class="mt-3 flex items-center gap-2">
      <button
        type="button"
        class="rounded-lg border border-brand-500 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50"
        :disabled="uploadingTemplate"
        @click="$emit('upload')"
      >
        {{ uploadingTemplate ? '上传中…' : '上传模板' }}
      </button>
      <span class="text-xs text-slate-500">上传后点击列表中的模板可绑定到当前映射</span>
    </div>

    <div class="mt-3 max-h-36 overflow-auto rounded-lg border border-slate-200 bg-white">
      <div
        v-for="item in filteredTemplates"
        :key="item.id"
        role="button"
        tabindex="0"
        class="flex w-full items-center justify-between border-b border-slate-100 px-3 py-2 text-left text-sm hover:bg-slate-50"
        :class="selectedTemplateId === item.id ? 'bg-brand-50 text-brand-700' : 'text-slate-700'"
        @click="$emit('select-template', item.id)"
        @keydown.enter="$emit('select-template', item.id)"
      >
        <span class="truncate">{{ item.name }}</span>
        <div class="ml-2 flex shrink-0 items-center gap-2">
          <span class="text-xs text-slate-500">{{ item.template_type }}</span>
          <button type="button" class="text-xs text-slate-500 hover:text-slate-700" @click.stop="$emit('rename-template', item)">重命名</button>
          <button type="button" class="text-xs text-red-500 hover:text-red-700" @click.stop="$emit('delete-template', item)">删除</button>
        </div>
      </div>
      <p v-if="filteredTemplates.length === 0" class="px-3 py-3 text-sm text-slate-400">暂无可用模板，请先上传</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  templates: { type: Array, default: () => [] },
  selectedTemplateId: { type: [Number, null], default: null },
  templateForm: { type: Object, required: true },
  taskTemplateType: { type: String, required: true },
  uploadingTemplate: { type: Boolean, default: false },
  fileInputKey: { type: Number, default: 0 },
  isDirectorOrAdmin: { type: Boolean, default: false },
})

defineEmits([
  'update:name',
  'update:type',
  'update:visibility',
  'pick-file',
  'upload',
  'select-template',
  'rename-template',
  'delete-template',
])

const filteredTemplates = computed(() =>
  (props.templates || []).filter((item) => item.template_type === props.taskTemplateType)
)
</script>
