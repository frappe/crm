<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('New Abonement')" @click="showCreateModal = true" />
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <template v-else>
      <div class="mb-8">
        <div class="text-lg font-semibold text-ink-gray-8 mb-4">{{ __('Abonement Types') }}</div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div v-for="t in types" :key="t.name" class="bg-surface-base border border-outline-gray-1 rounded-xl p-4">
            <div class="text-p-base font-medium text-ink-gray-8">{{ t.abonement_name }}</div>
            <div class="text-2xl font-bold text-ink-gray-9 mt-2">\${{ t.price }}</div>
            <div class="text-p-sm text-ink-gray-5 mt-1">{{ t.total_classes }} {{ __('classes') }} · {{ t.validity_days }} {{ __('days') }}</div>
          </div>
        </div>
      </div>

      <div>
        <div class="text-lg font-semibold text-ink-gray-8 mb-4">{{ __('Student Abonements') }}</div>
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead>
              <tr class="border-b border-outline-gray-2 text-p-xs text-ink-gray-5 uppercase tracking-wider">
                <th class="pb-3 pr-4 font-medium">{{ __('Student') }}</th>
                <th class="pb-3 pr-4 font-medium">{{ __('Type') }}</th>
                <th class="pb-3 pr-4 font-medium">{{ __('Remaining') }}</th>
                <th class="pb-3 pr-4 font-medium">{{ __('Total') }}</th>
                <th class="pb-3 pr-4 font-medium">{{ __('Status') }}</th>
                <th class="pb-3 pr-4 font-medium">{{ __('End Date') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ab in abonements" :key="ab.name" class="border-b border-outline-gray-1 text-p-sm">
                <td class="py-3 pr-4 text-ink-gray-8">{{ ab.student }}</td>
                <td class="py-3 pr-4 text-ink-gray-7">{{ ab.abonement_type }}</td>
                <td class="py-3 pr-4 font-medium" :class="ab.classes_remaining > 0 ? 'text-ink-gray-8' : 'text-ink-red-5'">{{ ab.classes_remaining }}</td>
                <td class="py-3 pr-4 text-ink-gray-7">{{ ab.total_classes }}</td>
                <td class="py-3 pr-4"><Badge :label="__(ab.status)" variant="subtle" /></td>
                <td class="py-3 pr-4 text-ink-gray-7">{{ ab.end_date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import { ref, onMounted } from 'vue'

const types = ref([])
const abonements = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const crumbs = [{ label: __('LMS'), route: { name: 'LmsCourses' } }, { label: __('Abonements') }]

onMounted(async () => {
  loading.value = true
  try {
    const [t, a] = await Promise.all([
      call('crm.api.lms.get_abonement_types'),
      call('crm.api.lms.get_student_abonements'),
    ])
    types.value = t || []
    abonements.value = a || []
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading abonements'))
  } finally {
    loading.value = false
  }
})
</script>