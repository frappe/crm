<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <AssignTo v-model="assignees.data" doctype="CRM Lead" :docname="leadId" />
      <Dropdown
        v-if="doc && document.statuses"
        :options="statuses"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            v-if="doc.status"
            :label="statusLabel(doc.status)"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          >
            <template #prefix>
              <IndicatorIcon :class="getLeadStatus(doc.status).color" />
            </template>
          </Button>
        </template>
      </Dropdown>
      <Button
        :label="__('Convert to Deal')"
        variant="solid"
        @click="showConvertToDealModal = true"
      />
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel>
        <div
          v-if="activeTabName === 'Properties'"
          class="flex flex-1 flex-col overflow-hidden"
        >
          <div class="flex items-center justify-between border-b px-5 py-3">
            <div>
              <div class="text-base font-medium text-ink-gray-9">
                {{ linkedPropertiesTitle }}
              </div>
              <div class="text-sm text-ink-gray-6">
                {{ linkedPropertiesDescription }}
              </div>
            </div>
            <div class="flex gap-2">
              <Button
                v-if="isBuyerLead"
                :label="__('Edit Interest Details')"
                variant="subtle"
                @click="editBuyerInterestPreferences"
              />
              <Button
                v-if="isSellerLead"
                :label="__('Assign Property Unit')"
                variant="solid"
                @click="assignPropertyUnitToSeller"
              />
            </div>
          </div>
          <div class="flex-1 overflow-auto p-5">
            <div v-if="isBuyerLead" class="mb-5 flex flex-col gap-4">
              <div class="rounded border border-outline-gray-1 bg-surface-white p-4">
                <div class="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <div class="text-sm font-medium text-ink-gray-9">
                      {{ __('Interest Details') }}
                    </div>
                    <div class="text-xs text-ink-gray-6">
                      {{ __('Buyer requirements used before selecting inventory units.') }}
                    </div>
                  </div>
                  <Button
                    :label="__('Edit')"
                    variant="subtle"
                    @click="editBuyerInterestPreferences"
                  />
                </div>
                <div class="grid gap-3 text-sm md:grid-cols-2 xl:grid-cols-4">
                  <div
                    v-for="item in buyerInterestPreferenceRows"
                    :key="item.label"
                    class="rounded bg-surface-gray-1 p-3"
                  >
                    <div class="text-xs text-ink-gray-5">{{ item.label }}</div>
                    <div class="mt-1 font-medium text-ink-gray-9">
                      {{ item.value || __('—') }}
                    </div>
                  </div>
                </div>
              </div>
              <div class="rounded border border-outline-gray-1 bg-surface-white p-4">
                <div class="mb-3">
                  <div class="text-sm font-medium text-ink-gray-9">
                    {{ __('Add Inventory Units to Interest') }}
                  </div>
                  <div class="text-xs text-ink-gray-6">
                    {{ __('Select one or many available inventory units, then save them to this buyer interest list.') }}
                  </div>
                </div>
                <div class="flex flex-col gap-3 lg:flex-row lg:items-start">
                  <TableMultiselectInput
                    v-model="selectedInterestUnits"
                    class="flex-1"
                    doctype="Lead Interested Unit"
                  />
                  <Button
                    :label="__('Add Selected Units')"
                    variant="solid"
                    :disabled="!selectedInterestUnits.length"
                    @click="addSelectedInterestedUnits"
                  />
                </div>
              </div>
            </div>
            <div
              v-if="linkedProperties.loading"
              class="rounded border border-outline-gray-1 p-5 text-sm text-ink-gray-6"
            >
              {{ __('Loading linked properties...') }}
            </div>
            <div
              v-else-if="!visibleLinkedPropertyRows.length"
              class="rounded border border-outline-gray-1 p-5 text-sm text-ink-gray-6"
            >
              {{ linkedPropertiesEmptyText }}
            </div>
            <div
              v-else
              class="overflow-hidden rounded border border-outline-gray-1"
            >
              <table v-if="isBuyerLead" class="w-full text-left text-sm">
                <thead class="border-b bg-surface-gray-1 text-ink-gray-6">
                  <tr>
                    <th class="px-4 py-3 font-medium">{{ __('Unit SKU') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Unit Name') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Area') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Developer') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Compound') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Finishing Type') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Budget') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Proposal Status') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in visibleLinkedPropertyRows"
                    :key="row.name"
                    class="border-b last:border-b-0"
                  >
                    <td class="px-4 py-3 text-ink-gray-9">{{ row.sku || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.name || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ formatUnitArea(row) }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.developer || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.project || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.finishing_type || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ formatPrice(row.price) }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.proposal_status || __('Not Sent') }}</td>
                  </tr>
                </tbody>
              </table>
              <table v-else class="w-full text-left text-sm">
                <thead class="border-b bg-surface-gray-1 text-ink-gray-6">
                  <tr>
                    <th class="px-4 py-3 font-medium">{{ __('Property Code / SKU') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Property Title / Unit') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Compound / Project') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Developer') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Unit Type') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Finishing Type') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Target Asking Price') }}</th>
                    <th class="px-4 py-3 font-medium">{{ __('Status') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in visibleLinkedPropertyRows"
                    :key="row.name"
                    class="border-b last:border-b-0"
                  >
                    <td class="px-4 py-3 text-ink-gray-9">{{ row.sku || row.property_code || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.property_title || row.name || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.project || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.developer || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.unit_type || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.finishing_type || __('—') }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ formatPrice(row.price) }}</td>
                    <td class="px-4 py-3 text-ink-gray-8">{{ row.status || __('—') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <Activities
          v-else
          ref="activities"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          doctype="CRM Lead"
          :docname="leadId"
          :tabs="tabs"
          @beforeSave="beforeStatusChange"
          @afterSave="reloadResources"
        />
      </template>
    </Tabs>
    <Resizer class="flex flex-col justify-between border-l" side="right">
      <div
        class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(leadId)"
      >
        {{ __(leadId) }}
      </div>
      <FileUploader
        :validateFile="validateIsImageFile"
        @success="(file) => updateField('image', file.file_url)"
      >
        <template #default="{ openFileSelector }">
          <div class="flex items-center justify-start gap-5 border-b p-5">
            <div class="group relative size-12">
              <Avatar
                size="3xl"
                class="size-12"
                :label="title"
                :image="doc.image"
              />
              <component
                :is="doc.image ? Dropdown : 'div'"
                v-bind="
                  doc.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: doc.image
                              ? __('Change Image')
                              : __('Upload Image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: __('Remove Image'),
                            onClick: () => updateField('image', ''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0.5 left-0 right-0.5 flex h-9 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="size-4 cursor-pointer text-white" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2.5 truncate">
              <Tooltip :text="doc.lead_name || __('Set First Name')">
                <div class="truncate text-2xl font-medium text-ink-gray-9">
                  {{ title }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Button
                  v-if="callEnabled"
                  :tooltip="__('Make a Call')"
                  :icon="PhoneIcon"
                  @click="
                    () =>
                      doc.mobile_no
                        ? makeCall(doc.mobile_no)
                        : toast.error(
                            __('Please set a mobile number to make calls'),
                          )
                  "
                />

                <Button
                  :tooltip="__('Send an Email')"
                  :icon="Email2Icon"
                  @click="
                    doc.email
                      ? openEmailBox()
                      : toast.error(
                          __('Please set an email address to send emails'),
                        )
                  "
                />
                <Button
                  :tooltip="__('Go to Website')"
                  :icon="LinkIcon"
                  @click="
                    doc.website
                      ? openWebsite(doc.website)
                      : toast.error(__('Please set a website to visit'))
                  "
                />

                <Button
                  :tooltip="__('Attach a File')"
                  :icon="AttachmentIcon"
                  @click="showFilesUploader = true"
                />

                <Button
                  v-if="canDelete"
                  :tooltip="__('Delete')"
                  variant="subtle"
                  theme="red"
                  icon="trash-2"
                  @click="deleteLead"
                />
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
        </template>
      </FileUploader>
      <SLASection
        v-if="doc.sla_status"
        v-model="doc"
        @updateField="updateField"
      />
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Lead"
          :docname="leadId"
          @reload="sections.reload"
          @beforeFieldChange="beforeStatusChange"
          @afterFieldChange="reloadResources"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <ConvertToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :lead="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="leadId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Lead'"
    :docname="leadId"
    name="Leads"
  />
  <LostReasonModal
    v-if="showLostReasonModal"
    v-model="showLostReasonModal"
    doctype="CRM Lead"
    :document="document"
  />
</template>
<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LostReasonModal from '@/components/Modals/LostReasonModal.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import TableMultiselectInput from '@/components/Controls/TableMultiselectInput.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  validateIsImageFile,
  isTranslatable,
} from '@/utils'
import { getView } from '@/utils/view'
import { renderFieldLayoutDialog } from '@/utils/renderFieldLayoutDialog'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { callEnabled } from '@/composables/telephony'
import {
  createResource,
  FileUploader,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Lead')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: { type: String, required: true },
})

const reload = ref(false)
const activities = ref(null)
const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showConvertToDealModal = ref(false)
const showFilesUploader = ref(false)
const selectedInterestUnits = ref([])

const {
  triggerOnChange,
  triggerOnRender,
  assignees,
  permissions,
  document,
  scripts,
  error,
} = useDocument('CRM Lead', props.leadId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const doc = computed(() => document.doc || {})
const isBuyerLead = computed(() => doc.value.party_type !== 'Seller')
const isSellerLead = computed(() => doc.value.party_type === 'Seller')

onMounted(async () => {
  if (document.doc) await triggerOnRender()
})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? 'Document not found'
        : 'Error occurred',
    )
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        deleteDoc: deleteLead,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Lead', params: { leadId: props.leadId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return doc.value?.[t] || props.leadId
})

const statuses = computed(() => {
  let customStatuses = document.statuses?.length
    ? document.statuses
    : document._statuses || []
  return statusOptions('lead', customStatuses, triggerStatusChange)
})

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

const tabs = computed(() => {
  return [
    {
      name: 'Data',
      label: __('Data'),
      icon: DetailsIcon,
    },
    {
      name: 'Properties',
      label: isBuyerLead.value ? __('Interest') : __('Properties'),
      icon: LinkIcon,
    },
    {
      name: 'Events',
      label: __('Event'),
      icon: EventIcon,
    },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
  ]
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab')

const activeTabName = computed(() => tabs.value[tabIndex.value]?.name)

const linkedProperties = createResource({
  url: 'real_estate_crm_customs.api.get_lead_linked_units',
  cache: ['leadLinkedProperties', props.leadId],
  params: { lead: props.leadId },
  auto: true,
})

const linkedPropertyRows = computed(() => linkedProperties.data || [])

const visibleLinkedPropertyRows = computed(() => {
  if (isSellerLead.value) {
    return linkedPropertyRows.value.filter((row) => row.owner_lead === props.leadId)
  }
  return linkedPropertyRows.value.filter((row) => row.relationship !== 'Seller Unit')
})

const linkedPropertiesTitle = computed(() =>
  isBuyerLead.value ? __('Interest') : __('Properties'),
)

const linkedPropertiesDescription = computed(() =>
  isBuyerLead.value
    ? __('Buyer interest details plus one or many selected inventory units.')
    : __('Seller property onboarding list: property identity, compound, developer, type, finishing, asking price, and status.'),
)

const linkedPropertiesEmptyText = computed(() =>
  isBuyerLead.value
    ? __('No interested units linked to this buyer lead yet.')
    : __('No seller properties assigned to this lead yet.'),
)

const buyerInterestPreferenceRows = computed(() => [
  {
    label: __('Interested Unit Area'),
    value: formatPreferredArea(),
  },
  {
    label: __('Area'),
    value: doc.value.preferred_area,
  },
  {
    label: __('Developer'),
    value: doc.value.preferred_developer,
  },
  {
    label: __('Compound'),
    value: doc.value.preferred_compound,
  },
  {
    label: __('Finishing Type'),
    value: doc.value.preferred_finishing_type,
  },
  {
    label: __('Delivery Time'),
    value: doc.value.preferred_delivery_time,
  },
  {
    label: __('Budget'),
    value: formatPrice(doc.value.buyer_budget),
  },
])

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Lead'],
  params: { doctype: 'CRM Lead' },
  auto: true,
})

function formatPrice(value) {
  if (value === null || value === undefined || value === '') return __('—')
  return value
}

function formatPreferredArea() {
  if (!doc.value.interested_unit_area) return ''
  return [doc.value.interested_unit_area, doc.value.area_unit].filter(Boolean).join(' ')
}

function formatUnitArea(row) {
  const unitArea = row.unit_area || row.area || row.size
  return unitArea ? [unitArea, doc.value.area_unit].filter(Boolean).join(' ') : __('—')
}

async function editBuyerInterestPreferences() {
  if (!isBuyerLead.value) {
    toast.error(__('Only buyer leads can have interest details'))
    return
  }

  let values = await renderFieldLayoutDialog({
    title: __('Edit Interest Details'),
    size: 'xl',
    defaults: {
      interested_unit_area: doc.value.interested_unit_area,
      area_unit: doc.value.area_unit || 'Sq M',
      preferred_area: doc.value.preferred_area,
      preferred_developer: doc.value.preferred_developer,
      preferred_compound: doc.value.preferred_compound,
      preferred_finishing_type: doc.value.preferred_finishing_type,
      preferred_delivery_time: doc.value.preferred_delivery_time,
      buyer_budget: doc.value.buyer_budget,
    },
    fields: [
      {
        fieldname: 'interested_unit_area',
        fieldtype: 'Float',
        label: __('Interested Unit Area'),
      },
      {
        fieldname: 'area_unit',
        fieldtype: 'Select',
        label: __('Area Unit'),
        options: 'Sq M\nSq Ft',
      },
      {
        fieldname: 'preferred_area',
        fieldtype: 'Data',
        label: __('Area'),
      },
      {
        fieldname: 'preferred_developer',
        fieldtype: 'Link',
        label: __('Developer'),
        options: 'Property Developer',
      },
      {
        fieldname: 'preferred_compound',
        fieldtype: 'Link',
        label: __('Compound / Project'),
        options: 'Real Estate Project',
      },
      {
        fieldname: 'preferred_finishing_type',
        fieldtype: 'Select',
        label: __('Finishing Type'),
        options: '\nCore & Shell\nSemi-Finished\nFully Finished',
      },
      {
        fieldname: 'preferred_delivery_time',
        fieldtype: 'Data',
        label: __('Delivery Time'),
      },
      {
        fieldname: 'buyer_budget',
        fieldtype: 'Currency',
        label: __('Budget'),
      },
    ],
    submitLabel: __('Save Interest Details'),
  })

  if (!values) return

  Object.entries(values).forEach(([fieldname, value]) => {
    doc.value[fieldname] = value
  })

  document.save.submit(null, {
    onSuccess: () => {
      sections.reload()
      toast.success(__('Interest details updated'))
    },
    onError: (err) => {
      toast.error(err.messages?.[0] || __('Error updating interest details'))
      document.reload?.()
    },
  })
}

async function addSelectedInterestedUnits() {
  if (!selectedInterestUnits.value.length) return

  const units = selectedInterestUnits.value.map((row) => row.unit).filter(Boolean)
  if (!units.length) return

  await call('real_estate_crm_customs.api.link_interested_units', {
    lead: props.leadId,
    units,
  })
  selectedInterestUnits.value = []
  linkedProperties.reload()
  document.reload?.()
  toast.success(__('Selected inventory units added to the buyer interest list'))
}

async function assignPropertyUnitToSeller() {
  if (doc.value.party_type !== 'Seller') {
    toast.error(__('Only seller leads can be assigned property units'))
    return
  }

  let values = await renderFieldLayoutDialog({
    title: __('Assign Property Unit'),
    fields: [
      {
        fieldname: 'unit',
        fieldtype: 'Link',
        label: __('Available Unit'),
        options: 'Real Estate Unit',
        reqd: 1,
        get_query: () => ({ filters: { status: 'Available' } }),
      },
    ],
  })

  if (!values?.unit) return

  await call('real_estate_crm_customs.api.assign_property_unit_to_seller', {
    lead: props.leadId,
    unit: values.unit,
  })
  linkedProperties.reload()
  sections.reload()
  document.reload?.()
  toast.success(__('Property unit assigned to this seller lead'))
}

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  setLostReason()
}

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function deleteLead() {
  showDeleteLinkedDocModal.value = true
}

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}

function statusLabel(status) {
  if (isTranslatable('CRM Lead Status')) return __(status)
  return status
}

const showLostReasonModal = ref(false)

function setLostReason() {
  if (
    getLeadStatus(document.doc.status).type !== 'Lost' ||
    (document.doc.lost_reason && document.doc.lost_reason !== 'Other') ||
    (document.doc.lost_reason === 'Other' && document.doc.lost_notes)
  ) {
    document.save.submit(null, {
      onSuccess: () => sections.reload(),
    })
    return
  }

  showLostReasonModal.value = true
}

function beforeStatusChange(data) {
  if (
    Object.hasOwn(data ?? {}, 'status') &&
    getLeadStatus(data.status).type == 'Lost'
  ) {
    setLostReason()
  } else {
    document.save.submit(null, {
      onSuccess: () => reloadResources(data),
    })
  }
}

function reloadResources(data) {
  if (Object.hasOwn(data ?? {}, 'lead_owner')) {
    assignees.reload()
  }
  if (
    Object.hasOwn(data ?? {}, 'status') &&
    getLeadStatus(data.status).type != 'Lost'
  ) {
    sections.reload()
  }
}
</script>
