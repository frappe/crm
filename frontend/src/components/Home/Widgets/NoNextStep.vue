<template>
  <HomeWidget
    :title="__('No next step')"
    :resource="resource"
    :config="config"
    :viewAll="recordListViews(config.doctype)"
    :emptyText="__('Every open lead and deal has a next step.')"
    :columns="['1rem', 'minmax(0,1fr)', '2.5rem', '1.75rem']"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ row }">
      <RecordRow :record="row">
        <ListCell class="justify-end text-ink-gray-5">
          <Tooltip
            :text="__('Last activity {0}', [prettyDate(row.idle_since)])"
          >
            <span class="relative whitespace-nowrap">
              {{ prettyDate(row.idle_since, true) }}
            </span>
          </Tooltip>
        </ListCell>
        <ListCell>
          <FollowUpPopover
            :doctype="row.doctype"
            :docname="row.name"
            :title="__('Follow up with {0}', [recordTitle(row).title])"
            @created="refreshHome"
          >
            <Button
              class="relative"
              variant="ghost"
              icon="lucide-calendar-clock"
              :tooltip="__('Follow up')"
            />
          </FollowUpPopover>
        </ListCell>
      </RecordRow>
    </template>
  </HomeWidget>
</template>
<script setup>
import FollowUpPopover from '@/components/FollowUp/FollowUpPopover.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import RecordRow from '@/components/Home/RecordRow.vue'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'
import { prettyDate } from '@/utils'
import { recordListViews, recordTitle } from '@/utils/home'
import { Tooltip } from 'frappe-ui'
import { ListCell } from 'frappe-ui/list'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('no_next_step', () => props.config)
</script>
