import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

export const organizationsStore = defineStore('crm-organizations', () => {
  let organizationsByName = reactive({})

  const organizations = createResource({
    url: 'crm.api.session.get_organizations',
    cache: 'organizations',
    initialData: [],
    auto: true,
    transform(organizations) {
      for (let organization of organizations) {
        organizationsByName[organization.name] = organization
      }
      return organizations
    },
    onError(error) {
      const isAuthError = ['AuthenticationError', 'PermissionError'].includes(
        error?.exc_type,
      )

      if (isAuthError) {
        window.location.href = '/login?redirect-to=/crm'
      }
    },
  })

  function getOrganization(name) {
    return organizationsByName[name]
  }

  return {
    organizations,
    getOrganization,
  }
})
