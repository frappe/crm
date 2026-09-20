<template>
  <div class="flex h-screen flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="WA Leads" />
      </template>
      <template #right-header>
        <Button
          :label="__('Refresh')"
          :iconLeft="LucideRefreshCcw"
          @click="refreshAll"
        />
      </template>
    </LayoutHeader>

    <div
      v-if="!whatsappEnabled"
      class="flex flex-1 items-center justify-center text-ink-gray-5"
    >
      {{ __('WhatsApp integration is not enabled.') }}
    </div>
    <div v-else class="flex flex-1 overflow-hidden">
      <!-- Conversation list (one per WhatsApp Profile) -->
      <div class="flex w-[320px] shrink-0 flex-col border-r overflow-hidden">
        <div class="p-3">
          <TextInput
            v-model="search"
            type="text"
            :placeholder="__('Search conversations...')"
            :debounce="300"
          >
            <template #prefix>
              <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-6" />
            </template>
          </TextInput>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div
            v-if="profiles.loading && !profiles.data"
            class="flex justify-center p-4"
          >
            <LoadingIndicator class="h-5 w-5" />
          </div>
          <div
            v-else-if="!profiles.data?.profiles?.length"
            class="p-4 text-center text-sm text-ink-gray-5"
          >
            {{ __('No WhatsApp conversations yet') }}
          </div>
          <div
            v-for="row in profiles.data?.profiles || []"
            :key="row.profile"
            class="flex cursor-pointer items-start gap-2.5 border-b p-3 hover:bg-surface-gray-2"
            :class="{ 'bg-surface-gray-3': row.profile === selectedProfile }"
            @click="selectProfile(row.profile)"
          >
            <Avatar :label="row.profile_name || row.number" size="lg" />
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-2">
                <div class="truncate font-medium text-ink-gray-9">
                  {{ row.profile_name || row.number }}
                </div>
                <div class="shrink-0 text-2xs text-ink-gray-5">
                  {{ formatDate(row.last_message_at, 'D MMM') }}
                </div>
              </div>
              <div class="flex items-center justify-between gap-2">
                <div class="truncate text-sm text-ink-gray-6">
                  <span v-if="row.last_message_direction === 'Outgoing'">
                    {{ __('You: ') }}
                  </span>
                  {{ row.last_message_preview }}
                </div>
                <Badge
                  v-if="row.unread_count"
                  :label="String(row.unread_count)"
                  theme="green"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat panel -->
      <div class="flex flex-1 flex-col overflow-hidden">
        <div
          v-if="!selectedProfile"
          class="flex flex-1 items-center justify-center text-ink-gray-5"
        >
          {{ __('Select a conversation to view messages') }}
        </div>
        <template v-else>
          <div class="flex items-center justify-between gap-2.5 border-b p-3">
            <div class="flex items-center gap-2.5">
              <Avatar :label="doc.profile_name || doc.number" size="lg" />
              <div>
                <router-link
                  v-if="doc.contact"
                  :to="{ name: 'Contact', params: { contactId: doc.contact } }"
                  class="font-medium text-ink-gray-9 hover:underline"
                >
                  {{ doc.profile_name || doc.number }}
                </router-link>
                <div v-else class="font-medium text-ink-gray-9">
                  {{ doc.profile_name || doc.number }}
                </div>
                <div class="text-sm text-ink-gray-5">{{ doc.mobile_no }}</div>
              </div>
            </div>
            <div v-if="!links.loading">
              <Dropdown
                v-if="links.data?.organization"
                :options="linkOptions"
                placement="right"
              >
                <Button :label="__('Linked Records')" iconLeft="link" />
              </Dropdown>
              <Button
                v-else
                :label="__('Convert to B2B')"
                variant="solid"
                @click="showOrganizationModal = true"
              />
            </div>
          </div>
          <FadedScrollableDiv class="flex flex-1 flex-col overflow-y-auto">
            <div
              v-if="whatsappMessages.loading && !whatsappMessages.data?.length"
              class="flex h-full items-center justify-center"
            >
              <LoadingIndicator class="h-6 w-6" />
            </div>
            <div
              v-else-if="!whatsappMessages.data?.length"
              class="flex h-full items-center justify-center text-ink-gray-5"
            >
              {{ __('No messages yet') }}
            </div>
            <WhatsAppArea
              v-else
              v-model="whatsappMessages"
              v-model:reply="replyMessage"
              class="px-4 py-3"
              :messages="whatsappMessages.data || []"
            />
          </FadedScrollableDiv>
          <WhatsAppBox
            ref="whatsappBox"
            v-model="doc"
            v-model:reply="replyMessage"
            v-model:whatsapp="whatsappMessages"
            doctype="Contact"
          />
        </template>
      </div>
    </div>
    <OrganizationModal
      v-if="showOrganizationModal"
      v-model="showOrganizationModal"
      :data="{ organization_name: doc.profile_name || doc.number }"
      :options="{ redirect: false, afterInsert: onOrganizationCreated }"
    />
  </div>
