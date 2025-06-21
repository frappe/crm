# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document


class CRMSiteVisit(Document):
    def before_save(self):
        """Server-side processing before saving - handles all auto-population and workflow logic"""
        # Auto-populate reference details
        self.populate_reference_details()

        # Auto-populate address if customer_address is provided
        self.populate_address_details()

        # Set follow-up date if required but not set
        self.auto_set_followup_date()

        # Process geolocation if coordinates provided
        self.process_geolocation()

        # Update workflow status based on check-in/out state
        self.update_workflow_status()

    def validate(self):
        """Validate Site Visit document"""
        self.validate_time_sequence()
        self.validate_location_accuracy()
        self.calculate_duration()
        self.validate_follow_up_date()
        self.validate_submission_workflow()

    def populate_reference_details(self):
        """Auto-populate reference details server-side"""
        if not self.reference_name or not self.reference_type:
            return

        try:
            ref_doc = frappe.get_doc(self.reference_type, self.reference_name)

            if self.reference_type == 'CRM Lead':
                # Only populate if field is empty to avoid overwriting user changes
                if not self.reference_title:
                    self.reference_title = ref_doc.get('lead_name') or ref_doc.get('organization') or 'Unknown'
                if ref_doc.get('mobile_no') and not self.contact_phone:
                    self.contact_phone = ref_doc.mobile_no
                if ref_doc.get('email') and not self.contact_email:
                    self.contact_email = ref_doc.email
                if ref_doc.get('city') and not self.city:
                    self.city = ref_doc.city
                if ref_doc.get('state') and not self.state:
                    self.state = ref_doc.state
                if ref_doc.get('organization') and not self.organization:
                    self.organization = ref_doc.organization

            elif self.reference_type == 'CRM Deal':
                if not self.reference_title:
                    self.reference_title = ref_doc.get('organization') or ref_doc.name
                if ref_doc.get('deal_value') and not self.potential_value:
                    self.potential_value = ref_doc.deal_value
                if ref_doc.get('probability') and not self.probability_percentage:
                    self.probability_percentage = ref_doc.probability
                if ref_doc.get('organization') and not self.organization:
                    self.organization = ref_doc.organization

            elif self.reference_type == 'Customer':
                if not self.reference_title:
                    self.reference_title = ref_doc.get('customer_name') or 'Unknown'
                if ref_doc.get('customer_name') and not self.organization:
                    self.organization = ref_doc.customer_name

        except Exception as e:
            frappe.log_error(f"Failed to populate reference details for {self.name}: {str(e)}")

    def populate_address_details(self):
        """Auto-populate address from customer_address"""
        if not self.customer_address:
            return

        try:
            addr = frappe.get_doc('Address', self.customer_address)

            # Only populate if field is empty
            if not self.visit_address:
                address_lines = []
                if addr.address_line1:
                    address_lines.append(addr.address_line1)
                if addr.address_line2:
                    address_lines.append(addr.address_line2)
                self.visit_address = '\n'.join(address_lines)

            if not self.city and addr.city:
                self.city = addr.city
            if not self.state and addr.state:
                self.state = addr.state
            if not self.country and addr.country:
                self.country = addr.country
            if not self.pincode and addr.pincode:
                self.pincode = addr.pincode

        except Exception as e:
            frappe.log_error(f"Failed to populate address for {self.name}: {str(e)}")

    def auto_set_followup_date(self):
        """Auto-set follow-up date if required but not set"""
        if self.follow_up_required and not self.follow_up_date and self.visit_date:
            self.follow_up_date = frappe.utils.add_days(self.visit_date, 7)

    def process_geolocation(self):
        """Process geolocation data server-side"""
        # Process check-in location
        if (self.check_in_latitude and self.check_in_longitude and
                not self.check_in_location):
            self.check_in_location = self.get_address_from_coordinates(
                self.check_in_latitude, self.check_in_longitude
            )

        # Process check-out location
        if (self.check_out_latitude and self.check_out_longitude and
                not self.check_out_location):
            self.check_out_location = self.get_address_from_coordinates(
                self.check_out_latitude, self.check_out_longitude
            )

    def update_workflow_status(self):
        """Update workflow status based on current state"""
        # Auto-update status based on check-in/out
        if self.check_in_time and not self.check_out_time and self.status == 'Planned':
            self.status = 'In Progress'
        elif self.check_in_time and self.check_out_time and self.status == 'In Progress':
            self.status = 'Completed'

    def get_address_from_coordinates(self, latitude, longitude):
        """Server-side reverse geocoding with caching"""
        try:
            # Check if we have a cached result
            cache_key = f"geocode_{latitude:.6f}_{longitude:.6f}"
            cached_result = frappe.cache().get_value(cache_key)
            if cached_result:
                return cached_result

            # Make API call
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&zoom=18&addressdetails=1"
            headers = {'User-Agent': 'Frappe CRM Site Visit'}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'display_name' in data:
                    address = data['display_name']
                    # Cache for 24 hours
                    frappe.cache().set_value(cache_key, address, expires_in_sec=86400)
                    return address
        except Exception as e:
            frappe.log_error(f"Geocoding error for {latitude}, {longitude}: {str(e)}")

        # Fallback to coordinates
        return f"{float(latitude):.6f}, {float(longitude):.6f}"

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
            check_in = frappe.utils.get_datetime(self.check_in_time)
            check_out = frappe.utils.get_datetime(self.check_out_time)
            if check_out <= check_in:
                frappe.throw(_("Check-out time must be after check-in time"))
        
        if self.planned_start_time and self.planned_end_time:
            planned_start = frappe.utils.get_datetime(f"{self.visit_date} {self.planned_start_time}")
            planned_end = frappe.utils.get_datetime(f"{self.visit_date} {self.planned_end_time}")
            if planned_end <= planned_start:
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

    def validate_submission_workflow(self):
        """Validate submission workflow and provide guidance"""
        if self.docstatus == 0:  # Draft
            if self.status == 'Completed' and self.check_out_time:
                frappe.msgprint(
                    _("Visit is completed. You can now submit this document to finalize the record."),
                    indicator='green',
                    alert=True
                )

    def before_submit(self):
        """Validate before submission - enforce completion requirement"""
        if self.status != 'Completed':
            frappe.throw(
                _("Site Visit can only be submitted after completion. Current status: {0}").format(self.status),
                title=_("Submission Not Allowed")
            )

        if not self.check_out_time:
            frappe.throw(
                _("Cannot submit without check-out. Please complete the visit first."),
                title=_("Check-out Required")
            )

        if not self.visit_summary:
            frappe.msgprint(
                _("Consider adding a visit summary before submission for better record keeping."),
                indicator='orange',
                alert=True
            )

    def on_submit(self):
        """Actions after successful submission"""
        # Create follow-up tasks
        if self.follow_up_required and self.follow_up_date:
            self.create_follow_up_activity()

        # Update related lead/deal scores
        self.update_related_records()

        # Send completion notification
        self.send_completion_notification()

        # Log submission for analytics
        self.log_visit_completion()

    def update_related_records(self):
        """Update related CRM records after visit completion"""
        try:
            if self.reference_type == 'CRM Lead':
                self.update_lead_from_visit()
            elif self.reference_type == 'CRM Deal':
                self.update_deal_from_visit()
        except Exception as e:
            frappe.log_error(f"Failed to update related records for {self.name}: {str(e)}")

    def update_lead_from_visit(self):
        """Update lead based on visit outcome"""
        if not self.reference_name:
            return

        try:
            lead = frappe.get_doc('CRM Lead', self.reference_name)

            # Add visit summary as comment
            comment_text = f"Site visit completed on {self.visit_date}\n"
            if self.lead_quality:
                comment_text += f"Lead Quality: {self.lead_quality}\n"
            if self.visit_summary:
                comment_text += f"Summary: {self.visit_summary}\n"
            if self.next_steps:
                comment_text += f"Next Steps: {self.next_steps}"

            lead.add_comment('Comment', comment_text)
            lead.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to update lead {self.reference_name}: {str(e)}")

    def update_deal_from_visit(self):
        """Update deal based on visit outcome"""
        if not self.reference_name:
            return

        try:
            deal = frappe.get_doc('CRM Deal', self.reference_name)

            # Update deal probability if provided
            if self.probability_percentage and self.probability_percentage != deal.probability:
                deal.probability = self.probability_percentage

            # Add visit summary as comment
            comment_text = f"Site visit completed on {self.visit_date}\n"
            if self.visit_summary:
                comment_text += f"Summary: {self.visit_summary}\n"
            if self.next_steps:
                comment_text += f"Next Steps: {self.next_steps}"

            deal.add_comment('Comment', comment_text)
            deal.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to update deal {self.reference_name}: {str(e)}")

    def send_completion_notification(self):
        """Send notification after visit completion"""
        try:
            # Notify sales manager if exists
            if self.sales_manager and self.sales_manager != self.sales_person:
                frappe.sendmail(
                    recipients=[self.sales_manager],
                    subject=f"Site Visit Completed - {self.reference_title}",
                    message=f"""
                    <div style="font-family: Arial, sans-serif; color: #333;">
                        <h3>Site Visit Completed</h3>
                        <p>A site visit has been completed:</p>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <p><strong>Visit ID:</strong> {self.name}</p>
                            <p><strong>Customer:</strong> {self.reference_title}</p>
                            <p><strong>Sales Person:</strong> {self.sales_person}</p>
                            <p><strong>Visit Date:</strong> {self.visit_date}</p>
                            {f'<p><strong>Lead Quality:</strong> {self.lead_quality}</p>' if self.lead_quality else ''}
                            {f'<p><strong>Potential Value:</strong> {frappe.utils.fmt_money(self.potential_value)}</p>' if self.potential_value else ''}
                            {f'<p><strong>Follow-up Required:</strong> Yes ({self.follow_up_date})</p>' if self.follow_up_required else ''}
                        </div>
                        {f'<p><strong>Summary:</strong><br>{self.visit_summary}</p>' if self.visit_summary else ''}
                        <p>You can view the complete visit details in the CRM system.</p>
                    </div>
                    """
                )
        except Exception as e:
            frappe.log_error(f"Failed to send completion notification: {str(e)}")

    def log_visit_completion(self):
        """Log visit completion for analytics and reporting"""
        try:
            # Log essential metrics for dashboard/analytics
            frappe.db.set_value('CRM Site Visit', self.name, {
                'submitted_on': frappe.utils.now(),
                'submitted_by': frappe.session.user
            }, update_modified=False)

            # You can extend this to create custom analytics logs
            # For example, maintaining a separate analytics table

        except Exception as e:
            frappe.log_error(f"Failed to log visit completion: {str(e)}")

    def on_update(self):
        """Actions after document update"""
        # Only create follow-up activities for submitted documents
        # Draft documents should wait until submission
        if (self.follow_up_required and self.follow_up_date and
                self.status == 'Completed' and self.docstatus == 1):
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


