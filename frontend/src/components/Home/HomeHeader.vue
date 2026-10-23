<template>
  <div class="flex flex-wrap items-end justify-between gap-4 px-5 pb-2 pt-6">
    <div class="flex flex-col gap-2">
      <h1 class="text-2xl-semibold leading-none text-ink-gray-9">
        {{ greeting }}
      </h1>
      <p
        class="flex flex-wrap items-center gap-1.5 text-p-base text-ink-gray-6"
      >
        <template v-for="(part, index) in summary" :key="part.key">
          <span v-if="index" aria-hidden="true">·</span>
          <span :class="{ 'text-ink-gray-8': part.count }">
            {{ part.label }}
          </span>
        </template>
      </p>
    </div>
    <div class="flex items-center gap-2">
      <Button
        :label="__('My reports')"
        iconLeft="lucide-chart-column"
        :route="{ name: 'Dashboard' }"
      />
      <Dropdown :options="newOptions">
        <Button variant="solid" :label="__('New')" iconLeft="lucide-plus" />
      </Dropdown>
    </div>
  </div>
  <LeadModal v-if="showLeadModal" v-model="showLeadModal" />
  <DealModal v-if="showDealModal" v-model="showDealModal" />
</template>

<script setup>
import LeadModal from '@/components/Modals/LeadModal.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { homeVersion, refreshHome } from '@/composables/homeWidget'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { greetingFor } from '@/utils/home'
import { Dropdown, createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const { user } = sessionStore()
const { getUser } = usersStore()
const { showModal } = useDoctypeModal()

const showLeadModal = ref(false)
const showDealModal = ref(false)

const counts = createResource({
  url: 'crm.api.home.get_counts',
  auto: true,
  initialData: {},
})

watch(homeVersion, () => counts.reload())

const greeting = computed(() => {
  const name = getUser().first_name || getUser().full_name
  return greetingFor(new Date(), name)
})

const summary = computed(() => {
  const {
    replies_waiting = 0,
    follow_ups_due = 0,
    new_leads = 0,
  } = counts.data || {}
  return [
    {
      key: 'replies',
      count: replies_waiting,
      label:
        replies_waiting === 1
          ? __('1 reply waiting')
          : __('{0} replies waiting', [replies_waiting]),
    },
    {
      key: 'follow-ups',
      count: follow_ups_due,
      label:
        follow_ups_due === 1
          ? __('1 follow-up due')
          : __('{0} follow-ups due', [follow_ups_due]),
    },
    {
      key: 'leads',
      count: new_leads,
      label:
        new_leads === 1 ? __('1 new lead') : __('{0} new leads', [new_leads]),
    },
  ]
})

const newOptions = [
  {
    label: __('Lead'),
    icon: 'lucide-user-plus',
    onClick: () => (showLeadModal.value = true),
  },
  {
    label: __('Deal'),
    icon: 'lucide-handshake',
    onClick: () => (showDealModal.value = true),
  },
  {
    label: __('Task'),
    icon: 'lucide-square-check',
    onClick: () =>
      showModal({
        doctype: 'CRM Task',
        title: 'Task',
        defaults: { status: 'Todo', priority: 'Low', assigned_to: user },
        callbacks: { afterInsert: refreshHome },
      }),
  },
]
</script>
