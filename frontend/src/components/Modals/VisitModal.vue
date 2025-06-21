<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('New Site Visit') }}
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
          :data="_visit"
          doctype="CRM Site Visit"
        />
        <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="loading"
            @click="createVisit"
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
import { call, createResource } from 'frappe-ui'
import { ref, nextTick, watch, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
  options: {
    type: Object,
    default: {
      redirect: true,
      afterInsert: () => {},
    },
  },
})

const { getUser, isManager } = usersStore()

const router = useRouter()
const show = defineModel()
const error = ref(null)
const loading = ref(false)

let _visit = ref({
  visit_date: new Date().toISOString().split('T')[0],
  visit_type: 'Initial Meeting',
  status: 'Planned',
  sales_person: '',
  reference_doctype: '',
  reference_name: '',
  visit_to: '',
  contact_person: '',
  contact_email: '',
  contact_phone: '',
  address_line_1: '',
  city: '',
  state: '',
  country: '',
  visit_purpose: '',
  priority: 'Medium',
})

const visitStatuses = computed(() => [
  { label: 'Planned', value: 'Planned' },
  { label: 'In Progress', value: 'In Progress' },
  { label: 'Completed', value: 'Completed' },
  { label: 'Cancelled', value: 'Cancelled' },
])

async function createVisit() {
  loading.value = true
  error.value = null

  try {
    const doc = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Site Visit',
        ..._visit.value,
      },
    })
    
    if (doc.name) {
      capture('visit_created')
      handleVisitUpdate(doc)
    }
  } catch (err) {
    error.value = err.messages?.join('\n') || err.message
  } finally {
    loading.value = false
  }
}

function handleVisitUpdate(doc) {
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Visit',
      params: { visitId: doc.name },
    })
  }
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Site Visit'],
  params: { doctype: 'CRM Site Visit', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = visitStatuses.value
              field.prefix = 'blue'
            }

            if (field.fieldtype === 'Table') {
              _visit.value[field.fieldname] = []
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
      _visit.value = { 
        visit_date: new Date().toISOString().split('T')[0],
        visit_type: 'Initial Meeting',
        status: 'Planned',
        sales_person: getUser().name,
        priority: 'Medium',
        ...props.defaults 
      }
    })
  },
)

const showQuickEntryModal = defineModel('quickEntry')

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => (show.value = false))
}

onMounted(() => {
  if (!_visit.value.sales_person) {
    _visit.value.sales_person = getUser().name
  }
  if (!_visit.value.status && visitStatuses.value[0]?.value) {
    _visit.value.status = visitStatuses.value[0].value
  }
})
</script>
