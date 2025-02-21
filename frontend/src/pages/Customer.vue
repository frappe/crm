<template>
  <LayoutHeader v-if="customer.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
  </LayoutHeader>
  <div ref="parentRef" class="flex h-full overflow-hidden">
    <Resizer v-if="customer.doc" :parent="$refs.parentRef" class="flex h-full flex-col overflow-hidden border-r">
      <div class="border-b">
        <FileUploader @success="changeCustomerImage" :validateFile="validateFile">
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="group relative h-15.5 w-15.5">
                  <Avatar size="3xl" class="h-15.5 w-15.5" :label="customer.doc.customer_name"
                    :image="customer.doc.image" />
                  <component :is="customer.doc.image ? Dropdown : 'div'" v-bind="customer.doc.image
                    ? {
                      options: [
                        {
                          icon: 'upload',
                          label: customer.doc.image
                            ? __('Change image')
                            : __('Upload image'),
                          onClick: openFileSelector,
                        },
                        {
                          icon: 'trash-2',
                          label: __('Remove image'),
                          onClick: () => changeCustomerImage(''),
                        },
                      ],
                    }
                    : { onClick: openFileSelector }
                    " class="!absolute bottom-0 left-0 right-0">
                    <div
                      class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                      style="
                        -webkit-clip-path: inset(22px 0 0 0);
                        clip-path: inset(22px 0 0 0);
                      ">
                      <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                    </div>
                  </component>
                </div>
                <div class="flex flex-col gap-2 truncate">
                  <div class="truncate text-2xl font-medium text-ink-gray-9">
                    <span>{{ customer.doc.customer_name }}</span>
                  </div>
                  <div v-if="customer.doc.website" class="flex items-center gap-1.5 text-base text-ink-gray-8">
                    <WebsiteIcon class="size-4" />
                    <span>{{ website(customer.doc.website) }}</span>
                  </div>
                </div>
              </div>
              <div class="flex gap-1.5">
                <Button :label="__('Delete')" theme="red" size="sm" @click="deleteCustomer">
                  <template #prefix>
                    <FeatherIcon name="trash-2" class="h-4 w-4" />
                  </template>
                </Button>
                <Tooltip :text="__('Open website')" v-if="customer.doc.website">
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
      <div class="flex-1 overflow-auto p-5">
        <div class="space-y-6">
          <div v-if="customer.doc.tax_id" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Tax ID') }}</label>
            <p class="text-base text-gray-900">{{ customer.doc.tax_id }}</p>
          </div>
          <div v-if="customer.doc.customer_group" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Customer Group') }}</label>
            <p class="text-base text-gray-900">{{ customer.doc.customer_group }}</p>
          </div>
          <div v-if="customer.doc.territory" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Territory') }}</label>
            <p class="text-base text-gray-900">{{ customer.doc.territory }}</p>
          </div>
          <div v-if="customer.doc.default_currency" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Default Currency') }}</label>
            <p class="text-base text-gray-900">{{ customer.doc.default_currency }}</p>
          </div>
          <div v-if="customer.doc.default_price_list" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Default Price List') }}</label>
            <p class="text-base text-gray-900">{{ customer.doc.default_price_list }}</p>
          </div>
          <div v-if="customer.doc.payment_terms" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Payment Terms') }}</label>
            <p class="text-base text-gray-900">{{ customer.doc.payment_terms }}</p>
          </div>
          <div v-if="customer.doc.credit_limits?.length" class="space-y-2">
            <h3 class="text-lg font-medium text-gray-900">{{ __('Credit Limits') }}</h3>
            <div class="space-y-4">
              <div v-for="limit in customer.doc.credit_limits" :key="limit.name" class="rounded-lg border p-4">
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-500">{{ __('Company') }}</label>
                    <p class="text-base text-gray-900">{{ limit.company }}</p>
                  </div>
                  <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-500">{{ __('Credit Limit') }}</label>
                    <p class="text-base text-gray-900">{{ formatCurrency(limit.credit_limit) }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Resizer>
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-item="{ tab, selected }">
        <button
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-ink-gray-5 duration-300 ease-in-out hover:border-outline-gray-3 hover:text-ink-gray-9"
          :class="{ 'text-ink-gray-9': selected }">
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ __(tab.label) }}
          <Badge class="group-hover:bg-surface-gray-7" :class="[selected ? 'bg-surface-gray-7' : 'bg-gray-600']"
            variant="solid" theme="gray" size="sm">
            {{ tab.count }}
          </Badge>
        </button>
      </template>
      <template #tab-panel="{ tab }">
        <TimelineView v-if="tab.label === 'Timeline' && customer.doc" class="mt-4" :items="timeline.data || []"
              doctype="Customer" :docname="customer.doc?.name || ''" @comment-added="refreshTimeline" />
        <ContactsListView class="mt-4" v-if="tab.label === 'Contacts' && rows.length" :rows="rows" :columns="columns"
          :options="{ selectable: false, showTooltip: false }" />
        <div v-if="!rows.length && tab.label !== 'Timeline'"
          class="grid flex-1 place-items-center text-xl font-medium text-ink-gray-4">
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.icon" class="!h-10 !w-10" />
            <div>{{ __('No {0} Found', [__(tab.label)]) }}</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createDocumentResource,
  createResource,
  Tooltip,
  Breadcrumbs,
  Avatar,
  FileUploader,
  Dropdown,
  Tabs,
  call,
  toast
} from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { getView } from '@/utils/view'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Icon from '@/components/Icon.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import Resizer from '@/components/Resizer.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import TimelineView from '@/components/Timeline/TimelineView.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import { FeatherIcon } from 'frappe-ui'
import { Badge } from 'frappe-ui'

