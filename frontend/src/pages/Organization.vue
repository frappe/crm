<template>
  <LayoutHeader v-if="organization.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <CustomActions
        v-if="organization._actions?.length"
        :actions="organization._actions"
      />
      <Button
        v-if="tabs[tabIndex]?.name === 'Deals'"
        variant="solid"
        :label="__('Create Deal')"
        iconLeft="plus"
        @click="showDealModal = true"
      />
      <Button
        v-if="tabs[tabIndex]?.name === 'Contacts'"
        variant="solid"
        :label="__('Create Contact')"
        iconLeft="plus"
        @click="showContactModal = true"
      />
    </template>
  </LayoutHeader>
  <div v-if="organization.doc" class="flex h-full overflow-hidden">
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel>
        <Activities
          v-if="!['Deals', 'Contacts'].includes(tabs[tabIndex]?.name)"
          ref="activities"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          doctype="CRM Organization"
          :docname="props.organizationId"
          :tabs="activityTabs"
        />
        <div v-else class="flex flex-1 flex-col overflow-y-auto">
          <DealsListView
            v-if="tabs[tabIndex]?.name === 'Deals' && dealRows.length"
            class="mt-4"
            :rows="dealRows"
            :columns="dealColumns"
            :options="{ selectable: false, showTooltip: false }"
          />
          <ContactsListView
            v-else-if="tabs[tabIndex]?.name === 'Contacts' && contactRows.length"
            class="mt-4"
            :rows="contactRows"
            :columns="contactColumns"
            :options="{ selectable: false, showTooltip: false }"
          />
          <EmptyState
            v-else
            :icon="tabs[tabIndex]?.icon"
            :name="__(tabs[tabIndex]?.label)"
          />
        </div>
      </template>
    </Tabs>
    <Resizer
      class="flex flex-col justify-between border-l"
      side="right"
    >
      <div
        class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(props.organizationId)"
      >
        {{ __(props.organizationId) }}
      </div>
      <FileUploader
        :validateFile="validateIsImageFile"
        @success="changeOrganizationImage"
      >
        <template #default="{ openFileSelector, error }">
          <div class="flex flex-col items-start justify-start gap-4 border-b p-5">
            <div class="flex gap-4 items-center">
              <div class="group relative h-15.5 w-15.5">
                <Avatar
                  size="3xl"
                  class="h-15.5 w-15.5"
                  :label="organization.doc.organization_name"
                  :image="organization.doc.organization_logo"
                />
                <component
                  :is="organization.doc.organization_logo ? Dropdown : 'div'"
                  v-bind="
                    organization.doc.organization_logo
                      ? {
                          options: [
                            {
                              icon: 'upload',
                              label: organization.doc.organization_logo
                                ? __('Change Image')
                                : __('Upload Image'),
                              onClick: openFileSelector,
                            },
                            {
                              icon: 'trash-2',
                              label: __('Remove Image'),
                              onClick: () => changeOrganizationImage(''),
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
              <div class="flex flex-col gap-2 truncate">
                <div class="truncate text-2xl font-medium text-ink-gray-9">
                  <span>{{ organization.doc.name }}</span>
                </div>
                <div
                  v-if="organization.doc.website"
                  class="flex items-center gap-1.5 text-base text-ink-gray-8"
                >
                  <WebsiteIcon class="size-4" />
                  <span>{{ website(organization.doc.website) }}</span>
                </div>
                <ErrorMessage :message="__(error)" />
              </div>
            </div>
            <div class="flex gap-1.5 flex-wrap">
              <Button
                :tooltip="__('Send an Email')"
                size="sm"
                :iconLeft="Email2Icon"
                @click="openEmailBox()"
              />
              <Button
                :tooltip="__('Attach a File')"
                size="sm"
                :iconLeft="AttachmentIcon"
                @click="showFilesUploader = true"
              />
              <Button
                :tooltip="__('Open Website')"
                icon="link"
                size="sm"
                @click="openWebsite"
              />
              <Button
                v-if="linkedLead"
                :label="__('Go to Lead')"
                size="sm"
                iconLeft="arrow-right"
                @click="router.push({ name: 'Lead', params: { leadId: linkedLead } })"
              />
              <Button
                v-else
                :label="__('Create Lead')"
                size="sm"
                iconLeft="plus"
                @click="createLeadFromOrg()"
              />
              <Button
                v-if="canDelete"
                :label="__('Delete')"
                theme="red"
                size="sm"
                iconLeft="trash-2"
                @click="deleteOrganization()"
              />
            </div>
          </div>
        </template>
      </FileUploader>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Organization"
          :docname="organization.doc.name"
          @reload="sections.reload"
          @beforeFieldChange="beforeFieldChange"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Organization'"
    :docname="props.organizationId"
    name="Organizations"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="{ company_name: props.organizationId }"
    :options="{ redirect: false, afterInsert: () => contacts.reload() }"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="{ organization: props.organizationId }"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Organization"
    :docname="props.organizationId"
    @after="
      () => {
        activities?.all_activities?.reload()
      }
    "
  />
</template>

<script setup>
import Activities from '@/components/Activities/Activities.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import CustomActions from '@/components/CustomActions.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import { whatsappEnabled } from '@/composables/whatsapp'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { getView } from '@/utils/view'
import {
  formatDate,
  timeAgo,
  validateIsImageFile,
  setupCustomizations,
  copyToClipboard,
  openWebsite as openExternalWebsite,
} from '@/utils'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Dropdown,
  Tabs,
  createListResource,
  usePageMeta,
  createResource,
  toast,
  call,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from 'frappe-ui/frappe'
import { computed, ref, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  organizationId: { type: String, required: true },
})

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { getUser } = usersStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Organization')
const { capture } = useTelemetry()

const route = useRoute()
const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')
const reload = ref(false)
const activities = ref(null)
const showFilesUploader = ref(false)
const showDeleteLinkedDocModal = ref(false)
const showContactModal = ref(false)
const showDealModal = ref(false)
const linkedLead = ref(null)

const {
  document: organization,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('CRM Organization', props.organizationId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

onMounted(async () => {
  if (organization.doc) {
    await triggerOnRender()
    await fetchLinkedLead()
  }
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Organizations'), route: { name: 'Organizations' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Organization')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Organizations',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Organization',
      params: { organizationId: props.organizationId },
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return organization.doc?.[t] || props.organizationId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

const tabs = computed(() => {
  let tabOptions = [
    { name: 'Activity', label: __('Activity'), icon: ActivityIcon },
    { name: 'Emails', label: __('Emails'), icon: EmailIcon },
    { name: 'Comments', label: __('Comments'), icon: CommentIcon },
    { name: 'Calls', label: __('Calls'), icon: PhoneIcon },
    { name: 'Events', label: __('Events'), icon: EventIcon },
    { name: 'Tasks', label: __('Tasks'), icon: TaskIcon },
    { name: 'Notes', label: __('Notes'), icon: NoteIcon },
    { name: 'Attachments', label: __('Attachments'), icon: AttachmentIcon },
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
    {
      name: 'Deals',
      label: __('Deals'),
      icon: DealsIcon,
      count: computed(() => deals.data?.length || 0),
    },
    {
      name: 'Contacts',
      label: __('Contacts'),
      icon: ContactsIcon,
      count: computed(() => contacts.data?.length || 0),
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const activityTabs = computed(() =>
  tabs.value.filter((t) => !['Deals', 'Contacts'].includes(t.name)),
)

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastOrganizationTab')

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activity'].includes(currentTab?.name)) {
    changeTabTo('emails')
  }
  nextTick(() => {
    if (activities.value?.emailBox) {
      activities.value.emailBox.show = true
    }
  })
}

async function fetchLinkedLead() {
  try {
    const result = await call('crm.api.organization.get_linked_lead', {
      organization: props.organizationId,
    })
    linkedLead.value = result || null
  } catch {
    linkedLead.value = null
  }
}

async function createLeadFromOrg() {
  try {
    const leadName = await call(
      'crm.api.organization.create_lead_from_organization',
      { organization: props.organizationId },
    )
    if (leadName) {
      linkedLead.value = leadName
      toast.success(__('Lead created successfully'))
      router.push({ name: 'Lead', params: { leadId: leadName } })
    }
  } catch (e) {
    toast.error(e.messages?.[0] || __('Failed to create lead'))
  }
}

async function deleteOrganization() {
  showDeleteLinkedDocModal.value = true
}

function changeOrganizationImage(file) {
  organization.setValue.submit({
    organization_logo: file?.file_url || null,
  })
}

function beforeFieldChange(data) {
  if (Object.hasOwn(data ?? {}, 'organization_name')) {
    call('frappe.client.rename_doc', {
      doctype: 'CRM Organization',
      old_name: props.organizationId,
      new_name: data.organization_name,
    }).then(() => {
      router.push({
        name: 'Organization',
        params: { organizationId: data.organization_name },
      })
    })
  } else {
    organization.save.submit()
  }
}

function website(url) {
  return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
}

function openWebsite() {
  if (!organization.doc.website) {
    toast.error(__('No Website Found'))
    return
  }
  openExternalWebsite(organization.doc.website)
}

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Organization'],
  params: { doctype: 'CRM Organization' },
  auto: true,
  transform: (data) => getParsedSections(data),
})

function getParsedSections(_sections) {
  return _sections.map((section) => {
    section.columns = section.columns.map((column) => {
      column.fields = column.fields.map((field) => {
        if (field.fieldname === 'address') {
          return {
            ...field,
            create: (value, close) => {
              showAddressModal()
              close()
            },
            edit: (address) => showAddressModal(address),
          }
        } else {
          return field
        }
      })
      return column
    })
    return section
  })
}

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Deal',
  cache: ['deals', props.organizationId],
  fields: [
    'name',
    'organization',
    'currency',
    'annual_revenue',
    'status',
    'email',
    'mobile_no',
    'deal_owner',
    'modified',
  ],
  filters: { organization: props.organizationId },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  cache: ['contacts', props.organizationId],
  fields: [
    'name',
    'full_name',
    'image',
    'email_id',
    'mobile_no',
    'company_name',
    'modified',
  ],
  filters: { company_name: props.organizationId },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const { getFormattedCurrency } = getMeta('CRM Deal')

const dealRows = computed(() => {
  if (!deals.data) return []
  return deals.data.map((row) => getDealRowObject(row))
})

const contactRows = computed(() => {
  if (!contacts.data) return []
  return contacts.data.map((row) => getContactRowObject(row))
})

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: organization.doc?.organization_logo,
    },
    annual_revenue: getFormattedCurrency('annual_revenue', deal),
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
    modified: {
      label: formatDate(deal.modified),
      timeAgo: __(timeAgo(deal.modified)),
    },
  }
}

function getContactRowObject(contact) {
  return {
    name: contact.name,
    full_name: {
      label: contact.full_name,
      image_label: contact.full_name,
      image: contact.image,
    },
    email: contact.email_id,
    mobile_no: contact.mobile_no,
    company_name: {
      label: contact.company_name,
      logo: organization.doc?.organization_logo,
    },
    modified: {
      label: formatDate(contact.modified),
      timeAgo: __(timeAgo(contact.modified)),
    },
  }
}

const dealColumns = [
  { label: __('Organization'), key: 'organization', width: '11rem' },
  { label: __('Amount'), key: 'annual_revenue', align: 'right', width: '9rem' },
  { label: __('Status'), key: 'status', width: '10rem' },
  { label: __('Email'), key: 'email', width: '12rem' },
  { label: __('Mobile No.'), key: 'mobile_no', width: '11rem' },
  { label: __('Deal Owner'), key: 'deal_owner', width: '10rem' },
  { label: __('Last Modified'), key: 'modified', width: '8rem' },
]

const contactColumns = [
  { label: __('Name'), key: 'full_name', width: '17rem' },
  { label: __('Email'), key: 'email', width: '12rem' },
  { label: __('Phone'), key: 'mobile_no', width: '12rem' },
  { label: __('Organization'), key: 'company_name', width: '12rem' },
  { label: __('Last Modified'), key: 'modified', width: '8rem' },
]

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        organization.doc.address = d.name
        organization.save.submit()
      },
    },
  })
}

watch(
  () => organization.doc,
  async (doc) => {
    if (doc) await fetchLinkedLead()
  },
  { once: true },
)

watch(
  () => organization.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField: organization.setValue.submit,
        createToast: toast.create,
        deleteDoc: deleteOrganization,
        call,
      })
      organization._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
