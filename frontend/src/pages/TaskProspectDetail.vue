<template>
  <LayoutHeader v-if="contact.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <!-- Task Status Selector (when task is loaded) -->
      <div v-if="taskData" class="flex items-center gap-2">
        <span class="text-xs font-medium text-ink-gray-5">{{ __('Task Status:') }}</span>
        <select
          :value="taskData.status || 'To Do'"
          class="rounded-md border px-2.5 py-1 text-xs font-semibold focus:outline-none cursor-pointer transition-colors"
          :class="getStatusBadgeClass(taskData.status || 'To Do')"
          @change="changeTaskStatus($event.target.value)"
        >
          <option value="To Do">{{ __('To Do') }}</option>
          <option value="In Progress">{{ __('In Progress') }}</option>
          <option value="Pending">{{ __('Pending') }}</option>
          <option value="Callback">{{ __('Callback') }}</option>
          <option value="Follow up">{{ __('Follow up') }}</option>
          <option value="Not Interested">{{ __('Not Interested') }}</option>
        </select>
      </div>

      <CustomActions
        v-if="contact._actions?.length"
        :actions="contact._actions"
      />
      <Button
        :label="__('New Deal')"
        iconLeft="lucide-plus"
        @click="openDealModal"
      />
    </template>
  </LayoutHeader>

  <div v-if="contact.doc" ref="parentRef" class="flex h-full">
    <!-- Left Side Panel (Matches Contact Detail Page) -->
    <Resizer
      v-if="contact.doc"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="changeContactImage"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="group relative h-15.5 w-15.5">
                  <Avatar
                    size="3xl"
                    class="h-15.5 w-15.5"
                    :label="contact.doc.full_name"
                    :image="contact.doc.image"
                  />
                  <component
                    :is="contact.doc.image ? Dropdown : 'div'"
                    v-bind="
                      contact.doc.image
                        ? {
                            options: [
                              {
                                icon: 'lucide-upload',
                                label: contact.doc.image
                                  ? __('Change Image')
                                  : __('Upload Image'),
                                onClick: openFileSelector,
                              },
                              {
                                icon: 'lucide-trash-2',
                                label: __('Remove Image'),
                                onClick: () => changeContactImage(''),
                              },
                            ],
                          }
                        : { onClick: openFileSelector }
                    "
                    class="!absolute bottom-0 left-0 right-0"
                  >
                    <div
                      class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                      style="
                        -webkit-clip-path: inset(22px 0 0 0);
                        clip-path: inset(22px 0 0 0);
                      "
                    >
                      <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                    </div>
                  </component>
                </div>
                <div class="flex flex-col gap-1.5 truncate text-ink-gray-9">
                  <div class="truncate text-3xl-medium">
                    <span v-if="contact.doc.salutation">
                      {{ contact.doc.salutation + ' ' }}
                    </span>
                    <span>{{ contact.doc.full_name }}</span>
                  </div>
                  <div
                    v-if="contact.doc.company_name"
                    class="flex items-center gap-1.5 text-base text-ink-gray-8"
                  >
                    {{ contact.doc.company_name }}
                  </div>
                  <div
                    v-if="contact.doc.designation"
                    class="text-xs text-ink-gray-5"
                  >
                    {{ contact.doc.designation }}
                  </div>
                  <ErrorMessage :message="__(error)" />
                </div>
              </div>

              <!-- Allocation info snippet -->
              <div v-if="taskData" class="w-full rounded bg-surface-gray-1 p-2.5 text-xs text-ink-gray-6 border border-outline-gray-2 space-y-1">
                <div class="flex items-center justify-between">
                  <span><span class="font-medium text-ink-gray-8">{{ __('Allocated:') }}</span> {{ taskData.allocation_date }}</span>
                  <span v-if="taskData.timezone && taskData.timezone !== 'Not Available'" class="font-mono text-[11px] text-ink-gray-5">
                    {{ taskData.timezone }}
                  </span>
                </div>
                <div v-if="taskData.notes" class="text-ink-gray-7 truncate">
                  <span class="font-medium">{{ __('Notes:') }}</span> {{ taskData.notes }}
                </div>
              </div>

              <div class="flex gap-1.5">
                <Button
                  v-if="callEnabled && contact.doc.mobile_no"
                  :label="__('Make Call')"
                  size="sm"
                  :iconLeft="PhoneIcon"
                  @click="callEnabled && makeCall(contact.doc.mobile_no)"
                />
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="parsedSections"
          doctype="Contact"
          :docname="contact.doc.name"
          @reload="sections.reload"
        />
      </div>
    </Resizer>

    <!-- Right Side Activities Panel with allowEmail=true -->
    <ContactActivities
      ref="contactActivitiesRef"
      :contact="contact.doc"
      :contactId="props.contactId"
      :taskId="taskData?.name || props.taskId"
      :allowEmail="true"
      :dealRows="rows"
      :dealColumns="columns"
      @newDeal="openDealModal"
      @taskStatusUpdated="onTaskStatusUpdated"
    />
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="dealDefaults"
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import ContactActivities from '@/components/ContactActivities/ContactActivities.vue'
import CustomActions from '@/components/CustomActions.vue'
import { validateIsImageFile, setupCustomizations } from '@/utils'
import { useContactFields } from '@/composables/useContactFields'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  call,
  createResource,
  usePageMeta,
  Dropdown,
  toast,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { makeCall, $dialog, $socket } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
  taskId: { type: [String, Number], default: null },
})

