<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <div class="flex items-center justify-between px-5 pb-4 pt-3">
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
  <ListView
    v-if="rows"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'Call Log',
        params: { callLogId: row.name },
      }),
    }"
    row-key="name"
  >
    <ListHeader class="mx-5" />
    <ListRows>
      <ListRow
        class="mx-5"
        v-for="row in rows"
        :key="row.name"
        v-slot="{ column, item }"
        :row="row"
      >
        <ListRowItem :item="item">
          <template #prefix>
            <div v-if="['caller', 'receiver'].includes(column.key)">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.image"
                :label="item.label"
                size="sm"
              />
            </div>
            <div v-else-if="['type', 'duration'].includes(column.key)">
              <FeatherIcon :name="item.icon" class="h-3 w-3" />
            </div>
          </template>
          <div v-if="column.key === 'creation'" class="truncate text-base">
            {{ item.timeAgo }}
          </div>
          <div v-else-if="column.key === 'status'" class="truncate text-base">
            <Badge
              :variant="'subtle'"
              :theme="item.color"
              size="md"
              :label="item.label"
            />
          </div>
        </ListRowItem>
      </ListRow>
    </ListRows>
    <ListSelectBanner />
  </ListView>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import SortIcon from '@/components/Icons/SortIcon.vue'
import FilterIcon from '@/components/Icons/FilterIcon.vue'
import {
  secondsToDuration,
  dateFormat,
  dateTooltipFormat,
  timeAgo,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import {
  Avatar,
  Badge,
  createListResource,
  Breadcrumbs,
  ListView,
  ListHeader,
  ListRows,
  ListRow,
  ListRowItem,
  ListSelectBanner,
  FeatherIcon,
} from 'frappe-ui'
import { computed } from 'vue'

const { getUser } = usersStore()
const { getContact } = contactsStore()

const breadcrumbs = [{ label: 'Call Logs', route: { name: 'Call Logs' } }]

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
    width: '9rem',
  },
  {
    label: 'To',
    key: 'receiver',
    width: '9rem',
  },
  {
    label: 'Type',
    key: 'type',
    width: '9rem',
  },
  {
    label: 'Status',
    key: 'status',
    width: '9rem',
  },
  {
    label: 'Duration',
    key: 'duration',
    width: '6rem',
  },
  {
    label: 'From (number)',
    key: 'from',
    width: '9rem',
  },
  {
    label: 'To (number)',
    key: 'to',
    width: '9rem',
  },
  {
    label: 'Created on',
    key: 'creation',
    width: '8rem',
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
      creation: {
        label: dateFormat(callLog.creation, dateTooltipFormat),
        timeAgo: timeAgo(callLog.creation),
      },
    }
  })
})
</script>
