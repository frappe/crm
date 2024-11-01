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
              v-if="isManager() || detailMode"
              variant="ghost"
              class="w-7"
              @click="detailMode ? (detailMode = false) : openQuickEntryModal()"
            >
              <EditIcon class="h-4 w-4" />
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div>
          <div v-if="detailMode" class="flex flex-col gap-3.5">
            <div
              v-for="field in detailFields"
              :key="field.name"
              class="flex h-7 items-center gap-2 text-base text-gray-800"
            >
              <div class="grid w-7 place-content-center">
                <component :is="field.icon" />
              </div>
              <div v-if="field.type == 'dropdown'">
                <Dropdown
                  :options="field.options"
                  class="form-control -ml-2 mr-2 w-full flex-1"
                >
                  <template #default="{ open }">
                    <Button
                      variant="ghost"
                      :label="contact.data[field.name]"
                      class="dropdown-button w-full justify-between truncate hover:bg-white"
                    >
                      <div class="truncate">{{ contact.data[field.name] }}</div>
                      <template #suffix>
                        <FeatherIcon
                          :name="open ? 'chevron-up' : 'chevron-down'"
                          class="h-4 text-gray-600"
                        />
                      </template>
                    </Button>
                  </template>
                </Dropdown>
              </div>
              <div v-else>{{ field.value }}</div>
            </div>
          </div>
          <Fields
            v-else-if="filteredSections"
            :sections="filteredSections"
            :data="_contact"
          />
        </div>
      </div>
      <div v-if="!detailMode" class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            v-for="action in dialogOptions.actions"
            :key="action.label"
            v-bind="action"
          >
            {{ __(action.label) }}
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
</template>

<script setup>
import Fields from '@/components/Fields.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import ContactIcon from '@/components/Icons/ContactIcon.vue'
import GenderIcon from '@/components/Icons/GenderIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import AddressIcon from '@/components/Icons/AddressIcon.vue'
import CertificateIcon from '@/components/Icons/CertificateIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import Dropdown from '@/components/frappe-ui/Dropdown.vue'
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
      detailMode: false,
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const router = useRouter()
const show = defineModel()

const detailMode = ref(false)
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

  let size = detailMode.value ? '' : 'xl'
  let actions = detailMode.value
    ? []
    : [
        {
          label: editMode.value ? 'Save' : 'Create',
          variant: 'solid',
          disabled: !dirty.value,
          onClick: () => (editMode.value ? updateContact() : callInsertDoc()),
        },
      ]

  return { title, size, actions }
})

const detailFields = computed(() => {
  let details = [
    {
      icon: ContactIcon,
      name: 'full_name',
      value:
        (_contact.value.salutation ? _contact.value.salutation + '. ' : '') +
        _contact.value.full_name,
    },
    {
      icon: GenderIcon,
      name: 'gender',
      value: _contact.value.gender,
    },
    {
      icon: Email2Icon,
      name: 'email_id',
      value: _contact.value.email_id,
    },
    {
      icon: PhoneIcon,
      name: 'mobile_no',
      value: _contact.value.actual_mobile_no,
    },
    {
      icon: OrganizationsIcon,
      name: 'company_name',
      value: _contact.value.company_name,
    },
    {
      icon: CertificateIcon,
      name: 'designation',
      value: _contact.value.designation,
    },
    {
      icon: AddressIcon,
      name: 'address',
      value: _contact.value.address,
    },
  ]

  return details.filter((detail) => detail.value)
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['quickEntryFields', 'Contact'],
  params: { doctype: 'Contact', type: 'Quick Entry' },
  auto: true,
})

const filteredSections = computed(() => {
  let allSections = sections.data || []
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

  return allSections
})

const dirty = computed(() => {
  return JSON.stringify(props.contact.data) !== JSON.stringify(_contact.value)
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    detailMode.value = props.options.detailMode
    editMode.value = false
    nextTick(() => {
      _contact.value = { ...props.contact.data }
      if (_contact.value.name) {
        editMode.value = true
      }
    })
  },
)

const showQuickEntryModal = defineModel('quickEntry')

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => {
    show.value = false
  })
}
</script>

<style scoped>
:deep(:has(> .dropdown-button)) {
  width: 100%;
}
</style>
