<template>
  <div ref="chartRef" :style="{ width: '100%', height: `${height}px` }" />
</template>

<script setup>
/**
 * @component GaugeChart
 * @description ECharts 仪表盘组件，用于展示整体完成率/评审率等关键指标。
 * @props {number} value - 当前值 (0~100)
 * @props {string} title - 指标名称
 * @props {string} color - 主色
 * @props {number} height - 图表高度
 */
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { GaugeChart as EGaugeChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([EGaugeChart, CanvasRenderer])

const props = defineProps({
  value: { type: Number, default: 0 },
  title: { type: String, default: '' },
  color: { type: String, default: '#059669' },
  height: { type: Number, default: 200 },
})

const chartRef = ref(null)
let chart = null

function buildOption() {
  return {
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 5,
        itemStyle: { color: props.color },
        progress: {
          show: true,
          width: 16,
          roundCap: true,
        },
        pointer: { show: false },
        axisLine: {
          lineStyle: { width: 16, color: [[1, 'rgba(148,163,184,0.15)']] },
          roundCap: true,
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: {
          show: !!props.title,
          offsetCenter: [0, '70%'],
          fontSize: 12,
          color: '#64748b',
        },
        detail: {
          offsetCenter: [0, '30%'],
          fontSize: 28,
          fontWeight: 700,
          color: '#1e293b',
          formatter: '{value}%',
        },
        data: [{ value: Math.round(props.value), name: props.title }],
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

watch(() => [props.value, props.title, props.color], () => nextTick(renderChart))

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
