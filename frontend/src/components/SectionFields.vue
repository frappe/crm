<template>
  <div class="flex max-h-[300px] flex-col gap-1.5 overflow-y-auto">
    <div
      v-for="field in fields"
      :key="field.label"
      :class="[field.hidden && 'hidden']"
      class="flex items-center gap-2 px-3 leading-5 first:mt-3"
    >
      <div class="w-[106px] shrink-0 text-sm text-gray-600">
        {{ field.label }}
        <span class="text-red-500">{{ field.reqd ? ' *' : '' }}</span>
      </div>
      <div
        class="grid min-h-[28px] flex-1 items-center overflow-hidden text-base"
      >
        <Tooltip
          v-if="field.read_only && field.type !== 'checkbox'"
          class="flex h-7 cursor-pointer items-center px-2 py-1 text-gray-600"
          :text="field.tooltip"
        >
          {{ data[field.name] }}
        </Tooltip>
        <FormControl
          v-else-if="field.type == 'checkbox'"
          class="form-control"
          :type="field.type"
          v-model="data[field.name]"
          @change.stop="emit('update', field.name, $event.target.checked)"
          :disabled="Boolean(field.read_only)"
        />
        <FormControl
          v-else-if="
            ['email', 'number', 'date', 'password', 'textarea'].includes(
              field.type
            )
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
          v-else-if="['lead_owner', 'deal_owner'].includes(field.name)"
          class="form-control"
          :value="data[field.name] && getUser(data[field.name]).full_name"
          doctype="User"
          @change="(data) => emit('update', field.name, data)"
          :placeholder="'Select' + ' ' + field.label + '...'"
          :hideMe="true"
        >
          <template v-if="data[field.name]" #prefix>
            <UserAvatar class="mr-1.5" :user="data[field.name]" size="sm" />
          </template>
          <template #item-prefix="{ option }">
            <UserAvatar class="mr-1.5" :user="option.value" size="sm" />
          </template>
          <template #item-label="{ option }">
            <Tooltip :text="option.value">
              {{ getUser(option.value).full_name }}
            </Tooltip>
          </template>
        </Link>
        <Link
          v-else-if="field.type === 'link'"
          class="form-control"
          :value="data[field.name]"
          :doctype="field.doctype"
          :placeholder="field.placeholder"
          @change="(data) => emit('update', field.name, data)"
          :onCreate="field.create"
        />
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
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { Tooltip } from 'frappe-ui'
import { defineModel } from 'vue'

const props = defineProps({
  fields: {
    type: Object,
    required: true,
  },
})

const { getUser } = usersStore()

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
