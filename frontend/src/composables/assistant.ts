import { createResource } from 'frappe-ui'
import { ref, shallowRef } from 'vue'
import type { ChangedRecords } from '@/utils/assistantChanges'

// the Flow assistant panel, shared so any page can open it with a message typed in
export const assistantOpen = ref(false)
export const assistantPrompt = ref('')
export const flowInstalled = ref(false)
// Flow's logo from its app entry, shown when the window is minimized
export const flowLogo = ref('')
// what the assistant's latest reply changed; lists and record pages reload from it
export const assistantChanges = shallowRef<ChangedRecords | null>(null)

let checkedFlow = false

export function openAssistant(prompt = ''): void {
  assistantPrompt.value = prompt
  assistantOpen.value = true
}

// Flow is a separate app before Frappe 17 and part of the framework after; either way the
// user may use it when they can read their chats
export function checkFlowInstalled(): void {
  if (checkedFlow) return
  checkedFlow = true
  createResource({
    url: 'frappe.client.get_count',
    params: { doctype: 'Flow Session' },
    auto: true,
    onSuccess: () => (flowInstalled.value = true),
  })
  createResource({
    url: 'frappe.apps.get_apps',
    auto: true,
    onSuccess: (apps: { name: string; logo?: string }[]) => {
      flowLogo.value = apps.find((app) => app.name === 'flow')?.logo ?? ''
    },
  })
}
