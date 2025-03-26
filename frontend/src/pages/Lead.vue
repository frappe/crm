<template>
  <LayoutHeader v-if="lead.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <CustomActions v-if="customActions" :actions="customActions" />
      <AssignTo
        v-model="lead.data._assignedTo"
        :data="lead.data"
        doctype="Lead"
      />
      <Dropdown :options="statusOptions('lead', updateField, customStatuses)">
        <template #default="{ open }">
          <Button
            :label="lead.data.status"
            :class="getLeadStatus(lead.data.status).colorClass"
          >
            <template #prefix>
              <IndicatorIcon :class="getLeadStatus(lead.data.status).color" />
            </template>
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
      <Button
        :label="__('Convert to Opportunity')"
        variant="solid"
        @click="showConvertToOpportunityModal = true"
      />
    </template>
  </LayoutHeader>
  <div v-if="lead?.data" class="flex h-full overflow-hidden">
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-panel>
        <Activities
          ref="activities"
          doctype="Lead"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          v-model="lead"
        />
      </template>
    </Tabs>
    <Resizer class="flex flex-col justify-between border-l" side="right">
      <div
        class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(lead.data.name)"
      >
        {{ __(lead.data.name) }}
      </div>
      <FileUploader
        @success="(file) => updateField('image', file.file_url)"
        :validateFile="validateFile"
      >
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 border-b p-5">
            <div class="group relative size-12">
              <Avatar
                size="3xl"
                class="size-12"
                :label="lead.data.first_name || __('Untitled')"
                :image="lead.data.image"
              />
              <component
                :is="lead.data.image ? Dropdown : 'div'"
                v-bind="
                  lead.data.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: lead.data.image
                              ? __('Change image')
                              : __('Upload image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: __('Remove image'),
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
              <Tooltip :text="lead.data.lead_name || __('Set first name')">
                <div class="truncate text-2xl font-medium text-ink-gray-9" @click="showRenameModal = true">
                  {{ lead.data.lead_name || lead.data.title || __('Untitled') }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Tooltip v-if="callEnabled" :text="__('Make a call')">
                  <Button
                    class="h-7 w-7"
                    @click="
                      () =>
                        lead.data.mobile_no
                          ? makeCall(lead.data.mobile_no)
                          : errorMessage(__('No phone number set'))
                    "
                  >
                    <PhoneIcon class="h-4 w-4" />
                  </Button>
                </Tooltip>
                <Tooltip :text="__('Send an email')">
                  <Button class="h-7 w-7">
                    <Email2Icon
                      class="h-4 w-4"
                      @click="
                        lead.data.email
                          ? openEmailBox()
                          : errorMessage(__('No email set'))
                      "
                    />
                  </Button>
                </Tooltip>
                <Tooltip :text="__('Go to website')">
                  <Button class="h-7 w-7">
                    <LinkIcon
                      class="h-4 w-4"
                      @click="
                        lead.data.website
                          ? openWebsite(lead.data.website)
                          : errorMessage(__('No website set'))
                      "
                    />
                  </Button>
                </Tooltip>
                <Tooltip :text="__('Attach a file')">
                  <Button class="h-7 w-7" @click="showFilesUploader = true">
                    <AttachmentIcon class="h-4 w-4" />
                  </Button>
                </Tooltip>
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
        </template>
      </FileUploader>
      <SLASection
        v-if="lead.data.sla_status"
        v-model="lead.data"
        @updateField="updateField"
      />
      <div
        v-if="fieldsLayout.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <div class="flex flex-col overflow-y-auto">
          <div
            v-for="(section, i) in fieldsLayout.data"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== fieldsLayout.data.length - 1 }"
          >
          <Section :is-opened="section.opened" :label="section.label">
              <template #actions>
                <div v-if="section.contacts" class="pr-2">
                  <Link
                    value=""
                    doctype="Contact"
                    @change="(e) => addContact(e)"
                    :onCreate="
                      (value, close) => {
                        _contact = {
                          first_name: value,
                        }
                        showContactModal = true
                        close()
                      }
                    "
                  >
                    <template #target="{ togglePopover }">
                      <Button
                        class="h-7 px-3"
                        variant="ghost"
                        icon="plus"
                        @click="togglePopover()"
                      />
                    </template>
                  </Link>
                </div>
                <div v-else-if="section.addresses" class="pr-2">
                  <Link
                    value=""
                    doctype="Address"
                    @change="(e) => addAddress(e)"
                    :onCreate="
                      (value, close) => {
                        _address = {
                          name: value,
                        }
                        showAddressModal = true
                        close()
                      }
                    "
                  >
                    <template #target="{ togglePopover }">
                      <Button
                        class="h-7 px-3"
                        variant="ghost"
                        icon="plus"
                        @click="togglePopover()"
                      />
                    </template>
                  </Link>
                </div>
                <Button
                  v-else-if="
                    ((!section.contacts && !section.addresses && i == 2) || i == 0) && isManager()
                  "
                  variant="ghost"
                  class="w-7 mr-2"
                  @click="showSidePanelModal = true"
                >
                  <EditIcon class="h-4 w-4" />
                </Button>
              </template>
              <SectionFields
                v-if="section.fields"
                :fields="section.fields"
                :isLastSection="i == fieldsLayout.data.length - 1"
                v-model="lead.data"
                @update="updateField"
              />
              <div v-else>
                <div
                  v-if="
                    section.contacts && leadContacts?.loading && leadContacts?.data?.length == 0
                  "
                  class="flex min-h-20 flex-1 items-center justify-center gap-3 text-base text-ink-gray-4"
                >
                  <LoadingIndicator class="h-4 w-4" />
                  <span>{{ __('Loading...') }}</span>
                </div>
                <div
                  v-if="
                    section.addresses && leadAddresses?.loading && leadAddresses?.data?.length == 0
                  "
                  class="flex min-h-20 flex-1 items-center justify-center gap-3 text-base text-ink-gray-4"
                >
                  <LoadingIndicator class="h-4 w-4" />
                  <span>{{ __('Loading...') }}</span>
                </div>
                <div
                  v-else-if="section.contacts && leadContacts?.data?.length"
                  v-for="(contact, i) in leadContacts.data"
                  :key="contact.name"
                >
                  <div
                    class="px-2 pb-2.5"
                    :class="[i == 0 ? 'pt-5' : 'pt-2.5']"
                  >
                    <Section :is-opened="contact.opened">
                      <template #header="{ opened, toggle }">
                        <div
                          class="flex cursor-pointer items-center justify-between gap-2 pr-1 text-base leading-5 text-ink-gray-7"
                        >
                          <div
                            class="flex h-7 items-center gap-2 truncate"
                            @click="toggle()"
                          >
                            <Avatar
                              :label="contact.full_name"
                              :image="contact.image"
                              size="md"
                            />
                            <div class="truncate">
                              {{ contact.full_name }}
                            </div>
                          </div>
                          <div class="flex items-center">
                            <Dropdown :options="contactOptions(contact)">
                              <Button
                                icon="more-horizontal"
                                class="text-ink-gray-5"
                                variant="ghost"
                              />
                            </Dropdown>
                            <Button
                              variant="ghost"
                              @click="
                                router.push({
                                  name: 'Contact',
                                  params: { contactId: contact.name },
                                })
                              "
                            >
                              <ArrowUpRightIcon class="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" @click="toggle()">
                              <FeatherIcon
                                name="chevron-right"
                                class="h-4 w-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                                :class="{ 'rotate-90': opened }"
                              />
                            </Button>
                          </div>
                        </div>
                      </template>
                      <div
                        class="flex flex-col gap-1.5 text-base text-ink-gray-8"
                      >
                        <div class="flex items-center gap-3 pb-1.5 pl-1 pt-4">
                          <Email2Icon class="h-4 w-4" />
                          {{ contact.email }}
                        </div>
                        <div class="flex items-center gap-3 p-1 py-1.5">
                          <PhoneIcon class="h-4 w-4" />
                          {{ contact.mobile_no }}
                        </div>
                      </div>
                    </Section>
                  </div>
                  <div
                    v-if="i != leadContacts.data.length - 1"
                    class="mx-2 h-px border-t border-gray-200"
                  />
                </div>
                <div
                  v-else-if="section.addresses && leadAddresses?.data?.length"
                  v-for="(address, i) in leadAddresses.data"
                  :key="address.name"
                >
                  <div
                    class="px-2 pb-2.5"
                    :class="[i == 0 ? 'pt-5' : 'pt-2.5']"
                  >
                    <Section :is-opened="address.opened">
                      <template #header="{ opened, toggle }">
                        <div
                          class="flex cursor-pointer items-center justify-between gap-2 pr-1 text-base leading-5 text-ink-gray-7"
                        >
                          <div
                            class="flex h-7 items-center gap-2 truncate"
                            @click="toggle()"
                          >
                            <div class="truncate">
                              {{ address.name }}
                            </div>
                            <Badge
                              v-if="address.is_primary_address"
                              class="ml-2"
                              variant="outline"
                              :label="__('Bill')"
                              theme="green"
                            />
                            <Badge
                              v-if="address.is_shipping_address"
                              class="ml-0"
                              variant="outline"
                              :label="__('Ship')"
                              theme="green"
                            />
                          </div>
                          <div class="flex items-center">
                            <Dropdown :options="addressOptions(address)">
                              <Button
                                icon="more-horizontal"
                                class="text-ink-gray-5"
                                variant="ghost"
                              />
                            </Dropdown>
                            <Button
                              variant="ghost"
                              @click="
                                router.push({
                                  name: 'Address',
                                  params: { addressId: address.name },
                                })
                              "
                            >
                              <ArrowUpRightIcon class="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" @click="toggle()">
                              <FeatherIcon
                                name="chevron-right"
                                class="h-4 w-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                                :class="{ 'rotate-90': opened }"
                              />
                            </Button>
                          </div>
                        </div>
                      </template>
                      <div
                        class="flex flex-col gap-1.5 text-base text-ink-gray-8"
                      >
                        <div class="flex items-center gap-3 pb-1.5 pl-1 pt-4">
                          <AddressIcon class="h-4 w-4" />
                          {{ address.address_line1 }}
                        </div>
                        <div class="flex items-center gap-3 p-1 py-1.5">
                          <PhoneIcon class="h-4 w-4" />
                          {{ address.phone }}
                        </div>
                      </div>
                    </Section>
                  </div>
                  <div
                    v-if="i != leadAddresses.data.length - 1"
                    class="mx-2 h-px border-t border-gray-200"
                  />
                </div>
                <div
                  v-else-if="section.addresses"
                  class="flex h-20 items-center justify-center text-base text-ink-gray-5"
                >
                  {{ __('No addresses added') }}
                </div>
                <div
                  v-else
                  class="flex h-20 items-center justify-center text-base text-ink-gray-5"
                >
                  {{ __('No contacts added') }}
                </div>
              </div>
            </Section>
          </div>
        </div>
      </div>
    </Resizer>
  </div>
  <AssignmentModal
    v-if="showAssignmentModal"
    v-model="showAssignmentModal"
    v-model:assignees="lead.data._assignedTo"
    :doc="lead.data"
    doctype="Lead"
  />
  <Dialog
    v-model="showConvertToOpportunityModal"
    :options="{
      title: __('Convert to Opportunity'),
      size: 'xl',
      actions: [
        {
          label: __('Convert'),
          variant: 'solid',
          onClick: convertToOpportunity,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-4 flex items-center gap-2 text-ink-gray-5">
        <ProspectsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Prospect') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingProspectChecked" />
        </div>
        <Link
          v-if="existingProspectChecked"
          class="form-control mt-2.5"
          variant="subtle"
          size="md"
          :value="existingProspect"
          doctype="Prospect"
          @change="(data) => (existingProspect = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{
            __(
              'New prospect will be created based on the data in details section',
            )
          }}
        </div>
      </div>

      <div class="mb-4 mt-6 flex items-center gap-2 text-ink-gray-5">
        <ContactsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Contact') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingContactChecked" />
        </div>
        <Link
          v-if="existingContactChecked"
          class="form-control mt-2.5"
          variant="subtle"
          size="md"
          :value="existingContact"
          doctype="Contact"
          @change="(data) => (existingContact = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{ __("New contact will be created based on the person's details") }}
        </div>
      </div>
    </template>
  </Dialog>
  <ContactModal
    v-model="showContactModal"
    :contact="_contact"
    :options="{
      redirect: false,
      afterInsert: (doc) => addContact(doc.name),
    }"
  />
  <AddressModal
    v-model="showAddressModal"
    :address="_address"
    :options="{
      afterInsert: (doc) => addAddress(doc.name),
    }"
  />
  <SidePanelModal
    v-if="showSidePanelModal"
    v-model="showSidePanelModal"
    @reload="() => fieldsLayout.reload()"
  />
  <FilesUploader
    v-if="lead.data?.name"
    v-model="showFilesUploader"
    doctype="Lead"
    :docname="lead.data.name"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <RenameModal
      v-model="showRenameModal"
      doctype="Lead"
      :docname="lead?.data?.name"
      :title="lead?.data?.title"
      :options="{
        afterRename: afterRename
      }"
  />
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import ToDoIcon from '@/components/Icons/ToDoIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import ProspectsIcon from '@/components/Icons/ProspectsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import AddressIcon from '@/components/Icons/AddressIcon.vue'
import SuccessIcon from '@/components/Icons/SuccessIcon.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import SidePanelModal from '@/components/Settings/SidePanelModal.vue'
import RenameModal from '@/components/Modals/RenameModal.vue'
import Link from '@/components/Controls/Link.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import {
  openWebsite,
  createToast,
  setupAssignees,
  setupCustomizations,
  errorMessage,
  copyToClipboard,
} from '@/utils'
import { getView } from '@/utils/view'
import { globalStore } from '@/stores/global'

