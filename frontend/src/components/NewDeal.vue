<template>
  <div class="flex flex-col gap-4">
    <div v-for="section in allFields" :key="section.section">
      <div class="grid grid-cols-3 gap-4">
        <div v-for="field in section.fields" :key="field.name">
          <div class="mb-2 text-sm text-gray-600">{{ field.label }}</div>
          <FormControl
            v-if="field.type === 'select'"
            type="select"
            :options="field.options"
            v-model="newDeal[field.name]"
          >
            <template v-if="field.prefix" #prefix>
              <IndicatorIcon :class="field.prefix" />
            </template>
          </FormControl>
          <FormControl
            v-else-if="field.type === 'email'"
            type="email"
            v-model="newDeal[field.name]"
          />
          <Link
            v-else-if="field.type === 'link'"
            class="form-control"
            :value="newDeal[field.name]"
            :doctype="field.doctype"
            @change="(e) => field.change(e)"
            :placeholder="field.placeholder"
            :onCreate="field.create"
          />
          <Link
            v-else-if="field.type === 'user'"
            class="form-control"
            :value="getUser(newDeal[field.name]).full_name"
            :doctype="field.doctype"
            @change="(e) => field.change(e)"
            :placeholder="field.placeholder"
          >
            <template #prefix>
              <UserAvatar class="mr-2" :user="newDeal[field.name]" size="sm" />
            </template>
            <template #item-prefix="{ option }">
              <UserAvatar class="mr-2" :user="option.value" size="sm" />
            </template>
            <template #item-label="{ option }">
              <Tooltip :text="option.value">
                {{ getUser(option.value).full_name }}
              </Tooltip>
            </template>
          </Link>
          <FormControl v-else type="text" v-model="newDeal[field.name]" />
        </div>
      </div>
    </div>
  </div>
  <OrganizationModal
    v-model="showOrganizationModal"
    :organization="_organization"
    :options="{
      redirect: false,
      afterInsert: (doc) => (newLead.organization = doc.name),
    }"
  />
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { Tooltip } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const { getUser } = usersStore()
const { getDealStatus, statusOptions } = statusesStore()

const props = defineProps({
  newDeal: {
    type: Object,
    required: true,
  },
})

const showOrganizationModal = ref(false)
const _organization = ref({})

const allFields = computed(() => {
  return [
    {
      section: 'Deal Details',
      fields: [
        {
          label: 'Salutation',
          name: 'salutation',
          type: 'link',
          doctype: 'Salutation',
          placeholder: 'Salutation',
          change: (data) => (props.newDeal.salutation = data),
        },
        {
          label: 'First Name',
          name: 'first_name',
          type: 'data',
        },
        {
          label: 'Last Name',
          name: 'last_name',
          type: 'data',
        },
        {
          label: 'Email',
          name: 'email',
          type: 'data',
        },
        {
          label: 'Mobile No',
          name: 'mobile_no',
          type: 'data',
        },
      ],
    },
    {
      section: 'Other Details',
      fields: [
        {
          label: 'Organization',
          name: 'organization',
          type: 'link',
          placeholder: 'Organization',
          doctype: 'CRM Organization',
          change: (data) => (props.newDeal.organization = data),
          create: (value, close) => {
            _organization.value.organization_name = value
            showOrganizationModal.value = true
            close()
          },
        },
        {
          label: 'Status',
          name: 'status',
          type: 'select',
          options: statusOptions(
            'deal',
            (field, value) => (props.newDeal[field] = value)
          ),
          prefix: getDealStatus(props.newDeal.status).iconColorClass,
        },
        {
          label: 'Deal Owner',
          name: 'deal_owner',
          type: 'user',
          placeholder: 'Deal Owner',
          doctype: 'User',
          change: (data) => (props.newDeal.deal_owner = data),
        },
      ],
    },
  ]
})

onMounted(() => {
  if (!props.newDeal.status) {
    props.newDeal.status = getDealStatus(props.newDeal.status).name
  }
  if (!props.newDeal.deal_owner) {
    props.newDeal.deal_owner = getUser().email
  }
})
</script>
