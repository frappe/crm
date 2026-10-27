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
      <HomeTable :columns="columns" :rows="rows" :rowRoute="recordRoute">
        <template #follow_up="{ row }">
          <div class="flex justify-end" @click.stop.prevent>
            <FollowUpPopover
              :doctype="row.doctype"
              :docname="row.name"
              :title="__('Follow up with {0}', [recordTitle(row)])"
              @created="refreshHome"
            >
              <Button
                variant="ghost"
                icon="lucide-calendar-clock"
                :tooltip="__('Follow up')"
              />
            </FollowUpPopover>
          </div>
        </template>
      </HomeTable>
    </template>
  </HomeWidget>
</template>
<script setup>
import FollowUpPopover from '@/components/FollowUp/FollowUpPopover.vue'
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'
import { recordListViews, recordRoute, recordTitle } from '@/utils/home'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const columns = [
  homeColumns.record(),
  homeColumns.status(),
  homeColumns.timeAgo('idle_since', __('Idle since')),
  { key: 'follow_up', label: '', width: '1.75rem' },
]

const resource = useHomeWidget('no_next_step', () => props.config)
</script>
