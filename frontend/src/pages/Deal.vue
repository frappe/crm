<template>
  <LayoutHeader v-if="deal.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <FormControl
        type="autocomplete"
        :options="activeAgents"
        :value="getUser(deal.data.deal_owner).full_name"
        @change="(option) => updateField('deal_owner', option.email)"
        placeholder="Deal owner"
      >
        <template #prefix>
          <UserAvatar class="mr-2" :user="deal.data.deal_owner" size="sm" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.email" size="sm" />
        </template>
      </FormControl>
      <Dropdown
        :options="statusDropdownOptions(deal.data, 'deal', updateField)"
      >
        <template #default="{ open }">
          <Button :label="deal.data.status">
            <template #prefix>
              <IndicatorIcon :class="dealStatuses[deal.data.status].color" />
            </template>
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
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
        About this deal
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
        </div>
      </div>
      <div class="flex flex-1 flex-col justify-between overflow-hidden">
        <div class="flex flex-col overflow-y-auto">
          <div
            v-for="(section, i) in detailSections.data"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== detailSections.data.length - 1 }"
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
                        label="Add contact"
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
                            class="flex h-7 items-center gap-2"
                            @click="toggle()"
                          >
                            <Avatar
                              :label="getContactByName(contact.name).full_name"
                              :image="getContactByName(contact.name).image"
                              size="md"
                            />
                            {{ getContactByName(contact.name).full_name }}
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
                              <ExternalLinkIcon class="h-4 w-4" />
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
</template>
<script setup>
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import ExternalLinkIcon from '@/components/Icons/ExternalLinkIcon.vue'
import SuccessIcon from '@/components/Icons/SuccessIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import Link from '@/components/Controls/Link.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import {
  dealStatuses,
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
  FeatherIcon,
  FormControl,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  Badge,
} from 'frappe-ui'
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'

const { getUser } = usersStore()
const { getContactByName, contacts } = contactsStore()
const { organizations, getOrganization } = organizationsStore()
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
})

const reload = ref(false)
const showOrganizationModal = ref(false)
const _organization = ref({})

function updateDeal(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

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

const breadcrumbs = computed(() => {
  let items = [{ label: 'Deals', route: { name: 'Deals' } }]
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

const detailSections = createResource({
  url: 'crm.api.doc.get_doctype_fields',
  params: { doctype: 'CRM Deal' },
  cache: 'dealFields',
  auto: true,
  transform: (data) => {
    return getParsedFields(data)
  },
})

function getParsedFields(sections) {
  sections.forEach((section) => {
    section.fields.forEach((field) => {
      if (['website', 'annual_revenue'].includes(field.name)) {
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
            params: { organizationId: deal.data.organization },
          })
      }
    })
  })

  let contactSection = {
    label: 'Contacts',
    opened: true,
    contacts: deal.data.contacts.map((contact) => {
      return {
        name: contact.contact,
        is_primary: contact.is_primary,
        opened: false,
      }
    }),
  }

  return [...sections, contactSection]
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
      label: 'Set as primary contact',
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
    await contacts.reload()
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
    contacts.reload()
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

const organization = computed(() => {
  return getOrganization(deal.data.organization)
})

function updateField(name, value, callback) {
  updateDeal(name, value, () => {
    deal.data[name] = value
    callback?.()
  })
}
</script>
