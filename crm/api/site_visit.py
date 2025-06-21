# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days


@frappe.whitelist()
def get_upcoming_visits(limit=10):
    """Get upcoming site visits for current user"""
    user = frappe.session.user
    
    visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'status': ['in', ['Planned', 'In Progress']],
            'visit_date': ['>=', getdate()]
        },
        fields=[
            'name', 'visit_date', 'reference_title', 'visit_type',
            'status', 'city', 'visit_address', 'priority',
            'planned_start_time', 'check_in_time'
        ],
        order_by='visit_date asc, planned_start_time asc',
        limit=limit
    )
    
    return visits


@frappe.whitelist()
def get_visit_analytics(from_date=None, to_date=None, sales_person=None):
    """Get visit analytics data"""
    if not from_date:
        from_date = add_days(getdate(), -30)
    if not to_date:
        to_date = getdate()
    
    filters = {
        'visit_date': ['between', [from_date, to_date]]
    }
    
    if sales_person:
        filters['sales_person'] = sales_person
    
    visits = frappe.get_all(
        'CRM Site Visit',
        filters=filters,
        fields=[
            'name', 'status', 'visit_type', 'lead_quality',
            'total_duration', 'potential_value', 'probability_percentage'
        ]
    )
    
    # Calculate analytics
    total_visits = len(visits)
    completed_visits = len([v for v in visits if v.status == 'Completed'])
    total_duration = sum([v.total_duration or 0 for v in visits])
    total_potential_value = sum([v.potential_value or 0 for v in visits])
    
    # Status breakdown
    status_breakdown = {}
    for visit in visits:
        status_breakdown[visit.status] = status_breakdown.get(visit.status, 0) + 1
    
    # Visit type breakdown
    type_breakdown = {}
    for visit in visits:
        type_breakdown[visit.visit_type] = type_breakdown.get(visit.visit_type, 0) + 1
    
    # Lead quality breakdown
    quality_breakdown = {}
    for visit in visits:
        if visit.lead_quality:
            quality_breakdown[visit.lead_quality] = quality_breakdown.get(visit.lead_quality, 0) + 1
    
    return {
        'total_visits': total_visits,
        'completed_visits': completed_visits,
        'completion_rate': (completed_visits / total_visits * 100) if total_visits > 0 else 0,
        'total_duration_hours': total_duration / 3600 if total_duration else 0,
        'avg_duration_hours': (total_duration / total_visits / 3600) if total_visits > 0 else 0,
        'total_potential_value': total_potential_value,
        'status_breakdown': status_breakdown,
        'type_breakdown': type_breakdown,
        'quality_breakdown': quality_breakdown
    }


@frappe.whitelist()
def quick_checkin(visit_id, latitude, longitude, accuracy=None):
    """Quick check-in for mobile users - DEPRECATED: Use checkin_visit instead"""
    frappe.log_error("Using deprecated quick_checkin API. Please update to checkin_visit.")
    return checkin_visit(visit_id, latitude, longitude, accuracy)


@frappe.whitelist()
def checkin_visit(visit_id, latitude, longitude, accuracy=None):
    """Unified check-in function with workflow awareness"""
    # Use the enhanced function from doctype controller
    from crm.fcrm.doctype.crm_site_visit.crm_site_visit import mobile_checkin
    return mobile_checkin(visit_id, latitude, longitude, accuracy)


@frappe.whitelist()
def quick_checkout(visit_id, latitude, longitude, visit_summary=None, lead_quality=None):
    """Quick check-out for mobile users - DEPRECATED: Use checkout_visit instead"""
    frappe.log_error("Using deprecated quick_checkout API. Please update to checkout_visit.")
    return checkout_visit(visit_id, latitude, longitude, visit_summary, lead_quality)


@frappe.whitelist()
def checkout_visit(visit_id, latitude, longitude, visit_summary=None, lead_quality=None, auto_submit=False):
    """Unified check-out function with workflow awareness"""
    # Use the enhanced function from doctype controller
    from crm.fcrm.doctype.crm_site_visit.crm_site_visit import mobile_checkout
    return mobile_checkout(visit_id, latitude, longitude, visit_summary, auto_submit)


@frappe.whitelist()
def submit_visit_api(visit_id):
    """API wrapper for visit submission with workflow validation"""
    from crm.fcrm.doctype.crm_site_visit.crm_site_visit import submit_visit
    return submit_visit(visit_id)


