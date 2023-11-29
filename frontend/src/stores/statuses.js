import { defineStore } from 'pinia'
import { createListResource } from 'frappe-ui'
import { reactive, h } from 'vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'

export const statusesStore = defineStore('crm-statuses', () => {
  let leadStatusesByName = reactive({})
  let dealStatusesByName = reactive({})

  const leadStatuses = createListResource({
    doctype: 'CRM Lead Status',
    fields: ['name', 'color', 'position'],
    orderBy: 'position asc',
    cache: 'lead-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        status.color =
          status.color == 'black'
            ? '!text-gray-900'
            : `!text-${status.color}-600`
        leadStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  const dealStatuses = createListResource({
    doctype: 'CRM Deal Status',
    fields: ['name', 'color', 'position'],
    orderBy: 'position asc',
    cache: 'deal-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        status.color =
          status.color == 'black'
            ? '!text-gray-900'
            : `!text-${status.color}-600`
        dealStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  function getLeadStatus(name) {
    return leadStatusesByName[name]
  }

  function getDealStatus(name) {
    return dealStatusesByName[name]
  }

  function statusOptions(doctype, action) {
    let statusesByName =
      doctype == 'deal' ? dealStatusesByName : leadStatusesByName
    let options = []
    for (const status in statusesByName) {
      options.push({
        label: statusesByName[status].name,
        icon: () => h(IndicatorIcon, { class: statusesByName[status].color }),
        onClick: () => {
          action && action('status', statusesByName[status].name)
        },
      })
    }
    return options
  }

  return {
    leadStatuses,
    dealStatuses,
    getLeadStatus,
    getDealStatus,
    statusOptions,
  }
})
