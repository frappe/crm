<template>
  <HomeWidget
    :title="__('Assigned to me')"
    :resource="resource"
    :config="config"
    :viewAll="recordListViews(config.doctype)"
    :emptyText="__('Nothing open is assigned to you.')"
    emptyIcon="lucide-user-check"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows }">
      <RecordRow
        v-for="row in rows"
        :key="`${row.doctype}:${row.name}`"
        :record="row"
      >
        <Badge
          v-if="isNew(row)"
          :label="__('New')"
          theme="blue"
          variant="subtle"
        />
        <Tooltip :text="__('Assigned {0}', [prettyDate(row.assigned_at)])">
          <span class="w-8 whitespace-nowrap text-right">
            {{ prettyDate(row.assigned_at, true) }}
          </span>
        </Tooltip>
      </RecordRow>
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import RecordRow from '@/components/Home/RecordRow.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { statusesStore } from '@/stores/statuses'
import { prettyDate } from '@/utils'
import { recordListViews } from '@/utils/home'
import { Badge, Tooltip } from 'frappe-ui'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const { getLeadStatus, getDealStatus } = statusesStore()

const resource = useHomeWidget('assigned_to_me', () => props.config)

function isNew(row) {
  const getStatus = row.doctype === 'CRM Deal' ? getDealStatus : getLeadStatus
  return getStatus(row.status)?.type === 'Open'
}
</script>
