"""
CRM Site Visit Workflow API - Server-side workflow management
Handles all workflow transitions, validations, and state management on server-side
"""

import frappe
import requests
from frappe import _
from frappe.utils import now_datetime, getdate, add_days


@frappe.whitelist()
def get_form_metadata(docname=None, reference_type=None, reference_name=None):
    """Get complete form metadata and workflow state for client rendering"""
    metadata = {
        'workflow_state': {},
        'available_actions': [],
        'reference_data': {},
        'validation_rules': {},
        'form_guidance': {},
        'field_properties': {}
    }

    try:
        # If editing existing document
        if docname and frappe.db.exists('CRM Site Visit', docname):
            doc = frappe.get_doc('CRM Site Visit', docname)
            metadata['workflow_state'] = get_workflow_metadata(doc)
            metadata['available_actions'] = get_available_actions(doc)
            metadata['form_guidance'] = get_form_guidance(doc)
            metadata['field_properties'] = get_context_field_properties(doc)

        # If creating new with reference
        if reference_type and reference_name:
            metadata['reference_data'] = get_reference_metadata(reference_type, reference_name)

        # Get validation rules
        metadata['validation_rules'] = get_validation_rules()

        return {
            'success': True,
            'metadata': metadata
        }

    except Exception as e:
        frappe.log_error(f"Failed to get form metadata: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


def get_workflow_metadata(doc):
    """Get comprehensive workflow state and progress information"""
    workflow_state = {
        'current_status': doc.status,
        'docstatus': doc.docstatus,
        'docstatus_name': get_docstatus_name(doc.docstatus),
        'workflow_stage': get_workflow_stage_name(doc),
        'progress_percentage': get_workflow_progress_percentage(doc),
        'next_step_hint': get_next_step_hint(doc),

        # Action capabilities
        'can_checkin': doc.status == 'Planned' and not doc.check_in_time,
        'can_checkout': doc.status == 'In Progress' and doc.check_in_time and not doc.check_out_time,
        'can_submit': doc.status == 'Completed' and doc.docstatus == 0 and doc.check_out_time,
        'can_cancel': doc.docstatus == 0,

        # Data completeness
        'has_location': bool(doc.check_in_latitude and doc.check_in_longitude),
        'has_summary': bool(doc.visit_summary),
        'has_followup': bool(doc.follow_up_required and doc.follow_up_date),

        # Time tracking
        'is_checked_in': bool(doc.check_in_time),
        'is_checked_out': bool(doc.check_out_time),
        'duration_seconds': doc.total_duration or 0,
        'duration_formatted': format_duration(doc.total_duration) if doc.total_duration else "0 min"
    }

    return workflow_state


def get_available_actions(doc):
    """Get list of available workflow actions with detailed configuration"""
    actions = []

    # Check-in action
    if doc.status == 'Planned' and not doc.check_in_time:
        actions.append({
            'action': 'checkin',
            'label': 'Check In',
            'icon': 'map-pin',
            'primary': True,
            'requires_location': True,
            'requires_confirmation': False,
            'button_class': 'btn-primary',
            'description': 'Mark arrival at customer location'
        })

        # Manual location option
        actions.append({
            'action': 'manual_checkin',
            'label': 'Manual Check-In',
            'icon': 'edit',
            'primary': False,
            'requires_location': False,
            'requires_confirmation': True,
            'button_class': 'btn-secondary',
            'description': 'Check-in without GPS location'
        })

    # Check-out action
    if doc.status == 'In Progress' and doc.check_in_time and not doc.check_out_time:
        actions.append({
            'action': 'checkout',
            'label': 'Check Out',
            'icon': 'check-circle',
            'primary': True,
            'requires_location': True,
            'requires_summary': True,
            'button_class': 'btn-success',
            'description': 'Complete the visit and record outcome'
        })

    # Submit action
    if doc.status == 'Completed' and doc.docstatus == 0 and doc.check_out_time:
        actions.append({
            'action': 'submit',
            'label': 'Submit Visit',
            'icon': 'file-check',
            'primary': True,
            'requires_confirmation': True,
            'button_class': 'btn-primary',
            'description': 'Finalize the visit record and trigger follow-ups'
        })

        # Quick submit with summary
        actions.append({
            'action': 'quick_submit',
            'label': 'Complete & Submit',
            'icon': 'zap',
            'primary': False,
            'requires_summary': True,
            'button_class': 'btn-success',
            'description': 'Add summary and submit in one step'
        })

    # Calendar actions
    if not doc.is_new():
        if doc.calendar_event:
            actions.append({
                'action': 'view_calendar',
                'label': 'View Calendar Event',
                'icon': 'calendar',
                'primary': False,
                'button_class': 'btn-default',
                'description': 'Open related calendar event'
            })
        else:
            actions.append({
                'action': 'create_calendar',
                'label': 'Create Calendar Event',
                'icon': 'calendar-plus',
                'primary': False,
                'button_class': 'btn-default',
                'description': 'Create calendar event for this visit'
            })

    # Follow-up actions
    if doc.status == 'Completed' and doc.follow_up_required and doc.follow_up_date:
        actions.append({
            'action': 'create_followup',
            'label': 'Create Follow-up Task',
            'icon': 'bell',
            'primary': False,
            'button_class': 'btn-info',
            'description': 'Create follow-up task for sales team'
        })

    return actions


def get_form_guidance(doc):
    """Get contextual form guidance messages"""
    guidance = {
        'message': '',
        'type': 'info',  # info, warning, success, danger
        'show_progress': True,
        'workflow_hints': []
    }

    if doc.is_new():
        guidance.update({
            'message': '📝 <strong>Step 1:</strong> Fill in visit details and save as draft. You can plan the visit and add customer details.',
            'type': 'info',
            'workflow_hints': [
                'Choose visit type and purpose',
                'Select customer or lead reference',
                'Set visit date and time',
                'Add location details if available'
            ]
        })
    else:
        status_guidance = {
            'Planned': {
                'message': '📍 <strong>Step 2:</strong> Visit is planned. Use "Check In" when you arrive at the location to start the visit.',
                'type': 'info',
                'hints': [
                    'Review customer details before departure',
                    'Check location and contact information',
                    'Use Check In button when you arrive'
                ]
            },
            'In Progress': {
                'message': '🏃 <strong>Step 3:</strong> Visit is in progress. Use "Check Out" when you complete the visit.',
                'type': 'warning',
                'hints': [
                    'Conduct your meeting or demonstration',
                    'Take notes for visit summary',
                    'Use Check Out when finished'
                ]
            },
            'Completed': {
                'message': '✅ <strong>Step 4:</strong> Visit completed! You can now <strong>Submit</strong> this document to finalize the record and trigger follow-up actions.' if doc.docstatus == 0 else '🎉 <strong>Complete:</strong> Visit has been submitted and finalized. All workflow actions have been triggered.',
                'type': 'success',
                'hints': [
                    'Add visit summary and outcome',
                    'Set lead quality if applicable',
                    'Submit to trigger follow-ups'
                ] if doc.docstatus == 0 else [
                    'Visit record is finalized',
                    'Follow-up tasks created',
                    'Analytics updated'
                ]
            },
            'Cancelled': {
                'message': '❌ <strong>Cancelled:</strong> This visit has been cancelled.',
                'type': 'danger',
                'hints': ['Visit was cancelled and will not be processed']
            },
            'Postponed': {
                'message': '⏳ <strong>Postponed:</strong> This visit has been postponed. Update the visit date when rescheduled.',
                'type': 'warning',
                'hints': [
                    'Update visit date when rescheduled',
                    'Notify customer of new timing',
                    'Change status back to Planned when ready'
                ]
            }
        }

        if doc.status in status_guidance:
            guidance.update(status_guidance[doc.status])
            guidance['workflow_hints'] = status_guidance[doc.status]['hints']

    return guidance


@frappe.whitelist()
def perform_workflow_action(docname, action, **kwargs):
    """Unified endpoint for all workflow actions with comprehensive error handling"""
    try:
        doc = frappe.get_doc('CRM Site Visit', docname)

        # Check permissions
        if not doc.has_permission('write'):
            frappe.throw(_("Insufficient permissions to perform this action"))

        # Route to specific action handlers
        if action == 'checkin':
            return handle_checkin(doc, **kwargs)
        elif action == 'manual_checkin':
            return handle_manual_checkin(doc, **kwargs)
        elif action == 'checkout':
            return handle_checkout(doc, **kwargs)
        elif action == 'submit':
            return handle_submission(doc, **kwargs)
        elif action == 'quick_submit':
            return handle_quick_submission(doc, **kwargs)
        elif action == 'create_followup':
            return handle_create_followup(doc, **kwargs)
        elif action == 'create_calendar':
            return handle_create_calendar(doc, **kwargs)
        else:
            frappe.throw(_("Invalid workflow action: {0}").format(action))

    except Exception as e:
        frappe.log_error(f"Workflow action failed: {action} for {docname}: {str(e)}")
        return {
            'success': False,
            'message': f"Action failed: {str(e)}",
            'action': action
        }


def handle_create_followup(doc, **kwargs):
    """Create follow-up task based on visit outcome"""
    try:
        # Validate prerequisites
        if not doc.follow_up_required:
            frappe.throw(_("Follow-up is not marked as required for this visit"))

        if not doc.follow_up_date:
            frappe.throw(_("Follow-up date is required to create follow-up task"))

        if doc.status != 'Completed':
            frappe.throw(_("Visit must be completed before creating follow-up tasks"))

        # Check if follow-up task already exists
        existing_task = frappe.db.exists('Task', {
            'reference_type': 'CRM Site Visit',
            'reference_name': doc.name
        })

        if existing_task:
            return {
                'success': False,
                'message': f'Follow-up task already exists: {existing_task}',
                'existing_task': existing_task
            }

        # Determine task assignment
        assigned_to = kwargs.get('assigned_to') or doc.sales_person or frappe.session.user

        # Create task document
        task = frappe.new_doc('Task')
        task.update({
            'subject': f'Follow-up: {doc.reference_title or doc.name}',
            'description': f"""Follow-up task for site visit: {doc.name}

Visit Summary: {doc.visit_summary or 'No summary provided'}
Next Steps: {doc.next_steps or 'No specific next steps defined'}
Lead Quality: {doc.lead_quality or 'Not specified'}

Visit Details:
- Visit Date: {doc.visit_date}
- Duration: {format_duration(doc.total_duration) if doc.total_duration else 'Not recorded'}
- Location: {doc.check_in_location or 'Not recorded'}

Reference: {doc.reference_type} - {doc.reference_name if doc.reference_name else 'None'}
""",
            'status': 'Open',
            'priority': 'Medium',
            'exp_start_date': doc.follow_up_date,
            'exp_end_date': add_days(doc.follow_up_date, 7),  # Default 1 week to complete
            'reference_type': 'CRM Site Visit',
            'reference_name': doc.name,
            'assigned_to': assigned_to
        })

        # Set priority based on lead quality
        if doc.lead_quality == 'Hot':
            task.priority = 'High'
        elif doc.lead_quality == 'Cold':
            task.priority = 'Low'

        # Add project if visit is linked to a deal with project
        if doc.reference_type == 'CRM Deal' and doc.reference_name:
            deal = frappe.get_doc('CRM Deal', doc.reference_name)
            if hasattr(deal, 'project') and deal.project:
                task.project = deal.project

        task.insert(ignore_permissions=True)

        # Update the visit document to link the task
        doc.db_set('follow_up_task', task.name)

        return {
            'success': True,
            'message': f'Follow-up task created successfully: {task.name}',
            'task_name': task.name,
            'task_subject': task.subject,
            'assigned_to': assigned_to,
            'due_date': doc.follow_up_date
        }

    except Exception as e:
        frappe.log_error(f"Failed to create follow-up task for {doc.name}: {str(e)}")
        return {
            'success': False,
            'message': f"Failed to create follow-up task: {str(e)}"
        }


def handle_create_calendar(doc, **kwargs):
    """Create calendar event for the site visit"""
    try:
        # Validate prerequisites
        if not doc.visit_date:
            frappe.throw(_("Visit date is required to create calendar event"))

        # Check if calendar event already exists
        if doc.calendar_event:
            existing_event = frappe.db.exists('Event', doc.calendar_event)
            if existing_event:
                return {
                    'success': False,
                    'message': f'Calendar event already exists: {doc.calendar_event}',
                    'existing_event': doc.calendar_event
                }

        # Determine event timing
        visit_date = getdate(doc.visit_date)
        start_time = kwargs.get('start_time', '10:00:00')  # Default start time
        duration_hours = kwargs.get('duration_hours', 2)  # Default 2 hours

        # Parse start time and calculate end time
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(visit_date, datetime.strptime(start_time, '%H:%M:%S').time())
        end_datetime = start_datetime + timedelta(hours=duration_hours)

        # Create event description
        description = f"""Site Visit: {doc.reference_title or doc.name}

Visit Details:
- Type: {doc.visit_type}
- Purpose: {doc.visit_purpose or 'Not specified'}
- Sales Person: {doc.sales_person}

Customer Information:
- Reference: {doc.reference_type} - {doc.reference_name if doc.reference_name else 'None'}
- Contact: {doc.contact_phone or 'Not provided'}
- Email: {doc.contact_email or 'Not provided'}

Location:
- Address: {doc.customer_address or 'To be determined'}
- City: {doc.city or ''}
- State: {doc.state or ''}

Notes: {doc.visit_notes or 'No additional notes'}
"""

        # Create calendar event
        event = frappe.new_doc('Event')
        event.update({
            'subject': f'Site Visit: {doc.reference_title or doc.name}',
            'description': description,
            'starts_on': start_datetime,
            'ends_on': end_datetime,
            'event_type': 'Public',
            'event_category': 'Meeting',
            'status': 'Open',
            'reference_doctype': 'CRM Site Visit',
            'reference_docname': doc.name
        })

        # Add attendees
        attendees = []

        # Add sales person
        if doc.sales_person:
            sales_person_email = frappe.db.get_value('User', doc.sales_person, 'email')
            if sales_person_email:
                attendees.append({
                    'reference_doctype': 'User',
                    'reference_docname': doc.sales_person,
                    'email': sales_person_email
                })

        # Add customer contact if available
        if doc.contact_email:
            attendees.append({
                'email': doc.contact_email
            })

        # Add attendees to event
        for attendee in attendees:
            event.append('event_participants', attendee)

        event.insert(ignore_permissions=True)

        # Update the visit document to link the calendar event
        doc.db_set('calendar_event', event.name)

        return {
            'success': True,
            'message': f'Calendar event created successfully: {event.name}',
            'event_name': event.name,
            'event_subject': event.subject,
            'start_time': start_datetime,
            'end_time': end_datetime,
            'attendees_count': len(attendees)
        }

    except Exception as e:
        frappe.log_error(f"Failed to create calendar event for {doc.name}: {str(e)}")
        return {
            'success': False,
            'message': f"Failed to create calendar event: {str(e)}"
        }


def handle_checkin(doc, latitude=None, longitude=None, accuracy=None):
    """Handle automatic check-in with GPS location"""
    # Validate state
    if doc.status != 'Planned':
        frappe.throw(_("Can only check-in from Planned status. Current status: {0}").format(doc.status))

    if doc.check_in_time:
        frappe.throw(_("Already checked in at {0}").format(doc.check_in_time))

    # Validate location data
    if not latitude or not longitude:
        frappe.throw(_("GPS coordinates are required for automatic check-in"))

    try:
        # Get address from coordinates
        address = get_address_from_coordinates(latitude, longitude)

        # Validate location accuracy
        accuracy_warning = None
        if accuracy and accuracy > 100:
            accuracy_warning = f"Location accuracy is low ({int(accuracy)}m). Location may not be precise."

        # Update document
        doc.check_in_time = now_datetime()
        doc.check_in_latitude = latitude
        doc.check_in_longitude = longitude
        doc.check_in_location = address
        doc.location_accuracy = f"{int(accuracy)} meters" if accuracy else "Unknown"
        doc.status = 'In Progress'

        # Save with validation
        doc.save()

        response = {
            'success': True,
            'message': f'Check-in successful at {address}',
            'location': address,
            'check_in_time': doc.check_in_time,
            'workflow_state': get_workflow_metadata(doc)
        }

        if accuracy_warning:
            response['warning'] = accuracy_warning

        return response

    except Exception as e:
        frappe.log_error(f"Check-in failed for {doc.name}: {str(e)}")
        frappe.throw(_("Check-in failed: {0}").format(str(e)))


def handle_manual_checkin(doc, location_name=None, latitude=None, longitude=None, reason=None):
    """Handle manual check-in without GPS"""
    # Validate state
    if doc.status != 'Planned':
        frappe.throw(_("Can only check-in from Planned status"))

    if not location_name:
        frappe.throw(_("Location name is required for manual check-in"))

    if not reason:
        frappe.throw(_("Reason for manual entry is required"))

    try:
        # Update document
        doc.check_in_time = now_datetime()
        doc.check_in_location = location_name
        doc.check_in_latitude = latitude or 0
        doc.check_in_longitude = longitude or 0
        doc.location_accuracy = f"Manual Entry: {reason}"
        doc.status = 'In Progress'

        doc.save()

        return {
            'success': True,
            'message': f'Manual check-in successful at {location_name}',
            'location': location_name,
            'check_in_time': doc.check_in_time,
            'workflow_state': get_workflow_metadata(doc)
        }

    except Exception as e:
        frappe.log_error(f"Manual check-in failed for {doc.name}: {str(e)}")
        frappe.throw(_("Manual check-in failed: {0}").format(str(e)))


def handle_checkout(doc, latitude=None, longitude=None, visit_summary=None, lead_quality=None, next_steps=None,
                    follow_up_required=None, follow_up_date=None):
    """Handle check-out with visit completion"""
    # Validate state
    if doc.status != 'In Progress':
        frappe.throw(_("Can only check-out from In Progress status"))

    if not doc.check_in_time:
        frappe.throw(_("Cannot check-out without check-in"))

    try:
        # Get address if coordinates provided
        checkout_location = None
        if latitude and longitude:
            checkout_location = get_address_from_coordinates(latitude, longitude)

        # Calculate duration
        check_in_time = frappe.utils.get_datetime(doc.check_in_time)
        check_out_time = frappe.utils.get_datetime(now_datetime())
        duration = (check_out_time - check_in_time).total_seconds()

        # Update document
        doc.check_out_time = now_datetime()
        if checkout_location:
            doc.check_out_latitude = latitude
            doc.check_out_longitude = longitude
            doc.check_out_location = checkout_location
        doc.total_duration = int(duration)
        doc.status = 'Completed'

        # Update visit details if provided
        if visit_summary:
            doc.visit_summary = visit_summary
        if lead_quality:
            doc.lead_quality = lead_quality
        if next_steps:
            doc.next_steps = next_steps
        if follow_up_required is not None:
            doc.follow_up_required = follow_up_required
        if follow_up_date:
            doc.follow_up_date = follow_up_date

        doc.save()

        return {
            'success': True,
            'message': f'Check-out successful. Duration: {format_duration(duration)}',
            'location': checkout_location or 'Location not captured',
            'duration': format_duration(duration),
            'check_out_time': doc.check_out_time,
            'can_submit': True,
            'workflow_state': get_workflow_metadata(doc)
        }

    except Exception as e:
        frappe.log_error(f"Check-out failed for {doc.name}: {str(e)}")
        frappe.throw(_("Check-out failed: {0}").format(str(e)))


def handle_submission(doc, **kwargs):
    """Handle visit submission with workflow validation"""
    # Validate submission readiness
    if doc.docstatus != 0:
        frappe.throw(_("Visit is already submitted or cancelled"))

    if doc.status != 'Completed':
        frappe.throw(_("Visit must be completed before submission. Current status: {0}").format(doc.status))

    if not doc.check_out_time:
        frappe.throw(_("Cannot submit without check-out"))

    try:
        # Perform submission
        doc.submit()

        return {
            'success': True,
            'message': 'Site visit submitted successfully',
            'visit_id': doc.name,
            'docstatus': doc.docstatus,
            'submitted_on': now_datetime(),
            'workflow_state': get_workflow_metadata(doc)
        }

    except Exception as e:
        frappe.log_error(f"Submission failed for {doc.name}: {str(e)}")
        return {
            'success': False,
            'message': f"Submission failed: {str(e)}",
            'visit_id': doc.name
        }


def handle_quick_submission(doc, visit_summary=None, lead_quality=None, next_steps=None, follow_up_required=None,
                            follow_up_date=None):
    """Handle quick submission with summary dialog data"""
    try:
        # Update visit details
        if visit_summary:
            doc.visit_summary = visit_summary
        if lead_quality:
            doc.lead_quality = lead_quality
        if next_steps:
            doc.next_steps = next_steps
        if follow_up_required is not None:
            doc.follow_up_required = follow_up_required
        if follow_up_date:
            doc.follow_up_date = follow_up_date

        # Save changes first
        doc.save()

        # Then submit
        return handle_submission(doc)

    except Exception as e:
        frappe.log_error(f"Quick submission failed for {doc.name}: {str(e)}")
        frappe.throw(_("Quick submission failed: {0}").format(str(e)))


# Utility Functions
def get_address_from_coordinates(latitude, longitude):
    """Server-side reverse geocoding with error handling"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&zoom=18&addressdetails=1"
        headers = {'User-Agent': 'Frappe CRM Site Visit'}

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'display_name' in data:
                return data['display_name']
    except Exception as e:
        frappe.log_error(f"Geocoding error: {str(e)}")

    # Fallback to coordinates
    return f"{float(latitude):.6f}, {float(longitude):.6f}"


def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if not seconds or seconds <= 0:
        return "0 min"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def get_docstatus_name(docstatus):
    """Get human readable docstatus name"""
    status_map = {0: 'Draft', 1: 'Submitted', 2: 'Cancelled'}
    return status_map.get(docstatus, 'Unknown')


def get_workflow_stage_name(doc):
    """Get current workflow stage name"""
    if doc.docstatus == 1:
        return "Submitted"
    elif doc.docstatus == 2:
        return "Cancelled"
    elif doc.status == 'Completed':
        return "Ready to Submit"
    elif doc.status == 'In Progress':
        return "In Progress"
    elif doc.status == 'Planned':
        return "Planned"
    else:
        return doc.status


def get_workflow_progress_percentage(doc):
    """Get workflow completion percentage"""
    if doc.docstatus == 1:
        return 100
    elif doc.docstatus == 2:
        return 0
    elif doc.status == 'Completed':
        return 80
    elif doc.status == 'In Progress':
        return 50
    elif doc.status == 'Planned':
        return 20
    else:
        return 0


def get_next_step_hint(doc):
    """Get hint for next workflow step"""
    if doc.docstatus == 1:
        return "Visit workflow complete"
    elif doc.status == 'Planned':
        return "Check in when you arrive at location"
    elif doc.status == 'In Progress':
        return "Check out when visit is complete"
    elif doc.status == 'Completed':
        return "Submit to finalize the visit"
    else:
        return "Follow workflow guidance"


def get_reference_metadata(reference_type, reference_name):
    """Get metadata for reference document"""
    try:
        ref_doc = frappe.get_doc(reference_type, reference_name)
        metadata = {
            'reference_type': reference_type,
            'reference_name': reference_name,
            'auto_populate_data': {}
        }

        if reference_type == 'CRM Lead':
            metadata['auto_populate_data'] = {
                'reference_title': ref_doc.get('lead_name') or ref_doc.get('organization') or 'Unknown',
                'contact_phone': ref_doc.get('mobile_no') or ref_doc.get('phone'),
                'contact_email': ref_doc.get('email'),
                'city': ref_doc.get('city'),
                'state': ref_doc.get('state'),
                'country': ref_doc.get('country')
            }
        elif reference_type == 'CRM Deal':
            metadata['auto_populate_data'] = {
                'reference_title': ref_doc.get('organization') or ref_doc.name,
                'potential_value': ref_doc.get('deal_value')
            }
        elif reference_type == 'Customer':
            metadata['auto_populate_data'] = {
                'reference_title': ref_doc.get('customer_name') or 'Unknown'
            }

        # Remove None values
        metadata['auto_populate_data'] = {k: v for k, v in metadata['auto_populate_data'].items() if v}

        return metadata

    except Exception as e:
        frappe.log_error(f"Failed to get reference metadata: {str(e)}")
        return {}


def get_validation_rules():
    """Get client-side validation rules"""
    return {
        'required_fields': ['visit_date', 'visit_type', 'sales_person'],
        'conditional_required': {
            'visit_summary': 'status == "Completed"',
            'follow_up_date': 'follow_up_required == 1'
        },
        'date_validations': {
            'follow_up_date': 'must_be_future',
            'visit_date': 'can_be_past_or_future'
        },
        'workflow_rules': {
            'checkin_requires_planned_status': True,
            'checkout_requires_checkin': True,
            'submit_requires_completed': True
        }
    }


def get_context_field_properties(doc):
    """Get context-specific field properties"""
    properties = {}

    # Status-based field properties
    if doc.status == 'Completed':
        properties.update({
            'visit_summary': {'required': True, 'highlight': True},
            'lead_quality': {'required': True},
            'next_steps': {'highlight': True}
        })

    # Docstatus-based properties
    if doc.docstatus == 1:
        properties.update({
            'check_in_time': {'readonly': True},
            'check_out_time': {'readonly': True},
            'total_duration': {'readonly': True}
        })

    return properties
