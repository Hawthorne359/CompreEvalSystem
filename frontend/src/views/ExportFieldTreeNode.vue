<template>
  <div>
    <!-- Node header row -->
    <div
      class="flex cursor-pointer items-center justify-between"
      :class="[
        depth === 0
          ? 'bg-brand-600 px-4 py-2.5 text-white'
          : depth === 1
            ? 'border-b border-slate-200 bg-slate-100 px-4 py-2 hover:bg-slate-200'
            : 'border-b border-slate-100 bg-white px-4 py-1.5 hover:bg-slate-50',
      ]"
      :style="depth > 0 ? `padding-left: ${depth * 1.25 + 1}rem` : ''"
      @click="expanded = !expanded"
    >
      <div class="flex min-w-0 items-center gap-2">
        <!-- expand arrow -->
        <span
          class="shrink-0 text-xs transition-transform duration-150"
          :class="[expanded ? 'rotate-90' : '', depth === 0 ? 'text-white/70' : 'text-slate-400']"
        >▶</span>

        <!-- select-all checkbox for this node -->
        <input
          type="checkbox"
          class="h-3.5 w-3.5 shrink-0 cursor-pointer rounded"
          :checked="allFieldKeys.length > 0 && allFieldKeys.every((k) => selectedKeys.has(k))"
          :indeterminate.prop="
            allFieldKeys.some((k) => selectedKeys.has(k)) &&
            !allFieldKeys.every((k) => selectedKeys.has(k))
          "
          @click.stop
          @change="onToggleSelectAll"
        />

        <!-- label -->
        <span
          class="min-w-0 truncate"
          :class="depth === 0 ? 'text-sm font-semibold text-white' : depth === 1 ? 'text-sm font-medium text-slate-700' : 'text-sm text-slate-600'"
        >
          <span v-if="node.category" class="mr-0.5 font-mono">{{ node.category }}</span>
          <span v-if="node.category"> — </span>
          {{ node.name }}
        </span>

        <!-- field count badge -->
        <span
          v-if="node.total_field_count > 0"
          class="shrink-0 text-xs"
          :class="depth === 0 ? 'text-white/60' : 'text-slate-400'"
        >{{ node.total_field_count }} 个字段</span>
      </div>

      <!-- action button -->
      <button
        type="button"
        class="ml-2 shrink-0 rounded px-2 py-0.5 text-xs"
        :class="depth === 0 ? 'text-white/80 hover:bg-white/10 hover:text-white' : 'text-brand-600 hover:bg-brand-50 hover:text-brand-800'"
        @click.stop="onAddCommon"
      >{{ depth === 0 ? '全选本模块' : '直接加入常用' }}</button>
    </div>

    <!-- Expanded content -->
    <div v-if="expanded">
      <!-- Child nodes (recursive) -->
      <ExportFieldTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :selected-keys="selectedKeys"
        @toggle-field="$emit('toggle-field', $event)"
        @add-common="$emit('add-common', $event)"
      />

      <!-- Fields belonging directly to this node -->
      <div
        v-if="node.fields && node.fields.length > 0"
        class="divide-y divide-slate-50 bg-slate-50/50"
      >
        <div
          v-for="f in node.fields"
          :key="f.key"
          class="flex cursor-pointer items-center justify-between px-4 py-1.5 hover:bg-slate-100"
          :class="selectedKeys.has(f.key) ? 'bg-brand-50' : ''"
          :style="`padding-left: ${(depth + 1) * 1.25 + 1}rem`"
          @click="$emit('toggle-field', f.key)"
        >
          <div class="flex min-w-0 items-center gap-2">
            <input
              type="checkbox"
              class="h-3.5 w-3.5 shrink-0 cursor-pointer rounded"
              :checked="selectedKeys.has(f.key)"
              @click.stop
              @change="$emit('toggle-field', f.key)"
            />
            <span
              v-if="f.split_type === 'agg_score'"
              class="rounded bg-brand-100 px-1 text-xs text-brand-700"
            >汇总</span>
            <span
              v-else-if="f.is_common"
              class="rounded bg-green-100 px-1 text-xs text-green-700"
            >常用</span>
            <span class="min-w-0 truncate text-sm text-slate-700">{{ f.label }}</span>
            <span
              v-if="FIELD_TOOLTIPS[f.split_type]"
              class="shrink-0 cursor-help select-none text-slate-400 hover:text-slate-600"
              :title="FIELD_TOOLTIPS[f.split_type]"
            >ⓘ</span>
          </div>
          <code class="ml-2 shrink-0 select-all rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-500">{{ f.key }}</code>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  depth: { type: Number, default: 0 },
  selectedKeys: { type: Set, required: true },
})

const emit = defineEmits(['toggle-field', 'add-common'])

// Default collapsed for depth-0 (root modules), expanded for deeper nodes when they have few fields
const expanded = ref(false)

// Recursively collect all field keys reachable from this node
function collectAllKeys(n) {
  const keys = []
  for (const f of n.fields || []) keys.push(f.key)
  for (const child of n.children || []) keys.push(...collectAllKeys(child))
  return keys
}

// Collect only is_common / agg_score field keys from this node and all descendants
function collectCommonKeys(n) {
  const keys = []
  for (const f of n.fields || []) {
    if (f.is_common || f.split_type === 'agg_score') keys.push(f.key)
  }
  for (const child of n.children || []) keys.push(...collectCommonKeys(child))
  return keys
}

const allFieldKeys = computed(() => collectAllKeys(props.node))

function onToggleSelectAll() {
  const keys = collectCommonKeys(props.node)
  const allSelected = keys.length > 0 && keys.every((k) => props.selectedKeys.has(k))
  for (const k of keys) {
    emit('toggle-field', k, allSelected ? 'deselect' : 'select')
  }
}

function onAddCommon() {
  emit('add-common', props.node)
}

const FIELD_TOOLTIPS = {
  self_score: '学生本人填写的原始自评分',
  process_record: '学生自评时填写的过程说明文字',
  reviewer_score: '评审老师打出的分数（双评时按项目规则取均值/最大值/第一次）',
  arbitration_score: '当双评分差超出阈值时由仲裁员最终确定的分，可覆盖评审分',
  final_adopted_score: '最终确认分：优先取仲裁分，否则按规则合并多轮评审分（最终成绩）',
  imported_score: '通过 Excel 批量导入的外部成绩（如体测成绩、课程成绩）',
  agg_score: '该模块/指标所有子项的加权汇总总分',
  evidence_count: '学生上传的佐证材料数量',
  evidence_names: '佐证材料文件名列表（分号分隔）',
  evidence_urls: '佐证材料下载链接列表（换行分隔）',
}
</script>
