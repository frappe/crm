import { sessionStore } from '@/stores/session'
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

// Marks where a field came out empty so only the text around it is cleaned up
const EMPTY = '\u0000'
const SEPARATORS = '[\\s\\-–—|:·,]*'
const emptyInBrackets = new RegExp(`[(\\[]\\s*#?\\s*${EMPTY}\\s*[)\\]]`, 'g')
const leadingEmpty = new RegExp(`^${SEPARATORS}${EMPTY}${SEPARATORS}`)
const emptyWithSeparator = new RegExp(`${SEPARATORS}${EMPTY}`, 'g')

function fillFields(template, doc) {
  return template.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, key) => {
    const value = doc?.[key]
    return value === undefined || value === null || value === ''
      ? EMPTY
      : String(value)
  })
}

function removeEmptyFields(subject) {
  if (!subject.includes(EMPTY)) return subject.trim()
  return subject
    .replace(emptyInBrackets, '')
    .replace(leadingEmpty, '')
    .replace(emptyWithSeparator, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function fallbackSubject(doc) {
  const prefix = doc?.lead_name || doc?.organization || ''
  return `${prefix} (#${doc?.name})`
}

export function renderEmailSubject(template, doc) {
  if (!template) return fallbackSubject(doc)
  return removeEmptyFields(fillFields(template, doc)) || fallbackSubject(doc)
}

export function getEmailSubject(doctype, doc) {
  const template = userEmailSubjects.data?.[emailSubjectFields[doctype]]
  return renderEmailSubject(template, doc)
}
