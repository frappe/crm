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
        :title="tab.name"
        v-model:reload="reload"
        v-model:tabIndex="tabIndex"
        v-model="deal"
      />
    </Tabs>
    <div class="flex w-[352px] flex-col justify-between border-l">
      <div
        class="flex h-10.5 items-center border-b px-5 py-2.5 text-lg font-semibold"
      >
        {{ __('About this Deal') }}
      </div>
      <div class="flex items-center justify-start gap-5 border-b p-5">
        <Tooltip :text="__('Organization logo')">
          <div class="group relative h-[88px] w-[88px]">
            <Avatar
              size="3xl"
              class="h-[88px] w-[88px]"
              :label="organization?.name"
              :image="organization?.organization_logo"
            />
          </div>
        </Tooltip>
        <div class="flex flex-col gap-2.5 truncate">
          <Tooltip :text="organization?.name">
            <div class="truncate text-2xl font-medium">
              {{ organization?.name }}
            </div>
          </Tooltip>
          <div class="flex gap-1.5">
            <Tooltip v-if="callEnabled" :text="__('Make a call')">
              <Button class="h-7 w-7" @click="triggerCall">
                <PhoneIcon class="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip :text="__('Send an email')">
              <Button class="h-7 w-7">
                <EmailIcon
                  class="h-4 w-4"
                  @click="
                    deal.data.email
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
                    deal.data.website
                      ? openWebsite(deal.data.website)
                      : errorMessage(__('No website set'))
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
                        :label="__('Add Contact')"
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
                  v-if="
                    deal_contacts?.loading && deal_contacts?.data?.length == 0
                  "
                  class="flex min-h-20 flex-1 items-center justify-center gap-3 text-base text-gray-500"
                >
                  <LoadingIndicator class="h-4 w-4" />
                  <span>{{ __('Loading...') }}</span>
                </div>
                <div
                  v-else-if="section.contacts.length"
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
                              :label="contact.full_name"
                              :image="contact.image"
                              size="md"
                            />
                            <div class="truncate">
                              {{ contact.full_name }}
                            </div>
                            <Badge
                              v-if="contact.is_primary"
                              class="ml-2"
                              variant="outline"
                              :label="__('Primary')"
                              theme="green"
                            />
                          </div>
                          <div class="flex items-center">
                            <Dropdown :options="contactOptions(contact.name)">
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
                    v-if="i != section.contacts.length - 1"
                    class="mx-2 h-px border-t border-gray-200"
                  />
                </div>
                <div
                  v-else
                  class="flex h-20 items-center justify-center text-base text-gray-600"
                >
                  {{ __('No contacts added') }}
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
    v-model:organization="_organization"
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
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
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
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { whatsappEnabled, callEnabled } from '@/stores/settings'
import {
  createResource,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
} from 'frappe-ui'
import { ref, computed, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const { $dialog, makeCall } = globalStore()
const { organizations, getOrganization } = organizationsStore()
const { statusOptions, getDealStatus } = statusesStore()
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

onMounted(() => {
  if (deal.data) return
  deal.fetch()
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
      reload.value = true
      createToast({
        title: __('Deal updated'),
        icon: 'check',
        iconClasses: 'text-green-600',
      })
      callback?.()
    },
    onError: (err) => {
      createToast({
        title: __('Error updating deal'),
        text: __(err.messages?.[0]),
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
      title: __('Error Updating Deal'),
      text: __('{0} is a required field', [meta[fieldname].label]),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return true
  }
  return false
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Deals'), route: { name: 'Deals' } }]
  items.push({
    label: organization.value?.name,
    route: { name: 'Deal', params: { dealId: deal.data.name } },
  })
  return items
})

const tabIndex = ref(0)
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
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const detailSections = computed(() => {
  let data = deal.data
  if (!data) return []
  return getParsedFields(data.doctype_fields, deal_contacts.data)
})

function getParsedFields(sections, contacts) {
  sections.forEach((section) => {
    if (section.name == 'contacts_tab') {
      delete section.fields
      section.contacts =
        contacts?.map((contact) => {
          return {
            name: contact.name,
            full_name: contact.full_name,
            email: contact.email,
            mobile_no: contact.mobile_no,
            image: contact.image,
            is_primary: contact.is_primary,
            opened: false,
          }
        }) || []
    } else {
      section.fields.forEach((field) => {
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
      label: __('Delete'),
      icon: 'trash-2',
      onClick: () => removeContact(contact),
    },
  ]

  if (!contact.is_primary) {
    options.push({
      label: __('Set as Primary Contact'),
      icon: h(SuccessIcon, { class: 'h-4 w-4' }),
      onClick: () => setPrimaryContact(contact),
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
    deal_contacts.reload()
    createToast({
      title: __('Contact added'),
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
    deal_contacts.reload()
    createToast({
      title: __('Contact removed'),
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
    deal_contacts.reload()
    createToast({
      title: __('Primary contact set'),
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

const deal_contacts = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal_contacts',
  params: { name: props.dealId },
  cache: ['deal_contacts', props.dealId],
  auto: true,
})

function triggerCall() {
  let primaryContact = deal_contacts.data?.find((c) => c.is_primary)
  let mobile_no = primaryContact.mobile_no || null

  if (!primaryContact) {
    errorMessage(__('No primary contact set'))
    return
  }

  if (!mobile_no) {
    errorMessage(__('No mobile number set'))
    return
  }

  makeCall(mobile_no)
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
