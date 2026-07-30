import { createResource } from 'frappe-ui'

export const filterableFields = createResource({
  url: 'crm.api.doc.get_filterable_fields',
  transform: (data) => {
    data = data
      .filter((field) => !field.fieldname.startsWith('_'))
      // `description` renders as a second line in the dropdown, which has no
      // max width, so a long one stretches the whole list.
      .map(({ description, ...field }) => {
        return {
          label: field.label,
          value: field.fieldname,
          ...field,
        }
      })
    return data
  },
})
