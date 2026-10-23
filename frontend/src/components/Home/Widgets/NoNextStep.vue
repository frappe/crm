<template>
  <HomeWidget
    :title="__('No next step')"
    :resource="resource"
    :config="config"
    :viewAll="recordListViews(config.doctype)"
    :emptyText="__('Every open lead and deal has a next step.')"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows }">
      <RecordRow v-for="row in rows" :key="row.name" :record="row">
        <Tooltip :text="__('Last activity {0}', [prettyDate(row.idle_since)])">
          <span class="whitespace-nowrap">
            {{ prettyDate(row.idle_since, true) }}
          </span>
        </Tooltip>
        <FollowUpPopover
          :doctype="row.doctype"
          :docname="row.name"
          :title="__('Follow up with {0}', [recordTitle(row).title])"
          @created="refreshHome"
        >
          <Button
            variant="ghost"
            icon="lucide-calendar-clock"
            :tooltip="__('Follow up')"
          />
        </FollowUpPopover>
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

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('no_next_step', () => props.config)
</script>