</template>

<script setup>
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import WhatsAppArea from '@/components/Activities/WhatsAppArea.vue'
import WhatsAppBox from '@/components/Activities/WhatsAppBox.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import { whatsappEnabled } from '@/composables/whatsapp'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import {
  Button,
  TextInput,
  Avatar,
  Badge,
  Dropdown,
  FeatherIcon,
  call,
  createResource,
  toast,
  usePageMeta,
} from 'frappe-ui'
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  profile: { type: String, default: '' },
})

const { $socket } = globalStore()
const router = useRouter()

const search = ref('')
const selectedProfile = ref(props.profile || null)
const selectedProfileRow = ref(null)
const replyMessage = ref({})
const showOrganizationModal = ref(false)

// WhatsAppBox only needs .name (-> reference_name, may be blank if the
// profile has no linked Contact yet - the live `validate` hook on
// WhatsApp Message will still try to resolve one from the phone number)
// and .mobile_no (-> "to"). Built straight from the selected list row
// rather than fetching a document, since a profile doesn't require one.
const doc = computed(() => ({
  name: selectedProfileRow.value?.contact || '',
  mobile_no: selectedProfileRow.value ? `+${selectedProfileRow.value.number}` : '',
  profile_name: selectedProfileRow.value?.profile_name,
  number: selectedProfileRow.value?.number,
  contact: selectedProfileRow.value?.contact,
}))

const profiles = createResource({
  url: 'ouredu_fcrm_customizations.api.whatsapp_profiles.get_whatsapp_profiles',
  cache: 'whatsapp_profiles',
  params: { search: search.value },
  auto: true,
  onSuccess: (data) => {
    // deep-link support: if a profile was passed in the route but isn't
    // selected yet, select it once the list has loaded
    if (props.profile && !selectedProfileRow.value) {
      const row = data?.profiles?.find((r) => r.profile === props.profile)
      if (row) selectProfile(row.profile)
    }
  },
})

watch(search, (value) => {
  profiles.update({ params: { search: value } })
  profiles.reload()
})

const whatsappMessages = createResource({
  url: 'ouredu_fcrm_customizations.api.whatsapp_profiles.get_whatsapp_profile_messages',
  auto: false,
  transform: (data) => sortByCreation(data),
})

const links = createResource({
  url: 'ouredu_fcrm_customizations.api.whatsapp_profiles.get_whatsapp_profile_links',
  auto: false,
})

function sortByCreation(list) {
  return list.sort((a, b) => new Date(a.creation) - new Date(b.creation))
}

function selectProfile(profile) {
  selectedProfile.value = profile
  selectedProfileRow.value =
    profiles.data?.profiles?.find((r) => r.profile === profile) || null
  replyMessage.value = {}
  whatsappMessages.update({ params: { profile } })
  whatsappMessages.reload()
  links.update({ params: { profile } })
  links.reload()
}

function refreshAll() {
  profiles.reload()
  if (selectedProfile.value) {
    whatsappMessages.reload()
    links.reload()
  }
}

const linkOptions = computed(() => {
  const opts = []
  const data = links.data
  if (!data) return opts

  if (data.contact) {
    opts.push({
      label: `${__('Contact')}: ${data.contact.full_name || data.contact.name}`,
      icon: 'user',
      onClick: () =>
        router.push({ name: 'Contact', params: { contactId: data.contact.name } }),
    })
  }
  if (data.organization) {
    opts.push({
      label: `${__('Organization')}: ${data.organization.organization_name}`,
      onClick: () =>
        router.push({
          name: 'Organization',
          params: { organizationId: data.organization.name },
        }),
    })
  }
  for (const lead of data.leads || []) {
    opts.push({
      label: `${__('Lead')}: ${lead.lead_name || lead.name}`,
      onClick: () => router.push({ name: 'Lead', params: { leadId: lead.name } }),
    })
  }
  for (const deal of data.deals || []) {
    opts.push({
      label: `${__('Deal')}: ${deal.organization || deal.name}`,
      onClick: () => router.push({ name: 'Deal', params: { dealId: deal.name } }),
    })
  }
  return opts
})

async function onOrganizationCreated(organizationDoc) {
  try {
    await call('ouredu_fcrm_customizations.api.whatsapp_profiles.link_organization_to_profile', {
      profile: selectedProfile.value,
      organization: organizationDoc.name,
    })
    toast.success(__('Linked to {0}', [organizationDoc.name]))
    links.reload()
    profiles.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to link the organization'))
  }
}

onMounted(() => {
  // The realtime payload only carries {reference_doctype, reference_name},
  // not a phone number, so it can't be matched precisely to a profile here -
  // refresh the list and the open conversation on any change instead.
  $socket.on('whatsapp_message', () => {
    profiles.reload()
    if (selectedProfile.value) whatsappMessages.reload()
  })
})

onBeforeUnmount(() => {
  $socket.off('whatsapp_message')
})

usePageMeta(() => {
  return { title: __('WA Leads') }
})
</script>
