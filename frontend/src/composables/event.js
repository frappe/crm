import { usersStore } from '@/stores/users'
import { dayjs, createListResource } from 'frappe-ui'
import { sameArrayContents } from '@/utils'
import { computed, ref } from 'vue'

export const showEventModal = ref(false)
export const activeEvent = ref(null)

export function useEvent(doctype, docname) {
  const { getUser } = usersStore()

  const eventsResource = createListResource({
    doctype: 'Event',
    cache: ['calendar', docname],
    fields: [
      'name',
      'status',
      'subject',
      'description',
      'starts_on',
      'ends_on',
      'all_day',
      'event_type',
      'color',
      'owner',
      'reference_doctype',
      'reference_docname',
      'creation',
    ],
    filters: {
      reference_doctype: doctype,
      reference_docname: docname,
    },
    auto: true,
    orderBy: 'creation desc',
    onSuccess: (d) => {
      console.log(d)
    },
  })

  const eventParticipantsResource = createListResource({
    doctype: 'Event Participants',
    fields: ['*'],
    parent: 'Event',
  })

  const events = computed(() => {
    if (!eventsResource.data) return []
    const eventNames = eventsResource.data.map((e) => e.name)
    if (
      !eventParticipantsResource.data?.length ||
      eventsParticipantIsUpdated(eventNames)
    ) {
      eventParticipantsResource.update({
        filters: {
          parenttype: 'Event',
          parentfield: 'event_participants',
          parent: ['in', eventNames],
        },
      })
      !eventParticipantsResource.list.loading &&
        eventParticipantsResource.reload()
    } else {
      eventsResource.data.forEach((event) => {
        if (typeof event.owner !== 'object') {
          event.owner = {
            label: getUser(event.owner).full_name,
            image: getUser(event.owner).user_image,
            name: event.owner,
          }
        }

        event.event_participants = [
          ...eventParticipantsResource.data.filter(
            (participant) => participant.parent === event.name,
          ),
        ]

        event.participants = [
          event.owner,
          ...eventParticipantsResource.data
            .filter((participant) => participant.parent === event.name)
            .map((participant) => ({
              label: getUser(participant.email).full_name || participant.email,
              image: getUser(participant.email).user_image || '',
              name: participant.email,
            })),
        ]
      })
    }

    return eventsResource.data
  })

  function eventsParticipantIsUpdated(eventNames) {
    const parentFilter = eventParticipantsResource.filters?.parent?.[1]

    if (eventNames.length && !sameArrayContents(parentFilter, eventNames))
      return true

    let d = eventsResource.setValue.data
    if (!d) return false

    let newParticipants = d.event_participants.map((p) => p.name)
    let oldParticipants = eventParticipantsResource.data
      .filter((p) => p.parent === d.name)
      .map((p) => p.name)

    return !sameArrayContents(newParticipants, oldParticipants)
  }

  const startEndTime = (
    startTime,
    endTime,
    isFullDay = false,
    format = 'h:mm a',
  ) => {
    const start = dayjs(startTime)
    const end = dayjs(endTime)

    if (isFullDay) return __('All day')

    return `${start.format(format)} - ${end.format(format)}`
  }

  const startDate = (startTime, format = 'ddd, D MMM YYYY') => {
    const start = dayjs(startTime)
    return start.format(format)
  }

  return {
    eventsResource,
    eventParticipantsResource,
    events,
    startEndTime,
    startDate,
  }
}
