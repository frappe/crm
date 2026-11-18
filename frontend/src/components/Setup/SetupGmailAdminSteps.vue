<template>
  <section
    class="flex flex-col gap-3 rounded-5 border border-outline-gray-2 p-3"
  >
    <div class="flex items-start gap-3">
      <div class="flex min-w-0 flex-1 flex-col gap-1">
        <h3 class="text-p-base-medium text-ink-gray-8">
          {{ __('Your Google Workspace admin must allow Frappe first') }}
        </h3>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'This is a one-time step. Send these steps to your admin, or follow them if you are the admin.',
            )
          }}
        </p>
      </div>
      <Button
        class="-mt-1"
        variant="ghost"
        icon="lucide-copy"
        :tooltip="__('Copy steps for your admin')"
        :aria-label="__('Copy steps for your admin')"
        @click="copy(stepsText, __('Steps copied'))"
      />
    </div>
    <ol class="flex list-decimal flex-col gap-5 pl-5">
      <li
        v-for="(step, i) in steps"
        :key="i"
        class="text-p-base text-ink-gray-6"
      >
        <div class="flex min-w-0 flex-col">
          <span class="text-p-base-medium text-ink-gray-8">
            {{ step.title }}
          </span>
          <p class="text-p-base text-ink-gray-6">{{ step.description }}</p>
          <Button
            v-if="i === 0"
            class="mt-1.5 self-start"
            variant="outline"
            :href="ADMIN_CONSOLE"
            icon-right="lucide-arrow-up-right"
            :label="__('Open Google Admin console')"
          />
          <div
            v-if="i === 1 && clientId"
            class="mt-1.5 flex items-center gap-1 rounded-4 bg-surface-gray-2 py-1 pl-2 pr-1"
          >
            <code class="min-w-0 flex-1 truncate text-sm text-ink-gray-8">
              {{ clientId }}
            </code>
            <Button
              variant="ghost"
              size="sm"
              icon="lucide-copy"
              :tooltip="__('Copy client ID')"
              :aria-label="__('Copy client ID')"
              @click="copy(clientId, __('Client ID copied'))"
            />
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>

<script setup>
import { Button, toast } from 'frappe-ui'
import { computed } from 'vue'

const ADMIN_CONSOLE = 'https://admin.google.com/ac/owl/list?tab=configuredApps'

const props = defineProps({
  // Frappe's Google client ID, for the admin to allow; none when Frappe Cloud didn't send it
  clientId: { type: String, default: null },
})

const steps = computed(() => [
  {
    title: __('Open API controls in the Admin console'),
    description: __('Sign in as a Google Workspace admin.'),
  },
  {
    title: __('Add Frappe as an app'),
    description: __('Click Configure new app and search for this client ID.'),
  },
  {
    title: __('Choose who can connect mailboxes'),
    description: __('All users, or the group that has the support mailbox.'),
  },
  {
    title: __('Set access to Trusted'),
    description: __(
      'Select Trusted and click Continue, then click Finish on the review screen.',
    ),
  },
])

const stepsText = computed(() =>
  [
    __(
      'Please allow Frappe to access Gmail for our team (one-time, about 2 minutes):',
    ),
    '1. ' +
      __('Open {0} (Security > API controls > Manage Third-Party App Access)', [
        ADMIN_CONSOLE,
      ]),
    '2. ' +
      (props.clientId
        ? __('Click Configure new app and search for this client ID: {0}', [
            props.clientId,
          ])
        : __('Click Configure new app and search for Frappe')),
    '3. ' +
      __(
        'Choose who can connect mailboxes (all users, or the group with the support mailbox)',
      ),
    '4. ' +
      __(
        'Select Trusted and click Continue, then click Finish on the review screen',
      ),
  ].join('\n'),
)

async function copy(text, done) {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(done)
  } catch {
    toast.error(__("Couldn't copy. Select the text and copy it yourself."))
  }
}
</script>
