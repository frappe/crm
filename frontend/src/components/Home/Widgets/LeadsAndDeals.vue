<template>
  <HomeWidget
    :title="titles[doctype || 'Both']"
    :subtitle="tabEmpty[tab].subtitle"
    :resource="resource"
    :config="doctype ? null : config"
    :viewAll="recordListRoute(filter.doctype)"
    :emptyText="tabEmpty[tab].text"
    :emptyIcon="tabEmpty[tab].icon"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #tabs>
      <HomeTabs v-model="tab" :tabs="tabs" :counts="resource.data?.counts" />
    </template>
    <template #default="{ rows }">
      <HomeTable :columns="columns[tab]" :rows="rows" :rowRoute="recordRoute" />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeTabs from '@/components/Home/HomeTabs.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { useTabbedHomeWidget } from '@/composables/homeWidget'
import { recordListRoute, recordRoute } from '@/utils/home'
import { computed, ref } from 'vue'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
  doctype: { type: String, default: null },
})

const emit = defineEmits(['update:config'])

const titles = {
  Both: __('Needs your attention'),
  Lead: __('Leads needing attention'),
  Deal: __('Deals needing attention'),
}

const filter = computed(() =>
  props.doctype ? { doctype: props.doctype } : props.config,
)

const tabs = [
  { label: __('Awaiting reply'), value: 'replies' },
  { label: __('New'), value: 'new' },
]

const tabEmpty = {
  replies: {
    subtitle: __('Customers waiting on a reply from you'),
    text: __('No one is waiting on a reply from you.'),
    icon: 'lucide-inbox',
  },
  new: {
    subtitle: __('New leads and deals, newest first'),
    text: __('Nothing new for you right now.'),
    icon: 'lucide-sparkles',
  },
}

const columns = {
  replies: [
    homeColumns.record(),
    homeColumns.status(),
    homeColumns.channel(),
    homeColumns.timeAgo('awaiting_reply_since', __('Waiting since')),
  ],
  new: [
    homeColumns.record(),
    homeColumns.status(),
    homeColumns.timeAgo('creation', __('Created')),
  ],
}

const tab = ref('replies')

const resource = useTabbedHomeWidget('leads_and_deals', tab, () => filter.value)
</script>
