import { globalStore } from '@/stores/global'

export function formatNumberIntoCurrency(value, currency) {
  if (!value) return ''
  
  const { boot } = globalStore()
  const numberFormat = boot?.sysdefaults?.number_format || '# ###.##'
  
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currency || 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    numberingSystem: numberFormat.includes(',') ? 'latn' : undefined
  }).format(value)
} 