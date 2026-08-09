/**
 * Reads boot-time values from the correct location depending on context:
 * - Standalone www page: vars are at window.* (set by Jinja boot injection)
 * - Frappe Desk embed (legacy): vars are at window.frappe.boot.*
 *
 * Desk embed is being phased out; the www path is the primary one.
 */

function getRoles() {
  // Standalone www page sets window.user.roles via the Jinja boot block
  if (window.user?.roles) return window.user.roles
  // Legacy Desk embed fallback
  if (window.frappe?.boot?.user?.roles) return window.frappe.boot.user.roles
  return []
}

function getSessionUser() {
  if (window.session?.user) return window.session.user
  if (window.frappe?.session?.user) return window.frappe.session.user
  return ''
}

function getSysdefaults() {
  if (window.sysdefaults) return window.sysdefaults
  if (window.frappe?.boot?.sysdefaults) return window.frappe.boot.sysdefaults
  return {}
}

function getLang() {
  if (window.frappe?.boot?.lang) return window.frappe.boot.lang
  return navigator.language?.split('-')[0] || 'en'
}

function isAdministrator() {
  return getSessionUser() === 'Administrator'
}

export function useBoot() {
  return {
    getRoles,
    getSessionUser,
    getSysdefaults,
    getLang,
    isAdministrator,
  }
}
