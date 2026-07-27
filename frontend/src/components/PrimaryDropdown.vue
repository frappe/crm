<template>
  <Popover class="w-full min-w-0">
    <template #target="{ isOpen, togglePopover }">
      <Button
        :label="value"
        class="dropdown-button flex w-full items-center !justify-between bg-surface-base !px-2.5 py-1.5 text-base text-ink-gray-8 placeholder-ink-gray-4 transition-colors hover:bg-surface-base focus:bg-surface-base focus:outline-none focus:ring-0"
        @click="togglePopover"
      >
        <div v-if="value" class="truncate">{{ value }}</div>
        <div v-else class="text-base leading-5 text-ink-gray-4 truncate">
          {{ placeholder }}
        </div>
        <template #suffix>
          <FeatherIcon
            :name="isOpen ? 'chevron-up' : 'chevron-down'"
            class="h-4 text-ink-gray-5"
          />
        </template>
      </Button>
    </template>
    <template #body>
      <div
        class="my-2 p-1.5 min-w-72 space-y-1.5 divide-y divide-outline-gray-1 rounded-lg bg-surface-elevation-2 shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
      >
        <div>
          <PrimaryDropdownItem
            v-for="option in options"
            :key="option.name || option.value"
            :option="option"
            :placeholder="itemPlaceholder"
            :validate="validate"
          />
          <PrimaryDropdownItem
            v-if="draft"
            :option="draft"
            :placeholder="itemPlaceholder"
            :validate="validate"
          />
          <div v-if="!options.length && !draft">
            <div class="p-1.5 pl-3 pr-4 text-base text-ink-gray-4">
              {{ __('No {0} available', [label]) }}
            </div>
          </div>
        </div>
        <div v-if="!draft" class="pt-1.5">
          <Button
            variant="ghost"
            class="w-full !justify-start"
            :label="__('Create New')"
            iconLeft="plus"
            @click="addDraft"
          />
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import PrimaryDropdownItem from '@/components/PrimaryDropdownItem.vue'
import { Popover } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  value: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  itemPlaceholder: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  validate: { type: Function, default: null },
  onCreate: { type: Function, default: null },
  label: { type: String, default: '' },
})

// A new entry is drafted here, never in the parent's doc, so an incomplete
// value can never leak into an auto-save. The draft is saved by handing its
// value to onCreate, and cleared once saved or dismissed.
const draft = ref(null)

function addDraft() {
  draft.value = {
    value: '',
    selected: false,
    onSave: async (option) => {
      await props.onCreate?.(option.value)
      draft.value = null
    },
    onDelete: () => (draft.value = null),
  }
}
</script>

<style scoped>
.dropdown-button {
  border-color: transparent;
  background: transparent;
  /* The button is a shrink-0 flex child with min-width:auto, so it overflows
     its container on long values. Allow it to shrink so the value can truncate. */
  min-width: 0;
}

/* Button wraps the value in a `truncate` span; it also needs min-width:0 to
   shrink in the button's flex row so the long value ellipsizes. */
:deep(.dropdown-button > span) {
  min-width: 0;
  flex: 1;
}
</style>
