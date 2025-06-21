"""
CRM Site Visit Form Controller - Server-side form management
Handles all form interactions, field changes, validations, and auto-population on server-side
"""

import json

import frappe
from frappe.utils import getdate, add_days, flt


@frappe.whitelist()
def get_field_properties(docname=None, user_agent=None, form_data=None):
    """Get dynamic field properties based on context, device, and workflow state"""
    properties = {}

    try:
        # Parse form data if provided
        if form_data and isinstance(form_data, str):
            form_data = json.loads(form_data)

        # Device-specific properties
        is_mobile = detect_mobile_device(user_agent)
        if is_mobile:
            properties.update(get_mobile_field_properties())

        # Document-specific properties
        if docname and frappe.db.exists('CRM Site Visit', docname):
            doc = frappe.get_doc('CRM Site Visit', docname)
            properties.update(get_document_context_properties(doc))

        # Form data-based properties
        if form_data:
            properties.update(get_form_data_properties(form_data))

        return {
            'success': True,
            'field_properties': properties,
            'is_mobile': is_mobile
        }

    except Exception as e:
        frappe.log_error(f"Failed to get field properties: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


def detect_mobile_device(user_agent):
    """Detect if request is from mobile device"""
    if not user_agent:
        return False

    mobile_indicators = ['Mobile', 'Android', 'iPhone', 'iPad', 'Windows Phone', 'BlackBerry']
    return any(indicator in user_agent for indicator in mobile_indicators)


def get_mobile_field_properties():
    """Get field properties optimized for mobile devices"""
    return {
        # Hide complex fields on mobile
        'planned_start_time': {'hidden': True},
        'planned_end_time': {'hidden': True},
        'location_accuracy': {'hidden': True},
        'check_in_latitude': {'hidden': True},
        'check_in_longitude': {'hidden': True},
        'check_out_latitude': {'hidden': True},
        'check_out_longitude': {'hidden': True},

        # Make essential fields required
        'visit_type': {'required': True, 'bold': True},
        'visit_purpose': {'required': True, 'bold': True},
        'reference_title': {'bold': True},

        # Simplify complex fields
        'visit_summary': {'description': 'Brief summary of the visit'},
        'next_steps': {'description': 'What needs to happen next?'},

        # Mobile-friendly input types
        'contact_phone': {'input_type': 'tel'},
        'contact_email': {'input_type': 'email'},
        'visit_date': {'input_type': 'date'}
    }


def get_document_context_properties(doc):
    """Get field properties based on document state and workflow"""
    properties = {}

    # Status-based properties
    if doc.status == 'Planned':
        properties.update({
            'visit_date': {'required': True, 'highlight': True},
            'visit_type': {'required': True},
            'sales_person': {'required': True},
            'reference_title': {'highlight': True}
        })

    elif doc.status == 'In Progress':
        properties.update({
            'check_in_time': {'readonly': True, 'highlight': True},
            'check_in_location': {'readonly': True},
            'visit_purpose': {'highlight': True},
            'agenda': {'description': 'Update as visit progresses'}
        })

    elif doc.status == 'Completed':
        properties.update({
            'visit_summary': {'required': True, 'highlight': True, 'bold': True},
            'lead_quality': {'required': True, 'highlight': True},
            'next_steps': {'highlight': True},
            'follow_up_required': {'highlight': True},
            'check_in_time': {'readonly': True},
            'check_out_time': {'readonly': True},
            'total_duration': {'readonly': True}
        })

    # Docstatus-based properties
    if doc.docstatus == 1:  # Submitted
        # Make most fields readonly after submission
        readonly_fields = [
            'visit_date', 'visit_type', 'reference_type', 'reference_name',
            'check_in_time', 'check_out_time', 'visit_summary', 'lead_quality'
        ]
        for field in readonly_fields:
            properties[field] = properties.get(field, {})
            properties[field]['readonly'] = True

    # Location-based properties
    if doc.check_in_latitude and doc.check_in_longitude:
        properties.update({
            'check_in_location': {'description': 'Click to view on map'},
            'location_accuracy': {'description': f'GPS accuracy: {doc.location_accuracy}'}
        })

    # Follow-up properties
    if doc.follow_up_required:
        properties.update({
            'follow_up_date': {'required': True, 'highlight': True},
            'follow_up_notes': {'description': 'What should be followed up?'}
        })

    return properties


def get_form_data_properties(form_data):
    """Get field properties based on current form data"""
    properties = {}

    # Reference-based properties
    if form_data.get('reference_type'):
        if form_data['reference_type'] == 'CRM Lead':
            properties.update({
                'lead_quality': {'required': True},
                'potential_value': {'description': 'Estimated deal value'},
                'probability_percentage': {'description': 'Conversion probability'}
            })
        elif form_data['reference_type'] == 'CRM Deal':
            properties.update({
                'probability_percentage': {'required': True},
                'potential_value': {'description': 'Current deal value'}
            })

    # Visit type-based properties
    if form_data.get('visit_type'):
        visit_type = form_data['visit_type']

        if visit_type == 'Demo/Presentation':
            properties.update({
                'demo_feedback': {'required': True},
                'technical_requirements': {'description': 'Any technical needs discussed'}
            })
        elif visit_type == 'Contract Signing':
            properties.update({
                'potential_value': {'required': True, 'highlight': True},
                'contract_details': {'required': True}
            })
        elif visit_type == 'Follow-up':
            properties.update({
                'previous_visit_reference': {'description': 'Link to previous visit'},
                'follow_up_outcome': {'required': True}
            })

    # Status-based conditional requirements
    if form_data.get('follow_up_required'):
        properties.update({
            'follow_up_date': {'required': True},
            'follow_up_notes': {'required': True}
        })

    return properties


@frappe.whitelist()
def get_dynamic_options(doctype, fieldname, filters=None, search_term=None, limit=50):
    """Get dynamic field options based on context and filters"""
    try:
        if filters and isinstance(filters, str):
            filters = json.loads(filters)

        options = []

        if doctype == 'CRM Site Visit':
            options = get_site_visit_field_options(fieldname, filters, search_term, limit)

        return {
            'success': True,
            'options': options
        }

    except Exception as e:
        frappe.log_error(f"Failed to get dynamic options: {str(e)}")
        return {
            'success': False,
            'message': str(e),
            'options': []
        }


def get_site_visit_field_options(fieldname, filters, search_term, limit):
    """Get options for site visit fields"""
    options = []

    if fieldname == 'reference_name':
        # Get filtered reference options based on reference_type
        ref_type = filters.get('reference_type')
        if ref_type:
            options = get_reference_options(ref_type, search_term, limit)

    elif fieldname == 'customer_address':
        # Get addresses for selected customer/organization
        organization = filters.get('organization')
        if organization:
            options = get_address_options(organization, search_term, limit)

    elif fieldname == 'sales_person':
        # Get active sales persons
        options = get_sales_person_options(search_term, limit)

    elif fieldname == 'territory':
        # Get active territories
        options = get_territory_options(search_term, limit)

    return options


def get_reference_options(ref_type, search_term, limit):
    """Get reference document options"""
    options = []

    try:
        fields_map = {
            'CRM Lead': ['name', 'lead_name', 'organization', 'email'],
            'CRM Deal': ['name', 'organization', 'deal_value'],
            'Customer': ['name', 'customer_name', 'customer_group']
        }

        if ref_type in fields_map:
            fields = fields_map[ref_type]
            filters = {'docstatus': ['!=', 2]}  # Exclude cancelled

            if search_term:
                # Add search filters
                if ref_type == 'CRM Lead':
                    filters['lead_name'] = ['like', f'%{search_term}%']
                elif ref_type == 'CRM Deal':
                    filters['organization'] = ['like', f'%{search_term}%']
                elif ref_type == 'Customer':
                    filters['customer_name'] = ['like', f'%{search_term}%']

            docs = frappe.get_all(ref_type,
                                  filters=filters,
                                  fields=fields,
                                  limit=limit,
                                  order_by='modified desc'
                                  )

            for doc in docs:
                label = get_reference_display_label(ref_type, doc)
                options.append({
                    'value': doc.name,
                    'label': label,
                    'description': get_reference_description(ref_type, doc)
                })

    except Exception as e:
        frappe.log_error(f"Failed to get reference options: {str(e)}")

    return options


def get_reference_display_label(ref_type, doc):
    """Get display label for reference document"""
    if ref_type == 'CRM Lead':
        return doc.get('lead_name') or doc.get('organization') or doc.name
    elif ref_type == 'CRM Deal':
        return doc.get('organization') or doc.name
    elif ref_type == 'Customer':
        return doc.get('customer_name') or doc.name
    else:
        return doc.name


def get_reference_description(ref_type, doc):
    """Get description for reference document"""
    if ref_type == 'CRM Lead':
        email = doc.get('email', '')
        org = doc.get('organization', '')
        return f"{org} ({email})" if org and email else (org or email)
    elif ref_type == 'CRM Deal':
        value = doc.get('deal_value')
        return f"Value: {frappe.utils.fmt_money(value)}" if value else ""
    elif ref_type == 'Customer':
        group = doc.get('customer_group', '')
        return f"Group: {group}" if group else ""
    else:
        return ""


@frappe.whitelist()
def handle_field_change(docname, fieldname, value, form_data=None):
    """Handle server-side field change events with comprehensive updates"""
    try:
        response = {
            'success': True,
            'field_updates': {},
            'messages': [],
            'validations': [],
            'field_properties': {}
        }

        # Parse form data
        if form_data and isinstance(form_data, str):
            form_data = json.loads(form_data)
        else:
            form_data = {}

        # Handle specific field changes
        if fieldname == 'reference_type':
            response.update(handle_reference_type_change(value, form_data))

        elif fieldname == 'reference_name':
            response.update(handle_reference_name_change(value, form_data))

        elif fieldname == 'customer_address':
            response.update(handle_customer_address_change(value, form_data))

        elif fieldname == 'organization':
            response.update(handle_organization_change(value, form_data))

        elif fieldname == 'follow_up_required':
            response.update(handle_follow_up_required_change(value, form_data))

        elif fieldname == 'visit_type':
            response.update(handle_visit_type_change(value, form_data))

        elif fieldname == 'visit_date':
            response.update(handle_visit_date_change(value, form_data))

        # Validate the change
        validation_result = validate_field_change(fieldname, value, form_data)
        if validation_result.get('errors'):
            response['validations'] = validation_result['errors']
        if validation_result.get('warnings'):
            response['messages'] = validation_result['warnings']

        return response

    except Exception as e:
        frappe.log_error(f"Field change handling failed: {fieldname}={value}: {str(e)}")
        return {
            'success': False,
            'message': str(e),
            'field_updates': {},
            'messages': [],
            'validations': []
        }


def handle_reference_type_change(value, form_data):
    """Handle reference type change"""
    return {
        'field_updates': {
            'reference_name': '',
            'reference_title': '',
            'contact_phone': '',
            'contact_email': '',
            'potential_value': ''
        },
        'messages': [f'Reference type changed to {value}. Please select a {value}.'],
        'field_properties': {
            'reference_name': {'required': True if value else False}
        }
    }


def handle_reference_name_change(value, form_data):
    """Handle reference name change with auto-population"""
    if not value:
        return {'field_updates': {}}

    ref_type = form_data.get('reference_type')
    if not ref_type:
        return {'field_updates': {}}

    try:
        # Get auto-population data
        from crm.api.site_visit_workflow import get_reference_metadata
        metadata = get_reference_metadata(ref_type, value)

        updates = metadata.get('auto_populate_data', {})

        # Only update empty fields to avoid overwriting user changes
        filtered_updates = {}
        for field, new_value in updates.items():
            if not form_data.get(field) and new_value:
                filtered_updates[field] = new_value

        return {
            'field_updates': filtered_updates,
            'messages': [f'Auto-populated fields from {ref_type}: {value}'] if filtered_updates else []
        }

    except Exception as e:
        frappe.log_error(f"Reference auto-population failed: {str(e)}")
        return {
            'field_updates': {},
            'messages': [f'Could not auto-populate from {ref_type}']
        }


def handle_customer_address_change(value, form_data):
    """Handle customer address change with address auto-population"""
    if not value:
        return {'field_updates': {}}

    try:
        addr = frappe.get_doc('Address', value)

        updates = {}
        if addr.address_line1:
            address_text = addr.address_line1
            if addr.address_line2:
                address_text += f'\n{addr.address_line2}'
            updates['visit_address'] = address_text

        if addr.city:
            updates['city'] = addr.city
        if addr.state:
            updates['state'] = addr.state
        if addr.country:
            updates['country'] = addr.country
        if addr.pincode:
            updates['pincode'] = addr.pincode

        return {
            'field_updates': updates,
            'messages': ['Auto-populated address fields'] if updates else []
        }

    except Exception as e:
        frappe.log_error(f"Address auto-population failed: {str(e)}")
        return {
            'field_updates': {},
            'messages': ['Could not auto-populate address']
        }


def handle_follow_up_required_change(value, form_data):
    """Handle follow-up required change"""
    if value and not form_data.get('follow_up_date'):
        # Auto-set follow-up date to next week
        visit_date = form_data.get('visit_date', frappe.utils.nowdate())
        follow_up_date = add_days(getdate(visit_date), 7)

        return {
            'field_updates': {'follow_up_date': follow_up_date},
            'messages': ['Auto-set follow-up date to next week'],
            'field_properties': {
                'follow_up_date': {'required': True},
                'follow_up_notes': {'required': True}
            }
        }
    elif not value:
        return {
            'field_updates': {'follow_up_date': ''},
            'field_properties': {
                'follow_up_date': {'required': False},
                'follow_up_notes': {'required': False}
            }
        }

    return {'field_updates': {}}


def handle_visit_type_change(value, form_data):
    """Handle visit type change with conditional field requirements"""
    field_properties = {}
    messages = []

    if value == 'Contract Signing':
        field_properties.update({
            'potential_value': {'required': True, 'highlight': True},
            'contract_details': {'required': True}
        })
        messages.append('Contract signing visits require potential value and contract details')

    elif value == 'Demo/Presentation':
        field_properties.update({
            'agenda': {'required': True},
            'demo_materials': {'description': 'List materials needed for demo'}
        })
        messages.append('Demo visits require agenda and preparation')

    elif value == 'Follow-up':
        field_properties.update({
            'previous_visit_reference': {'description': 'Reference to previous visit'},
            'follow_up_outcome': {'required': True}
        })

    return {
        'field_updates': {},
        'field_properties': field_properties,
        'messages': messages
    }


def validate_field_change(fieldname, value, form_data):
    """Validate field changes and return errors/warnings"""
    errors = []
    warnings = []

    if fieldname == 'follow_up_date' and value:
        if getdate(value) < getdate():
            errors.append('Follow-up date cannot be in the past')
        elif getdate(value) == getdate():
            warnings.append('Follow-up date is today - consider setting for future')

    elif fieldname == 'visit_date' and value:
        visit_date = getdate(value)
        if visit_date < add_days(getdate(), -30):
            warnings.append('Visit date is more than 30 days in the past')
        elif visit_date > add_days(getdate(), 365):
            warnings.append('Visit date is more than 1 year in the future')

    elif fieldname == 'potential_value' and value:
        if flt(value) <= 0:
            errors.append('Potential value must be greater than zero')
        elif flt(value) > 10000000:  # 10 million
            warnings.append('Very high potential value - please verify')

    elif fieldname == 'probability_percentage' and value:
        prob = flt(value)
        if prob < 0 or prob > 100:
            errors.append('Probability percentage must be between 0 and 100')
        elif prob == 0:
            warnings.append('0% probability - consider if visit is worthwhile')

    return {
        'errors': errors,
        'warnings': warnings
    }


@frappe.whitelist()
def auto_populate_form_data(reference_type, reference_name, customer_address=None):
    """Comprehensive auto-population of form data from various sources"""
    data = {}

    try:
        # Populate reference data
        if reference_type and reference_name:
            ref_data = get_reference_auto_populate_data(reference_type, reference_name)
            data.update(ref_data)

        # Populate address data
        if customer_address:
            addr_data = get_address_auto_populate_data(customer_address)
            data.update(addr_data)

        return {
            'success': True,
            'data': data
        }

    except Exception as e:
        frappe.log_error(f"Auto-population failed: {str(e)}")
        return {
            'success': False,
            'message': str(e),
            'data': {}
        }


def get_reference_auto_populate_data(reference_type, reference_name):
    """Get auto-populate data from reference document"""
    data = {}

    try:
        ref_doc = frappe.get_doc(reference_type, reference_name)

        if reference_type == 'CRM Lead':
            data.update({
                'reference_title': ref_doc.get('lead_name') or ref_doc.get('organization') or 'Unknown',
                'contact_phone': ref_doc.get('mobile_no') or ref_doc.get('phone'),
                'contact_email': ref_doc.get('email'),
                'city': ref_doc.get('city'),
                'state': ref_doc.get('state'),
                'country': ref_doc.get('country'),
                'organization': ref_doc.get('organization')
            })

            # Lead-specific fields
            if ref_doc.get('lead_owner'):
                data['sales_person'] = ref_doc.lead_owner
            if ref_doc.get('source'):
                data['lead_source'] = ref_doc.source

        elif reference_type == 'CRM Deal':
            data.update({
                'reference_title': ref_doc.get('organization') or ref_doc.name,
                'potential_value': ref_doc.get('deal_value'),
                'probability_percentage': ref_doc.get('probability'),
                'organization': ref_doc.get('organization')
            })

            # Deal-specific fields
            if ref_doc.get('deal_owner'):
                data['sales_person'] = ref_doc.deal_owner
            if ref_doc.get('territory'):
                data['territory'] = ref_doc.territory

        elif reference_type == 'Customer':
            data.update({
                'reference_title': ref_doc.get('customer_name') or 'Unknown',
                'organization': ref_doc.get('customer_name'),
                'customer_group': ref_doc.get('customer_group'),
                'territory': ref_doc.get('territory')
            })

            # Get primary contact for customer
            contact = frappe.db.get_value('Contact',
                                          {'link_doctype': 'Customer', 'link_name': reference_name,
                                           'is_primary_contact': 1},
                                          ['phone', 'email_id'], as_dict=True
                                          )
            if contact:
                data.update({
                    'contact_phone': contact.phone,
                    'contact_email': contact.email_id
                })

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None and v != ''}

    except Exception as e:
        frappe.log_error(f"Reference data population failed: {str(e)}")

    return data


