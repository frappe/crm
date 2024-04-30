<template>
  <Dialog
    v-model="show"
    :options="{
      size: '3xl',
      title: __('Create Deal'),
    }"
  >
    <template #body-content>
      <div class="mb-4 grid grid-cols-3 gap-4">
        <div class="flex items-center gap-3 text-sm text-gray-600">
          <div>{{ __('Choose Existing Organization') }}</div>
          <Switch v-model="chooseExistingOrganization" />
        </div>
        <div class="flex items-center gap-3 text-sm text-gray-600">
          <div>{{ __('Choose Existing Contact') }}</div>
          <Switch v-model="chooseExistingContact" />
        </div>
      </div>
      <Fields class="border-t pt-4" :sections="sections" :data="deal" />
      <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
    </template>
    <template #actions>
      <div class="flex flex-row-reverse gap-2">
        <Button
          variant="solid"
          :label="__('Create')"
          :loading="isDealCreating"
          @click="createDeal"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Fields from '@/components/Fields.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { Switch, createResource } from 'frappe-ui'
import { computed, ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const { getUser } = usersStore()
const { getDealStatus, statusOptions } = statusesStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)

const deal = reactive({
  organization: '',
  organization_name: '',
  website: '',
  no_of_employees: '',
  territory: '',
  annual_revenue: '',
  industry: '',
  contact: '',
  salutation: '',
  first_name: '',
  last_name: '',
  email: '',
  mobile_no: '',
  gender: '',
  status: '',
  deal_owner: '',
})

const isDealCreating = ref(false)
const chooseExistingContact = ref(false)
const chooseExistingOrganization = ref(false)

const sections = computed(() => {
  let fields = []
  if (chooseExistingOrganization.value) {
    fields.push({
      section: 'Select Organization',
      fields: [
        {
          label: 'Organization',
          name: 'organization',
          type: 'link',
          placeholder: 'Frappé Technologies',
          doctype: 'CRM Organization',
        },
      ],
    })
  } else {
    fields.push({
      section: 'Organization Details',
      fields: [
        {
          label: 'Organization Name',
          name: 'organization_name',
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
          placeholder: '9,999,999',
        },
        {
          label: 'Industry',
          name: 'industry',
          type: 'link',
          doctype: 'CRM Industry',
          placeholder: 'Technology',
        },
      ],
    })
  }
  if (chooseExistingContact.value) {
    fields.push({
      section: 'Select Contact',
      fields: [
        {
          label: 'Contact',
          name: 'contact',
          type: 'link',
          placeholder: 'John Doe',
          doctype: 'Contact',
        },
      ],
    })
  } else {
    fields.push({
      section: 'Contact Details',
      fields: [
        {
          label: 'Salutation',
          name: 'salutation',
          type: 'link',
          doctype: 'Salutation',
          placeholder: 'Mr',
        },
        {
          label: 'First Name',
          name: 'first_name',
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
          placeholder: '+91 1234567890',
        },
        {
          label: 'Gender',
          name: 'gender',
          type: 'link',
          doctype: 'Gender',
          placeholder: 'Male',
        },
      ],
    })
  }
  fields.push({
    section: 'Deal Details',
    columns: 2,
    fields: [
      {
        label: 'Status',
        name: 'status',
        type: 'select',
        options: dealStatuses.value,
        prefix: getDealStatus(deal.status).iconColorClass,
      },
      {
        label: 'Deal Owner',
        name: 'deal_owner',
        type: 'user',
        placeholder: 'Deal Owner',
        doctype: 'User',
      },
    ],
  })
  return fields
})

const dealStatuses = computed(() => {
  let statuses = statusOptions('deal')
  if (!deal.status) {
    deal.status = statuses[0].value
  }
  return statuses
})

function createDeal() {
  createResource({
    url: 'crm.fcrm.doctype.crm_deal.crm_deal.create_deal',
    params: { args: deal },
    auto: true,
    validate() {
      error.value = null
      if (deal.website && !deal.website.startsWith('http')) {
        deal.website = 'https://' + deal.website
      }
      if (deal.annual_revenue) {
        deal.annual_revenue = deal.annual_revenue.replace(/,/g, '')
        if (isNaN(deal.annual_revenue)) {
          error.value = __('Annual Revenue should be a number')
          return error.value
        }
      }
      if (deal.mobile_no && isNaN(deal.mobile_no.replace(/[-+() ]/g, ''))) {
        error.value = __('Mobile No should be a number')
        return error.value
      }
      if (deal.email && !deal.email.includes('@')) {
        error.value = __('Invalid Email')
        return error.value
      }
      isDealCreating.value = true
    },
    onSuccess(name) {
      isDealCreating.value = false
      show.value = false
      router.push({ name: 'Deal', params: { dealId: name } })
    },
  })
}

onMounted(() => {
  if (!deal.deal_owner) {
    deal.deal_owner = getUser().email
  }
})
</script>
