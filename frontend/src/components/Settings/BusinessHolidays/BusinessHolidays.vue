<template>
  <HolidayLists v-if="holidayScreen.screen == 'list'" />
  <!-- Keyed on the name so saving a new or renamed list reloads it fresh. -->
  <HolidayListView v-else :key="holidayScreen.name ?? ''" />
</template>

<script setup lang="ts">
import HolidayLists from './HolidayLists.vue'
import HolidayListView from './HolidayListView.vue'
import { holidayScreen } from './store'
import type { HolidayListRow } from './types'
import { createListResource } from 'frappe-ui'
import { onUnmounted, provide, ref } from 'vue'

const holidaySearchQuery = ref('')

const holidayListResource = createListResource<HolidayListRow>({
  doctype: 'CRM Holiday List',
  fields: ['name', 'description', 'from_date', 'to_date', 'total_holidays'],
  cache: ['HolidayLists'],
  orderBy: 'modified desc',
  start: 0,
  pageLength: 999,
  auto: true,
})

provide('holidaySearchQuery', holidaySearchQuery)
provide('holidayListResource', holidayListResource)

onUnmounted(() => {
  holidaySearchQuery.value = ''
  holidayListResource.filters = {}
  holidayScreen.value = { screen: 'list', name: null }
})
</script>
