<template>
  <ListView :title="title" :columns="columns" :rows="rows" />
</template>

<script setup>
import ListView from '../components/ListView.vue'
import { computed } from 'vue'
import { createListResource } from 'frappe-ui'

const title = 'Contacts'

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  fields: ['name', 'full_name', 'email_id', 'phone'],
  orderBy: 'full_name asc',
  cache: 'Contacts',
  pageLength: 999,
  auto: true,
})
contacts.fetch()

const columns = [
  {
    label: 'Full Name',
    key: 'full_name',
    type: 'user',
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
    key: 'phone',
    type: 'phone',
    size: 'w-44',
  },
]

const rows = computed(() => {
  return contacts.data?.map((contact) => {
    return {
      full_name: contact.full_name,
      email: contact.email_id,
      phone: contact.phone,
    }
  })
})
</script>
