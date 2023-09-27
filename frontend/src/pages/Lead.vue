<template>
  <LayoutHeader v-if="lead.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Autocomplete
        :options="activeAgents"
        :value="getUser(lead.data.lead_owner).full_name"
        @change="(option) => updateAssignedAgent(option.email)"
        placeholder="Lead owner"
      >
        <template #prefix>
          <UserAvatar class="mr-2" :user="lead.data.lead_owner" size="sm" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.email" size="sm" />
        </template>
      </Autocomplete>
      <Dropdown :options="statusDropdownOptions(lead.data, 'lead', updateLead)">
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
      <Button
        label="Convert to deal"
        variant="solid"
        @click="convertToDeal()"
      />
    </template>
  </LayoutHeader>
  <div v-if="lead?.data" class="flex h-full overflow-hidden">
    <TabGroup as="div" class="flex flex-1 flex-col" @change="onTabChange">
      <TabList class="relative flex items-center gap-6 border-b pl-5">
        <Tab
          ref="tabRef"
          as="template"
          v-for="tab in tabs"
          :key="tab.label"
          v-slot="{ selected }"
        >
          <button
            class="-mb-[1px] flex items-center gap-2 border-b border-transparent py-2.5 text-base text-gray-600 transition-all duration-300 ease-in-out hover:border-gray-400 hover:text-gray-900"
            :class="{ 'text-gray-900': selected }"
          >
            <component v-if="tab.icon" :is="tab.icon" class="h-5" />
            {{ tab.label }}
          </button>
        </Tab>
        <div
          ref="indicator"
          class="absolute -bottom-[1px] h-[1px] w-[82px] bg-gray-900"
          :style="{ left: `${indicatorLeftValue}px` }"
        />
      </TabList>
      <TabPanels class="flex flex-1 overflow-hidden">
        <TabPanel
          class="flex flex-1 flex-col overflow-y-auto"
          v-for="tab in tabs"
          :key="tab.label"
        >
          <Activities
            :title="tab.label"
            v-model:reload="reload"
            v-model="lead"
          />
        </TabPanel>
      </TabPanels>
    </TabGroup>
    <div class="flex w-[352px] flex-col justify-between border-l">
      <div
        class="flex h-[41px] items-center border-b px-5 py-2.5 text-lg font-semibold"
      >
        About this lead
      </div>
      <FileUploader @success="changeLeadImage" :validateFile="validateFile">
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 p-5">
            <div class="group relative h-[88px] w-[88px]">
              <Avatar
                size="3xl"
                class="h-[88px] w-[88px]"
                :label="lead.data.first_name"
                :image="lead.data.image"
              />
              <Dropdown
                :options="[
                  {
                    icon: 'upload',
                    label: lead.data.image ? 'Change photo' : 'Upload photo',
                    onClick: openFileSelector,
                  },
                  {
                    icon: 'trash-2',
                    label: 'Remove photo',
                    onClick: () => {
                      lead.data.image = ''
                      updateLead('image', '')
                    },
                  },
                ]"
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0 left-0 right-0 flex h-11 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                </div>
              </Dropdown>
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
            v-for="(section, i) in detailSections"
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
                    <div class="w-[106px] text-gray-600">
                      {{ field.label }}
                    </div>
                    <div class="flex-1">
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
                      />
                      <Autocomplete
                        v-else-if="field.type === 'user'"
                        :options="activeAgents"
                        :value="getUser(lead.data[field.name]).full_name"
                        @change="(option) => updateAssignedAgent(option.email)"
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
                      </Autocomplete>
                      <Dropdown
                        v-else-if="field.type === 'dropdown'"
                        :options="
                          statusDropdownOptions(lead.data, 'lead', updateLead)
                        "
                        class="w-full flex-1"
                      >
                        <template #default="{ open }">
                          <Button
                            :label="lead.data[field.name]"
                            class="w-full justify-between"
                          >
                            <template #prefix>
                              <IndicatorIcon
                                :class="
                                  leadStatuses[lead.data[field.name]].color
                                "
                              />
                            </template>
                            <template #default>{{
                              lead.data[field.name]
                            }}</template>
                            <template #suffix>
                              <FeatherIcon
                                :name="open ? 'chevron-up' : 'chevron-down'"
                                class="h-4 text-gray-600"
                              />
                            </template>
                          </Button>
                        </template>
                      </Dropdown>
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
                  </div>
                </div>
              </transition>
            </Toggler>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Toggler from '@/components/Toggler.vue'
