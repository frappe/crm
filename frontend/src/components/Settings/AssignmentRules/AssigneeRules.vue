<template>
  <div>
    <div class="flex flex-col gap-1">
      <span class="text-lg font-semibold text-ink-gray-8">{{
        __('Assignee rules')
      }}</span>
      <span class="text-p-sm text-ink-gray-6">
        {{
          __('Choose how {0} are assigned among salespeople.', [documentType])
        }}
      </span>
    </div>
    <div class="mt-8 flex items-center justify-between gap-2">
      <div>
        <div class="text-base font-medium text-ink-gray-8">
          {{
            __('{0} routing', [
              assignmentRuleData.documentType == 'CRM Lead'
                ? __('Lead')
                : __('Deal'),
            ])
          }}
        </div>
        <div class="text-p-sm text-ink-gray-6 mt-1">
          {{
            __('Choose how {0} are assigned among the selected assignees.', [
              documentType,
            ])
          }}
        </div>
      </div>
      <div>
        <Popover placement="bottom-end">
          <template #target="{ togglePopover }">
            <div
              class="flex items-center justify-between text-base rounded h-7 py-1.5 pl-2 pr-2 border border-outline-gray-2 bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] select-none min-w-40"
              @click="togglePopover()"
            >
              <div>
                {{
                  documentRoutingOptions.find(
                    (option) => option.value == assignmentRuleData.rule,
                  )?.label
                }}
              </div>
              <FeatherIcon name="chevron-down" class="size-4" />
            </div>
          </template>
          <template #body="{ togglePopover }">
            <div
              class="p-1 text-ink-gray-7 mt-1 w-48 bg-white shadow-xl rounded"
            >
              <div
                v-for="option in documentRoutingOptions"
                :key="option.value"
                class="p-2 cursor-pointer hover:bg-gray-50 text-sm flex items-center justify-between rounded"
                @click="
                  () => {
                    assignmentRuleData.rule = option.value
                    togglePopover()
                  }
                "
              >
                <span>
                  {{ option.label }}
                </span>
                <FeatherIcon
                  v-if="assignmentRuleData.rule == option.value"
                  name="check"
                  class="size-4"
                />
              </div>
            </div>
          </template>
        </Popover>
      </div>
    </div>
    <div class="mt-7 flex items-center justify-between gap-2">
      <div>
        <div class="text-base font-medium text-ink-gray-8">
          {{ __('Assignees') }}
        </div>
        <div class="text-p-sm text-ink-gray-6 mt-1">
          {{ __('Select the assignees for {0}.', [documentType]) }}
        </div>
      </div>
      <AssigneeSearch @addAssignee="validateAssignmentRule('users')" />
    </div>
    <div class="mt-4 flex flex-wrap gap-2">
      <div
        v-for="user in users"
        :key="user.name"
        class="flex items-center gap-2 text-sm bg-surface-gray-2 rounded-md p-1 w-max px-2 select-none"
      >
        <Avatar :image="user.user_image" :label="user.full_name" size="sm" />
        <div class="text-ink-gray-7">
          {{ user.full_name }}
        </div>
        <Tooltip
          v-if="user.email == assignmentRuleData.lastUser"
          :text="__('Last user assigned by this rule')"
          :hover-delay="0.35"
          :placement="'top'"
        >
          <div
            class="text-xs rounded-full select-none bg-blue-600 text-white p-0.5 px-2"
          >
            {{ __('Last') }}
          </div>
        </Tooltip>
        <Button variant="ghost" icon="x" @click="removeAssignedUser(user)" />
      </div>
    </div>
    <ErrorMessage :message="assignmentRuleErrors.users" />
  </div>
</template>

<script setup>
import { Avatar, Button, ErrorMessage, Popover, Tooltip } from 'frappe-ui'
import AssigneeSearch from './AssigneeSearch.vue'
import { computed, inject } from 'vue'
import { usersStore } from '@/stores/users'

const { getUser } = usersStore()
const assignmentRuleData = inject('assignmentRuleData')
const assignmentRuleErrors = inject('assignmentRuleErrors')
const validateAssignmentRule = inject('validateAssignmentRule')
const documentType = computed(() =>
  assignmentRuleData.value.documentType == 'CRM Lead'
    ? __('leads')
    : __('deals'),
)

const documentRoutingOptions = [
  {
    label: 'Auto-rotate',
    value: 'Round Robin',
  },
  {
    label: 'Assign by workload',
    value: 'Load Balancing',
  },
]

const removeAssignedUser = (user) => {
  assignmentRuleData.value.users = assignmentRuleData.value.users.filter(
    (u) => u.user !== user.name,
  )
  validateAssignmentRule('users')
}

const users = computed(() => {
  const _users = []
  assignmentRuleData.value.users.forEach((user) => {
    _users.push(getUser(user.user))
  })
  return _users
})
</script>
