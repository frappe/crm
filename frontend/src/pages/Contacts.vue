<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Contacts" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="contactsListView?.customListActions"
        :actions="contactsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        @click="showContactModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="contacts"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Contact"
  />
  <ContactsListView
    ref="contactsListView"
    v-if="contacts.data && rows.length"
    v-model="contacts.data.page_length_count"
    v-model:list="contacts"
    :rows="rows"
    :columns="contacts.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: contacts.data.row_count,
      totalCount: contacts.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div
    v-else-if="contacts.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <ContactsIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Contacts')]) }}</span>
      <Button :label="__('Create')" @click="showContactModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <ContactModal
    v-model="showContactModal"
    v-model:quickEntry="showQuickEntryModal"
    :contact="{}"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Contact"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { organizationsStore } from '@/stores/organizations.js'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { ref, computed } from 'vue'

const { getOrganization } = organizationsStore()

const showContactModal = ref(false)
const showQuickEntryModal = ref(false)

const contactsListView = ref(null)

// contacts data is loaded in the ViewControls component
const contacts = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !contacts.value?.data?.data ||
    !['list', 'group_by'].includes(contacts.value.data.view_type)
  )
    return []
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
          timeAgo: __(timeAgo(contact[row])),
        }
      }
    })
    return _rows
  })
})
</script>
