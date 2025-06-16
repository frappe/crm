# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from frappe.utils import cstr, now_datetime, getdate, add_days


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
    """Quick check-in for mobile users"""
    try:
        doc = frappe.get_doc('CRM Site Visit', visit_id)
        
        if not doc.has_permission('write'):
            frappe.throw(_("You don't have permission to update this visit"))
        
        if doc.check_in_time:
            frappe.throw(_("Already checked in for this visit"))
        
        # Get address from coordinates
        address = get_address_from_coordinates(float(latitude), float(longitude))
        
        # Update document
        doc.check_in_time = now_datetime()
        doc.check_in_latitude = float(latitude)
        doc.check_in_longitude = float(longitude)
        doc.check_in_location = address
        doc.location_accuracy = f"{accuracy} meters" if accuracy else "Unknown"
        doc.status = 'In Progress'
        
        doc.save(ignore_permissions=True)
        
        return {
            'success': True,
            'message': 'Check-in successful',
            'visit_id': visit_id,
            'check_in_time': doc.check_in_time,
            'location': address
        }
        
    except Exception as e:
        frappe.log_error(f"Check-in failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


@frappe.whitelist()
def quick_checkout(visit_id, latitude, longitude, visit_summary=None, lead_quality=None):
    """Quick check-out for mobile users"""
    try:
        doc = frappe.get_doc('CRM Site Visit', visit_id)
        
        if not doc.has_permission('write'):
            frappe.throw(_("You don't have permission to update this visit"))
        
        if not doc.check_in_time:
            frappe.throw(_("Cannot check-out without check-in"))
        
        if doc.check_out_time:
            frappe.throw(_("Already checked out for this visit"))
        
        # Get address from coordinates
        address = get_address_from_coordinates(float(latitude), float(longitude))
        
        # Calculate duration
        check_in_time = frappe.utils.get_datetime(doc.check_in_time)
        check_out_time = frappe.utils.get_datetime(now_datetime())
        duration = (check_out_time - check_in_time).total_seconds()
        
        # Update document
        doc.check_out_time = now_datetime()
        doc.check_out_latitude = float(latitude)
        doc.check_out_longitude = float(longitude)
        doc.check_out_location = address
        doc.total_duration = int(duration)
        doc.status = 'Completed'
        
        if visit_summary:
            doc.visit_summary = visit_summary
        
        if lead_quality:
            doc.lead_quality = lead_quality
        
        doc.save(ignore_permissions=True)
        
        # Format duration
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        return {
            'success': True,
            'message': 'Check-out successful',
            'visit_id': visit_id,
            'check_out_time': doc.check_out_time,
            'duration': duration_str,
            'location': address
        }
        
    except Exception as e:
        frappe.log_error(f"Check-out failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


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
    """Get dashboard data for site visits"""
    user = frappe.session.user
    today = getdate()
    
    # Today's visits
    today_visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'visit_date': today
        },
        fields=['name', 'status', 'reference_title', 'planned_start_time']
    )
    
    # This week's visits
    week_start = add_days(today, -7)
    week_visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'visit_date': ['between', [week_start, today]]
        },
        fields=['status']
    )
    
    week_completed = len([v for v in week_visits if v.status == 'Completed'])
    week_total = len(week_visits)
    
    # Pending follow-ups
    pending_followups = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'follow_up_required': 1,
            'follow_up_date': ['<=', today],
            'status': 'Completed'
        },
        fields=['name', 'reference_title', 'follow_up_date']
    )
    
    return {
        'today_visits': today_visits,
        'week_completion_rate': (week_completed / week_total * 100) if week_total > 0 else 0,
        'pending_followups': pending_followups,
        'total_today': len(today_visits),
        'completed_today': len([v for v in today_visits if v.status == 'Completed']),
        'in_progress_today': len([v for v in today_visits if v.status == 'In Progress'])
    }
