<template>
  <div class="flex items-center justify-between gap-2 p-5">
    <div class="flex flex-1 items-center overflow-hidden pl-1 gap-2">
      <FadedScrollableDiv
        class="flex overflow-x-auto -ml-1"
        orientation="horizontal"
      >
        <Draggable
          class="flex w-full gap-2 items-center"
          :list="newQuickFilters"
          group="filters"
          item-key="fieldname"
        >
          <template #item="{ element: filter }">
            <div class="group whitespace-nowrap cursor-grab">
              <Button class="cursor-grab">
                <template #default>
                  <Tooltip :text="filter.fieldname">
                    <span>{{ filter.label }}</span>
                  </Tooltip>
                </template>
                <template #suffix>
                  <FeatherIcon
                    class="h-3.5 cursor-pointer group-hover:flex hidden"
                    name="x"
                    @click.stop="removeQuickFilter(filter)"
                  />
                </template>
              </Button>
            </div>
          </template>
        </Draggable>
      </FadedScrollableDiv>
      <div>
        <Autocomplete
          value=""
          :options="quickFilterOptions"
          @change="(e) => addQuickFilter(e)"
        >
          <template #target="{ togglePopover }">
            <Button
              class="whitespace-nowrap mr-2"
              variant="ghost"
              :label="__('Add filter')"
              iconLeft="plus"
              @click="togglePopover()"
            />
          </template>
          <template #item-label="{ option }">
            <Tooltip :text="option.value" :hover-delay="1">
              <div class="flex-1 truncate text-ink-gray-7">
                {{ option.label }}
              </div>
            </Tooltip>
          </template>
        </Autocomplete>
      </div>
    </div>
    <div class="-ml-2 h-[70%] border-l" />
    <div class="flex gap-1">
      <Button
        :label="__('Save')"
        :loading="updateQuickFilters.loading"
        @click="saveQuickFilters"
      />
      <Button icon="x" @click="$emit('close')" />
    </div>
  </div>
</template>
<script setup>
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import Draggable from 'vuedraggable'
import { useQuickFilters } from './quickFilter'
import { Autocomplete, Button, Tooltip, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const list = defineModel()

const emit = defineEmits(['close'])

const {
  newQuickFilters,
  quickFilterOptions,
  addQuickFilter,
  removeQuickFilter,
  saveQuickFilters,
  updateQuickFilters,
} = useQuickFilters(list.value, props.doctype)
</script>
