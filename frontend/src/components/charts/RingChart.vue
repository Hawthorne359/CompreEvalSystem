<template>
  <div class="ring-chart" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        :stroke="trackColor"
        :stroke-width="strokeWidth"
      />
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        fill="none"
        :stroke="color"
        :stroke-width="strokeWidth"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
        class="ring-chart__progress"
        :style="{ '--target-offset': dashOffset }"
      />
    </svg>
    <div class="ring-chart__label">
      <slot>
        <span class="ring-chart__value" :style="{ fontSize: valueFontSize }">{{ displayValue }}</span>
        <span v-if="showUnit" class="ring-chart__unit">%</span>
      </slot>
    </div>
  </div>
</template>

<script setup>
/**
 * @component RingChart
 * @description 纯 SVG 环形图组件，用于完成率/占比展示。
 * @props {number} percentage - 0~100 的百分比
 * @props {string} color - 进度条颜色
 * @props {number} size - 画布尺寸 (px)
 * @props {number} strokeWidth - 环形粗细
 */
import { computed } from 'vue'

const props = defineProps({
  percentage: { type: Number, default: 0 },
  color: { type: String, default: '#3b82f6' },
  trackColor: { type: String, default: '#e2e8f0' },
  size: { type: Number, default: 120 },
  strokeWidth: { type: Number, default: 10 },
  showUnit: { type: Boolean, default: true },
})

const center = computed(() => props.size / 2)
const radius = computed(() => (props.size - props.strokeWidth) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const clampedPct = computed(() => Math.max(0, Math.min(100, props.percentage)))
const dashOffset = computed(() => circumference.value * (1 - clampedPct.value / 100))
const displayValue = computed(() => Math.round(clampedPct.value))
const valueFontSize = computed(() => `${Math.max(14, props.size / 5)}px`)
</script>

<style scoped>
.ring-chart {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.ring-chart svg {
  transform: rotate(-90deg);
}

.ring-chart__progress {
  transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.ring-chart__label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1px;
}

.ring-chart__value {
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
}

.ring-chart__unit {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}
</style>
