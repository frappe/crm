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
    :columns="columns"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ row }">
      <RecordRow :record="row">
        <ListCell class="text-ink-gray-5">
          <Tooltip v-if="row.channel" :text="channels[row.channel]?.label">
            <span class="relative flex">
              <component :is="channels[row.channel]?.icon" class="size-4" />
            </span>
          </Tooltip>
        </ListCell>
        <ListCell class="justify-end text-ink-gray-5">
          <Tooltip
            :text="
              __('Waiting since {0}', [prettyDate(row.awaiting_reply_since)])
            "
          >
            <span class="relative whitespace-nowrap">
              {{ prettyDate(row.awaiting_reply_since, true) }}
            </span>
          </Tooltip>
        </ListCell>
        <ListCell v-if="team">
          <OwnerAvatar :user="row.owner" />
        </ListCell>
      </RecordRow>
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import OwnerAvatar from '@/components/Home/OwnerAvatar.vue'
import RecordRow from '@/components/Home/RecordRow.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { prettyDate } from '@/utils'
import { recordListViews } from '@/utils/home'
import { Tooltip } from 'frappe-ui'
import { ListCell } from 'frappe-ui/list'

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
  '1rem',
  'minmax(0,1fr)',
  '1rem',
  '2.5rem',
  ...(props.team ? ['1.25rem'] : []),
]

const resource = useHomeWidget(
  props.team ? 'team_replies_waiting' : 'replies_waiting',
  () => props.config,
)
</script>
