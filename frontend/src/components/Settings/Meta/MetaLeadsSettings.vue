<template>
  <div class="flex h-full flex-col gap-6 overflow-y-auto py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Meta Lead Ads') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Facebook & Instagram lead forms: connect your account, pick pages, map fields — leads arrive in real time.',
          )
        }}
      </p>
    </div>

    <div class="flex flex-col gap-4 px-2">
      <!-- step 1: app credentials -->
      <div class="rounded-lg border border-outline-gray-2 p-4">
        <div class="mb-2 text-p-base-medium text-ink-gray-7">
          1. {{ __('Meta App (developers.facebook.com)') }}
        </div>
        <div class="grid grid-cols-2 gap-3">
          <FormControl v-model="appForm.app_id" type="text" :label="__('App ID')" />
          <FormControl
            v-model="appForm.app_secret"
            type="password"
            :label="__('App Secret')"
            :placeholder="status.data?.has_app_secret ? __('•••••• (saved — type to replace)') : ''"
          />
        </div>
        <div class="mt-3 flex items-center gap-2">
          <Button :label="__('Save app')" variant="solid" @click="saveApp" />
        </div>
        <div v-if="status.data?.webhook_url" class="mt-3 flex flex-col gap-1 text-p-sm text-ink-gray-6">
          <div class="flex items-center gap-2">
            <span class="shrink-0 font-medium">{{ __('Webhook URL') }}:</span>
            <span class="truncate">{{ status.data.webhook_url }}</span>
            <Button variant="ghost" icon="lucide-copy" @click="copy(status.data.webhook_url)" />
          </div>
          <div class="flex items-center gap-2">
            <span class="shrink-0 font-medium">{{ __('Verify token') }}:</span>
            <span class="truncate">{{ status.data.webhook_verify_token }}</span>
            <Button
              variant="ghost"
              icon="lucide-copy"
              @click="copy(status.data.webhook_verify_token)"
            />
          </div>
          <span class="text-ink-gray-5">
            {{ __('Configure them in the app under Webhooks → Page → subscribe to "leadgen".') }}
          </span>
        </div>
      </div>

      <!-- step 2: connect -->
      <div class="flex items-center justify-between rounded-lg border border-outline-gray-2 p-4">
        <div class="flex flex-col">
          <span class="text-p-base-medium text-ink-gray-7">
            2.
            {{
              status.data?.connected
                ? __('Connected as {0}', [status.data.connected_user_name])
                : __('Connect Facebook')
            }}
          </span>
          <span v-if="status.data?.connected" class="text-p-sm text-ink-gray-5">
            {{ __('Token valid until') }}: {{ status.data.user_token_expires_at || '—' }}
          </span>
          <span v-if="metaError" class="text-p-sm text-ink-red-5">{{ metaError }}</span>
        </div>
        <div class="flex gap-2">
          <Button
            v-if="status.data?.connected"
            :label="__('Refresh pages')"
            :loading="refreshing"
            @click="refreshPages"
          />
          <Button
            :variant="status.data?.connected ? 'outline' : 'solid'"
            :label="status.data?.connected ? __('Reconnect') : __('Connect with Facebook')"
            @click="connect"
          />
          <Button
            v-if="status.data?.connected"
            variant="ghost"
            :label="__('Disconnect')"
            @click="disconnect"
          />
        </div>
      </div>

      <!-- step 3: pages & forms -->
      <div class="rounded-lg border border-outline-gray-2 p-4">
        <div class="mb-2 text-p-base-medium text-ink-gray-7">
          3. {{ __('Pages & lead forms') }}
        </div>
        <div v-if="pages.data?.length" class="flex flex-col gap-3">
          <div
            v-for="page in pages.data"
            :key="page.name"
            class="rounded-md border border-outline-gray-1 p-3"
          >
            <div class="flex items-center justify-between gap-3">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="truncate text-p-base-medium text-ink-gray-8">
                    {{ page.page_name }}
                  </span>
                  <Badge
                    v-if="page.sync_enabled && page.webhook_subscribed"
                    :label="__('Real-time')"
                    theme="green"
                    size="sm"
                  />
                  <Badge v-if="!page.token_valid" :label="__('Token expired')" theme="red" size="sm" />
                </div>
                <div class="text-p-sm text-ink-gray-5">
                  {{ page.category }} · {{ page.forms.length }} {{ __('forms') }}
                  <span v-if="page.last_webhook_at">
                    · {{ __('last lead webhook') }}: {{ page.last_webhook_at }}
                  </span>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-p-sm text-ink-gray-5">{{ __('Sync leads') }}</span>
                <Switch
                  :modelValue="Boolean(page.sync_enabled)"
                  @update:modelValue="(v) => togglePage(page, v)"
                />
              </div>
            </div>
            <div v-if="page.forms.length" class="mt-2 divide-y divide-outline-gray-1">
              <div
                v-for="form in page.forms"
                :key="form.name"
                class="flex items-center justify-between gap-3 py-1.5"
              >
                <div class="min-w-0">
                  <span class="truncate text-p-base text-ink-gray-7">{{ form.form_name }}</span>
                  <span class="ml-2 text-p-sm text-ink-gray-4">
                    {{ form.lead_count }} {{ __('leads') }}
                    <template v-if="form.form_status"> · {{ form.form_status }}</template>
                  </span>
                </div>
                <div class="flex shrink-0 gap-1">
                  <Button :label="__('Map fields')" size="sm" @click="openMapping(form.name)" />
                  <Button
                    :label="__('Backfill 90d')"
                    size="sm"
                    variant="ghost"
                    @click="backfill(form.name)"
                  />
                  <Button
                    :label="__('Test lead')"
                    size="sm"
                    variant="ghost"
                    @click="testLead(form.name)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-p-base text-ink-gray-5">
          {{ __('No pages yet — connect Facebook above.') }}
        </div>
        <div class="mt-3 rounded-md bg-surface-gray-1 p-3 text-p-sm text-ink-gray-5">
          {{
            __(
              'Leads not arriving despite a valid connection? In Meta Business Settings → Integrations → Leads Access, the business may restrict who can read leads: assign this CRM there. Also make sure the connecting user has the Advertise role on the page.',
            )
          }}
        </div>
      </div>

      <!-- failure logs -->
      <details class="rounded-lg border border-outline-gray-2 p-4">
        <summary class="cursor-pointer text-p-base-medium text-ink-gray-7">
          {{ __('Sync failures') }}
        </summary>
        <div v-if="failures.data?.length" class="mt-2 flex flex-col gap-2">
          <div
            v-for="log in failures.data"
            :key="log.name"
            class="rounded bg-surface-gray-1 p-2 text-p-sm text-ink-gray-6"
          >
            <div class="font-medium">{{ log.creation }} · {{ log.type }}</div>
            <div class="truncate">{{ log.lead_data }}</div>
          </div>
        </div>
        <div v-else class="mt-2 text-p-sm text-ink-gray-5">{{ __('No failures. 🎉') }}</div>
        <Button class="mt-2" variant="ghost" :label="__('Reload')" @click="failures.reload()" />
      </details>
    </div>
  </div>

  <!-- field mapping dialog -->
  <Dialog v-model="showMapping" :options="{ title: mappingTitle, size: 'xl' }">
    <template #body-content>
      <div class="flex flex-col gap-2">
        <div class="mb-1 text-p-sm text-ink-gray-5">
          {{ __('Map every form question to a CRM Lead field. First name is required.') }}
        </div>
        <div
          v-for="q in mappingQuestions"
          :key="q.key"
          class="grid grid-cols-2 items-center gap-3"
        >
          <div class="min-w-0">
            <div class="truncate text-p-base text-ink-gray-8">{{ q.label || q.key }}</div>
            <div class="text-p-sm text-ink-gray-4">{{ q.type }}</div>
          </div>
          <FormControl
            v-model="q.mapped_to_crm_field"
            type="select"
            :options="leadFieldOptions"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <Button class="w-full" variant="solid" :label="__('Save mapping')" @click="saveMapping" />
    </template>
  </Dialog>
