<template>
  <div class="mini-bar-chart">
    <div
      v-for="(item, idx) in normalizedItems"
      :key="idx"
      class="mini-bar-chart__row"
    >
      <span class="mini-bar-chart__label" :title="item.label">{{ item.label }}</span>
      <div class="mini-bar-chart__track">
        <div
          class="mini-bar-chart__fill"
          :style="{ width: `${item.widthPct}%`, backgroundColor: item.color || defaultColor }"
        />
      </div>
      <span class="mini-bar-chart__value">{{ item.displayValue }}</span>
    </div>
    <div v-if="!items?.length" class="mini-bar-chart__empty">暂无数据</div>
  </div>
</template>

<script setup>
/**
 * @component MiniBarChart
 * @description 轻量水平柱状图组件，用于专业/班级对比。
 * @props {Array} items - [{label, value, color?}]
 * @props {number} maxValue - 手动指定最大值，不设则自动取 items 最大值
 */
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  maxValue: { type: Number, default: 0 },
  defaultColor: { type: String, default: '#3b82f6' },
  suffix: { type: String, default: '' },
})

const normalizedItems = computed(() => {
  if (!props.items?.length) return []
  const max = props.maxValue || Math.max(...props.items.map((i) => i.value ?? 0), 1)
  return props.items.map((item) => ({
    ...item,
    widthPct: Math.min(100, ((item.value ?? 0) / max) * 100),
    displayValue: `${item.value ?? 0}${props.suffix}`,
  }))
})
</script>

<style scoped>
.mini-bar-chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mini-bar-chart__row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mini-bar-chart__label {
  flex-shrink: 0;
  width: 70px;
  font-size: 12px;
  color: #475569;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-bar-chart__track {
  flex: 1;
  height: 18px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.mini-bar-chart__fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 2px;
}

.mini-bar-chart__value {
  flex-shrink: 0;
  width: 48px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  text-align: right;
}

.mini-bar-chart__empty {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: #94a3b8;
}
</style>
