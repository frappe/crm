<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('CNPJ Enrichment') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Fill in Organization and Lead details from a CNPJ using the CPF.CNPJ API',
          )
        }}
        <a
          href="https://www.cpfcnpj.com.br/dev/"
          target="_blank"
          rel="noopener noreferrer"
          class="text-ink-gray-8 underline"
        >
          {{ __('API docs') }}
        </a>
      </p>
    </div>

    <div
      v-if="settings.get.loading"
      class="flex flex-1 items-center justify-center"
    >
      <LoadingIndicator class="size-8" />
    </div>
    <div v-else class="flex-1 flex flex-col gap-4 overflow-y-auto">
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Enable enrichment') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Turn on CNPJ enrichment for this site. When off, the Enrich from CNPJ button is hidden',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            :model-value="Boolean(settings.doc.enabled)"
            size="sm"
            @update:model-value="(value) => update('enabled', value)"
          />
        </div>
      </div>

      <div class="px-2">
        <Password
          v-model="settings.doc.api_token"
          :label="__('API token')"
          placeholder="************"
          autocomplete="off"
          :description="
            __(
              'A public sandbox token with fictitious data is available in the API docs.',
            )
          "
        />
      </div>

      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Auto-enrich new records') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __('Enrich automatically when a record with a CNPJ is created')
            }}
          </div>
        </div>
        <div>
          <Switch
            :model-value="Boolean(settings.doc.auto_enrich)"
            size="sm"
            :disabled="!settings.doc.enabled"
            @update:model-value="(value) => update('auto_enrich', value)"
          />
        </div>
      </div>

      <div class="px-2 w-48">
        <FormControl
          v-model.number="settings.doc.request_timeout"
          type="number"
          :label="__('Request timeout (seconds)')"
          placeholder="15"
        />
      </div>

      <div class="px-2">
        <Button variant="solid" :loading="settings.save.loading" @click="save">
          {{ __('Save') }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Button,
  createDocumentResource,
  FormControl,
  LoadingIndicator,
  Password,
  Switch,
  toast,
} from 'frappe-ui'

const settings = createDocumentResource({
  doctype: 'CRM Registry Enrichment Settings',
  name: 'CRM Registry Enrichment Settings',
  auto: true,
})

function update(fieldname, value) {
  settings.doc[fieldname] = value ? 1 : 0
  settings.save.submit(null, {
    onSuccess: () =>
      toast.success(
        value
          ? __('Setting enabled successfully')
          : __('Setting disabled successfully'),
      ),
    onError: (err) => toast.error(err.messages?.[0] || __('Could not save')),
  })
}

function save() {
  settings.save.submit(null, {
    onSuccess: () => toast.success(__('Settings saved successfully')),
    onError: (err) => toast.error(err.messages?.[0] || __('Could not save')),
  })
}
</script>
