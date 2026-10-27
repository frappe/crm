<template>
  <HomeWidget
    :title="__('Team replies waiting')"
    :resource="resource"
    :config="config"
    :viewAll="recordListRoute(config.doctype)"
    :emptyText="__('No one is waiting on a reply from your team.')"
    emptyIcon="lucide-inbox"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows }">
      <HomeTable :columns="columns" :rows="rows" :rowRoute="recordRoute" />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { useHomeWidget } from '@/composables/homeWidget'
import { recordListRoute, recordRoute } from '@/utils/home'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const columns = [
  homeColumns.record(),
  homeColumns.status(),
  homeColumns.channel(),
  homeColumns.timeAgo('awaiting_reply_since', __('Waiting since')),
  homeColumns.user('owner', __('Owner')),
]

const resource = useHomeWidget('team_replies_waiting', () => props.config)
</script>
