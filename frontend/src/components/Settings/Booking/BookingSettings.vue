<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Booking Calendars') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Public Calendly-style booking pages: services, prices, availability and team.') }}
        </p>
      </div>
      <Button variant="solid" :label="__('New calendar')" iconLeft="plus" @click="openEditor()" />
    </div>

    <!-- personal Google Calendar connection -->
    <div
      class="mx-2 flex items-center justify-between rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
    >
      <div class="flex flex-col">
        <span class="text-p-base-medium text-ink-gray-7">
          {{ __('Your Google Calendar') }}
        </span>
        <span class="text-p-sm text-ink-gray-5">
          {{
            googleConnection.data?.connected
              ? __('Connected — your busy events block booking slots')
              : __('Connect it so your busy events block booking slots')
          }}
        </span>
      </div>
      <Button
        :variant="googleConnection.data?.connected ? 'subtle' : 'solid'"
        :label="googleConnection.data?.connected ? __('Connected') : __('Connect')"
        @click="connectGoogle"
      />
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="calendars.data?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="cal in calendars.data"
          :key="cal.name"
          class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
          @click="openEditor(cal.name)"
        >
          <Badge
            :label="cal.enabled ? __('Active') : __('Off')"
            :theme="cal.enabled ? 'green' : 'gray'"
            size="sm"
          />
          <div class="min-w-0 flex-1">
            <div class="truncate text-p-base-medium text-ink-gray-8">
              {{ cal.calendar_name }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              /book/{{ cal.route }} · {{ cal.duration }} min
              <span v-if="cal.price"> · {{ cal.price }} {{ cal.currency }}</span>
            </div>
          </div>
          <span class="shrink-0 text-p-sm text-ink-gray-5">
            {{ cal.upcoming_count }} {{ __('upcoming') }}
          </span>
          <Button
            variant="ghost"
            icon="lucide-external-link"
            @click.stop="openPublicPage(cal.route)"
          />
          <Button variant="ghost" icon="lucide-trash-2" @click.stop="removeCalendar(cal)" />
        </div>
      </div>
      <div v-else-if="!calendars.loading" class="px-2 text-p-base text-ink-gray-5">
        {{ __('No booking calendars yet. Create the first one!') }}
      </div>
    </div>
  </div>

  <!-- editor dialog -->
  <Dialog v-model="showEditor" :options="{ title: editorTitle, size: '2xl' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <FormControl v-model="form.calendar_name" type="text" :label="__('Name')" required />
          <FormControl
            v-model="form.route"
            type="text"
            :label="__('URL slug (/book/…)')"
            :placeholder="'consulenza-30'"
          />
        </div>
        <FormControl v-model="form.description" type="textarea" :rows="2" :label="__('Description')" />
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.location"
            type="text"
            :label="__('Location / meeting link')"
          />
          <FormControl
            v-model="form.timezone"
            type="text"
            :label="__('Timezone (IANA)')"
            :placeholder="'Europe/Rome'"
          />
        </div>
        <div class="grid grid-cols-3 gap-3">
          <FormControl v-model="form.duration" type="number" :label="__('Duration (min)')" />
          <FormControl v-model="form.price" type="number" :label="__('Price')" />
          <FormControl v-model="form.currency" type="text" :label="__('Currency')" />
        </div>
        <div class="grid grid-cols-4 gap-3">
          <FormControl v-model="form.buffer_before" type="number" :label="__('Buffer before')" />
          <FormControl v-model="form.buffer_after" type="number" :label="__('Buffer after')" />
          <FormControl v-model="form.min_notice_hours" type="number" :label="__('Min notice (h)')" />
          <FormControl v-model="form.max_horizon_days" type="number" :label="__('Horizon (days)')" />
        </div>
        <div class="flex flex-wrap gap-4 py-1">
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.enabled" size="sm" /> {{ __('Enabled') }}
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.show_in_menu" size="sm" /> {{ __('Show on /book page') }}
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.check_google_busy" size="sm" />
            {{ __('Block Google Calendar busy slots') }}
          </label>
        </div>

        <div>
          <div class="mb-1 text-xs text-ink-gray-5">
            {{ __('Team members (round robin)') }}
          </div>
          <div class="flex flex-wrap gap-1.5">
            <Button
              v-for="u in meta.data?.users || []"
              :key="u"
              size="sm"
              :variant="form.members.includes(u) ? 'solid' : 'outline'"
              :label="u"
              @click="toggleMember(u)"
            />
          </div>
        </div>

        <div>
          <div class="mb-1 text-xs text-ink-gray-5">{{ __('Weekly hours') }}</div>
          <div
            v-for="(row, i) in form.availability"
            :key="i"
            class="mb-2 grid grid-cols-[1fr_1fr_1fr_32px] gap-2"
          >
            <FormControl
              v-model="row.workday"
              type="select"
              :options="WEEKDAYS.map((d) => ({ label: __(d), value: d }))"
            />
            <FormControl v-model="row.start_time" type="time" />
            <FormControl v-model="row.end_time" type="time" />
            <Button variant="ghost" icon="lucide-trash-2" @click="form.availability.splice(i, 1)" />
          </div>
          <Button
            variant="ghost"
            :label="__('Add hours')"
            iconLeft="plus"
            @click="form.availability.push({ workday: 'Monday', start_time: '09:00', end_time: '18:00' })"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        @click="saveCalendar"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { createResource, Dialog, FormControl, Switch, toast } from 'frappe-ui'
import { ref, reactive, computed } from 'vue'

const WEEKDAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const calendars = createResource({
  url: 'crm.api.booking.list_calendars_admin',
  cache: 'booking-calendars-admin',
  auto: true,
})

const meta = createResource({
  url: 'crm.api.automation.get_builder_meta',
  cache: 'crm-automation-meta',
  auto: true,
})

const googleConnection = createResource({
  url: 'crm.integrations.google.api.get_status',
  cache: 'google-calendar-connection',
  auto: true,
})

function connectGoogle() {
  if (googleConnection.data?.connected) {
    toast.success(__('Google Calendar is already connected'))
    return
  }
  createResource({
    url: 'crm.integrations.google.oauth.get_login_url',
    auto: true,
    onSuccess: (data) => (window.location.href = data.login_url),
    onError: (e) =>
      toast.error(e.messages?.[0] || __('Failed to start Google authorization')),
  })
}

const showEditor = ref(false)
const saving = ref(false)
const editingName = ref(null)

const emptyForm = () => ({
  calendar_name: '',
  route: '',
  enabled: true,
  description: '',
  location: '',
  timezone: 'Europe/Rome',
  duration: 30,
  slot_interval: 0,
  buffer_before: 0,
  buffer_after: 0,
  min_notice_hours: 4,
  max_horizon_days: 30,
  price: 0,
  currency: 'EUR',
  show_in_menu: true,
  check_google_busy: true,
  members: [],
  availability: [
    { workday: 'Monday', start_time: '09:00', end_time: '18:00' },
    { workday: 'Tuesday', start_time: '09:00', end_time: '18:00' },
    { workday: 'Wednesday', start_time: '09:00', end_time: '18:00' },
    { workday: 'Thursday', start_time: '09:00', end_time: '18:00' },
    { workday: 'Friday', start_time: '09:00', end_time: '18:00' },
  ],
})

const form = reactive(emptyForm())

const editorTitle = computed(() =>
  editingName.value ? __('Edit calendar') : __('New calendar'),
)

function openEditor(name = null) {
  editingName.value = name
  Object.assign(form, emptyForm())
  if (!name) {
    showEditor.value = true
    return
  }
  createResource({
    url: 'crm.api.booking.get_calendar_admin',
    params: { name },
    auto: true,
    onSuccess: (data) => {
      Object.assign(form, data, {
        enabled: Boolean(data.enabled),
        show_in_menu: Boolean(data.show_in_menu),
        check_google_busy: Boolean(data.check_google_busy),
        availability: (data.availability || []).map((a) => ({
          workday: a.workday,
          start_time: a.start_time.slice(0, 5),
          end_time: a.end_time.slice(0, 5),
        })),
      })
      showEditor.value = true
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to load')),
  })
}

function toggleMember(u) {
  const i = form.members.indexOf(u)
  i == -1 ? form.members.push(u) : form.members.splice(i, 1)
}

function saveCalendar() {
  saving.value = true
  createResource({
    url: 'crm.api.booking.save_calendar',
    params: { name: editingName.value, calendar: { ...form } },
    auto: true,
    onSuccess: () => {
      saving.value = false
      showEditor.value = false
      toast.success(__('Calendar saved'))
      calendars.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

function removeCalendar(cal) {
  createResource({
    url: 'crm.api.booking.delete_calendar',
    params: { name: cal.name },
    auto: true,
    onSuccess: () => calendars.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
  })
}

function openPublicPage(route) {
  window.open(`/book/${route}`, '_blank')
}
</script>
