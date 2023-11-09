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
          onClick: ({ close }) => updateContact(close),
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          type="text"
          size="md"
          variant="outline"
          label="Salutation"
          v-model="_contact.salutation"
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
        <FormControl
          type="text"
          variant="outline"
          size="md"
          label="Organisation"
          v-model="_contact.company_name"
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
import { FormControl, Dialog, call } from 'frappe-ui'
import { ref, defineModel, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router';

const props = defineProps({
  contact: {
    type: Object,
    default: {},
  },
})

const router = useRouter()

const show = defineModel()
const contacts = defineModel('reloadContacts')

const editMode = ref(false)
let _contact = ref({})

async function updateContact(close) {
  if (JSON.stringify(props.contact) === JSON.stringify(_contact.value)) {
    return
  }

  if (_contact.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'Contact',
      name: _contact.value.name,
      fieldname: _contact.value,
    })
    if (d.name) {
      contacts.value.reload()
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'Contact',
        ..._contact.value,
      },
    })
    if (d.name) {
      contacts.value.reload()
      router.push({
        name: 'Contact',
        params: { contactId: d.name },
      })
    }
  }
  close()
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
      if (_contact.value.first_name) {
        editMode.value = true
      }
    })
  }
)
</script>
