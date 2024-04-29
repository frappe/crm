<template>
  <Dialog
    v-model="show"
    :options="{
      size: '3xl',
      title: __('Create Lead'),
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div
          v-for="section in allFields"
          :key="section.section"
          class="border-t pt-4 first:border-t-0"
        >
          <div class="grid grid-cols-3 gap-4">
            <div v-for="field in section.fields" :key="field.name">
              <div class="mb-2 text-sm text-gray-600">
                {{ __(field.label) }}
                <span class="text-red-500" v-if="field.mandatory">*</span>
              </div>
              <FormControl
                v-if="field.type === 'select'"
                type="select"
                class="form-control"
                :options="field.options"
                v-model="lead[field.name]"
                :placeholder="__(field.placeholder)"
              >
                <template v-if="field.prefix" #prefix>
                  <IndicatorIcon :class="field.prefix" />
                </template>
              </FormControl>
              <Link
                v-else-if="field.type === 'link'"
                class="form-control"
                :value="lead[field.name]"
                :doctype="field.doctype"
                @change="(v) => (lead[field.name] = v)"
                :placeholder="__(field.placeholder)"
                :onCreate="field.create"
              />
              <Link
                v-else-if="field.type === 'user'"
                class="form-control"
                :value="getUser(lead[field.name]).full_name"
                :doctype="field.doctype"
                @change="(v) => (lead[field.name] = v)"
                :placeholder="__(field.placeholder)"
                :hideMe="true"
              >
                <template #prefix>
                  <UserAvatar class="mr-2" :user="lead[field.name]" size="sm" />
                </template>
                <template #item-prefix="{ option }">
                  <UserAvatar class="mr-2" :user="option.value" size="sm" />
                </template>
                <template #item-label="{ option }">
                  <Tooltip :text="option.value">
                    <div class="cursor-pointer">
                      {{ getUser(option.value).full_name }}
                    </div>
                  </Tooltip>
                </template>
              </Link>
              <FormControl
                v-else
                type="text"
                :placeholder="__(field.placeholder)"
                v-model="lead[field.name]"
              />
            </div>
          </div>
        </div>
      </div>
      <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
    </template>
    <template #actions>
      <div class="flex flex-row-reverse gap-2">
        <Button variant="solid" :label="__('Save')" @click="createNewLead" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { Tooltip, createResource } from 'frappe-ui'
import { computed, onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const { getUser } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isLeadCreating = ref(false)

const lead = reactive({
  salutation: '',
  first_name: '',
  last_name: '',
  email: '',
  mobile_no: '',
  gender: '',
  organization: '',
  website: '',
  no_of_employees: '',
  territory: '',
  annual_revenue: '',
  industry: '',
  status: '',
  lead_owner: '',
})

const allFields = computed(() => {
  return [
    {
      section: 'Contact Details',
      fields: [
        {
          label: 'Salutation',
          name: 'salutation',
          type: 'link',
          placeholder: 'Mr',
          doctype: 'Salutation',
        },
        {
          label: 'First Name',
          name: 'first_name',
          mandatory: true,
          type: 'data',
          placeholder: 'John',
        },
        {
          label: 'Last Name',
          name: 'last_name',
          type: 'data',
          placeholder: 'Doe',
        },
        {
          label: 'Email',
          name: 'email',
          type: 'data',
          placeholder: 'john@doe.com',
        },
        {
          label: 'Mobile No',
          name: 'mobile_no',
          type: 'data',
          placeholder: '+91 9876543210',
        },
        {
          label: 'Gender',
          name: 'gender',
          type: 'link',
          doctype: 'Gender',
          placeholder: 'Male',
        },
      ],
    },
    {
      section: 'Organization Details',
      fields: [
        {
          label: 'Organization',
          name: 'organization',
          type: 'data',
          placeholder: 'Frappé Technologies',
        },
        {
          label: 'Website',
          name: 'website',
          type: 'data',
          placeholder: 'https://frappe.io',
        },
        {
          label: 'No of Employees',
          name: 'no_of_employees',
          type: 'select',
          options: [
            { label: __('1-10'), value: '1-10' },
            { label: __('11-50'), value: '11-50' },
            { label: __('51-200'), value: '51-200' },
            { label: __('201-500'), value: '201-500' },
            { label: __('501-1000'), value: '501-1000' },
            { label: __('1001-5000'), value: '1001-5000' },
            { label: __('5001-10000'), value: '5001-10000' },
            { label: __('10001+'), value: '10001+' },
          ],
          placeholder: '1-10',
        },
        {
          label: 'Territory',
          name: 'territory',
          type: 'link',
          doctype: 'CRM Territory',
          placeholder: 'India',
        },
        {
          label: 'Annual Revenue',
          name: 'annual_revenue',
          type: 'data',
          placeholder: '1000000',
        },
        {
          label: 'Industry',
          name: 'industry',
          type: 'link',
          doctype: 'CRM Industry',
          placeholder: 'Technology',
        },
      ],
    },
    {
      section: 'Other Details',
      fields: [
        {
          label: 'Status',
          name: 'status',
          type: 'select',
          options: statusOptions(
            'lead',
            (field, value) => (lead[field] = value)
          ),
          prefix: getLeadStatus(lead.status).iconColorClass,
        },
        {
          label: 'Lead Owner',
          name: 'lead_owner',
          type: 'user',
          placeholder: 'Lead Owner',
          doctype: 'User',
        },
      ],
    },
  ]
})

const createLead = createResource({
  url: 'frappe.client.insert',
  makeParams(values) {
    return {
      doc: {
        doctype: 'CRM Lead',
        ...values,
      },
    }
  },
})

function createNewLead() {
  createLead.submit(lead, {
    validate() {
      error.value = null
      if (!lead.first_name) {
        error.value = __('First Name is mandatory')
        return error.value
      }
      if (lead.website && !lead.website.startsWith('http')) {
        lead.website = 'https://' + lead.website
      }
      if (lead.annual_revenue) {
        lead.annual_revenue = lead.annual_revenue.replace(/,/g, '')
        if (isNaN(lead.annual_revenue)) {
          error.value = __('Annual Revenue should be a number')
          return error.value
        }
      }
      if (lead.mobile_no && isNaN(lead.mobile_no.replace(/[-+() ]/g, ''))) {
        error.value = __('Mobile No should be a number')
        return error.value
      }
      if (lead.email && !lead.email.includes('@')) {
        error.value = __('Invalid Email')
        return error.value
      }
      isLeadCreating.value = true
    },
    onSuccess(data) {
      isLeadCreating.value = false
      show.value = false
      router.push({ name: 'Lead', params: { leadId: data.name } })
    },
  })
}

onMounted(() => {
  if (!lead.lead_owner) {
    lead.lead_owner = getUser().email
  }
})
</script>

<style scoped>
:deep(.form-control select) {
  padding-left: 2rem;
}
</style>
