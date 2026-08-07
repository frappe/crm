import { ref, provide, inject } from 'vue'
import { createResource } from 'frappe-ui'

const COMPANY_KEY = Symbol('fc_company')
const LS_KEY = 'fc_active_company'

export function provideCompanyContext() {
  const company = ref(localStorage.getItem(LS_KEY) || '')

  function setCompany(name) {
    company.value = name
    localStorage.setItem(LS_KEY, name)
  }

  const companiesResource = createResource({
    url: 'crm.finance.api.get_accessible_companies',
    auto: true,
    onSuccess(data) {
      const names = (data || []).map(c => c.name)
      if (company.value && !names.includes(company.value)) {
        company.value = ''
        localStorage.removeItem(LS_KEY)
      }
      if (!company.value && names.length > 0) {
        setCompany(names[0])
      }
    },
  })

  provide(COMPANY_KEY, { company, setCompany, companiesResource })
  return { company, setCompany, companiesResource }
}

export function useCompanyContext() {
  return inject(COMPANY_KEY)
}
