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
      <Button icon="more-horizontal" />
    </div>
  </div>
  <ContactsListView :rows="rows" :columns="columns" />
  <ContactModal
    v-model="showContactModal"
    v-model:reloadContacts="contacts"
    :contact="{}"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/ContactModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import { FeatherIcon, Breadcrumbs, Dropdown } from 'frappe-ui'
import { contactsStore } from '@/stores/contacts.js'
import { organizationsStore } from '@/stores/organizations.js'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const { contacts } = contactsStore()
const { getOrganization } = organizationsStore()
const route = useRoute()

const showContactModal = ref(false)

const currentContact = computed(() => {
  return contacts.data.find(
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

const rows = computed(() => {
  return contacts.data.map((contact) => {
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
        logo: getOrganization(contact.company_name)?.organization_logo,
      },
      modified: {
        label: dateFormat(contact.modified, dateTooltipFormat),
        timeAgo: timeAgo(contact.modified),
      },
    }
  })
})

const columns = [
  {
    label: 'Name',
    key: 'full_name',
    width: '17rem',
  },
  {
    label: 'Email',
    key: 'email',
    width: '12rem',
  },
  {
    label: 'Phone',
    key: 'mobile_no',
    width: '12rem',
  },
  {
    label: 'Organization',
    key: 'company_name',
    width: '12rem',
  },
  {
    label: 'Last modified',
    key: 'modified',
    width: '8rem',
  },
]

onMounted(() => {
  const el = document.querySelector('.router-link-active')
  if (el)
    setTimeout(() => {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
})
</script>
