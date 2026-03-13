<template>
  <div>
    <!-- 当前节点行 -->
    <div
      :class="[
        'flex items-center gap-3 px-4 py-3',
        depth === 1
          ? (node.id === highlightId ? 'border-b border-slate-100 bg-blue-50' : 'border-b border-slate-100 bg-slate-50')
          : (node.id === highlightId ? 'bg-blue-50' : 'hover:bg-slate-50'),
        depth > 1 ? 'border-b border-slate-50' : '',
      ]"
      :style="depth > 1 ? `padding-left: ${(depth - 1) * 2}rem` : ''"
    >
      <!-- 展开/收起按钮（有子项时显示） -->
      <button
        v-if="node.children && node.children.length"
        type="button"
        class="flex-none text-slate-400 hover:text-slate-600"
        :title="expanded ? '收起子项' : '展开子项'"
        @click="expanded = !expanded"
      >
        <span class="inline-block w-4 text-center text-xs font-bold">
          {{ expanded ? '▼' : '▶' }}
        </span>
      </button>
      <!-- 叶节点占位，保持对齐 -->
      <span v-else class="inline-block w-4 flex-none text-center text-xs text-slate-300">—</span>

      <!-- 节点信息 -->
      <div class="min-w-0 flex-1">
        <span :class="depth === 1 ? 'font-medium text-slate-800' : 'text-slate-800'">
          {{ node.name }}
        </span>
        <!-- 根节点 category 标签 -->
        <span
          v-if="node.category"
          class="ml-2 rounded bg-brand-50 px-1.5 py-0.5 text-xs text-brand-700"
        >{{ node.category }}</span>
        <!-- 聚合方式（有子项或是根节点时显示） -->
        <span
          v-if="node.children?.length || depth === 1"
          class="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500"
        >{{ aggLabel }}</span>
        <!-- 记录性标记 -->
        <span
          v-if="node.is_record_only"
          class="ml-2 rounded bg-orange-100 px-1.5 py-0.5 text-xs font-medium text-orange-600"
        >记录</span>
        <!-- 评分来源（叶节点，或有子项但来源非 children 时显示） -->
        <span
          v-if="!node.children?.length || node.score_source !== 'children'"
          class="ml-2 rounded px-1.5 py-0.5 text-xs"
          :class="{
            'bg-orange-50 text-orange-600': node.score_source === 'import',
            'bg-purple-50 text-purple-600': node.score_source === 'self',
            'bg-teal-50 text-teal-600': node.score_source === 'children',
            'bg-slate-100 text-slate-500': node.score_source === 'reviewer' || !node.score_source,
          }"
        >{{ sourceLabel }}</span>
        <!-- 权重（父级为加权求和时） -->
        <span v-if="showWeight" class="ml-1 text-xs text-slate-400">权重 {{ node.weight }}</span>
        <!-- 满分 -->
        <span class="ml-1 text-xs text-slate-400">
          <template v-if="parentAggFormula === 'sum_capped'">
            <!-- 父级为封顶求和：子项自身满分无独立意义，显示封顶说明 -->
            <span class="text-slate-300">（封顶汇总至父级上限）</span>
          </template>
          <template v-else-if="hasGradeRules">
            <!-- 有年级规则：满分文字省略，规则行明细在后面展示 -->
            <span v-if="node.children?.length" class="text-slate-300">
              {{ { sum: '（子项自动汇总）', weighted_sum: '（加权汇总）', average: '（平均汇总）', sum_capped: '（封顶汇总）' }[node.agg_formula] ?? '' }}
            </span>
          </template>
          <template v-else-if="node.max_score != null">
            满分 {{ node.max_score }}
            <span v-if="node.children?.length" class="text-slate-300">
              {{ { sum: '（子项自动汇总）', weighted_sum: '（加权汇总）', average: '（平均汇总）', sum_capped: '（封顶汇总）' }[node.agg_formula] ?? '' }}
            </span>
          </template>
          <template v-else>
            <span class="text-slate-300">无上限</span>
          </template>
        </span>
        <!-- grade_rules 规则行明细（替代原「年级差异」标签） -->
        <span v-if="hasGradeRules" class="ml-1 inline-flex flex-wrap gap-1">
          <span
            v-for="(rule, idx) in node.grade_rules.rules"
            :key="idx"
            class="rounded bg-green-50 px-1.5 py-0.5 text-xs text-green-600"
          >
            {{ rule.label ? rule.label + ' ' : formatYearRange(rule.min_year, rule.max_year) + ' ' }}{{ gradeRuleDisplay(rule) }}
          </span>
        </span>
        <!-- 说明 -->
        <span v-if="node.description" class="ml-2 truncate text-xs text-slate-400">
          {{ node.description }}
        </span>
      </div>

      <!-- 操作按钮 -->
      <div class="flex flex-none gap-2 text-sm">
        <button
          v-if="depth < maxDepth"
          type="button"
          class="app-action app-action-success"
          @click="$emit('add-child', node)"
        >+ 添加子项</button>
        <button
          type="button"
          class="app-action app-action-default"
          @click="$emit('edit', node)"
        >编辑</button>
        <button
          type="button"
          class="app-action app-action-danger"
          @click="$emit('delete', node, depth === 1)"
        >删除</button>
      </div>
    </div>

    <!-- 子节点（递归） -->
    <div v-if="expanded && node.children?.length">
      <IndicatorTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :max-depth="maxDepth"
        :parent-agg-formula="node.agg_formula"
        :highlight-id="highlightId"
        @add-child="$emit('add-child', $event)"
        @edit="$emit('edit', $event)"
        @delete="(node, isParent) => $emit('delete', node, isParent)"
      />
    </div>
    <!-- 展开但无子项提示（仅根节点展示） -->
    <div
      v-else-if="expanded && depth === 1 && (!node.children || node.children.length === 0)"
      class="px-10 py-3 text-xs text-slate-400"
    >暂无子项，点击「添加子项」</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  depth: { type: Number, default: 1 },
  maxDepth: { type: Number, default: 5 },
  /** 父节点的聚合方式，用于判断是否显示 weight 字段 */
  parentAggFormula: { type: String, default: '' },
  /** 最近编辑的指标 ID，匹配时该节点行显示浅蓝背景高亮 */
  highlightId: { type: [Number, String], default: null },
})

