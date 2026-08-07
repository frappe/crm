/**
 * Reads currency/locale from frappe.boot so all formatting respects the
 * system default instead of being hardcoded to a specific region.
 */
function getSysDefaults() {
  return window.frappe?.boot?.sysdefaults ?? {}
}

function getLang() {
  // frappe.boot.lang is a BCP-47 tag like "en", "sw", "ar"
  return window.frappe?.boot?.lang || 'en'
}

export function useCurrency() {
  function formatCurrency(amount, currency) {
    if (amount == null) return '—'
    const cur = currency || getSysDefaults().currency || 'USD'
    const lang = getLang()
    try {
      return new Intl.NumberFormat(lang, {
        style: 'currency',
        currency: cur,
        maximumFractionDigits: 0,
      }).format(amount)
    } catch {
      return cur + ' ' + Number(amount).toLocaleString()
    }
  }

  return { formatCurrency }
}
