<template>
  <div
    class="flex p-3 items-center justify-between cursor-pointer hover:bg-surface-menu-bar rounded"
  >
    <div class="w-7/12" @click="updateStep('view', data)">
      <div class="text-base text-ink-gray-7 font-medium">{{ data.name }}</div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-p-base w-full text-ink-gray-5 mt-0.5 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="w-3/12">
      <select
        class="w-full h-7 text-base hover:bg-surface-gray-3 rounded-md p-0 pl-2 pr-5 bg-transparent -ml-2 border-0 text-ink-gray-8 focus-visible:!ring-0 bg-none truncate"
        v-model="data.priority"
        @update:modelValue="onPriorityChange"
        @change="onPriorityChange"
      >
        <option
          v-for="option in priorityOptions"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>
    </div>
    <div class="flex justify-between items-center w-2/12">
      <Switch
        size="sm"
        :modelValue="!data.disabled"
        @update:modelValue="onToggle"
      />
      <Dropdown placement="right" :options="dropdownOptions">
        <Button
          icon="more-horizontal"
          variant="ghost"
          @click="isConfirmingDelete = false"
        />
      </Dropdown>
    </div>
  </div>
  <Dialog
    :options="{ title: __('Duplicate Assignment Rule') }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :label="__('New Assignment Rule Name')"
          type="text"
          v-model="duplicateDialog.name"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          :label="__('Close')"
          @click="duplicateDialog.show = false"
        />
        <Button variant="solid" :label="__('Duplicate')" @click="duplicate()" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Button,
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  Select,
  Switch,
  toast,
} from 'frappe-ui'
import { inject, ref } from 'vue'

const assignmentRulesList = inject('assignmentRulesList')
const updateStep = inject('updateStep')

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
})

const priorityOptions = [
  { label: 'Low', value: '0' },
  { label: 'Low-Medium', value: '1' },
  { label: 'Medium', value: '2' },
  { label: 'Medium-High', value: '3' },
  { label: 'High', value: '4' },
]

const duplicateDialog = ref({
  show: false,
  name: '',
})

const isConfirmingDelete = ref(false)

const deleteAssignmentRule = () => {
  createResource({
    url: 'frappe.client.delete',
    params: {
      doctype: 'Assignment Rule',
      name: props.data.name,
    },
    onSuccess: () => {
      assignmentRulesList.reload()
      isConfirmingDelete.value = false
      toast.success(__('Assignment rule deleted'))
    },
    auto: true,
  })
}

const dropdownOptions = [
  {
    label: __('Duplicate'),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: props.data.name + ' (Copy)',
      }
    },
    icon: 'copy',
  },
  {
    label: __('Delete'),
    icon: 'trash-2',
    onClick: (e) => {
      e.preventDefault()
      e.stopImmediatePropagation()
      isConfirmingDelete.value = true
    },
    condition: () => !isConfirmingDelete.value,
  },
  {
    label: __('Confirm Delete'),
    icon: 'trash-2',
    theme: 'red',
    onClick: () => deleteAssignmentRule(),
    condition: () => isConfirmingDelete.value,
  },
]

const duplicate = () => {
  createResource({
    url: 'crm.api.assignment_rule.duplicate_assignment_rule',
    params: {
      docname: props.data.name,
      new_name: duplicateDialog.value.name,
    },
    onSuccess: (data) => {
      assignmentRulesList.reload()
      toast.success(__('Assignment rule duplicated'))
      duplicateDialog.value.show = false
      duplicateDialog.value.name = ''
      updateStep('view', data)
    },
    auto: true,
  })
}

const onPriorityChange = () => {
  setAssignmentRuleValue('priority', props.data.priority)
}

const onToggle = () => {
  if (!props.data.users_exists && props.data.disabled) {
    toast.error(__('Cannot enable rule without adding users in it'))
    return
  }
  setAssignmentRuleValue('disabled', !props.data.disabled, 'status')
}

const setAssignmentRuleValue = (key, value, fieldName = undefined) => {
  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'Assignment Rule',
      name: props.data.name,
      fieldname: key,
      value: value,
    },
    onSuccess: () => {
      assignmentRulesList.reload()
      toast.success(__('Assignment rule {0} updated', [fieldName || key]))
    },
    auto: true,
  })
}
</script>
