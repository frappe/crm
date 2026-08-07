<template>
  <div class="fc-cashflow-chart">
    <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Cashflow — Last 6 Months</h3>
    <div v-if="!data || !data.length" class="h-44 flex items-center justify-center text-sm text-gray-400">No data</div>
    <div v-else class="relative overflow-hidden" style="height:180px;">
      <svg :viewBox="'0 0 ' + svgW + ' ' + svgH" class="w-full h-full" preserveAspectRatio="none">
        <!-- grid lines -->
        <line v-for="y in gridYs" :key="y" :x1="PAD_L" :x2="svgW - PAD_R" :y1="y" :y2="y"
          stroke="currentColor" stroke-width="0.5" class="text-gray-200 dark:text-gray-700" />
        <!-- area fill inflow -->
        <path :d="areaPathInflow" class="fc-fill-inflow" fill-opacity="0.15" />
        <!-- area fill outflow -->
        <path :d="areaPathOutflow" class="fc-fill-outflow" fill-opacity="0.15" />
        <!-- line inflow -->
        <path :d="linePathInflow" fill="none" class="fc-stroke-inflow" stroke-width="2" stroke-linejoin="round" />
        <!-- line outflow -->
        <path :d="linePathOutflow" fill="none" class="fc-stroke-outflow" stroke-width="2" stroke-linejoin="round" />
        <!-- month labels -->
        <text v-for="(d, i) in data" :key="'lbl'+i"
          :x="xAt(i)" :y="svgH - 4"
          text-anchor="middle" font-size="9" fill="currentColor"
          class="text-gray-400 dark:text-gray-500"
        >{{ d.month.slice(0, 3) }}</text>
        <!-- dots inflow -->
        <circle v-for="(d, i) in data" :key="'di'+i"
          :cx="xAt(i)" :cy="yAt(d.inflow)" r="3" class="fc-fill-inflow" />
        <!-- dots outflow -->
        <circle v-for="(d, i) in data" :key="'do'+i"
          :cx="xAt(i)" :cy="yAt(d.outflow)" r="3" class="fc-fill-outflow" />
      </svg>
    </div>
    <!-- legend -->
    <div class="flex gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
      <span class="flex items-center gap-1"><span class="inline-block w-3 h-0.5 bg-emerald-500 rounded"></span>Inflow</span>
      <span class="flex items-center gap-1"><span class="inline-block w-3 h-0.5 bg-red-500 rounded"></span>Outflow</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Array, default: () => [] } })

const svgW = 400
const svgH = 160
const PAD_L = 8
const PAD_R = 8
const PAD_T = 12
const PAD_B = 20

const maxVal = computed(() => {
  if (!props.data.length) return 1
  return Math.max(...props.data.flatMap(d => [d.inflow, d.outflow]), 1)
})

const gridYs = computed(() => {
  const steps = 4
  return Array.from({ length: steps + 1 }, (_, i) =>
    PAD_T + ((svgH - PAD_T - PAD_B) * i) / steps
  )
})

function xAt(i) {
  const n = props.data.length
  if (n <= 1) return svgW / 2
  return PAD_L + (i / (n - 1)) * (svgW - PAD_L - PAD_R)
}

function yAt(val) {
  const chartH = svgH - PAD_T - PAD_B
  return PAD_T + chartH - (val / maxVal.value) * chartH
}

const linePathInflow = computed(() => {
  if (!props.data.length) return ''
  return props.data.map((d, i) => (i === 0 ? 'M' : 'L') + xAt(i) + ' ' + yAt(d.inflow)).join(' ')
})
const linePathOutflow = computed(() => {
  if (!props.data.length) return ''
  return props.data.map((d, i) => (i === 0 ? 'M' : 'L') + xAt(i) + ' ' + yAt(d.outflow)).join(' ')
})

const baseline = computed(() => svgH - PAD_B)

const areaPathInflow = computed(() => {
  if (!props.data.length) return ''
  const pts = props.data.map((d, i) => xAt(i) + ' ' + yAt(d.inflow)).join(' L')
  const first = xAt(0) + ' ' + baseline.value
  const last = xAt(props.data.length - 1) + ' ' + baseline.value
  return 'M ' + first + ' L ' + pts + ' L ' + last + ' Z'
})
const areaPathOutflow = computed(() => {
  if (!props.data.length) return ''
  const pts = props.data.map((d, i) => xAt(i) + ' ' + yAt(d.outflow)).join(' L')
  const first = xAt(0) + ' ' + baseline.value
  const last = xAt(props.data.length - 1) + ' ' + baseline.value
  return 'M ' + first + ' L ' + pts + ' L ' + last + ' Z'
})
</script>

<style scoped>
/* SVG elements can't use Tailwind utilities directly — map semantic colors here */
.fc-fill-inflow  { fill:   #10b981; } /* emerald-500 */
.fc-stroke-inflow { stroke: #10b981; }
.fc-fill-outflow  { fill:   #ef4444; } /* red-500 */
.fc-stroke-outflow { stroke: #ef4444; }
</style>
