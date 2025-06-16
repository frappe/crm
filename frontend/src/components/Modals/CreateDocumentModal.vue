<template>
  <Dialog v-model="show" :options="dialogOptions">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __(dialogOptions.title) || __('Untitled') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              @click="openQuickEntryModal"
            >
              <template #icon>
                <EditIcon />
              </template>
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <template #icon>
                <FeatherIcon name="x" class="size-4" />
              </template>
            </Button>
          </div>
        </div>
        <div v-if="tabs.data">
          <FieldLayout :tabs="tabs.data" :data="_data" :doctype="doctype" />
          <ErrorMessage class="mt-2" :message="error" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            v-for="action in dialogOptions.actions"
            :key="action.label"
            v-bind="action"
            :label="__(action.label)"
            :loading="loading"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { FeatherIcon, createResource, ErrorMessage, call } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  data: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['callback'])

const { isManager } = usersStore()

const show = defineModel()

const loading = ref(false)
const error = ref(null)

let _data = ref({})

const dialogOptions = computed(() => {
  let doctype = props.doctype

  if (doctype.startsWith('CRM ') || doctype.startsWith('FCRM ')) {
    doctype = doctype.replace(/^(CRM |FCRM )/, '')
  }

  let title = __('New {0}', [doctype])
  let size = 'xl'
  let actions = [
    {
      label: __('Create'),
      variant: 'solid',
      onClick: () => create(),
    },
  ]

  return { title, size, actions }
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', props.doctype],
  params: { doctype: props.doctype, type: 'Quick Entry' },
  auto: true,
})

async function create() {
  loading.value = true
  error.value = null

  let doc = await call(
    'frappe.client.insert',
    {
      doc: {
        doctype: props.doctype,
        ..._data.value,
      },
    },
    {
      onError: (err) => {
        loading.value = false
        if (err.error) {
          error.value = err.error.messages?.[0]
        }
      },
    },
  )

  loading.value = false
  show.value = false
  emit('callback', doc)
}

watch(
  () => show.value,
  (value) => {
    if (!value) return

    nextTick(() => {
      _data.value = { ...props.data }
    })
  },
)

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: props.doctype }
  nextTick(() => (show.value = false))
}
</script>
