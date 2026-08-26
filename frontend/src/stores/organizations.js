import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive } from 'vue'
import { useRouter } from 'vue-router'

export const organizationsStore = defineStore('crm-organizations', () => {
  let organizationsByName = reactive({})

  const router = useRouter()

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
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
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
