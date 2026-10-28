<template>
  <div class="rounded-6 border border-outline-gray-2 bg-surface-base">
    <div class="flex items-center gap-3 border-b border-outline-gray-1 p-4">
      <Avatar :label="leadName" :image="doc.image" size="xl" class="shrink-0" />
      <div class="flex min-w-0 flex-col gap-1">
        <span class="truncate text-base-medium text-ink-gray-9">
          {{ leadName }}
        </span>
        <span class="truncate text-p-sm text-ink-gray-5">{{ doc.name }}</span>
      </div>
    </div>
    <dl
      class="grid grid-cols-[minmax(0,8rem)_minmax(0,1fr)] items-center gap-x-3 gap-y-3 p-4"
    >
      <template v-for="row in rows" :key="row.fieldname">
        <dt class="truncate text-base text-ink-gray-5">{{ row.label }}</dt>
        <dd class="flex min-w-0 items-center gap-1.5 text-base text-ink-gray-8">
          <template v-if="row.fieldname === 'status'">
            <IndicatorIcon :class="getLeadStatus(doc.status)?.color" />
            <span class="truncate">{{ row.text }}</span>
          </template>
          <template v-else-if="row.fieldname === 'lead_owner'">
            <UserAvatar :user="doc.lead_owner as string" size="xs" hideStatus />
            <span class="truncate">{{ row.text }}</span>
          </template>
          <template v-else-if="row.fieldname === '_assign'">
            <MultipleAvatar
              :avatars="parseAssignees(assignees)"
              size="sm"
              hideStatus
            />
            <Tooltip :text="__('Assignments from both leads are kept')">
              <span
                class="lucide-circle-help size-3.5 shrink-0 text-ink-gray-5"
                :aria-label="__('Assignments from both leads are kept')"
                role="img"
              />
            </Tooltip>
          </template>
          <Tooltip v-else :text="row.text">
            <span class="truncate">{{ row.text }}</span>
          </Tooltip>
        </dd>
      </template>
    </dl>
  </div>
</template>

<script setup lang="ts">
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { Avatar, Tooltip } from 'frappe-ui'
import { computed } from 'vue'
import { parseAssignees } from '@/utils'
import { formatAmount, type MergeField } from '@/composables/useLeadMerge'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'

const props = defineProps<{
  // the target lead with the picked values laid over it
  doc: Record<string, unknown>
  // plain-text values for the fields the merge decides on
  displays: Record<string, string>
  // every field the merge decides on, so picks outside FIELDS show up too
  fields: MergeField[]
  assignees: string[]
}>()

const { getLeadStatus } = statusesStore()
const { getUser } = usersStore()

const FIELDS: [string, string][] = [
  ['email', __('Email')],
  ['status', __('Status')],
  ['lead_owner', __('Lead owner')],
  ['job_title', __('Job title')],
  ['website', __('Website')],
  ['organization', __('Organization')],
  ['mobile_no', __('Mobile no.')],
  ['salutation', __('Salutation')],
  ['territory', __('Territory')],
  ['industry', __('Industry')],
  ['source', __('Source')],
  ['no_of_employees', __('No. of employees')],
  ['annual_revenue', __('Annual revenue')],
  ['_assign', __('Assigned to')],
]

function text(fieldname: string): string {
  if (fieldname in props.displays) return props.displays[fieldname]
  const value = props.doc[fieldname]
  if (fieldname === 'lead_owner') return getUser(value as string).full_name
  if (fieldname === 'annual_revenue') return formatAmount(value)
  return String(value)
}

// mirrors CRMLead.set_full_name, which rebuilds lead_name when the merge saves
const leadName = computed(() => {
  const doc = props.doc
  if (!doc.first_name) return (doc.lead_name || doc.name) as string
  return [doc.salutation, doc.first_name, doc.middle_name, doc.last_name]
    .filter(Boolean)
    .join(' ')
})

const rows = computed(() => {
  const listed = new Set(FIELDS.map(([fieldname]) => fieldname))
  const extra: [string, string][] = props.fields
    .filter((f) => !listed.has(f.fieldname))
    .map((f) => [f.fieldname, f.label])
  return [...FIELDS, ...extra]
    .filter(([fieldname]) =>
      fieldname === '_assign'
        ? props.assignees.length
        : props.doc[fieldname] || fieldname in props.displays,
    )
    .map(([fieldname, label]) => ({ fieldname, label, text: text(fieldname) }))
})
</script>
