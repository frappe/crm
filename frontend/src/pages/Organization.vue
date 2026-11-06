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
      <EnrichFromWebsite
        doctype="CRM Organization"
        :docname="props.organizationId"
        :website="organization.doc?.website"
        @done="onEnriched"
      />
      <Button
        v-if="activeTab === 'deals'"
        :label="__('New Deal')"
        iconLeft="lucide-plus"
        @click="showDealModal = true"
      />
      <Link
        v-if="activeTab === 'contacts'"
        value=""
        doctype="Contact"
        :filters="{ company_name: ['!=', props.organizationId] }"
        :onCreate="
          (value, close) => {
            _contact = {
              first_name: value,
              company_name: props.organizationId,
            }
            showContactModal = true
            close()
          }
        "
        @change="(contact) => addContact(contact)"
      >
        <template #target="{ togglePopover }">
          <Button
            :label="__('Add Contact')"
            iconLeft="lucide-plus"
            @click="togglePopover()"
          />
        </template>
      </Link>
    </template>
  </LayoutHeader>
  <div v-if="organization.doc" ref="parentRef" class="flex h-full">
    <Resizer
      v-if="organization.doc"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="changeOrganizationImage"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
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
                                icon: 'lucide-upload',
                                label: organization.doc.organization_logo
                                  ? __('Change Image')
                                  : __('Upload Image'),
                                onClick: openFileSelector,
                              },
                              {
                                icon: 'lucide-trash-2',
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
                  <div class="truncate text-3xl-medium text-ink-gray-9">
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
              <div class="flex gap-1.5">
                <Button
                  v-if="canDelete"
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  iconLeft="lucide-trash-2"
                  @click="deleteOrganization()"
                />
                <Button
                  :tooltip="__('Open Website')"
                  icon="lucide-link"
                  @click="openWebsite"
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
          :sections="sections.data"
          doctype="CRM Organization"
          :docname="organization.doc.name"
          @reload="sections.reload"
          @beforeFieldChange="beforeFieldChange"
        />
      </div>
    </Resizer>
    <Tabs
      v-model="activeTab"
      as="div"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tablist']]:gap-7.5 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&>[role='tabpanel']:not([hidden])]:flex [&>[role='tabpanel']:not([hidden])]:grow [&>[data-slot=tab-list]]:overflow-x-auto [&_[data-slot=tab-indicator]]:translate-y-0 [&>[data-slot=tab-panel]]:min-h-0 [&>[data-slot=tab-panel]]:flex-col [&>[data-slot=tab-panel]]:overflow-auto"
    >
      <template #tab-label="{ tab }">{{ __(tab.label) }}</template>
      <template #tab-suffix="{ tab, active }">
        <Badge
          :class="[active ? 'bg-surface-gray-10' : 'bg-gray-600']"
          variant="solid"
          theme="gray"
          size="sm"
        >
          {{ tab.count }}
        </Badge>
      </template>
      <template #tab-panel="{ tab }">
        <div
          v-if="tab.value === 'contacts' && contacts.error"
          class="space-y-2 px-5 py-4"
          role="alert"
        >
          <ErrorMessage
            :message="
              contacts.error?.messages?.[0] ||
              contacts.error?.message ||
              __('Contacts could not be loaded.')
            "
          />
          <Button
            :label="__('Try Again')"
            :loading="contacts.loading"
            @click="contacts.reload()"
          />
        </div>
        <div
          v-if="tab.value === 'contacts' && contacts.loading && !contacts.data"
          class="flex justify-center py-8"
          role="status"
          :aria-label="__('Loading contacts')"
        >
          <LoadingIndicator class="size-5" />
        </div>
        <DealsListView
          v-if="tab.label === 'Deals' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <ContactsListView
          v-if="tab.label === 'Contacts' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <EmptyState
          v-if="
            !rows.length &&
            !(
              tab.value === 'contacts' &&
              (contacts.loading || contacts.error || contacts.data?.total_count)
            )
          "
          :icon="tab.iconLeft"
          :name="__(tab.label)"
          :description="
            tab.value === 'deals'
              ? __('Use New Deal to create a deal for this organization.')
              : ''
          "
        />
        <div
          v-if="tab.value === 'contacts' && contacts.data"
          class="mt-auto flex flex-wrap items-center justify-between gap-3 border-t px-5 py-3 text-p-sm text-ink-gray-5"
        >
          <span
            v-if="!contacts.data.rows.length && contacts.data.total_count"
            >{{ __('There are no contacts on this page.') }}</span
          >
          <span>{{
            contacts.data.rows.length
              ? __('{0}–{1} of {2}', [
                  contacts.data.start + 1,
                  contacts.data.start + contacts.data.rows.length,
                  contacts.data.total_count,
                ])
              : __('{0} contacts', [contacts.data.total_count])
          }}</span>
          <div class="flex gap-2">
            <Button
              v-if="!contacts.data.rows.length && contacts.data.total_count"
              :label="__('First Page')"
              :disabled="contacts.loading"
              @click="firstContactPage"
            />
            <Button
              :label="__('Previous')"
              :disabled="contacts.loading || contactStart === 0"
              @click="changeContactPage(-1)"
            />
            <Button
              :label="__('Next')"
              :disabled="contacts.loading || !contacts.data.has_more"
              @click="changeContactPage(1)"
            />
          </div>
        </div>
      </template>
    </Tabs>
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
    :contact="_contact"
    :options="{ redirect: false, afterInsert: () => contacts.reload() }"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="{ organization: props.organizationId }"
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import Link from '@/components/Controls/Link.vue'
import CustomActions from '@/components/CustomActions.vue'
import EnrichFromWebsite from '@/components/EnrichFromWebsite.vue'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { getView } from '@/utils/view'
import {
  validateIsImageFile,
  setupCustomizations,
  openWebsite as openExternalWebsite,
} from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Dropdown,
  Tabs,
  createListResource,
  usePageMeta,
  createResource,
  LoadingIndicator,
  toast,
  call,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, ref, watch, onMounted } from 'vue'
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

