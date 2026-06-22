<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Mark All')" @click="batchMark" :disabled="!selectedSession" />
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <template v-else>
      <div class="flex items-center gap-4 mb-6">
        <div class="flex items-center gap-2">
          <label class="text-p-sm text-ink-gray-7">{{ __('Session') }}:</label>
          <select v-model="selectedSession" class="border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base">
            <option value="">{{ __('Select a session') }}</option>
            <option v-for="s in sessions" :key="s.name" :value="s.name">
              {{ s.date }} {{ s.start_time }} - {{ s.topic || s.title }}
            </option>
          </select>
        </div>
        <Button variant="outline" :label="__('Refresh')" @click="loadAttendance" />
      </div>

      <AttendanceGrid
        v-if="selectedSession"
        :session="selectedSession"
        :attendance="attendanceRecords"
        :students="enrolledStudents"
        @update="handleAttendanceUpdate"
      />
      <div v-else class="flex flex-col items-center justify-center h-40 text-ink-gray-5">
        <CalendarCheckIcon class="w-10 h-10 mb-2" />
        <div>{{ __('Select a session to view attendance') }}</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, LoadingIndicator, call, toast } from 'frappe-ui'
import CalendarCheckIcon from '~icons/lucide/calendar-check'
import AttendanceGrid from '@/components/LMS/AttendanceGrid.vue'
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const sessions = ref([])
const attendanceRecords = ref([])
const enrolledStudents = ref([])
const selectedSession = ref('')
const loading = ref(false)

const crumbs = [
  { label: __('LMS'), route: { name: 'LmsCourses' } },
  { label: __('Groups'), route: { name: 'LmsGroups' } },
  { label: __('Attendance') },
]

async function loadAttendance() {
  if (!selectedSession.value) return
  try {
    const [records, sessionData] = await Promise.all([
      call('crm.api.lms.get_attendance', { session: selectedSession.value }),
      call('crm.api.lms.get_academic_sessions', { group: route.params.groupId }),
    ])
    attendanceRecords.value = records || []
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading attendance'))
  }
}

async function handleAttendanceUpdate({ student, status }) {
  try {
    await call('crm.api.lms.mark_attendance', {
      data: { student, academic_session: selectedSession.value, status },
    })
    await loadAttendance()
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error saving attendance'))
  }
}

async function batchMark() {
  if (!selectedSession.value) return
  const list = enrolledStudents.value.map(s => ({
    student: s.name,
    status: 'Present',
  }))
  try {
    await call('crm.api.lms.batch_mark_attendance', {
      data: { academic_session: selectedSession.value, attendance_list: list },
    })
    toast.success(__('Attendance marked'))
    await loadAttendance()
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error batch marking'))
  }
}

onMounted(async () => {
  loading.value = true
  try {
    sessions.value = await call('crm.api.lms.get_academic_sessions', { group: route.params.groupId })
    const enrollments = await call('crm.api.lms.get_enrollments', { group: route.params.groupId })
    enrolledStudents.value = enrollments.map(e => ({ name: e.student }))
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading group'))
  } finally {
    loading.value = false
  }
})

watch(selectedSession, () => loadAttendance())
</script>