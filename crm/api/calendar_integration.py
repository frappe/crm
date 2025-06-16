# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def update_visit_from_calendar_event(doc, method):
    """Update site visit when calendar event is modified"""
    
    if doc.reference_type == 'CRM Site Visit' and doc.reference_name:
        try:
            visit = frappe.get_doc('CRM Site Visit', doc.reference_name)
            
            # Update visit timing based on event
            if doc.starts_on and not visit.planned_start_time:
                visit.db_set('planned_start_time', doc.starts_on, update_modified=False)
            
            if doc.ends_on and not visit.planned_end_time:
                visit.db_set('planned_end_time', doc.ends_on, update_modified=False)
            
            # Update calendar event reference in visit
            if not visit.calendar_event:
                visit.db_set('calendar_event', doc.name, update_modified=False)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Failed to update visit from calendar event: {str(e)}")


def delete_visit_calendar_event_link(doc, method):
    """Remove calendar event link when event is deleted"""
    
    if doc.reference_type == 'CRM Site Visit' and doc.reference_name:
        try:
            frappe.db.set_value('CRM Site Visit', doc.reference_name, 'calendar_event', None)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Failed to remove calendar event link: {str(e)}")


@frappe.whitelist()
def bulk_create_calendar_events():
    """Create calendar events for all site visits that don't have them"""
    
    visits = frappe.get_all('CRM Site Visit',
        filters={
            'calendar_event': ['is', 'not set'],
            'status': ['not in', ['Cancelled']],
            'sync_with_calendar': 1
        },
        fields=['name']
    )
    
    success_count = 0
    error_count = 0
    
    for visit_data in visits:
        try:
            visit = frappe.get_doc('CRM Site Visit', visit_data.name)
            from crm.api.site_visit_calendar import create_calendar_event_for_visit
            create_calendar_event_for_visit(visit)
            success_count += 1
        except Exception as e:
            error_count += 1
            frappe.log_error(f"Failed to create calendar event for {visit_data.name}: {str(e)}")
    
    return {
        'success': success_count,
        'errors': error_count,
        'message': f'Created {success_count} calendar events. {error_count} errors.'
    }


@frappe.whitelist()
def get_calendar_events_for_visits(from_date=None, to_date=None, sales_person=None):
    """Get calendar events related to site visits"""
    
    filters = {
        'reference_type': 'CRM Site Visit'
    }
    
    if from_date:
        filters['starts_on'] = ['>=', from_date]
    if to_date:
        filters['ends_on'] = ['<=', to_date]
    
    events = frappe.get_all('Event',
        filters=filters,
        fields=[
            'name', 'subject', 'starts_on', 'ends_on', 'reference_name',
            'color', 'description', 'event_type'
        ]
    )
    
    # Get visit details for each event
    for event in events:
        if event.reference_name:
            visit = frappe.get_value('CRM Site Visit', event.reference_name, 
                ['status', 'sales_person', 'reference_title', 'visit_type'], 
                as_dict=True
            )
            if visit:
                event.update(visit)
                
                # Filter by sales person if specified
                if sales_person and visit.sales_person != sales_person:
                    events.remove(event)
    
    return events


@frappe.whitelist()
def sync_visit_timing_with_event(visit_name, event_name):
    """Sync visit timing with its calendar event"""
    
    try:
        visit = frappe.get_doc('CRM Site Visit', visit_name)
        event = frappe.get_doc('Event', event_name)
        
        # Update visit with event timing
        if event.starts_on:
            visit.planned_start_time = event.starts_on
        if event.ends_on:
            visit.planned_end_time = event.ends_on
        
        visit.save(ignore_permissions=True)
        
        return {'success': True, 'message': 'Visit timing synced with calendar event'}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}


def auto_update_visit_status_from_calendar():
    """Auto-update visit status based on calendar events (scheduled function)"""
    
    from frappe.utils import now_datetime, getdate
    
    current_time = now_datetime()
    today = getdate()
    
    # Find visits that should be marked as "In Progress"
    planned_visits = frappe.get_all('CRM Site Visit',
        filters={
            'status': 'Planned',
            'visit_date': today,
            'planned_start_time': ['<=', current_time],
            'check_in_time': ['is', 'not set']
        },
        fields=['name']
    )
    
    for visit in planned_visits:
        try:
            frappe.db.set_value('CRM Site Visit', visit.name, 'status', 'In Progress')
        except Exception as e:
            frappe.log_error(f"Failed to auto-update visit status for {visit.name}: {str(e)}")
    
    frappe.db.commit()


@frappe.whitelist()
def create_recurring_visit_series(visit_name, frequency, end_date, count=None):
    """Create a series of recurring visits based on an existing visit"""
    
    try:
        base_visit = frappe.get_doc('CRM Site Visit', visit_name)
        
        from frappe.utils import add_days, add_weeks, add_months, getdate
        from datetime import datetime
        
        created_visits = []
        current_date = getdate(base_visit.visit_date)
        
        frequency_map = {
            'Weekly': lambda d: add_weeks(d, 1),
            'Bi-weekly': lambda d: add_weeks(d, 2),
            'Monthly': lambda d: add_months(d, 1),
            'Quarterly': lambda d: add_months(d, 3)
        }
        
        if frequency not in frequency_map:
            return {'success': False, 'message': 'Invalid frequency'}
        
        increment_func = frequency_map[frequency]
        iterations = 0
        max_iterations = count or 52  # Default max 52 iterations
        
        while current_date <= getdate(end_date) and iterations < max_iterations:
            current_date = increment_func(current_date)
            iterations += 1
            
            if current_date > getdate(end_date):
                break
            
            # Create new visit
            new_visit = frappe.copy_doc(base_visit)
            new_visit.visit_date = current_date
            new_visit.status = 'Planned'
            new_visit.check_in_time = None
            new_visit.check_out_time = None
            new_visit.total_duration = None
            new_visit.visit_summary = None
            new_visit.calendar_event = None
            
            # Update planned times if they exist
            if base_visit.planned_start_time:
                time_part = base_visit.planned_start_time.time()
                new_visit.planned_start_time = datetime.combine(current_date, time_part)
            
            if base_visit.planned_end_time:
                time_part = base_visit.planned_end_time.time()
                new_visit.planned_end_time = datetime.combine(current_date, time_part)
            
            new_visit.insert(ignore_permissions=True)
            created_visits.append(new_visit.name)
        
        return {
            'success': True,
            'message': f'Created {len(created_visits)} recurring visits',
            'visits': created_visits
        }
        
    except Exception as e:
        return {'success': False, 'message': str(e)}
