import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

export const customersStore = defineStore('customers', () => {
  let customersByName = reactive({})

  const customers = createResource({
    url: 'next_crm.api.session.get_customers',
    cache: 'customers',
    initialData: [],
    auto: true,
    transform(customers) {
      for (let customer of customers) {
        customerByName[customer.name] = customer
      }
      return customers
    },
    onError(error) {
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
      }
    },
  })

  function getCustomer(name) {
    return customersByName[name]
  }

  return {
    customers,
    getCustomer,
  }
})
