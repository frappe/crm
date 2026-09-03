<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[{ label: __('Social Planner'), route: { name: 'Social Planner' } }]"
      />
    </template>
    <template #right-header>
      <Button
        v-if="isManager()"
        variant="ghost"
        :label="__('Profiles')"
        iconLeft="settings"
        @click="openSocialSettings"
      />
      <Button variant="solid" :label="__('New post')" iconLeft="plus" @click="openComposer()" />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto px-3 py-4 sm:px-5">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <!-- connect CTA when no profiles are configured -->
      <div
        v-if="accounts.fetched && !(accounts.data || []).length"
        class="flex items-center justify-between gap-3 rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-4 py-3"
      >
        <div class="flex flex-col">
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __('No social profiles connected yet') }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{ __('Connect Facebook & Instagram to start scheduling.') }}
          </span>
        </div>
        <Button
          v-if="isManager()"
          variant="solid"
          :label="__('Connect profiles')"
          @click="openSocialSettings"
        />
      </div>

      <!-- month navigation -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
          <Button variant="ghost" icon="lucide-chevron-left" @click="shiftMonth(-1)" />
          <span class="w-44 text-center text-lg font-semibold capitalize text-ink-gray-9">
            {{ monthLabel }}
          </span>
          <Button variant="ghost" icon="lucide-chevron-right" @click="shiftMonth(1)" />
        </div>
        <div class="flex items-center gap-3">
          <div class="hidden items-center gap-3 sm:flex">
            <span
              v-for="legend in statusLegend"
              :key="legend.label"
              class="flex items-center gap-1.5 text-xs text-ink-gray-5"
            >
              <span class="size-2 rounded-full" :style="{ backgroundColor: legend.color }" />
              {{ legend.label }}
            </span>
          </div>
          <Button variant="outline" :label="__('Today')" @click="goToday" />
        </div>
      </div>

      <!-- month grid -->
      <div class="overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white shadow-sm">
        <div class="grid grid-cols-7 border-b border-outline-gray-2 bg-surface-gray-1">
          <div
            v-for="d in dayNames"
            :key="d"
            class="py-2 text-center text-xs font-medium uppercase tracking-wide text-ink-gray-5"
          >
            {{ d }}
          </div>
        </div>
        <div class="grid grid-cols-7">
          <div
            v-for="(cell, i) in cells"
            :key="cell.key"
            class="group relative flex min-h-[7rem] cursor-pointer flex-col gap-1 border-outline-gray-1 p-1.5 transition-colors hover:bg-surface-gray-1"
            :class="[
              i % 7 != 6 && 'border-r',
              i < 35 && 'border-b',
              !cell.inMonth && 'bg-surface-gray-1/60',
            ]"
            @click="openComposer(null, cell.date)"
          >
            <div class="flex items-center justify-between">
              <span
                class="flex size-6 items-center justify-center rounded-full text-xs"
                :class="
                  cell.isToday
                    ? 'bg-surface-gray-7 font-semibold text-ink-white'
                    : cell.inMonth
                      ? 'text-ink-gray-7'
                      : 'text-ink-gray-4'
                "
              >
                {{ cell.date.getDate() }}
              </span>
              <span
                class="hidden size-5 items-center justify-center rounded text-ink-gray-4 group-hover:flex"
              >
                <FeatherIcon name="plus" class="size-3.5" />
              </span>
            </div>
            <div class="flex min-w-0 flex-col gap-1">
              <button
                v-for="post in cell.posts.slice(0, 3)"
                :key="post.name"
                class="flex min-w-0 items-center gap-1.5 rounded-md border-l-2 px-1.5 py-1 text-left text-xs leading-tight"
                :class="chipClass(post.status)"
                :style="{ borderLeftColor: statusColor(post.status) }"
                @click.stop="openComposer(post)"
              >
                <span class="flex shrink-0 -space-x-1">
                  <span
                    v-for="platform in chipPlatforms(post)"
                    :key="platform"
                    class="size-2.5 rounded-full ring-1 ring-white"
                    :style="{ backgroundColor: platformColor(platform) }"
                  />
                </span>
                <span class="shrink-0 tabular-nums text-ink-gray-5">
                  {{ timeOf(post.scheduled_at) }}
                </span>
                <span class="truncate">{{ post.content }}</span>
              </button>
              <button
                v-if="cell.posts.length > 3"
                class="rounded px-1.5 py-0.5 text-left text-xs font-medium text-ink-gray-5 hover:bg-surface-gray-2"
                @click.stop="openDay(cell)"
              >
                +{{ cell.posts.length - 3 }} {{ __('more') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- drafts / pending -->
      <div v-if="unscheduled.length">
        <div class="mb-2 text-base font-semibold text-ink-gray-9">
          {{ __('Drafts & pending approval') }}
        </div>
        <div class="divide-y divide-outline-gray-1 overflow-hidden rounded-xl border border-outline-gray-2">
          <div
            v-for="post in unscheduled"
            :key="post.name"
            class="flex cursor-pointer items-center gap-3 bg-surface-white px-3 py-2.5 hover:bg-surface-gray-1"
            @click="openComposer(post)"
          >
            <Badge :label="__(post.status)" :theme="badgeTheme(post.status)" size="sm" />
            <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-8">
              {{ post.content }}
            </span>
            <span class="flex shrink-0 -space-x-1">
              <span
                v-for="platform in chipPlatforms(post)"
                :key="platform"
                class="size-3 rounded-full ring-1 ring-white"
                :style="{ backgroundColor: platformColor(platform) }"
              />
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- day overview dialog -->
  <Dialog v-model="showDay" :options="{ title: dayTitle, size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col divide-y divide-outline-gray-1">
        <div
          v-for="post in dayPosts"
          :key="post.name"
          class="flex cursor-pointer items-center gap-3 py-2.5 hover:bg-surface-gray-1"
          @click="((showDay = false), openComposer(post))"
        >
          <span class="w-12 shrink-0 tabular-nums text-sm text-ink-gray-5">
            {{ timeOf(post.scheduled_at) }}
          </span>
          <span class="flex shrink-0 -space-x-1">
            <span
              v-for="platform in chipPlatforms(post)"
              :key="platform"
              class="size-3 rounded-full ring-1 ring-white"
              :style="{ backgroundColor: platformColor(platform) }"
            />
          </span>
          <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-8">{{ post.content }}</span>
          <Badge :label="__(post.status)" :theme="badgeTheme(post.status)" size="sm" />
        </div>
      </div>
    </template>
  </Dialog>

  <!-- composer dialog -->
  <Dialog v-model="showComposer" :options="{ title: composerTitle, size: 'xl' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-xs font-medium text-ink-gray-5">{{ __('Profiles') }}</div>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="account in accounts.data || []"
              :key="account.name"
              class="flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-sm transition-colors"
              :class="
                isSelected(account.name)
                  ? 'border-outline-gray-4 bg-surface-gray-7 text-ink-white'
                  : 'border-outline-gray-2 text-ink-gray-7 hover:bg-surface-gray-1'
              "
              @click="toggleAccount(account.name)"
            >
              <span
                class="size-2.5 rounded-full"
                :style="{ backgroundColor: platformColor(account.platform) }"
              />
              {{ account.account_name }}
            </button>
          </div>
          <div
            v-if="accounts.fetched && !(accounts.data || []).length"
            class="flex items-center gap-2 text-sm text-ink-gray-5"
          >
            {{ __('No profiles connected.') }}
            <Button
              v-if="isManager()"
              size="sm"
              :label="__('Connect profiles')"
              @click="openSocialSettings"
            />
          </div>
        </div>

        <div>
          <FormControl
            v-model="form.content"
            type="textarea"
            :label="__('Content')"
            :rows="5"
            :placeholder="__('What do you want to share?')"
          />
          <div class="mt-1 text-right text-xs text-ink-gray-4">
            {{ form.content.length }} {{ __('characters') }}
          </div>
        </div>

        <div class="flex items-center gap-3">
          <FileUploader
            :fileTypes="['image/*', 'video/*']"
            @success="(file) => (form.media = file.file_url)"
          >
            <template #default="{ openFileSelector }">
              <Button
                variant="outline"
                :label="form.media ? __('Replace media') : __('Add media')"
                iconLeft="lucide-image"
                @click="openFileSelector()"
              />
            </template>
          </FileUploader>
          <template v-if="form.media">
            <img
              v-if="!isVideo(form.media)"
              :src="form.media"
              class="h-10 w-10 rounded-md object-cover"
            />
            <a :href="form.media" target="_blank" class="truncate text-sm text-ink-gray-5 underline">
              {{ form.media.split('/').pop() }}
            </a>
            <Button variant="ghost" icon="lucide-x" @click="form.media = ''" />
          </template>
        </div>

        <details v-if="form.targets.length" class="rounded-md border border-outline-gray-1 p-2">
          <summary class="cursor-pointer text-sm text-ink-gray-6">
            {{ __('Customize per profile (optional)') }}
          </summary>
          <div class="mt-2 flex flex-col gap-2">
            <FormControl
              v-for="t in form.targets"
              :key="t.account"
              v-model="t.override_content"
              type="textarea"
              :rows="2"
              :label="t.account"
              :placeholder="__('Leave empty to use the main content')"
            />
          </div>
        </details>

        <div class="grid grid-cols-2 gap-3">
          <FormControl v-model="form.scheduled_at" type="datetime-local" :label="__('Schedule at')" />
          <FormControl
            v-model="form.recurrence"
            type="select"
            :label="__('Repeat')"
            :options="['None', 'Daily', 'Weekly', 'Monthly'].map((r) => ({ label: __(r), value: r }))"
          />
        </div>

        <div v-if="editingStatus" class="text-xs text-ink-gray-5">
          {{ __('Status') }}: {{ __(editingStatus) }}
          <template v-if="targetErrors.length">
            <div v-for="err in targetErrors" :key="err" class="mt-1 text-ink-red-4">{{ err }}</div>
          </template>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex w-full flex-wrap justify-between gap-2">
        <div class="flex gap-2">
          <Button
            v-if="editingName && editingStatus != 'Published'"
            variant="ghost"
            theme="red"
            :label="__('Cancel post')"
            @click="cancelPost"
          />
        </div>
        <div class="flex gap-2">
          <Button :label="__('Save draft')" @click="save('Draft')" />
          <Button
            v-if="!isManager()"
            variant="solid"
            :label="__('Request approval')"
            @click="save('Pending Approval')"
          />
          <template v-else>
            <Button
              v-if="editingStatus == 'Pending Approval'"
              variant="subtle"
              :label="__('Approve')"
              @click="save('Scheduled')"
            />
            <Button variant="solid" :label="__('Schedule')" @click="save('Scheduled')" />
            <Button variant="solid" theme="green" :label="__('Publish now')" @click="publishNow" />
          </template>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'
import { platformColor } from '@/utils/social'
import {
  createResource,
  Breadcrumbs,
  Dialog,
  FormControl,
  FeatherIcon,
  FileUploader,
  toast,
} from 'frappe-ui'
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'

const { isManager } = usersStore()
const { $socket } = globalStore()

const current = ref(startOfMonth(new Date()))

const dayNames = [
  __('Mon'),
  __('Tue'),
  __('Wed'),
  __('Thu'),
  __('Fri'),
  __('Sat'),
  __('Sun'),
]

const STATUS_COLORS = {
  Scheduled: '#3b82f6',
  'Pending Approval': '#f59e0b',
  Published: '#22c55e',
  Failed: '#ef4444',
  Draft: '#9ca3af',
  Cancelled: '#d1d5db',
}

const statusLegend = computed(() => [
  { label: __('Scheduled'), color: STATUS_COLORS.Scheduled },
  { label: __('Published'), color: STATUS_COLORS.Published },
  { label: __('Pending'), color: STATUS_COLORS['Pending Approval'] },
  { label: __('Failed'), color: STATUS_COLORS.Failed },
])

function statusColor(status) {
  return STATUS_COLORS[status] || STATUS_COLORS.Draft
}

function startOfMonth(d) {
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

const monthLabel = computed(() =>
  current.value.toLocaleDateString(undefined, { month: 'long', year: 'numeric' }),
)

const rangeStart = computed(() => {
  const first = new Date(current.value)
  const shift = (first.getDay() + 6) % 7
  first.setDate(first.getDate() - shift)
  return first
})

const cells = computed(() => {
  const out = []
  const today = new Date()
  const byDay = {}
  for (const post of posts.data || []) {
    if (!post.scheduled_at) continue
    const key = post.scheduled_at.slice(0, 10)
    ;(byDay[key] = byDay[key] || []).push(post)
  }
  for (let i = 0; i < 42; i++) {
    const date = new Date(rangeStart.value)
    date.setDate(date.getDate() + i)
    const key = toDateStr(date)
    out.push({
      key,
      date,
      inMonth: date.getMonth() == current.value.getMonth(),
      isToday: toDateStr(today) == key,
      posts: byDay[key] || [],
    })
  }
  return out
})

function toDateStr(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function timeOf(dt) {
  return dt ? dt.slice(11, 16) : ''
}

function isVideo(url) {
  return /\.(mp4|mov|m4v|webm)(\?|$)/i.test(url || '')
}

const posts = createResource({
  url: 'crm.api.social.get_posts',
  makeParams: () => {
    const start = toDateStr(rangeStart.value) + ' 00:00:00'
    const endDate = new Date(rangeStart.value)
    endDate.setDate(endDate.getDate() + 42)
    return { start, end: toDateStr(endDate) + ' 23:59:59' }
  },
  auto: true,
})

const accounts = createResource({
  url: 'crm.api.social.get_accounts',
  cache: 'crm-social-accounts',
  auto: true,
})

const accountPlatform = computed(() => {
  const map = {}
  for (const a of accounts.data || []) map[a.name] = a.platform
  return map
})

function chipPlatforms(post) {
  const platforms = (post.targets || []).map(
    (t) => t.platform || accountPlatform.value[t.account],
  )
  return [...new Set(platforms.filter(Boolean))].slice(0, 4)
}

const unscheduled = computed(() =>
  (posts.data || []).filter(
    (p) => !p.scheduled_at && ['Draft', 'Pending Approval'].includes(p.status),
  ),
)

function shiftMonth(delta) {
  current.value = new Date(current.value.getFullYear(), current.value.getMonth() + delta, 1)
  posts.reload()
}

function goToday() {
  current.value = startOfMonth(new Date())
  posts.reload()
}

function openSocialSettings() {
  showSettings.value = true
  activeSettingsPage.value = 'Social Planner'
}

function chipClass(status) {
  return (
    {
      Scheduled: 'bg-surface-gray-1 text-ink-gray-8 hover:bg-surface-gray-2',
      'Pending Approval': 'bg-surface-amber-1 text-ink-amber-3 hover:bg-surface-amber-2',
      Published: 'bg-surface-green-1 text-ink-green-4 hover:bg-surface-green-2',
      Failed: 'bg-surface-red-1 text-ink-red-4 hover:bg-surface-red-2',
      Draft:
        'bg-surface-white text-ink-gray-5 border border-dashed border-outline-gray-2 hover:bg-surface-gray-1',
      Cancelled: 'bg-surface-gray-1 text-ink-gray-4 line-through',
    }[status] || 'bg-surface-gray-1'
  )
}

function badgeTheme(status) {
  return (
    {
      Draft: 'gray',
      'Pending Approval': 'orange',
      Scheduled: 'blue',
      Published: 'green',
      Failed: 'red',
      Cancelled: 'gray',
    }[status] || 'gray'
  )
}

// --- day overview ---

const showDay = ref(false)
const dayTitle = ref('')
const dayPosts = ref([])

function openDay(cell) {
  dayTitle.value = cell.date.toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
  dayPosts.value = cell.posts
  showDay.value = true
}

// --- composer ---

const showComposer = ref(false)
const editingName = ref(null)
const editingStatus = ref('')
const editingTargets = ref([])
const form = reactive({
  content: '',
  media: '',
  scheduled_at: '',
  recurrence: 'None',
  targets: [],
})

const composerTitle = computed(() =>
  editingName.value ? __('Edit post') : __('New post'),
)

const targetErrors = computed(() =>
  editingTargets.value
    .filter((t) => t.status == 'Failed' && t.error)
    .map((t) => `${t.platform || t.account}: ${t.error}`),
)

function openComposer(post = null, date = null) {
  editingName.value = post?.name || null
  editingStatus.value = post?.status || ''
  editingTargets.value = post?.targets || []
  form.content = post?.content || ''
  form.media = post?.media || ''
  form.recurrence = post?.recurrence || 'None'
  form.scheduled_at = post?.scheduled_at
    ? post.scheduled_at.slice(0, 16).replace(' ', 'T')
    : date
      ? toDateStr(date) + 'T09:00'
      : ''
  form.targets = (post?.targets || []).map((t) => ({
    account: t.account,
    override_content: t.override_content || '',
  }))
  showComposer.value = true
}

function isSelected(account) {
  return form.targets.some((t) => t.account == account)
}

function toggleAccount(account) {
  const i = form.targets.findIndex((t) => t.account == account)
  i == -1 ? form.targets.push({ account, override_content: '' }) : form.targets.splice(i, 1)
}

function payload(status) {
  return {
    name: editingName.value,
    post: {
      status,
      content: form.content,
      media: form.media,
      recurrence: form.recurrence,
      scheduled_at: form.scheduled_at ? form.scheduled_at.replace('T', ' ') + ':00' : null,
      targets: form.targets,
    },
  }
}

function save(status) {
  createResource({
    url: 'crm.api.social.save_post',
    params: payload(status),
    auto: true,
    onSuccess: () => {
      showComposer.value = false
      toast.success(__('Post saved'))
      posts.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to save')),
  })
}

function publishNow() {
  createResource({
    url: 'crm.api.social.save_post',
    params: payload('Scheduled'),
    auto: true,
    onSuccess: (data) => {
      createResource({
        url: 'crm.api.social.publish_now',
        params: { name: data.name },
        auto: true,
        onSuccess: () => {
          showComposer.value = false
          toast.success(__('Publishing…'))
          posts.reload()
        },
        onError: (e) => toast.error(e.messages?.[0] || __('Failed to publish')),
      })
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to save')),
  })
}

function cancelPost() {
  createResource({
    url: 'crm.api.social.cancel_post',
    params: { name: editingName.value },
    auto: true,
    onSuccess: () => {
      showComposer.value = false
      posts.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to cancel')),
  })
}

function onRealtime() {
  posts.reload()
}

onMounted(() => $socket.on('crm_social_post', onRealtime))
onBeforeUnmount(() => $socket.off('crm_social_post', onRealtime))
</script>
