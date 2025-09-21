import { createResource } from 'frappe-ui'

export const filterableFields = createResource({
  url: 'crm.api.doc.get_filterable_fields',
  transform: (data) => {
    data = data
      .filter((field) => !field.fieldname.startsWith('_'))
      .map((field) => {
        return {
          label: field.label,
          value: field.fieldname,
          ...field,
        }
      })
    return data
  },
})
