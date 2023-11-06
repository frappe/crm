<template>
  <div class="flex flex-col gap-4">
    <div v-for="section in allFields" :key="section.section">
      <div class="grid grid-cols-3 gap-4">
        <div v-for="field in section.fields" :key="field.name">
          <div class="mb-2 text-sm text-gray-600">{{ field.label }}</div>
          <FormControl
            v-if="field.type === 'select'"
            type="select"
            :options="field.options"
            v-model="newLead[field.name]"
          >
            <template v-if="field.name == 'status'" #prefix>
              <IndicatorIcon :class="leadStatuses[newLead[field.name]].color" />
            </template>
          </FormControl>
          <FormControl
            v-else-if="field.type === 'email'"
            type="email"
            v-model="newLead[field.name]"
          />
          <FormControl
            v-else-if="field.type === 'link'"
            type="autocomplete"
            :value="newLead[field.name]"
            :options="field.options"
            @change="(e) => field.change(e)"
            :placeholder="field.placeholder"
            class="form-control"
          />
          <FormControl
            v-else-if="field.type === 'user'"
            type="autocomplete"
            :options="activeAgents"
            :value="getUser(newLead[field.name]).full_name"
            @change="(option) => (newLead[field.name] = option.email)"
            :placeholder="field.placeholder"
          >
            <template #prefix>
              <UserAvatar class="mr-2" :user="newLead[field.name]" size="sm" />
            </template>
            <template #item-prefix="{ option }">
              <UserAvatar class="mr-2" :user="option.email" size="sm" />
            </template>
          </FormControl>
          <Dropdown
            v-else-if="field.type === 'dropdown'"
            :options="statusDropdownOptions(newLead)"
            class="w-full flex-1"
          >
            <template #default="{ open }">
              <Button
                :label="newLead[field.name]"
                class="w-full justify-between"
              >
                <template #prefix>
                  <IndicatorIcon
                    :class="leadStatuses[newLead[field.name]].color"
                  />
                </template>
                <template #default>{{ newLead[field.name] }}</template>
                <template #suffix>
                  <FeatherIcon
                    :name="open ? 'chevron-up' : 'chevron-down'"
                    class="h-4 text-gray-600"
                  />
                </template>
              </Button>
            </template>
          </Dropdown>
          <FormControl v-else type="text" v-model="newLead[field.name]" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { leadStatuses, statusDropdownOptions, activeAgents } from '@/utils'
import { FormControl, Button, Dropdown, FeatherIcon } from 'frappe-ui'

const { getUser } = usersStore()
const { organizationOptions } = organizationsStore()

const props = defineProps({
  newLead: {
    type: Object,
    required: true,
  },
})

const allFields = [
  {
    section: 'Lead Details',
    fields: [
      {
        label: 'Salutation',
        name: 'salutation',
        type: 'select',
        options: [
          {
            label: 'Mr',
            value: 'Mr',
          },
          {
            label: 'Ms',
            value: 'Ms',
          },
          {
            label: 'Mrs',
            value: 'Mrs',
          },
        ],
      },
      {
        label: 'First Name',
        name: 'first_name',
        type: 'data',
      },
      {
        label: 'Last Name',
        name: 'last_name',
        type: 'data',
      },
      {
        label: 'Email',
        name: 'email',
        type: 'data',
      },
      {
        label: 'Mobile no',
        name: 'mobile_no',
        type: 'data',
      },
    ],
  },
  {
    section: 'Other Details',
    fields: [
      {
        label: 'Organization',
        name: 'organization',
        type: 'link',
        placeholder: 'Organization',
        options: organizationOptions,
        change: (option) => {
          newLead.organization = option.name
        },
      },
      {
        label: 'Status',
        name: 'status',
        type: 'select',
        options: statusDropdownOptions(props.newLead),
      },
      {
        label: 'Lead owner',
        name: 'lead_owner',
        type: 'user',
        placeholder: 'Lead owner',
      },
    ],
  },
]
</script>
