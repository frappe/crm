<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Record Payment')" @click="showCreateModal = true" />
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <div v-else>
      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead>
            <tr class="border-b border-outline-gray-2 text-p-xs text-ink-gray-5 uppercase tracking-wider">
              <th class="pb-3 pr-4 font-medium">{{ __('Student') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Amount') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Method') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Date') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Abonement') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Notes') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in payments" :key="p.name" class="border-b border-outline-gray-1 text-p-sm">
              <td class="py-3 pr-4 text-ink-gray-8 font-medium">{{ p.student }}</td>
              <td class="py-3 pr-4 text-ink-gray-8 font-medium">\${{ p.amount }}</td>
              <td class="py-3 pr-4">
                <Badge :label="__(p.payment_method)" variant="subtle" size="sm" />
              </td>
              <td class="py-3 pr-4 text-ink-gray-7">{{ p.payment_date }}</td>
              <td class="py-3 pr-4 text-ink-gray-7">{{ p.student_abonement || '-' }}</td>
              <td class="py-3 pr-4 text-ink-gray-5 max-w-xs truncate">{{ p.notes || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="payments.length === 0" class="flex flex-col items-center justify-center h-40 text-ink-gray-5">
        <CreditCardIcon class="w-10 h-10 mb-2" />
        <div>{{ __('No payments recorded') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import CreditCardIcon from '~icons/lucide/credit-card'
import { ref, onMounted } from 'vue'

const payments = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const crumbs = [{ label: __('LMS'), route: { name: 'LmsCourses' } }, { label: __('Payments') }]

onMounted(async () => {
  loading.value = true
  try {
    payments.value = await call('crm.api.lms.get_payments')
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading payments'))
  } finally {
    loading.value = false
  }
})
</script>