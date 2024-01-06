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
              class="flex h-7 items-center gap-2 text-base text-gray-800"
              v-for="field in fields"
              :key="field.name"
            >
              <div class="grid w-7 place-content-center">
                <component :is="field.icon" />
              </div>
              <div>{{ field.value }}</div>
            </div>
          </div>
          <div v-else>
            <div class="flex flex-col gap-4">
              <FormControl
                type="text"
                ref="title"
                size="md"
                label="Organization Name"
                variant="outline"
                v-model="_organization.organization_name"
                placeholder="Add Organization Name"
              />
              <div class="flex gap-4">
                <FormControl
                  class="flex-1"
                  type="text"
                  size="md"
                  label="Website"
                  variant="outline"
                  v-model="_organization.website"
                  placeholder="Add Website"
                />
                <FormControl
                  class="flex-1"
                  type="text"
                  size="md"
                  label="Annual Revenue"
                  variant="outline"
                  v-model="_organization.annual_revenue"
                  placeholder="Add Annual Revenue"
                />
              </div>
              <Link
                class="flex-1"
                size="md"
                label="Territory"
                variant="outline"
                v-model="_organization.territory"
                doctype="CRM Territory"
                placeholder="Add Territory"
              />
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
                  label="No. of Employees"
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
                  placeholder="Add Industry"
                />
              </div>
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
import EditIcon from '@/components/Icons/EditIcon.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import TerritoryIcon from '@/components/Icons/TerritoryIcon.vue'
import Link from '@/components/Controls/Link.vue'
import { organizationsStore } from '@/stores/organizations'
import { call, FeatherIcon } from 'frappe-ui'
import { ref, defineModel, nextTick, watch, computed, h } from 'vue'
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
      detailMode: false,
      afterInsert: () => {},
    },
  },
})

const router = useRouter()
const show = defineModel()
const { organizations } = organizationsStore()

const title = ref(null)
const detailMode = ref(false)
const editMode = ref(false)
let _organization = ref({
  organization_name: '',
  website: '',
  annual_revenue: '',
  no_of_employees: '1-10',
  industry: '',
})

async function updateOrganization() {
  const old = { ...props.organization }
  const newOrg = { ..._organization.value }

  const nameChanged = old.name !== newOrg.name
  delete old.name
  delete newOrg.name

  const otherFieldChanged = JSON.stringify(old) !== JSON.stringify(newOrg)
  const values = newOrg

  if (!nameChanged && !otherFieldChanged) {
    show.value = false
    return
  }

  let name
  if (nameChanged) {
    name = await callRenameDoc()
  }
  if (otherFieldChanged) {
    name = await callSetValue(values)
  }
  handleOrganizationUpdate({ name })
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
  const doc = await call('frappe.client.insert', {
    doc: {
      doctype: 'CRM Organization',
      ..._organization.value,
    },
  })
  doc.name && handleOrganizationUpdate(doc)
}

function handleOrganizationUpdate(doc) {
  organizations.reload()
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Organization',
      params: { organizationId: doc.name },
    })
  }
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

const dialogOptions = computed(() => {
  let title = !editMode.value
    ? 'New Organization'
    : _organization.value.organization_name
  let size = detailMode.value ? '' : 'xl'
  let actions = detailMode.value
    ? []
    : [
        {
          label: editMode.value ? 'Save' : 'Create',
          variant: 'solid',
          onClick: () =>
            editMode.value ? updateOrganization() : callInsertDoc(),
        },
      ]

  return { title, size, actions }
})

const fields = computed(() => {
  let details = [
    {
      icon: OrganizationsIcon,
      name: 'organization_name',
      value: _organization.value.organization_name,
    },
    {
      icon: WebsiteIcon,
      name: 'website',
      value: _organization.value.website,
    },
    {
      icon: TerritoryIcon,
      name: 'territory',
      value: _organization.value.territory,
    },
    {
      icon: h(FeatherIcon, { name: 'dollar-sign', class: 'h-4 w-4' }),
      name: 'annual_revenue',
      value: _organization.value.annual_revenue,
    },
    {
      icon: h(FeatherIcon, { name: 'hash', class: 'h-4 w-4' }),
      name: 'no_of_employees',
      value: _organization.value.no_of_employees,
    },
    {
      icon: h(FeatherIcon, { name: 'briefcase', class: 'h-4 w-4' }),
      name: 'industry',
      value: _organization.value.industry,
    },
  ]

  return details.filter((field) => field.value)
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    detailMode.value = props.options.detailMode
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
