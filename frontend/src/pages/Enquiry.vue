<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template v-if="doc.name" #right-header>
      <AssignTo v-model="assignees.data" doctype="CRM Enquiry" :docname="enquiryId" />
      <Dropdown v-if="doc.status" :options="statuses" placement="right">
        <template #default="{ open }">
          <Button
            :label="doc.status"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          >
            <template #prefix>
              <IndicatorIcon :class="getEnquiryStatus(doc.status)?.color" />
            </template>
          </Button>
        </template>
      </Dropdown>
      <Button
        variant="solid"
        :label="__('Save')"
        @click="save"
      />
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="p-5">
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <FormControl
        type="text"
        v-model="doc.first_name"
        :label="__('First name')"
        required
      />
      <FormControl
        type="text"
        v-model="doc.mobile_no"
        :label="__('Mobile no')"
        required
      />
      <FormControl
        type="select"
        v-model="doc.status"
        :label="__('Status')"
        :options="statusOptions('enquiry')"
        required
      />
      <div>
        <div class="mb-2 text-sm text-ink-gray-5">
          {{ __('Owner') }}
        </div>
        <Link
          class="form-control"
          :value="doc.enquiry_owner"
          doctype="User"
          @change="(value) => (doc.enquiry_owner = value)"
          :filters="{
            name: ['in', users.data.crmUsers?.map((user) => user.name)],
          }"
          :hideMe="true"
        />
      </div>
    </div>
    <div class="mt-4">
      <FormControl
        type="textarea"
        v-model="doc.notes"
        :label="__('Notes')"
      />
    </div>
    <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
  </div>
  <ErrorMessage v-else-if="error" class="p-5" :message="__(error)" />
</template>

<script setup>
import AssignTo from '@/components/AssignTo.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { useDocument } from '@/data/document'
import { Breadcrumbs, Dropdown, FormControl, toast } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  enquiryId: {
    type: String,
    required: true,
  },
})

const { users } = usersStore()
const { statusOptions, getEnquiryStatus } = statusesStore()

const { triggerOnChange, assignees, document, error } = useDocument(
  'CRM Enquiry',
  props.enquiryId,
)

const doc = computed(() => document.doc || {})

const breadcrumbs = computed(() => {
  return [
    { label: __('Enquiries'), route: { name: 'Enquiries' } },
    { label: doc.value.first_name || props.enquiryId },
  ]
})

const statuses = computed(() => {
  return statusOptions('enquiry', [], triggerStatusChange)
})

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  document.save.submit()
}

function save() {
  document.save.submit(null, {
    onError: (err) => {
      toast.error(err.messages?.[0] || __('Error updating enquiry'))
    },
  })
}
</script>