defineEmits(['add-child', 'edit', 'delete'])

const expanded = ref(true)

const aggLabel = computed(() => {
  const map = { sum: '求和', weighted_sum: '加权求和', average: '平均', sum_capped: '封顶求和' }
  return map[props.node.agg_formula] ?? props.node.agg_formula
})

const sourceLabel = computed(() => {
  const map = {
    import: '统一导入',
    self: '学生自评',
    reviewer: '学生自评',   // reviewer 已废弃，等同于 self 显示
    children: '子项汇总',
  }
  return map[props.node.score_source] ?? '学生自评'
})

const showWeight = computed(() => props.parentAggFormula === 'weighted_sum')

const hasGradeRules = computed(() => {
  const rules = props.node.grade_rules?.rules
  return Array.isArray(rules) && rules.length > 0
})

/**
 * 年级数字转汉字标签（大一=1 … 大六=6，超出范围用"第N年级"）
 * @param {number} n
 * @returns {string}
 */
const YEAR_LABELS = { 1: '大一', 2: '大二', 3: '大三', 4: '大四', 5: '大五', 6: '大六' }

/**
 * 将 [min_year, max_year] 格式化为年级范围文字，如「大一~大三」或「大二」
 * @param {number} min
 * @param {number} max
 * @returns {string}
 */
function formatYearRange(min, max) {
  const s = YEAR_LABELS[min] ?? `第${min}年级`
  const e = YEAR_LABELS[max] ?? `第${max}年级`
  return min === max ? s : `${s}~${e}`
}

/**
 * 规则行满分显示：
 * - 系数为 1 时：显示「满分N」
 * - 系数不为 1 时：显示「满分N×C=贡献M」
 * @param {object} rule
 * @returns {string}
 */
function gradeRuleDisplay(rule) {
  const ms = rule.max_score != null ? Number(rule.max_score) : null
  if (ms == null) return '无上限'
  const coeff = rule.coefficient != null && rule.coefficient !== '' ? Number(rule.coefficient) : 1
  if (coeff === 1) return `满分${ms}`
  const contribution = +(ms * coeff).toFixed(2)
  return `满分${ms}×${coeff}=${contribution}`
}
</script>
