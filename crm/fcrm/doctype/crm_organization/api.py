import frappe

@frappe.whitelist()
def get_organization(name):
    doc = frappe.get_doc('CRM Organization', name)
    fields_meta = {
        'organization_name': {
            'label': 'Organization Name',
            'placeholder': 'Enter Organization Name'
        },
        'website': {
            'label': 'Website',
            'placeholder': 'Enter Website'
        },
        'territory': {
            'label': 'Territory',
            'placeholder': 'Select Territory'
        },
        'industry': {
            'label': 'Industry',
            'placeholder': 'Select Industry'
        },
        'no_of_employees': {
            'label': 'No. of Employees',
            'placeholder': 'Select No. of Employees'
        },
        'address': {
            'label': 'Address',
            'placeholder': 'Select Address'
        },
        'currency': {
            'label': 'Currency',
            'placeholder': 'Select Currency'
        },
        'annual_revenue': {
            'label': 'Annual Revenue',
            'placeholder': 'Enter Annual Revenue'
        },
        'organization_logo': {
            'label': 'Organization Logo',
            'placeholder': 'Upload Organization Logo'
        }
    }
    doc.fields_meta = fields_meta
    return doc 