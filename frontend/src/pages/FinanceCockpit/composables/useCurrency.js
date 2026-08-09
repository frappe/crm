import { useBoot } from './useBoot.js'

export function useCurrency() {
  const { getSysdefaults, getLang } = useBoot()

  function formatCurrency(amount, currency) {
    if (amount == null) return '—'
    const cur = currency || getSysdefaults().currency || 'USD'
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
