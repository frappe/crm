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
</template>

<script setup>
import Fields from '@/components/Fields.vue'
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
import { call, createResource } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'
import { createToast } from '@/utils'
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
  doc.name && handleContactUpdate(doc)
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
      if (field.name == 'email_id') {
        field.type = props.contact?.data?.name ? 'Dropdown' : 'Data'
        field.options =
          props.contact.data?.email_ids?.map((email) => {
            return {
              name: email.name,
              value: email.email_id,
              selected: email.email_id === props.contact.data.email_id,
              placeholder: 'john@doe.com',
              onClick: () => {
                _contact.value.email_id = email.email_id
                setAsPrimary('email', email.email_id)
              },
              onSave: (option, isNew) => {
                if (isNew) {
                  createNew('email', option.value)
                  if (props.contact.data.email_ids.length === 1) {
                    _contact.value.email_id = option.value
                  }
                } else {
                  editOption('Contact Email', option.name, option.value)
                }
              },
              onDelete: async (option, isNew) => {
                props.contact.data.email_ids =
                  props.contact.data.email_ids.filter(
                    (email) => email.name !== option.name,
                  )
                !isNew && (await deleteOption('Contact Email', option.name))
                if (_contact.value.email_id === option.value) {
                  if (props.contact.data.email_ids.length === 0) {
                    _contact.value.email_id = ''
                  } else {
                    _contact.value.email_id = props.contact.data.email_ids.find(
                      (email) => email.is_primary,
                    )?.email_id
                  }
                }
              },
            }
          }) || []
        field.create = () => {
          props.contact.data?.email_ids?.push({
            name: 'new-1',
            value: '',
            selected: false,
            isNew: true,
          })
        }
      } else if (
        field.name == 'mobile_no' ||
        field.name == 'actual_mobile_no'
      ) {
        field.type = props.contact?.data?.name ? 'Dropdown' : 'Data'
        field.name = 'actual_mobile_no'
        field.options =
          props.contact.data?.phone_nos?.map((phone) => {
            return {
              name: phone.name,
              value: phone.phone,
              selected: phone.phone === props.contact.data.actual_mobile_no,
              onClick: () => {
                _contact.value.actual_mobile_no = phone.phone
                _contact.value.mobile_no = phone.phone
                setAsPrimary('mobile_no', phone.phone)
              },
              onSave: (option, isNew) => {
                if (isNew) {
                  createNew('phone', option.value)
                  if (props.contact.data.phone_nos.length === 1) {
                    _contact.value.actual_mobile_no = option.value
                  }
                } else {
                  editOption('Contact Phone', option.name, option.value)
                }
              },
              onDelete: async (option, isNew) => {
                props.contact.data.phone_nos =
                  props.contact.data.phone_nos.filter(
                    (phone) => phone.name !== option.name,
                  )
                !isNew && (await deleteOption('Contact Phone', option.name))
                if (_contact.value.actual_mobile_no === option.value) {
                  if (props.contact.data.phone_nos.length === 0) {
                    _contact.value.actual_mobile_no = ''
                  } else {
                    _contact.value.actual_mobile_no =
                      props.contact.data.phone_nos.find(
                        (phone) => phone.is_primary_mobile_no,
                      )?.phone
                  }
                }
              },
            }
          }) || []
        field.create = () => {
          props.contact.data?.phone_nos?.push({
            name: 'new-1',
            value: '',
            selected: false,
            isNew: true,
          })
        }
      }
    })
  })

  return allSections
})

async function setAsPrimary(field, value) {
  let d = await call('crm.api.contact.set_as_primary', {
    contact: props.contact.data.name,
    field,
    value,
  })
  if (d) {
    props.contact.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

async function createNew(field, value) {
  let d = await call('crm.api.contact.create_new', {
    contact: props.contact.data.name,
    field,
    value,
  })
  if (d) {
    props.contact.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

async function editOption(doctype, name, value) {
  let d = await call('frappe.client.set_value', {
    doctype,
    name,
    fieldname: doctype == 'Contact Phone' ? 'phone' : 'email',
    value,
  })
  if (d) {
    props.contact.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

async function deleteOption(doctype, name) {
  await call('frappe.client.delete', {
    doctype,
    name,
  })
  await props.contact.reload()
  createToast({
    title: 'Contact updated',
    icon: 'check',
    iconClasses: 'text-green-600',
  })
}

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
