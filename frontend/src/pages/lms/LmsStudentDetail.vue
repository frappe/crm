<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Enroll in Course')" @click="showEnrollModal = true" />
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <template v-else-if="student">
      <div class="flex items-start gap-6 mb-8">
        <div v-if="student.image" class="w-20 h-20 rounded-full overflow-hidden flex-shrink-0">
          <img :src="student.image" :alt="student.student_name" class="w-full h-full object-cover" />
        </div>
        <div v-else class="w-20 h-20 rounded-full bg-surface-gray-2 flex items-center justify-center flex-shrink-0">
          <UserIcon class="w-8 h-8 text-ink-gray-5" />
        </div>
        <div class="flex-1">
          <div class="text-xl font-semibold text-ink-gray-9">{{ student.student_name }}</div>
          <div class="flex items-center gap-3 mt-2">
            <Badge :label="__(student.status)" variant="subtle" />
            <span class="text-p-sm text-ink-gray-5">{{ __('Enrolled') }}: {{ student.enrolled_on }}</span>
          </div>
          <div class="grid grid-cols-2 gap-x-8 gap-y-2 mt-4 text-p-sm">
            <div><span class="text-ink-gray-5">{{ __('Date of Birth') }}:</span> <span class="text-ink-gray-8">{{ student.date_of_birth || '-' }}</span></div>
            <div><span class="text-ink-gray-5">{{ __('Gender') }}:</span> <span class="text-ink-gray-8">{{ student.gender || '-' }}</span></div>
            <div><span class="text-ink-gray-5">{{ __('Parent') }}:</span> <span class="text-ink-gray-8">{{ student.parent_name || '-' }}</span></div>
            <div><span class="text-ink-gray-5">{{ __('Parent Phone') }}:</span> <span class="text-ink-gray-8">{{ student.parent_phone || '-' }}</span></div>
          </div>
        </div>
      </div>

      <AbonementBadge :student="student.name" class="mb-6" />

      <div class="mb-8">
        <div class="text-lg font-semibold text-ink-gray-8 mb-4">{{ __('Enrollments') }}</div>
        <div v-if="enrollments.length" class="space-y-2">
          <div v-for="enr in enrollments" :key="enr.name" class="flex items-center justify-between p-3 border border-outline-gray-1 rounded-lg">
            <div>
              <div class="text-p-sm font-medium text-ink-gray-8">{{ enr.course }}</div>
              <div class="text-p-xs text-ink-gray-5">{{ enr.group || __('No group') }} · {{ enr.enrollment_date }}</div>
            </div>
            <Badge :label="__(enr.status)" variant="subtle" />
          </div>
        </div>
        <div v-else class="text-p-sm text-ink-gray-5 py-4">{{ __('No enrollments') }}</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import UserIcon from '~icons/lucide/user'
import AbonementBadge from '@/components/LMS/AbonementBadge.vue'
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const student = ref(null)
const enrollments = ref([])
const loading = ref(false)
const showEnrollModal = ref(false)

const crumbs = [
  { label: __('LMS'), route: { name: 'LmsCourses' } },
  { label: __('Students'), route: { name: 'LmsStudents' } },
  { label: __('Student Detail') },
]

onMounted(async () => {
  loading.value = true
  try {
    const result = await call('crm.api.lms.get_student_detail', { student: route.params.studentId })
    student.value = result.student
    enrollments.value = result.enrollments || []
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading student'))
  } finally {
    loading.value = false
  }
})
</script>