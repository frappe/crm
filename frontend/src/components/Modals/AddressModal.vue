<template>
  <Dialog v-model="show" :options="dialogOptions">
    <template #body>
      <div class="bg-white px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-gray-900">
              {{ __(dialogOptions.title) || __('Untitled') }}
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
        <div v-if="sections.data">
          <Fields :sections="sections.data" :data="_address" />
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
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Address"
  />
</template>

<script setup>
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import Fields from '@/components/Fields.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { call, FeatherIcon, createResource, ErrorMessage } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'

const props = defineProps({
  options: {
    type: Object,
    default: {
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const show = defineModel()
const address = defineModel('address')

const loading = ref(false)
const error = ref(null)
const title = ref(null)
const editMode = ref(false)

let _address = ref({
  name: '',
  address_title: '',
  address_type: 'Billing',
  address_line1: '',
  address_line2: '',
  city: '',
  county: '',
  state: '',
  country: '',
  pincode: '',
})

const dialogOptions = computed(() => {
  let title = !editMode.value
    ? __('New Address')
    : __(_address.value.address_title)
  let size = 'xl'
  let actions = [
    {
      label: editMode.value ? __('Save') : __('Create'),
      variant: 'solid',
      onClick: () =>
        editMode.value ? updateAddress() : createAddress.submit(),
    },
  ]

  return { title, size, actions }
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['quickEntryFields', 'Address'],
  params: { doctype: 'Address', type: 'Quick Entry' },
  auto: true,
})

let doc = ref({})

function updateAddress() {
  error.value = null
  const old = { ...doc.value }
  const newAddress = { ..._address.value }

  const dirty = JSON.stringify(old) !== JSON.stringify(newAddress)
  const values = newAddress

  if (!dirty) {
    show.value = false
    return
  }

  loading.value = true
  updateAddressValues.submit({
    doctype: 'Address',
    name: _address.value.name,
    fieldname: values,
  })
}

const updateAddressValues = createResource({
  url: 'frappe.client.set_value',
  onSuccess(doc) {
    loading.value = false
    if (doc.name) {
      handleAddressUpdate(doc)
    }
  },
  onError(err) {
    loading.value = false
    error.value = err
  },
})

const createAddress = createResource({
  url: 'frappe.client.insert',
  makeParams() {
    return {
      doc: {
        doctype: 'Address',
        ..._address.value,
      },
    }
  },
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

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      // TODO: Issue with FormControl
      // title.value.el.focus()
      doc.value = address.value?.doc || address.value || {}
      _address.value = { ...doc.value }
      if (_address.value.name) {
        editMode.value = true
      }
    })
  },
)

const showQuickEntryModal = ref(false)

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => {
    show.value = false
  })
}
</script>
