const { __ } = window

export function getParsedFields(data, doctype, doc, handlers = {}) {
  // Handle both array and object data structures
  let sectionList
  if (Array.isArray(data)) {
    // Modal data structure
    sectionList = data[0]?.sections || []
  } else {
    // Regular data structure
    sectionList = data?.sections?.[0]?.sections || []
  }

  if (!sectionList.length) {
    return []
  }
  
  sectionList.forEach((section) => {
    if (section.name == 'contacts_section') return
    
    if (Array.isArray(section.fields) && typeof section.fields[0] === 'string') {
      section.fields = section.fields.map(fieldName => {
        // Use fields_meta from the data response
        const field = (typeof section.fields_meta === 'object' && section.fields_meta[fieldName]) || 
                     (doc?.fields_meta && doc.fields_meta[fieldName]) || {}
        
        // Get translated field label
        const translatedLabel = __(field.label || fieldName.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '))
        
        // Determine placeholder verb based on field type
        const getPlaceholderVerb = (fieldtype) => {
          switch(fieldtype?.toLowerCase()) {
            case 'select':
            case 'link':
              return __('Select')
            case 'date':
            case 'datetime':
              return __('Set')
            default:
              return __('Enter')
          }
        }

        // Base field data with translations
        const fieldData = {
          name: fieldName,
          label: translatedLabel,
          type: field.fieldtype || 'text',
          all_properties: field || {},
          placeholder: field.placeholder || `${getPlaceholderVerb(field.fieldtype)} ${translatedLabel}`
        }

        // Handle owner fields (lead_owner and deal_owner)
        if (fieldName.endsWith('_owner')) {
          return {
            ...fieldData,
            type: fieldName,
            filters: {
              ignore_user_type: 1
            }
          }
        }

        // Handle gender field
        if (fieldName === 'gender') {
          return {
            ...fieldData,
            type: 'select',
            options: [
              { label: __('Male'), value: 'Male' },
              { label: __('Female'), value: 'Female' }
            ],
            placeholder: `${__('Select')} ${translatedLabel}`
          }
        }

        // Handle field types that need special treatment
        switch (field.fieldtype?.toLowerCase()) {
          case 'select':
            fieldData.type = 'select'
            if (field.options) {
              fieldData.options = field.options.split('\n').map(option => ({
                label: __(option),
                value: option
              }))
              if (!fieldData.options.find(opt => opt.value === '')) {
                fieldData.options.unshift({ label: '', value: '' })
              }
            }
            break

          case 'link':
            fieldData.type = 'link'
            fieldData.doctype = field.options
            // Add create/link handlers if needed based on doctype
            if (field.options === 'CRM Organization' && handlers.organization) {
              fieldData.create = handlers.organization.create
              fieldData.link = handlers.organization.link
            }
            break

          case 'date':
            fieldData.type = 'Date'
            fieldData.class = 'form-input w-full rounded border border-gray-100 bg-surface-gray-2 px-2 py-1.5 text-base text-ink-gray-8 placeholder-ink-gray-4 transition-colors hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:border-outline-gray-4 focus:bg-surface-white focus:shadow-sm focus:outline-none focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3'
            break

          case 'datetime':
            fieldData.type = 'Datetime'
            fieldData.class = 'form-input w-full rounded border border-gray-100 bg-surface-gray-2 px-2 py-1.5 text-base text-ink-gray-8 placeholder-ink-gray-4 transition-colors hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:border-outline-gray-4 focus:bg-surface-white focus:shadow-sm focus:outline-none focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3'
            break
        }

        return fieldData
      })
    }
  })
  
  return sectionList
}