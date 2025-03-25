<template>
  <Dialog
    v-model="show"
    :options="{
      size: 'xl',
      actions: [
        {
          label: editMode ? __('Update') : __('Create'),
          variant: 'solid',
          onClick: () => updateEvent(),
        },
      ],
    }"
  >
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ editMode ? __('Edit Event') : __('Create Event') }}
        </h3>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <FormControl
            ref="subject"
            :label="__('Subject')"
            v-model="_event.subject"
            :required="true"
            :placeholder="__('Call with John Doe')"
          />
        </div>
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">
            {{ __('Description') }}
          </div>
          <TextEditor
            variant="outline"
            ref="description"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
            :bubbleMenu="true"
            :content="_event.description"
            @change="(val) => (_event.description = val)"
            :placeholder="__('Took a call with John Doe and discussed the new project.')"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Dropdown :options="eventStatusOptions(updateEventStatus)">
            <Button :label="_event.status" class="w-full justify-between">
              <template #prefix>
                <EventStatusIcon :status="_event.status" />
              </template>
            </Button>
          </Dropdown>
          <Link
            class="form-control"
            :value="getUser(_event._assign).full_name"
            doctype="User"
            @change="(option) => (_event._assign = option)"
            :placeholder="__('John Doe')"
            :hideMe="true"
          >
            <template #prefix>
              <UserAvatar class="mr-2 !h-4 !w-4" :user="_event.allocated_to" />
            </template>
            <template #item-prefix="{ option }">
              <UserAvatar class="mr-2" :user="option.value" size="sm" />
            </template>
            <template #item-label="{ option }">
              <Tooltip :text="option.value">
                <div class="cursor-pointer">
                  {{ getUser(option.value).full_name }}
                </div>
              </Tooltip>
            </template>
          </Link>
          <FormControl
            v-model="_event.event_type"
            type="select"
            :options="eventTypeOptions"
            :placeholder="__('Event Type')"
          />
          <FormControl
            v-model="_event.event_category"
            type="select"
            :options="eventCategoryOptions"
            :placeholder="__('Event Category')"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <DateTimePicker
            class="datepicker w-36"
            v-model="_event.starts_on"
            :placeholder="__('01/04/2024')"
            input-class="border-none"
          />
          <DateTimePicker
            class="datepicker w-36"
            v-model="_event.ends_on"
            :placeholder="__('01/04/2024')"
            input-class="border-none"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <FormControl
            class="form-control"
            type="checkbox"
            v-model="_event.sync_with_google_calendar"
            @change="(e) => (_event.sync_with_google_calendar = e.target.checked)"
          />
          <label
            class="text-sm text-ink-gray-5"
            @click="_event.sync_with_google_calendar = !_event.sync_with_google_calendar"
          >
            {{ __('Sync with Google Calendar') }}
          </label>
          <Link
            v-if="_event.sync_with_google_calendar"
            class="form-control"
            :value="_event.google_calendar"
            doctype="Google Calendar"
            @change="(option) => (_event.google_calendar = option)"
            :placeholder="__('Google Calendar')"
            :hideMe="true"
            :filters="{ enable: 1 }"
          >
          </Link>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EventStatusIcon from '@/components/Icons/EventStatusIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { eventStatusOptions, createToast } from '@/utils'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { TextEditor, Dropdown, FormControl, Tooltip, call, DateTimePicker, createResource } from 'frappe-ui'
import { ref, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  event: {
    type: Object,
    default: {},
  },
  doctype: {
    type: String,
    default: 'Lead',
  },
  doc: {
    type: String,
    default: '',
  },
})

const show = defineModel()
const events = defineModel('reloadEvents')

const emit = defineEmits(['updateEvent', 'after'])

const { getUser } = usersStore()

const title = ref(null)
const editMode = ref(false)
const _event = ref({
  title: '',
  description: '',
  _assign: '',
  starts_on: '',
  ends_on: '',
  status: 'Open',
  event_type: 'Private',
  event_category: 'Event',
  sync_with_google_calendar: true,
  google_calendar: getUser().google_calendar,
})

const eventMeta = ref(
  await call('next_crm.api.doc.get_fields_meta', {
    doctype: 'Event',
  }),
)

let eventTypeOptions = eventMeta.value.event_type.options.split('\n')
let eventCategoryOptions = eventMeta.value.event_category.options.split('\n')

function updateEventStatus(status) {
  _event.value.status = status
}

const fields = createResource({
  url: 'next_crm.api.doc.get_fields_meta',
  params: { doctype: 'Event' },
  auto: true,
  onSuccess: (data) => {
    data
  },
})

async function updateEvent() {
  if (!_event.value.subject) {
    createToast({
      title: __('Error'),
      text: __('Subject is mandatory'),
      icon: 'x',
      iconClasses: 'text-ink-red-4',
    })
    return
  }
  if (!_event.value.allocated_to) {
    _event.value.allocated_to = getUser().name
  }
  if (!_event.value.sync_with_google_calendar) {
    _event.value.google_calendar = null
  }
  _event.value.assigned_by = getUser().name
  if (_event.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'Event',
      name: _event.value.name,
      fieldname: _event.value,
    })
    if (d.name) {
      events.value.reload()
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'Event',
        reference_type: props.doctype,
        reference_name: props.doc || null,
        ..._event.value,
      },
    })
    if (d.name) {
      let participants = await call('frappe.client.insert', {
        doc: {
          doctype: 'Event Participants',
          parent: d.name,
          reference_doctype: props.doctype,
          reference_docname: props.doc || null,
          parentfield: 'event_participants',
          parenttype: 'Event',
        },
      })
      if (participants.name) {
        capture('event_created')
        events.value.reload()
        emit('after')
      }
    }
  }
  show.value = false
}

function render() {
  editMode.value = false
  nextTick(() => {
    title.value?.el?.focus?.()
    _event.value = { ...props.event }
    if (_event.value.description) {
      editMode.value = true
    }
  })
}

onMounted(() => show.value && render())

watch(show, (value) => {
  if (!value) return
  render()
})
</script>

<style scoped>
:deep(.datepicker svg) {
  width: 0.875rem;
  height: 0.875rem;
}
</style>
