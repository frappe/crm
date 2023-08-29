<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: list.title }]" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex justify-between items-center px-5 pb-2.5 border-b">
    <div class="flex items-center gap-2">
      <Dropdown :options="viewsDropdownOptions">
        <template #default="{ open }">
          <Button :label="currentView.label">
            <template #prefix
              ><FeatherIcon :name="currentView.icon" class="h-4"
            /></template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
            /></template>
          </Button>
        </template>
      </Dropdown>
    </div>
    <div class="flex items-center gap-2">
      <Button label="Sort">
        <template #prefix><SortIcon class="h-4" /></template>
      </Button>
      <Button label="Filter">
        <template #prefix><FilterIcon class="h-4" /></template>
      </Button>
      <Button icon="more-horizontal" />
    </div>
  </div>
  <ListView :list="list" :columns="columns" :rows="rows" row-key="name" />
</template>

<script setup>
import ListView from '@/components/ListView.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import SortIcon from '@/components/Icons/SortIcon.vue'
import FilterIcon from '@/components/Icons/FilterIcon.vue'
import { FeatherIcon, Button, Dropdown } from 'frappe-ui'
import { ref, computed } from 'vue'
import { contactsStore } from '@/stores/contacts.js'

const { contacts } = contactsStore()

const list = {
  title: 'Contacts',
  plural_label: 'Contacts',
  singular_label: 'Contact',
}

const columns = [
  {
    label: 'Full name',
    key: 'full_name',
    type: 'avatar',
    size: 'w-44',
  },
  {
    label: 'Email',
    key: 'email',
    type: 'email',
    size: 'w-44',
  },
  {
    label: 'Phone',
    key: 'mobile_no',
    type: 'phone',
    size: 'w-44',
  },
]

const rows = computed(() => {
  return contacts.data?.map((contact) => {
    return {
      name: contact.name,
      full_name: {
        label: contact.full_name,
        image_label: contact.full_name,
        image: contact.image,
      },
      email: contact.email_id,
      mobile_no: contact.mobile_no,
    }
  })
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
</script>
