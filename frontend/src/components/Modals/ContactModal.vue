<template>
  <Dialog
    v-model="show"
    :options="{
      title: editMode ? 'Edit contact' : 'New contact',
      size: 'xl',
      actions: [
        {
          label: editMode ? 'Update' : 'Create',
          variant: 'solid',
          disabled: !dirty,
          onClick: ({ close }) => editMode ? updateContact(close) : callInsertDoc(close),
        },
      ],
    }"
  >
    <template #body-content>
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
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { FormControl, Dialog, call } from 'frappe-ui'
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
      afterInsert: () => {},
    },
  },
})

const router = useRouter()
const show = defineModel()
const contacts = defineModel('reloadContacts')

const editMode = ref(false)
let _contact = ref({})

async function updateContact(close) {
  if (!dirty.value) {
    close()
    return
  }

  let name = await callSetValue(values)

  handleContactUpdate({ name }, close)
}

async function callSetValue(values) {
  const d = await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: _contact.value.name,
    fieldname: values,
  })
  return d.name
}

async function callInsertDoc(close) {
  const doc = await call('frappe.client.insert', {
    doc: {
      doctype: 'Contact',
      ..._contact.value,
    },
  })
  doc.name && handleContactUpdate(doc, close)
}

function handleContactUpdate(doc, close) {
  contacts.value?.reload()
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Contact',
      params: { contactId: doc.name },
    })
  }
  close && close()
  props.options.afterInsert && props.options.afterInsert(doc)
}

const dirty = computed(() => {
  return JSON.stringify(props.contact) !== JSON.stringify(_contact.value)
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
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
