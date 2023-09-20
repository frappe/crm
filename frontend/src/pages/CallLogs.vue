<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: list.title }]" />
    </template>
  </LayoutHeader>
  <div class="flex justify-between items-center px-5 pt-3 pb-4">
    <div class="flex items-center gap-2">
      <Button label="Sort">
        <template #prefix><SortIcon class="h-4" /></template>
      </Button>
      <Button label="Filter">
        <template #prefix><FilterIcon class="h-4" /></template>
      </Button>
    </div>
    <div class="flex items-center gap-2">
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
import { secondsToDuration } from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import { Button, createListResource } from 'frappe-ui'
import { computed } from 'vue'

const { getUser } = usersStore()
const { getContact } = contactsStore()

const list = {
  title: 'Call Logs',
  plural_label: 'Call Logs',
  singular_label: 'Call Log',
}

const callLogs = createListResource({
  type: 'list',
  doctype: 'CRM Call Log',
  fields: [
    'name',
    'caller',
    'receiver',
    'from',
    'to',
    'duration',
    'start_time',
    'end_time',
    'status',
    'type',
    'recording_url',
    'creation',
  ],
  orderBy: 'creation desc',
  cache: 'Call Logs',
  pageLength: 999,
  auto: true,
})

const columns = [
  {
    label: 'From',
    key: 'caller',
    type: 'avatar',
    size: 'w-32',
  },
  {
    label: 'To',
    key: 'receiver',
    type: 'avatar',
    size: 'w-32',
  },
  {
    label: 'Type',
    key: 'type',
    type: 'icon',
    size: 'w-32',
  },
  {
    label: 'Status',
    key: 'status',
    type: 'badge',
    size: 'w-32',
  },
  {
    label: 'Duration',
    key: 'duration',
    type: 'icon',
    size: 'w-20',
  },
  {
    label: 'From (number)',
    key: 'from',
    type: 'data',
    size: 'w-32',
  },
  {
    label: 'To (number)',
    key: 'to',
    type: 'data',
    size: 'w-32',
  },
  {
    label: 'Created on',
    key: 'creation',
    type: 'pretty_date',
    size: 'w-28',
  },
]

const rows = computed(() => {
  return callLogs.data?.map((callLog) => {
    let caller = callLog.caller
    let receiver = callLog.receiver

    if (callLog.type === 'Incoming') {
      caller = {
        label: getContact(callLog.from)?.full_name || 'Unknown',
        image: getContact(callLog.from)?.image,
      }
      receiver = {
        label: getUser(receiver).full_name,
        image: getUser(receiver).user_image,
      }
    } else {
      caller = {
        label: getUser(caller).full_name,
        image: getUser(caller).user_image,
      }
      receiver = {
        label: getContact(callLog.to)?.full_name || 'Unknown',
        image: getContact(callLog.to)?.image,
      }
    }

    return {
      name: callLog.name,
      caller: caller,
      receiver: receiver,
      from: callLog.from,
      to: callLog.to,
      duration: {
        label: secondsToDuration(callLog.duration),
        icon: 'clock',
      },
      type: {
        label: callLog.type,
        icon: callLog.type === 'Incoming' ? 'phone-incoming' : 'phone-outgoing',
      },
      status: {
        label: callLog.status,
        color: callLog.status === 'Completed' ? 'green' : 'gray',
      },
      creation: callLog.creation,
    }
  })
})
</script>
