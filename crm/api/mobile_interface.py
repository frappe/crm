"""
CRM Site Visit Mobile Interface API - Server-side mobile optimizations
Handles mobile-specific functionality, optimized data delivery, and mobile workflow management
"""

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, add_days


@frappe.whitelist()
def get_mobile_dashboard_data(date=None):
    """Get optimized dashboard data for mobile interface"""
    try:
        user = frappe.session.user
        target_date = getdate(date) if date else getdate()

        # Today's visits with essential mobile data
        today_visits = get_mobile_visits_for_date(user, target_date)

        # Quick stats for mobile
        stats = calculate_mobile_stats(user, target_date)

        # Upcoming visits (next 7 days)
        upcoming_visits = get_upcoming_mobile_visits(user, target_date)

        # Recent activity summary
        recent_activity = get_recent_activity_summary(user)

        # Quick actions available
        quick_actions = get_mobile_quick_actions(user)

        return {
            'success': True,
            'data': {
                'date': target_date,
                'visits': today_visits,
                'stats': stats,
                'upcoming_visits': upcoming_visits,
                'recent_activity': recent_activity,
                'quick_actions': quick_actions,
                'user_info': {
                    'name': user,
                    'full_name': frappe.get_value('User', user, 'full_name') or user
                }
            }
        }

    except Exception as e:
        frappe.log_error(f"Mobile dashboard data failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


def get_mobile_visits_for_date(user, date):
    """Get visits for specific date optimized for mobile"""
    visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'visit_date': date
        },
        fields=[
            'name', 'reference_title', 'visit_type', 'status', 'priority',
            'planned_start_time', 'city', 'visit_address', 'contact_phone',
            'check_in_time', 'check_out_time', 'docstatus', 'visit_purpose'
        ],
        order_by='planned_start_time asc, priority desc'
    )

    # Enhance each visit with mobile-specific data
    for visit in visits:
        # Workflow capabilities
        visit['can_checkin'] = (visit['status'] == 'Planned' and not visit['check_in_time'])
        visit['can_checkout'] = (
                    visit['status'] == 'In Progress' and visit['check_in_time'] and not visit['check_out_time'])
        visit['can_submit'] = (visit['status'] == 'Completed' and visit['docstatus'] == 0)

        # Time status
        visit['is_overdue'] = is_visit_overdue(visit)
        visit['time_status'] = get_visit_time_status(visit)

        # Mobile-friendly formatting
        visit['planned_time_formatted'] = format_mobile_time(visit['planned_start_time'])
        visit['status_color'] = get_status_color(visit['status'])
        visit['priority_icon'] = get_priority_icon(visit['priority'])

        # Shortened address for mobile
        visit['short_address'] = get_short_address(visit['city'], visit['visit_address'])

        # Next action hint
        visit['next_action'] = get_next_action_hint(visit)

    return visits


def get_mobile_stats(user, date):
    """Calculate key stats for mobile dashboard"""
    # Today's stats
    today_visits = frappe.get_all('CRM Site Visit',
                                  filters={'sales_person': user, 'visit_date': date},
                                  fields=['status', 'docstatus']
                                  )

    # This week's stats
    week_start = add_days(date, -date.weekday())
    week_visits = frappe.get_all('CRM Site Visit',
                                 filters={
                                     'sales_person': user,
                                     'visit_date': ['between', [week_start, date]]
                                 },
                                 fields=['status', 'docstatus', 'lead_quality']
                                 )

    # Calculate stats
    total_today = len(today_visits)
    completed_today = len([v for v in today_visits if v['status'] == 'Completed'])
    in_progress_today = len([v for v in today_visits if v['status'] == 'In Progress'])
    pending_today = len([v for v in today_visits if v['status'] == 'Planned'])
    submitted_today = len([v for v in today_visits if v['docstatus'] == 1])

    # Week stats
    week_total = len(week_visits)
    week_completed = len([v for v in week_visits if v['status'] == 'Completed'])
    week_hot_leads = len([v for v in week_visits if v.get('lead_quality') == 'Hot'])

    # Completion rates
    today_completion_rate = (completed_today / total_today * 100) if total_today > 0 else 0
    week_completion_rate = (week_completed / week_total * 100) if week_total > 0 else 0

    return {
        'today': {
            'total': total_today,
            'completed': completed_today,
            'in_progress': in_progress_today,
            'pending': pending_today,
            'submitted': submitted_today,
            'completion_rate': round(today_completion_rate, 1)
        },
        'week': {
            'total': week_total,
            'completed': week_completed,
            'completion_rate': round(week_completion_rate, 1),
            'hot_leads': week_hot_leads
        }
    }


