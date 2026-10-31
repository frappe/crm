// Stands in for the desk's `frappe/i18n` when a test imports a CRM desk contribution.
export const __ = (...args) => globalThis.__(...args)
