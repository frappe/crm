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
        <div v-if="tabs.data && _address.doc">
          <FieldLayout
            :tabs="tabs.data"
            :data="_address.doc"
            doctype="Address"
          />
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
import { useDocument } from '@/data/document'
import { capture } from '@/telemetry'
import { FeatherIcon, createResource, ErrorMessage } from 'frappe-ui'
import { ref, nextTick, computed, onMounted } from 'vue'

const props = defineProps({
  address: {
    type: String,
    default: '',
  },
  options: {
    type: Object,
    default: {
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const show = defineModel()

const loading = ref(false)
const error = ref(null)
const title = ref(null)
const editMode = ref(false)

const { document: _address, triggerOnBeforeCreate } = useDocument(
  'Address',
  props.address || '',
)

const dialogOptions = computed(() => {
  let title = !editMode.value
    ? __('New Address')
    : __(_address.doc?.address_title)
  let size = 'xl'
  let actions = [
    {
      label: editMode.value ? __('Save') : __('Create'),
      variant: 'solid',
      onClick: () => (editMode.value ? updateAddress() : createAddress()),
    },
  ]

  return { title, size, actions }
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Address'],
  params: { doctype: 'Address', type: 'Quick Entry' },
  auto: true,
})

const callBacks = {
  onSuccess: (doc) => {
    loading.value = false
    handleAddressUpdate(doc)
  },
  onError: (err) => {
    loading.value = false
    if (err.exc_type == 'MandatoryError') {
      const errorMessage = err.messages
        .map((msg) => {
          let arr = msg.split(': ')
          return arr[arr.length - 1].trim()
        })
        .join(', ')
      error.value = __('These fields are required: {0}', [errorMessage])
      return
    }
    error.value = err
  },
}

async function updateAddress() {
  loading.value = true
  await _address.save.submit(null, callBacks)
}

async function createAddress() {
  loading.value = true
  error.value = null

  await triggerOnBeforeCreate?.()

  await _createAddress.submit({
    doc: {
      doctype: 'Address',
      ..._address.doc,
    },
  })
}

const _createAddress = createResource({
  url: 'frappe.client.insert',
  onSuccess(doc) {
    loading.value = false
    if (doc.name) {
      capture('address_created')
      handleAddressUpdate(doc)
    }
  },
  onError(err) {
    loading.value = false
    error.value = err
  },
})

function handleAddressUpdate(doc) {
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

onMounted(() => {
  editMode.value = props.address ? true : false

  if (!props.address) {
    _address.doc = { address_type: 'Billing' }
  }
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'Address' }
  nextTick(() => {
    show.value = false
  })
}
</script>
