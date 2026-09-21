<template>
  <div class="flex h-full flex-col gap-6 p-6">
    <div class="flex justify-between">
      <div class="flex w-9/12 items-center gap-1">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="name || __('New Account')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('back')"
        />
        <Badge
          v-if="account.isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
      <div class="flex w-3/12 justify-end">
        <Button
          v-if="account.isDirty || account.isNew"
          :loading="account.saving"
          :label="account.isNew ? __('Create') : __('Save')"
          variant="solid"
          @click="save"
        />
      </div>
    </div>
    <div v-if="account.loading" class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-8" />
    </div>
    <!-- p-1/-m-1 leaves the scroll box a little slack beyond the content, so a
         focused control's ring isn't clipped by the edge it sits flush against. -->
    <div v-else class="-m-1 flex-1 overflow-y-auto p-1">
      <AccountForm :controller="account" />
    </div>
  </div>
</template>

<script setup>
import { AccountForm, useAccount } from '@whatsapp/ui'
import { LoadingIndicator, toast } from 'frappe-ui'

const props = defineProps({
  // Empty renders a blank account that the first save creates.
  name: { type: String, default: '' },
})

const emit = defineEmits(['back', 'created'])

const account = useAccount({ name: () => props.name })

// The form shows a failed save under itself, so only success needs a toast.
async function save() {
  const wasNew = account.isNew
  const saved = await account.save()
  if (!saved) return
  if (wasNew) {
    toast.success(__('Account created'))
    emit('created', saved)
  } else {
    toast.success(__('Account updated'))
  }
}
</script>