# Legacy API endpoints - now redirect to new workflow APIs
@frappe.whitelist(allow_guest=False)
def mobile_checkin(visit_id, latitude, longitude, accuracy=None):
    """Legacy API endpoint - redirects to new workflow API"""
    from crm.api.site_visit_workflow import perform_workflow_action
    return perform_workflow_action(
        docname=visit_id,
        action='checkin',
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy
    )


@frappe.whitelist(allow_guest=False)
def mobile_checkout(visit_id, latitude, longitude, visit_summary=None, auto_submit=False):
    """Legacy API endpoint - redirects to new workflow API"""
    from crm.api.site_visit_workflow import perform_workflow_action
    return perform_workflow_action(
        docname=visit_id,
        action='checkout',
        latitude=latitude,
        longitude=longitude,
        visit_summary=visit_summary,
        auto_submit=auto_submit
    )


@frappe.whitelist(allow_guest=False)
def submit_visit(visit_id):
    """Legacy API endpoint - redirects to new workflow API"""
    from crm.api.site_visit_workflow import perform_workflow_action
    return perform_workflow_action(
        docname=visit_id,
        action='submit'
    )


@frappe.whitelist(allow_guest=False)
def get_my_visits(status=None, limit=50):
    """Get visits for current user with enhanced mobile data"""
    filters = {'sales_person': frappe.session.user}
    if status:
        filters['status'] = status
    
    visits = frappe.get_all('CRM Site Visit',
        filters=filters,
        fields=[
            'name', 'visit_date', 'reference_title', 'visit_type',
            'status', 'city', 'state', 'visit_address', 'priority',
            'check_in_time', 'check_out_time', 'total_duration',
            'docstatus', 'modified'
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

        # Add workflow capabilities
        visit['can_checkin'] = (visit['status'] == 'Planned' and not visit['check_in_time'])
        visit['can_checkout'] = (
                    visit['status'] == 'In Progress' and visit['check_in_time'] and not visit['check_out_time'])
        visit['can_submit'] = (visit['status'] == 'Completed' and visit['docstatus'] == 0)

    return visits


# Utility Functions
@frappe.whitelist()
def get_distance_between_locations(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt

    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers

    return round(c * r, 2)


def get_address_from_coordinates(latitude, longitude):
    """Global function for reverse geocoding with fallback"""
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


# Document Event Hook Functions - these are called from hooks.py

def before_save_server_side_processing(doc, method):
    """Hook function called from hooks.py before_save"""
    # Call the instance method
    doc.before_save()

def update_lead_score_from_visit(doc, method):
    """Hook function - Update lead score based on visit outcome"""
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


def update_workflow_state(doc, method):
    """Hook function - Update workflow state on document update"""
    try:
        # Auto-update status based on check-in/out
        if doc.check_in_time and not doc.check_out_time and doc.status == 'Planned':
            doc.db_set('status', 'In Progress', update_modified=False)
        elif doc.check_in_time and doc.check_out_time and doc.status == 'In Progress':
            doc.db_set('status', 'Completed', update_modified=False)

        # Update calendar events if sync is enabled
        if doc.sync_with_calendar:
            doc.update_calendar_event_timing()

    except Exception as e:
        frappe.log_error(f"Failed to update workflow state for {doc.name}: {str(e)}")


def on_submit_enhancements(doc, method):
    """Hook function - Enhanced actions on document submission"""
    try:
        # Validate submission requirements
        if doc.status != 'Completed':
            frappe.throw(
                _("Site Visit can only be submitted after completion. Current status: {0}").format(doc.status),
                title=_("Submission Not Allowed")
            )

        if not doc.check_out_time:
            frappe.throw(
                _("Cannot submit without check-out. Please complete the visit first."),
                title=_("Check-out Required")
            )

        # Create follow-up tasks
        if doc.follow_up_required and doc.follow_up_date:
            doc.create_follow_up_activity()

        # Update related lead/deal scores
        doc.update_related_records()

        # Send completion notification
        doc.send_completion_notification()

        # Log submission for analytics
        doc.log_visit_completion()

        frappe.msgprint(
            _("Site visit submitted successfully. Follow-up tasks and notifications have been created."),
            indicator='green',
            alert=True
        )

    except Exception as e:
        frappe.log_error(f"Failed to process submission enhancements for {doc.name}: {str(e)}")
        frappe.throw(_("Error during submission processing. Please try again or contact support."))


def after_insert_calendar_sync(doc, method):
    """Hook function - Sync with calendar after document creation"""
    try:
        # Only sync if calendar sync is enabled
        if doc.sync_with_calendar:
            doc.sync_calendar_event()

        # Send creation notification to sales manager
        if doc.sales_manager and doc.sales_manager != doc.sales_person:
            frappe.sendmail(
                recipients=[doc.sales_manager],
                subject=f"New Site Visit Scheduled - {doc.reference_title}",
                message=f"""
                <div style="font-family: Arial, sans-serif; color: #333;">
                    <h3>New Site Visit Scheduled</h3>
                    <p>A new site visit has been scheduled:</p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <p><strong>Visit ID:</strong> {doc.name}</p>
                        <p><strong>Customer:</strong> {doc.reference_title}</p>
                        <p><strong>Sales Person:</strong> {doc.sales_person}</p>
                        <p><strong>Visit Date:</strong> {doc.visit_date}</p>
                        <p><strong>Visit Type:</strong> {doc.visit_type}</p>
                        {f'<p><strong>Planned Time:</strong> {doc.planned_start_time}</p>' if doc.planned_start_time else ''}
                        {f'<p><strong>Location:</strong> {doc.visit_address}</p>' if doc.visit_address else ''}
                    </div>
                    <p>You can view the complete visit details in the CRM system.</p>
                </div>
                """
            )

        frappe.msgprint(
            _("Site visit created successfully. Calendar sync and notifications have been processed."),
            indicator='green',
            alert=True
        )

    except Exception as e:
        frappe.log_error(f"Failed to process calendar sync after insert for {doc.name}: {str(e)}")
        # Don't throw error here as it would prevent document creation
        frappe.msgprint(
            _("Site visit created but calendar sync failed. You can manually sync later."),
            indicator='orange',
            alert=True
        )
