<template>
  <div
    v-for="field in fields"
    :key="field.label"
    class="flex items-center gap-2 px-3 text-base leading-5 first:mt-3"
  >
    <div class="w-[106px] shrink-0 text-gray-600">
      {{ field.label }}
    </div>
    <div class="flex-1 overflow-hidden">
      <Link
        v-if="field.type === 'link'"
        class="form-control"
        :value="data[field.name]"
        :doctype="field.doctype"
        :placeholder="field.placeholder"
        @change="(data) => emit('update', field.name, data)"
        :onCreate="field.create"
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
      <FormControl
        v-else-if="field.type === 'email'"
        class="form-control"
        type="email"
        :value="data[field.name]"
        :debounce="500"
        @change.stop="emit('update', field.name, $event.target.value)"
      />
      <FormControl
        v-else-if="field.type === 'date'"
        class="form-control"
        type="date"
        :value="data[field.name]"
        :debounce="500"
        @change.stop="emit('update', field.name, $event.target.value)"
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
    <ExternalLinkIcon
      v-if="field.type === 'link' && field.link && data[field.name]"
      class="h-4 w-4 shrink-0 cursor-pointer text-gray-600"
      @click="field.link(data[field.name])"
    />
  </div>
</template>

<script setup>
import ExternalLinkIcon from '@/components/Icons/ExternalLinkIcon.vue'
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
