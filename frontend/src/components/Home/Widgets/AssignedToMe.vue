<template>
  <HomeWidget
    :title="__('Assigned to me')"
    :resource="resource"
    :config="config"
    :viewAll="recordListViews(config.doctype)"
    :emptyText="__('Nothing open is assigned to you.')"
    emptyIcon="lucide-user-check"
    :columns="['1rem', 'minmax(0,1fr)', '3rem', '2.5rem']"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ row }">
      <RecordRow :record="row">
        <ListCell class="justify-end">
          <Badge
            v-if="isNew(row)"
            :label="__('New')"
            theme="blue"
            variant="subtle"
          />
        </ListCell>
        <ListCell class="justify-end text-ink-gray-5">
          <Tooltip :text="__('Assigned {0}', [prettyDate(row.assigned_at)])">
            <span class="relative whitespace-nowrap">
              {{ prettyDate(row.assigned_at, true) }}
            </span>
          </Tooltip>
        </ListCell>
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
import { ListCell } from 'frappe-ui/list'

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
