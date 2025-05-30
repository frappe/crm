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
              <EditIcon class="h-4 w-4" />
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <FieldLayout
          v-if="tabs.data?.length"
          :tabs="tabs.data"
          :data="_organization"
          doctype="CRM Organization"
        />
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
import { capture } from '@/telemetry'
import { call, FeatherIcon, createResource } from 'frappe-ui'
import { ref, nextTick, watch } from 'vue'
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

const emit = defineEmits(['openAddressModal'])

const { isManager } = usersStore()

const router = useRouter()
const show = defineModel()
const organization = defineModel('organization')

const loading = ref(false)
const title = ref(null)

let _organization = ref({
  organization_name: '',
  website: '',
  annual_revenue: '',
  no_of_employees: '1-10',
  industry: '',
})

let doc = ref({})

async function createOrganization() {
  const doc = await call('frappe.client.insert', {
    doc: {
      doctype: 'CRM Organization',
      ..._organization.value,
    },
  })
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
                _organization.value.address = value
                emit('openAddressModal')
                show.value = false
                close()
              }
              field.edit = (address) => {
                emit('openAddressModal', address)
                show.value = false
              }
            } else if (field.fieldtype === 'Table') {
              _organization.value[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    nextTick(() => {
      // TODO: Issue with FormControl
      // title.value.el.focus()
      doc.value = organization.value?.doc || organization.value || {}
      _organization.value = { ...doc.value }
    })
  },
)

const showQuickEntryModal = defineModel('showQuickEntryModal')

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => (show.value = false))
}
</script>
