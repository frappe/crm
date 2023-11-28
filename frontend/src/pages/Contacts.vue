<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create" @click="showContactModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex items-center justify-between px-5 pb-4 pt-3">
    <div class="flex items-center gap-2">
      <Dropdown :options="viewsDropdownOptions">
        <template #default="{ open }">
          <Button :label="currentView.label">
            <template #prefix>
              <FeatherIcon :name="currentView.icon" class="h-4" />
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
    </div>
    <div class="flex items-center gap-2">
      <Filter doctype="Contact" />
      <SortBy doctype="Contact" />
      <ViewSettings doctype="Contact" v-model="contacts" />
    </div>
  </div>
  <ContactsListView
    v-if="contacts.data"
    :rows="rows"
    :columns="contacts.data.columns"
  />
  <ContactModal v-model="showContactModal" :contact="{}" />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import ViewSettings from '@/components/ViewSettings.vue'
import { FeatherIcon, Breadcrumbs, Dropdown, createResource } from 'frappe-ui'
import { organizationsStore } from '@/stores/organizations.js'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { useDebounceFn } from '@vueuse/core'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

const { getOrganization } = organizationsStore()
const { get: getOrderBy } = useOrderBy()
const { getArgs, storage } = useFilter()
const route = useRoute()

const showContactModal = ref(false)

const currentContact = computed(() => {
  return contacts.data?.data?.find(
    (contact) => contact.name === route.params.contactId
  )
})

const breadcrumbs = computed(() => {
  let items = [{ label: 'Contacts', route: { name: 'Contacts' } }]
  if (!currentContact.value) return items
  items.push({
    label: currentContact.value.full_name,
    route: {
      name: 'Contact',
      params: { contactId: currentContact.value.name },
    },
  })
  return items
})

const currentView = ref({
  label: 'List',
  icon: 'list',
})

function getParams() {
  const filters = getArgs() || {}
  const order_by = getOrderBy() || 'modified desc'

  return {
    doctype: 'Contact',
    filters: filters,
    order_by: order_by,
  }
}

const contacts = createResource({
  url: 'crm.api.doc.get_list_data',
  params: getParams(),
  auto: true,
})

watch(
  () => getOrderBy(),
  (value, old_value) => {
    if (!value && !old_value) return
    contacts.params = getParams()
    contacts.reload()
  },
  { immediate: true }
)

watch(
  storage,
  useDebounceFn((value, old_value) => {
    if (JSON.stringify([...value]) === JSON.stringify([...old_value])) return
    contacts.params = getParams()
    contacts.reload()
  }, 300),
  { deep: true }
)

const rows = computed(() => {
  if (!contacts.data?.data) return []
  return contacts.data.data.map((contact) => {
    let _rows = {}
    contacts.data.rows.forEach((row) => {
      _rows[row] = contact[row]

      if (row == 'full_name') {
        _rows[row] = {
          label: contact.full_name,
          image_label: contact.full_name,
          image: contact.image,
        }
      } else if (row == 'company_name') {
        _rows[row] = {
          label: contact.company_name,
          logo: getOrganization(contact.company_name)?.organization_logo,
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(contact[row], dateTooltipFormat),
          timeAgo: timeAgo(contact[row]),
        }
      }
    })
    return _rows
  })
})

const viewsDropdownOptions = [
  {
    label: 'List',
    icon: 'list',
    onClick() {
      currentView.value = {
        label: 'List',
        icon: 'list',
      }
    },
  },
  {
    label: 'Table',
    icon: 'grid',
    onClick() {
      currentView.value = {
        label: 'Table',
        icon: 'grid',
      }
    },
  },
  {
    label: 'Calender',
    icon: 'calendar',
    onClick() {
      currentView.value = {
        label: 'Calender',
        icon: 'calendar',
      }
    },
  },
  {
    label: 'Board',
    icon: 'columns',
    onClick() {
      currentView.value = {
        label: 'Board',
        icon: 'columns',
      }
    },
  },
]
</script>
