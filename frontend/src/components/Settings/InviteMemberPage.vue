<template>
  <div class="flex h-full flex-col gap-8 p-8">
    <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
      {{ __('Send Invites To') }}
    </h2>
    <div class="flex-1 overflow-y-auto">
      <MultiValueInput
        v-model="invitees"
        :validate="validateEmail"
        :error-message="
          (value) => __('{0} is an invalid email address', [value])
        "
      />
      <FormControl
        type="select"
        class="mt-4"
        v-model="role"
        variant="outline"
        :label="__('Invite as')"
        :options="[
          { label: __('Regular Access'), value: 'Sales User' },
          { label: __('Manager Access'), value: 'Sales Manager' },
          { label: __('Admin Access'), value: 'Administrator' },
        ]"
      />
      <ErrorMessage class="mt-2" v-if="error" :message="error" />
    </div>
    <div class="flex flex-row-reverse">
      <Button :label="__('Send Invites')" variant="solid" @click="update" />
    </div>
  </div>
</template>
<script setup>
import MultiValueInput from '@/components/Controls/MultiValueInput.vue'
import { validateEmail } from '@/utils'
import { FormControl } from 'frappe-ui'
import { ref } from 'vue'

const invitees = ref([])
const role = ref('Sales User')
const error = ref(null)
</script>
