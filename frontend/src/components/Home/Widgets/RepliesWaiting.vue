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
      <RecordRow
        v-for="row in rows"
        :key="`${row.doctype}:${row.name}`"
        :record="row"
      >
        <Tooltip :text="channels[row.channel]?.label">
          <span class="flex w-4 justify-center">
            <component
              :is="channels[row.channel]?.icon"
              v-if="row.channel"
              class="size-4"
            />
          </span>
        </Tooltip>
        <Tooltip
          :text="
            __('Waiting since {0}', [prettyDate(row.awaiting_reply_since)])
          "
        >
          <span class="w-8 whitespace-nowrap text-right">
            {{ prettyDate(row.awaiting_reply_since, true) }}
          </span>
        </Tooltip>
        <OwnerAvatar v-if="team" :user="row.owner" />
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

const props = defineProps({
  config: { type: Object, default: () => ({}) },
  team: { type: Boolean, default: false },
})

const emit = defineEmits(['update:config'])

const channels = {
  email: { label: __('Email'), icon: EmailIcon },
  whatsapp: { label: __('WhatsApp'), icon: WhatsAppIcon },
}

const resource = useHomeWidget(
  props.team ? 'team_replies_waiting' : 'replies_waiting',
  () => props.config,
)
</script>
