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
    <template v-else>
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-ink-gray-9">{{ __('My Learning') }}</h1>
        <p class="text-p-base text-ink-gray-5 mt-1">{{ __('Track your courses, abonements and schedule') }}</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div class="bg-surface-base border border-outline-gray-1 rounded-xl p-5">
          <div class="flex items-center gap-2 text-ink-gray-5 text-p-sm mb-2">
            <WalletIcon class="w-4 h-4" />
            <span>{{ __('Abonement Balance') }}</span>
          </div>
          <div v-if="balance" class="text-3xl font-bold" :class="balance.remaining > 0 ? 'text-ink-gray-9' : 'text-ink-red-5'">
            {{ balance.remaining }}
            <span class="text-p-base font-normal text-ink-gray-5">{{ __('classes left') }}</span>
          </div>
          <div v-else class="text-p-base text-ink-gray-5">{{ __('No active abonement') }}</div>
        </div>

        <div class="bg-surface-base border border-outline-gray-1 rounded-xl p-5">
          <div class="flex items-center gap-2 text-ink-gray-5 text-p-sm mb-2">
            <BookOpenIcon class="w-4 h-4" />
            <span>{{ __('Active Courses') }}</span>
          </div>
          <div class="text-3xl font-bold text-ink-gray-9">{{ activeCourses }}</div>
        </div>

        <div class="bg-surface-base border border-outline-gray-1 rounded-xl p-5">
          <div class="flex items-center gap-2 text-ink-gray-5 text-p-sm mb-2">
            <CalendarIcon class="w-4 h-4" />
            <span>{{ __('Next Class') }}</span>
          </div>
          <div v-if="nextSession" class="text-p-sm text-ink-gray-8">{{ nextSession.date }} {{ nextSession.start_time }}</div>
          <div v-else class="text-p-base text-ink-gray-5">{{ __('No upcoming classes') }}</div>
        </div>
      </div>

      <div class="mb-8">
        <div class="text-lg font-semibold text-ink-gray-8 mb-4">{{ __('My Courses') }}</div>
        <div v-if="enrollments.length" class="space-y-2">
          <div
            v-for="enr in enrollments"
            :key="enr.name"
            class="flex items-center justify-between p-4 border border-outline-gray-1 rounded-xl cursor-pointer hover:bg-surface-gray-1 transition-colors"
            @click="router.push({ name: 'LmsCourseDetail', params: { courseId: enr.course } })"
          >
            <div class="flex items-center gap-3">
              <BookOpenIcon class="w-5 h-5 text-ink-gray-5" />
              <div>
                <div class="text-p-sm font-medium text-ink-gray-8">{{ enr.course }}</div>
                <div class="text-p-xs text-ink-gray-5">{{ enr.group || __('No group') }}</div>
              </div>
            </div>
            <Badge :label="__(enr.status)" variant="subtle" />
          </div>
        </div>
        <div v-else class="text-p-sm text-ink-gray-5 py-6 text-center">{{ __('You are not enrolled in any courses yet') }}</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import BookOpenIcon from '~icons/lucide/book-open'
import WalletIcon from '~icons/lucide/wallet'
import CalendarIcon from '~icons/lucide/calendar'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { sessionStore } from '@/stores/session'

const router = useRouter()
const session = sessionStore()
const enrollments = ref([])
const balance = ref(null)
const nextSession = ref(null)
const loading = ref(false)
const activeCourses = computed(() => enrollments.value.filter(e => e.status === 'Active').length)
const crumbs = [{ label: __('LMS'), route: { name: 'LmsStudentDashboard' } }, { label: __('My Learning') }]

onMounted(async () => {
  loading.value = true
  try {
    const [enrResult, abResult] = await Promise.allSettled([
      call('crm.api.lms.get_enrollments'),
      call('crm.api.abonement.check_abonement_balance'),
    ])
    if (enrResult.status === 'fulfilled') enrollments.value = enrResult.value || []
    if (abResult.status === 'fulfilled') balance.value = abResult.value
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading dashboard'))
  } finally {
    loading.value = false
  }
})
</script>