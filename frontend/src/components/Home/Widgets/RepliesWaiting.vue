<template>
  <HomeWidget
    :title="team ? __('Team replies waiting') : __('Replies waiting')"
    :resource="resource"
    :config="config"
    :viewAll="recordListViews(config.doctype)"
    :emptyText="
      team
        ? __('No one is waiting on a reply from your team.')
        : __('No one is waiting on a reply from you.')
    "
    emptyIcon="lucide-inbox"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows }">
      <HomeTable :columns="columns" :rows="rows" :rowRoute="recordRoute">
        <template #channel="{ item, column }">
          <ListRowItem
            v-if="channels[item]"
            :item="channels[item].label"
            :column="column"
            class="overflow-hidden"
          >
            <template #prefix>
              <component :is="channels[item].icon" class="size-4" />
            </template>
          </ListRowItem>
        </template>
      </HomeTable>
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { recordListViews, recordRoute } from '@/utils/home'
import { ListRowItem } from 'frappe-ui/experimental'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
  team: { type: Boolean, default: false },
})

const emit = defineEmits(['update:config'])

const channels = {
  email: { label: __('Email'), icon: EmailIcon },
  whatsapp: { label: __('WhatsApp'), icon: WhatsAppIcon },
}

const columns = [
  homeColumns.record(),
  homeColumns.status(),
  { key: 'channel', label: __('Channel'), width: '6rem' },
  homeColumns.timeAgo('awaiting_reply_since', __('Waiting since')),
  ...(props.team ? [homeColumns.user('owner', __('Owner'))] : []),
]

const resource = useHomeWidget(
  props.team ? 'team_replies_waiting' : 'replies_waiting',
  () => props.config,
)
</script>