def get_address_auto_populate_data(address_name):
    """Get auto-populate data from address"""
    data = {}

    try:
        addr = frappe.get_doc('Address', address_name)

        # Build address text
        address_lines = []
        if addr.address_line1:
            address_lines.append(addr.address_line1)
        if addr.address_line2:
            address_lines.append(addr.address_line2)

        data.update({
            'visit_address': '\n'.join(address_lines) if address_lines else '',
            'city': addr.city,
            'state': addr.state,
            'country': addr.country,
            'pincode': addr.pincode
        })

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None and v != ''}

    except Exception as e:
        frappe.log_error(f"Address data population failed: {str(e)}")

    return data


def get_address_options(organization, search_term, limit):
    """Get address options for organization"""
    options = []

    try:
        filters = {
            'link_doctype': ['in', ['Customer', 'Lead', 'Supplier']],
            'link_name': organization
        }

        if search_term:
            filters['address_title'] = ['like', f'%{search_term}%']

        addresses = frappe.get_all('Address',
                                   filters=filters,
                                   fields=['name', 'address_title', 'address_line1', 'city'],
                                   limit=limit
                                   )

        for addr in addresses:
            label = addr.address_title or addr.name
            description = f"{addr.address_line1}, {addr.city}" if addr.address_line1 and addr.city else ""

            options.append({
                'value': addr.name,
                'label': label,
                'description': description
            })

    except Exception as e:
        frappe.log_error(f"Failed to get address options: {str(e)}")

    return options


def get_sales_person_options(search_term, limit):
    """Get sales person options"""
    options = []

    try:
        filters = {'enabled': 1}
        if search_term:
            filters['name'] = ['like', f'%{search_term}%']

        users = frappe.get_all('User',
                               filters=filters,
                               fields=['name', 'full_name', 'email'],
                               limit=limit
                               )

        for user in users:
            label = user.full_name or user.name
            options.append({
                'value': user.name,
                'label': label,
                'description': user.email
            })

    except Exception as e:
        frappe.log_error(f"Failed to get sales person options: {str(e)}")

    return options


def get_territory_options(search_term, limit):
    """Get territory options"""
    options = []

    try:
        filters = {}
        if search_term:
            filters['territory_name'] = ['like', f'%{search_term}%']

        territories = frappe.get_all('Territory',
                                     filters=filters,
                                     fields=['name', 'territory_name', 'parent_territory'],
                                     limit=limit
                                     )

        for territory in territories:
            label = territory.territory_name or territory.name
            description = f"Parent: {territory.parent_territory}" if territory.parent_territory else ""

            options.append({
                'value': territory.name,
                'label': label,
                'description': description
            })

    except Exception as e:
        frappe.log_error(f"Failed to get territory options: {str(e)}")

    return options
