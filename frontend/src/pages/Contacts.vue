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
  <ViewControls
    v-model="contacts"
    v-model:loadMore="loadMore"
    doctype="Contact"
  />
  <ContactsListView
    v-if="contacts.data && rows.length"
    v-model="contacts.data.page_length_count"
    :rows="rows"
    :columns="contacts.data.columns"
    :options="{
      rowCount: contacts.data.row_count,
      totalCount: contacts.data.total_count,
    }"
    @loadMore="() => loadMore++"
  />
  <div
    v-else-if="contacts.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <ContactsIcon class="h-10 w-10" />
      <span>No Contacts Found</span>
      <Button label="Create" @click="showContactModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <ContactModal v-model="showContactModal" :contact="{}" />
</template>

<script setup>
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { Breadcrumbs } from 'frappe-ui'
import { organizationsStore } from '@/stores/organizations.js'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const { getOrganization } = organizationsStore()
const route = useRoute()

const showContactModal = ref(false)

const currentContact = computed(() => {
  return contacts.value?.data?.data?.find(
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

// contacts data is loaded in the ViewControls component
const contacts = ref({})
const loadMore = ref(1)

const rows = computed(() => {
  if (!contacts.value?.data?.data) return []
  return contacts.value?.data.data.map((contact) => {
    let _rows = {}
    contacts.value?.data.rows.forEach((row) => {
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
</script>
