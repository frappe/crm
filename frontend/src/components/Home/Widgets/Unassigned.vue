<template>
  <HomeWidget
    :title="__('Unassigned')"
    :resource="resource"
    :config="config"
    :viewAll="recordListViews(config.doctype)"
    :emptyText="__('Every new lead and deal has an assignee.')"
    emptyIcon="lucide-user-check"
    :columns="['1rem', 'minmax(0,1fr)', '2.5rem']"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ row }">
      <RecordRow :record="row">
        <ListCell class="justify-end text-ink-gray-5">
          <Tooltip :text="__('Created {0}', [prettyDate(row.creation)])">
            <span class="relative whitespace-nowrap">
              {{ prettyDate(row.creation, true) }}
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
import { prettyDate } from '@/utils'
import { recordListViews } from '@/utils/home'
import { Tooltip } from 'frappe-ui'
import { ListCell } from 'frappe-ui/list'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('unassigned', () => props.config)
</script>
