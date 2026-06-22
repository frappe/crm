<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Add Student')" @click="showCreateModal = true" />
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
              <th class="pb-3 pr-4 font-medium">{{ __('Name') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Status') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Enrolled On') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Parent') }}</th>
              <th class="pb-3 pr-4 font-medium">{{ __('Parent Phone') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="s in students"
              :key="s.name"
              class="border-b border-outline-gray-1 hover:bg-surface-gray-1 cursor-pointer transition-colors"
              @click="router.push({ name: 'LmsStudentDetail', params: { studentId: s.name } })"
            >
              <td class="py-3 pr-4">
                <div class="flex items-center gap-3">
                  <div v-if="s.image" class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0">
                    <img :src="s.image" :alt="s.student_name" class="w-full h-full object-cover" />
                  </div>
                  <div v-else class="w-8 h-8 rounded-full bg-surface-gray-2 flex items-center justify-center flex-shrink-0">
                    <UserIcon class="w-4 h-4 text-ink-gray-5" />
                  </div>
                  <span class="text-p-sm font-medium text-ink-gray-8">{{ s.student_name }}</span>
                </div>
              </td>
              <td class="py-3 pr-4"><Badge :label="__(s.status)" variant="subtle" /></td>
              <td class="py-3 pr-4 text-p-sm text-ink-gray-7">{{ s.enrolled_on }}</td>
              <td class="py-3 pr-4 text-p-sm text-ink-gray-7">{{ s.parent_name || '-' }}</td>
              <td class="py-3 pr-4 text-p-sm text-ink-gray-7">{{ s.parent_phone || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="students.length === 0" class="flex flex-col items-center justify-center h-40 text-ink-gray-5">
        <UserIcon class="w-10 h-10 mb-2" />
        <div>{{ __('No students yet') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import UserIcon from '~icons/lucide/users'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const students = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const crumbs = [{ label: __('LMS'), route: { name: 'LmsCourses' } }, { label: __('Students') }]

onMounted(async () => {
  loading.value = true
  try {
    students.value = await call('crm.api.lms.get_students')
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading students'))
  } finally {
    loading.value = false
  }
})
</script>