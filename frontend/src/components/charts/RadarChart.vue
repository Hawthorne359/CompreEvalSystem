<template>
  <div ref="chartRef" :style="{ width: '100%', height: `${height}px` }" />
</template>

<script setup>
/**
 * @component RadarChart
 * @description ECharts 雷达图组件，用于多维度对比（院系/专业完成率、评分等）。
 * @props {Array} indicators - 雷达维度 [{name, max}]
 * @props {Array} seriesData - 数据系列 [{name, values: [...], color?}]
 * @props {number} height - 图表高度
 */
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { RadarChart as ERadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([ERadarChart, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  indicators: { type: Array, default: () => [] },
  seriesData: { type: Array, default: () => [] },
  height: { type: Number, default: 280 },
})

const chartRef = ref(null)
let chart = null

const COLORS = ['#c8102e', '#3b82f6', '#059669', '#f59e0b', '#8b5cf6', '#ec4899']

function buildOption() {
  return {
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 11, color: '#64748b' },
      data: props.seriesData.map((s) => s.name),
    },
    radar: {
      indicator: props.indicators.map((ind) => ({
        name: ind.name,
        max: ind.max ?? 100,
      })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#475569', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.25)' } },
      splitArea: { areaStyle: { color: ['rgba(241,245,249,0.6)', 'rgba(255,255,255,0.4)'] } },
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } },
    },
    series: [
      {
        type: 'radar',
        data: props.seriesData.map((s, i) => ({
          name: s.name,
          value: s.values,
          areaStyle: { opacity: 0.15 },
          lineStyle: { width: 2 },
          itemStyle: { color: s.color || COLORS[i % COLORS.length] },
        })),
      },
    ],
  }
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption(buildOption(), true)
}

function handleResize() {
  chart?.resize()
}

watch(
  () => [props.indicators, props.seriesData],
  () => nextTick(renderChart),
  { deep: true },
)

onMounted(() => {
  nextTick(renderChart)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>
