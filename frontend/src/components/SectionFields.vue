<template>
  <div class="flex max-h-[300px] flex-col gap-1.5 overflow-y-auto">
    <div
      v-for="field in fields"
      :key="field.label"
      class="flex items-center gap-2 px-3 leading-5 first:mt-3"
    >
      <div class="w-[106px] shrink-0 text-sm text-gray-600">
        {{ field.label }}
      </div>
      <div class="grid min-h-[28px] flex-1 text-base items-center overflow-hidden">
        <FormControl
          v-if="
            [
              'email',
              'number',
              'date',
              'password',
              'textarea',
              'checkbox',
            ].includes(field.type)
          "
          class="form-control"
          :class="{
            '[&_input]:text-gray-500':
              field.type === 'date' && !data[field.name],
          }"
          :type="field.type"
          :value="data[field.name]"
          :placeholder="field.placeholder"
          :debounce="500"
          @change.stop="emit('update', field.name, $event.target.value)"
        />
        <FormControl
          v-else-if="field.type === 'select'"
          class="form-control cursor-pointer [&_select]:cursor-pointer"
          type="select"
          :value="data[field.name]"
          :options="field.options"
          :debounce="500"
          @change.stop="emit('update', field.name, $event.target.value)"
        />
        <Link
          v-else-if="field.type === 'link'"
          class="form-control"
          :value="data[field.name]"
          :doctype="field.doctype"
          :placeholder="field.placeholder"
          @change="(data) => emit('update', field.name, data)"
          :onCreate="field.create"
        />
        <Tooltip
          v-else-if="field.type === 'read_only'"
          class="flex h-7 cursor-pointer items-center px-2 py-1"
          :text="field.tooltip"
        >
          {{ field.value }}
        </Tooltip>
        <FormControl
          v-else
          class="form-control"
          type="text"
          :value="data[field.name]"
          :placeholder="field.placeholder"
          :debounce="500"
          @change.stop="emit('update', field.name, $event.target.value)"
        />
      </div>
      <ArrowUpRightIcon
        v-if="field.type === 'link' && field.link && data[field.name]"
        class="h-4 w-4 shrink-0 cursor-pointer text-gray-600 hover:text-gray-800"
        @click="field.link(data[field.name])"
      />
    </div>
  </div>
</template>

<script setup>
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import Link from '@/components/Controls/Link.vue'
import { FormControl, Tooltip } from 'frappe-ui'
import { defineModel } from 'vue'

const props = defineProps({
  fields: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update'])

const data = defineModel()
</script>

<style scoped>
:deep(.form-control input:not([type='checkbox'])),
:deep(.form-control select),
:deep(.form-control textarea),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}

:deep(.form-control button) {
  gap: 0;
}
:deep(.form-control [type='checkbox']) {
  margin-left: 9px;
  cursor: pointer;
}

:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control button svg) {
  color: white;
  width: 0;
}
</style>