</template>

<script setup>
import { createResource, Dialog, FormControl, Switch, toast } from 'frappe-ui'
import { ref, computed } from 'vue'

const metaError = ref(new URLSearchParams(window.location.search).get('meta_error') || '')

const appForm = ref({ app_id: '', app_secret: '' })

const status = createResource({
  url: 'crm.integrations.meta.api.get_status',
  auto: true,
  onSuccess: (data) => {
    appForm.value.app_id = data.app_id
  },
})

const pages = createResource({
  url: 'crm.integrations.meta.api.get_pages',
  auto: true,
})

const failures = createResource({
  url: 'crm.integrations.meta.api.get_failure_logs',
  auto: true,
})

function copy(text) {
  navigator.clipboard?.writeText(text)
  toast.success(__('Copied'))
}

function saveApp() {
  createResource({
    url: 'crm.integrations.meta.api.save_app_settings',
    params: { app_id: appForm.value.app_id, app_secret: appForm.value.app_secret },
    auto: true,
    onSuccess: () => {
      appForm.value.app_secret = ''
      toast.success(__('Saved'))
      status.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to save')),
  })
}

function connect() {
  createResource({
    url: 'crm.integrations.meta.oauth.get_login_url',
    auto: true,
    onSuccess: (data) => (window.location.href = data.login_url),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to start login')),
  })
}

function disconnect() {
  createResource({
    url: 'crm.integrations.meta.api.disconnect',
    auto: true,
    onSuccess: () => {
      toast.success(__('Disconnected'))
      status.reload()
    },
  })
}

const refreshing = ref(false)
function refreshPages() {
  refreshing.value = true
  createResource({
    url: 'crm.integrations.meta.api.refresh_pages',
    auto: true,
    onSuccess: () => {
      refreshing.value = false
      toast.success(__('Pages refreshed'))
      pages.reload()
    },
    onError: (e) => {
      refreshing.value = false
      toast.error(e.messages?.[0] || __('Failed to refresh'))
    },
  })
}

function togglePage(page, enabled) {
  createResource({
    url: 'crm.integrations.meta.api.set_page_sync',
    params: { page_id: page.name, enabled },
    auto: true,
    onSuccess: () => pages.reload(),
    onError: (e) => {
      toast.error(e.messages?.[0] || __('Failed to update page'))
      pages.reload()
    },
  })
}

function testLead(formId) {
  createResource({
    url: 'crm.integrations.meta.api.create_test_lead',
    params: { form_id: formId },
    auto: true,
    onSuccess: () =>
      toast.success(__('Test lead created — it should arrive via webhook in moments')),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to create test lead')),
  })
}

function backfill(formId) {
  createResource({
    url: 'crm.integrations.meta.api.backfill',
    params: { form_id: formId },
    auto: true,
    onSuccess: () => toast.success(__('Backfill started — leads will appear shortly')),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to start backfill')),
  })
}

// --- mapping dialog ---
const showMapping = ref(false)
const mappingFormId = ref(null)
const mappingTitle = ref('')
const mappingQuestions = ref([])
const leadFields = ref([])

const leadFieldOptions = computed(() => [
  { label: __('— not synced —'), value: '' },
  ...leadFields.value.map((f) => ({ label: f.label, value: f.fieldname })),
])

function openMapping(formId) {
  createResource({
    url: 'crm.integrations.meta.api.get_form_mapping',
    params: { form_id: formId },
    auto: true,
    onSuccess: (data) => {
      mappingFormId.value = data.name
      mappingTitle.value = data.form_name
      mappingQuestions.value = data.questions
      leadFields.value = data.lead_fields
      showMapping.value = true
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to load form')),
  })
}

function saveMapping() {
  const mapping = {}
  for (const q of mappingQuestions.value) {
    mapping[q.key] = q.mapped_to_crm_field || ''
  }
  createResource({
    url: 'crm.integrations.meta.api.save_form_mapping',
    params: { form_id: mappingFormId.value, mapping },
    auto: true,
    onSuccess: () => {
      showMapping.value = false
      toast.success(__('Mapping saved'))
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to save mapping')),
  })
}
</script>
