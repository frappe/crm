# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days, add_months
from datetime import timedelta
import json


@frappe.whitelist()
def get_site_visit_analytics(from_date=None, to_date=None, sales_person=None, territory=None):
    """Get comprehensive site visit analytics"""
    
    if not from_date:
        from_date = add_months(getdate(), -3)
    if not to_date:
        to_date = getdate()
    
    filters = {
        'visit_date': ['between', [from_date, to_date]],
        'docstatus': ['!=', 2]
    }
    
    if sales_person:
        filters['sales_person'] = sales_person
    
    if territory:
        filters['territory'] = territory
    
    # Get all visits data
    visits = frappe.get_all(
        'CRM Site Visit',
        filters=filters,
        fields=[
            'name', 'visit_date', 'sales_person', 'status', 'visit_type',
            'lead_quality', 'total_duration', 'potential_value', 'probability_percentage',
            'reference_type', 'reference_name', 'city', 'check_in_time', 'check_out_time',
            'territory'
        ]
    )
    
    # Calculate key metrics
    total_visits = len(visits)
    completed_visits = len([v for v in visits if v.status == 'Completed'])
    in_progress_visits = len([v for v in visits if v.status == 'In Progress'])
    planned_visits = len([v for v in visits if v.status == 'Planned'])
    cancelled_visits = len([v for v in visits if v.status == 'Cancelled'])
    
    # Calculate durations
    total_duration = sum([v.total_duration or 0 for v in visits if v.total_duration])
    avg_duration = total_duration / completed_visits if completed_visits > 0 else 0
    
    # Calculate conversion metrics
    hot_leads = len([v for v in visits if v.lead_quality == 'Hot'])
    warm_leads = len([v for v in visits if v.lead_quality == 'Warm'])
    cold_leads = len([v for v in visits if v.lead_quality == 'Cold'])
    
    # Calculate potential value
    total_potential_value = sum([v.potential_value or 0 for v in visits])
    avg_potential_value = total_potential_value / total_visits if total_visits > 0 else 0
    
    # Sales person performance
    sales_performance = {}
    for visit in visits:
        sales_person_name = visit.sales_person or 'Unassigned'
        if sales_person_name not in sales_performance:
            sales_performance[sales_person_name] = {
                'total_visits': 0,
                'completed_visits': 0,
                'total_duration': 0,
                'hot_leads': 0,
                'potential_value': 0
            }
        
        perf = sales_performance[sales_person_name]
        perf['total_visits'] += 1
        if visit.status == 'Completed':
            perf['completed_visits'] += 1
        if visit.total_duration:
            perf['total_duration'] += visit.total_duration
        if visit.lead_quality == 'Hot':
            perf['hot_leads'] += 1
        if visit.potential_value:
            perf['potential_value'] += visit.potential_value
    
    # Visit type analysis
    visit_type_analysis = {}
    for visit in visits:
        visit_type = visit.visit_type or 'Unknown'
        if visit_type not in visit_type_analysis:
            visit_type_analysis[visit_type] = {
                'count': 0,
                'completed': 0,
                'hot_leads': 0,
                'avg_duration': 0,
                'total_duration': 0
            }
        
        analysis = visit_type_analysis[visit_type]
        analysis['count'] += 1
        if visit.status == 'Completed':
            analysis['completed'] += 1
            if visit.total_duration:
                analysis['total_duration'] += visit.total_duration
        if visit.lead_quality == 'Hot':
            analysis['hot_leads'] += 1
    
    # Calculate average durations for visit types
    for vtype, data in visit_type_analysis.items():
        if data['completed'] > 0:
            data['avg_duration'] = data['total_duration'] / data['completed']
    
    # Time-based analysis (weekly trends)
    weekly_trends = get_weekly_trends(visits)
    
    # City-wise analysis
    city_analysis = {}
    for visit in visits:
        city = visit.city or 'Unknown'
        if city not in city_analysis:
            city_analysis[city] = {
                'count': 0,
                'completed': 0,
                'hot_leads': 0,
                'potential_value': 0
            }
        
        city_data = city_analysis[city]
        city_data['count'] += 1
        if visit.status == 'Completed':
            city_data['completed'] += 1
        if visit.lead_quality == 'Hot':
            city_data['hot_leads'] += 1
        if visit.potential_value:
            city_data['potential_value'] += visit.potential_value
    
    return {
        'summary': {
            'total_visits': total_visits,
            'completed_visits': completed_visits,
            'in_progress_visits': in_progress_visits,
            'planned_visits': planned_visits,
            'cancelled_visits': cancelled_visits,
            'completion_rate': (completed_visits / total_visits * 100) if total_visits > 0 else 0,
            'total_duration_hours': total_duration / 3600 if total_duration > 0 else 0,
            'avg_duration_hours': avg_duration / 3600 if avg_duration > 0 else 0,
            'hot_leads': hot_leads,
            'warm_leads': warm_leads,
            'cold_leads': cold_leads,
            'total_potential_value': total_potential_value,
            'avg_potential_value': avg_potential_value
        },
        'sales_performance': sales_performance,
        'visit_type_analysis': visit_type_analysis,
        'city_analysis': city_analysis,
        'weekly_trends': weekly_trends
    }


