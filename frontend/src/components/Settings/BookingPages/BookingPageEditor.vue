<template>
  <div class="flex h-full flex-col text-ink-gray-8">
    <div class="flex items-center justify-between px-6 pt-8 pb-4">
      <div class="flex min-w-0 items-center gap-2">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="doc?.title || __('Booking Pages')"
          size="md"
          class="-ml-4 !max-w-96 !justify-start !pr-0 text-lg-semibold text-ink-gray-7 hover:bg-transparent hover:opacity-70 focus:bg-transparent focus:ring-0"
          @click="goBack"
        />
        <Badge
          v-if="unsaved"
          variant="subtle"
          theme="amber"
          size="sm"
          :label="__('Not Saved')"
        />
      </div>
      <div v-if="doc" class="flex items-center gap-4">
        <div class="flex h-7 items-center gap-2">
          <Switch
            size="sm"
            :model-value="Boolean(doc.enabled)"
            @update:model-value="(v: boolean) => set('enabled', v ? 1 : 0)"
          />
          <span class="text-sm text-ink-gray-7">{{ __('Live') }}</span>
        </div>
        <Button :label="__('Preview')" @click="openPage">
          <template #prefix><LucideEye class="h-4 w-4" /></template>
        </Button>
        <Button
          variant="solid"
          :label="__('Save')"
          :disabled="!unsaved || hoursErrors.size > 0"
          :loading="saving"
          @click="save"
        />
      </div>
    </div>

    <div v-if="!doc" class="mt-12 flex justify-center">
      <LoadingIndicator class="w-4" />
    </div>
    <div v-else class="bp-tabs flex-1 overflow-y-auto px-6 pb-8">
      <Tabs v-model="activeTab" as="div" :tabs="tabs">
        <template #tab-panel="{ tab }">
          <!-- SETUP TAB -->
          <div v-if="tab.value === 'setup'" class="pt-5">
            <ErrorMessage v-if="error" class="mb-4" :message="error" />

            <!-- Details -->
            <section class="flex flex-col gap-4">
              <div class="grid grid-cols-2 gap-4">
                <FormControl
                  :model-value="doc.title"
                  type="text"
                  :label="__('Title')"
                  @update:model-value="(v: string) => set('title', v)"
                />
                <div>
                  <div class="mb-1.5 text-sm text-ink-gray-5">
                    {{ __('Route') }}
                  </div>
                  <div
                    class="flex h-7 items-center rounded-4 border border-transparent bg-surface-gray-2 px-2.5 text-base focus-within:border-outline-gray-4 focus-within:bg-surface-base"
                  >
                    <span class="shrink-0 text-ink-gray-4">{{
                      ROUTE_PREFIX
                    }}</span>
                    <input
                      :value="doc.route"
                      class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 focus:outline-none focus:ring-0"
                      @input="
                        set('route', ($event.target as HTMLInputElement).value)
                      "
                      @blur="set('route', slugify(doc.route))"
                    />
                  </div>
                </div>
                <FormControl
                  :model-value="String(doc.duration)"
                  type="select"
                  :label="__('Duration')"
                  :options="durationOptions"
                  @update:model-value="
                    (v: string) => set('duration', Number(v))
                  "
                />
                <FormControl
                  :model-value="doc.location_type"
                  type="select"
                  :label="__('Location')"
                  :options="locationOptions"
                  @update:model-value="(v: string) => set('location_type', v)"
                />
                <FormControl
                  v-if="
                    ['In person', 'Custom link'].includes(doc.location_type)
                  "
                  class="col-span-2"
                  :model-value="doc.location"
                  type="text"
                  :label="
                    doc.location_type === 'In person'
                      ? __('Address')
                      : __('Link')
                  "
                  @update:model-value="(v: string) => set('location', v)"
                />
                <FormControl
                  :model-value="
                    doc.document_type === 'CRM Deal' ? __('Deal') : __('Lead')
                  "
                  type="text"
                  :label="__('Each booking creates a')"
                  :description="__('Set when the page was created')"
                  disabled
                />
                <div
                  v-if="doc.location_type === 'Google Meet'"
                  class="col-span-2 text-p-sm text-ink-gray-5"
                >
                  {{
                    __(
                      "Meet links come from each host's Google Calendar. A host without one is asked to send the guest a link.",
                    )
                  }}
                </div>
              </div>
              <FormControl
                :model-value="doc.description"
                type="textarea"
                :label="__('Description')"
                :placeholder="__('What the meeting is for, shown on the page')"
                @update:model-value="(v: string) => set('description', v)"
              />
            </section>

            <!-- Hosts: same picker and chips as assignment rule assignees -->
            <section class="mt-8">
              <div class="flex items-center justify-between gap-2">
                <SectionTitle
                  class="!mb-0"
                  :title="__('Hosts')"
                  :description="
                    __(
                      'With more than one host, each booking goes to a free host in turn.',
                    )
                  "
                />
                <AssigneeSearch
                  :label="__('Add Host')"
                  @add-assignee="dirty = true"
                />
              </div>
              <div class="mt-4 flex flex-wrap gap-2">
                <div
                  v-for="host in doc.hosts"
                  :key="String(host.user)"
                  class="flex w-max select-none items-center gap-2 rounded-5 bg-surface-gray-2 p-1 px-2 text-sm"
                >
                  <UserAvatar :user="String(host.user)" size="sm" />
                  <div class="text-ink-gray-7">
                    {{ getUser(String(host.user))?.full_name || host.user }}
                  </div>
                  <Button
                    variant="ghost"
                    icon="lucide-x"
                    @click="removeHost(host)"
                  />
                </div>
              </div>
              <ErrorMessage
                v-if="!doc.hosts.length"
                class="mt-2"
                :message="__('Add at least one host')"
              />
              <!-- Google Calendar: the CRM has no connect screen yet, so point to the desk -->
              <div
                v-if="googleNote"
                class="mt-4 flex items-start justify-between gap-4 rounded-6 border border-outline-gray-2 p-3"
              >
                <div class="flex gap-2.5">
                  <LucideCalendarSync
                    class="mt-0.5 size-4 shrink-0 text-ink-gray-5"
                  />
                  <div class="flex flex-col gap-1 text-p-sm text-ink-gray-6">
                    <span>{{ googleNote }}</span>
                    <span v-if="othersUnconnected.length">
                      {{
                        __(
                          'Not connected yet: {0}. They each connect their own calendar by opening this page.',
                          [othersUnconnected.join(', ')],
                        )
                      }}
                    </span>
                  </div>
                </div>
                <Button
                  v-if="googleAction"
                  class="shrink-0"
                  :label="googleAction.label"
                  :href="googleAction.href"
                  iconRight="lucide-external-link"
                />
              </div>
            </section>

            <!-- Weekly hours -->
            <section class="mt-8">
              <SectionTitle
                :title="__('Weekly hours')"
                :description="
                  __(
                    'When people can book. Busy times on the host\'s calendar are left out.',
                  )
                "
              />
              <div class="flex flex-col">
                <div
                  v-for="day in WEEKDAYS"
                  :key="day"
                  class="flex items-start gap-4 border-b border-outline-gray-1 py-2.5 last:border-0"
                >
                  <div class="flex h-7 w-36 shrink-0 items-center gap-2.5">
                    <Switch
                      size="sm"
                      :model-value="hoursFor(day).length > 0"
                      @update:model-value="(on: boolean) => toggleDay(day, on)"
                    />
                    <span
                      class="text-base"
                      :class="
                        hoursFor(day).length
                          ? 'text-ink-gray-8'
                          : 'text-ink-gray-5'
                      "
                    >
                      {{ __(day) }}
                    </span>
                  </div>
                  <div
                    v-if="!hoursFor(day).length"
                    class="flex h-7 items-center text-base text-ink-gray-4"
                  >
                    {{ __('Unavailable') }}
                  </div>
                  <div v-else class="flex flex-col gap-2">
                    <template
                      v-for="(row, i) in hoursFor(day)"
                      :key="row.name || row._key"
                    >
                      <div class="flex items-center gap-2">
                        <TimePicker
                          class="w-28"
                          :interval="15"
                          format="h:mm a"
                          :model-value="hhmm(row.start_time)"
                          @update:model-value="
                            (v: string) => setTime(row, 'start_time', v)
                          "
                        />
                        <span class="text-ink-gray-4">–</span>
                        <TimePicker
                          class="w-28"
                          :interval="15"
                          format="h:mm a"
                          :options="endTimeOptions(row)"
                          :model-value="hhmm(row.end_time)"
                          @update:model-value="
                            (v: string) => setTime(row, 'end_time', v)
                          "
                        />
                        <Button
                          variant="ghost"
                          icon="lucide-x"
                          :tooltip="__('Remove')"
                          @click="removeHoursRow(row)"
                        />
                        <template v-if="i === 0">
                          <Button
                            variant="ghost"
                            icon="lucide-plus"
                            :tooltip="__('Add hours')"
                            @click="addHours(day)"
                          />
                          <Popover side="bottom" align="end" bare>
                            <template #trigger>
                              <Button
                                variant="ghost"
                                icon="lucide-copy"
                                :tooltip="__('Copy times to…')"
                                @click="copyTargets = []"
                              />
                            </template>
                            <template #default="{ close }">
                              <div
                                class="mt-1 w-52 rounded-6 bg-surface-base p-1.5 shadow-2xl"
                              >
                                <div
                                  class="px-2 pb-1.5 pt-1 text-sm text-ink-gray-5"
                                >
                                  {{ __('Copy times to') }}
                                </div>
                                <Checkbox
                                  v-for="target in WEEKDAYS"
                                  :key="target"
                                  padded
                                  :label="__(target)"
                                  :disabled="target === day"
                                  :model-value="
                                    target === day ||
                                    copyTargets.includes(target)
                                  "
                                  @update:model-value="
                                    (on: boolean) =>
                                      toggleCopyTarget(target, on)
                                  "
                                />
                                <Button
                                  class="mt-1.5 w-full"
                                  variant="solid"
                                  :label="__('Apply')"
                                  :disabled="!copyTargets.length"
                                  @click="(copyTimes(day), close())"
                                />
                              </div>
                            </template>
                          </Popover>
                        </template>
                      </div>
                      <ErrorMessage
                        v-if="hoursErrors.get(row)"
                        class="-mt-1"
                        :message="hoursErrors.get(row)"
                      />
                    </template>
                  </div>
                </div>
              </div>
              <div class="mt-4 grid grid-cols-2 gap-4">
                <FormControl
                  :model-value="doc.timezone"
                  type="select"
                  :label="__('Timezone')"
                  :options="timezoneOptions"
                  @update:model-value="(v: string) => set('timezone', v)"
                />
                <div>
                  <div class="mb-1.5 text-sm text-ink-gray-5">
                    {{ __('Holidays') }}
                  </div>
                  <Link
                    doctype="CRM Holiday List"
                    :model-value="doc.holiday_list"
                    :placeholder="__('None')"
                    @update:model-value="(v: string) => set('holiday_list', v)"
                  />
                </div>
              </div>
            </section>

            <!-- Limits -->
            <section class="mt-8">
              <SectionTitle :title="__('Limits')" />
              <div class="grid grid-cols-2 gap-4">
                <FormControl
                  :model-value="doc.min_notice"
                  type="number"
                  min="0"
                  :label="__('Minimum notice (hours)')"
                  @update:model-value="
                    (v: string) => set('min_notice', Number(v))
                  "
                />
                <FormControl
                  :model-value="doc.max_days_ahead"
                  type="number"
                  min="1"
                  :label="__('Bookable days ahead')"
                  @update:model-value="
                    (v: string) => set('max_days_ahead', Number(v))
                  "
                />
                <FormControl
                  :model-value="doc.buffer"
                  type="number"
                  min="0"
                  :label="__('Buffer between meetings (minutes)')"
                  @update:model-value="(v: string) => set('buffer', Number(v))"
                />
                <FormControl
                  :model-value="String(doc.slot_interval || 0)"
                  type="select"
                  :label="__('Start times')"
                  :options="intervalOptions"
                  @update:model-value="
                    (v: string) => set('slot_interval', Number(v))
                  "
                />
              </div>
            </section>

            <!-- Form: the page's own web form, in the Forms field editor -->
            <section class="mt-8">
              <SectionTitle
                :title="__('Form')"
                :description="
                  __(
                    'What people fill in after picking a time. Answers go to the {0}.',
                    [recordLabel],
                  )
                "
              />
              <FormBuilderPanel
                v-if="doc.web_form"
                ref="formBuilder"
                :name="doc.web_form"
                embedded
                :locked-fields="['email']"
              />
            </section>

            <!-- After booking -->
            <section class="mt-8">
              <SectionTitle :title="__('After booking')" />
              <div class="flex flex-col gap-4">
                <div class="flex items-center justify-between gap-4">
                  <div>
                    <div class="text-p-base-medium text-ink-gray-7">
                      {{ __('Create a {0} for new people', [recordLabel]) }}
                    </div>
                    <div class="text-p-sm text-ink-gray-5">
                      {{
                        __(
                          'Bookings from someone already in the CRM link to their lead or deal. Otherwise a {0} is created and assigned to the host.',
                          [recordLabel],
                        )
                      }}
                    </div>
                  </div>
                  <Switch
                    size="sm"
                    :model-value="Boolean(doc.create_lead)"
                    @update:model-value="
                      (v: boolean) => set('create_lead', v ? 1 : 0)
                    "
                  />
                </div>
                <div v-if="doc.create_lead" class="w-1/2">
                  <div class="mb-1.5 text-sm text-ink-gray-5">
                    {{ __('Source') }}
                  </div>
                  <Link
                    doctype="CRM Lead Source"
                    :model-value="doc.lead_source"
                    :placeholder="__('None')"
                    @update:model-value="(v: string) => set('lead_source', v)"
                  />
                </div>
                <FormControl
                  :model-value="doc.event_title"
                  type="text"
                  :label="__('Meeting title')"
                  :placeholder="__('{page} ({guest})')"
                  :description="
                    __(
                      'How the meeting is named on the calendar. Use {guest}, {host}, {page} or a form field like {organization_name}.',
                    )
                  "
                  @update:model-value="(v: string) => set('event_title', v)"
                />
                <FormControl
                  :model-value="doc.confirmation_message"
                  type="textarea"
                  :label="__('Confirmation message')"
                  :placeholder="
                    __(
                      'Shown after someone books, and added to their confirmation email',
                    )
                  "
                  @update:model-value="
                    (v: string) => set('confirmation_message', v)
                  "
                />
                <FormControl
                  :model-value="doc.guest_reminder || 'No reminder'"
                  type="select"
                  :label="__('Remind guest')"
                  :options="reminderOptions"
                  :description="
                    __(
                      'An email before the meeting, with links to reschedule or cancel.',
                    )
                  "
                  @update:model-value="(v: string) => set('guest_reminder', v)"
                />
              </div>
            </section>
          </div>
          <!-- SHARE TAB -->
          <div v-else class="flex flex-col pt-5">
            <p v-if="!doc.enabled" class="mb-5 text-p-sm text-ink-gray-5">
              {{
                __(
                  'This page isn’t live yet. Turn on Live to make the link and embeds work.',
                )
              }}
            </p>

            <div>
              <div class="flex flex-col gap-1">
                <span class="text-lg-semibold text-ink-gray-8">{{
                  __('Link')
                }}</span>
                <span class="text-p-sm text-ink-gray-6">{{
                  __('Send people straight to the booking page.')
                }}</span>
              </div>
              <div class="mt-3.5 flex items-center gap-2">
                <TextInput
                  class="flex-1"
                  size="sm"
                  readonly
                  :model-value="publicUrl"
                >
                  <template #suffix>
                    <button
                      class="flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
                      :title="__('Copy link')"
                      @click="copyToClipboard(publicUrl)"
                    >
                      <LucideCopy class="h-4 w-4" />
                    </button>
                  </template>
                </TextInput>
                <a :href="publicUrl" target="_blank">
                  <Button :label="__('Open')">
                    <template #prefix
                      ><LucideExternalLink class="h-4 w-4"
                    /></template>
                  </Button>
                </a>
              </div>
            </div>

            <hr class="my-8 border-outline-gray-2" />

            <div>
              <div class="flex flex-col gap-1">
                <span class="text-lg-semibold text-ink-gray-8">{{
                  __('Embed')
                }}</span>
                <span class="text-p-sm text-ink-gray-6">{{
                  __('Put the booking calendar on your own website.')
                }}</span>
              </div>
              <div class="relative mt-3.5">
                <textarea
                  readonly
                  rows="8"
                  class="w-full resize-none rounded-5 border border-outline-gray-2 bg-surface-gray-1 py-2 pl-3 pr-10 font-mono text-xs text-ink-gray-7 focus:border-outline-gray-4 focus:outline-none focus:ring-0 focus-visible:outline-none"
                  :value="iframeSnippet"
                />
                <button
                  class="absolute right-2 top-2 flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
                  :title="__('Copy')"
                  @click="copyToClipboard(iframeSnippet)"
                >
                  <LucideCopy class="h-4 w-4" />
                </button>
              </div>
            </div>

            <hr class="my-8 border-outline-gray-2" />

            <div>
              <div class="flex flex-col gap-1">
                <span class="text-lg-semibold text-ink-gray-8">{{
                  __('Allowed domains')
                }}</span>
                <span class="text-p-sm text-ink-gray-6">
                  {{
                    __(
                      'Sites where this page may be embedded, one per line. Browsers block the iframe on any site not listed here.',
                    )
                  }}
                </span>
              </div>
              <textarea
                :value="doc.allowed_embedding_domains"
                rows="3"
                spellcheck="false"
                placeholder="https://www.example.com"
                class="mt-3.5 w-full resize-none rounded-5 border border-outline-gray-2 px-3 py-2 font-mono text-xs text-ink-gray-8 focus:border-outline-gray-4 focus:outline-none focus:ring-0 focus-visible:outline-none"
                @input="
                  set(
                    'allowed_embedding_domains',
                    ($event.target as HTMLTextAreaElement).value,
                  )
                "
              />
              <p
                v-if="invalidEmbeddingDomains.length"
                class="mt-1.5 text-xs text-ink-red-5"
              >
                {{
                  __('Not a valid domain and will be ignored: {0}', [
                    invalidEmbeddingDomains.join(', '),
                  ])
                }}
              </p>
              <p
                v-else-if="!embeddingDomains.length"
                class="mt-1.5 text-xs text-ink-gray-5"
              >
                {{
                  __(
                    'No domains added. The embed will only work on this site until you add one.',
                  )
                }}
              </p>
            </div>
          </div>
        </template>
      </Tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { copyToClipboard } from '@/utils'
