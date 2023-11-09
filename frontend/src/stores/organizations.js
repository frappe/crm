import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive, computed } from 'vue'

export const organizationsStore = defineStore('crm-organizations', () => {
  let organizationsByName = reactive({})

  const organizations = createResource({
    url: 'crm.api.session.get_organizations',
    cache: 'organizations',
    initialData: [],
    transform(organizations) {
      for (let organization of organizations) {
        organizationsByName[organization.name] = organization
      }
      return organizations
    },
    onError(error) {
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
      }
    },
  })
  organizations.fetch()

  function getOrganization(name) {
    return organizationsByName[name]
  }

  function getOrganizationOptions() {
    return [
      { label: '---', value: '' },
      ...organizations.data?.map((org) => ({
        label: org.name,
        value: org.name,
      })),
    ]
  }

  return {
    organizations,
    getOrganizationOptions,
    getOrganization,
  }
})
