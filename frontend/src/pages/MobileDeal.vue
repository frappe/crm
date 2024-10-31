<template>
  <LayoutHeader v-if="deal.data">
    <header
      class="relative flex h-10.5 items-center justify-between gap-2 py-2.5 pl-2"
    >
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
      <div class="absolute right-0">
        <Dropdown :options="statusOptions('deal', updateField, customStatuses)">
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
      </div>
    </header>
  </LayoutHeader>
  <div
    v-if="deal.data"
    class="flex h-12 items-center justify-between gap-2 border-b px-3 py-2.5"
  >
    <component :is="deal.data._assignedTo?.length == 1 ? 'Button' : 'div'">
      <MultipleAvatar
        :avatars="deal.data._assignedTo"
        @click="showAssignmentModal = true"
      />
    </component>
    <div class="flex items-center gap-2">
      <CustomActions v-if="customActions" :actions="customActions" />
    </div>
  </div>
  <div v-if="deal.data" class="flex h-full overflow-hidden">
    <Tabs
      v-model="tabIndex"
      v-slot="{ tab }"
      :tabs="tabs"
      tablistClass="!px-3"
      class="overflow-auto"
    >
      <div v-if="tab.name == 'Details'">
        <SLASection
          v-if="deal.data.sla_status"
          v-model="deal.data"
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
              class="flex flex-col px-2 py-3 sm:p-3"
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
                          variant="ghost"
                          icon="plus"
                          @click="togglePopover()"
                        />
                      </template>
                    </Link>
                  </div>
                </template>
                <SectionFields
                  v-if="section.fields"
                  :fields="section.fields"
                  :isLastSection="i == fieldsLayout.data.length - 1"
                  v-model="deal.data"
                  @update="updateField"
                />
                <div v-else>
                  <div
                    v-if="
                      dealContacts?.loading && dealContacts?.data?.length == 0
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
                                <Button
                                  icon="more-horizontal"
                                  class="text-gray-600"
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
      <Activities
        v-else
        doctype="CRM Deal"
        :tabs="tabs"
        v-model:reload="reload"
        v-model:tabIndex="tabIndex"
        v-model="deal"
      />
    </Tabs>
  </div>
  <OrganizationModal
    v-model="showOrganizationModal"
    v-model:organization="_organization"
    :options="{
      redirect: false,
      afterInsert: (doc) => updateField('organization', doc.name),
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
    v-if="showAssignmentModal"
    v-model="showAssignmentModal"
    v-model:assignees="deal.data._assignedTo"
    :doc="deal.data"
    doctype="CRM Deal"
  />
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import SuccessIcon from '@/components/Icons/SuccessIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import Link from '@/components/Controls/Link.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import { createToast, setupAssignees, setupCustomizations } from '@/utils'
import { getView } from '@/utils/view'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import {
  whatsappEnabled,
  callEnabled,
  isMobileView,
} from '@/composables/settings'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import {
  createResource,
  Dropdown,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
} from 'frappe-ui'
import { ref, computed, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { $dialog, $socket } = globalStore()
const { statusOptions, getDealStatus } = statusesStore()
const route = useRoute()
const router = useRouter()

const props = defineProps({
  dealId: {
    type: String,
    required: true,
  },
})

const customActions = ref([])
const customStatuses = ref([])

const deal = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal',
  params: { name: props.dealId },
  cache: ['deal', props.dealId],
  onSuccess: async (data) => {
    if (data.organization) {
      organization.update({
        params: { doctype: 'CRM Organization', name: data.organization },
      })
      organization.fetch()
    }

    let obj = {
      doc: data,
      $dialog,
      $socket,
      router,
      updateField,
      createToast,
      deleteDoc: deleteDeal,
      resource: {
        deal,
        dealContacts,
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

const organization = createResource({
  url: 'frappe.client.get',
  onSuccess: (data) => (deal.data._organizationObj = data),
})

onMounted(() => {
  if (deal.data) return
  deal.fetch()
})

const reload = ref(false)
const showOrganizationModal = ref(false)
const showAssignmentModal = ref(false)
const _organization = ref({})

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
  let meta = deal.data.fields_meta || {}
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

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Deal')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Deals',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: organization.data?.name || __('Untitled'),
    route: { name: 'Deal', params: { dealId: deal.data.name } },
  })
  return items
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Details',
      label: __('Details'),
      icon: DetailsIcon,
      condition: () => isMobileView.value,
    },
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
const { tabIndex } = useActiveTabManager(tabs, 'lastDealTab')

const fieldsLayout = createResource({
  url: 'crm.api.doc.get_sidebar_fields',
  cache: ['fieldsLayout', props.dealId],
  params: { doctype: 'CRM Deal', name: props.dealId },
  auto: true,
  transform: (data) => getParsedFields(data),
})

function getParsedFields(sections) {
  sections.forEach((section) => {
    if (section.name == 'contacts_section') return
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
    dealContacts.reload()
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
    dealContacts.reload()
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
    dealContacts.reload()
    createToast({
      title: __('Primary contact set'),
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

const dealContacts = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal_contacts',
  params: { name: props.dealId },
  cache: ['deal_contacts', props.dealId],
  auto: true,
  onSuccess: (data) => {
    let contactSection = fieldsLayout.data?.find(
      (section) => section.name == 'contacts_section',
    )
    if (!contactSection) return
    contactSection.contacts = data.map((contact) => {
      return {
        name: contact.name,
        full_name: contact.full_name,
        email: contact.email,
        mobile_no: contact.mobile_no,
        image: contact.image,
        is_primary: contact.is_primary,
        opened: false,
      }
    })
  },
})

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
</script>
