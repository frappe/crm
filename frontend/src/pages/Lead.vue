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
      <component :is="lead.data._assignedTo?.length == 1 ? 'Button' : 'div'">
        <MultipleAvatar
          :avatars="lead.data._assignedTo"
          @click="showAssignmentModal = true"
        />
      </component>
      <Dropdown :options="statusOptions('lead', updateField, customStatuses)">
        <template #default="{ open }">
          <Button
            :label="lead.data.status"
            :class="getLeadStatus(lead.data.status).colorClass"
          >
            <template #prefix>
              <IndicatorIcon />
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
        :label="__('Convert to Deal')"
        variant="solid"
        @click="showConvertToDealModal = true"
      />
    </template>
  </LayoutHeader>
  <div v-if="lead?.data" class="flex h-full overflow-hidden">
    <Tabs v-model="tabIndex" v-slot="{ tab }" :tabs="tabs">
      <Activities
        ref="activities"
        doctype="CRM Lead"
        :tabs="tabs"
        v-model:reload="reload"
        v-model:tabIndex="tabIndex"
        v-model="lead"
      />
    </Tabs>
    <Resizer class="flex flex-col justify-between border-l" side="right">
      <div
        class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium"
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
                <div class="truncate text-2xl font-medium">
                  {{ lead.data.lead_name || __('Untitled') }}
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
              <SectionFields
                :fields="section.fields"
                :isLastSection="i == fieldsLayout.data.length - 1"
                v-model="lead.data"
                @update="updateField"
              />
              <template v-if="i == 0 && isManager()" #actions>
                <Button
                  variant="ghost"
                  class="w-7 mr-2"
                  @click="showSidePanelModal = true"
                >
                  <EditIcon class="h-4 w-4" />
                </Button>
              </template>
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
    doctype="CRM Lead"
  />
  <Dialog
    v-model="showConvertToDealModal"
    :options="{
      title: __('Convert to Deal'),
      size: 'xl',
      actions: [
        {
          label: __('Convert'),
          variant: 'solid',
          onClick: convertToDeal,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-4 flex items-center gap-2 text-gray-600">
        <OrganizationsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Organization') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingOrganizationChecked" />
        </div>
        <Link
          v-if="existingOrganizationChecked"
          class="form-control mt-2.5"
          variant="outline"
          size="md"
          :value="existingOrganization"
          doctype="CRM Organization"
          @change="(data) => (existingOrganization = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{
            __(
              'New organization will be created based on the data in details section',
            )
          }}
        </div>
      </div>

      <div class="mb-4 mt-6 flex items-center gap-2 text-gray-600">
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
          variant="outline"
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
  <SidePanelModal
    v-if="showSidePanelModal"
    v-model="showSidePanelModal"
    @reload="() => fieldsLayout.reload()"
  />
  <FilesUploader
    v-if="lead.data?.name"
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="lead.data.name"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
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
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelModal from '@/components/Settings/SidePanelModal.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
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
import { contactsStore } from '@/stores/contacts'
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { $dialog, $socket, makeCall } = globalStore()
const { getContactByName, contacts } = contactsStore()
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

const lead = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_lead',
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
const showAssignmentModal = ref(false)
const showSidePanelModal = ref(false)
const showFilesUploader = ref(false)

function updateLead(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

  if (!Array.isArray(fieldname) && validateRequired(fieldname, value)) return

  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'CRM Lead',
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
        iconClasses: 'text-green-600',
      })
      callback?.()
    },
    onError: (err) => {
      createToast({
        title: __('Error updating lead'),
        text: __(err.messages?.[0]),
        icon: 'x',
        iconClasses: 'text-red-600',
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
      iconClasses: 'text-red-600',
    })
    return true
  }
  return false
}

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
    label: lead.data.lead_name || __('Untitled'),
    route: { name: 'Lead', params: { leadId: lead.data.name } },
  })
  return items
})

usePageMeta(() => {
  return {
    title: lead.data?.lead_name || lead.data?.name,
  }
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
      name: 'Tasks',
      label: __('Tasks'),
      icon: TaskIcon,
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
  url: 'crm.api.doc.get_sidebar_fields',
  cache: ['fieldsLayout', props.leadId],
  params: { doctype: 'CRM Lead', name: props.leadId },
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
    doctype: 'CRM Lead',
    name,
  })
  router.push({ name: 'Leads' })
}

// Convert to Deal
const showConvertToDealModal = ref(false)
const existingContactChecked = ref(false)
const existingOrganizationChecked = ref(false)

const existingContact = ref('')
const existingOrganization = ref('')

async function convertToDeal(updated) {
  let valueUpdated = false

  if (existingContactChecked.value && !existingContact.value) {
    createToast({
      title: __('Error'),
      text: __('Please select an existing contact'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return
  }

  if (existingOrganizationChecked.value && !existingOrganization.value) {
    createToast({
      title: __('Error'),
      text: __('Please select an existing organization'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return
  }

  if (existingContactChecked.value && existingContact.value) {
    lead.data.salutation = getContactByName(existingContact.value).salutation
    lead.data.first_name = getContactByName(existingContact.value).first_name
    lead.data.last_name = getContactByName(existingContact.value).last_name
    lead.data.email_id = getContactByName(existingContact.value).email_id
    lead.data.mobile_no = getContactByName(existingContact.value).mobile_no
    existingContactChecked.value = false
    valueUpdated = true
  }

  if (existingOrganizationChecked.value && existingOrganization.value) {
    lead.data.organization = existingOrganization.value
    existingOrganizationChecked.value = false
    valueUpdated = true
  }

  if (valueUpdated) {
    updateLead(
      {
        salutation: lead.data.salutation,
        first_name: lead.data.first_name,
        last_name: lead.data.last_name,
        email_id: lead.data.email_id,
        mobile_no: lead.data.mobile_no,
        organization: lead.data.organization,
      },
      '',
      () => convertToDeal(true),
    )
    showConvertToDealModal.value = false
  } else {
    let deal = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal',
      {
        lead: lead.data.name,
      },
    )
    if (deal) {
      capture('convert_lead_to_deal')
      if (updated) {
        await contacts.reload()
      }
      router.push({ name: 'Deal', params: { dealId: deal } })
    }
  }
}

const activities = ref(null)

function openEmailBox() {
  activities.value.emailBox.show = true
}
</script>
