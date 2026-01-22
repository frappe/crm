<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('New contact') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit fields layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              @click="show = false"
              icon="x"
            />
          </div>
        </div>
        <FieldLayout
          v-if="tabs.data?.length"
          :tabs="tabs.data"
          :data="_contact.doc"
          doctype="Contact"
        />
        <ErrorMessage class="mt-8" v-if="error" :message="__(error)" />
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="loading"
            @click="createContact"
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
import {
  showQuickEntryModal,
  quickEntryProps,
  showAddressModal,
  addressProps,
} from '@/composables/modals'
import { useDocument } from '@/data/document'
import { capture } from '@/telemetry'
import { call, createResource } from 'frappe-ui'
import { ref, nextTick, onMounted } from 'vue'
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

const loading = ref(false)
const error = ref(null)

const { document: _contact, triggerOnBeforeCreate } = useDocument('Contact')

async function createContact() {
  loading.value = true
  error.value = null

  if (_contact.doc.email_id) {
    _contact.doc.email_ids = [
      { email_id: _contact.doc.email_id, is_primary: 1 },
    ]
    delete _contact.doc.email_id
  }

  if (_contact.doc.mobile_no) {
    _contact.doc.phone_nos = [
      { phone: _contact.doc.mobile_no, is_primary_mobile_no: 1 },
    ]
    delete _contact.doc.mobile_no
  }

  await triggerOnBeforeCreate?.()

  const doc = await call(
    'frappe.client.insert',
    {
      doc: {
        doctype: 'Contact',
        ..._contact.doc,
      },
    },
    {
      onError: (err) => {
        error.value = err.error?.messages?.[0]
        loading.value = false
      },
    },
  )
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

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Contact'],
  params: { doctype: 'Contact', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'email_id') {
              field.read_only = false
            } else if (field.fieldname == 'mobile_no') {
              field.read_only = false
            } else if (field.fieldname == 'address') {
              field.create = (value, close) => {
                _contact.doc.address = value
                openAddressModal()
                close()
              }
              field.edit = (address) => openAddressModal(address)
            } else if (field.fieldtype === 'Table') {
              _contact.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

onMounted(() => {
  _contact.doc = {}
  Object.assign(_contact.doc, props.contact.data || props.contact)
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'Contact' }
  nextTick(() => (show.value = false))
}

function openAddressModal(_address) {
  showAddressModal.value = true
  addressProps.value = {
    doctype: 'Address',
    address: _address,
  }
  nextTick(() => (show.value = false))
}
</script>

<style scoped>
:deep(:has(> .dropdown-button)) {
  width: 100%;
}
</style>
