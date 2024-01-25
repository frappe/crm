<template>
  <LayoutHeader v-if="deal.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="deal.data._customActions"
        :actions="deal.data._customActions"
      />
      <component :is="deal.data._assignedTo?.length == 1 ? 'Button' : 'div'">
        <MultipleAvatar
          :avatars="deal.data._assignedTo"
          @click="showAssignmentModal = true"
        />
      </component>
      <Dropdown :options="statusOptions('deal', updateField)">
        <template #default="{ open }">
          <Button
            :label="deal.data.status"
            :class="getDealStatus(deal.data.status).colorClass"
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
    </template>
  </LayoutHeader>
  <div v-if="deal.data" class="flex h-full overflow-hidden">
    <Tabs v-model="tabIndex" v-slot="{ tab }" :tabs="tabs">
      <Activities
        ref="activities"
        doctype="CRM Deal"
        :title="tab.label"
        v-model:reload="reload"
        v-model="deal"
      />
    </Tabs>
    <div class="flex w-[352px] flex-col justify-between border-l">
      <div
        class="flex h-[41px] items-center border-b px-5 py-2.5 text-lg font-semibold"
      >
        About this Deal
      </div>
      <div class="flex items-center justify-start gap-5 border-b p-5">
        <Tooltip
          text="Organization logo"
          class="group relative h-[88px] w-[88px]"
        >
          <Avatar
            size="3xl"
            class="h-[88px] w-[88px]"
            :label="organization?.name"
            :image="organization?.organization_logo"
          />
        </Tooltip>
        <div class="flex flex-col gap-2.5 truncate">
          <Tooltip :text="organization?.name">
            <div class="truncate text-2xl font-medium">
              {{ organization?.name }}
            </div>
          </Tooltip>
          <div class="flex gap-1.5">
            <Tooltip text="Make a call...">
              <Button
                class="h-7 w-7"
                @click="
                  () =>
                    deal.data.mobile_no
                      ? makeCall(deal.data.mobile_no)
                      : errorMessage('No mobile number set')
                "
              >
                <PhoneIcon class="h-4 w-4" />
              </Button>
            </Tooltip>
            <Button class="h-7 w-7">
              <EmailIcon
                class="h-4 w-4"
                @click="
                  deal.data.email
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
                    deal.data.website
                      ? openWebsite(deal.data.website)
                      : errorMessage('No website set')
                  "
                />
              </Button>
            </Tooltip>
          </div>
        </div>
      </div>
      <SLASection
        v-if="deal.data.sla_status"
        v-model="deal.data"
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
                          company_name: deal.data.organization,
                        }
                        showContactModal = true
                        close()
                      }
                    "
                  >
                    <template #target="{ togglePopover }">
                      <Button
                        class="h-7 px-3"
                        label="Add Contact"
                        @click="togglePopover()"
                      >
                        <template #prefix>
                          <FeatherIcon name="plus" class="h-4" />
                        </template>
                      </Button>
                    </template>
                  </Link>
                </div>
              </template>
              <SectionFields
                v-if="section.fields"
                :fields="section.fields"
                v-model="deal.data"
                @update="updateField"
              />
              <div v-else>
                <div
                  v-if="section.contacts.length"
                  v-for="(contact, i) in section.contacts"
                  :key="contact.name"
                >
                  <div
                    class="px-2 pb-2.5"
                    :class="[i == 0 ? 'pt-5' : 'pt-2.5']"
                  >
                    <Section :is-opened="contact.opened">
                      <template #header="{ opened, toggle }">
                        <div
                          class="flex cursor-pointer items-center justify-between gap-2 pr-1 text-base leading-5 text-gray-700"
                        >
                          <div
                            class="flex h-7 items-center gap-2 truncate"
                            @click="toggle()"
                          >
                            <Avatar
                              :label="getContactByName(contact.name).full_name"
                              :image="getContactByName(contact.name).image"
                              size="md"
                            />
                            <div class="truncate">
                              {{ getContactByName(contact.name).full_name }}
                            </div>
                            <Badge
                              v-if="contact.is_primary"
                              class="ml-2"
                              variant="outline"
                              label="Primary"
                              theme="green"
                            />
                          </div>
                          <div class="flex items-center">
                            <Dropdown :options="contactOptions(contact)">
                              <Button variant="ghost">
                                <FeatherIcon
                                  name="more-horizontal"
                                  class="h-4 text-gray-600"
                                />
                              </Button>
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
                                class="h-4 w-4 text-gray-900 transition-all duration-300 ease-in-out"
                                :class="{ 'rotate-90': opened }"
                              />
                            </Button>
                          </div>
                        </div>
                      </template>
                      <div
                        class="flex flex-col gap-1.5 text-base text-gray-800"
                      >
                        <div class="flex items-center gap-3 pb-1.5 pl-1 pt-4">
                          <EmailIcon class="h-4 w-4" />
                          {{ getContactByName(contact.name).email_id }}
                        </div>
                        <div class="flex items-center gap-3 p-1 py-1.5">
                          <PhoneIcon class="h-4 w-4" />
                          {{ getContactByName(contact.name).mobile_no }}
                        </div>
                      </div>
                    </Section>
                  </div>
                  <div
                    v-if="i != section.contacts.length - 1"
                    class="mx-2 h-px border-t border-gray-200"
                  />
                </div>
                <div
                  v-else
                  class="flex h-20 items-center justify-center text-base text-gray-600"
                >
                  No contacts added
                </div>
              </div>
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
  <ContactModal
    v-model="showContactModal"
    :contact="_contact"
    :options="{
      redirect: false,
      afterInsert: (doc) => addContact(doc.name),
    }"
  />
  <AssignmentModal
    v-if="deal.data"
    :doc="deal.data"
    v-model="showAssignmentModal"
    v-model:assignees="deal.data._assignedTo"
  />
