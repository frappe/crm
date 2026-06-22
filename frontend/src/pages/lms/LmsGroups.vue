<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :crumbs="crumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Create Group')" @click="showCreateModal = true" />
    </template>
  </LayoutHeader>
  <div class="p-5">
    <div v-if="loading" class="flex items-center justify-center h-40">
      <LoadingIndicator />
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="g in groups"
        :key="g.name"
        class="bg-surface-base border border-outline-gray-1 rounded-xl p-4 cursor-pointer hover:shadow-md transition-shadow"
        @click="router.push({ name: 'LmsGroupAttendance', params: { groupId: g.name } })"
      >
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-lg bg-surface-gray-2 flex items-center justify-center">
            <UsersIcon class="w-5 h-5 text-ink-gray-5" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-p-base font-medium text-ink-gray-8 truncate">{{ g.group_name }}</div>
            <div class="text-p-xs text-ink-gray-5">{{ g.course }}</div>
          </div>
        </div>
        <div class="flex items-center justify-between text-p-xs text-ink-gray-5 pt-3 border-t border-outline-gray-1">
          <Badge :label="__(g.status)" variant="subtle" size="sm" />
          <span>{{ g.max_students ? __('Max') + ': ' + g.max_students : '' }}</span>
        </div>
      </div>
    </div>
    <div v-if="!loading && groups.length === 0" class="flex flex-col items-center justify-center h-40 text-ink-gray-5">
      <UsersIcon class="w-10 h-10 mb-2" />
      <div>{{ __('No groups yet') }}</div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Badge, LoadingIndicator, call, toast } from 'frappe-ui'
import UsersIcon from '~icons/lucide/users'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const groups = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const crumbs = [{ label: __('LMS'), route: { name: 'LmsCourses' } }, { label: __('Groups') }]

onMounted(async () => {
  loading.value = true
  try {
    groups.value = await call('crm.api.lms.get_student_groups')
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error loading groups'))
  } finally {
    loading.value = false
  }
})
</script>