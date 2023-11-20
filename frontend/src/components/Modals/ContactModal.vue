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
              class="flex h-7 items-center gap-2"
              v-for="field in fields"
              :key="field.name"
            >
              <component class="mx-1" :is="field.icon" />
              <div>{{ field.value }}</div>
            </div>
          </div>
          <div v-else>
            <div class="flex flex-col gap-4">
              <Link
                variant="outline"
                size="md"
                label="Salutation"
                v-model="_contact.salutation"
                doctype="Salutation"
                placeholder="Mr./Mrs./Ms..."
              />
              <div class="flex gap-4">
                <FormControl
                  class="flex-1"
                  variant="outline"
                  size="md"
                  type="text"
                  label="First Name"
                  v-model="_contact.first_name"
                />
                <FormControl
                  class="flex-1"
                  variant="outline"
                  size="md"
                  type="text"
                  label="Last Name"
                  v-model="_contact.last_name"
                />
              </div>
              <Link
                variant="outline"
                size="md"
                label="Organization"
                v-model="_contact.company_name"
                doctype="CRM Organization"
                placeholder="Select organization"
              />
              <div class="flex gap-4">
                <Link
                  class="flex-1"
                  variant="outline"
                  size="md"
                  label="Gender"
                  v-model="_contact.gender"
                  doctype="Gender"
                  placeholder="Select gender"
                />
                <FormControl
                  class="flex-1"
                  variant="outline"
                  size="md"
                  type="text"
                  label="Designation"
                  v-model="_contact.designation"
                />
              </div>
              <div class="flex gap-4">
                <FormControl
                  class="flex-1"
                  variant="outline"
                  size="md"
                  type="text"
                  label="Mobile no"
                  v-model="_contact.mobile_no"
                />
                <FormControl
                  class="flex-1"
                  variant="outline"
                  size="md"
                  type="email"
                  label="Email"
                  v-model="_contact.email_id"
                />
              </div>
              <Link
                variant="outline"
                size="md"
                label="Address"
                v-model="_contact.address"
                doctype="Address"
                placeholder="Select address"
              />
            </div>
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
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import Link from '@/components/Controls/Link.vue'
import { FormControl, Dialog, call, FeatherIcon } from 'frappe-ui'
import { ref, defineModel, nextTick, watch, computed } from 'vue'
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
const contacts = defineModel('reloadContacts')

const detailMode = ref(false)
const editMode = ref(false)
let _contact = ref({})

async function updateContact() {
  if (!dirty.value) {
    show.value = false
    return
  }

  let values = { ..._contact.value }

  let name = await callSetValue(values)

  handleContactUpdate({ name })
}

async function callSetValue(values) {
  const d = await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: _contact.value.name,
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
  contacts.value?.reload()
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
  let title = detailMode.value
    ? _contact.value.full_name
    : editMode.value
    ? 'Edit contact'
    : 'Create contact'
  let size = detailMode.value ? '' : 'xl'
  let actions = detailMode.value
    ? []
    : [
        {
          label: editMode.value ? 'Update' : 'Create',
          variant: 'solid',
          disabled: !dirty.value,
          onClick: () => (editMode.value ? updateContact() : callInsertDoc()),
        },
      ]

  return { title, size, actions }
})

const fields = computed(() => {
  return [
    {
      icon: ContactsIcon,
      name: 'full_name',
      value: _contact.value.full_name,
    },
    {
      icon: ContactsIcon,
      name: 'gender',
      value: _contact.value.gender,
    },
    {
      icon: ContactsIcon,
      name: 'email_id',
      value: _contact.value.email_id,
    },
    {
      icon: ContactsIcon,
      name: 'mobile_no',
      value: _contact.value.mobile_no,
    },
    {
      icon: ContactsIcon,
      name: 'company_name',
      value: _contact.value.company_name,
    },
    {
      icon: ContactsIcon,
      name: 'designation',
      value: _contact.value.designation,
    },
    {
      icon: ContactsIcon,
      name: 'address',
      value: _contact.value.address,
    },
  ]
})

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
