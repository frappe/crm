<template>
  <NestedPopover>
    <template #target>
      <Button label="View Settings">
        <template #prefix>
          <SettingsIcon class="h-4" />
        </template>
      </Button>
    </template>
    <template #body>
      <div
        class="my-2 rounded-lg border border-gray-100 bg-white p-1.5 shadow-xl"
      >
        <Draggable
          :list="columns"
          @end="onEnd"
          item-key="key"
          class="list-group"
        >
          <template #item="{ element }">
            <div
              class="flex cursor-grab items-center justify-between gap-6 rounded px-2 py-1.5 text-base text-gray-800 hover:bg-gray-50"
            >
              <div class="flex items-center gap-2">
                <DragVerticalIcon class="h-3.5" />
                <div>{{ element.label }}</div>
              </div>
              <div class="flex cursor-pointer items-center gap-1">
                <Button variant="ghost" class="!h-5 w-5 !p-1">
                  <EditIcon class="h-3.5" />
                </Button>
                <Button variant="ghost" class="!h-5 w-5 !p-1">
                  <FeatherIcon name="x" class="h-3.5" />
                </Button>
              </div>
            </div>
          </template>
        </Draggable>
      </div>
    </template>
  </NestedPopover>
</template>

<script setup>
import SettingsIcon from '@/components/Icons/SettingsIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import NestedPopover from '@/components/NestedPopover.vue'
import Draggable from 'vuedraggable'
import { computed, defineModel } from 'vue'
import { FeatherIcon, call } from 'frappe-ui'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const list = defineModel()

const columns = computed(() => list.value?.data?.columns)

const rows = computed(() => list.value?.data?.rows)

function onEnd() {
  call(
    'crm.fcrm.doctype.crm_list_view_settings.crm_list_view_settings.update',
    {
      doctype: props.doctype,
      columns: columns.value,
      rows: rows.value,
    }
  )
}
</script>