import { createDialog } from '@/utils/dialogs'
import {
  Badge,
  Button,
  Checkbox,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Popover,
  Switch,
  Tabs,
  TextInput,
  TimePicker,
  call,
  toast,
} from 'frappe-ui'
import {
  computed,
  defineComponent,
  h,
  onBeforeUnmount,
  onMounted,
  provide,
  ref,
  watch,
} from 'vue'
import AssigneeSearch from '@/components/Settings/AssignmentRules/AssigneeSearch.vue'
import FormBuilderPanel from '@/components/Settings/Forms/FormBuilderPanel.vue'
import LucideCalendarSync from '~icons/lucide/calendar-sync'
import LucideCopy from '~icons/lucide/copy'
import LucideExternalLink from '~icons/lucide/external-link'
import LucideEye from '~icons/lucide/eye'
import LucideSettings from '~icons/lucide/settings'
import LucideShare2 from '~icons/lucide/share-2'
import { ROUTE_PREFIX, pageUrl, slugify } from './bookingPages'

type RowValue = string | number | undefined

interface Row {
  name?: string
  _key?: number
  [field: string]: RowValue
}

type DialogContext = { close: () => void }

interface BookingPageDoc {
  doctype: 'CRM Booking Page'
  name: string
  title: string
  route: string
  enabled: 0 | 1
  duration: number
  location_type: string
  location?: string
  description?: string
  timezone?: string
  holiday_list?: string
  min_notice: number
  max_days_ahead: number
  buffer: number
  slot_interval: number
  create_lead: 0 | 1
  lead_source?: string
  confirmation_message?: string
  guest_reminder?: string
  event_title?: string
  allowed_embedding_domains?: string
  hosts: Row[]
  availability: Row[]
  web_form?: string
  document_type?: 'CRM Lead' | 'CRM Deal'
}

