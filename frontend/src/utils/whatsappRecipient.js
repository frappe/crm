import { createDialog } from '@/utils/dialogs'
import { watch } from 'vue'

// The server refuses to move a Lead or Deal off a number it has a WhatsApp
// conversation with (crm/api/whatsapp.py) until the request carries this.
export const CONFIRM_RECIPIENT_CHANGE = { confirm_whatsapp_recipient_change: 1 }

export function isRecipientChangeRefusal(error) {
  return error?.exc_type === 'WhatsAppRecipientChangeError'
}

export function confirmRecipientChange(error) {
  return new Promise((resolve) => {
    let confirmed = false
    const dialog = createDialog({
      title: __('Change WhatsApp recipient?'),
      message: error.messages?.[0],
      actions: [
        {
          label: __('Cancel'),
          onClick: ({ close }) => close(),
        },
        {
          label: __('Change'),
          variant: 'solid',
          theme: 'red',
          onClick: ({ close }) => {
            confirmed = true
            close()
          },
        },
      ],
    })
    const stop = watch(
      () => dialog.show,
      (show) => {
        if (show) return
        stop()
        resolve(confirmed)
      },
    )
  })
}

/**
 * Runs `request`, and if the server refuses because it would move a WhatsApp
 * conversation, asks the user and runs it again with their confirmation.
 * Resolves to undefined when the user backs out.
 *
 * @param {(extraParams?: object) => Promise<any>} request
 */
export async function withRecipientConfirmation(request) {
  try {
    return await request()
  } catch (error) {
    if (!isRecipientChangeRefusal(error)) throw error
    if (!(await confirmRecipientChange(error))) return
    return request(CONFIRM_RECIPIENT_CHANGE)
  }
}
