<template>
  <LayoutHeader v-if="deal.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Autocomplete
        :options="activeAgents"
        :value="getUser(deal.data.lead_owner).full_name"
        @change="(option) => updateAssignedAgent(option.email)"
        placeholder="Deal owner"
      >
        <template #prefix>
          <UserAvatar class="mr-2" :user="deal.data.lead_owner" size="sm" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.email" size="sm" />
        </template>
      </Autocomplete>
      <Dropdown :options="statusDropdownOptions(deal.data, 'deal', updateDeal)">
        <template #default="{ open }">
          <Button :label="deal.data.deal_status">
            <template #prefix>
              <IndicatorIcon
                :class="dealStatuses[deal.data.deal_status].color"
              />
            </template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
            /></template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </LayoutHeader>
  <div v-if="deal.data" class="flex h-full overflow-hidden">
    <Tabs v-model="tabIndex" v-slot="{ tab }" :tabs="tabs">
      <Activities :title="tab.label" v-model:reload="reload" v-model="deal" />
    </Tabs>
    <div class="flex w-[352px] flex-col justify-between border-l">
      <div
        class="flex h-[41px] items-center border-b px-5 py-2.5 text-lg font-semibold"
      >
        About this deal
      </div>
      <FileUploader @success="changeDealImage" :validateFile="validateFile">
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 border-b p-5">
            <div class="group relative h-[88px] w-[88px]">
              <Avatar
                size="3xl"
                class="h-[88px] w-[88px]"
                :label="deal.data.organization_name"
                :image="deal.data.organization_logo"
              />
              <Dropdown
                :options="[
                  {
                    icon: 'upload',
                    label: deal.data.organization_logo
                      ? 'Change image'
                      : 'Upload image',
                    onClick: openFileSelector,
                  },
                  {
                    icon: 'trash-2',
                    label: 'Remove image',
                    onClick: () => {
                      deal.data.organization_logo = ''
                      updateDeal('organization_logo', '')
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
              <Tooltip :text="deal.data.organization_name">
                <div class="truncate text-2xl font-medium">
                  {{ deal.data.organization_name }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Tooltip text="Make a call...">
                  <Button
                    class="h-7 w-7"
                    @click="() => makeCall(deal.data.mobile_no)"
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
                      @click="openWebsite(deal.data.website)"
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
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== detailSections.length - 1 }"
          >
            <Toggler :is-opened="section.opened" v-slot="{ opened, toggle }">
              <div
                class="flex max-w-fit cursor-pointer items-center gap-2 pl-2 pr-3 text-base font-semibold leading-5"
                @click="toggle()"
              >
                <FeatherIcon
                  name="chevron-right"
                  class="h-4 text-gray-600 transition-all duration-300 ease-in-out"
                  :class="{ 'rotate-90': opened }"
                />
                {{ section.label }}
              </div>
              <transition
                enter-active-class="duration-300 ease-in"
                leave-active-class="duration-300 ease-[cubic-bezier(0, 1, 0.5, 1)]"
                enter-to-class="max-h-[200px] overflow-hidden"
                leave-from-class="max-h-[200px] overflow-hidden"
                enter-from-class="max-h-0 overflow-hidden"
                leave-to-class="max-h-0 overflow-hidden"
              >
                <div v-if="opened" class="flex flex-col gap-1.5">
                  <div
                    v-for="field in section.fields"
                    :key="field.label"
                    class="flex items-center gap-2 px-3 text-base leading-5 first:mt-3"
                  >
                    <div class="w-[106px] text-gray-600">
                      {{ field.label }}
                    </div>
                    <div class="flex-1">
                      <FormControl
                        v-if="field.type === 'select'"
                        type="select"
                        :options="field.options"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control cursor-pointer [&_select]:cursor-pointer"
                      >
                        <template #prefix>
                          <IndicatorIcon
                            :class="dealStatuses[deal.data[field.name]].color"
                          />
                        </template>
                      </FormControl>
                      <FormControl
                        v-else-if="field.type === 'email'"
                        type="email"
                        class="form-control"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                      />
                      <Autocomplete
                        v-else-if="field.type === 'link'"
                        :value="deal.data[field.name]"
                        :options="field.options"
                        @change="(e) => field.change(e)"
                        :placeholder="field.placeholder"
                        class="form-control"
                      />
                      <Autocomplete
                        v-else-if="field.type === 'user'"
                        :options="activeAgents"
                        :value="getUser(deal.data[field.name]).full_name"
                        @change="(option) => updateAssignedAgent(option.email)"
                        class="form-control"
                        :placeholder="deal.placeholder"
                      >
                        <template #target="{ togglePopover }">
                          <Button
                            variant="ghost"
                            @click="togglePopover()"
                            :label="getUser(deal.data[field.name]).full_name"
                            class="w-full !justify-start"
                          >
                            <template #prefix>
                              <UserAvatar
                                :user="deal.data[field.name]"
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
                          statusDropdownOptions(deal.data, 'deal', updateDeal)
                        "
                        class="w-full flex-1"
                      >
                        <template #default="{ open }">
                          <Button
                            :label="deal.data[field.name]"
                            class="w-full justify-between"
                          >
                            <template #prefix>
                              <IndicatorIcon
                                :class="
                                  dealStatuses[deal.data[field.name]].color
                                "
                              />
                            </template>
                            <template #default>{{
                              deal.data[field.name]
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
                        v-else-if="field.type === 'date'"
                        type="date"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control"
                      />
                      <FormControl
                        v-else-if="field.type === 'number'"
                        type="number"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control"
                      />
                      <FormControl
                        v-else-if="field.type === 'tel'"
                        type="tel"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control"
                      />
                      <FormControl
                        v-else
                        type="text"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control"
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
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Toggler from '@/components/Toggler.vue'
import Activities from '@/components/Activities.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import {
  dealStatuses,
  statusDropdownOptions,
  openWebsite,
  createToast,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import {
  createResource,
  FeatherIcon,
  FileUploader,
  ErrorMessage,
  Autocomplete,
  FormControl,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
} from 'frappe-ui'
import { ref, computed } from 'vue'

const { getUser, users } = usersStore()
const { contacts } = contactsStore()

const props = defineProps({
  dealId: {
    type: String,
    required: true,
  },
})

const deal = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_lead',
  params: { name: props.dealId },
  cache: ['deal', props.dealId],
  auto: true,
})