const showDeleteLinkedDocModal = ref(false)
const showContactModal = ref(false)
const showDealModal = ref(false)
const _contact = ref({})

const {
  document: organization,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('CRM Organization', props.organizationId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

function onEnriched() {
  organization.reload?.()
  sections.reload()
}

onMounted(async () => {
  if (organization.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Organizations'), route: { name: 'Organizations' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(
      route.query.view,
      route.query.viewType,
      'CRM Organization',
    )
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
      query: route.query,
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

const activeTab = ref('deals')
const tabs = [
  {
    value: 'deals',
    label: 'Deals',
    iconLeft: DealsIcon,
    count: computed(() => deals.data?.length),
  },
  {
    value: 'contacts',
    label: 'Contacts',
    iconLeft: ContactsIcon,
    count: computed(() => contacts.data?.total_count),
  },
]

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Deal',
  cache: ['deals', props.organizationId],
  fields: [
    'name',
    'organization',
    'currency',
    'deal_value',
    'status',
    'email',
    'mobile_no',
    'deal_owner',
    'modified',
  ],
  filters: {
    organization: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const contactStart = ref(0)
const contactPageLength = 20
const contacts = createResource({
  url: 'crm.api.contact.get_organization_contacts',
  makeParams: () => ({
    organization: props.organizationId,
    start: contactStart.value,
    page_length: contactPageLength,
  }),
  auto: true,
})

function firstContactPage() {
  contactStart.value = 0
  contacts.reload()
}

function changeContactPage(direction) {
  contactStart.value = Math.max(
    0,
    contactStart.value + direction * contactPageLength,
  )
  contacts.reload()
}

// This explicit user action changes the contact's employer. Reading synchronized
// contacts uses their native Organization links without changing that employer.
async function addContact(contact) {
  if (!contact) return
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: contact,
    fieldname: 'company_name',
    value: props.organizationId,
  })
  contacts.reload()
  toast.success(__('Contact added to {0}', [props.organizationId]))
}

const rows = computed(() => {
  const data = activeTab.value === 'deals' ? deals.data : contacts.data?.rows

  if (!data) return []

  return data.map((row) => {
    return activeTab.value === 'deals'
      ? getDealRowObject(row)
      : getContactRowObject(row)
  })
})

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => {
  return activeTab.value === 'deals' ? dealColumns : contactColumns
})

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: organization.doc?.organization_logo,
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
      logo:
        contact.company_name === organization.doc?.name
          ? organization.doc?.organization_logo
          : undefined,
    },
    modified: timestampCell(contact.modified),
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

const contactColumns = [
  {
    label: __('Name'),
    key: 'full_name',
    width: '17rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Phone'),
    key: 'mobile_no',
    width: '12rem',
  },
  {
    label: __('Organization'),
    key: 'company_name',
    width: '12rem',
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
        organization.doc.address = d.name
        organization.save.submit()
      },
    },
  })
}

// Setup custom actions from Form Scripts
watch(
  () => organization.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        updateField: organization.setValue.submit,
        deleteDoc: deleteOrganization,
        call,
      })
      organization._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