def calculate_mobile_stats(user, date):
    """Calculate comprehensive stats optimized for mobile display"""
    stats = get_mobile_stats(user, date)

    # Add performance indicators
    stats['performance'] = {
        'efficiency_score': calculate_efficiency_score(user),
        'streak_days': calculate_completion_streak(user),
        'this_month_visits': get_month_visit_count(user, date)
    }

    return stats


def get_upcoming_mobile_visits(user, from_date, limit=5):
    """Get upcoming visits for mobile preview"""
    upcoming = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'visit_date': ['>', from_date],
            'status': ['in', ['Planned', 'In Progress']]
        },
        fields=[
            'name', 'visit_date', 'reference_title', 'visit_type',
            'city', 'planned_start_time', 'priority'
        ],
        order_by='visit_date asc, planned_start_time asc',
        limit=limit
    )

    # Format for mobile
    for visit in upcoming:
        visit['date_formatted'] = format_mobile_date(visit['visit_date'])
        visit['time_formatted'] = format_mobile_time(visit['planned_start_time'])
        visit['days_from_today'] = (getdate(visit['visit_date']) - from_date).days

    return upcoming


@frappe.whitelist()
def get_mobile_visit_form(visit_id):
    """Get optimized visit form data for mobile interface"""
    try:
        visit = frappe.get_doc('CRM Site Visit', visit_id)

        # Check permissions
        if not visit.has_permission('read'):
            frappe.throw(_("You don't have permission to view this visit"))

        # Essential data for mobile form
        mobile_data = {
            'name': visit.name,
            'reference_title': visit.reference_title,
            'visit_type': visit.visit_type,
            'visit_purpose': visit.visit_purpose,
            'status': visit.status,
            'docstatus': visit.docstatus,
            'visit_date': visit.visit_date,
            'planned_start_time': visit.planned_start_time,
            'city': visit.city,
            'visit_address': visit.visit_address,
            'contact_phone': visit.contact_phone,
            'contact_email': visit.contact_email,
            'check_in_time': visit.check_in_time,
            'check_out_time': visit.check_out_time,
            'total_duration': visit.total_duration,
            'visit_summary': visit.visit_summary,
            'lead_quality': visit.lead_quality,
            'next_steps': visit.next_steps,
            'follow_up_required': visit.follow_up_required,
            'follow_up_date': visit.follow_up_date,
            'priority': visit.priority
        }

        # Workflow state for mobile
        workflow = get_mobile_workflow_state(visit)

        # Mobile form configuration
        form_config = get_mobile_form_config(visit)

        # Quick actions
        quick_actions = get_visit_quick_actions(visit)

        return {
            'success': True,
            'visit_data': mobile_data,
            'workflow': workflow,
            'form_config': form_config,
            'quick_actions': quick_actions
        }

    except Exception as e:
        frappe.log_error(f"Mobile visit form failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


def get_mobile_workflow_state(visit):
    """Get workflow state optimized for mobile"""
    return {
        'current_status': visit.status,
        'current_step': get_mobile_workflow_step(visit),
        'progress_percentage': get_workflow_progress_percentage(visit),
        'can_checkin': visit.status == 'Planned' and not visit.check_in_time,
        'can_checkout': visit.status == 'In Progress' and visit.check_in_time and not visit.check_out_time,
        'can_submit': visit.status == 'Completed' and visit.docstatus == 0,
        'next_action': get_next_action_hint(visit),
        'status_color': get_status_color(visit.status),
        'step_description': get_step_description(visit)
    }


def get_mobile_workflow_step(visit):
    """Get current workflow step for mobile display"""
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


def get_mobile_form_config(visit):
    """Get mobile form configuration"""
    config = {
        'required_fields': ['visit_type', 'visit_purpose'],
        'hidden_fields': [
            'planned_start_time', 'planned_end_time', 'location_accuracy',
            'check_in_latitude', 'check_in_longitude',
            'check_out_latitude', 'check_out_longitude'
        ],
        'readonly_fields': [],
        'highlight_fields': [],
        'compact_sections': [
            'location_details', 'timing_details', 'checkin_details'
        ]
    }

    # Status-specific configurations
    if visit.status == 'In Progress':
        config['readonly_fields'].extend(['check_in_time', 'check_in_location'])
        config['highlight_fields'].append('visit_purpose')

    elif visit.status == 'Completed':
        config['required_fields'].extend(['visit_summary', 'lead_quality'])
        config['highlight_fields'].extend(['visit_summary', 'next_steps'])
        config['readonly_fields'].extend(['check_in_time', 'check_out_time'])

    # Submitted documents
    if visit.docstatus == 1:
        config['readonly_fields'].extend([
            'visit_date', 'visit_type', 'reference_type', 'reference_name',
            'visit_summary', 'lead_quality'
        ])

    return config


@frappe.whitelist()
def create_quick_visit_mobile(customer_name, visit_type="Initial Meeting", purpose="", phone=""):
    """Create quick visit from mobile interface"""
    try:
        # Create minimal visit record
        visit = frappe.get_doc({
            'doctype': 'CRM Site Visit',
            'visit_date': getdate(),
            'visit_type': visit_type,
            'visit_purpose': purpose or f"Quick visit for {customer_name}",
            'reference_title': customer_name,
            'contact_phone': phone,
            'sales_person': frappe.session.user,
            'status': 'Planned',
            'priority': 'Medium'
        })

        visit.insert()

        return {
            'success': True,
            'visit_id': visit.name,
            'message': f'Quick visit created for {customer_name}',
            'workflow_state': get_mobile_workflow_state(visit)
        }

    except Exception as e:
        frappe.log_error(f"Quick visit creation failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


@frappe.whitelist()
def mobile_quick_checkin(visit_id, latitude=None, longitude=None, accuracy=None):
    """Quick check-in optimized for mobile"""
    try:
        # Use the workflow API
        from crm.api.site_visit_workflow import perform_workflow_action

        result = perform_workflow_action(
            docname=visit_id,
            action='checkin',
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy
        )

        # Add mobile-specific enhancements
        if result.get('success'):
            result['mobile_notification'] = {
                'title': 'Check-in Successful',
                'message': f"Checked in at {result.get('location', 'location')}",
                'type': 'success'
            }

        return result

    except Exception as e:
        frappe.log_error(f"Mobile check-in failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


@frappe.whitelist()
def mobile_quick_checkout(visit_id, latitude=None, longitude=None, summary="", quality=""):
    """Quick check-out optimized for mobile"""
    try:
        # Use the workflow API
        from crm.api.site_visit_workflow import perform_workflow_action

        result = perform_workflow_action(
            docname=visit_id,
            action='checkout',
            latitude=latitude,
            longitude=longitude,
            visit_summary=summary,
            lead_quality=quality
        )

        # Add mobile-specific enhancements
        if result.get('success'):
            result['mobile_notification'] = {
                'title': 'Check-out Successful',
                'message': f"Visit completed. Duration: {result.get('duration', 'unknown')}",
                'type': 'success'
            }

            # Ask about submission
            result['prompt_submission'] = {
                'title': 'Submit Visit?',
                'message': 'Visit completed successfully. Submit now to finalize?',
                'actions': ['submit_now', 'submit_later']
            }

        return result

    except Exception as e:
        frappe.log_error(f"Mobile check-out failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


@frappe.whitelist()
def get_mobile_navigation_data(user_location=None):
    """Get navigation data for mobile interface"""
    try:
        user = frappe.session.user
        today = getdate()

        # Get today's visits that need navigation
        visits_needing_nav = frappe.get_all(
            'CRM Site Visit',
            filters={
                'sales_person': user,
                'visit_date': today,
                'status': ['in', ['Planned', 'In Progress']]
            },
            fields=[
                'name', 'reference_title', 'visit_address', 'city',
                'check_in_latitude', 'check_in_longitude', 'contact_phone',
                'planned_start_time', 'status'
            ]
        )

        # Enhance with navigation data
        for visit in visits_needing_nav:
            if visit['check_in_latitude'] and visit['check_in_longitude']:
                visit['has_coordinates'] = True
                visit[
                    'google_maps_url'] = f"https://www.google.com/maps/dir/?api=1&destination={visit['check_in_latitude']},{visit['check_in_longitude']}"
                visit[
                    'apple_maps_url'] = f"http://maps.apple.com/?daddr={visit['check_in_latitude']},{visit['check_in_longitude']}"
            else:
                visit['has_coordinates'] = False
                if visit['visit_address']:
                    address_encoded = visit['visit_address'].replace(' ', '+').replace('\n', '+')
                    visit['google_maps_url'] = f"https://www.google.com/maps/dir/?api=1&destination={address_encoded}"

            # Distance calculation if user location provided
            if (user_location and visit.get('check_in_latitude') and visit.get('check_in_longitude')):
                visit['distance'] = calculate_distance(
                    user_location['latitude'], user_location['longitude'],
                    visit['check_in_latitude'], visit['check_in_longitude']
                )

        return {
            'success': True,
            'visits': visits_needing_nav,
            'user_location': user_location
        }

    except Exception as e:
        frappe.log_error(f"Mobile navigation data failed: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


# Utility Functions for Mobile
def is_visit_overdue(visit):
    """Check if visit is overdue"""
    if not visit.get('planned_start_time') or visit['status'] != 'Planned':
        return False

    planned_time = frappe.utils.get_datetime(f"{visit['visit_date']} {visit['planned_start_time']}")
    return planned_time < now_datetime()


def get_visit_time_status(visit):
    """Get time status for visit"""
    if visit['status'] == 'Completed':
        return 'completed'
    elif visit['status'] == 'In Progress':
        return 'in_progress'
    elif is_visit_overdue(visit):
        return 'overdue'
    elif visit.get('planned_start_time'):
        planned_time = frappe.utils.get_datetime(f"{visit['visit_date']} {visit['planned_start_time']}")
        time_diff = (planned_time - now_datetime()).total_seconds() / 3600
        if time_diff <= 1:
            return 'upcoming'
        else:
            return 'scheduled'
    else:
        return 'scheduled'


def format_mobile_time(time_str):
    """Format time for mobile display"""
    if not time_str:
        return ""

    try:
        time_obj = frappe.utils.get_time(time_str)
        return time_obj.strftime("%I:%M %p")
    except:
        return str(time_str)


def format_mobile_date(date_str):
    """Format date for mobile display"""
    if not date_str:
        return ""

    try:
        date_obj = getdate(date_str)
        today = getdate()

        if date_obj == today:
            return "Today"
        elif date_obj == add_days(today, 1):
            return "Tomorrow"
        elif date_obj == add_days(today, -1):
            return "Yesterday"
        else:
            return date_obj.strftime("%b %d")
    except:
        return str(date_str)


def get_status_color(status):
    """Get color code for status"""
    color_map = {
        'Planned': '#3498db',  # Blue
        'In Progress': '#f39c12',  # Orange
        'Completed': '#27ae60',  # Green
        'Cancelled': '#e74c3c',  # Red
        'Postponed': '#9b59b6'  # Purple
    }
    return color_map.get(status, '#95a5a6')


def get_priority_icon(priority):
    """Get icon for priority"""
    icon_map = {
        'High': '🔴',
        'Medium': '🟡',
        'Low': '🟢'
    }
    return icon_map.get(priority, '⚪')


def get_short_address(city, full_address):
    """Get shortened address for mobile display"""
    if city:
        return city
    elif full_address:
        # Return first line of address
        return full_address.split('\n')[0][:30] + "..." if len(full_address) > 30 else full_address.split('\n')[0]
    else:
        return "No address"


def get_next_action_hint(visit):
    """Get next action hint for mobile"""
    if visit['status'] == 'Planned':
        return "Check In"
    elif visit['status'] == 'In Progress':
        return "Check Out"
    elif visit['status'] == 'Completed' and visit.get('docstatus') == 0:
        return "Submit"
    else:
        return ""


def get_step_description(visit):
    """Get step description for mobile"""
    descriptions = {
        'Planned': 'Ready to start visit',
        'In Progress': 'Currently at location',
        'Completed': 'Visit finished, ready to submit',
        'Cancelled': 'Visit was cancelled',
        'Postponed': 'Visit rescheduled'
    }
    return descriptions.get(visit.status, visit.status)


def get_workflow_progress_percentage(visit):
    """Get workflow progress percentage"""
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


def get_recent_activity_summary(user):
    """Get recent activity summary for mobile dashboard"""
    # Last 7 days activity
    week_ago = add_days(getdate(), -7)

    recent_visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'sales_person': user,
            'visit_date': ['>=', week_ago],
            'status': 'Completed'
        },
        fields=['name', 'visit_date', 'reference_title', 'lead_quality'],
        order_by='visit_date desc',
        limit=5
    )

    # Format for mobile
    for visit in recent_visits:
        visit['date_formatted'] = format_mobile_date(visit['visit_date'])
        visit['quality_color'] = {
            'Hot': '#e74c3c',
            'Warm': '#f39c12',
            'Cold': '#3498db'
        }.get(visit.get('lead_quality'), '#95a5a6')

    return recent_visits


def get_mobile_quick_actions(user):
    """Get quick actions available for mobile"""
    actions = [
        {
            'action': 'create_visit',
            'label': 'New Visit',
            'icon': 'plus',
            'color': '#3498db'
        },
        {
            'action': 'view_today',
            'label': "Today's Visits",
            'icon': 'calendar',
            'color': '#27ae60'
        },
        {
            'action': 'emergency_checkin',
            'label': 'Quick Check-in',
            'icon': 'map-pin',
            'color': '#f39c12'
        }
    ]

    return actions


def get_visit_quick_actions(visit):
    """Get quick actions for specific visit"""
    actions = []

    if visit.status == 'Planned' and not visit.check_in_time:
        actions.extend([
            {'action': 'checkin', 'label': 'Check In', 'primary': True},
            {'action': 'navigate', 'label': 'Navigate', 'primary': False},
            {'action': 'call_customer', 'label': 'Call', 'primary': False}
        ])

    elif visit.status == 'In Progress':
        actions.extend([
            {'action': 'checkout', 'label': 'Check Out', 'primary': True},
            {'action': 'add_notes', 'label': 'Add Notes', 'primary': False}
        ])

    elif visit.status == 'Completed' and visit.docstatus == 0:
        actions.extend([
            {'action': 'submit', 'label': 'Submit', 'primary': True},
            {'action': 'edit_summary', 'label': 'Edit Summary', 'primary': False}
        ])

    return actions


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates (in kilometers)"""
    from math import radians, cos, sin, asin, sqrt

    try:
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers

        return round(c * r, 2)
    except:
        return None


def calculate_efficiency_score(user):
    """Calculate user efficiency score"""
    # Simplified efficiency calculation
    # In practice, this would be more sophisticated
    month_start = getdate().replace(day=1)

    month_visits = frappe.get_all('CRM Site Visit',
                                  filters={
                                      'sales_person': user,
                                      'visit_date': ['>=', month_start]
                                  },
                                  fields=['status', 'docstatus']
                                  )

    if not month_visits:
        return 0

    completed = len([v for v in month_visits if v['status'] == 'Completed'])
    submitted = len([v for v in month_visits if v['docstatus'] == 1])

    completion_rate = (completed / len(month_visits)) * 100 if month_visits else 0
    submission_rate = (submitted / completed) * 100 if completed else 0

    # Weighted score
    efficiency = (completion_rate * 0.6) + (submission_rate * 0.4)
    return round(efficiency, 1)


def calculate_completion_streak(user):
    """Calculate consecutive days with completed visits"""
    # This is a simplified implementation
    # In practice, you'd check day by day backwards
    recent_days = 7
    streak = 0

    for i in range(recent_days):
        date = add_days(getdate(), -i)
        day_visits = frappe.get_all('CRM Site Visit',
                                    filters={
                                        'sales_person': user,
                                        'visit_date': date,
                                        'status': 'Completed'
                                    }
                                    )

        if day_visits:
            streak += 1
        else:
            break

    return streak


def get_month_visit_count(user, date):
    """Get visit count for current month"""
    month_start = date.replace(day=1)

    count = frappe.db.count('CRM Site Visit', filters={
        'sales_person': user,
        'visit_date': ['>=', month_start]
    })

    return count
