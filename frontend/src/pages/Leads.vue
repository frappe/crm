<template>
  <ListView :title="title" :columns="columns" :rows="rows" />
</template>

<script setup>
import ListView from '../components/ListView.vue'

const title = 'Leads'

const columns = [
  {
    label: 'Title',
    key: 'title',
    size: 'flex-1',
  },
  {
    label: 'Company',
    key: 'company',
    size: 'w-44',
  },
  {
    label: 'Stage',
    key: 'stage',
    size: 'w-40',
  },
  {
    label: 'Contact',
    key: 'contact',
    size: 'w-44',
  },
  {
    label: 'Closed Date',
    key: 'closedDate',
    size: 'w-44',
  },
  {
    label: 'Value',
    key: 'value',
    size: 'w-40',
    align: 'text-right',
  },
]

const rows = [
  {
    title: 'Summer Catalog',
    company: 'Stripe',
    stage: 'Qualified',
    contact: 'Angela Bower',
    closedDate: '27 Sept, 2023',
    value: 99000.0,
  },
]
</script>
