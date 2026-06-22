<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Create Course')" @click="showCreateModal = true" />
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="course in courses"
        :key="course.name"
        class="bg-surface-base border border-outline-gray-1 rounded-xl p-4 cursor-pointer hover:shadow-md transition-shadow"
        @click="router.push({ name: 'LmsCourseDetail', params: { courseId: course.name } })"
      >
        <div class="flex items-start gap-3">
          <div v-if="course.image" class="w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
            <img :src="course.image" :alt="course.title" class="w-full h-full object-cover" />
          </div>
          <div v-else class="w-16 h-16 rounded-lg bg-surface-gray-2 flex items-center justify-center flex-shrink-0">
            <BookOpenIcon class="w-6 h-6 text-ink-gray-5" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-p-base text-ink-gray-8 font-medium truncate">{{ course.title }}</div>
            <div class="text-p-sm text-ink-gray-5 mt-0.5">{{ course.category || __('Uncategorized') }}</div>
            <div class="flex items-center gap-3 mt-2 text-p-xs text-ink-gray-5">
              <span>{{ course.lesson_count || 0 }} {{ __('lessons') }}</span>
              <span v-if="course.price">\${{ course.price }}</span>
              <span v-else>{{ __('Free') }}</span>
            </div>
          </div>
        </div>
        <div class="flex items-center justify-between mt-3 pt-3 border-t border-outline-gray-1">
          <Badge :label="__(course.status)" variant="subtle" />
          <span class="text-p-xs text-ink-gray-5">{{ course.student_count || 0 }} {{ __('students') }}</span>
        </div>
      </div>
    </div>
    <div v-if="!loading && courses.length === 0" class="flex flex-col items-center justify-center h-40 text-ink-gray-5">
      <BookOpenIcon class="w-10 h-10 mb-2" />
      <div>{{ __('No courses yet') }}</div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import BookOpenIcon from '~icons/lucide/book-open'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const courses = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const crumbs = [{ label: __('LMS'), route: { name: 'LmsCourses' } }, { label: __('Courses') }]

onMounted(async () => {
  loading.value = true
  try {
    courses.value = await call('crm.api.lms.get_courses')
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading courses'))
  } finally {
    loading.value = false
  }
})
</script>