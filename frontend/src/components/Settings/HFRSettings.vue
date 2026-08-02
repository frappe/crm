<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex justify-between items-start px-2">
      <div class="flex flex-col gap-1">
        <h2 class="text-2xl-semibold leading-none text-ink-gray-8">
          {{ __('HFR Integration') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Connect to the Kenya Health Facility Registry (HFR) via the HIE to pre-fill Organisation and Lead records from verified registry data.') }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Badge
          v-if="isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
        <Button
          v-if="isDirty"
          variant="solid"
          :label="__('Save Changes')"
          :loading="saving"
          @click="save"
        />
      </div>
    </div>

    <div v-if="settings.loading" class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-8" />
    </div>

    <div v-else class="flex-1 overflow-y-auto flex flex-col">

      <!-- Enable toggle -->
      <div class="flex items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7">{{ __('Enable HFR Integration') }}</div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Allow Sales Agents to search the Health Facility Registry when creating Organisations and Leads.') }}
          </div>
        </div>
        <Switch v-model="form.hfr_enabled" size="sm" @update:modelValue="markDirty" />
      </div>

      <template v-if="form.hfr_enabled">
        <div class="h-px border-t mx-2 border-outline-elevation-2" />
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('HIE Credentials') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('HIE Base URL') }}</label>
              <FormControl
                v-model="form.hfr_url"
                type="text"
                placeholder="https://hie.example.health"
                class="flex-1"
                @input="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('HFR Fetch Path') }}</label>
              <FormControl
                v-model="form.hfr_fetch_path"
                type="text"
                placeholder="/v1/hfr/facilities"
                class="flex-1"
                @input="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('HIE Username') }}</label>
              <FormControl
                v-model="form.hfr_username"
                type="text"
                class="flex-1"
                @input="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('HIE Password') }}</label>
              <FormControl
                v-model="form.hfr_password"
                type="password"
                :placeholder="__('Leave blank to keep existing')"
                class="flex-1"
                @input="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                {{ __('JWT Expiry') }}
                <span class="text-ink-gray-4 ml-1">{{ __('(seconds)') }}</span>
              </label>
              <FormControl
                v-model="form.hfr_jwt_expiry"
                type="number"
                placeholder="20000"
                class="flex-1"
                @input="markDirty"
              />
            </div>
          </div>
        </div>
      </template>

      <div v-if="saveError" class="mx-2 mt-2">
        <ErrorMessage :message="saveError" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import {
  Badge,
  Button,
  createResource,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'

const isDirty = ref(false)
const saving = ref(false)
const saveError = ref('')

const form = reactive({
  hfr_enabled: 0,
  hfr_url: '',
  hfr_fetch_path: '/v1/hfr/facilities',
  hfr_username: '',
  hfr_password: '',
  hfr_jwt_expiry: 20000,
})

const settings = createResource({
  url: 'crm.api.hfr.get_hfr_settings',
  auto: true,
  onSuccess(data) {
    Object.assign(form, data)
    form.hfr_password = ''
    isDirty.value = false
  },
})

const saveResource = createResource({
  url: 'crm.api.hfr.update_hfr_settings',
  method: 'POST',
  onSuccess() {
    isDirty.value = false
    saving.value = false
    saveError.value = ''
    settings.reload()
    toast.success(__('HFR settings saved'))
  },
  onError(err) {
    saveError.value = (err && err.message) || __('Failed to save settings')
    saving.value = false
  },
})

function markDirty() {
  isDirty.value = true
  saveError.value = ''
}

function save() {
  saving.value = true
  saveError.value = ''
  const payload = { ...form }
  if (!payload.hfr_password) delete payload.hfr_password
  saveResource.submit({ settings: payload })
}
</script>
