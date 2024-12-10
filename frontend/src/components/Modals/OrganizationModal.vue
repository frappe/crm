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
          <FieldLayout :tabs="filteredSections" :data="_organization" />
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
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="CRM Organization"
  />
</template>

<script setup>
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import FieldLayout from '@/components/FieldLayout.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { call, FeatherIcon, createResource } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'
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
const editMode = ref(false)
let _address = ref({})
let _organization = ref({
  organization_name: '',
  website: '',
  annual_revenue: '',
  no_of_employees: '1-10',
  industry: '',
})

const showAddressModal = ref(false)

let doc = ref({})

async function updateOrganization() {
  const old = { ...doc.value }
  const newOrg = { ..._organization.value }

  const nameChanged = old.organization_name !== newOrg.organization_name
  delete old.organization_name
  delete newOrg.organization_name

  const otherFieldChanged = JSON.stringify(old) !== JSON.stringify(newOrg)
  const values = newOrg

  if (!nameChanged && !otherFieldChanged) {
    show.value = false
    return
  }

  let name
  loading.value = true
  if (nameChanged) {
    name = await callRenameDoc()
  }
  if (otherFieldChanged) {
    name = await callSetValue(values)
  }
  handleOrganizationUpdate({ name }, nameChanged)
}

async function callRenameDoc() {
  const d = await call('frappe.client.rename_doc', {
    doctype: 'CRM Organization',
    old_name: doc.value?.organization_name,
    new_name: _organization.value.organization_name,
  })
  loading.value = false
  return d
}

async function callSetValue(values) {
  const d = await call('frappe.client.set_value', {
    doctype: 'CRM Organization',
    name: _organization.value.name,
    fieldname: values,
  })
  loading.value = false
  return d.name
}

async function callInsertDoc() {
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

function handleOrganizationUpdate(doc, renamed = false) {
  if (doc.name && (props.options.redirect || renamed)) {
    router.push({
      name: 'Organization',
      params: { organizationId: doc.name },
    })
  } else {
    organization.value.reload?.()
  }
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

const dialogOptions = computed(() => {
  let title = !editMode.value
    ? __('New Organization')
    : __(_organization.value.organization_name)
  let size = 'xl'
  let actions = [
    {
      label: editMode.value ? __('Save') : __('Create'),
      variant: 'solid',
      onClick: () => (editMode.value ? updateOrganization() : callInsertDoc()),
    },
  ]

  return { title, size, actions }
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Organization'],
  params: { doctype: 'CRM Organization', type: 'Quick Entry' },
  auto: true,
})

const filteredSections = computed(() => {
  let allSections = tabs.data?.[0]?.sections || []
  if (!allSections.length) return []

  allSections.forEach((s) => {
    s.fields.forEach((field) => {
      if (field.name == 'address') {
        field.create = (value, close) => {
          _organization.value.address = value
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

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      // TODO: Issue with FormControl
      // title.value.el.focus()
      doc.value = organization.value?.doc || organization.value || {}
      _organization.value = { ...doc.value }
      if (_organization.value.name) {
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
