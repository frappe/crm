<template>
  <Dialog v-model="show" :options="dialogOptions">
    <template #body>
      <div class="bg-white px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-gray-900">
              {{ dialogOptions.title || 'Untitled' }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="detailMode"
              variant="ghost"
              class="w-7"
              @click="detailMode = false"
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
                      :label="contact[field.name]"
                      class="dropdown-button w-full justify-between truncate hover:bg-white"
                    >
                      <div class="truncate">{{ contact[field.name] }}</div>
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
          <div class="flex flex-col gap-4" v-else>
            <div class="flex gap-4" v-for="(section, i) in sections" :key="i">
              <div v-for="(field, j) in section.fields" :key="j" class="flex-1">
                <Link
                  v-if="field.type === 'link'"
                  variant="outline"
                  size="md"
                  :label="field.label"
                  v-model="_contact[field.name]"
                  :doctype="field.doctype"
                  :placeholder="field.placeholder"
                />
                <div class="space-y-1.5" v-if="field.type === 'dropdown'">
                  <label class="block text-base text-gray-600">
                    {{ field.label }}
                  </label>
                  <Dropdown
                    :options="field.options"
                    class="form-control w-full flex-1"
                  >
                    <template #default="{ open }">
                      <Button
                        :label="contact[field.name]"
                        class="dropdown-button h-8 w-full justify-between truncate rounded border border-gray-300 bg-white px-2.5 py-1.5 text-base placeholder-gray-500 hover:border-gray-400 hover:bg-white hover:shadow-sm focus:border-gray-500 focus:bg-white focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400"
                      >
                        <div class="truncate">{{ contact[field.name] }}</div>
                        <template #suffix>
                          <FeatherIcon
                            :name="open ? 'chevron-up' : 'chevron-down'"
                            class="h-4 text-gray-600"
                          />
                        </template>
                      </Button>
                    </template>
                    <template #footer>
                      <Button
                        variant="ghost"
                        class="w-full !justify-start"
                        label="Create New"
                        @click="field.create()"
                      >
                        <template #prefix>
                          <FeatherIcon name="plus" class="h-4" />
                        </template>
                      </Button>
                    </template>
                  </Dropdown>
                </div>
                <FormControl
                  v-else-if="field.type === 'data'"
                  variant="outline"
                  size="md"
                  type="text"
                  :label="field.label"
                  :placeholder="field.placeholder"
                  v-model="_contact[field.name]"
                />
              </div>
            </div>
            <Dialog v-model="_show" :options="_dialogOptions">
              <template #body-content>
                <FormControl
                  :type="new_field.type"
                  variant="outline"
                  v-model="new_field.value"
                  :placeholder="new_field.placeholder"
                />
              </template>
            </Dialog>
          </div>
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
            {{ action.label }}
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import DropdownItem from '@/components/DropdownItem.vue'
import ContactIcon from '@/components/Icons/ContactIcon.vue'
import GenderIcon from '@/components/Icons/GenderIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import AddressIcon from '@/components/Icons/AddressIcon.vue'
import CertificateIcon from '@/components/Icons/CertificateIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import Link from '@/components/Controls/Link.vue'
import Dropdown from '@/components/frappe-ui/Dropdown.vue'
import { contactsStore } from '@/stores/contacts'
import { call } from 'frappe-ui'
import { ref, defineModel, nextTick, watch, computed, h } from 'vue'
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

const router = useRouter()
const show = defineModel()
const { contacts } = contactsStore()

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
    name: props.contact.name,
    fieldname: values,
  })
  return d.name
}

