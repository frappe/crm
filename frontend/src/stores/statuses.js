import { defineStore } from 'pinia'
import { createListResource } from 'frappe-ui'
import { h } from 'vue'
import { reactive } from 'vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { capture } from '@/telemetry'
import { translateDealStatus, getOriginalDealStatus } from '@/utils/dealStatusTranslations'
import { translateLeadStatus, getOriginalLeadStatus } from '@/utils/leadStatusTranslations'

export const statusesStore = defineStore('crm-statuses', () => {
  let leadStatusesByName = reactive({})
  let dealStatusesByName = reactive({})
  let communicationStatusesByName = reactive({})

  const leadStatuses = createListResource({
    doctype: 'CRM Lead Status',
    fields: ['name', 'color', 'position'],
    orderBy: 'position asc',
    cache: 'lead-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        status.colorClass = colorClasses(status.color)
        status.iconColorClass = colorClasses(status.color, true)
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
        status.colorClass = colorClasses(status.color)
        status.iconColorClass = colorClasses(status.color, true)
        dealStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  const communicationStatuses = createListResource({
    doctype: 'CRM Communication Status',
    fields: ['name'],
    cache: 'communication-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        communicationStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  function colorClasses(color, onlyIcon = false) {
    let textColor = `!text-${color}-600`
    if (color == 'black') {
      textColor = '!text-ink-gray-9'
    } else if (['gray', 'green'].includes(color)) {
      textColor = `!text-${color}-700`
    }

    let bgColor = `!bg-${color}-100 hover:!bg-${color}-200 active:!bg-${color}-300`

    return [textColor, onlyIcon ? '' : bgColor]
  }

  function getLeadStatus(name) {
    if (!name) {
      name = leadStatuses.data[0]?.name
    }
    return leadStatusesByName[name]
  }

  function getDealStatus(name) {
    if (!name) {
      name = dealStatuses.data[0]?.name
    }
    return dealStatusesByName[name]
  }

  function getCommunicationStatus(name) {
    if (!name) {
      name = communicationStatuses.data[0]?.name
    }
    return communicationStatusesByName[name]
  }

  function statusOptions(doctype, updateField, customStatuses = []) {
    let statusesMap = doctype === 'deal' ? dealStatusesByName : leadStatusesByName
    let statuses = customStatuses?.length ? customStatuses : Object.keys(statusesMap)
    
    return statuses.map((status) => ({
      label: doctype === 'deal' 
        ? translateDealStatus(statusesMap[status]?.name || status)
        : translateLeadStatus(statusesMap[status]?.name || status),
      value: status,
      onClick: () => {
        capture('status_changed', { doctype, status })
        updateField?.('status', statusesMap[status]?.name || status)
      },
      icon: () => h(IndicatorIcon, {
        class: statusesMap[status]?.iconColorClass || ['!text-gray-600']
      })
    }))
  }

  function getStatusLabel(doctype, status) {
    if (doctype === 'deal') {
      return translateDealStatus(status)
    }
    return translateLeadStatus(status)
  }

  function getOriginalStatusValue(doctype, translatedStatus) {
    if (doctype === 'deal') {
      return getOriginalDealStatus(translatedStatus)
    }
    return getOriginalLeadStatus(translatedStatus)
  }

  return {
    leadStatuses,
    dealStatuses,
    communicationStatuses,
    getLeadStatus,
    getDealStatus,
    getCommunicationStatus,
    statusOptions,
    getStatusLabel,
    getOriginalStatusValue,
  }
})
