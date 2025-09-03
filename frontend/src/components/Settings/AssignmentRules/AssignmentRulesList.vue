<template>
  <div
    v-if="assignmentRulesList.loading && !assignmentRulesList.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else>
    <div
      v-if="assignmentRulesList.data?.length === 0"
      class="flex items-center justify-center rounded-md border border-gray-200 p-4"
    >
      <div class="text-sm text-ink-gray-7">
        {{ __('No items in the list') }}
      </div>
    </div>
    <div v-else>
      <div class="grid grid-cols-11 items-center gap-4 text-sm text-gray-600">
        <div class="col-span-7 ml-2">{{ __('Assignment rule') }}</div>
        <div class="col-span-2">{{ __('Priority') }}</div>
        <div class="col-span-2">{{ __('Enabled') }}</div>
      </div>
      <hr class="mt-2 mx-2" />
      <div
        v-for="assignmentRule in assignmentRulesList.data"
        :key="assignmentRule.name"
      >
        <AssignmentRuleListItem :data="assignmentRule" />
        <hr class="mx-2" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { LoadingIndicator } from 'frappe-ui'
import { inject } from 'vue'
import AssignmentRuleListItem from './AssignmentRuleListItem.vue'

const assignmentRulesList = inject('assignmentRulesList')
</script>
