<template>
  <div class="p-8 sticky top-0">
    <div class="flex items-start justify-between">
      <div class="flex flex-col gap-1">
        <h1 class="text-xl font-semibold text-ink-gray-8">
          {{ __('Assignment rules') }}
        </h1>
        <p class="text-p-base text-ink-gray-6 max-w-md">
          {{
            __(
              'Assignment Rules automatically route leads or deals to the right team members based on predefined conditions.',
            )
          }}
        </p>
      </div>
      <Button
        :label="__('Create new')"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="plus"
      />
    </div>
  </div>
  <div class="overflow-y-auto px-8 pb-6">
    <AssignmentRulesList />
  </div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import AssignmentRulesList from './AssignmentRulesList.vue'
import { inject, provide } from 'vue'

const updateStep = inject('updateStep')

const assignmentRulesListData = createResource({
  url: 'crm.api.assignment_rule.get_assignment_rules_list',
  cache: ['assignmentRules', 'get_assignment_rules_list'],
  auto: true,
})

provide('assignmentRulesList', assignmentRulesListData)

const goToNew = () => {
  updateStep('view', null)
}
</script>
