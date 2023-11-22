<template>
  <LayoutHeader v-if="lead.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <FormControl
        type="autocomplete"
        :options="activeAgents"
        :value="getUser(lead.data.lead_owner).full_name"
        @change="(option) => updateField('lead_owner', option.email)"
        placeholder="Lead owner"
      >
        <template #prefix>
          <UserAvatar class="mr-2" :user="lead.data.lead_owner" size="sm" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.email" size="sm" />
        </template>
      </FormControl>
      <Dropdown
        :options="statusDropdownOptions(lead.data, 'lead', updateField)"
      >
        <template #default="{ open }">
          <Button :label="lead.data.status">
            <template #prefix>
              <IndicatorIcon :class="leadStatuses[lead.data.status].color" />
            </template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
            /></template>
          </Button>
        </template>
      </Dropdown>
      <Button label="Convert to deal" variant="solid" @click="convertToDeal" />
    </template>
  </LayoutHeader>
  <div v-if="lead?.data" class="flex h-full overflow-hidden">
    <Tabs v-model="tabIndex" v-slot="{ tab }" :tabs="tabs">
      <Activities
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
        About this lead
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
                    @click="() => makeCall(lead.data.mobile_no)"
                  >
                    <PhoneIcon class="h-4 w-4" />
                  </Button>
                </Tooltip>
                <Button class="h-7 w-7">
                  <EmailIcon class="h-4 w-4" />
                </Button>
                <Tooltip text="Go to website...">
                  <Button class="h-7 w-7">
                    <LinkIcon
                      class="h-4 w-4"
                      @click="openWebsite(lead.data.website)"
                    />
                  </Button>
                </Tooltip>
              </div>
              <ErrorMessage :message="error" />
            </div>
          </div>
        </template>
      </FileUploader>
      <div class="flex flex-1 flex-col justify-between overflow-hidden">
        <div class="flex flex-col overflow-y-auto">
          <div
            v-for="(section, i) in detailSections.data"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== detailSections.data.length - 1 }"
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
  <OrganizationModal
    v-model="showOrganizationModal"
    :organization="_organization"
    :options="{
      redirect: false,
      afterInsert: (doc) =>
        updateField('organization', doc.name, () => {
          organizations.reload()
        }),
    }"
  />
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
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import {
  leadStatuses,
  statusDropdownOptions,
  openWebsite,
  createToast,
  activeAgents,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import { organizationsStore } from '@/stores/organizations'
import {
  createResource,
  FileUploader,
  ErrorMessage,
  FeatherIcon,
  FormControl,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
} from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const { getUser } = usersStore()
const { contacts } = contactsStore()
const { organizations, getOrganization } = organizationsStore()
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
})

const reload = ref(false)
const showOrganizationModal = ref(false)
const _organization = ref({})

function updateLead(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

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

const breadcrumbs = computed(() => {
  let items = [{ label: 'Leads', route: { name: 'Leads' } }]
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

const detailSections = createResource({
  url: 'crm.api.doc.get_doctype_fields',
  params: { doctype: 'CRM Lead' },
  cache: 'leadFields',
  auto: true,
  transform: (data) => {
    return getParsedFields(data)
  },
})

function getParsedFields(sections) {
  sections.forEach((section) => {
    section.fields.forEach((field) => {
      if (['website', 'industry'].includes(field.name)) {
        field.value = organization.value?.[field.name]
        field.tooltip =
          'This field is read-only and is fetched from the organization'
      } else if (field.name == 'organization') {
        field.create = (value, close) => {
          _organization.value.organization_name = value
          showOrganizationModal.value = true
          close()
        }
        field.link = () =>
          router.push({
            name: 'Organization',
            params: { organizationId: lead.data.organization },
          })
      }
    })
  })

  return sections
}

const organization = computed(() => {
  return getOrganization(lead.data.organization)
})

async function convertToDeal() {
  let deal = await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', {
    lead: lead.data.name,
  })
  if (deal) {
    await contacts.reload()
    router.push({ name: 'Deal', params: { dealId: deal } })
  }
}

function updateField(name, value, callback) {
  updateLead(name, value, () => {
    lead.data[name] = value
    callback?.()
  })
}
</script>
