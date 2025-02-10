const { __ } = window

export function getParsedFields(data, doctype, doc, handlers = {}) {
  // Handle both array and object data structures
  let sectionList
  if (Array.isArray(data)) {
    // Check if data is already the sections list
    if (data[0]?.fields || data[0]?.contacts) {
      sectionList = data
    } else {
      // Modal data structure
      sectionList = data[0]?.sections || []
    }
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
        
        // Base field data with translations
        const fieldData = {
          name: fieldName,
          label: translatedLabel,
          type: field.fieldtype ? capitalizeFieldType(field.fieldtype) : 'Text',
          all_properties: field || {},
        }

        // Handle owner fields
        if (fieldName.endsWith('_owner')) {
          fieldData.type = 'Link'
          fieldData.options = 'User'
          fieldData.filters = {
            ignore_user_type: 1
          }
          return fieldData
        }

        // Handle field types that need special treatment
        const fieldType = field.fieldtype?.toLowerCase() || ''
        switch (fieldType) {
          case 'select':
            fieldData.type = 'Select'
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
            fieldData.type = 'Link'
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

          case 'check':
            fieldData.type = 'Check'
            break
        }

        return fieldData
      })
    }
  })
  
  return sectionList
}

// Helper function to capitalize field types consistently
function capitalizeFieldType(type) {
  const typeMap = {
    'select': 'Select',
    'link': 'Link',
    'date': 'Date',
    'datetime': 'Datetime',
    'check': 'Check',
    'text': 'Text',
    // Add other field types as needed
  }
  return typeMap[type.toLowerCase()] || type
}