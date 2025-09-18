<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Sales Funnel" />
    </template>
    <template #right-header>
      <Dropdown :button="{ label: selectedLabel }" :options="funnelOptions" />
    </template>
  </LayoutHeader>

  <div class="chart-wrapper">
    <div class="chart-container">
      <CanvasJSChart :options="options" :style="styleOptions" />
      <div class="watermark-box"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Dropdown } from 'frappe-ui'

const viewControls = ref(null)
const selectedLabel = ref('Select Funnel Type 🡫')

const funnelTypes = {
  Buyer: { doctype: 'CRM Lead', filterKey: 'custom_lead_type' },
  Seller: { doctype: 'CRM Lead', filterKey: 'custom_lead_type' },
  Property: { doctype: 'Item'}
}

const options = ref({
  animationEnabled: true,
  theme: 'light1',
  // Design was getting very inconsistent with funnel type change. So commented it out.
  // title: {
  //   text: 'Sales Funnel by Lead Stage',
  //   horizontalAlign: 'center',
  //   fontSize: 26,
  //   padding: { right: 120 }
  // },
  data: [{
    type: 'funnel',
    indexLabel: '{label} - {y}%',  // Single % sign here
    neckHeight: 0,
    dataPoints: [
      { label: 'None', y: 0 },
      { label: 'Service', y: 0 },
      { label: 'Pipeline', y: 0 },
      { label: 'After-Sales', y: 0 }
    ]
  }]
})

const styleOptions = ref({
  width: '100%',
  height: '100%'
})

const funnelOptions = [
  {
    label: 'Buyer Lead',
    icon: 'handshake',
    onClick: () => fetchFunnelData('Buyer')
  },
  {
    label: 'Seller Lead',
    icon: 'tag',
    onClick: () => fetchFunnelData('Seller')
  },
  {
    label: 'Property',
    icon: 'home',
    onClick: () => fetchFunnelData('Property')
  }
]

const fetchFunnelData = async (type) => {
  selectedLabel.value = `${type} Funnel 🡫`

  const { doctype, filterKey } = funnelTypes[type]

  try {
    const response = await call(
      'crm.utils.sales_funnel.get_funnel_data',
      {
        doctype,
        value: type,
        filter_key: filterKey,
      }
    )

    const stageData = response.message || {}

    // Calculate percentages from raw counts
    const total = Object.values(stageData).reduce((sum, val) => sum + (val || 0), 0)

    const chartData = [
      { label: 'None', y: total ? Math.round((stageData['None'] || 0) / total * 100) : 0 },
      { label: 'Service', y: total ? Math.round((stageData['Service Stage'] || 0) / total * 100) : 0 },
      { label: 'Pipeline', y: total ? Math.round((stageData['Pipeline Stage'] || 0) / total * 100) : 0 },
      { label: 'After-Sales', y: total ? Math.round((stageData['After Sales Stage'] || 0) / total * 100) : 0 }
    ]

    options.value = {
      ...options.value,
      data: [{
        ...options.value.data[0],
        dataPoints: chartData
      }]
    }
  } catch (err) {
    console.error('Failed to fetch funnel data:', err)
    // Reset to empty state
    options.value.data[0].dataPoints = [
      { label: 'None', y: 0 },
      { label: 'Service', y: 0 },
      { label: 'Pipeline', y: 0 },
      { label: 'After-Sales', y: 0 }
    ]
  }
}

// Load initial data when component mounts
onMounted(() => {
  fetchFunnelData('Buyer')
})
</script>

<style scoped>
.chart-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 90vh;
  padding: 2rem;
  background-color: #fff;
  box-sizing: border-box;
}

.chart-container {
  position: relative;
  width: 75vw;
  max-width: 900px;
  height: 600px;
}

.watermark-box {
  position: absolute;
  bottom: 0.1%;
  right: 0.2%;
  width: clamp(60px, 8vw, 100px);
  height: 10px;
  background-color: rgb(255, 255, 255);
  border-radius: 6px;
  z-index: 10;
  transition: all 0.3s ease;
}
</style>
