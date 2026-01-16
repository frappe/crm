<template>
  <BusinessHolidayList v-if="holidayListActiveStep.screen == 'list'" />
  <BusinessHolidayView v-else-if="holidayListActiveStep.screen == 'view'" />
</template>

<script setup>
import BusinessHolidayList from './BusinessHolidayList.vue'
import BusinessHolidayView from './BusinessHolidayView.vue'
import { ref, provide, onUnmounted } from 'vue'
import { createListResource } from 'frappe-ui'
import { holidayListActiveStep } from './utils'

const holidayListSearchQuery = ref('')

const holidayListData = createListResource({
  doctype: 'CRM Holiday List',
  fields: ['name'],
  cache: ['holidayList'],
  orderBy: 'modified desc',
  start: 0,
  pageLength: 999,
  auto: true,
})

provide('holidayListSearchQuery', holidayListSearchQuery)
provide('holidayListResource', holidayListData)

onUnmounted(() => {
  holidayListSearchQuery.value = ''
  holidayListData.filters = {}
})
</script>
