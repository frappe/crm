<template>
    <LayoutHeader v-if="property.doc">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs">
          <template #prefix="{ item }">
            <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
          </template>
        </Breadcrumbs>
      </template>
      <template #right-header>
        <Badge
          class = "inline-flex items-center rounded-md bg-yellow-50 px-3 py-3 text-xs font-medium text-yellow-800 ring-1 ring-yellow-600/20 ring-inset"
          :variant="'outline'"
          :ref_for="true"
          theme="gray"
          size="lg"
          :label="property.doc?.custom_stage || 'None'"
        >
        </Badge>
      </template>
    </LayoutHeader>
    <div ref="parentRef" class="flex h-full">
      <Resizer
        v-if="property.doc"
        :parent="$refs.parentRef"
        class="flex h-full flex-col overflow-hidden border-r"
      >
        <div class="border-b">
          <FileUploader
            @success="changePropertyImage"
            :validateFile="validateFile"
          >
            <template #default="{ openFileSelector, error }">
              <div class="flex flex-col items-start justify-start gap-4 p-5">
                <div class="flex gap-4 items-center">
                  <div class="group relative h-15.5 w-15.5">
                    <Avatar
                      size="3xl"
                      class="h-15.5 w-15.5"
                      :label="property.doc.item_name"
                      :image="property.doc.image"
                    />
                    <component
                      :is="property.doc.image ? Dropdown : 'div'"
                      v-bind="
                        property.doc.image
                          ? {
                              options: [
                                {
                                  icon: 'upload',
                                  label: property.doc.image
                                    ? __('Change image')
                                    : __('Upload image'),
                                  onClick: openFileSelector,
                                },
                                {
                                  icon: 'trash-2',
                                  label: __('Remove image'),
                                  onClick: () => changePropertyImage(''),
                                },
                              ],
                            }
                          : { onClick: openFileSelector }
                      "
                      class="!absolute bottom-0 left-0 right-0"
                    >
                      <div
                        class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                        style="
                          -webkit-clip-path: inset(22px 0 0 0);
                          clip-path: inset(22px 0 0 0);
                        "
                      >
                        <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                      </div>
                    </component>
                  </div>
                  <div class="flex flex-col gap-2 truncate">
                    <div class="truncate text-2xl font-medium text-ink-gray-9">
                      <span>{{ property.doc.name }}</span>
                    </div>
                    <div
                      v-if="property.doc.website"
                      class="flex items-center gap-1.5 text-base text-ink-gray-8"
                    >
                      <WebsiteIcon class="size-4" />
                      <span>{{ website(property.doc.website) }}</span>
                    </div>
                    <ErrorMessage :message="__(error)" />
                  </div>
                </div>
                <div class="flex gap-1.5">
                  <Button
                    :label="__('Delete')"
                    theme="red"
                    size="sm"
                    @click="deleteProperty"
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
            </template>
          </FileUploader>
        </div>
        <div
          v-if="sections.data"
          class="flex flex-1 flex-col justify-between overflow-hidden"
        >
          <SidePanelLayout
          :sections="sections.data"
          doctype="Item"
          :docname="propertyId"
          @reload="sections.reload"
        />
        </div>
      </Resizer>
      <Tabs as="div" v-model="tabIndex" :tabs="tabs">
        <template #tab-item="{ tab, selected }">
          <button
            class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-ink-gray-5 duration-300 ease-in-out hover:border-outline-gray-3 hover:text-ink-gray-9"
            :class="{ 'text-ink-gray-9': selected }"
          >
            <component v-if="tab.icon" :is="tab.icon" class="h-5" />
            {{ __(tab.label) }}
            <Badge
              v-if="tab.label !== 'Data'"
              class="group-hover:bg-surface-gray-7"
              :class="[selected ? 'bg-surface-gray-7' : 'bg-gray-600']"
              variant="solid"
              theme="gray"
              size="sm"
            >
              {{ tab.count }}
            </Badge>
          </button>
        </template>
        <template #tab-panel="{ tab }">
          <DealsListView
            class="mt-4"
            v-if="tab.label === 'Deals' && rows.length"
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
          <!-- Add the DataFields component for the "Data" tab -->
          <div class="ml-8 mr-8 mb-4">
            <DataFields
              v-if="tab.label === 'Data'"
              :doctype="'Item'"
              :docname="propertyId"
            />
        </div>
          <div
            v-if="!rows.length && tab.label !== 'Data'"
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
    <QuickEntryModal
      v-if="showQuickEntryModal"
      v-model="showQuickEntryModal"
      doctype="Item"
    />
    <AddressModal v-model="showAddressModal" v-model:address="_address" />
  </template>

  <script setup>
  import Resizer from '@/components/Resizer.vue'
  import SidePanelLayout from '@/components/SidePanelLayout.vue'
  import Icon from '@/components/Icon.vue'
  import LayoutHeader from '@/components/LayoutHeader.vue'
  import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
  import AddressModal from '@/components/Modals/AddressModal.vue'
  import DealsListView from '@/components/ListViews/DealsListView.vue'
  import ContactsListView from '@/components/ListViews/ContactsListView.vue'
  import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
  import CameraIcon from '@/components/Icons/CameraIcon.vue'
  import DealsIcon from '@/components/Icons/DealsIcon.vue'
  import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
  import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
  import DataFields from '@/components/Activities/DataFields.vue'
  import { getSettings } from '@/stores/settings'
  import { getMeta } from '@/stores/meta'
  import { globalStore } from '@/stores/global'
  import { usersStore } from '@/stores/users'
  import { statusesStore } from '@/stores/statuses'
  import { getView } from '@/utils/view'
  import { formatDate, timeAgo } from '@/utils'
  import {
    toast as createToast,
    Tooltip,
    Breadcrumbs,
    Avatar,
    FileUploader,
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

  // Define props
  const props = defineProps({
    propertyId: {
      type: String,
      required: true,
    },
  })

  // Initialize stores and utilities
  const { brand } = getSettings()
  const { getUser } = usersStore()
  const { $dialog } = globalStore()
  const { getDealStatus } = statusesStore()
  const showQuickEntryModal = ref(false)

  const route = useRoute()
  const router = useRouter()

  // Create document resource for the property
  const property = createDocumentResource({
    doctype: 'Item',
    name: props.propertyId,
    cache: ['property', props.propertyId],
    fields: ['*'],
    auto: true,
  })

  // Function to update a field
  async function updateField(fieldname, value) {
    await property.setValue.submit({
      [fieldname]: value,
    })
    createToast({
      title: __('Property updated'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }

  // Compute breadcrumbs
  const breadcrumbs = computed(() => {
    let items = [{ label: __('Properties'), route: { name: 'Properties' } }]

    if (route.query.view || route.query.viewType) {
      let view = getView(
        route.query.view,
        route.query.viewType,
        'Item',
      )
      if (view) {
        items.push({
          label: __(view.label),
          icon: view.icon,
          route: {
            name: 'Properties',
            params: { viewType: route.query.viewType },
            query: { view: route.query.view },
          },
        })
      }
    }

    items.push({
      label: props.propertyId,
      route: {
        name: 'Property',
        params: { propertyId: props.propertyId },
      },
    })
    return items
  })

  // Set page meta
  usePageMeta(() => {
    return {
      title: props.propertyId,
      icon: brand.favicon,
    }
  })

  // File validation for image upload
  function validateFile(file) {
    let extn = file.name.split('.').pop().toLowerCase()
    if (!['png', 'jpg', 'jpeg'].includes(extn)) {
      return __('Only PNG and JPG images are allowed')
    }
  }

  // Function to change property image
  async function changePropertyImage(file) {
    await call('frappe.client.set_value', {
      doctype: 'Item',
      name: props.propertyId,
      fieldname: 'image',
      value: file?.file_url || '',
    })
    property.reload()
  }

  // Function to delete property
  async function deleteProperty() {
    $dialog({
      title: __('Delete property'),
      message: __('Are you sure you want to delete this property?'),
      actions: [
        {
          label: __('Delete'),
          theme: 'red',
          variant: 'solid',
          async onClick(close) {
            await call('frappe.client.delete', {
              doctype: 'Item',
              name: props.propertyId,
            })
            close()
            router.push({ name: 'Properties' })
          },
        },
      ],
    })
  }

  // Function to format website URL
  function website(url) {
    return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
  }

  // Function to open website
  function openWebsite() {
    if (!property.doc.website)
      createToast({
        title: __('Website not found'),
        icon: 'x',
        iconClasses: 'text-ink-red-4',
      })
    else window.open(property.doc.website, '_blank')
  }

  // Address modal state
  const showAddressModal = ref(false)
  const _property = ref({})
  const _address = ref({})

  // Fetch side panel sections
  const sections = createResource({
    url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
    cache: ['sidePanelSections', 'Item'],
    params: { doctype: 'Item' },
    auto: true,
    transform: (data) => getParsedSections(data),
  })

  // Parse sections for side panel
  function getParsedSections(_sections) {
    return _sections.map((section) => {
      section.columns = section.columns.map((column) => {
        column.fields = column.fields.map((field) => {
          if (field.fieldname === 'address') {
            return {
              ...field,
              create: (value, close) => {
                _property.value.address = value
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
        })
        return column
      })
      return section
    })
  }

  // Tab state and configuration
  const tabIndex = ref(0)
  const tabs = [
    {
      label: 'Deals',
      icon: h(DealsIcon, { class: 'h-4 w-4' }),
      count: computed(() => deals.data?.length),
    },
    {
      label: 'Contacts',
      icon: h(ContactsIcon, { class: 'h-4 w-4' }),
      count: computed(() => contacts.data?.length),
    },
    {
      label: 'Data',
      icon: h(DetailsIcon, { class: 'h-4 w-4' }),
    },
  ]

  // Fetch deals data
  const deals = createListResource({
    type: 'list',
    doctype: 'CRM Deal',
    cache: ['deals', props.propertyId],
    fields: [
      'name',
      'organization',
      'lead',
      'currency',
      'annual_revenue',
      'status',
      'email',
      'mobile_no',
      'deal_owner',
      'modified',
    ],
    filters: {
      custom_property_: props.propertyId,
    },
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  // Fetch contacts data
  const contacts = createListResource({
    type: 'list',
    doctype: 'Contact',
    cache: ['contacts', props.propertyId],
    fields: [
      'name',
      'full_name',
      'image',
      'email_id',
      'mobile_no',
      'company_name',
      'modified',
    ],
    filters: {
      custom_property_reference: props.propertyId,
    },
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  // Compute rows for the table
  const rows = computed(() => {
    let list = []
    list = !tabIndex.value ? deals : contacts

    if (!list.data) return []

    return list.data.map((row) => {
      return !tabIndex.value ? getDealRowObject(row) : getContactRowObject(row)
    })
  })

  // Get formatted currency for deals
  const { getFormattedCurrency } = getMeta('CRM Deal')

  // Compute columns for the table
  const columns = computed(() => {
    return tabIndex.value === 0 ? dealColumns : contactColumns
  })

  // Function to format deal row object
  function getDealRowObject(deal) {
    return {
      name: deal.name,
      lead: {
        label: deal.lead,
        // logo: organization.doc?.organization_logo,
      },
      // annual_revenue: getFormattedCurrency('annual_revenue', deal),
      custom_deal_type: deal.custom_deal_type,
      status: {
        label: deal.status,
        color: getDealStatus(deal.status)?.color,
      },
      email: deal.email,
      mobile_no: deal.mobile_no,
      deal_owner: {
        label: deal.deal_owner && getUser(deal.deal_owner).full_name,
        ...(deal.deal_owner && getUser(deal.deal_owner)),
      },
      modified: {
        label: formatDate(deal.modified),
        timeAgo: __(timeAgo(deal.modified)),
      },
    }
  }

  // Function to format contact row object
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
      custom_property_reference: {
        label: contact.custom_property_reference,
        // logo: organization.doc?.organization_logo,
      },
      modified: {
        label: formatDate(contact.modified),
        timeAgo: __(timeAgo(contact.modified)),
      },
    }
  }

  // Define columns for deals
  const dealColumns = [
    {
      label: __('Name'),
      key: 'name',
      width: '13rem',
    },
    {
      label: __('Lead'),
      key: 'lead',
      width: '11rem',
    },
    {
      label: __('Type'),
      key: 'custom_deal_type',
      // align: 'right',
      width: '10rem',
    },
    {
      label: __('Status'),
      key: 'status',
      width: '10rem',
    },
    {
      label: __('Email'),
      key: 'email',
      width: '12rem',
    },
    {
      label: __('Mobile no'),
      key: 'mobile_no',
      width: '11rem',
    },
    {
      label: __('Deal owner'),
      key: 'deal_owner',
      width: '10rem',
    },
    {
      label: __('Last modified'),
      key: 'modified',
      width: '8rem',
    },
  ]

  // Define columns for contacts
  const contactColumns = [
    {
      label: __('Name'),
      key: 'full_name',
      width: '17rem',
    },
    {
      label: __('Email'),
      key: 'email',
      width: '12rem',
    },
    {
      label: __('Phone'),
      key: 'mobile_no',
      width: '12rem',
    },
    // {
    //   label: __('Property'),
    //   key: 'custom_property_reference',
    //   width: '12rem',
    // },
    {
      label: __('Last modified'),
      key: 'modified',
      width: '8rem',
    },
  ]
  </script>
