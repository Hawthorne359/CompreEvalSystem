<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-4">
    <div class="mb-3 flex items-center justify-between">
      <h5 class="text-sm font-semibold text-slate-800">Word/PDF 占位符映射</h5>
      <button type="button" class="rounded border border-brand-500 px-2 py-1 text-xs text-brand-700 hover:bg-brand-50" @click="$emit('add-row')">
        + 新增占位符
      </button>
    </div>
    <p class="mb-3 text-xs text-slate-500">模板中直接写 <code class="rounded bg-slate-100 px-1">@占位符</code>，这里配置它映射到哪个字段（统计字段同样可用）。</p>
    <details class="mb-3 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      <summary class="cursor-pointer font-medium text-slate-700">占位符示例</summary>
      <p class="mt-1">模板中写：<code class="rounded bg-slate-100 px-1">@统计_平均分</code>，映射到字段“统计_平均分”。</p>
      <p class="mt-1">模板中写：<code class="rounded bg-slate-100 px-1">@reviewer_signatures_all</code>，映射到“测评小组成员签名（全部）”。</p>
    </details>

    <div class="space-y-2">
      <div class="grid grid-cols-12 items-center gap-2 px-1 text-xs font-medium text-slate-500">
        <span class="col-span-5">模板占位符（@token）</span>
        <span class="col-span-6">字段（导出值来源）</span>
        <span class="col-span-1 text-center">操作</span>
      </div>
      <div v-for="(row, idx) in config.word_placeholders" :key="`word-${idx}`" class="rounded border bg-slate-50/60 p-2">
        <div class="grid grid-cols-12 items-center gap-2">
          <div class="col-span-1 text-center text-xs text-slate-400">@</div>
          <input
            :value="row.placeholder"
            type="text"
            class="col-span-4 rounded border bg-white px-2 py-1.5 text-sm font-mono"
            placeholder="占位符名称"
            @input="$emit('update-row', { idx, key: 'placeholder', value: $event.target.value })"
          />
          <select
            :value="row.field_key"
            class="col-span-6 rounded border bg-white px-2 py-1.5 text-sm"
            @change="$emit('update-row', { idx, key: 'field_key', value: $event.target.value })"
          >
            <option value="">请选择对应字段</option>
            <optgroup v-for="group in groupedDisplayFields" :key="`word-${group.id}`" :label="group.label">
              <option v-for="field in group.fields" :key="field.key" :value="field.key">{{ field.label }} ({{ field.key }})</option>
            </optgroup>
          </select>
          <button type="button" class="col-span-1 text-center text-xs text-red-500 hover:text-red-700" @click="$emit('remove-row', idx)">删除</button>
        </div>
        <div class="mt-1 flex items-center justify-between px-1 text-xs text-slate-400">
          <span>模板写法：<code class="rounded bg-slate-200 px-1 font-mono">{{ formatTokenPreview(row.placeholder) }}</code></span>
          <span class="truncate px-2">{{ getFieldDisplayName(row.field_key) }}</span>
          <button type="button" class="text-brand-600 hover:text-brand-800" @click="$emit('copy', row.placeholder)">复制</button>
        </div>
      </div>
      <p v-if="!config.word_placeholders?.length" class="py-6 text-center text-sm text-slate-400">暂无占位符配置</p>
    </div>

    <div class="mt-4 rounded border border-dashed border-slate-300 bg-slate-50 p-3">
      <label class="mb-1 block text-xs font-medium text-slate-600">ZIP 内文件名模板（多文件导出生效）</label>
      <input
        :value="config.zip_filename_pattern"
        type="text"
        class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm font-mono"
        placeholder="{student_no}_{real_name}"
        @input="$emit('update:zipPattern', $event.target.value)"
      />
      <p class="mt-1 text-xs text-slate-400">可用：{student_no} {real_name} {class_name} {department} {rank} {username}</p>
    </div>
  </section>
</template>

<script setup>
defineProps({
  config: { type: Object, required: true },
  groupedDisplayFields: { type: Array, default: () => [] },
  formatTokenPreview: { type: Function, required: true },
  getFieldDisplayName: { type: Function, required: true },
})

defineEmits(['add-row', 'remove-row', 'update-row', 'copy', 'update:zipPattern'])
</script>
