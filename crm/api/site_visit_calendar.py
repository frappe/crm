# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_datetime, add_to_date, getdate


def create_calendar_event_for_visit(doc, method=None):
    """Create or update calendar event when site visit is saved"""
    
    if doc.status in ['Cancelled']:
        # Delete event if visit is cancelled
        delete_calendar_event_for_visit(doc.name)
        return
    
    # Check if event already exists
    existing_event = frappe.db.get_value('Event', 
        {'reference_type': 'CRM Site Visit', 'reference_name': doc.name}, 
        'name'
    )
    
    if existing_event:
        # Update existing event
        update_calendar_event(existing_event, doc)
    else:
        # Create new event
        create_new_calendar_event(doc)


def create_new_calendar_event(visit_doc):
    """Create a new calendar event for the site visit"""
    
    # Calculate event timing
    start_time = visit_doc.planned_start_time or get_default_start_time(visit_doc.visit_date)
    end_time = visit_doc.planned_end_time or add_to_date(start_time, hours=1)
    
    # Create event description
    description = f"""
    <h4>Site Visit Details</h4>
    <p><strong>Customer:</strong> {visit_doc.reference_title or 'N/A'}</p>
    <p><strong>Type:</strong> {visit_doc.visit_type}</p>
    <p><strong>Purpose:</strong> {visit_doc.visit_purpose or 'N/A'}</p>
    <p><strong>Priority:</strong> {visit_doc.priority}</p>
    
    {f'<p><strong>Address:</strong> {visit_doc.visit_address}</p>' if visit_doc.visit_address else ''}
    {f'<p><strong>City:</strong> {visit_doc.city}, {visit_doc.state}</p>' if visit_doc.city else ''}
    {f'<p><strong>Contact:</strong> {visit_doc.contact_phone}</p>' if visit_doc.contact_phone else ''}
    {f'<p><strong>Email:</strong> {visit_doc.contact_email}</p>' if visit_doc.contact_email else ''}
    
    {f'<p><strong>Agenda:</strong> {visit_doc.visit_agenda}</p>' if visit_doc.visit_agenda else ''}
    
    <p><strong>Site Visit ID:</strong> {visit_doc.name}</p>
    <p><a href="/app/crm-site-visit/{visit_doc.name}" target="_blank">View Site Visit</a></p>
    """
    
    # Determine event color based on visit type and status
    color = get_event_color(visit_doc.visit_type, visit_doc.status)
    
    try:
        event = frappe.get_doc({
            'doctype': 'Event',
            'subject': f'📍 Site Visit: {visit_doc.reference_title or visit_doc.name}',
            'description': description,
            'starts_on': start_time,
            'ends_on': end_time,
            'all_day': 0,
            'event_type': 'Private',
            'color': color,
            'reference_type': 'CRM Site Visit',
            'reference_name': visit_doc.name,
            'event_participants': [
                {
                    'reference_doctype': 'User',
                    'reference_docname': visit_doc.sales_person
                }
            ]
        })
        
        # Add sales manager if specified
        if visit_doc.sales_manager and visit_doc.sales_manager != visit_doc.sales_person:
            event.append('event_participants', {
                'reference_doctype': 'User',
                'reference_docname': visit_doc.sales_manager
            })
        
        event.insert(ignore_permissions=True)
        
        # Update site visit with event reference
        frappe.db.set_value('CRM Site Visit', visit_doc.name, 'calendar_event', event.name)
        frappe.db.commit()
        
        frappe.msgprint(f'Calendar event created: {event.name}', alert=True, indicator='green')
        
    except Exception as e:
        frappe.log_error(f"Failed to create calendar event for visit {visit_doc.name}: {str(e)}")


def update_calendar_event(event_name, visit_doc):
    """Update existing calendar event with latest visit details"""
    
    try:
        event = frappe.get_doc('Event', event_name)
        
        # Update event details
        event.subject = f'📍 Site Visit: {visit_doc.reference_title or visit_doc.name}'
        
        # Update timing if specified
        if visit_doc.planned_start_time:
            event.starts_on = visit_doc.planned_start_time
        if visit_doc.planned_end_time:
            event.ends_on = visit_doc.planned_end_time
        elif visit_doc.planned_start_time:
            event.ends_on = add_to_date(visit_doc.planned_start_time, hours=1)
        
        # Update description
        event.description = f"""
        <h4>Site Visit Details</h4>
        <p><strong>Customer:</strong> {visit_doc.reference_title or 'N/A'}</p>
        <p><strong>Type:</strong> {visit_doc.visit_type}</p>
        <p><strong>Purpose:</strong> {visit_doc.visit_purpose or 'N/A'}</p>
        <p><strong>Status:</strong> {visit_doc.status}</p>
        <p><strong>Priority:</strong> {visit_doc.priority}</p>
        
        {f'<p><strong>Address:</strong> {visit_doc.visit_address}</p>' if visit_doc.visit_address else ''}
        {f'<p><strong>City:</strong> {visit_doc.city}, {visit_doc.state}</p>' if visit_doc.city else ''}
        {f'<p><strong>Contact:</strong> {visit_doc.contact_phone}</p>' if visit_doc.contact_phone else ''}
        {f'<p><strong>Email:</strong> {visit_doc.contact_email}</p>' if visit_doc.contact_email else ''}
        
        {f'<p><strong>Agenda:</strong> {visit_doc.visit_agenda}</p>' if visit_doc.visit_agenda else ''}
        
        {f'<p><strong>Check-in:</strong> {visit_doc.check_in_time}</p>' if visit_doc.check_in_time else ''}
        {f'<p><strong>Check-out:</strong> {visit_doc.check_out_time}</p>' if visit_doc.check_out_time else ''}
        {f'<p><strong>Visit Summary:</strong> {visit_doc.visit_summary}</p>' if visit_doc.visit_summary else ''}
        
        <p><strong>Site Visit ID:</strong> {visit_doc.name}</p>
        <p><a href="/app/crm-site-visit/{visit_doc.name}" target="_blank">View Site Visit</a></p>
        """
        
        # Update color based on status
        event.color = get_event_color(visit_doc.visit_type, visit_doc.status)
        
        event.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Failed to update calendar event {event_name}: {str(e)}")