const props = defineProps<{ name: string }>()

const activeTab = ref('setup')
const tabs = [
  { value: 'setup', label: __('Setup'), iconLeft: LucideSettings },
  { value: 'share', label: __('Share'), iconLeft: LucideShare2 },
]
const emit = defineEmits<{ back: [] }>()

const WEEKDAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const SectionTitle = defineComponent({
  props: {
    title: { type: String, default: '' },
    description: { type: String, default: '' },
  },
  setup: (p) => () =>
    h('div', { class: 'mb-3' }, [
      h('div', { class: 'text-base-semibold text-ink-gray-8' }, p.title),
      p.description &&
        h('div', { class: 'mt-0.5 text-p-sm text-ink-gray-5' }, p.description),
    ]),
})

const { getUser } = usersStore()

// AssigneeSearch adds to and filters by `assignmentRuleData.users`; here that's the hosts
provide(
  'assignmentRuleData',
  computed(() => ({ users: doc.value?.hosts || [] })),
)

const doc = ref<BookingPageDoc | null>(null)

const reminderOptions = [
  { label: __('No reminder'), value: 'No reminder' },
  { label: __('1 hour before'), value: '1 hour before' },
  { label: __('1 day before'), value: '1 day before' },
]

// Google Calendar for this page's hosts: who hasn't connected, and where to do it
interface GoogleStatus {
  configured: boolean
  can_set_up: boolean
  unconnected: string[]
  my_calendar: string | null
}
const google = ref<GoogleStatus | null>(null)
const me = getUser().name

