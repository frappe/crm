<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <Button variant="outline" :label="__('Refresh')" @click="loadDashboard" :loading="loading" />
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <template v-else>
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-ink-gray-9">{{ __('Instructor Dashboard') }}</h1>
        <p class="text-p-base text-ink-gray-5 mt-1">{{ __('Today') }}: {{ today }}</p>
      </div>

      <!-- Stats row -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-surface-base border border-outline-gray-1 rounded-xl p-5">
          <div class="flex items-center gap-2 text-ink-gray-5 text-p-sm mb-2">
            <UsersIcon class="w-4 h-4" />
            <span>{{ __('Active Groups') }}</span>
          </div>
          <div class="text-3xl font-bold text-ink-gray-9">{{ dashboard.groups?.length || 0 }}</div>
        </div>
        <div class="bg-surface-base border border-outline-gray-1 rounded-xl p-5">
          <div class="flex items-center gap-2 text-ink-gray-5 text-p-sm mb-2">
            <CalendarIcon class="w-4 h-4" />
            <span>{{ __('Today Classes') }}</span>
          </div>
          <div class="text-3xl font-bold text-ink-gray-9">{{ dashboard.sessions?.length || 0 }}</div>
        </div>
        <div class="bg-surface-base border border-outline-gray-1 rounded-xl p-5">
          <div class="flex items-center gap-2 text-ink-gray-5 text-p-sm mb-2">
            <ClipboardCheckIcon class="w-4 h-4" />
            <span>{{ __('Pending Reviews') }}</span>
          </div>
          <div class="text-3xl font-bold text-ink-amber-6">{{ dashboard.pending_assignments || 0 }}</div>
        </div>
        <div class="bg-surface-base border border-outline-gray-1 rounded-xl p-5 cursor-pointer hover:shadow-md transition-shadow" @click="router.push({ name: 'LmsKnowledgeBase' })">
          <div class="flex items-center gap-2 text-ink-gray-5 text-p-sm mb-2">
            <BookOpenIcon class="w-4 h-4" />
            <span>{{ __('Knowledge Base') }}</span>
          </div>
          <div class="text-p-sm text-ink-gray-7 mt-2">{{ __('Browse lectures & materials') }}</div>
        </div>
      </div>

      <!-- Today's Schedule -->
      <div class="mb-8">
        <div class="text-lg font-semibold text-ink-gray-8 mb-4 flex items-center gap-2">
          <CalendarIcon class="w-5 h-5 text-ink-gray-5" />
          {{ __('Today Schedule') }}
        </div>
        <div v-if="dashboard.sessions?.length" class="space-y-2">
          <div
            v-for="s in dashboard.sessions"
            :key="s.name"
            class="flex items-center gap-4 p-4 border border-outline-gray-1 rounded-xl hover:bg-surface-gray-1 transition-colors"
          >
            <div class="flex-shrink-0 w-16 text-center">
              <div class="text-lg font-bold text-ink-gray-8">{{ s.start_time?.slice(0, 5) }}</div>
              <div class="text-p-xs text-ink-gray-5">{{ s.end_time?.slice(0, 5) }}</div>
            </div>
            <div class="w-px h-10 bg-outline-gray-2" />
            <div class="flex-1 min-w-0">
              <div class="text-p-sm font-medium text-ink-gray-8">{{ s.title }}</div>
              <div class="flex items-center gap-3 text-p-xs text-ink-gray-5 mt-0.5">
                <span>{{ s.group }}</span>
                <span v-if="s.room">· {{ s.room }}</span>
                <span v-if="s.topic">· {{ s.topic }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                :label="__('Journal')"
                @click="router.push({ name: 'LmsGroupJournal', params: { groupId: s.group } })"
              />
              <Button
                v-if="s.video_recording_url"
                variant="ghost"
                size="sm"
                :label="__('Recording')"
                @click="window.open(s.video_recording_url, '_blank')"
              />
              <Badge :label="__(s.status)" variant="subtle" size="sm" />
            </div>
          </div>
        </div>
        <div v-else class="text-p-sm text-ink-gray-5 py-8 text-center border border-dashed border-outline-gray-2 rounded-xl">
          <CalendarIcon class="w-8 h-8 mx-auto mb-2 text-ink-gray-4" />
          {{ __('No classes scheduled for today') }}
        </div>
      </div>

      <!-- Active Groups -->
      <div>
        <div class="text-lg font-semibold text-ink-gray-8 mb-4 flex items-center gap-2">
          <UsersIcon class="w-5 h-5 text-ink-gray-5" />
          {{ __('My Groups') }}
        </div>
        <div v-if="dashboard.groups?.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="g in dashboard.groups"
            :key="g.name"
            class="bg-surface-base border border-outline-gray-1 rounded-xl p-5 hover:shadow-md transition-shadow"
          >
            <div class="flex items-start justify-between mb-3">
              <div>
                <div class="text-p-base font-semibold text-ink-gray-8">{{ g.group_name }}</div>
                <div class="text-p-xs text-ink-gray-5 mt-0.5">{{ g.course }}</div>
              </div>
              <GraduationCapIcon class="w-5 h-5 text-ink-gray-4" />
            </div>
            <div class="flex items-center gap-4 mb-3 text-p-xs text-ink-gray-5">
              <span>{{ g.enrolled_count || 0 }} {{ __('students') }}</span>
              <span>{{ g.completed_lessons }}/{{ g.total_lessons }} {{ __('lessons') }}</span>
            </div>
            <!-- Progress bar -->
            <div class="w-full h-2 bg-surface-gray-2 rounded-full overflow-hidden mb-4">
              <div
                class="h-full bg-surface-blue-6 rounded-full transition-all duration-500"
                :style="{ width: g.progress_pct + '%' }"
              />
            </div>
            <div class="flex items-center justify-between">
              <span class="text-p-xs font-medium" :class="g.progress_pct >= 80 ? 'text-ink-green-6' : 'text-ink-gray-6'">
                {{ g.progress_pct }}% {{ __('complete') }}
              </span>
              <div class="flex gap-2">
                <Button
                  variant="solid"
                  size="sm"
                  :label="__('Journal')"
                  @click.stop="router.push({ name: 'LmsGroupJournal', params: { groupId: g.name } })"
                />
                <Button
                  variant="outline"
                  size="sm"
                  :label="__('Attendance')"
                  @click.stop="router.push({ name: 'LmsGroupAttendance', params: { groupId: g.name } })"
                />
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-p-sm text-ink-gray-5 py-8 text-center border border-dashed border-outline-gray-2 rounded-xl">
          <UsersIcon class="w-8 h-8 mx-auto mb-2 text-ink-gray-4" />
          {{ __('No groups assigned to you') }}
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import CalendarIcon from '~icons/lucide/calendar'
import UsersIcon from '~icons/lucide/users'
import BookOpenIcon from '~icons/lucide/book-open'
import ClipboardCheckIcon from '~icons/lucide/clipboard-check'
import GraduationCapIcon from '~icons/lucide/graduation-cap'
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const dashboard = reactive({ sessions: [], groups: [], pending_assignments: 0 })
const today = new Date().toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

const crumbs = [
  { label: __('LMS'), route: { name: 'LmsCourses' } },
  { label: __('Instructor Dashboard') },
]

async function loadDashboard() {
  loading.value = true
  try {
    const result = await call('crm.api.lms.get_instructor_dashboard')
    dashboard.sessions = result.sessions || []
    dashboard.groups = result.groups || []
    dashboard.pending_assignments = result.pending_assignments || 0
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading dashboard'))
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>