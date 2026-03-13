<template>
  <div ref="chartRef" :style="{ width: '100%', height: `${height}px` }" />
</template>

<script setup>
/**
 * @component BarChart
 * @description ECharts 柱状图组件，用于院系/专业/班级数据对比。
 * @props {Array} categories - X轴标签 [string]
 * @props {Array} seriesData - 数据系列 [{name, data: [number], color?}]
 * @props {number} height - 图表高度
 * @props {boolean} horizontal - 是否水平（横向）柱状图
 * @props {string} suffix - 数值后缀（如 '%', '分'）
 */
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart as EBarChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([EBarChart, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  categories: { type: Array, default: () => [] },
  seriesData: { type: Array, default: () => [] },
  height: { type: Number, default: 280 },
  horizontal: { type: Boolean, default: false },
  suffix: { type: String, default: '' },
})

const chartRef = ref(null)
let chart = null

const COLORS = ['#c8102e', '#3b82f6', '#059669', '#f59e0b', '#8b5cf6']

function buildOption() {
  const categoryAxis = {
    type: 'category',
    data: props.categories,
    axisLabel: {
      fontSize: 11,
      color: '#475569',
      rotate: props.horizontal ? 0 : (props.categories.length > 6 ? 30 : 0),
    },
    axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } },
    axisTick: { show: false },
  }
  const valueAxis = {
    type: 'value',
    axisLabel: { fontSize: 11, color: '#94a3b8', formatter: `{value}${props.suffix}` },
    splitLine: { lineStyle: { color: 'rgba(148,163,184,0.15)' } },
  }

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        let html = `<div style="font-size:12px;color:#334155;font-weight:600">${params[0].axisValue}</div>`
        for (const p of params) {
          html += `<div style="font-size:11px;color:#64748b;margin-top:2px">${p.marker} ${p.seriesName}: <b style="color:#1e293b">${p.value}${props.suffix}</b></div>`
        }
        return html
      },
    },
    legend: props.seriesData.length > 1
      ? { bottom: 0, textStyle: { fontSize: 11, color: '#64748b' } }
      : undefined,
    grid: {
      left: props.horizontal ? 80 : 40,
      right: 16,
      top: 12,
      bottom: props.seriesData.length > 1 ? 36 : 24,
      containLabel: false,
    },
    xAxis: props.horizontal ? valueAxis : categoryAxis,
    yAxis: props.horizontal ? categoryAxis : valueAxis,
    series: props.seriesData.map((s, i) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
      barMaxWidth: 32,
      itemStyle: {
        color: s.color || COLORS[i % COLORS.length],
        borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0],
      },
    })),
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
  () => [props.categories, props.seriesData],
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