async function loadGoogleStatus() {
  const users = (doc.value?.hosts || []).map((h) => String(h.user))
  google.value = users.length
    ? await call('crm.api.booking.google_status', { users }).catch(() => null)
    : null
}
watch(() => doc.value?.hosts?.map((h) => h.user).join(), loadGoogleStatus, {
  immediate: true,
})
// back from connecting in the desk tab
onMounted(() => window.addEventListener('focus', loadGoogleStatus))
onBeforeUnmount(() => window.removeEventListener('focus', loadGoogleStatus))

const iNeedGoogle = computed(
  () => !!google.value?.configured && google.value.unconnected.includes(me),
)
const othersUnconnected = computed(() =>
  google.value?.configured
    ? google.value.unconnected
        .filter((u) => u !== me)
        .map((u) => getUser(u)?.full_name || u)
    : [],
)
const googleNote = computed(() => {
  if (!google.value) return ''
  if (!google.value.configured) {
    return google.value.can_set_up
      ? __(
          "Google isn't set up on this site. Set it up so hosts can connect Google Calendar: their Google meetings then block booked times, and bookings get Meet links.",
        )
      : ''
  }
  if (iNeedGoogle.value) {
    return __(
      'Connect Google Calendar to avoid double bookings and automatically generate Google Meet links for meetings.',
    )
  }
  return othersUnconnected.value.length
    ? __(
        'Hosts who connect Google Calendar avoid double bookings and automatically get Google Meet links for meetings.',
      )
    : ''
})
const googleAction = computed(() => {
  if (!google.value) return null
  if (!google.value.configured) {
    return google.value.can_set_up
      ? { label: __('Set up Google'), href: '/app/google-settings' }
      : null
  }
  if (!iNeedGoogle.value) return null
  const href = google.value.my_calendar
    ? `/app/google-calendar/${encodeURIComponent(google.value.my_calendar)}`
    : '/app/google-calendar/new?' +
      new URLSearchParams({
        user: me,
        calendar_name: getUser().full_name || me,
        enable: '1',
        pull_from_google_calendar: '1',
        push_to_google_calendar: '1',
      })
  return { label: __('Connect Google Calendar'), href }
})

