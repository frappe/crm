# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta


class CRMSiteVisit(Document):
    def validate(self):
        """Validate Site Visit document"""
        self.validate_time_sequence()
        self.validate_location_accuracy()
        self.calculate_duration()
        self.validate_follow_up_date()
        
    def sync_calendar_event(self):
        """Create or update calendar event for this visit"""
        try:
            from crm.api.site_visit_calendar import create_calendar_event_for_visit
            create_calendar_event_for_visit(self)
        except Exception as e:
            frappe.log_error(f"Calendar sync failed for {self.name}: {str(e)}")
    
    def update_calendar_event_timing(self):
        """Update calendar event when check-in/out happens"""
        try:
            from crm.api.site_visit_calendar import on_visit_checkin_checkout
            on_visit_checkin_checkout(self)
        except Exception as e:
            frappe.log_error(f"Calendar timing update failed for {self.name}: {str(e)}")
    
    def on_trash(self):
        """Delete associated calendar event when visit is deleted"""
        try:
            from crm.api.site_visit_calendar import delete_calendar_event_for_visit
            delete_calendar_event_for_visit(self.name)
        except Exception as e:
            frappe.log_error(f"Calendar event deletion failed for {self.name}: {str(e)}")

    def validate_time_sequence(self):
        """Ensure check-out is after check-in"""
        if self.check_in_time and self.check_out_time:
            if self.check_out_time <= self.check_in_time:
                frappe.throw(_("Check-out time must be after check-in time"))
        
        if self.planned_start_time and self.planned_end_time:
            if self.planned_end_time <= self.planned_start_time:
                frappe.throw(_("Planned end time must be after planned start time"))

    def validate_location_accuracy(self):
        """Warn about poor location accuracy"""
        if self.location_accuracy and 'meters' in self.location_accuracy:
            try:
                accuracy = float(self.location_accuracy.replace(' meters', ''))
                if accuracy > 100:  # 100 meters threshold
                    frappe.msgprint(
                        _("Location accuracy is low ({0}). Consider retaking location for better accuracy.").format(self.location_accuracy), 
                        indicator='orange',
                        alert=True
                    )
            except:
                pass

    def calculate_duration(self):
        """Calculate visit duration automatically"""
        if self.check_in_time and self.check_out_time:
            check_in = frappe.utils.get_datetime(self.check_in_time)
            check_out = frappe.utils.get_datetime(self.check_out_time)
            duration = (check_out - check_in).total_seconds()
            self.total_duration = int(duration)

    def validate_follow_up_date(self):
        """Ensure follow-up date is not in the past"""
        if self.follow_up_required and self.follow_up_date:
            if frappe.utils.getdate(self.follow_up_date) < frappe.utils.getdate():
                frappe.throw(_("Follow-up date cannot be in the past"))

    def on_update(self):
        """Actions after document update"""
        # Auto-create follow-up task if required
        if self.follow_up_required and self.follow_up_date and self.status == 'Completed':
            self.create_follow_up_activity()
        
        # Create or update calendar event
        if self.sync_with_calendar:
            self.sync_calendar_event()
        
        # Update event on check-in/check-out
        if self.check_in_time or self.check_out_time:
            self.update_calendar_event_timing()

    def create_follow_up_activity(self):
        """Create follow-up ToDo if doesn't exist"""
        existing = frappe.db.exists('ToDo', {
            'reference_type': 'CRM Site Visit',
            'reference_name': self.name,
            'status': 'Open'
        })
        
        if not existing:
            todo = frappe.get_doc({
                'doctype': 'ToDo',
                'description': f'Follow-up for Site Visit: {self.name}\nCustomer: {self.reference_title}',
                'date': self.follow_up_date,
                'assigned_by': frappe.session.user,
                'owner': self.sales_person,
                'reference_type': 'CRM Site Visit',
                'reference_name': self.name,
                'priority': 'Medium',
                'status': 'Open'
            })
            todo.insert(ignore_permissions=True)
            frappe.db.commit()
    @staticmethod
    def default_list_data():
        columns = [
			{
				"label": "Reference Title",
				"type": "Data",
				"key": "reference_title",
				"width": "11rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "10rem",
			},
   {
				"label": "Visit Date",
				"type": "Date",
				"key": "visit_date",
				"width": "10rem",
			},
   {
				"label": "Visit Type",
				"type": "Select",
				"key": "visit_type",
                "options": """Initial Meeting
Demo/Presentation
Negotiation
Contract Signing
Follow-up
Support
Other""",
				"width": "10rem",
			},
			{
				"label": "Sales Person",
				"type": "Text",
				"key": "Sales Person",
				"width": "10rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
        rows = [
			"name",
			"organization",
			"status",
    "visit_date",
    "visit_type",
    "sales_person",
			"modified",
			"_assign",
		]
        return {"columns": columns, "rows": rows}


@frappe.whitelist()
def get_distance_between_locations(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return round(c * r, 2)


@frappe.whitelist(allow_guest=False)
def mobile_checkin(visit_id, latitude, longitude, accuracy=None):
    """API endpoint for mobile check-in"""
    doc = frappe.get_doc('CRM Site Visit', visit_id)
    
    # Validate permissions
    if not doc.has_permission('write'):
        frappe.throw(_("Insufficient permissions"))
    
    # Get address from coordinates
    address = get_address_from_coordinates(latitude, longitude)
    
    # Update check-in details
    doc.check_in_time = frappe.utils.now()
    doc.check_in_latitude = latitude
    doc.check_in_longitude = longitude
    doc.check_in_location = address
    doc.location_accuracy = f"{accuracy} meters" if accuracy else "Unknown"
    doc.status = 'In Progress'
    
    doc.save()
    
    return {
        "success": True,
        "message": "Check-in successful",
        "visit_id": visit_id,
        "check_in_time": doc.check_in_time,
        "location": address
    }


@frappe.whitelist(allow_guest=False)
def mobile_checkout(visit_id, latitude, longitude, visit_summary=None):
    """API endpoint for mobile check-out"""
    doc = frappe.get_doc('CRM Site Visit', visit_id)
    
    # Validate permissions
    if not doc.has_permission('write'):
        frappe.throw(_("Insufficient permissions"))
    
    if not doc.check_in_time:
        frappe.throw(_("Cannot check-out without check-in"))
    
    # Get address from coordinates
    address = get_address_from_coordinates(latitude, longitude)
    
    # Calculate duration
    check_in_time = frappe.utils.get_datetime(doc.check_in_time)
    check_out_time = frappe.utils.get_datetime(frappe.utils.now())
    duration = (check_out_time - check_in_time).total_seconds()
    
    # Update check-out details
    doc.check_out_time = frappe.utils.now()
    doc.check_out_latitude = latitude
    doc.check_out_longitude = longitude
    doc.check_out_location = address
    doc.total_duration = int(duration)
    doc.status = 'Completed'
    
    if visit_summary:
        doc.visit_summary = visit_summary
    
    doc.save()
    
    return {
        "success": True,
        "message": "Check-out successful",
        "visit_id": visit_id,
        "check_out_time": doc.check_out_time,
        "duration": format_duration(duration),
        "location": address
    }


@frappe.whitelist(allow_guest=False)
def get_my_visits(status=None, limit=50):
    """Get visits for current user"""
    filters = {'sales_person': frappe.session.user}
    if status:
        filters['status'] = status
    
    visits = frappe.get_all('CRM Site Visit',
        filters=filters,
        fields=[
            'name', 'visit_date', 'reference_title', 'visit_type',
            'status', 'city', 'state', 'visit_address', 'priority',
            'check_in_time', 'check_out_time', 'total_duration'
        ],
        order_by='visit_date desc',
        limit=limit
    )
    
    # Format duration for each visit
    for visit in visits:
        if visit.total_duration:
            visit.formatted_duration = format_duration(visit.total_duration)
        else:
            visit.formatted_duration = "0 minutes"
    
    return visits


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


def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "0 minutes"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def send_visit_reminders():
    """Send reminders for upcoming site visits"""
    tomorrow = frappe.utils.add_days(frappe.utils.nowdate(), 1)
    
    visits = frappe.get_all('CRM Site Visit', 
        filters={
            'visit_date': tomorrow,
            'status': 'Planned'
        },
        fields=['name', 'sales_person', 'reference_title', 'visit_address', 'planned_start_time']
    )
    
    for visit in visits:
        # Send email reminder
        try:
            frappe.sendmail(
                recipients=[visit.sales_person],
                subject=f"Site Visit Reminder - {visit.reference_title}",
                message=f"""
                <div style="font-family: Arial, sans-serif; color: #333;">
                    <h3>Site Visit Reminder</h3>
                    <p>Hi,</p>
                    <p>You have a site visit scheduled for tomorrow:</p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <p><strong>Customer:</strong> {visit.reference_title}</p>
                        <p><strong>Visit ID:</strong> {visit.name}</p>
                        <p><strong>Location:</strong> {visit.visit_address or 'Not specified'}</p>
                        {f'<p><strong>Planned Time:</strong> {visit.planned_start_time}</p>' if visit.planned_start_time else ''}
                    </div>
                    <p>Please ensure you have all necessary materials ready and check the location before leaving.</p>
                    <p>Best regards,<br>CRM System</p>
                </div>
                """
            )
        except Exception as e:
            frappe.log_error(f"Failed to send visit reminder: {str(e)}")


    

def update_lead_score_from_visit(doc, method):
    """Update lead score based on visit outcome"""
    if doc.reference_type == 'CRM Lead' and doc.status == 'Completed':
        try:
            lead = frappe.get_doc('CRM Lead', doc.reference_name)
            
            # Calculate score based on visit outcome
            score_increment = 0
            
            if doc.lead_quality == 'Hot':
                score_increment = 20
            elif doc.lead_quality == 'Warm':
                score_increment = 10
            elif doc.lead_quality == 'Cold':
                score_increment = 5
            
            # Additional scoring factors
            if doc.potential_value and doc.potential_value > 100000:
                score_increment += 10
            if doc.probability_percentage and doc.probability_percentage > 70:
                score_increment += 15
            
            # You might need to add a custom field for lead_score in CRM Lead
            # For now, we'll add it to the notes or custom fields
            if score_increment > 0:
                lead.add_comment('Comment', f'Site visit completed. Lead score increased by {score_increment} points. Quality: {doc.lead_quality}')
                lead.save(ignore_permissions=True)
                
        except Exception as e:
            frappe.log_error(f"Failed to update lead score: {str(e)}")
