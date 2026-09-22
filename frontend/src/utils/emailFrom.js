export function resolveFromEmail(fromOptions, fromEmail, userEmail) {
  let isPermitted = (fromOptions || []).some((f) => f.value === fromEmail)
  return isPermitted ? fromEmail : userEmail
}

export function matchReceivingMailbox(fromOptions, recipients) {
  return (
    (fromOptions || []).find((f) => (recipients || []).includes(f.value))
      ?.value ?? null
  )
}