const dirty = ref(false)
const saving = ref(false)
const error = ref('')
let nextKey = 1

const durationOptions = [15, 20, 30, 45, 60, 90, 120].map((m) => ({
  label: __('{0} minutes', [m]),
  value: String(m),
}))
const intervalOptions = [
  { label: __('Every meeting length'), value: '0' },
  ...[15, 30, 60].map((m) => ({
    label: __('Every {0} minutes', [m]),
    value: String(m),
  })),
]
const locationOptions = [
  'Google Meet',
  'Phone call',
  'In person',
  'Custom link',
].map((v) => ({ label: __(v), value: v }))
const timezoneOptions = computed(() => {
  let zones: string[]
  try {
    zones = Intl.supportedValuesOf('timeZone')
  } catch {
    zones = []
  }
  if (doc.value?.timezone && !zones.includes(doc.value.timezone)) {
    zones.unshift(doc.value.timezone)
  }
  return zones.map((z) => ({ label: z.replace(/_/g, ' '), value: z }))
})
onMounted(load)

async function load() {
  doc.value = await call('frappe.client.get', {
    doctype: 'CRM Booking Page',
    name: props.name,
  })
  dirty.value = false
}

function set<K extends keyof BookingPageDoc>(
  field: K,
  value: BookingPageDoc[K],
) {
  if (!doc.value) return
  doc.value[field] = value
  dirty.value = true
}

