<template>
  <Dialog v-model="showDialog" :options="{ size: 'xl', title: __('Transfer to HD Ticket') }">
    <template #body-content>
      <div class="space-y-4">
        <!-- Info box: Found X email(s) -->
        <div
          v-if="emails.length > 0"
          class="rounded-md border-l-4 border-green-500 bg-green-50 p-4"
        >
          <p class="text-sm font-medium text-green-800">
            {{ __('Found {0} email(s)', [emails.length]) }}
          </p>
        </div>

        <!-- Customer/Lead info preview -->
        <div
          v-if="sourceDoc"
          class="rounded-md border-l-4 border-blue-500 bg-blue-50 p-4"
        >
          <div class="space-y-1 text-sm">
            <p class="font-medium text-blue-800">{{ __('Customer Information') }}</p>
            <div class="text-blue-700">
              <p v-if="customerName">
                <span class="font-medium">{{ __('Name') }}:</span> {{ customerName }}
              </p>
              <p v-if="customerEmail">
                <span class="font-medium">{{ __('Email') }}:</span> {{ customerEmail }}
              </p>
              <p v-if="customerPhone">
                <span class="font-medium">{{ __('Phone') }}:</span> {{ customerPhone }}
              </p>
            </div>
          </div>
        </div>

        <!-- Email list -->
        <div v-if="emails.length > 0" class="space-y-2">
          <div class="flex items-center gap-2 border-b pb-2">
            <input
              type="checkbox"
              :checked="allSelected"
              @change="toggleSelectAll"
              class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label class="text-sm font-medium text-gray-700">
              {{ __('Select All') }}
            </label>
          </div>

          <div class="max-h-[400px] space-y-2 overflow-y-auto">
            <div
              v-for="email in emails"
              :key="email.name"
              class="flex items-start gap-3 rounded-md border p-3 hover:bg-gray-50"
            >
              <input
                type="checkbox"
                :checked="selectedEmails.includes(email.name)"
                @change="toggleEmail(email.name)"
                class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div class="flex-1 space-y-1">
                <p class="font-semibold text-gray-900">
                  {{ email.subject || __('No Subject') }}
                </p>
                <p class="text-sm text-gray-600">
                  <span class="font-medium">{{ __('From') }}:</span> {{ email.sender || '-' }}
                </p>
                <p class="text-sm text-gray-600">
                  <span class="font-medium">{{ __('Date') }}:</span>
                  {{ formatDate(email.creation) }}
                </p>
                <p
                  v-if="email.content"
                  class="mt-2 text-sm text-gray-500"
                >
                  {{ formatEmailPreview(email.content) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="rounded-md bg-gray-50 p-4 text-center text-sm text-gray-600">
          {{ __('No emails found for transfer') }}
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        variant="ghost"
        :label="__('Cancel')"
        @click="closeDialog"
        :disabled="isLoading"
      />
      <Button
        variant="solid"
        :label="__('Create HD Ticket')"
        :loading="isLoading"
        :disabled="selectedEmails.length === 0"
        @click="handleTransfer"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button } from "frappe-ui"
import { ref, computed, watch } from "vue"
import { formatEmailPreview, formatDate } from "@/utils/emailTransfer"

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  sourceDoc: {
    type: Object,
    default: null,
  },
  emails: {
    type: Array,
    default: () => [],
  },
  targetType: {
    type: String,
    default: "HD Ticket",
  },
})

const emit = defineEmits(["update:show", "transfer", "close"])

const showDialog = computed({
  get: () => props.show,
  set: (value) => emit("update:show", value),
})

const selectedEmails = ref([])
const isLoading = ref(false)

// Initialize selected emails when emails change
watch(
  () => props.emails,
  (newEmails) => {
    if (newEmails && newEmails.length > 0) {
      selectedEmails.value = newEmails.map((e) => e.name)
    } else {
      selectedEmails.value = []
    }
  },
  { immediate: true }
)

const allSelected = computed(() => {
  return (
    props.emails.length > 0 &&
    selectedEmails.value.length === props.emails.length
  )
})

const customerName = computed(() => {
  if (!props.sourceDoc) return ""
  const first = props.sourceDoc.first_name || ""
  const last = props.sourceDoc.last_name || ""
  return `${first} ${last}`.trim() || props.sourceDoc.name || ""
})

const customerEmail = computed(() => {
  if (!props.sourceDoc) return ""
  return (
    props.sourceDoc.email ||
    props.sourceDoc.email_id ||
    props.sourceDoc.email_account ||
    ""
  )
})

const customerPhone = computed(() => {
  if (!props.sourceDoc) return ""
  return props.sourceDoc.mobile_no || props.sourceDoc.phone || ""
})

function toggleSelectAll() {
  if (allSelected.value) {
    selectedEmails.value = []
  } else {
    selectedEmails.value = props.emails.map((e) => e.name)
  }
}

function toggleEmail(emailName) {
  const index = selectedEmails.value.indexOf(emailName)
  if (index > -1) {
    selectedEmails.value.splice(index, 1)
  } else {
    selectedEmails.value.push(emailName)
  }
}

function closeDialog() {
  showDialog.value = false
  emit("close")
}

async function handleTransfer() {
  if (selectedEmails.value.length === 0) {
    return
  }

  isLoading.value = true
  try {
    emit("transfer", selectedEmails.value)
  } catch (error) {
    console.error("Error in transfer:", error)
  } finally {
    isLoading.value = false
  }
}
</script>