import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import { capture } from '@/telemetry'
import {
  createResource,
  FileUploader,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Switch,
  Breadcrumbs,
  call,
  usePageMeta,
} from 'frappe-ui'
import { h, ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { $dialog, $socket, makeCall } = globalStore()

const { statusOptions, getLeadStatus } = statusesStore()
const { isManager } = usersStore()
const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const customActions = ref([])
const customStatuses = ref([])
const showAssignmentModal = ref(false)
const _address = ref({})
const lead = createResource({
  url: '/api/method/next_crm.api.lead.get_lead',
  params: { name: props.leadId },
  cache: ['lead', props.leadId],
  onSuccess: async (data) => {
    let obj = {
      doc: data,
      $dialog,
      $socket,
      router,
      updateField,
      createToast,
      deleteDoc: deleteLead,
      resource: {
        lead,
        fieldsLayout,
      },
      call,
    }
    setupAssignees(data)
    let customization = await setupCustomizations(data, obj)
    customActions.value = customization.actions || []
    customStatuses.value = customization.statuses || []
  },
})

onMounted(() => {
  if (lead.data) return
  lead.fetch()
})

const reload = ref(false)
const showSidePanelModal = ref(false)
const showFilesUploader = ref(false)
const showRenameModal = ref(false)

function updateLead(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

  if (!Array.isArray(fieldname) && validateRequired(fieldname, value)) return

  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'Lead',
      name: props.leadId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      lead.reload()
      reload.value = true
      createToast({
        title: __('Lead updated'),
        icon: 'check',
        iconClasses: 'text-ink-green-3',
      })
      callback?.()
    },
    onError: (err) => {
      createToast({
        title: __('Error updating lead'),
        text: __(err.messages?.[0]),
        icon: 'x',
        iconClasses: 'text-ink-red-4',
      })
    },
  })
}

