import { globalStore } from '@/stores/global'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { createListResource, createResource, toast } from 'frappe-ui'
import { defineStore } from 'pinia'
import { computed } from 'vue'

export type AvailabilityCategory = 'Active' | 'Away' | 'Unavailable'

export interface AvailabilityStatus {
  name: string
  category: AvailabilityCategory
  color: string
  enabled: 0 | 1
  position: number
}

interface AvailabilityEvent {
  user: string
  crm_availability: string | null
  crm_availability_changed_on: string
  crm_availability_changed_by: string
}

const dotColors: Record<string, string> = {
  black: 'bg-surface-gray-9',
  gray: 'bg-surface-gray-6',
  blue: 'bg-surface-blue-6',
  green: 'bg-surface-green-6',
  red: 'bg-surface-red-6',
  pink: 'bg-surface-pink-6',
  orange: 'bg-surface-orange-6',
  amber: 'bg-surface-amber-6',
  yellow: 'bg-surface-yellow-6',
  cyan: 'bg-surface-cyan-6',
  teal: 'bg-surface-teal-6',
  violet: 'bg-surface-violet-6',
  purple: 'bg-surface-purple-6',
}

export const availabilityStore = defineStore('crm-availability', () => {
  const session = sessionStore()
  const { users, getUser } = usersStore()
  const { $socket } = globalStore()

  const statuses = createListResource({
    doctype: 'CRM Availability Status',
    fields: ['name', 'category', 'color', 'enabled', 'position'],
    orderBy: 'position asc',
    cache: 'crm-availability-statuses',
    pageLength: 100,
    initialData: [],
    auto: true,
  })

  const enabledStatuses = computed<AvailabilityStatus[]>(() =>
    (statuses.data || []).filter((s: AvailabilityStatus) => s.enabled),
  )

  // users who never picked a status count as Active
  const defaultStatus = computed(
    () =>
      enabledStatuses.value.find((s) => s.category === 'Active')?.name || '',
  )

  function getStatus(name?: string | null): AvailabilityStatus | undefined {
    return (statuses.data || []).find(
      (s: AvailabilityStatus) => s.name === (name || defaultStatus.value),
    )
  }

  function userStatus(user?: string): AvailabilityStatus | undefined {
    return getStatus(getUser(user).crm_availability)
  }

  function dotColor(status?: AvailabilityStatus): string {
    return dotColors[status?.color || ''] || 'bg-surface-gray-6'
  }

  const myStatus = computed(() => userStatus()?.name || '')

  const setAvailability = createResource({ url: 'frappe.client.set_value' })

  function setMyStatus(status: string) {
    if (!status || status === myStatus.value) return
    const user = getUser()
    const previous = user.crm_availability
    user.crm_availability = status
    setAvailability.submit(
      {
        doctype: 'User',
        name: session.user,
        fieldname: 'crm_availability',
        value: status,
      },
      {
        onSuccess: () => toast.success(__('Status set to {0}', [__(status)])),
        onError: () => {
          user.crm_availability = previous
          toast.error(__('Could not update your status'))
        },
      },
    )
  }

  // statuses can be renamed, recategorised or disabled while a tab is open;
  // a rename also changes users' crm_availability
  $socket.on('crm_availability_statuses_updated', () => {
    statuses.reload()
    users.reload()
  })

  // events sent while the tab was offline are lost, so refetch after reconnecting
  $socket.io.on('reconnect', () => {
    statuses.reload()
    users.reload()
  })

  $socket.on('crm_availability_updated', (data: AvailabilityEvent) => {
    const user = getUser(data.user)
    user.crm_availability = data.crm_availability
    user.crm_availability_changed_on = data.crm_availability_changed_on

    const changedBySomeoneElse =
      data.user === session.user &&
      data.crm_availability_changed_by !== session.user
    if (changedBySomeoneElse) {
      const status = getStatus(data.crm_availability)?.name || ''
      toast.info(__('Your status was changed to {0}', [__(status)]))
    }
  })

  return {
    statuses,
    enabledStatuses,
    myStatus,
    getStatus,
    userStatus,
    dotColor,
    setMyStatus,
  }
})
