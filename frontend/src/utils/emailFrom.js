export function resolveFromEmail(fromOptions, fromEmail, userEmail) {
  let isPermitted = (fromOptions || []).some((f) => f.value === fromEmail)
  return isPermitted ? fromEmail : userEmail
}

function bareAddress(value) {
  let match = value.match(/<([^>]+)>/)
  return (match ? match[1] : value).trim().toLowerCase()
}

export function matchReceivingMailbox(fromOptions, recipients) {
  let addresses = (recipients || []).map(bareAddress)
  return (
    (fromOptions || []).find((f) => addresses.includes(bareAddress(f.value)))
      ?.value ?? null
  )
}
