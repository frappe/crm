<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <template v-else-if="course">
      <div class="flex items-start gap-6 mb-8">
        <div v-if="course.image" class="w-32 h-32 rounded-xl overflow-hidden flex-shrink-0">
          <img :src="course.image" :alt="course.title" class="w-full h-full object-cover" />
        </div>
        <div class="flex-1">
          <div class="text-2xl font-semibold text-ink-gray-9">{{ course.title }}</div>
          <div class="text-p-base text-ink-gray-5 mt-1">{{ course.category || __('Uncategorized') }}</div>
          <div class="flex items-center gap-4 mt-3">
            <Badge :label="__(course.status)" variant="subtle" />
            <span class="text-p-sm text-ink-gray-5">{{ course.lesson_count || 0 }} {{ __('lessons') }}</span>
            <span class="text-p-sm text-ink-gray-5">{{ course.student_count || 0 }} {{ __('students') }}</span>
            <span v-if="course.duration" class="text-p-sm text-ink-gray-5">{{ course.duration }}h</span>
          </div>
          <div v-if="course.price" class="text-xl font-semibold text-ink-gray-8 mt-2">\${{ course.price }}</div>
          <div v-else class="text-xl font-semibold text-ink-gray-5 mt-2">{{ __('Free') }}</div>
          <div v-if="course.description" class="mt-4 text-p-base text-ink-gray-7 leading-relaxed" v-html="course.description" />
        </div>
      </div>

      <div v-if="modules.length" class="mb-8">
        <div class="text-lg font-semibold text-ink-gray-8 mb-4">{{ __('Course Modules') }}</div>
        <div v-for="mod in modules" :key="mod.name" class="border border-outline-gray-1 rounded-xl mb-3 overflow-hidden">
          <div class="flex items-center justify-between p-4 bg-surface-gray-1 cursor-pointer" @click="toggleModule(mod.name)">
            <div class="flex items-center gap-2">
              <ChevronRightIcon class="w-4 h-4 text-ink-gray-5 transition-transform" :class="{ 'rotate-90': expandedModules[mod.name] }" />
              <span class="text-p-base font-medium text-ink-gray-8">{{ mod.module_name }}</span>
            </div>
            <span class="text-p-xs text-ink-gray-5">{{ mod.description }}</span>
          </div>
          <div v-if="expandedModules[mod.name]" class="border-t border-outline-gray-1 divide-y divide-outline-gray-1">
            <div
              v-for="lec in lectures.filter(l => l.module === mod.name)"
              :key="lec.name"
              class="flex items-center gap-3 p-3 pl-10 hover:bg-surface-gray-1 cursor-pointer transition-colors"
              @click="router.push({ name: 'LmsStudentLecture', params: { lectureId: lec.name } })"
            >
              <FileTextIcon class="w-4 h-4 text-ink-gray-5" />
              <span class="text-p-sm text-ink-gray-7 flex-1">{{ lec.title }}</span>
              <span class="text-p-xs text-ink-gray-5">{{ lec.duration ? lec.duration + 'min' : '' }}</span>
              <Badge v-if="lec.content_type !== 'Text'" :label="__(lec.content_type)" variant="subtle" size="sm" />
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import ChevronRightIcon from '~icons/lucide/chevron-right'
import FileTextIcon from '~icons/lucide/file-text'
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const course = ref(null)
const modules = ref([])
const lectures = ref([])
const loading = ref(false)
const expandedModules = reactive({})

const crumbs = [
  { label: __('LMS'), route: { name: 'LmsCourses' } },
  { label: __('Courses'), route: { name: 'LmsCourses' } },
  { label: __('Course Detail') },
]

function toggleModule(name) {
  expandedModules[name] = !expandedModules[name]
}

onMounted(async () => {
  loading.value = true
  try {
    const result = await call('crm.api.lms.get_course_detail', { course: route.params.courseId })
    course.value = result.course
    modules.value = result.modules || []
    lectures.value = result.lectures || []
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading course'))
  } finally {
    loading.value = false
  }
})
</script>