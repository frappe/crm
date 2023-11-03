<template>
  <Dialog
    v-model="show"
    :options="{
      title: editMode ? 'Edit Organization' : 'Create Organization',
      size: 'xl',
      actions: [
        {
          label: editMode ? 'Update' : 'Create',
          variant: 'solid',
          onClick: ({ close }) => updateOrganization(close),
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-sm text-gray-600">Organization name</div>
          <TextInput
            ref="title"
            variant="outline"
            v-model="_organization.name"
            placeholder="Add organization name"
          />
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">Website</div>
          <TextInput
            variant="outline"
            v-model="_organization.website"
            placeholder="Add website"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { TextInput, Dialog, call } from 'frappe-ui'
import { ref, defineModel, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  organization: {
    type: Object,
    default: {},
  },
})

const show = defineModel()
const organizations = defineModel('reloadOrganizations')

const title = ref(null)
const editMode = ref(false)
let _organization = ref({})
const router = useRouter()

async function updateOrganization(close) {
  const old = { ...props.organization }
  const newOrg = { ..._organization.value }

  const nameChanged = old.name !== newOrg.name
  delete old.name
  delete newOrg.name

  const otherFieldChanged = JSON.stringify(old) !== JSON.stringify(newOrg)
  const values = newOrg

  if (!nameChanged && !otherFieldChanged) {
    close()
    return
  }

  if (editMode.value) {
    let name
    if (nameChanged) {
      name = await callRenameDoc()
    }
    if (otherFieldChanged) {
      name = await callSetValue(values)
    }
    handleOrganizationUpdate(name)
  } else {
    await callInsertDoc()
  }
  close()
}

async function callRenameDoc() {
  const d = await call('frappe.client.rename_doc', {
    doctype: 'CRM Organization',
    old_name: props.organization.name,
    new_name: _organization.value.name,
  })
  return d
}

async function callSetValue(values) {
  const d = await call('frappe.client.set_value', {
    doctype: 'CRM Organization',
    name: _organization.value.name,
    fieldname: values,
  })
  return d.name
}

async function callInsertDoc() {
  const d = await call('frappe.client.insert', {
    doc: {
      doctype: 'CRM Organization',
      organization_name: _organization.value.name,
      website: _organization.value.website,
    },
  })
  d.name && handleOrganizationUpdate()
}

function handleOrganizationUpdate(name) {
  organizations.value.reload()
  if (name) {
    router.push({
      name: 'Organization',
      params: { organizationId: name },
    })
  }
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      title.value.el.focus()
      _organization.value = { ...props.organization }
      if (_organization.value.name) {
        editMode.value = true
      }
    })
  }
)
</script>
