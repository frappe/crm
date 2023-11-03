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

async function updateOrganization(close) {
  if (
    props.organization.organization_name === _organization.value.name &&
    props.organization.website === _organization.value.website
  )
    return

  if (editMode.value) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Organization',
      name: _organization.value.name,
      fieldname: _organization.value,
    })
    if (d.name) {
      organizations.value.reload()
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Organization',
        organization_name: _organization.value.name,
        website: _organization.value.website,
      },
    })
    if (d.name) {
      organizations.value.reload()
    }
  }
  close()
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