const props = defineProps({
  customerId: {
    type: String,
    required: true,
  },
})

const { brand } = getSettings()
const { getUser } = usersStore()
const { $dialog } = globalStore()

const route = useRoute()
const router = useRouter()

const customer = createDocumentResource({
  doctype: 'Customer',
  name: props.customerId,
  cache: ['customer', props.customerId],
  fields: ['*'],
  auto: true,
})

async function updateField(fieldname, value) {
  await customer.setValue.submit({
    [fieldname]: value,
  })
  toast({
    title: __('Customer updated'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Customers'), route: { name: 'Customers' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(
      route.query.view,
      route.query.viewType,
      'Customer'
    )
    if (view) {
      items.push({
        label: view.title,
        route: {
          name: 'Customers',
          query: { view: route.query.view, viewType: route.query.viewType },
        },
      })
    }
  }

  if (customer.doc) {
    items.push({
      label: customer.doc.customer_name,
    })
  }

  return items
})

const contactsCount = createResource({
  url: 'crm.api.doc.get_contacts_count',
  params: {
    doctype: 'Customer',
    name: props.customerId
  },
  auto: true,
})

const tabIndex = ref(0)
const tabs = computed(() => [
  {
    label: 'Timeline',
    icon: CalendarIcon,
    count: computed(() => timeline.data?.length || 0),
  },
  {
    label: 'Contacts',
    icon: ContactsIcon,
    count: contactsCount.data || 0,
  },
])

const rows = ref([])
const columns = ref([])

watch(
  () => tabIndex.value,
  async (newIndex) => {
    const tab = tabs.value[newIndex]
    try {
      if (tab.label === 'Contacts') {
        const response = await call('crm.api.doc.get_contacts', {
          reference_doctype: 'Customer',
          reference_name: props.customerId,
        })
        rows.value = response || []
        columns.value = [
          { key: 'name', label: 'Contact', type: 'Data' },
          { key: 'email', label: 'Email', type: 'Data' },
          { key: 'phone', label: 'Phone', type: 'Data' },
        ]
      }
    } catch (error) {
      console.error(`Error fetching ${tab.label.toLowerCase()}:`, error)
      toast({
        title: `Error fetching ${tab.label.toLowerCase()}`,
        message: error.message,
        icon: 'x',
        iconClasses: 'text-red-500',
      })
      rows.value = []
    }
  },
  { immediate: true }
)

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: customer.doc?.default_currency || 'USD',
  }).format(value)
}

function website(url) {
  return url.replace(/^https?:\/\//, '')
}

function validateFile(file) {
  const maxSize = 5 * 1024 * 1024 // 5MB
  if (file.size > maxSize) {
    return __('File size should not exceed 5MB')
  }
  if (!file.type.startsWith('image/')) {
    return __('Only image files are allowed')
  }
  return null
}

async function changeCustomerImage(image) {
  await customer.setValue.submit({
    image: image,
  })
  toast({
    title: __('Customer image updated'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}

async function deleteCustomer() {
  const confirmed = await $dialog({
    title: __('Delete Customer'),
    message: __('Are you sure you want to delete this customer? This action cannot be undone.'),
    actions: [
      {
        label: __('Yes, delete'),
        variant: 'solid',
        theme: 'red',
      },
      {
        label: __('No'),
        variant: 'subtle',
      },
    ],
  })
  if (!confirmed) return

  try {
    await call('frappe.client.delete', {
      doctype: 'Customer',
      name: props.customerId,
    })
    toast({
      title: __('Customer deleted'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
    router.push({ name: 'Customers' })
  } catch (error) {
    console.error('Error deleting customer:', error)
    toast({
      title: __('Error deleting customer'),
      message: error.message,
      icon: 'x',
      iconClasses: 'text-red-500',
    })
  }
}

function openWebsite() {
  if (customer.doc?.website) {
    window.open(customer.doc.website, '_blank')
  }
}

const timeline = createResource({
  url: 'crm.api.doc.get_timeline',
  cache: ['timeline', props.customerId],
  params: {
    doctype: 'Customer',
    name: props.customerId,
  },
  auto: true,
})

const refreshTimeline = async () => {
    try {
        await timeline.reload()
    } catch (error) {
        console.error('Error refreshing timeline:', error)
    }
}
</script> 