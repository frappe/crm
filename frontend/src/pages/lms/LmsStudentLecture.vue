<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
  </LayoutHeader>
  <div class="p-5 max-w-4xl mx-auto">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <template v-else-if="lecture">
      <div class="mb-8">
        <div class="text-2xl font-semibold text-ink-gray-9 mb-2">{{ lecture.title }}</div>
        <div class="flex items-center gap-3 text-p-sm text-ink-gray-5">
          <span>{{ lecture.course }}</span>
          <span v-if="lecture.module">· {{ lecture.module }}</span>
          <span v-if="lecture.duration">· {{ lecture.duration }} min</span>
          <Badge :label="__(lecture.content_type)" variant="subtle" size="sm" />
        </div>
      </div>

      <LectureContent v-if="lecture.content" :content="lecture.content" :video-url="lecture.video_url" />

      <div v-if="lecture.materials && lecture.materials.length" class="mt-8">
        <div class="text-lg font-semibold text-ink-gray-8 mb-4">{{ __('Materials') }}</div>
        <div class="space-y-2">
          <div v-for="mat in lecture.materials" :key="mat.file_name" class="flex items-center gap-3 p-3 border border-outline-gray-1 rounded-lg">
            <FileIcon class="w-4 h-4 text-ink-gray-5" />
            <span class="text-p-sm text-ink-gray-8 flex-1">{{ mat.file_name }}</span>
            <Badge :label="__(mat.type)" variant="subtle" size="sm" />
            <Button v-if="mat.file" variant="ghost" :label="__('Download')" @click="downloadFile(mat.file)" />
          </div>
        </div>
      </div>

      <div class="mt-8 border-t border-outline-gray-1 pt-8">
        <div class="text-lg font-semibold text-ink-gray-8 mb-4">{{ __('My Assignment') }}</div>
        <div v-if="assignment" class="mb-4">
          <div class="flex items-center gap-3 mb-4">
            <Badge :label="__(assignment.status)" variant="subtle" />
            <span v-if="assignment.score !== null" class="text-p-sm text-ink-gray-7">{{ __('Score') }}: {{ assignment.score }}/100</span>
          </div>
          <div v-if="assignment.comment" class="p-4 bg-surface-gray-1 rounded-lg text-p-sm text-ink-gray-7 mb-4" v-html="assignment.comment" />
        </div>
        <div class="border border-outline-gray-1 rounded-xl p-5">
          <div class="text-p-sm font-medium text-ink-gray-7 mb-3">{{ __('Submit your work') }}</div>
          <div class="flex items-center gap-3 mb-3">
            <TextInput v-if="fileUrl" v-model="fileUrl" :placeholder="__('File URL')" class="flex-1" />
            <input type="file" @change="handleFileUpload" class="block w-full text-p-sm text-ink-gray-5 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-p-sm file:font-medium file:bg-surface-gray-2 file:text-ink-gray-8 hover:file:bg-surface-gray-3" />
          </div>
          <div class="flex gap-2">
            <Button variant="solid" :label="__('Submit')" @click="submitAssignment" :disabled="submitting" />
            <Button v-if="assignment" variant="outline" :label="__('Update')" @click="submitAssignment" :disabled="submitting" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Badge, Button, TextInput, LoadingIndicator, call, toast } from 'frappe-ui'
import FileIcon from '~icons/lucide/file'
import LectureContent from '@/components/LMS/LectureContent.vue'
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { sessionStore } from '@/stores/session'

const route = useRoute()
const session = sessionStore()
const lecture = ref(null)
const assignment = ref(null)
const fileUrl = ref('')
const files = ref([])
const submitting = ref(false)
const loading = ref(false)

const crumbs = [
  { label: __('LMS'), route: { name: 'LmsCourses' } },
  { label: __('Lecture') },
]

async function handleFileUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    const uploaded = await call('frappe.client.upload', { file, doctype: 'Student Assignment', fieldname: 'file' })
    fileUrl.value = uploaded.file_url
  } catch (e) {
    toast.error(e.messages?.[0] || __('Upload failed'))
  }
}

function downloadFile(url) {
  window.open(url, '_blank')
}

async function submitAssignment() {
  if (!fileUrl.value) {
    toast.error(__('Please attach a file'))
    return
  }
  submitting.value = true
  try {
    const result = await call('crm.api.lms.submit_assignment', {
      data: {
        name: assignment.value?.name,
        student: session.user?.full_name,
        lecture: route.params.lectureId,
        file: fileUrl.value,
      },
    })
    toast.success(__('Assignment submitted'))
    assignment.value = await call('crm.api.lms.get_assignments', {
      student: session.user?.full_name,
      lecture: route.params.lectureId,
    })?.[0]
  } catch (e) {
    toast.error(e.messages?.[0] || __('Submission failed'))
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    lecture.value = await call('crm.api.lms.get_lecture_detail', { lecture: route.params.lectureId })
    const asg = await call('crm.api.lms.get_assignments', {
      student: session.user?.full_name,
      lecture: route.params.lectureId,
    })
    if (asg?.length) assignment.value = asg[0]
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading lecture'))
  } finally {
    loading.value = false
  }
})
</script>