function setRow(row: Row, field: string, value: RowValue) {
  row[field] = value
  dirty.value = true
}

// Weekly hours

function hhmm(value: RowValue): string {
  if (!value) return ''
  const [h, m] = String(value).split(':')
  return `${h.padStart(2, '0')}:${(m || '00').padStart(2, '0')}`
}

// A day can have more than one row, for split hours like 10–1 and 2–6
function hoursFor(day: string): Row[] {
  return (doc.value?.availability || [])
    .filter((r) => r.workday === day)
    .sort((a, b) => hhmm(a.start_time).localeCompare(hhmm(b.start_time)))
}

// the same checks the server runs on save, shown under the offending row
const hoursErrors = computed(() => {
  const errors = new Map<Row, string>()
  for (const day of WEEKDAYS) {
    let latestEnd = ''
    for (const row of hoursFor(day)) {
      const start = hhmm(row.start_time)
      const end = hhmm(row.end_time)
      if (start >= end) {
        errors.set(row, __('End time must be after the start time'))
      } else if (start < latestEnd) {
        errors.set(row, __('Times overlap with another set of times'))
      }
      if (end > latestEnd) latestEnd = end
    }
  }
  return errors
})

const LAST_MINUTE = 23 * 60 + 45

function minutes(value: RowValue): number {
  const [h, m] = hhmm(value).split(':').map(Number)
  return h * 60 + (m || 0)
}