const reload = ref(false)

function updateDeal(fieldname, value) {
  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'CRM Lead',
      name: props.dealId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      deal.reload()
      contacts.reload()
      reload.value = true
      createToast({
        title: 'Deal updated',
        icon: 'check',
        iconClasses: 'text-green-600',
      })
    },
    onError: (err) => {
      createToast({
        title: 'Error updating deal',
        text: err.messages?.[0],
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  })
}

const breadcrumbs = computed(() => {
  let items = [{ label: 'Deals', route: { name: 'Deals' } }]
  items.push({
    label: deal.data.organization_name,
    route: { name: 'Deal', params: { dealId: deal.data.name } },
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

function changeDealImage(file) {
  deal.data.organization_logo = file.file_url
  updateDeal('organization_logo', file.file_url)
}

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return 'Only PNG and JPG images are allowed'
  }
}

const detailSections = computed(() => {
  return [
    {
      label: 'Organization',
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
          label: 'Amount',
          type: 'number',
          name: 'annual_revenue',
        },
        {
          label: 'Close date',
          type: 'date',
          name: 'close_date',
        },
        {
          label: 'Probability',
          type: 'data',
          name: 'probability',
        },
        {
          label: 'Next step',
          type: 'data',
          name: 'next_step',
        },
      ],
    },
    {
      label: 'Contacts',
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
            deal.data.salutation = data.value
            updateDeal('salutation', data.value)
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
          type: 'tel',
          name: 'mobile_no',
        },
      ],
    },
  ]
})

const activeAgents = computed(() => {
  const nonAgents = ['Administrator', 'Guest']
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

function updateAssignedAgent(email) {
  deal.data.lead_owner = email
  updateDeal('lead_owner', email)
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
