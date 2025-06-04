<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('New Organization') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              @click="openQuickEntryModal"
            >
<<<<<<< HEAD
              <EditIcon class="h-4 w-4" />
=======
              <EditIcon class="w-4 h-4" />
>>>>>>> c4feed1 (fix: handle new document for lead/deal/contact/organization)
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <FieldLayout
          v-if="tabs.data?.length"
          :tabs="tabs.data"
<<<<<<< HEAD
          :data="_organization"
          doctype="CRM Organization"
        />
=======
          :data="_organization.doc"
          doctype="CRM Organization"
        />
        <ErrorMessage class="mt-8" v-if="error" :message="__(error)" />
>>>>>>> c4feed1 (fix: handle new document for lead/deal/contact/organization)
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="loading"
            @click="createOrganization"
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
import { call, FeatherIcon, createResource } from 'frappe-ui'
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
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
const organization = defineModel('organization')

const loading = ref(false)
const title = ref(null)

const { document: _organization } = useDocument('CRM Organization')

if (Object.keys(_organization.doc).length != 0) {
  _organization.doc = { no_of_employees: '1-10' }
}

let doc = ref({})

async function createOrganization() {
  const doc = await call(
    'frappe.client.insert',
    {
      doc: {
        doctype: 'CRM Organization',
        ..._organization.doc,
      },
    },
<<<<<<< HEAD
  })
=======
    {
      onError: (err) => {
        if (err.error.exc_type == 'ValidationError') {
          error.value = err.error?.messages?.[0]
        }
      },
    },
  )
>>>>>>> c4feed1 (fix: handle new document for lead/deal/contact/organization)
  loading.value = false
  if (doc.name) {
    capture('organization_created')
    handleOrganizationUpdate(doc)
  }
}

function handleOrganizationUpdate(doc) {
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Organization',
      params: { organizationId: doc.name },
    })
  } else {
    organization.value?.reload?.()
  }
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Organization'],
  params: { doctype: 'CRM Organization', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'address') {
              field.create = (value, close) => {
                _organization.doc.address = value
                openAddressModal()
                close()
              }
              field.edit = (address) => openAddressModal(address)
            } else if (field.fieldtype === 'Table') {
              _organization.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

onMounted(() => {
  Object.assign(
    _organization.doc,
    organization.value?.doc || organization.value || {},
  )
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Organization' }
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