function toTime(total: number): string {
  const h = String(Math.floor(total / 60)).padStart(2, '0')
  const m = String(total % 60).padStart(2, '0')
  return `${h}:${m}`
}

function formatDuration(total: number): string {
  if (total < 60) return __('{0} mins', [total])
  const hours = total / 60
  return hours === 1 ? __('1 hr') : __('{0} hrs', [+hours.toFixed(2)])
}

function formatClock(total: number): string {
  const h = Math.floor(total / 60)
  const m = String(total % 60).padStart(2, '0')
  return `${h % 12 || 12}:${m} ${h < 12 ? 'am' : 'pm'}`
}

// like Google: end times start after the start time and show the length
function endTimeOptions(row: Row) {
  const start = minutes(row.start_time)
  const options = []
  for (let t = start + 15; t <= LAST_MINUTE; t += 15) {
    options.push({
      value: toTime(t),
      label: `${formatClock(t)} (${formatDuration(t - start)})`,
    })
  }
  return options
}

function setTime(row: Row, field: 'start_time' | 'end_time', value: string) {
  if (!value) return
  if (field === 'start_time') {
    // a start past the end pushes the end along, keeping the range's length
    const length = Math.max(minutes(row.end_time) - minutes(row.start_time), 15)
    const start = Math.min(minutes(value), LAST_MINUTE - 15)
    setRow(row, 'start_time', `${toTime(start)}:00`)
    if (start >= minutes(row.end_time)) {
      setRow(
        row,
        'end_time',
        `${toTime(Math.min(start + length, LAST_MINUTE))}:00`,
      )
    }
    return
  }
  setRow(row, field, `${hhmm(value)}:00`)
}

function newRow(day: string, start: string, end: string): Row {
  return { _key: nextKey++, workday: day, start_time: start, end_time: end }
}

function toggleDay(day: string, on: boolean) {
  if (!doc.value) return
  const rows = doc.value.availability.filter((r) => r.workday !== day)
  if (on) rows.push(newRow(day, '09:00:00', '17:00:00'))
  doc.value.availability = rows
  dirty.value = true
}

// the new range starts an hour after the day's last one ends
function addHours(day: string) {
  if (!doc.value) return
  const last = hoursFor(day).at(-1)
  const from = Math.min(
    Number(hhmm(last?.end_time || '08:00').split(':')[0]) + 1,
    22,
  )
  const pad = (hour: number) => `${String(hour).padStart(2, '0')}:00:00`
  doc.value.availability.push(
    newRow(day, pad(from), pad(Math.min(from + 2, 23))),
  )
  dirty.value = true
}

function removeHoursRow(row: Row) {
  if (!doc.value) return
  doc.value.availability = doc.value.availability.filter((r) => r !== row)
  dirty.value = true
}

// "Copy times to": the days ticked take this day's hours, like Calendly
const copyTargets = ref<string[]>([])

