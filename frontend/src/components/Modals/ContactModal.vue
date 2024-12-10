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
        <div v-if="filteredSections.length">
          <FieldLayout :tabs="filteredSections" :data="_contact" />
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
          />
        </div>
      </div>
    </template>
  </Dialog>
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Contact"
  />
</template>

<script setup>
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import FieldLayout from '@/components/FieldLayout.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { call, createResource } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  contact: {
    type: Object,
    default: {},
  },
  options: {
    type: Object,
    default: {
      redirect: true,
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const router = useRouter()
const show = defineModel()

const editMode = ref(false)
let _contact = ref({})
let _address = ref({})

const showAddressModal = ref(false)

async function updateContact() {
  if (!dirty.value) {
    show.value = false
    return
  }

  const values = { ..._contact.value }

  let name = await callSetValue(values)

  handleContactUpdate({ name })
}

async function callSetValue(values) {
  const d = await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: props.contact.data.name,
    fieldname: values,
  })
  return d.name
}

async function callInsertDoc() {
  if (_contact.value.email_id) {
    _contact.value.email_ids = [{ email_id: _contact.value.email_id }]
    delete _contact.value.email_id
  }

  if (_contact.value.actual_mobile_no) {
    _contact.value.phone_nos = [{ phone: _contact.value.actual_mobile_no }]
    delete _contact.value.actual_mobile_no
  }

  const doc = await call('frappe.client.insert', {
    doc: {
      doctype: 'Contact',
      ..._contact.value,
    },
  })
  if (doc.name) {
    capture('contact_created')
    handleContactUpdate(doc)
  }
}

function handleContactUpdate(doc) {
  props.contact?.reload?.()
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Contact',
      params: { contactId: doc.name },
    })
  }
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

const dialogOptions = computed(() => {
  let title = !editMode.value ? 'New Contact' : _contact.value.full_name

  let size = 'xl'
  let actions = [
    {
      label: editMode.value ? 'Save' : 'Create',
      variant: 'solid',
      disabled: !dirty.value,
      onClick: () => (editMode.value ? updateContact() : callInsertDoc()),
    },
  ]

  return { title, size, actions }
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Contact'],
  params: { doctype: 'Contact', type: 'Quick Entry' },
  auto: true,
})

const filteredSections = computed(() => {
  let allSections = tabs.data?.[0]?.sections || []
  if (!allSections.length) return []

  allSections.forEach((s) => {
    s.fields.forEach((field) => {
      if (field.name == 'address') {
        field.create = (value, close) => {
          _contact.value.address = value
          _address.value = {}
          showAddressModal.value = true
          close()
        }
        field.edit = async (addr) => {
          _address.value = await call('frappe.client.get', {
            doctype: 'Address',
            name: addr,
          })
          showAddressModal.value = true
        }
      }
    })
  })

  return [{ no_tabs: true, sections: allSections }]
})

const dirty = computed(() => {
  return JSON.stringify(props.contact.data) !== JSON.stringify(_contact.value)
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      _contact.value = { ...props.contact.data }
      if (_contact.value.name) {
        editMode.value = true
      }
    })
  },
)

const showQuickEntryModal = ref(false)

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => (show.value = false))
}
</script>

<style scoped>
:deep(:has(> .dropdown-button)) {
  width: 100%;
}
</style>