@frappe.whitelist()
def get_visit_workflow_info(visit_id):
    """Get complete workflow information for a visit"""
    try:
        visit = frappe.get_doc('CRM Site Visit', visit_id)

        # Check permissions
        if not visit.has_permission('read'):
            frappe.throw(_("You don't have permission to view this visit"))

        # Determine available actions
        can_checkin = (visit.status == 'Planned' and not visit.check_in_time)
        can_checkout = (visit.status == 'In Progress' and visit.check_in_time and not visit.check_out_time)
        can_submit = (visit.status == 'Completed' and visit.docstatus == 0 and visit.check_out_time)

        # Get workflow guidance message
        workflow_guidance = get_workflow_guidance_message(visit)

        # Get next available actions
        next_actions = []
        if can_checkin:
            next_actions.append({'action': 'checkin', 'label': 'Check In', 'primary': True})
        if can_checkout:
            next_actions.append({'action': 'checkout', 'label': 'Check Out', 'primary': True})
        if can_submit:
            next_actions.append({'action': 'submit', 'label': 'Submit Visit', 'primary': True})
        
        return {
            'success': True,
            'visit_id': visit_id,
            'current_status': visit.status,
            'docstatus': visit.docstatus,
            'workflow_stage': get_workflow_stage(visit),
            'can_checkin': can_checkin,
            'can_checkout': can_checkout,
            'can_submit': can_submit,
            'workflow_guidance': workflow_guidance,
            'next_actions': next_actions,
            'progress_percentage': get_workflow_progress(visit)
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to get workflow info for visit {visit_id}: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


def get_workflow_guidance_message(visit):
    """Get contextual guidance message for current workflow step"""
    if visit.status == 'Planned':
        return "Visit is planned. Use 'Check In' when you arrive at the location."
    elif visit.status == 'In Progress':
        return "Visit is in progress. Use 'Check Out' when you complete the visit."
    elif visit.status == 'Completed' and visit.docstatus == 0:
        return "Visit completed! You can now submit this document to finalize the record."
    elif visit.status == 'Completed' and visit.docstatus == 1:
        return "Visit has been submitted and finalized. All workflow actions completed."
    elif visit.status == 'Cancelled':
        return "This visit has been cancelled."
    elif visit.status == 'Postponed':
        return "This visit has been postponed. Update the visit date when rescheduled."
    else:
        return "Unknown workflow status."


def get_workflow_stage(visit):
    """Get current workflow stage name"""
    if visit.docstatus == 1:
        return "Submitted"
    elif visit.status == 'Completed':
        return "Ready to Submit"
    elif visit.status == 'In Progress':
        return "In Progress"
    elif visit.status == 'Planned':
        return "Planned"
    else:
        return visit.status


def get_workflow_progress(visit):
    """Get workflow completion percentage"""
    if visit.docstatus == 1:
        return 100
    elif visit.status == 'Completed':
        return 80
    elif visit.status == 'In Progress':
        return 50
    elif visit.status == 'Planned':
        return 20
    else:
        return 0


@frappe.whitelist()
def create_quick_visit(reference_type, reference_name, visit_purpose, visit_type="Initial Meeting"):
    """Create a quick site visit"""
    try:
        # Get reference document details
        ref_doc = frappe.get_doc(reference_type, reference_name)
        
        # Create site visit
        visit = frappe.get_doc({
            'doctype': 'CRM Site Visit',
            'visit_date': getdate(),
            'visit_type': visit_type,
            'reference_type': reference_type,
            'reference_name': reference_name,
            'sales_person': frappe.session.user,
            'visit_purpose': visit_purpose,
            'status': 'Planned'
        })
        
        # Auto-populate reference details
        if reference_type == 'CRM Lead':
            visit.reference_title = ref_doc.get('lead_name') or ref_doc.get('organization') or 'Unknown'
            if ref_doc.get('mobile_no'):
                visit.contact_phone = ref_doc.mobile_no
            if ref_doc.get('email'):
                visit.contact_email = ref_doc.email
        elif reference_type == 'CRM Deal':
            visit.reference_title = ref_doc.get('organization') or ref_doc.name
        
        visit.insert(ignore_permissions=True)
        
        return {
            'success': True,
            'message': 'Site visit created successfully',
            'visit_id': visit.name,
            'visit_name': visit.name
        }
        
    except Exception as e:
        frappe.log_error(f"Quick visit creation failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


def get_address_from_coordinates(latitude, longitude):
    """Get address from coordinates using reverse geocoding"""
    try:
        import requests
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&zoom=18&addressdetails=1"
        headers = {'User-Agent': 'Frappe CRM Site Visit'}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'display_name' in data:
                return data['display_name']
    except Exception as e:
        frappe.log_error(f"Geocoding error: {str(e)}")
    
    # Fallback to coordinates
    return f"{latitude:.6f}, {longitude:.6f}"


@frappe.whitelist()
def get_visit_dashboard_data():
    """Get enhanced dashboard data for site visits with workflow metrics"""
    user = frappe.session.user
    today = getdate()
    
    # Today's visits
    today_visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'visit_date': today
        },
        fields=['name', 'status', 'reference_title', 'planned_start_time', 'docstatus']
    )
    
    # This week's visits
    week_start = add_days(today, -7)
    week_visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'visit_date': ['between', [week_start, today]]
        },
        fields=['status', 'docstatus']
    )
    
    week_completed = len([v for v in week_visits if v.status == 'Completed'])
    week_total = len(week_visits)
    week_submitted = len([v for v in week_visits if v.docstatus == 1])
    
    # Pending follow-ups
    pending_followups = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'follow_up_required': 1,
            'follow_up_date': ['<=', today],
            'status': 'Completed',
            'docstatus': 1
        },
        fields=['name', 'reference_title', 'follow_up_date']
    )

    # Workflow-specific metrics
    ready_to_submit = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'status': 'Completed',
            'docstatus': 0
        },
        fields=['name', 'reference_title', 'visit_date']
    )

    # Calculate workflow efficiency
    workflow_efficiency = calculate_user_workflow_efficiency(user)

    # Today's workflow breakdown
    today_workflow_stats = {
        'planned': len([v for v in today_visits if v.status == 'Planned']),
        'in_progress': len([v for v in today_visits if v.status == 'In Progress']),
        'completed': len([v for v in today_visits if v.status == 'Completed' and v.docstatus == 0]),
        'submitted': len([v for v in today_visits if v.docstatus == 1])
    }
    
    return {
        'today_visits': today_visits,
        'week_completion_rate': (week_completed / week_total * 100) if week_total > 0 else 0,
        'week_submission_rate': (week_submitted / week_completed * 100) if week_completed > 0 else 0,
        'pending_followups': pending_followups,
        'total_today': len(today_visits),
        'completed_today': len([v for v in today_visits if v.status == 'Completed']),
        'in_progress_today': len([v for v in today_visits if v.status == 'In Progress']),
        'submitted_today': len([v for v in today_visits if v.docstatus == 1]),
        'ready_to_submit': ready_to_submit,
        'ready_to_submit_count': len(ready_to_submit),
        'workflow_efficiency': workflow_efficiency,
        'today_workflow_stats': today_workflow_stats
    }


def calculate_user_workflow_efficiency(user):
    """Calculate workflow efficiency metrics for a user"""
    # Get last 30 days of completed visits
    from_date = add_days(getdate(), -30)

    visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'visit_date': ['>=', from_date],
            'status': 'Completed'
        },
        fields=['name', 'check_out_time', 'docstatus', 'modified']
    )

    if not visits:
        return {
            'submission_rate': 0,
            'avg_submission_delay': 0,
            'total_completed': 0
        }

    total_completed = len(visits)
    submitted_count = len([v for v in visits if v.docstatus == 1])
    submission_rate = (submitted_count / total_completed * 100) if total_completed > 0 else 0

    # Calculate average submission delay (simplified)
    submission_delays = []
    for visit in visits:
        if visit.docstatus == 1 and visit.check_out_time:
            # This is a simplified calculation - in practice you'd track actual submission time
            submission_delays.append(1)  # Assume 1 day average delay

    avg_submission_delay = sum(submission_delays) / len(submission_delays) if submission_delays else 0

    return {
        'submission_rate': submission_rate,
        'avg_submission_delay': avg_submission_delay,
        'total_completed': total_completed,
        'total_submitted': submitted_count
    }