async function callInsertDoc() {
  if (_contact.value.email_id) {
    _contact.value.email_ids = [{ email_id: _contact.value.email_id }]
    delete _contact.value.email_id
  }

  if (_contact.value.mobile_no) {
    _contact.value.phone_nos = [{ phone: _contact.value.mobile_no }]
    delete _contact.value.mobile_no
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
  contacts.reload()
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
      icon: EmailIcon,
      name: 'email_id',
      value: _contact.value.email_id,
      ...sections.value[2].fields[0],
    },
    {
      icon: PhoneIcon,
      name: 'mobile_no',
      value: _contact.value.mobile_no,
      ...sections.value[3].fields[0],
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

const sections = computed(() => {
  return [
    {
      fields: [
        {
          label: 'Salutation',
          type: 'link',
          name: 'salutation',
          placeholder: 'Mr./Mrs./Ms...',
          doctype: 'Salutation',
          change: (value) => {
            _contact.value.salutation = value
          },
        },
      ],
    },
    {
      fields: [
        {
          label: 'First Name',
          type: 'data',
          name: 'first_name',
        },
        {
          label: 'Last Name',
          type: 'data',
          name: 'last_name',
        },
      ],
    },
    {
      fields: [
        {
          label: 'Email',
          type: props.contact.name ? 'dropdown' : 'data',
          name: 'email_id',
          options: props.contact?.email_ids?.map((email) => {
            return {
              component: h(DropdownItem, {
                value: email.email_id,
                selected: email.email_id === props.contact.email_id,
                onClick: () => setAsPrimary('email', email.email_id),
              }),
            }
          }),
          create: (value) => {
            new_field.value = {
              type: 'email',
              value,
              placeholder: 'Add Email Address',
            }
            _dialogOptions.value = {
              title: 'Add Email',
              actions: [
                {
                  label: 'Add',
                  variant: 'solid',
                  onClick: () => createNew('email'),
                },
              ],
            }
            _show.value = true
          },
        },
      ],
    },
    {
      fields: [
        {
          label: 'Mobile No.',
          type: props.contact.name ? 'dropdown' : 'data',
          name: 'mobile_no',
          options: props.contact?.phone_nos?.map((phone) => {
            return {
              component: h(DropdownItem, {
                value: phone.phone,
                selected: phone.phone === props.contact.mobile_no,
                onClick: () => setAsPrimary('mobile_no', phone.phone),
              }),
            }
          }),
          create: (value) => {
            new_field.value = {
              type: 'tel',
              value,
              placeholder: 'Add Mobile No.',
            }
            _dialogOptions.value = {
              title: 'Add Mobile No.',
              actions: [
                {
                  label: 'Add',
                  variant: 'solid',
                  onClick: () => createNew('phone'),
                },
              ],
            }
            _show.value = true
          },
        },
        {
          label: 'Gender',
          type: 'link',
          name: 'gender',
          placeholder: 'Select Gender',
          doctype: 'Gender',
          change: (value) => {
            _contact.value.gender = value
          },
        },
      ],
    },
    {
      fields: [
        {
          label: 'Organization',
          type: 'link',
          name: 'company_name',
          placeholder: 'Select Organization',
          doctype: 'CRM Organization',
          change: (value) => {
            _contact.value.company_name = value
          },
          link: (data) => {
            router.push({
              name: 'Organization',
              params: { organizationId: data },
            })
          },
        },
      ],
    },
    {
      fields: [
        {
          label: 'Designation',
          type: 'data',
          name: 'designation',
        },
      ],
    },
    {
      fields: [
        {
          label: 'Address',
          type: 'link',
          name: 'address',
          placeholder: 'Select Address',
          doctype: 'Address',
          change: (value) => {
            _contact.value.address = value
          },
        },
      ],
    },
  ]
})

const _show = ref(false)
const new_field = ref({})

const _dialogOptions = ref({})

async function setAsPrimary(field, value) {
  let d = await call('crm.api.contact.set_as_primary', {
    contact: props.contact.name,
    field,
    value,
  })
  if (d) {
    contacts.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

async function createNew(field) {
  let d = await call('crm.api.contact.create_new', {
    contact: props.contact.name,
    field,
    value: new_field.value?.value,
  })
  if (d) {
    contacts.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
  _show.value = false
}

const dirty = computed(() => {
  return JSON.stringify(props.contact) !== JSON.stringify(_contact.value)
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    detailMode.value = props.options.detailMode
    editMode.value = false
    nextTick(() => {
      _contact.value = { ...props.contact }
      if (_contact.value.name) {
        editMode.value = true
      }
    })
  }
)
</script>

<style scoped>
:deep(:has(> .dropdown-button)) {
  width: 100%;
}
</style>
