<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-white px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-gray-900">
              {{ __('Create Campaign') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager()"
              variant="ghost"
              class="w-7"
              @click="openQuickEntryModal"
            >
              <EditIcon class="h-4 w-4" />
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div>
          <CampaignFields  :sections="sections.data"  :data="campaign"          />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isCampignCreating"
            @click="createCampign"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { createResource } from 'frappe-ui'
import { ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import CampaignFields from '../CampaignFields.vue'

const props = defineProps({
  defaults: Object,
})

const { isManager } = usersStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)

const campaign = reactive({
})

const isCampignCreating = ref(false)

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['quickEntryFields', 'CRM Campaign'],
  params: { doctype: 'CRM Campaign', type: 'Quick Entry' },
  auto: true,
  onSuccess(data) {
    sections.originalData = JSON.parse(JSON.stringify(data))
  },
})


function createCampign() {
  createResource({
    url: 'crm.fcrm.doctype.crm_campaign.crm_campaign.create_or_update_campaign',
    params: { args: campaign },
    auto: true,
    validate() {

    },
    onSuccess(name) {
      capture('campign_created')
      isCampignCreating.value = false
      show.value = false
      router.push({ name: 'Campaign', params: { campaignId: name } })
    },
    onError(err) {
      isCampignCreating.value = false
      if (!err.messages) {
        error.value = err.message
        return
      }
      error.value = err.messages.join('\n')
    },
  })
}

const showQuickEntryModal = defineModel('quickEntry')

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => {
    show.value = false
  })
}

</script>