const route = useRoute()
const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')
const taskData = ref(null)

const {
  document: contact,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('Contact', props.contactId)

const transformField = useContactFields(contact)

async function fetchTaskDetails() {
  try {
    const res = await call('crm.api.daily_allocation.get_task_for_contact', {
      contact: props.contactId,
      task_name: props.taskId || null,
    })
    if (res) {
      taskData.value = res
    }
  } catch (err) {
    console.error('Failed to load task details:', err)
  }
}

onMounted(async () => {
  await fetchTaskDetails()
  if (contact.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  return [
    { label: __('My Tasks'), route: { name: 'Tasks' } },
    {
      label: title.value,
      route: {
        name: 'TaskProspect',
        params: { contactId: props.contactId },
        query: route.query,
      },
    },
  ]
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return contact.doc?.[t] || props.contactId
})

usePageMeta(() => {
  return {
    title: `${title.value} — My Tasks`,
    icon: brand.favicon,
  }
})

const showDealModal = ref(false)
const dealDefaults = ref({})
const contactActivitiesRef = ref(null)

async function changeTaskStatus(newStatus) {
  if (!taskData.value?.name) return
  try {
    await call('crm.api.daily_allocation.update_task_status', {
      task_name: taskData.value.name,
      status: newStatus,
    })
    taskData.value.status = newStatus
    toast.success(__('Task status updated to {0}', [newStatus]))
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to update status'))
  }
}

function onTaskStatusUpdated(newStatus) {
  if (taskData.value) {
    taskData.value.status = newStatus
  }
}

function getStatusBadgeClass(st) {
  switch (st) {
    case 'To Do':
      return 'bg-surface-gray-2 text-ink-gray-7 border-outline-gray-2'
    case 'In Progress':
      return 'bg-surface-blue-2 text-ink-blue-4 border-outline-blue-2'
    case 'Pending':
      return 'bg-surface-amber-2 text-ink-amber-5 border-outline-amber-2'
    case 'Callback':
      return 'bg-surface-purple-2 text-ink-purple-4 border-outline-purple-2'
    case 'Follow up':
      return 'bg-surface-teal-2 text-ink-teal-4 border-outline-teal-2'
    case 'Not Interested':
      return 'bg-surface-gray-3 text-ink-gray-6 border-outline-gray-3'
    default:
      return 'bg-surface-gray-2 text-ink-gray-7 border-outline-gray-2'
  }
}

// company_name is free text, so only pick an existing organization; otherwise the deal creates one
async function openDealModal() {
  const company = contact.doc.company_name
  const isOrganization =
    company &&
    (await call('frappe.client.get_count', {
      doctype: 'CRM Organization',
      filters: { name: company },
    }))
  dealDefaults.value = {
    contact: contact.doc.name,
    ...(isOrganization
      ? { organization: company }
      : { organization_name: company }),
  }
  showDealModal.value = true
}

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact image updated'))
    },
  })
}

const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

const rows = computed(() => {
  if (!deals.data || !deals.data.length) return []
  return deals.data.map((row) => getDealRowObject(row))
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
})

const parsedSections = computed(() => {
  if (!sections.data) return []
  return sections.data.map((section) => ({
    ...section,
    columns: section.columns.map((column) => ({
      ...column,
      fields: column.fields.map((field) => {
        field.label = fieldLabelMap[field.fieldname] || field.label
        field.placeholder =
          fieldPlaceholderMap[field.fieldname] || field.placeholder
        return transformField(field, { showAddressModal })
      }),
    })),
  }))
})

const fieldLabelMap = {
  mobile_no: __('Mobile Number'),
  company_name: __('Organization'),
}

const fieldPlaceholderMap = {
  mobile_no: __('Add Mobile Number...'),
  company_name: __('Add Organization...'),
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    deal_value: getFormattedCurrency('deal_value', deal),
    status: {
      label: deal.status,
      color: getDealStatus(deal.status)?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: timestampCell(deal.modified),
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'deal_value',
    align: 'right',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile Number'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal Owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        contact.doc.address = d.name
        contact.save.submit()
      },
    },
  })
}

// Setup custom actions from Form Scripts
watch(
  () => contact.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        updateField: contact.setValue.submit,
        deleteDoc: () => {},
        call,
      })
      contact._actions = s.actions || []
    }
  },
  { once: true },
)
</script>

