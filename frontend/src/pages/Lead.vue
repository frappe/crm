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
          <div class="flex items-center justify-start gap-5 p-5">
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
            v-for="section in detailSections"
            :key="section.label"
            class="flex flex-col"
          >
            <Toggler :is-opened="section.opened" v-slot="{ opened, toggle }">
              <div class="sticky top-0 z-10 border-t bg-white p-3">
                <div
                  class="flex max-w-fit cursor-pointer items-center gap-2 px-2 text-base font-semibold leading-5"
                  @click="toggle()"
                >
                  <FeatherIcon
                    name="chevron-right"
                    class="h-4 text-gray-600 transition-all duration-300 ease-in-out"
                    :class="{ 'rotate-90': opened }"
                  />
                  {{ section.label }}
                </div>
              </div>
              <transition
                enter-active-class="duration-300 ease-in"
                leave-active-class="duration-300 ease-[cubic-bezier(0, 1, 0.5, 1)]"
                enter-to-class="max-h-[200px] overflow-hidden"
                leave-from-class="max-h-[200px] overflow-hidden"
                enter-from-class="max-h-0 overflow-hidden"
                leave-to-class="max-h-0 overflow-hidden"
              >
                <div v-if="opened" class="flex flex-col gap-1.5 px-3">
                  <div
                    v-for="field in section.fields"
                    :key="field.name"
                    class="flex items-center gap-2 px-3 text-base leading-5 last:mb-3"
                  >
                    <div class="w-[106px] shrink-0 text-gray-600">
                      {{ field.label }}
                    </div>
                    <div class="flex-1 overflow-hidden">
                      <FormControl
                        v-if="field.type === 'select'"
                        type="select"
                        :options="field.options"
                        :value="lead.data[field.name]"
                        @change.stop="
                          updateLead(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control cursor-pointer [&_select]:cursor-pointer"
                      >
                        <template #prefix>
                          <IndicatorIcon
                            :class="leadStatuses[lead.data[field.name]].color"
                          />
                        </template>
                      </FormControl>
                      <FormControl
                        v-else-if="field.type === 'email'"
                        type="email"
                        class="form-control"
                        :value="lead.data[field.name]"
                        @change.stop="
                          updateLead(field.name, $event.target.value)
                        "
                        :debounce="500"
                      />
                      <Autocomplete
                        v-else-if="field.type === 'link'"
                        :value="lead.data[field.name]"
                        :options="field.options"
                        @change="(e) => field.change(e)"
                        :placeholder="field.placeholder"
                        class="form-control"
                      >
                        <template
                          v-if="field.create"
                          #footer="{ value, close }"
                        >
                          <div>
                            <Button
                              variant="ghost"
                              class="w-full !justify-start"
                              label="Create one"
                              @click="field.create(value, close)"
                            >
                              <template #prefix>
                                <FeatherIcon name="plus" class="h-4" />
                              </template>
                            </Button>
                          </div>
                        </template>
                      </Autocomplete>
                      <FormControl
                        v-else-if="field.type === 'user'"
                        type="autocomplete"
                        :options="activeAgents"
                        :value="getUser(lead.data[field.name]).full_name"
                        @change="
                          (option) => updateField('lead_owner', option.email)
                        "
                        class="form-control"
                        :placeholder="field.placeholder"
                      >
                        <template #target="{ togglePopover }">
                          <Button
                            variant="ghost"
                            @click="togglePopover()"
                            :label="getUser(lead.data[field.name]).full_name"
                            class="w-full !justify-start"
                          >
                            <template #prefix>
                              <UserAvatar
                                :user="lead.data[field.name]"
                                size="sm"
                              />
                            </template>
                          </Button>
                        </template>
                        <template #item-prefix="{ option }">
                          <UserAvatar
                            class="mr-2"
                            :user="option.email"
                            size="sm"
                          />
                        </template>
                      </FormControl>
                      <Tooltip
                        :text="field.tooltip"
                        class="flex h-7 cursor-pointer items-center px-2 py-1"
                        v-else-if="field.type === 'read_only'"
                      >
                        {{ field.value }}
                      </Tooltip>
                      <FormControl
                        v-else
                        type="text"
                        :value="lead.data[field.name]"
                        @change.stop="
                          updateLead(field.name, $event.target.value)
                        "
                        class="form-control"
                        :debounce="500"
                      />
                    </div>
                    <ExternalLinkIcon
                      v-if="
                        field.type === 'link' &&
                        field.link &&
                        lead.data[field.name]
                      "
                      class="h-4 w-4 shrink-0 cursor-pointer text-gray-600"
                      @click="field.link(lead.data[field.name])"
                    />
                  </div>
                </div>
              </transition>
            </Toggler>
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
      afterInsert: (doc) => updateField('organization', doc.name),
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
import ExternalLinkIcon from '@/components/Icons/ExternalLinkIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Toggler from '@/components/Toggler.vue'
import Activities from '@/components/Activities.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
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
const { getOrganization, getOrganizationOptions } = organizationsStore()
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

const detailSections = computed(() => {
  return [
    {
      label: 'Details',
      opened: true,
      fields: [
        {
          label: 'Organization',
          type: 'link',
          name: 'organization',
          placeholder: 'Select organization',
          options: getOrganizationOptions(),
          change: (data) => data && updateField('organization', data.value),
          create: (value, close) => {
            _organization.value.organization_name = value
            showOrganizationModal.value = true
            close()
          },
          link: () => {
            router.push({
              name: 'Organization',
              params: { organizationId: organization.value?.name },
            })
          },
        },
        {
          label: 'Website',
          type: 'read_only',
          name: 'website',
          value: organization.value?.website,
          tooltip:
            'It is a read only field, value is fetched from organization',
        },
        {
          label: 'Industry',
          type: 'read_only',
          name: 'industry',
          value: organization.value?.industry,
          tooltip:
            'It is a read only field, value is fetched from organization',
        },
        {
          label: 'Job title',
          type: 'data',
          name: 'job_title',
        },
        {
          label: 'Source',
          type: 'link',
          name: 'source',
          placeholder: 'Select source...',
          options: [
            { label: 'Advertisement', value: 'Advertisement' },
            { label: 'Web', value: 'Web' },
            { label: 'Others', value: 'Others' },
          ],
          change: (data) => updateField('source', data.value),
        },
      ],
    },
    {
      label: 'Person',
      opened: true,
      fields: [
        {
          label: 'Salutation',
          type: 'link',
          name: 'salutation',
          placeholder: 'Mr./Mrs./Ms.',
          options: [
            { label: 'Dr', value: 'Dr' },
            { label: 'Mr', value: 'Mr' },
            { label: 'Mrs', value: 'Mrs' },
            { label: 'Ms', value: 'Ms' },
            { label: 'Mx', value: 'Mx' },
            { label: 'Prof', value: 'Prof' },
            { label: 'Master', value: 'Master' },
            { label: 'Madam', value: 'Madam' },
            { label: 'Miss', value: 'Miss' },
          ],
          change: (data) => updateField('salutation', data.value),
        },
        {
          label: 'First name',
          type: 'data',
          name: 'first_name',
        },
        {
          label: 'Last name',
          type: 'data',
          name: 'last_name',
        },
        {
          label: 'Email',
          type: 'email',
          name: 'email',
        },
        {
          label: 'Mobile no.',
          type: 'phone',
          name: 'mobile_no',
        },
      ],
    },
  ]
})

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

function updateField(name, value) {
  updateLead(name, value, () => {
    lead.data[name] = value
  })
}
</script>

<style scoped>
:deep(.form-control input),
:deep(.form-control select),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}

:deep(.form-control button) {
  gap: 0;
}

:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control button svg) {
  color: white;
  width: 0;
}
</style>