import Activities from '@/components/Activities.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue'
import { TransitionPresets, useTransition } from '@vueuse/core'
import {
  leadStatuses,
  statusDropdownOptions,
  openWebsite,
  createToast,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import {
  createResource,
  FileUploader,
  ErrorMessage,
  FeatherIcon,
  Autocomplete,
  FormControl,
  Dropdown,
  Tooltip,
  Avatar,
} from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import CameraIcon from '../components/Icons/CameraIcon.vue'

const { getUser, users } = usersStore()
const { contacts } = contactsStore()
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

function updateLead(fieldname, value) {
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
      if (fieldname == 'is_deal') {
        router.push({ name: 'Deal', params: { dealId: lead.data.name } })
      }
      lead.reload()
      contacts.reload()
      reload.value = true
      createToast({
        title: 'Lead updated',
        icon: 'check',
        iconClasses: 'text-green-600',
      })
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
    label: 'Notes',
    icon: NoteIcon,
  },
]

function changeLeadImage(file) {
  lead.data.image = file.file_url
  updateLead('image', file.file_url)
}

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return 'Only PNG and JPG images are allowed'
  }
}

const tabRef = ref([])
const indicator = ref(null)

let indicatorLeft = ref(20)
const indicatorLeftValue = useTransition(indicatorLeft, {
  duration: 250,
  ease: TransitionPresets.easeOutCubic,
})

function onTabChange(index) {
  const selectedTab = tabRef.value[index].el
  indicator.value.style.width = `${selectedTab.offsetWidth}px`
  indicatorLeft.value = selectedTab.offsetLeft
}

const detailSections = computed(() => {
  return [
    {
      label: 'Details',
      opened: true,
      fields: [
        {
          label: 'Organization',
          type: 'data',
          name: 'organization_name',
        },
        {
          label: 'Website',
          type: 'data',
          name: 'website',
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
          change: (data) => {
            lead.data.source = data.value
            updateLead('source', data.value)
          },
        },
        {
          label: 'Industry',
          type: 'link',
          name: 'industry',
          placeholder: 'Select industry...',
          options: [
            { label: 'Advertising', value: 'Advertising' },
            { label: 'Agriculture', value: 'Agriculture' },
            { label: 'Banking', value: 'Banking' },
            { label: 'Others', value: 'Others' },
          ],
          change: (data) => {
            lead.data.industry = data.value
            updateLead('industry', data.value)
          },
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
          change: (data) => {
            lead.data.salutation = data.value
            updateLead('salutation', data.value)
          },
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

const activeAgents = computed(() => {
  const nonAgents = ['Administrator', 'admin@example.com', 'Guest']
  return users.data
    .filter((user) => !nonAgents.includes(user.name))
    .sort((a, b) => a.full_name - b.full_name)
    .map((user) => {
      return {
        label: user.full_name,
        value: user.email,
        ...user,
      }
    })
})

function convertToDeal() {
  lead.data.status = 'Qualified'
  lead.data.is_deal = 1
  updateLead('is_deal', 1)
}

function updateAssignedAgent(email) {
  lead.data.lead_owner = email
  updateLead('lead_owner', email)
}
</script>

<style scoped>
:deep(.form-control input),
:deep(.form-control select),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}

:deep(.form-control button svg) {
  color: white;
}
</style>
