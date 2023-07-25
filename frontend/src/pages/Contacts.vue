<template>
  <ListView :title="title" :columns="columns" :rows="rows" row-key="name" />
</template>

<script setup>
import ListView from '../components/ListView.vue'
import { computed } from 'vue'
import { createListResource } from 'frappe-ui'

const title = 'Contacts'

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  fields: ['name', 'full_name', 'image', 'email_id', 'phone'],
  orderBy: 'full_name asc',
  cache: 'Contacts',
  pageLength: 999,
  auto: true,
})
contacts.fetch()

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
    key: 'phone',
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
      phone: contact.phone,
    }
  })
})
</script>
