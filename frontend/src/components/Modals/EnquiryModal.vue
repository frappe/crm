<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create enquiry') }}
            </h3>
          </div>
          <Button variant="ghost" class="w-7" icon="x" @click="show = false" />
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormControl
            type="text"
            v-model="form.first_name"
            :label="__('First name')"
            required
          />
          <FormControl
            type="text"
            v-model="form.mobile_no"
            :label="__('Mobile no')"
            required
          />
          <FormControl
            type="select"
            v-model="form.status"
            :label="__('Status')"
            :options="enquiryStatuses"
            required
          />
          <div>
            <div class="mb-2 text-sm text-ink-gray-5">
              {{ __('Owner') }}
            </div>
            <Link
              class="form-control"
              :value="form.enquiry_owner"
              doctype="User"
              @change="(value) => (form.enquiry_owner = value)"
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
            v-model="form.notes"
            :label="__('Notes')"
          />
        </div>
        <div class="mt-4">
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __('Assign to') }}
          </div>
          <Link
            class="form-control"
            value=""
            doctype="User"
            @change="(option) => addAssignee(option) && ($refs.input.value = '')"
            :placeholder="__('John Doe')"
            :filters="{
              name: ['in', users.data.crmUsers?.map((user) => user.name)],
            }"
            :hideMe="true"
          >
            <template #target="{ togglePopover }">
              <div
                class="w-full min-h-12 flex flex-wrap items-center gap-1.5 p-1.5 pb-5 rounded-lg bg-surface-gray-2 cursor-text"
                @click.stop="togglePopover"
              >
                <Tooltip
                  :text="assignee.name"
                  v-for="assignee in assignees"
                  :key="assignee.name"
                  @click.stop
                >
                  <div
                    class="flex items-center text-sm p-0.5 text-ink-gray-6 border border-outline-gray-1 bg-surface-modal rounded-full cursor-pointer"
                    @click.stop
                  >
                    <UserAvatar :user="assignee.name" size="sm" />
                    <div class="ml-1">{{ getUser(assignee.name).full_name }}</div>
                    <Button
                      variant="ghost"
                      class="rounded-full !size-4 m-1"
                      @click.stop="removeAssignee(assignee.name)"
                    >
                      <template #icon>
                        <FeatherIcon name="x" class="h-3 w-3 text-ink-gray-6" />
                      </template>
                    </Button>
                  </div>
                </Tooltip>
              </div>
            </template>
            <template #item-prefix="{ option }">
              <UserAvatar class="mr-2" :user="option.value" size="sm" />
            </template>
            <template #item-label="{ option }">
              <Tooltip :text="option.value">
                <div class="cursor-pointer text-ink-gray-9">
                  {{ getUser(option.value).full_name }}
                </div>
              </Tooltip>
            </template>
          </Link>
        </div>
        <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create enquiry')"
            :loading="isCreating"
            @click="createEnquiry"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { useTelemetry } from 'frappe-ui/frappe'
import { FormControl, Tooltip, createResource, call } from 'frappe-ui'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const show = defineModel()

const { users, getUser } = usersStore()
const { statusOptions } = statusesStore()
const { capture } = useTelemetry()
const router = useRouter()

const error = ref('')
const isCreating = ref(false)

const form = reactive({
  first_name: '',
  mobile_no: '',
  notes: '',
  status: '',
  enquiry_owner: '',
})

const assignees = ref([])

const enquiryStatuses = computed(() => statusOptions('enquiry') || [])
const defaultStatus = computed(
  () => enquiryStatuses.value?.[0]?.value || 'New',
)

const createEnquiryResource = createResource({
  url: 'frappe.client.insert',
})

function addAssignee(value) {
  let obj = {
    name: value,
    image: getUser(value).user_image,
    label: getUser(value).full_name,
  }
  if (!assignees.value.find((assignee) => assignee.name === value)) {
    assignees.value.push(obj)
  }
}

function removeAssignee(value) {
  assignees.value = assignees.value.filter(
    (assignee) => assignee.name !== value,
  )
}

function validateForm() {
  error.value = ''
  if (!form.first_name) {
    error.value = __('First name is mandatory')
    return false
  }
  if (!form.mobile_no) {
    error.value = __('Mobile no is mandatory')
    return false
  }
  if (isNaN(form.mobile_no.replace(/[-+() ]/g, ''))) {
    error.value = __('Mobile no should be a number')
    return false
  }
  if (!form.status) {
    form.status = defaultStatus.value
  }
  if (!form.status) {
    error.value = __('Status is required')
    return false
  }
  if (!form.enquiry_owner) {
    error.value = __('Owner is required')
    return false
  }
  return true
}

function assignEnquiry(enquiryName) {
  let list = assignees.value.map((assignee) => assignee.name)
  let uniqueAssignees = [...new Set(list)].filter(
    (name) => name !== form.enquiry_owner,
  )
  if (!uniqueAssignees.length) return Promise.resolve()
  return call('frappe.desk.form.assign_to.add', {
    doctype: 'CRM Enquiry',
    name: enquiryName,
    assign_to: uniqueAssignees,
  })
}

function createEnquiry() {
  if (!validateForm()) {
    return
  }

  createEnquiryResource.submit(
    {
      doc: {
        doctype: 'CRM Enquiry',
        first_name: form.first_name,
        mobile_no: form.mobile_no,
        notes: form.notes,
        status: form.status,
        enquiry_owner: form.enquiry_owner,
      },
    },
    {
      validate() {
        isCreating.value = true
      },
      async onSuccess(data) {
        try {
          await assignEnquiry(data.name)
          capture('enquiry_created')
          show.value = false
          router.push({ name: 'Enquiry', params: { enquiryId: data.name } })
        } finally {
          isCreating.value = false
        }
      },
      onError(err) {
        isCreating.value = false
        if (!err.messages) {
          error.value = err.message
          return
        }
        error.value = err.messages.join('\n')
      },
    },
  )
}

onMounted(() => {
  if (!form.enquiry_owner) {
    form.enquiry_owner = getUser().name
  }
})

watch(
  enquiryStatuses,
  (statuses) => {
    if (!form.status && statuses?.[0]?.value) {
      form.status = statuses[0].value
    }
  },
  { immediate: true },
)
</script>