function toggleCopyTarget(day: string, on: boolean) {
  copyTargets.value = on
    ? [...copyTargets.value, day]
    : copyTargets.value.filter((d) => d !== day)
}

function copyTimes(day: string) {
  if (!doc.value) return
  const source = hoursFor(day)
  const targets = new Set(copyTargets.value)
  doc.value.availability = [
    ...doc.value.availability.filter((r) => !targets.has(String(r.workday))),
    ...[...targets].flatMap((d) =>
      source.map((r) => newRow(d, String(r.start_time), String(r.end_time))),
    ),
  ]
  dirty.value = true
}

// Form

const formBuilder = ref<InstanceType<typeof FormBuilderPanel> | null>(null)
const recordLabel = computed(() =>
  doc.value?.document_type === 'CRM Deal' ? __('deal') : __('lead'),
)
// the page and its form save together from the header
const unsaved = computed(() => dirty.value || Boolean(formBuilder.value?.dirty))

function removeHost(row: Row) {
  if (!doc.value) return
  doc.value.hosts = doc.value.hosts.filter((h) => h !== row)
  dirty.value = true
}

// Saving

async function save() {
  if (!doc.value) return
  error.value = ''
  saving.value = true
  try {
    // the form toasts its own errors
    if (formBuilder.value?.dirty && !(await formBuilder.value.save())) return
    if (!dirty.value) {
      toast.success(__('Booking page saved'))
      return
    }
    const order = (day: string) => WEEKDAYS.indexOf(day)
    doc.value.availability.sort(
      (a, b) =>
        order(a.workday) - order(b.workday) ||
        hhmm(a.start_time).localeCompare(hhmm(b.start_time)),
    )
    doc.value = await call('frappe.client.save', { doc: doc.value })
    dirty.value = false
    toast.success(__('Booking page saved'))
  } catch (e) {
    error.value =
      (e as { messages?: string[] })?.messages?.[0] ||
      __('Could not save the page')
  } finally {
    saving.value = false
  }
}

const publicUrl = computed(() => (doc.value ? pageUrl(doc.value.route) : ''))
const embeddingDomains = computed(() =>
  (doc.value?.allowed_embedding_domains || '').split(/\s+/).filter(Boolean),
)
// mirrors ALLOWED_EMBEDDING_DOMAIN_RE in crm/www/crm_form.py, which drops anything else
const EMBEDDING_DOMAIN_RE =
  /^(https?:\/\/)?(\*\.)?[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?(?::\d+)?$/
const invalidEmbeddingDomains = computed(() =>
  embeddingDomains.value.filter((d) => !EMBEDDING_DOMAIN_RE.test(d)),
)
// the script grows or shrinks the iframe to fit each step, so it never scrolls inside
const iframeSnippet = computed(() => {
  if (!doc.value) return ''
  const route = doc.value.route
  const id = `crm-book-${route}`
  const origin = new URL(publicUrl.value).origin
  return [
    `<iframe id="${id}" src="${publicUrl.value}?embed=1" width="100%" height="720" style="border:0" title="${doc.value?.title || 'Book a meeting'}"></iframe>`,
    '<script>',
    '  addEventListener("message", (e) => {',
    `    if (e.origin === "${origin}" && e.data?.type === "crm-book:height" && e.data.route === "${route}")`,
    `      document.getElementById("${id}").style.height = e.data.height + "px";`,
    '  });',
    '</' + 'script>',
  ].join('\n')
})

function openPage() {
  if (doc.value) window.open(pageUrl(doc.value.route), '_blank')
}

function goBack() {
  if (!unsaved.value) return emit('back')
  createDialog({
    title: __('Discard changes?'),
    message: __('Your changes to this page are not saved.'),
    size: 'sm',
    actions: [
      {
        label: __('Keep editing'),
        onClick: ({ close }: DialogContext) => close(),
      },
      {
        label: __('Discard'),
        variant: 'solid',
        theme: 'red',
        onClick: ({ close }: DialogContext) => {
          close()
          emit('back')
        },
      },
    ],
  })
}
</script>

<style scoped>
.bp-tabs :deep(> div) {
  overflow: visible;
}

/* same pinned tab bar as the web form builder */
.bp-tabs :deep([role='tablist']) {
  position: sticky;
  top: 0;
  z-index: 10;
  padding-left: 0;
  padding-right: 0;
  background-color: var(--surface-elevation-2);
}
</style>
