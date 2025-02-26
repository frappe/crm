<template>
  <div class="flex h-full flex-col gap-8 p-8 text-ink-gray-9">
    <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
      {{ __('General') }}
      <Badge
        v-if="settings.isDirty"
        :label="__('Not Saved')"
        variant="subtle"
        theme="orange"
      />
    </h2>

    <div v-if="settings.doc" class="flex-1 flex flex-col gap-8 overflow-y-auto">
      <div class="flex w-full">
        <FormControl
          type="text"
          class="w-1/2"
          v-model="settings.doc.brand_name"
          :label="__('Brand Name')"
        />
      </div>

      <!-- logo -->

      <div class="flex flex-col justify-between gap-4">
        <span class="text-base font-semibold text-ink-gray-9">
          {{ __('Logo') }}
        </span>
        <div class="flex flex-1 gap-5">
          <div
            class="flex items-center justify-center rounded border border-outline-gray-modals px-10 py-2"
          >
            <img
              :src="settings.doc?.brand_logo || '/assets/crm/images/logo.png'"
              alt="Logo"
              class="size-8 rounded"
            />
          </div>
          <div class="flex flex-1 flex-col gap-2">
            <ImageUploader
              label="Favicon"
              image_type="image/ico"
              :image_url="settings.doc?.brand_logo"
              @upload="(url) => (settings.doc.brand_logo = url)"
              @remove="() => (settings.doc.brand_logo = '')"
            />
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Appears in the left sidebar. Recommended size is 32x32 px in PNG or SVG',
                )
              }}
            </span>
          </div>
        </div>
      </div>

      <!-- favicon -->

      <div class="flex flex-col justify-between gap-4">
        <span class="text-base font-semibold text-ink-gray-9">
          {{ __('Favicon') }}
        </span>
        <div class="flex flex-1 gap-5">
          <div
            class="flex items-center justify-center rounded border border-outline-gray-modals px-10 py-2"
          >
            <img
              :src="settings.doc?.favicon || '/assets/crm/images/logo.png'"
              alt="Favicon"
              class="size-8 rounded"
            />
          </div>
          <div class="flex flex-1 flex-col gap-2">
            <ImageUploader
              label="Favicon"
              image_type="image/ico"
              :image_url="settings.doc?.favicon"
              @upload="(url) => (settings.doc.favicon = url)"
              @remove="() => (settings.doc.favicon = '')"
            />
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Appears next to the title in your browser tab. Recommended size is 32x32 px in PNG or ICO',
                )
              }}
            </span>
          </div>
        </div>
      </div>

      <!-- Home actions -->

      <div class="flex flex-col justify-between gap-4">
        <span class="text-base font-semibold text-ink-gray-9">
          {{ __('Home actions') }}
        </span>
        <div class="flex flex-1">
          <Grid
            v-model="settings.doc.dropdown_items"
            doctype="CRM Dropdown Item"
            parentDoctype="FCRM Settings"
          />
        </div>
      </div>
    </div>

    <div class="flex justify-between flex-row-reverse">
      <Button
        variant="solid"
        :label="__('Update')"
        :disabled="!settings.isDirty"
        @click="updateSettings"
      />
      <ErrorMessage :message="settings.save.error" />
    </div>
  </div>
</template>
<script setup>
import ImageUploader from '@/components/Controls/ImageUploader.vue'
import Grid from '@/components/Controls/Grid.vue'
import { FormControl, Badge, ErrorMessage } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'

const { _settings: settings, setupBrand } = getSettings()

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
      setupBrand()
    },
  })
}
</script>