function validateRequired(fieldname, value) {
  let meta = lead.data.fields_meta || {}
  if (meta[fieldname]?.reqd && !value) {
    createToast({
      title: __('Error Updating Lead'),
      text: __('{0} is a required field', [meta[fieldname].label]),
      icon: 'x',
      iconClasses: 'text-ink-red-4',
    })
    return true
  }
  return false
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Lead')
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
    label: lead.data.lead_name || lead.data.title || __('Untitled'),
    route: { name: 'Lead', params: { leadId: lead.data.name } },
  })
  return items
})

usePageMeta(() => {
  return {
    title: lead.data?.lead_name || lead.data?.name,
  }
})

const showContactModal = ref(false)
const showAddressModal = ref(false)
const _contact = ref({})

function contactOptions(contact) {
  let options = [
    {
      label: __('Remove'),
      icon: 'trash-2',
      onClick: () => removeContact(contact.name),
    },
  ]
  return options
}

function addressOptions(address) {
  let options = [
    {
      label: __('Remove'),
      icon: 'trash-2',
      onClick: () => removeAddress(address.name),
    },
  ]
  return options
}

async function addContact(contact) {
  let d = await call('next_crm.api.contact.link_contact_to_doc', {
    contact,
    doctype: "Lead",
    docname: props.leadId,
  })
  if (d) {
    leadContacts.reload()
    createToast({
      title: __('Contact added'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
}

async function addAddress(address) {
  let d = await call('next_crm.api.address.link_address_to_doc', {
    address: address,
    doctype: "Lead",
    docname: props.leadId,
  })
  if (d) {
    leadAddresses.reload()
    createToast({
      title: __('Address added'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
}

async function removeContact(contact) {
  let d = await call('next_crm.api.contact.remove_link_from_contact', {
    contact,
    doctype: "Lead",
    docname: props.leadId,
  })
  if (d) {
    leadContacts.reload()
    createToast({
      title: __('Contact removed'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
}

async function removeAddress(address) {
  let d = await call('next_crm.api.lead.remove_address', {
    opportunity: props.leadId,
    address,
  })
  if (d) {
    leadAddresses.reload()
    createToast({
      title: __('Address removed'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
}

const leadContacts = createResource({
  url: '/api/method/next_crm.api.contact.get_lead_opportunity_contacts',
  params: {
    doctype: "Lead",
    docname: props.leadId 
  },
  cache: ['lead_contacts', props.leadId],
  auto: true,
  transform: (data) => {
    data.forEach((contact) => {
      contact.opened = false
    })
    return data
  },
})

const leadAddresses = createResource({
  url: '/api/method/next_crm.api.lead.get_lead_addresses',
  params: { name: props.leadId },
  cache: ['lead_addresses', props.leadId],
  auto: true,
  transform: (data) => {
    data.forEach((address) => {
      address.opened = false
    })
    return data
  },
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Emails',
      label: __('Emails'),
      icon: EmailIcon,
    },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    {
      name: 'Calls',
      label: __('Calls'),
      icon: PhoneIcon,
      condition: () => callEnabled.value,
    },
    {
      name: 'ToDos',
      label: __('ToDos'),
      icon: ToDoIcon,
    },
    {
      name: 'Events',
      label: __('Events'),
      icon: EventIcon,
    },
    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab')

watch(tabs, (value) => {
  if (value && route.params.tabName) {
    let index = value.findIndex(
      (tab) => tab.name.toLowerCase() === route.params.tabName.toLowerCase(),
    )
    if (index !== -1) {
      tabIndex.value = index
    }
  }
})

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return __('Only PNG and JPG images are allowed')
  }
}

const fieldsLayout = createResource({
  url: 'next_crm.api.doc.get_sidebar_fields',
  cache: ['fieldsLayout', props.leadId],
  params: { doctype: 'Lead', name: props.leadId },
  auto: true,
})

function updateField(name, value, callback) {
  updateLead(name, value, () => {
    lead.data[name] = value
    callback?.()
  })
}

async function deleteLead(name) {
  await call('frappe.client.delete', {
    doctype: 'Lead',
    name,
  })
  router.push({ name: 'Leads' })
}

// Convert to Opportunity
const showConvertToOpportunityModal = ref(false)
const existingContactChecked = ref(false)
const existingProspectChecked = ref(false)

const existingContact = ref('')
const existingProspect = ref('')

async function convertToOpportunity() {

  if (existingContactChecked.value && !existingContact.value) {
    createToast({
      title: __('Error'),
      text: __('Please select an existing contact'),
      icon: 'x',
      iconClasses: 'text-ink-red-4',
    })
    return
  }

  if (existingProspectChecked.value && !existingProspect.value) {
    createToast({
      title: __('Error'),
      text: __('Please select an existing prospect'),
      icon: 'x',
      iconClasses: 'text-ink-red-4',
    })
    return
  }

  if (existingContactChecked.value && existingContact.value) {
    existingContact.value = ''
  }

  if (existingProspectChecked.value && existingProspect.value) {
    existingProspectChecked.value = false

  }

  let opportunity = await call(
    'next_crm.overrides.lead.convert_to_opportunity',
    {
      lead: lead.data.name,
      prospect: existingProspect.value
    },
  ).catch((err) => {
    createToast({
      title: __('Error converting to deal'),
      text: __(err.messages?.[0]),
      icon: 'x',
      iconClasses: 'text-ink-red-4',
    })
  })

  if (opportunity) {
    capture('convert_lead_to_opportunity')

      await contacts.reload()
    
    router.push({ name: 'Opportunity', params: { opportunityId: opportunity } })
  }
  
}

const activities = ref(null)

function openEmailBox() {
  activities.value.emailBox.show = true
}

function afterRename(renamed_docname) {
  router.push({ name: props.doctype, params: { leadId: renamed_docname } }).then(() => {
    location.reload();
  });
}
</script>
