<template>
  <aside class="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm backdrop-blur">
    <h4 class="text-sm font-semibold text-slate-800">配置摘要</h4>
    <dl class="mt-3 space-y-2 text-sm">
      <div class="flex justify-between gap-2">
        <dt class="text-slate-500">任务类型</dt>
        <dd class="font-medium text-slate-800">{{ taskLabel }}</dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-slate-500">当前映射</dt>
        <dd class="truncate text-right text-slate-700">{{ mappingName || '未命名草稿' }}</dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-slate-500">绑定模板</dt>
        <dd class="truncate text-right text-slate-700">{{ templateName || '未绑定' }}</dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-slate-500">Excel 列数</dt>
        <dd class="text-slate-700">{{ excelColumnCount }}</dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-slate-500">Word 占位符</dt>
        <dd class="text-slate-700">{{ wordPlaceholderCount }}</dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-slate-500">统计字段</dt>
        <dd class="text-slate-700">{{ computedFieldCount }}</dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-slate-500">Word可用统计字段</dt>
        <dd class="text-slate-700">{{ wordUsableComputedCount }}</dd>
      </div>
    </dl>

    <div class="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
      <label class="mb-1 block text-xs font-medium text-slate-600">输出粒度</label>
      <select
        :value="groupFileMode"
        class="w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-xs"
        @change="$emit('update:groupFileMode', $event.target.value)"
      >
        <option value="single_file">整体单文件</option>
        <option value="per_group_file">按分组各一份（ZIP）</option>
        <option v-if="taskType !== 'xlsx'" value="per_student_file">每人单独文件（ZIP）</option>
      </select>
      <label class="mb-1 mt-2 block text-xs font-medium text-slate-600">分组维度</label>
      <select
        :value="groupBy"
        class="w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-xs"
        @change="$emit('update:groupBy', $event.target.value)"
      >
        <option value="">不分组（全部）</option>
        <option v-if="allowedGroupByOptions.includes('class')" value="class">按班级</option>
        <option v-if="allowedGroupByOptions.includes('major')" value="major">按专业</option>
        <option v-if="allowedGroupByOptions.includes('department')" value="department">按院系</option>
      </select>
    </div>

    <div class="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
      <label class="mb-1 block text-xs font-medium text-slate-600">测评小组成员签名口径</label>
      <select
        :value="reviewerSignatureSource"
        class="w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-xs"
        @change="$emit('update:reviewerSignatureSource', $event.target.value)"
      >
        <option value="actual_scored">按实际评分成员</option>
        <option value="assigned">按任务分配成员</option>
      </select>
      <label
        class="mt-2 flex items-center gap-2 text-xs"
        :class="isActualScoredSource ? 'cursor-pointer text-slate-700' : 'cursor-not-allowed text-slate-400'"
      >
        <input
          :checked="!!includeArbitrationInSignature"
          type="checkbox"
          :disabled="!isActualScoredSource"
          class="cursor-pointer disabled:cursor-not-allowed"
          @change="$emit('update:includeArbitrationInSignature', $event.target.checked)"
        />
        包含仲裁人员（仅“实际评分成员”生效）
      </label>
    </div>

    <div class="mt-4 space-y-2">
      <button
        type="button"
        class="w-full rounded-lg border border-brand-500 px-3 py-2 text-sm text-brand-700 hover:bg-brand-50 disabled:opacity-50"
        :disabled="saving"
        @click="$emit('save')"
      >
        {{ saving ? '保存中…' : '保存映射' }}
      </button>
      <button
        type="button"
        class="w-full rounded-lg border border-green-600 px-3 py-2 text-sm text-green-700 hover:bg-green-50 disabled:opacity-50"
        :disabled="exporting"
        @click="$emit('export')"
      >
        {{ exporting ? '导出中…' : '使用已保存映射导出' }}
      </button>
      <p class="text-xs text-slate-500">导出不会自动新建映射；请先保存后再导出。</p>
      <p v-if="notice" class="rounded border border-brand-200 bg-brand-50 px-2 py-1.5 text-xs text-brand-700">{{ notice }}</p>
      <p v-if="error" class="rounded border border-red-200 bg-red-50 px-2 py-1.5 text-xs text-red-700">{{ error }}</p>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  taskType: { type: String, required: true },
  wordPdfFormat: { type: String, default: 'word' },
  mappingName: { type: String, default: '' },
  templateName: { type: String, default: '' },
  excelColumnCount: { type: Number, default: 0 },
  wordPlaceholderCount: { type: Number, default: 0 },
  computedFieldCount: { type: Number, default: 0 },
  wordUsableComputedCount: { type: Number, default: 0 },
  multiFile: { type: Boolean, default: false },
  groupBy: { type: String, default: '' },
  groupFileMode: { type: String, default: 'single_file' },
  allowedGroupByOptions: { type: Array, default: () => ['class', 'major', 'department'] },
  reviewerSignatureSource: { type: String, default: 'actual_scored' },
  includeArbitrationInSignature: { type: Boolean, default: false },
  saving: { type: Boolean, default: false },
  exporting: { type: Boolean, default: false },
  notice: { type: String, default: '' },
  error: { type: String, default: '' },
})

defineEmits([
  'save',
  'export',
  'update:multiFile',
  'update:groupBy',
  'update:groupFileMode',
  'update:reviewerSignatureSource',
  'update:includeArbitrationInSignature',
])

const taskLabel = computed(() => {
  if (props.taskType === 'xlsx') return 'Excel 批量导出'
  return props.wordPdfFormat === 'pdf' ? 'PDF 单人表导出' : 'Word 单人表导出'
})

const isActualScoredSource = computed(() => props.reviewerSignatureSource === 'actual_scored')
</script>
