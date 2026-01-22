<template>
  <div
    v-if="assignmentRulesList.loading && !assignmentRulesList.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <EmptyState
    v-else-if="assignmentRulesList.data?.length === 0"
    title="No assignment rules found"
    description="Add one to get started."
    :icon="h(SettingsIcon2, { class: 'rotate-90'})"
  />
  <div v-else>
    <div class="flex items-center py-2 px-4 text-sm text-ink-gray-5">
      <div class="w-7/12">{{ __('Assignment rule') }}</div>
      <div class="w-3/12">{{ __('Priority') }}</div>
      <div class="w-2/12">{{ __('Enabled') }}</div>
    </div>
    <div class="h-px border-t mx-4 border-outline-gray-modals" />
    <div class="overflow-y-auto px-2">
      <template
        v-for="(assignmentRule, i) in assignmentRulesList.data"
        :key="assignmentRule.name"
      >
        <AssignmentRuleListItem :data="assignmentRule" />
        <hr v-if="assignmentRulesList.data.length !== i + 1" class="mx-2" />
      </template>
    </div>
  </div>
</template>

<script setup>
import SettingsIcon2 from '@/components/Icons/SettingsIcon2.vue'
import AssignmentRuleListItem from './AssignmentRuleListItem.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { LoadingIndicator } from 'frappe-ui'
import { inject, h } from 'vue'

const assignmentRulesList = inject('assignmentRulesList')
</script>