def delete_calendar_event_for_visit(visit_name):
    """Delete calendar event when visit is cancelled or deleted"""
    
    try:
        event_name = frappe.db.get_value('Event', 
            {'reference_type': 'CRM Site Visit', 'reference_name': visit_name}, 
            'name'
        )
        
        if event_name:
            frappe.delete_doc('Event', event_name, ignore_permissions=True)
            frappe.db.commit()
            
    except Exception as e:
        frappe.log_error(f"Failed to delete calendar event for visit {visit_name}: {str(e)}")


def get_default_start_time(visit_date):
    """Get default start time for visit (9 AM on visit date)"""
    return get_datetime(f"{visit_date} 09:00:00")


def get_event_color(visit_type, status):
    """Get appropriate color for calendar event based on visit type and status"""
    
    # Status-based colors (priority)
    if status == 'Completed':
        return '#28a745'  # Green
    elif status == 'In Progress':
        return '#007bff'  # Blue
    elif status == 'Cancelled':
        return '#dc3545'  # Red
    elif status == 'Postponed':
        return '#fd7e14'  # Orange
    
    # Visit type-based colors (fallback)
    type_colors = {
        'Initial Meeting': '#6f42c1',     # Purple
        'Demo/Presentation': '#20c997',   # Teal
        'Negotiation': '#fd7e14',         # Orange
        'Contract Signing': '#ffc107',    # Yellow
        'Follow-up': '#6c757d',           # Gray
        'Support': '#17a2b8',             # Cyan
        'Other': '#6c757d'                # Gray
    }
    
    return type_colors.get(visit_type, '#6c757d')


@frappe.whitelist()
def create_event_for_existing_visits():
    """Bulk create calendar events for existing site visits that don't have events"""
    
    # Get all active site visits without calendar events
    visits = frappe.get_all('CRM Site Visit', 
        filters={
            'status': ['not in', ['Cancelled']],
            'calendar_event': ['is', 'not set']
        },
        fields=['name']
    )
    
    created_count = 0
    failed_count = 0
    
    for visit in visits:
        try:
            visit_doc = frappe.get_doc('CRM Site Visit', visit.name)
            create_new_calendar_event(visit_doc)
            created_count += 1
        except Exception as e:
            failed_count += 1
            frappe.log_error(f"Failed to create event for visit {visit.name}: {str(e)}")
    
    return {
        'created': created_count,
        'failed': failed_count,
        'message': f'Created {created_count} calendar events. {failed_count} failed.'
    }


@frappe.whitelist()
def sync_visit_with_calendar_event(visit_name):
    """Manually sync a specific visit with its calendar event"""
    
    try:
        visit_doc = frappe.get_doc('CRM Site Visit', visit_name)
        
        existing_event = frappe.db.get_value('Event', 
            {'reference_type': 'CRM Site Visit', 'reference_name': visit_name}, 
            'name'
        )
        
        if existing_event:
            update_calendar_event(existing_event, visit_doc)
            return {'success': True, 'message': 'Calendar event updated successfully'}
        else:
            create_new_calendar_event(visit_doc)
            return {'success': True, 'message': 'Calendar event created successfully'}
            
    except Exception as e:
        frappe.log_error(f"Manual sync failed for visit {visit_name}: {str(e)}")
        return {'success': False, 'message': str(e)}


def on_visit_checkin_checkout(visit_doc):
    """Update calendar event when check-in/check-out happens"""
    
    event_name = frappe.db.get_value('Event', 
        {'reference_type': 'CRM Site Visit', 'reference_name': visit_doc.name}, 
        'name'
    )
    
    if event_name:
        # Update the event with actual timing if check-in/out happened
        try:
            event = frappe.get_doc('Event', event_name)
            
            # Update actual start time if checked in
            if visit_doc.check_in_time and not event.get('actual_start_time'):
                event.db_set('actual_start_time', visit_doc.check_in_time)
            
            # Update actual end time if checked out
            if visit_doc.check_out_time and not event.get('actual_end_time'):
                event.db_set('actual_end_time', visit_doc.check_out_time)
                
                # Update event end time to actual checkout time
                event.db_set('ends_on', visit_doc.check_out_time)
            
            # Update color based on new status
            new_color = get_event_color(visit_doc.visit_type, visit_doc.status)
            if event.color != new_color:
                event.db_set('color', new_color)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Failed to update event timing for visit {visit_doc.name}: {str(e)}")


# Integration with Google Calendar (Optional)
@frappe.whitelist()
def sync_with_google_calendar(visit_name):
    """Sync site visit with Google Calendar (requires Google Calendar integration)"""
    
    # This is a placeholder for Google Calendar integration
    # You would need to set up Google Calendar API credentials
    
    try:
        visit_doc = frappe.get_doc('CRM Site Visit', visit_name)
        
        # Check if Google Calendar is configured
        if not frappe.db.get_single_value('Google Settings', 'enable'):
            return {'success': False, 'message': 'Google Calendar integration not configured'}
        
        # Here you would implement the actual Google Calendar API calls
        # For now, we'll just create a local event
        
        create_calendar_event_for_visit(visit_doc)
        
        return {'success': True, 'message': 'Event synced with calendar'}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}
