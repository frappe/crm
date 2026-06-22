<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Button variant="outline" :label="__('Attendance')" @click="router.push({ name: 'LmsGroupAttendance', params: { groupId } })" />
        <Button variant="solid" :label="__('Refresh')" @click="loadJournal" :loading="loading" />
      </div>
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <template v-else>
      <!-- Group header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-semibold text-ink-gray-9">{{ group?.group_name }}</h1>
          <p class="text-p-sm text-ink-gray-5 mt-1">{{ group?.course }} · {{ today }}</p>
        </div>
        <div class="flex items-center gap-3">
          <div v-if="session" class="text-p-sm text-ink-gray-5">
            {{ __('Session') }}: {{ session.start_time?.slice(0, 5) }} - {{ session.end_time?.slice(0, 5) }}
            <span v-if="session.topic"> · {{ session.topic }}</span>
          </div>
          <Button v-if="session" variant="outline" size="sm" :label="__('Set Recording')" @click="showRecordingModal = true" />
        </div>
      </div>

      <!-- Journal Grid -->
      <div class="overflow-x-auto border border-outline-gray-1 rounded-xl">
        <table class="w-full text-left min-w-[800px]">
          <thead>
            <tr class="bg-surface-gray-1 border-b border-outline-gray-2 text-p-xs text-ink-gray-5 uppercase tracking-wider">
              <th class="py-3 px-4 font-medium sticky left-0 bg-surface-gray-1 z-10 min-w-[180px]">{{ __('Student') }}</th>
              <th class="py-3 px-3 font-medium text-center w-28">{{ __('Attendance') }}</th>
              <th class="py-3 px-3 font-medium text-center w-20">{{ __('HW Score') }}</th>
              <th class="py-3 px-3 font-medium text-center w-36">{{ __('Codify Coins') }}</th>
              <th class="py-3 px-3 font-medium text-center w-28">{{ __('Report') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="s in students"
              :key="s.name"
              class="border-b border-outline-gray-1 hover:bg-surface-gray-1 transition-colors"
            >
              <!-- Student name -->
              <td class="py-2.5 px-4 sticky left-0 bg-surface-base">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full bg-surface-gray-2 flex items-center justify-center flex-shrink-0 overflow-hidden">
                    <img v-if="s.image" :src="s.image" :alt="s.student_name" class="w-full h-full object-cover" />
                    <UserIcon v-else class="w-4 h-4 text-ink-gray-5" />
                  </div>
                  <div>
                    <div class="text-p-sm font-medium text-ink-gray-8">{{ s.student_name }}</div>
                    <div v-if="s.parent_name" class="text-p-xs text-ink-gray-5">{{ s.parent_name }}</div>
                  </div>
                </div>
              </td>

              <!-- Attendance -->
              <td class="py-2.5 px-3 text-center">
                <select
                  v-model="s.attendance_status"
                  class="border border-outline-gray-2 rounded-lg px-2 py-1.5 text-p-xs bg-surface-base cursor-pointer w-full"
                  @change="updateAttendance(s)"
                >
                  <option value="">{{ __('Select') }}</option>
                  <option value="Present">{{ __('Present') }}</option>
                  <option value="Late">{{ __('Late') }}</option>
                  <option value="Absent">{{ __('Absent') }}</option>
                  <option value="Excused">{{ __('Excused') }}</option>
                </select>
              </td>

              <!-- HW Score -->
              <td class="py-2.5 px-3 text-center">
                <div class="flex items-center justify-center gap-1">
                  <input
                    v-model.number="s.scoreInput"
                    type="number"
                    min="0"
                    max="100"
                    class="w-14 border border-outline-gray-2 rounded-lg px-2 py-1.5 text-p-xs text-center bg-surface-base"
                    @change="updateScore(s)"
                  />
                  <span class="text-p-xs text-ink-gray-5">/100</span>
                </div>
              </td>

              <!-- Codify Coins -->
              <td class="py-2.5 px-3 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button
                    class="w-7 h-7 rounded-full bg-surface-red-1 text-ink-red-6 hover:bg-surface-red-2 flex items-center justify-center transition-colors"
                    @click="adjustCoins(s, -10)"
                  >
                    <MinusIcon class="w-3 h-3" />
                  </button>
                  <span class="text-p-sm font-bold text-ink-amber-6 min-w-[2rem] text-center">{{ s.codify_coins }}</span>
                  <button
                    class="w-7 h-7 rounded-full bg-surface-green-1 text-ink-green-6 hover:bg-surface-green-2 flex items-center justify-center transition-colors"
                    @click="adjustCoins(s, 10)"
                  >
                    <PlusIcon class="w-3 h-3" />
                  </button>
                </div>
              </td>

              <!-- Report -->
              <td class="py-2.5 px-3 text-center">
                <Button
                  variant="ghost"
                  size="sm"
                  :label="__('Report')"
                  @click="openReportModal(s)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="students.length === 0" class="flex flex-col items-center justify-center h-40 text-ink-gray-5 border border-dashed border-outline-gray-2 rounded-xl mt-4">
        <UserIcon class="w-8 h-8 mb-2" />
        <div>{{ __('No students in this group') }}</div>
      </div>
    </template>
  </div>

  <!-- Recording URL Modal -->
  <Dialog v-model="showRecordingModal" :title="__('Set Video Recording URL')">
    <template #body>
      <div class="space-y-3">
        <label class="text-p-sm text-ink-gray-7">{{ __('Recording URL') }}</label>
        <TextInput v-model="recordingUrl" type="url" :placeholder="__('https://youtube.com/...')" />
      </div>
    </template>
    <template #actions>
      <Button variant="outline" :label="__('Cancel')" @click="showRecordingModal = false" />
      <Button variant="solid" :label="__('Save')" @click="saveRecording" :loading="savingRecording" />
    </template>
  </Dialog>

  <!-- Report Modal -->
  <Dialog v-model="showReportModal" :title="__('Student Report') + ': ' + (reportStudent?.student_name || '')" class="max-w-2xl">
    <template #body>
      <div v-if="reportStudent" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-p-xs text-ink-gray-5">{{ __('Template') }}</label>
            <select v-model="reportForm.template" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1">
              <option value="General Progress">{{ __('General Progress') }}</option>
              <option value="Technical Skills">{{ __('Technical Skills') }}</option>
              <option value="Behavior">{{ __('Behavior') }}</option>
              <option value="Custom">{{ __('Custom') }}</option>
            </select>
          </div>
          <div>
            <label class="text-p-xs text-ink-gray-5">{{ __('Overall Performance') }}</label>
            <select v-model="reportForm.overall_performance" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1">
              <option value="">{{ __('Select') }}</option>
              <option value="Excellent">{{ __('Excellent') }}</option>
              <option value="Good">{{ __('Good') }}</option>
              <option value="Satisfactory">{{ __('Satisfactory') }}</option>
              <option value="Needs Improvement">{{ __('Needs Improvement') }}</option>
            </select>
          </div>
        </div>
        <div>
          <label class="text-p-xs text-ink-gray-5">{{ __('Technical Skills') }}</label>
          <textarea v-model="reportForm.technical_skills" rows="3" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1" :placeholder="__('Describe technical progress...')" />
        </div>
        <div>
          <label class="text-p-xs text-ink-gray-5">{{ __('Behavior & Engagement') }}</label>
          <textarea v-model="reportForm.behavior" rows="2" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1" :placeholder="__('Behavior notes...')" />
        </div>
        <div>
          <label class="text-p-xs text-ink-gray-5">{{ __('Recommendations') }}</label>
          <textarea v-model="reportForm.recommendations" rows="2" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1" :placeholder="__('Recommendations for growth...')" />
        </div>
        <label class="flex items-center gap-2 text-p-sm text-ink-gray-7">
          <input v-model="reportForm.is_published" type="checkbox" class="rounded border-outline-gray-2" />
          {{ __('Publish (visible to parent)') }}
        </label>
      </div>
    </template>
    <template #actions>
      <Button variant="outline" :label="__('Cancel')" @click="showReportModal = false" />
      <Button variant="solid" :label="__('Save Report')" @click="saveReport" :loading="savingReport" />
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Dialog, TextInput, Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import UserIcon from '~icons/lucide/user'
import PlusIcon from '~icons/lucide/plus'
import MinusIcon from '~icons/lucide/minus'
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const groupId = route.params.groupId

const loading = ref(false)
const students = ref([])
const session = ref(null)
const group = ref(null)
const today = new Date().toLocaleDateString('ru-RU')

// Recording modal
const showRecordingModal = ref(false)
const recordingUrl = ref('')
const savingRecording = ref(false)

// Report modal
const showReportModal = ref(false)
const reportStudent = ref(null)
const savingReport = ref(false)
const reportForm = reactive({
  template: 'General Progress',
  overall_performance: '',
  technical_skills: '',
  behavior: '',
  engagement: '',
  recommendations: '',
  is_published: false,
})

const crumbs = [
  { label: __('LMS'), route: { name: 'LmsCourses' } },
  { label: __('Instructor Dashboard'), route: { name: 'LmsInstructorDashboard' } },
  { label: __('Group Journal') },
]

async function loadJournal() {
  loading.value = true
  try {
    const result = await call('crm.api.lms.get_group_students', { group: groupId })
    students.value = (result.students || []).map(s => ({
      ...s,
      scoreInput: s.scores?.[0]?.score || null,
    }))
    session.value = result.session

    // Fetch group info
    const groups = await call('crm.api.lms.get_student_groups')
    group.value = groups.find(g => g.name === groupId) || null
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading journal'))
  } finally {
    loading.value = false
  }
}

async function updateAttendance(s) {
  if (!session.value) return
  try {
    await call('crm.api.lms.mark_attendance', {
      data: {
        student: s.name,
        academic_session: session.value.name,
        status: s.attendance_status,
      },
    })
    toast.success(`${s.student_name}: ${s.attendance_status}`)
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error saving attendance'))
    s.attendance_status = s.attendance_status === 'Present' ? 'Absent' : 'Present'
  }
}

async function updateScore(s) {
  if (!session.value || s.scoreInput === null) return
  try {
    await call('crm.api.lms.update_student_score', {
      data: {
        student: s.name,
        lecture: session.value.name,
        score: s.scoreInput,
      },
    })
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error saving score'))
  }
}

async function adjustCoins(s, delta) {
  try {
    const result = await call('crm.api.lms.update_student_coins', {
      data: { student: s.name, delta },
    })
    s.codify_coins = result.codify_coins
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error updating coins'))
  }
}

async function saveRecording() {
  if (!session.value) return
  savingRecording.value = true
  try {
    await call('crm.api.lms.update_session_recording', {
      data: { session: session.value.name, video_url: recordingUrl.value },
    })
    toast.success(__('Recording URL saved'))
    showRecordingModal.value = false
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error saving recording'))
  } finally {
    savingRecording.value = false
  }
}

function openReportModal(s) {
  reportStudent.value = s
  reportForm.template = 'General Progress'
  reportForm.overall_performance = ''
  reportForm.technical_skills = ''
  reportForm.behavior = ''
  reportForm.engagement = ''
  reportForm.recommendations = ''
  reportForm.is_published = false
  showReportModal.value = true
}

async function saveReport() {
  if (!reportStudent.value) return
  savingReport.value = true
  try {
    await call('crm.api.lms.create_student_report', {
      data: {
        student: reportStudent.value.name,
        template: reportForm.template,
        overall_performance: reportForm.overall_performance,
        technical_skills: reportForm.technical_skills,
        behavior: reportForm.behavior,
        engagement: reportForm.engagement,
        recommendations: reportForm.recommendations,
        is_published: reportForm.is_published ? 1 : 0,
      },
    })
    toast.success(__('Report saved'))
    showReportModal.value = false
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error saving report'))
  } finally {
    savingReport.value = false
  }
}

onMounted(loadJournal)
</script>