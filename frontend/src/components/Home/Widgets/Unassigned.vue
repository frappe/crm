<template>
  <HomeWidget
    :title="__('Unassigned')"
    :resource="resource"
    :config="config"
    :viewAll="recordListViews(config.doctype)"
    :emptyText="__('Every new lead and deal has an assignee.')"
    emptyIcon="lucide-user-check"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows }">
      <RecordRow
        v-for="row in rows"
        :key="`${row.doctype}:${row.name}`"
        :record="row"
      >
        <Tooltip :text="__('Created {0}', [prettyDate(row.creation)])">
          <span class="w-8 whitespace-nowrap text-right">
            {{ prettyDate(row.creation, true) }}
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
import { prettyDate } from '@/utils'
import { recordListViews } from '@/utils/home'
import { Tooltip } from 'frappe-ui'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('unassigned', () => props.config)
</script>
