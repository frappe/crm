<template>
  <LayoutHeader v-if="lead.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="lead.data._customActions"
        :actions="lead.data._customActions"
      />
      <component :is="lead.data._assignedTo?.length == 1 ? 'Button' : 'div'">
        <MultipleAvatar
          :avatars="lead.data._assignedTo"
          @click="showAssignmentModal = true"
        />
      </component>
      <Dropdown :options="statusOptions('lead', updateField)">
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
        label="Convert to Deal"
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
        :title="tab.label"
        v-model:reload="reload"
        v-model="lead"
      />
    </Tabs>
    <div class="flex w-[352px] flex-col justify-between border-l">
      <div
        class="flex h-[41px] items-center border-b px-5 py-2.5 text-lg font-semibold"
      >
        About this Lead
      </div>
      <FileUploader
        @success="(file) => updateField('image', file.file_url)"
        :validateFile="validateFile"
      >
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 border-b p-5">
            <div class="group relative h-[88px] w-[88px]">
              <Avatar
                size="3xl"
                class="h-[88px] w-[88px]"
                :label="lead.data.first_name"
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
                              ? 'Change image'
                              : 'Upload image',
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: 'Remove image',
                            onClick: () => updateField('image', ''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0 left-0 right-0 flex h-13 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2.5 truncate">
              <Tooltip :text="lead.data.lead_name">
                <div class="truncate text-2xl font-medium">
                  {{ lead.data.lead_name }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Tooltip text="Make a call...">
                  <Button
                    class="h-7 w-7"
                    @click="
                      () =>
                        lead.data.mobile_no
                          ? makeCall(lead.data.mobile_no)
                          : errorMessage('No phone number set')
                    "
                  >
                    <PhoneIcon class="h-4 w-4" />
                  </Button>
                </Tooltip>
                <Button class="h-7 w-7">
                  <EmailIcon
                    class="h-4 w-4"
                    @click="
                      lead.data.email
                        ? openEmailBox()
                        : errorMessage('No email set')
                    "
                  />
                </Button>
                <Tooltip text="Go to website...">
                  <Button class="h-7 w-7">
                    <LinkIcon
                      class="h-4 w-4"
                      @click="
                        lead.data.website
                          ? openWebsite(lead.data.website)
                          : errorMessage('No website set')
                      "
                    />
                  </Button>
                </Tooltip>
              </div>
              <ErrorMessage :message="error" />
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
        v-if="detailSections.length"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <div class="flex flex-col overflow-y-auto">
          <div
            v-for="(section, i) in detailSections"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== detailSections.length - 1 }"
          >
            <Section :is-opened="section.opened" :label="section.label">
              <SectionFields
                :fields="section.fields"
                v-model="lead.data"
                @update="updateField"
              />
            </Section>
          </div>
        </div>
      </div>
    </div>
  </div>
  <AssignmentModal
    v-if="lead.data"
    :doc="lead.data"
    v-model="showAssignmentModal"
    v-model:assignees="lead.data._assignedTo"
  />
  <Dialog
    v-model="showConvertToDealModal"
    :options="{
      title: 'Convert to Deal',
      size: 'xl',
      actions: [
        {
          label: 'Convert',
          variant: 'solid',
          onClick: convertToDeal,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-4 flex items-center gap-2 text-gray-600">
        <OrganizationsIcon class="h-4 w-4" />
        <label class="block text-base"> Organization </label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>Choose Existing</div>
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
          New organization will be created based on the data in details section
        </div>
      </div>

      <div class="mb-4 mt-6 flex items-center gap-2 text-gray-600">
        <ContactsIcon class="h-4 w-4" />
        <label class="block text-base"> Contact </label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>Choose Existing</div>
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
          New contact will be created based on the person's details
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
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
  setupCustomActions,
  errorMessage,
} from '@/utils'
import { globalStore } from '@/stores/global'
import { contactsStore } from '@/stores/contacts'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { viewsStore } from '@/stores/views'
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
} from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const { $dialog, makeCall } = globalStore()
const { getContactByName, contacts } = contactsStore()
const { organizations } = organizationsStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { getDefaultView } = viewsStore()
const router = useRouter()

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const lead = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_lead',
  params: { name: props.leadId },
  cache: ['lead', props.leadId],
  auto: true,
  onSuccess: (data) => {
    setupAssignees(data)
    setupCustomActions(data, {
      doc: data,
      $dialog,
      router,
      updateField,
      createToast,
      deleteDoc: deleteLead,
      call,
    })
  },
})

const reload = ref(false)
const showAssignmentModal = ref(false)

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
        title: 'Lead updated',
        icon: 'check',
        iconClasses: 'text-green-600',
      })
      callback?.()
    },
    onError: (err) => {
      createToast({
        title: 'Error updating lead',
        text: err.messages?.[0],
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  })
}

function validateRequired(fieldname, value) {
  let meta = lead.data.all_fields || {}
  if (meta[fieldname]?.reqd && !value) {
    createToast({
      title: 'Error Updating Lead',
      text: `${meta[fieldname].label} is a required field`,
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return true
  }
  return false
}

const breadcrumbs = computed(() => {
  let defaultView = getDefaultView()
  let route = { name: 'Leads' }
  if (defaultView?.route_name == 'Leads' && defaultView?.is_view) {
    route = { name: 'Leads', query: { view: defaultView.name } }
  }
  let items = [{ label: 'Leads', route: route }]
  items.push({
    label: lead.data.lead_name,
    route: { name: 'Lead', params: { leadId: lead.data.name } },
  })
  return items
})

const tabIndex = ref(0)
const tabs = [
  {
    label: 'Activity',
    icon: ActivityIcon,
  },
  {
    label: 'Emails',
    icon: EmailIcon,
  },
  {
    label: 'Calls',
    icon: PhoneIcon,
  },
  {
    label: 'Tasks',
    icon: TaskIcon,
  },
  {
    label: 'Notes',
    icon: NoteIcon,
  },
]

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return 'Only PNG and JPG images are allowed'
  }
}

const detailSections = computed(() => {
  let data = lead.data
  if (!data) return []
  return data.doctype_fields
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
      title: 'Error',
      text: 'Please select an existing contact',
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return
  }

  if (existingOrganizationChecked.value && !existingOrganization.value) {
    createToast({
      title: 'Error',
      text: 'Please select an existing organization',
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
      () => convertToDeal(true)
    )
    showConvertToDealModal.value = false
  } else {
    let deal = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal',
      {
        lead: lead.data.name,
      }
    )
    if (deal) {
      if (updated) {
        await organizations.reload()
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
