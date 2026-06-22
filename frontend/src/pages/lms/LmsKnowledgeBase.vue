<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <select v-model="selectedCourse" class="border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base" @change="loadLectures">
          <option value="">{{ __('All Courses') }}</option>
          <option v-for="c in courses" :key="c.name" :value="c.name">{{ c.title }}</option>
        </select>
        <Button variant="solid" :label="__('Create Lecture')" @click="showCreateModal = true" />
      </div>
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <template v-else>
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-ink-gray-9">{{ __('Knowledge Base') }}</h1>
        <p class="text-p-base text-ink-gray-5 mt-1">{{ __('Browse lectures and materials organized by module') }}</p>
      </div>

      <div v-if="modules.length === 0 && ungrouped.length === 0" class="flex flex-col items-center justify-center h-40 text-ink-gray-5">
        <BookOpenIcon class="w-10 h-10 mb-2" />
        <div>{{ __('No lectures found') }}</div>
      </div>

      <!-- Modules -->
      <div v-for="mod in modules" :key="mod.name" class="mb-6">
        <div class="flex items-center gap-2 mb-3">
          <FolderOpenIcon class="w-5 h-5 text-ink-gray-5" />
          <span class="text-lg font-semibold text-ink-gray-8">{{ mod.module_name }}</span>
          <span class="text-p-xs text-ink-gray-5">{{ mod.lectures?.length || 0 }} {{ __('lectures') }}</span>
        </div>
        <div class="space-y-2 ml-7">
          <div
            v-for="lec in mod.lectures"
            :key="lec.name"
            class="border border-outline-gray-1 rounded-xl overflow-hidden"
          >
            <div
              class="flex items-center gap-3 p-4 cursor-pointer hover:bg-surface-gray-1 transition-colors"
              @click="toggleLecture(lec.name)"
            >
              <ChevronRightIcon
                class="w-4 h-4 text-ink-gray-5 transition-transform flex-shrink-0"
                :class="{ 'rotate-90': expandedLectures[lec.name] }"
              />
              <FileTextIcon class="w-4 h-4 text-ink-gray-5 flex-shrink-0" />
              <span class="text-p-sm font-medium text-ink-gray-8 flex-1">{{ lec.title }}</span>
              <span class="text-p-xs text-ink-gray-5">{{ lec.duration ? lec.duration + 'min' : '' }}</span>
              <Badge :label="__(lec.content_type)" variant="subtle" size="sm" />
            </div>
            <div v-if="expandedLectures[lec.name]" class="border-t border-outline-gray-1 p-4 bg-surface-gray-1">
              <!-- Video -->
              <LectureContent :content="lec.content" :video-url="lec.video_url" />
              <!-- Edit button -->
              <div class="mt-4 flex justify-end">
                <Button variant="outline" size="sm" :label="__('Edit')" @click="editLecture(lec)" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Ungrouped lectures -->
      <div v-if="ungrouped.length" class="mb-6">
        <div class="flex items-center gap-2 mb-3">
          <FileTextIcon class="w-5 h-5 text-ink-gray-5" />
          <span class="text-lg font-semibold text-ink-gray-8">{{ __('Other Lectures') }}</span>
        </div>
        <div class="space-y-2 ml-7">
          <div
            v-for="lec in ungrouped"
            :key="lec.name"
            class="border border-outline-gray-1 rounded-xl overflow-hidden"
          >
            <div
              class="flex items-center gap-3 p-4 cursor-pointer hover:bg-surface-gray-1 transition-colors"
              @click="toggleLecture(lec.name)"
            >
              <ChevronRightIcon
                class="w-4 h-4 text-ink-gray-5 transition-transform flex-shrink-0"
                :class="{ 'rotate-90': expandedLectures[lec.name] }"
              />
              <FileTextIcon class="w-4 h-4 text-ink-gray-5 flex-shrink-0" />
              <span class="text-p-sm font-medium text-ink-gray-8 flex-1">{{ lec.title }}</span>
              <Badge :label="__(lec.content_type)" variant="subtle" size="sm" />
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>

  <!-- Create Lecture Modal -->
  <Dialog v-model="showCreateModal" :title="__('Create Lecture')" class="max-w-xl">
    <template #body>
      <div class="space-y-4">
        <div>
          <label class="text-p-xs text-ink-gray-5">{{ __('Course') }}</label>
          <select v-model="createForm.course" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1" required>
            <option value="">{{ __('Select course') }}</option>
            <option v-for="c in courses" :key="c.name" :value="c.name">{{ c.title }}</option>
          </select>
        </div>
        <div>
          <label class="text-p-xs text-ink-gray-5">{{ __('Module') }}</label>
          <select v-model="createForm.module" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1">
            <option value="">{{ __('No module (ungrouped)') }}</option>
            <option v-for="m in availableModules" :key="m.name" :value="m.name">{{ m.module_name }}</option>
          </select>
        </div>
        <div>
          <label class="text-p-xs text-ink-gray-5">{{ __('Title') }} *</label>
          <TextInput v-model="createForm.title" :placeholder="__('Lecture title')" class="mt-1" />
        </div>
        <div>
          <label class="text-p-xs text-ink-gray-5">{{ __('Content') }}</label>
          <textarea v-model="createForm.content" rows="4" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1" :placeholder="__('Lecture content (markdown or HTML)')" />
        </div>
        <div>
          <label class="text-p-xs text-ink-gray-5">{{ __('Video URL') }}</label>
          <TextInput v-model="createForm.video_url" type="url" :placeholder="__('https://youtube.com/...')" class="mt-1" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-p-xs text-ink-gray-5">{{ __('Duration (min)') }}</label>
            <TextInput v-model.number="createForm.duration" type="number" class="mt-1" />
          </div>
          <div>
            <label class="text-p-xs text-ink-gray-5">{{ __('Content Type') }}</label>
            <select v-model="createForm.content_type" class="w-full border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base mt-1">
              <option value="Text">{{ __('Text') }}</option>
              <option value="Video">{{ __('Video') }}</option>
              <option value="Presentation">{{ __('Presentation') }}</option>
              <option value="Quiz">{{ __('Quiz') }}</option>
            </select>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <Button variant="outline" :label="__('Cancel')" @click="showCreateModal = false" />
      <Button variant="solid" :label="__('Create')" @click="createLecture" :loading="creating" />
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Badge, TextInput, Dialog, LoadingIndicator, call, toast } from 'frappe-ui'
import BookOpenIcon from '~icons/lucide/book-open'
import FileTextIcon from '~icons/lucide/file-text'
import FolderOpenIcon from '~icons/lucide/folder-open'
import ChevronRightIcon from '~icons/lucide/chevron-right'
import LectureContent from '@/components/LMS/LectureContent.vue'
import { ref, reactive, computed, onMounted } from 'vue'

