import { setDayjsLocale } from './dayjs'

// Function to handle locale changes
export async function setLocale(locale) {
  if (!locale) return
  
  try {
    // Set dayjs locale
    await setDayjsLocale(locale)
    
    // Set Frappe locale if available
    if (window.frappe) {
      window.frappe.boot = window.frappe.boot || {}
      window.frappe.boot.lang = locale
    }
  } catch (e) {
    console.warn('Error setting locale:', e)
  }
}

// Initialize with default locale
const defaultLocale = window.frappe?.boot?.lang || window.navigator.language || 'en'
setLocale(defaultLocale) 