</template>
<script setup>
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import SuccessIcon from '@/components/Icons/SuccessIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
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
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
} from 'frappe-ui'
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'

const { $dialog, makeCall } = globalStore()
const { getContactByName, contacts } = contactsStore()
const { organizations, getOrganization } = organizationsStore()
const { statusOptions, getDealStatus } = statusesStore()
const { getDefaultView } = viewsStore()
const router = useRouter()

const props = defineProps({
  dealId: {
    type: String,
    required: true,
  },
})

const deal = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal',
  params: { name: props.dealId },
  cache: ['deal', props.dealId],
  auto: true,
  onSuccess: (data) => {
    setupAssignees(data)
    setupCustomActions(data, {
      doc: data,
      $dialog,
      router,
      updateField,
      createToast,
      deleteDoc: deleteDeal,
      call,
    })
  },
})

const reload = ref(false)
const showOrganizationModal = ref(false)
const showAssignmentModal = ref(false)
const _organization = ref({})

const organization = computed(() => {
  return deal.data?.organization && getOrganization(deal.data.organization)
})

function updateDeal(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

  if (validateRequired(fieldname, value)) return

  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'CRM Deal',
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
      callback?.()
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

function validateRequired(fieldname, value) {
  let meta = deal.data.all_fields || {}
  if (meta[fieldname]?.reqd && !value) {
    createToast({
      title: 'Error Updating Deal',
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
  let route = { name: 'Deals' }
  if (defaultView?.route_name == 'Deals' && defaultView?.is_view) {
    route = { name: 'Deals', query: { view: defaultView.name } }
  }
  let items = [{ label: 'Deals', route: route }]
  items.push({
    label: organization.value?.name,
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

const detailSections = computed(() => {
  let data = deal.data
  if (!data) return []
  return getParsedFields(data.doctype_fields, data.contacts)
})

function getParsedFields(sections, contacts) {
  sections.forEach((section) => {
    if (section.name == 'contacts_tab') {
      delete section.fields
      section.contacts =
        contacts?.map((contact) => {
          return {
            name: contact.contact,
            is_primary: contact.is_primary,
            opened: false,
          }
        }) || []
    } else {
      section.fields.forEach((field) => {
        if (
          !deal.data.organization &&
          ['website', 'territory', 'annual_revenue'].includes(field.name)
        ) {
          field.hidden = true
        }
        if (field.name == 'organization') {
          field.create = (value, close) => {
            _organization.value.organization_name = value
            showOrganizationModal.value = true
            close()
          }
          field.link = (org) =>
            router.push({
              name: 'Organization',
              params: { organizationId: org },
            })
        }
      })
    }
  })
  return sections
}

const showContactModal = ref(false)
const _contact = ref({})

function contactOptions(contact) {
  let options = [
    {
      label: 'Delete',
      icon: 'trash-2',
      onClick: () => removeContact(contact.name),
    },
  ]

  if (!contact.is_primary) {
    options.push({
      label: 'Set as Primary Contact',
      icon: h(SuccessIcon, { class: 'h-4 w-4' }),
      onClick: () => setPrimaryContact(contact.name),
    })
  }

  return options
}

async function addContact(contact) {
  let d = await call('crm.fcrm.doctype.crm_deal.crm_deal.add_contact', {
    deal: props.dealId,
    contact,
  })
  if (d) {
    deal.reload()
    createToast({
      title: 'Contact added',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

async function removeContact(contact) {
  let d = await call('crm.fcrm.doctype.crm_deal.crm_deal.remove_contact', {
    deal: props.dealId,
    contact,
  })
  if (d) {
    deal.reload()
    createToast({
      title: 'Contact removed',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

async function setPrimaryContact(contact) {
  let d = await call('crm.fcrm.doctype.crm_deal.crm_deal.set_primary_contact', {
    deal: props.dealId,
    contact,
  })
  if (d) {
    await contacts.reload()
    deal.reload()
    createToast({
      title: 'Primary contact set',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

function updateField(name, value, callback) {
  updateDeal(name, value, () => {
    deal.data[name] = value
    callback?.()
  })
}

async function deleteDeal(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Deal',
    name,
  })
  router.push({ name: 'Deals' })
}

const activities = ref(null)

function openEmailBox() {
  activities.value.emailBox.show = true
}
</script>
