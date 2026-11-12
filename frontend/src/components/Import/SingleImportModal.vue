<template>
  <Dialog v-model:open="show" :size="'2xl'">
    <template #title>
      <div class="text-xl font-semibold text-ink-gray-9">
        {{ __('Single Import') }}
      </div>
    </template>
    <template #default>
      <div class="flex flex-col gap-4 py-2">
        <p class="text-sm text-ink-gray-6">
          {{ __('Create and import a single record. Corresponding Contact and Organization records will be automatically created or linked.') }}
        </p>

        <form @submit.prevent="submit" class="flex flex-col gap-4">
          <!-- Row 1: Name & Designation -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <FormControl
              type="text"
              :label="__('First Name')"
              v-model="form.first_name"
              :placeholder="__('e.g. John')"
              :required="!form.organization"
            />
            <FormControl
              type="text"
              :label="__('Last Name')"
              v-model="form.last_name"
              :placeholder="__('e.g. Doe')"
            />
            <FormControl
              type="text"
              :label="__('Designation')"
              v-model="form.designation"
              :placeholder="__('e.g. Director')"
            />
          </div>

          <!-- Row 2: Status & ID -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormControl
              type="select"
              :label="__('Status')"
              v-model="form.status"
              :options="statusOptions"
            />
            <FormControl
              type="text"
              :label="__('ID (Optional)')"
              v-model="form.id"
              :placeholder="__('Auto-generated if empty')"
            />
          </div>

          <!-- Row 3: Contact details -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormControl
              type="email"
              :label="__('Email')"
              v-model="form.email"
              :placeholder="__('john@example.com')"
            />
            <FormControl
              type="text"
              :label="__('Mobile Number')"
              v-model="form.mobile_no"
              :placeholder="__('+1 555-0100')"
            />
          </div>

          <!-- Row 4: Organization & Website -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormControl
              type="text"
              :label="__('Organization Name')"
              v-model="form.organization"
              :placeholder="__('e.g. ABC Technology')"
            />
            <FormControl
              type="text"
              :label="__('Website')"
              v-model="form.website"
              :placeholder="__('https://example.com')"
            />
          </div>

          <!-- Row 5: Address -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <FormControl
              type="text"
              :label="__('City')"
              v-model="form.city"
              :placeholder="__('e.g. New York')"
            />
            <FormControl
              type="text"
              :label="__('State')"
              v-model="form.state"
              :placeholder="__('e.g. NY')"
            />
            <FormControl
              type="text"
              :label="__('Country')"
              v-model="form.country"
              :placeholder="__('e.g. United States')"
            />
          </div>

          <ErrorMessage v-if="error" :message="error" />
        </form>
      </div>
    </template>
    <template #actions>
      <div class="flex w-full justify-end gap-2">
        <Button
          variant="subtle"
          :label="__('Cancel')"
          :disabled="loading"
          @click="show = false"
        />
        <Button
          variant="solid"
          :label="__('Import Record')"
          :loading="loading"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, FormControl, ErrorMessage, call, toast } from 'frappe-ui'
import { ref, reactive, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'success'])

const show = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const loading = ref(false)
const error = ref('')

const statusOptions = [
  { label: 'New', value: 'New' },
  { label: 'Contacted', value: 'Contacted' },
  { label: 'Qualified', value: 'Qualified' },
  { label: 'Nurture', value: 'Nurture' },
  { label: 'Unqualified', value: 'Unqualified' },
  { label: 'Junk', value: 'Junk' },
]

const form = reactive({
  first_name: '',
  last_name: '',
  designation: '',
  id: '',
  status: 'New',
  email: '',
  mobile_no: '',
  organization: '',
  website: '',
  city: '',
  state: '',
  country: '',
})

function resetForm() {
  form.first_name = ''
  form.last_name = ''
  form.designation = ''
  form.id = ''
  form.status = 'New'
  form.email = ''
  form.mobile_no = ''
  form.organization = ''
  form.website = ''
  form.city = ''
  form.state = ''
  form.country = ''
  error.value = ''
}

async function submit() {
  error.value = ''
  if (!form.first_name && !form.organization && !form.email) {
    error.value = __('Please provide at least a First Name, Organization Name, or Email.')
    return
  }

  loading.value = true
  try {
    const res = await call('crm.api.import_data.execute_single_import', {
      data: { ...form },
    })
    toast.success(__('Record imported successfully!'))
    resetForm()
    show.value = false
    emit('success', res)
  } catch (err) {
    console.error(err)
    error.value = err.messages?.[0] || err.message || __('Failed to import record.')
  } finally {
    loading.value = false
  }
}
</script>

