<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Email Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'profile-settings')"
        />
        <Badge
          v-if="isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div class="flex gap-2">
        <Button
          variant="solid"
          :label="__('Update')"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div>Emails</div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import { computed } from 'vue'

const emit = defineEmits(['updateStep'])

const isDirty = computed(() => {
  // check if emails or signature have changed
  return false
})

function update() {
  // update emails
}
</script>
