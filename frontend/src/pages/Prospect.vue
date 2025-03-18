<template>
  <LayoutHeader v-if="prospect.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <Dropdown
        v-slot="{ open }"
        :button= "__('Create')"
        :options="[
          {
            label: __('Opportunity'),
            onClick: createOpportunity
          },
          {
            label: __('Customer'),
            onClick: createCustomer
          },
        ]"
        @click.stop
      >
        <Button :label="'Create'">
          <template #suffix>
            <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-4" />
          </template>
        </Button>
      </Dropdown>
    </template>
  </LayoutHeader>
  <div ref="parentRef" class="flex h-full">
    <Resizer
      v-if="prospect.doc"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="flex flex-col gap-2 truncate">
                  <div class="truncate text-2xl font-medium text-ink-gray-9">
                    <span>{{ prospect.doc.name }}</span>
                  </div>
                  <div
                    v-if="prospect.doc.website"
                    class="flex items-center gap-1.5 text-base text-ink-gray-8"
                  >
                    <WebsiteIcon class="size-4" />
                    <span>{{ website(prospect.doc.website) }}</span>
                  </div>
                  <ErrorMessage :message="__(error)" />
                </div>
              </div>
              <div class="flex gap-1.5">
                <Button
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  @click="deleteProspect"
                >
                  <template #prefix>
                    <FeatherIcon name="trash-2" class="h-4 w-4" />
                  </template>
                </Button>
                <Tooltip :text="__('Open website')">
                  <div>
                    <Button @click="openWebsite">
                      <FeatherIcon name="link" class="h-4 w-4" />
                    </Button>
                  </div>
                </Tooltip>
              </div>
            </div>
      </div>
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
              <template #actions>
                <Button
                  v-if="i == 0 && isManager()"
                  variant="ghost"
                  class="w-7"
                  @click="showSidePanelModal = true"
                >
                  <EditIcon class="h-4 w-4" />
                </Button>
              </template>
              <SectionFields
                v-if="section.fields"
                :fields="section.fields"
                :isLastSection="i == fieldsLayout.data.length - 1"
                v-model="prospect.doc"
                @update="updateField"
              />
            </Section>
          </div>
        </div>
      </div>
    </Resizer>
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-item="{ tab, selected }">
        <button
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-ink-gray-5 duration-300 ease-in-out hover:border-gray-400 hover:text-ink-gray-9"
          :class="{ 'text-ink-gray-9': selected }"
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ __(tab.label) }}
          <Badge
            class="group-hover:bg-surface-gray-9"
            :class="[selected ? 'bg-surface-gray-9' : 'bg-surface-gray-5']"
            variant="solid"
            theme="gray"
            size="sm"
          >
            {{ tab.count }}
          </Badge>
        </button>
      </template>
      <template #tab-panel="{ tab }">
        <OpportunitiesListView
          class="mt-4"
          v-if="tab.label === 'Opportunities' && rows.length"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <ContactsListView
          class="mt-4"
          v-if="tab.label === 'Contacts' && rows.length"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <AddressesListView
          class="mt-4"
          v-if="tab.label === 'Addresses' && rows.length"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <div
          v-if="!rows.length"
          class="grid flex-1 place-items-center text-xl font-medium text-ink-gray-4"
        >
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.icon" class="!h-10 !w-10" />
            <div>{{ __('No {0} Found', [__(tab.label)]) }}</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
  <SidePanelModal
    v-if="showSidePanelModal"
    v-model="showSidePanelModal"
    doctype="Prospect"
    @reload="() => fieldsLayout.reload()"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Prospect"
  />
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
</template>
  
  <script setup>
  import Resizer from '@/components/Resizer.vue'
  import Section from '@/components/Section.vue'
  import SectionFields from '@/components/SectionFields.vue'
  import SidePanelModal from '@/components/Settings/SidePanelModal.vue'
  import Icon from '@/components/Icon.vue'
  import LayoutHeader from '@/components/LayoutHeader.vue'
  import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
  import AddressModal from '@/components/Modals/AddressModal.vue'
  import OpportunitiesListView from '@/components/ListViews/OpportunitiesListView.vue'
  import ContactsListView from '@/components/ListViews/ContactsListView.vue'
  import AddressesListView from '@/components/ListViews/AddressesListView.vue'
  import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
  import EditIcon from '@/components/Icons/EditIcon.vue'
  import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
  import OpportunitiesIcon from '@/components/Icons/OpportunitiesIcon.vue'
  import AddressIcon from '@/components/Icons/AddressIcon.vue'
  import { globalStore } from '@/stores/global'
  import { usersStore } from '@/stores/users'
  import { statusesStore } from '@/stores/statuses'
  import { getView } from '@/utils/view'
  import {
    dateFormat,
    dateTooltipFormat,
    timeAgo,
    formatNumberIntoCurrency,
    createToast,
  } from '@/utils'
  import {
    Tooltip,
    Breadcrumbs,
    Dropdown,
    Tabs,
    call,
    createListResource,
    createDocumentResource,
    usePageMeta,
    createResource,
  } from 'frappe-ui'
  import { h, computed, ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { capture } from '@/telemetry'
  
  const props = defineProps({
    prospectId: {
      type: String,
      required: true,
    },
  })
  
  const { getUser, isManager } = usersStore()
  const { $dialog } = globalStore()
  const { getDealStatus } = statusesStore()
  const showSidePanelModal = ref(false)
  const showQuickEntryModal = ref(false)
  
  const route = useRoute()
  const router = useRouter()
  
  const prospect = createDocumentResource({
    doctype: 'Prospect',
    name: props.prospectId,
    cache: ['prospect', props.prospectId],
    fields: ['*'],
    auto: true,
  })
  
  async function updateField(fieldname, value) {
    await prospect.setValue.submit({
      [fieldname]: value,
    })
    createToast({
      title: __('Prospect updated'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
  
  const breadcrumbs = computed(() => {
    let items = [{ label: __('Prospects'), route: { name: 'Prospects' } }]
  
    if (route.query.view || route.query.viewType) {
      let view = getView(
        route.query.view,
        route.query.viewType,
        'Prospect',
      )
      if (view) {
        items.push({
          label: __(view.label),
          icon: view.icon,
          route: {
            name: 'Prospects',
            params: { viewType: route.query.viewType },
            query: { view: route.query.view },
          },
        })
      }
    }
  
    items.push({
      label: props.prospectId,
      route: {
        name: 'Prospect',
        params: { prospectId: props.prospectId },
      },
    })
    return items
  })
  
  usePageMeta(() => {
    return {
      title: props.prospectId,
    }
  })
  
  async function deleteProspect() {
    $dialog({
      title: __('Delete prospect'),
      message: __('Are you sure you want to delete this prospect?'),
      actions: [
        {
          label: __('Delete'),
          theme: 'red',
          variant: 'solid',
          async onClick(close) {
            try {
              await call('frappe.client.delete', {
                doctype: 'Prospect',
                name: props.prospectId,
              })
              close()
              router.push({ name: 'Prospects' })
            } catch (error) {
              const errorMessage = 
                error.name === 'LinkExistsError' || error.message.includes('LinkExistsError')
                  ? __('Cannot delete this prospect because it is linked to other records.')
                  : __('Failed to delete the prospect. Please try again later.');
              createToast({
                title: __('Error'),
                text: errorMessage,
                icon: 'x',
                iconClasses: 'text-ink-red-4',
              });
            }
          },
        },
      ],
    })
  }
  
  function website(url) {
    return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
  }
  
  function openWebsite() {
    if (!prospect.doc.website)
      createToast({
        title: __('Website not found'),
        icon: 'x',
        iconClasses: 'text-ink-red-4',
      })
    else window.open(prospect.doc.website, '_blank')
  }
  
  const showAddressModal = ref(false)
  const _prospect = ref({})
  const _address = ref({})
  
  const fieldsLayout = createResource({
    url: 'next_crm.api.doc.get_sidebar_fields',
    cache: ['fieldsLayout', props.prospectId],
    params: { doctype: 'Prospect', name: props.prospectId },
    auto: true,
    transform: (data) => getParsedFields(data),
  })
  
  function getParsedFields(data) {
    return data.map((section) => {
      return {
        ...section,
        fields: computed(() =>
          section.fields.map((field) => {
            if (field.name === 'address') {
              return {
                ...field,
                create: (value, close) => {
                  _prospect.value.address = value
                  _address.value = {}
                  showAddressModal.value = true
                  close()
                },
                edit: async (addr) => {
                  _address.value = await call('frappe.client.get', {
                    doctype: 'Address',
                    name: addr,
                  })
                  showAddressModal.value = true
                },
              }
            } else {
              return field
            }
          }),
        ),
      }
    })
  }
  
  const tabIndex = ref(0)
  const tabs = [
    {
      label: 'Opportunities',
      icon: h(OpportunitiesIcon, { class: 'h-4 w-4' }),
      count: computed(() => opportunities.data?.length),
    },
    {
      label: 'Contacts',
      icon: h(ContactsIcon, { class: 'h-4 w-4' }),
      count: computed(() => contacts.data?.length),
    },
    {
      label: 'Addresses',
      icon: h(AddressIcon, { class: 'h-4 w-4' }),
      count: computed(() => addresses.data?.length),
    },
  ]
  
  const opportunities = createListResource({
    type: 'list',
    doctype: 'Opportunity',
    cache: ['opportunities', props.prospectId],
    fields: [
      'name',
      'currency',
      'opportunity_amount',
      'status',
      'contact_email',
      'contact_mobile',
      'modified',
    ],
    filters: {
      opportunity_from: "Prospect",
      party_name: props.prospectId,
    },
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })
  
  async function getContactsList() { 
  const contact_names = await call('next_crm.api.contact.get_linked_contact', {
    link_doctype: 'Prospect',
    link_name: props.prospectId,
  })

  const list = createListResource({
    type: 'list',
    doctype: 'Contact',
    fields: [
      'name',
      'first_name',
      'image',
      'email_id',
      'company_name',
      'modified',
    ],
    filters: {
      name: ['in', contact_names],
    },
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  return list
}

async function getAddressesList() { 
  const address_names = await call('next_crm.api.address.get_linked_address', {
    link_doctype: 'Prospect',
    link_name: props.prospectId,
  })

  const list = createListResource({
    type: 'list',
    doctype: 'Address',
    fields: [
      'name',
      'address_title',
      'address_type',
      'address_line1',
      'phone',
      'modified',
    ],
    filters: {
      name: ['in', address_names],
    },
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  return list
}

const contacts = await getContactsList();
const addresses = await getAddressesList();

const rows = computed(() => {
  let list = []
  if (tabIndex.value === 0)
    list = opportunities
  else if (tabIndex.value === 1)
    list = contacts
  else if (tabIndex.value === 2)
    list = addresses

  if (!list.data) return []

  return list.data.map((row) => {
    if (tabIndex.value === 0)
      return getOpportunityRowObject(row)
    else if (tabIndex.value === 1)
      return getContactRowObject(row)
    else if (tabIndex.value === 2)
      return getAddressRowObject(row)
  })
})

const columns = computed(() => {
  if (tabIndex.value === 0)
    return opportunityColumns
  else if (tabIndex.value === 1)
    return contactColumns
  else if (tabIndex.value === 2)
    return addressColumns
})
  
  function getOpportunityRowObject(opportunity) {
    return {
      name: opportunity.name,
      opportunity_amount: formatNumberIntoCurrency(
        opportunity.opportunity_amount,
        opportunity.currency,
      ),
      status: {
        label: opportunity.status,
        color: getDealStatus(opportunity.status)?.iconColorClass,
      },
      email: opportunity.contact_email,
      mobile_no: opportunity.contact_mobile,
      opportunity_owner: {
        label: opportunity.opportunity_owner && getUser(opportunity.opportunity_owner).full_name,
        ...(opportunity.opportunity_owner && getUser(opportunity.opportunity_owner)),
      },
      modified: {
        label: dateFormat(opportunity.modified, dateTooltipFormat),
        timeAgo: __(timeAgo(opportunity.modified)),
      },
    }
  }

  function getContactRowObject(contact) {
  return {
    name: contact.name,
    full_name: {
      label: contact.full_name,
      image_label: contact.full_name,
      image: contact.image,
    },
    email: contact.email_id,
    mobile_no: contact.mobile_no,
    company_name: {
      label: contact.company_name,
      logo: props.customer?.image,
    },
    modified: {
      label: dateFormat(contact.modified, dateTooltipFormat),
      timeAgo: __(timeAgo(contact.modified)),
    },
  }
}

function getAddressRowObject(address) {
  return {
    name: address.name,
    address_title: address.address_title,
    address_type: address.address_type,
    address_line1: address.address_line1,
    phone: address.phone,
    modified: {
      label: dateFormat(address.modified, dateTooltipFormat),
      timeAgo: __(timeAgo(address.modified)),
    },
  }
}

async function createCustomer() {
  $dialog({
    title: __('Create Customer'),
    message: __('Are you sure you want to create a new Customer from this Prospect\'s details?'),
    actions: [
      {
        label: __('Create'),
        theme: 'green',
        variant: 'solid',
        async onClick(close) {
          try {
            const customer = await call('next_crm.overrides.prospect.create_customer', {
              prospect: prospect.name,
            })
            close()
            router.push({ name: 'Customer', params: { customerId: customer } })
          } catch (error) {
            createToast({
              title: __('Error'),
              text: error,
              icon: 'x',
              iconClasses: 'text-ink-red-4',
            });
          }
        },
      },
    ],
  })
}

  // Convert to Opportunity
  async function createOpportunity() {
      let opportunity = await call(
        'next_crm.overrides.prospect.create_opportunity',
        {
          prospect: prospect.name,
        },
      )
      if (opportunity) {
        capture('create_prospect_from_opportunity')
        router.push({ name: 'Opportunity', params: { opportunityId: opportunity } })
      }
  }
  
  const opportunityColumns = [
    {
      label: __('Amount'),
      key: 'opportunity_amount',
      width: '9rem',
    },
    {
      label: __('Status'),
      key: 'status',
      width: '10rem',
    },
    {
      label: __('Email'),
      key: 'contact_email',
      width: '12rem',
    },
    {
      label: __('Mobile no'),
      key: 'contact_mobile',
      width: '11rem',
    },
    {
      label: __('Last modified'),
      key: 'modified',
      width: '8rem',
    },
  ]

  const contactColumns = [
  {
    label: __('Name'),
    key: 'name',
    width: '17rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem' ,
  },
  {
    label: __('Company'),
    key: 'company_name',
    width: '12rem',
  },
  {
    label: __('Last modified'),
    key: 'modified',
    width: '8rem',
  },
]

const addressColumns = [
  {
    label: __('Title'),
    key: 'address_title',
    width: '17rem',
  },
  {
    label: __('Type'),
    key: 'address_type',
    width: '12rem' ,
  },
  {
    label: __('Line 1'),
    key: 'address_line1',
    width: '12rem',
  },
  {
    label: __('Phone'),
    key: 'phone',
    width: '12rem',
  },
  {
    label: __('Last modified'),
    key: 'modified',
    width: '8rem',
  },
]
</script>
