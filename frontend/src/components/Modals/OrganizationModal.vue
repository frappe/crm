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
          onClick: ({ close }) =>
            editMode ? updateOrganization(close) : callInsertDoc(close),
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          type="text"
          ref="title"
          size="md"
          label="Organization name"
          variant="outline"
          v-model="_organization.organization_name"
          placeholder="Add organization name"
        />
        <div class="flex gap-4">
          <FormControl
            class="flex-1"
            type="text"
            size="md"
            label="Website"
            variant="outline"
            v-model="_organization.website"
            placeholder="Add website"
          />
          <FormControl
            class="flex-1"
            type="text"
            size="md"
            label="Annual revenue"
            variant="outline"
            v-model="_organization.annual_revenue"
            placeholder="Add annual revenue"
          />
        </div>
        <div class="flex gap-4">
          <FormControl
            class="flex-1"
            type="select"
            :options="[
              '1-10',
              '11-50',
              '51-200',
              '201-500',
              '501-1000',
              '1001-5000',
              '5001-10000',
              '10001+',
            ]"
            size="md"
            label="No. of employees"
            variant="outline"
            v-model="_organization.no_of_employees"
          />
          <Link
            class="flex-1"
            size="md"
            label="Industry"
            variant="outline"
            v-model="_organization.industry"
            doctype="CRM Industry"
            placeholder="Add industry"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { FormControl, Dialog, call } from 'frappe-ui'
import { ref, defineModel, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  organization: {
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
const organizations = defineModel('reloadOrganizations')

const title = ref(null)
const editMode = ref(false)
let _organization = ref({
  organization_name: '',
  website: '',
  annual_revenue: '',
  no_of_employees: '1-10',
  industry: '',
})

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

  let name
  if (nameChanged) {
    name = await callRenameDoc()
  }
  if (otherFieldChanged) {
    name = await callSetValue(values)
  }
  handleOrganizationUpdate({ name }, close)
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

async function callInsertDoc(close) {
  const doc = await call('frappe.client.insert', {
    doc: {
      doctype: 'CRM Organization',
      organization_name: _organization.value.organization_name,
      website: _organization.value.website,
    },
  })
  doc.name && handleOrganizationUpdate(doc, close)
}

function handleOrganizationUpdate(doc, close) {
  organizations.value?.reload()
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Organization',
      params: { organizationId: doc.name },
    })
  }
  close && close()
  props.options.afterInsert && props.options.afterInsert(doc)
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      // TODO: Issue with FormControl
      // title.value.el.focus()
      _organization.value = { ...props.organization }
      if (_organization.value.name) {
        editMode.value = true
      }
    })
  }
)
</script>
