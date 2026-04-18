<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-4">
    <div class="mb-3 flex items-center justify-between">
      <h5 class="text-sm font-semibold text-slate-800">Excel 列映射</h5>
      <button type="button" class="rounded border border-brand-500 px-2 py-1 text-xs text-brand-700 hover:bg-brand-50" @click="$emit('add-column')">
        + 新增列
      </button>
    </div>

    <div class="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
      <div class="flex flex-wrap items-center gap-x-6 gap-y-2">
        <label class="flex items-center gap-2">
          <span class="shrink-0 text-xs font-medium text-slate-600">数据写入起始行：</span>
          <input
            :value="config.data_start_row"
            type="number"
            :min="config.write_header ? Number(config.header_row || 1) + 1 : 1"
            class="w-16 rounded border border-slate-300 bg-white px-2 py-1 text-center text-sm font-mono"
            @input="$emit('update:dataStartRow', Number($event.target.value || 1))"
          />
        </label>
        <label class="flex cursor-pointer items-center gap-2">
          <input
            :checked="!!config.write_header"
            type="checkbox"
            class="cursor-pointer"
            @change="$emit('update:writeHeader', $event.target.checked)"
          />
          <span class="text-xs text-slate-700">写入表头行</span>
        </label>
      </div>
    </div>

    <div class="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-medium text-slate-700">静态单元格（只写一次）</span>
        <button type="button" class="rounded border border-brand-500 px-2 py-1 text-xs text-brand-700 hover:bg-brand-50" @click="$emit('add-static')">+ 新增</button>
      </div>
      <details class="mb-2 rounded border border-slate-200 bg-white/70 px-3 py-2 text-xs text-slate-600">
        <summary class="cursor-pointer font-medium text-slate-700">使用说明与示例</summary>
        <p class="mt-1">用于写入只出现一次的信息，比如表头区域中的院系、年级、人数等。</p>
        <p class="mt-1">建议只用两种模式：1) 单值字段写入；2) 模板拼接写入（一个单元格可混合多个字段）。</p>
        <p class="mt-1">示例：A1 模板写 <code class="rounded bg-slate-100 px-1">{major} {class_grade} 参评{scope_valid_submission_count}人</code></p>
      </details>
      <div class="space-y-2">
        <div
          v-for="(row, idx) in config.static_cells"
          :key="`sc-${idx}`"
          class="grid grid-cols-12 items-center gap-2"
        >
          <input
            :value="row.cell"
            type="text"
            class="col-span-2 rounded border border-slate-300 bg-white px-2 py-1.5 text-center text-sm font-mono"
            placeholder="C3"
            @input="$emit('update-static', { idx, key: 'cell', value: $event.target.value })"
          />
          <select
            :value="row.field_key"
            :disabled="row.aggregation === 'count' || row.aggregation === 'template'"
            class="col-span-7 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm disabled:opacity-50"
            @change="$emit('update-static', { idx, key: 'field_key', value: $event.target.value })"
          >
            <option value="">请选择字段</option>
            <optgroup v-for="group in groupedDisplayFields" :key="`sc-${group.id}`" :label="group.label">
              <option v-for="field in group.fields" :key="field.key" :value="field.key">{{ field.label }} ({{ field.key }})</option>
            </optgroup>
          </select>
          <select
            :value="row.aggregation || 'first'"
            class="col-span-2 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
            @change="$emit('update-static', { idx, key: 'aggregation', value: $event.target.value })"
          >
            <option value="first">单值字段写入</option>
            <option value="template">模板拼接写入</option>
          </select>
          <button type="button" class="col-span-1 text-center text-xs text-red-500 hover:text-red-700" @click="$emit('remove-static', idx)">删除</button>
          <input
            v-if="row.aggregation === 'template'"
            :value="row.template || ''"
            type="text"
            class="col-span-12 rounded border border-slate-300 bg-white px-2 py-1.5 text-xs font-mono"
            placeholder="{major} {class_grade} 参评{scope_valid_submission_count}人"
            @input="$emit('update-static', { idx, key: 'template', value: $event.target.value })"
          />
        </div>
        <p v-if="!config.static_cells?.length" class="py-3 text-center text-xs text-slate-400">暂无静态单元格</p>
      </div>
    </div>

    <div class="mb-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-medium text-slate-700">统计字段（computed_fields）</span>
        <button type="button" class="rounded border border-brand-500 px-2 py-1 text-xs text-brand-700 hover:bg-brand-50" @click="$emit('add-computed')">+ 新增</button>
      </div>
      <details class="mb-2 rounded border border-slate-200 bg-white/70 px-3 py-2 text-xs text-slate-600">
        <summary class="cursor-pointer font-medium text-slate-700">使用说明与示例</summary>
        <p class="mt-1">步骤：1) 先新建统计字段；2) 再在静态单元格、Excel 列或 Word 占位符中当普通字段使用。</p>
        <p class="mt-1">示例1：stat_valid_count = count + 统计对象“有效行”。</p>
        <p class="mt-1">示例2：stat_avg_score = avg + 选择字段“总分(final_score)”。</p>
        <p class="mt-1">示例3：stat_reviewers = join_distinct + 统计对象“评审成员(reviewers)”。</p>
      </details>
      <div class="space-y-2">
        <div v-for="(row, idx) in config.computed_fields" :key="`cf-${idx}`" class="grid grid-cols-12 items-center gap-2">
          <input
            :value="row.key"
            type="text"
            class="col-span-2 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm font-mono"
            placeholder="key"
            @input="$emit('update-computed', { idx, key: 'key', value: $event.target.value })"
          />
          <select
            :value="row.fn || 'count'"
            class="col-span-2 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
            @change="$emit('update-computed', { idx, key: 'fn', value: $event.target.value })"
          >
            <option value="count">计数 (count)</option>
            <option value="sum">求和 (sum)</option>
            <option value="avg">平均值 (avg)</option>
            <option value="min">最小值 (min)</option>
            <option value="max">最大值 (max)</option>
            <option value="join_distinct">去重拼接 (join_distinct)</option>
          </select>
          <select
            :value="row.target || 'valid_rows'"
            class="col-span-2 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
            @change="$emit('update-computed', { idx, key: 'target', value: $event.target.value })"
          >
            <option value="valid_rows">有效行 (valid_rows)</option>
            <option value="missing_submissions">未参评人数 (missing_submissions)</option>
            <option value="reviewers">评审成员 (reviewers)</option>
          </select>
          <select
            :value="row.field_key || ''"
            class="col-span-4 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
            @change="$emit('update-computed', { idx, key: 'field_key', value: $event.target.value })"
          >
            <option value="">字段（sum/avg/min/max 必填）</option>
            <optgroup v-for="group in groupedDisplayFields" :key="`cf-${group.id}`" :label="group.label">
              <option v-for="field in group.fields" :key="field.key" :value="field.key">{{ field.label }} ({{ field.key }})</option>
            </optgroup>
          </select>
          <button type="button" class="col-span-1 text-center text-xs text-red-500 hover:text-red-700" @click="$emit('remove-computed', idx)">删除</button>
          <input
            :value="row.precision ?? ''"
            type="number"
            class="col-span-1 rounded border border-slate-300 bg-white px-1 py-1 text-center text-xs"
            placeholder="精度"
            @input="$emit('update-computed', { idx, key: 'precision', value: $event.target.value })"
          />
        </div>
        <p v-if="!config.computed_fields?.length" class="py-3 text-center text-xs text-slate-400">暂无统计字段</p>
      </div>
      <p class="mt-2 text-xs text-slate-400">命名建议：仅用英文字母/数字/下划线，如 stat_avg_score、stat_valid_count。</p>
    </div>

    <div class="space-y-2">
      <div class="grid grid-cols-12 items-center gap-2 px-1 text-xs font-medium text-slate-500">
        <span class="col-span-1 text-center">列标</span>
        <span class="col-span-8">字段（导出值来源）</span>
        <span class="col-span-2">表头（显示文本）</span>
        <span class="col-span-1 text-center">操作</span>
      </div>
      <div v-for="(row, idx) in config.excel_columns" :key="`col-${idx}`" class="grid grid-cols-12 items-center gap-2">
        <input
          :value="row.column"
          type="text"
          class="col-span-1 rounded border px-2 py-1.5 text-center text-sm font-mono"
          placeholder="A"
          @input="$emit('update-column', { idx, key: 'column', value: $event.target.value })"
        />
        <select
          :value="row.field_key"
          class="col-span-8 rounded border px-2 py-1.5 text-sm"
          @change="$emit('update-column', { idx, key: 'field_key', value: $event.target.value })"
        >
          <option value="">请选择字段</option>
          <optgroup v-for="group in groupedDisplayFields" :key="`excel-${group.id}`" :label="group.label">
            <option v-for="field in group.fields" :key="field.key" :value="field.key">{{ field.label }} ({{ field.key }})</option>
          </optgroup>
        </select>
        <input
          :value="row.header"
          type="text"
          class="col-span-2 rounded border px-2 py-1.5 text-sm"
          placeholder="表头"
          @input="$emit('update-column', { idx, key: 'header', value: $event.target.value })"
        />
        <button type="button" class="col-span-1 text-center text-xs text-red-500 hover:text-red-700" @click="$emit('remove-column', idx)">删除</button>
      </div>
      <p v-if="!config.excel_columns?.length" class="py-6 text-center text-sm text-slate-400">暂无列配置</p>
      <p class="text-xs text-slate-400">说明：列标是 Excel 列号（A/B/C...），字段是数据键，表头是写入标题行的显示名。</p>
    </div>
  </section>
</template>

<script setup>
defineProps({
  config: { type: Object, required: true },
  groupedDisplayFields: { type: Array, default: () => [] },
})

defineEmits([
  'add-column',
  'remove-column',
  'update-column',
  'add-static',
  'remove-static',
  'update-static',
  'add-computed',
  'remove-computed',
  'update-computed',
  'update:dataStartRow',
  'update:writeHeader',
])
</script>
