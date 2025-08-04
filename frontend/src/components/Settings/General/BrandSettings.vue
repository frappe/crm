<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex px-2 justify-between">
      <div class="flex items-center gap-1 -ml-4 w-9/12">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Brand settings')"
          size="md"
          @click="() => emit('updateStep', 'general-settings')"
          class="text-xl !h-7 font-semibold hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5"
        />
        <Badge
          v-if="settings.isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Update')"
          icon-left="plus"
          variant="solid"
          :disabled="!settings.isDirty"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <!-- Fields -->
    <div class="flex flex-1 flex-col p-2 gap-4 overflow-y-auto">
      <div class="flex w-full">
        <FormControl
          type="text"
          class="w-1/2"
          v-model="settings.doc.brand_name"
          :label="__('Brand name')"
        />
      </div>

      <!-- logo -->
      <div class="flex flex-col justify-between gap-4">
        <span class="text-base font-semibold text-ink-gray-8">
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
        <span class="text-base font-semibold text-ink-gray-8">
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
    </div>
    <div v-if="errorMessage">
      <ErrorMessage :message="__(errorMessage)" />
    </div>
  </div>
</template>
<script setup>
import ImageUploader from '@/components/Controls/ImageUploader.vue'
import { FormControl, ErrorMessage } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'
import { ref } from 'vue'

const { _settings: settings, setupBrand } = getSettings()

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
      setupBrand()
    },
  })
}

const emit = defineEmits(['updateStep'])
const errorMessage = ref('')
</script>
