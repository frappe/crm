<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between px-2 pt-2">
      <div class="flex flex-col gap-1 w-9/12">
        <div class="flex gap-2 items-center">
          <h2 class="flex text-2xl-semibold leading-none h-5">
            {{ __('Assignment Rules') }}
          </h2>
          <Tooltip :text="__('View documentation')">
            <a
              href="https://docs.frappe.io/crm/assignment-rule"
              target="_blank"
            >
              <LucideCircleQuestionMark class="h-4 w-4 text-ink-gray-6" />
            </a>
          </Tooltip>
        </div>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Auto-assign leads/deals to the right sales user based on predefined conditions.',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('New')"
          icon-left="lucide-plus"
          variant="solid"
          @click="goToNew()"
        />
      </div>
    </div>

    <!-- Assignment rules list -->
    <div class="flex h-full overflow-y-auto">
      <AssignmentRulesList />
    </div>
  </div>
</template>

<script setup>
import AssignmentRulesList from './AssignmentRulesList.vue'
import { createResource, Tooltip } from 'frappe-ui'
import LucideCircleQuestionMark from '~icons/lucide/circle-question-mark'
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
