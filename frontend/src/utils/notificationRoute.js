// Where a notification opens. A notification about a task that is not tied to a lead or
// deal has no reference_name, and a Lead route with an empty leadId makes Vue Router throw
// while the list renders, so such a notification opens the Tasks list instead.
export function notificationRoute(notification) {
  if (!notification.reference_name) {
    return { name: 'Tasks' }
  }

  const params =
    notification.route_name === 'Deal'
      ? { dealId: notification.reference_name }
      : { leadId: notification.reference_name }

  return {
    name: notification.route_name,
    params,
    hash: notification.hash,
  }
}