const loading = ref(false)
const courses = ref([])
const modules = ref([])
const ungrouped = ref([])
const expandedLectures = reactive({})
const selectedCourse = ref('')
const showCreateModal = ref(false)
const creating = ref(false)
const createForm = reactive({
  course: '',
  module: '',
  title: '',
  content: '',
  video_url: '',
  duration: 30,
  content_type: 'Text',
})

const availableModules = computed(() => {
  if (!createForm.course) return []
  return modules.value.filter(m => {
    // Find modules for the selected course
    return true
  })
})

const crumbs = [
  { label: __('LMS'), route: { name: 'LmsCourses' } },
  { label: __('Instructor Dashboard'), route: { name: 'LmsInstructorDashboard' } },
  { label: __('Knowledge Base') },
]

function toggleLecture(name) {
  expandedLectures[name] = !expandedLectures[name]
}

async function loadCourses() {
  try {
    courses.value = await call('crm.api.lms.get_courses_by_instructor')
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading courses'))
  }
}

async function loadLectures() {
  loading.value = true
  try {
    const result = await call('crm.api.lms.get_lectures_by_module', {
      course: selectedCourse.value || undefined,
    })
    modules.value = result.modules || []
    ungrouped.value = result.ungrouped || []
    // Flatten all lectures into expanded state
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading lectures'))
  } finally {
    loading.value = false
  }
}

async function createLecture() {
  if (!createForm.title || !createForm.course) {
    toast.error(__('Title and Course are required'))
    return
  }
  creating.value = true
  try {
    await call('crm.api.lms.create_lecture', {
      data: {
        title: createForm.title,
        course: createForm.course,
        module: createForm.module || null,
        content: createForm.content,
        video_url: createForm.video_url,
        duration: createForm.duration,
        content_type: createForm.content_type,
      },
    })
    toast.success(__('Lecture created'))
    showCreateModal.value = false
    createForm.title = ''
    createForm.content = ''
    createForm.video_url = ''
    createForm.duration = 30
    createForm.content_type = 'Text'
    await loadLectures()
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error creating lecture'))
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await loadCourses()
  await loadLectures()
})
</script>