def get_weekly_trends(visits):
    """Get weekly trends for visits"""
    weekly_data = {}
    
    for visit in visits:
        if not visit.visit_date:
            continue
            
        # Get week start date (Monday)
        visit_date = getdate(visit.visit_date)
        week_start = visit_date - timedelta(days=visit_date.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        
        if week_key not in weekly_data:
            weekly_data[week_key] = {
                'week_start': week_key,
                'total_visits': 0,
                'completed_visits': 0,
                'hot_leads': 0,
                'potential_value': 0
            }
        
        week_data = weekly_data[week_key]
        week_data['total_visits'] += 1
        if visit.status == 'Completed':
            week_data['completed_visits'] += 1
        if visit.lead_quality == 'Hot':
            week_data['hot_leads'] += 1
        if visit.potential_value:
            week_data['potential_value'] += visit.potential_value
    
    # Convert to sorted list
    return sorted(weekly_data.values(), key=lambda x: x['week_start'])


@frappe.whitelist()
def get_visit_heatmap_data(sales_person=None):
    """Get data for visit heatmap visualization"""
    
    # Get last 90 days of data
    from_date = add_days(getdate(), -90)
    to_date = getdate()
    
    filters = {
        'visit_date': ['between', [from_date, to_date]],
        'docstatus': ['!=', 2]
    }
    
    if sales_person:
        filters['sales_person'] = sales_person
    
    visits = frappe.get_all(
        'CRM Site Visit',
        filters=filters,
        fields=['visit_date', 'status']
    )
    
    # Create heatmap data
    heatmap_data = {}
    current_date = from_date
    
    while current_date <= to_date:
        date_str = current_date.strftime('%Y-%m-%d')
        heatmap_data[date_str] = {
            'date': date_str,
            'count': 0,
            'completed': 0
        }
        current_date = add_days(current_date, 1)
    
    # Fill in actual data
    for visit in visits:
        if not visit.visit_date:
            continue
            
        date_str = visit.visit_date.strftime('%Y-%m-%d')
        if date_str in heatmap_data:
            heatmap_data[date_str]['count'] += 1
            if visit.status == 'Completed':
                heatmap_data[date_str]['completed'] += 1
    
    return list(heatmap_data.values())


@frappe.whitelist()
def get_location_analytics():
    """Get location-based analytics for visits"""
    
    # Get visits with location data
    visits = frappe.get_all(
        'CRM Site Visit',
        filters={
            'check_in_latitude': ['!=', ''],
            'check_in_longitude': ['!=', ''],
            'docstatus': ['!=', 2]
        },
        fields=[
            'name', 'check_in_latitude', 'check_in_longitude', 'city',
            'status', 'visit_type', 'lead_quality', 'potential_value'
        ]
    )
    
    # Group by approximate location (rounded coordinates)
    location_groups = {}
    
    for visit in visits:
        try:
            # Safely convert and round coordinates
            lat = visit.check_in_latitude
            lng = visit.check_in_longitude
            
            if not lat or not lng:
                continue
                
            lat_rounded = round(float(lat), 2)
            lng_rounded = round(float(lng), 2)
            location_key = f"{lat_rounded},{lng_rounded}"
            
            if location_key not in location_groups:
                location_groups[location_key] = {
                    'lat': lat_rounded,
                    'lng': lng_rounded,
                    'city': visit.city or 'Unknown',
                    'visits': [],
                    'total_visits': 0,
                    'completed_visits': 0,
                    'hot_leads': 0,
                    'total_potential_value': 0
                }
            
            group = location_groups[location_key]
            group['visits'].append(visit.name)
            group['total_visits'] += 1
            
            if visit.status == 'Completed':
                group['completed_visits'] += 1
            if visit.lead_quality == 'Hot':
                group['hot_leads'] += 1
            if visit.potential_value:
                group['total_potential_value'] += visit.potential_value
                
        except (ValueError, TypeError):
            # Skip visits with invalid coordinate data
            continue
    
    return list(location_groups.values())


@frappe.whitelist()
def export_visit_data(from_date=None, to_date=None, sales_person=None):
    """Export comprehensive visit data for analysis"""
    
    if not from_date:
        from_date = add_months(getdate(), -1)
    if not to_date:
        to_date = getdate()
    
    filters = {
        'visit_date': ['between', [from_date, to_date]],
        'docstatus': ['!=', 2]
    }
    
    if sales_person:
        filters['sales_person'] = sales_person
    
    visits = frappe.get_all(
        'CRM Site Visit',
        filters=filters,
        fields=[
            'name', 'visit_date', 'sales_person', 'reference_type', 'reference_name',
            'reference_title', 'visit_type', 'status', 'priority', 'city', 'state',
            'visit_purpose', 'visit_summary', 'lead_quality', 'potential_value',
            'probability_percentage', 'check_in_time', 'check_out_time', 'total_duration',
            'follow_up_required', 'follow_up_date'
        ],
        order_by='visit_date desc'
    )
    
    # Add calculated fields
    for visit in visits:
        if visit.total_duration and visit.total_duration > 0:
            visit['duration_hours'] = round(visit.total_duration / 3600, 2)
        else:
            visit['duration_hours'] = 0
        
        if visit.visit_date:
            visit['week_of_year'] = getdate(visit.visit_date).isocalendar()[1]
            visit['month'] = getdate(visit.visit_date).strftime('%B %Y')
        else:
            visit['week_of_year'] = 0
            visit['month'] = 'Unknown'
    
    return visits