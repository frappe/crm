import { sessionStore } from '@/stores/session'
import { interpolateTemplate } from '@/utils'
import { createResource } from 'frappe-ui'

export const defaultEmailSubjects = {
  'CRM Lead': '{{ lead_name }} (#{{ name }})',
  'CRM Deal': '{{ organization }} (#{{ name }})',
}

export const emailSubjectFields = {
  'CRM Lead': 'crm_lead_email_subject',
  'CRM Deal': 'crm_deal_email_subject',
}

// The current user's own subject formats, set in Profile → Email Settings
export const userEmailSubjects = createResource({
  url: 'frappe.client.get_value',
  makeParams: () => ({
    doctype: 'User',
    filters: { name: sessionStore().user },
    fieldname: Object.values(emailSubjectFields),
  }),
  cache: 'user-email-subjects',
})

export function loadUserEmailSubjects() {
  if (!userEmailSubjects.fetched && !userEmailSubjects.loading) {
    userEmailSubjects.fetch()
  }
}

// Drop empty brackets and stray separators left behind by empty fields
function tidy(subject) {
  return subject
    .replace(/\(\s*#?\s*\)|\[\s*#?\s*\]/g, '')
    .replace(/\s+/g, ' ')
    .replace(/^[\s\-–—|:·,]+|[\s\-–—|:·,]+$/g, '')
    .trim()
}

function fallbackSubject(doc) {
  const prefix = doc?.lead_name || doc?.organization || ''
  return `${prefix} (#${doc?.name})`
}

export function renderEmailSubject(template, doc) {
  if (!template) return fallbackSubject(doc)
  return tidy(interpolateTemplate(template, doc)) || fallbackSubject(doc)
}

export function getEmailSubject(doctype, doc) {
  const template = userEmailSubjects.data?.[emailSubjectFields[doctype]]
  return renderEmailSubject(template, doc)
}
