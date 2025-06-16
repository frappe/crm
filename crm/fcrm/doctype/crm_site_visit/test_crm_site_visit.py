# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
import unittest


class TestCRMSiteVisit(unittest.TestCase):
    def setUp(self):
        """Set up test data"""
        self.test_lead = self.create_test_lead()
        
    def create_test_lead(self):
        """Create a test lead for site visit"""
        if not frappe.db.exists("CRM Lead", "Test Lead for Site Visit"):
            lead = frappe.get_doc({
                "doctype": "CRM Lead",
                "lead_name": "Test Lead for Site Visit",
                "organization": "Test Company",
                "email": "test@example.com",
                "mobile_no": "9876543210",
                "lead_owner": "Administrator"
            })
            lead.insert()
            return lead.name
        return "Test Lead for Site Visit"
    
    def test_create_site_visit(self):
        """Test creating a site visit"""
        visit = frappe.get_doc({
            "doctype": "CRM Site Visit",
            "visit_date": frappe.utils.today(),
            "visit_type": "Initial Meeting",
            "reference_type": "CRM Lead",
            "reference_name": self.test_lead,
            "sales_person": "Administrator",
            "visit_purpose": "Initial discussion about requirements"
        })
        visit.insert()
        
        self.assertEqual(visit.status, "Planned")
        self.assertEqual(visit.reference_type, "CRM Lead")
        
        # Clean up
        visit.delete()
    
    def test_time_validation(self):
        """Test time sequence validation"""
        visit = frappe.get_doc({
            "doctype": "CRM Site Visit",
            "visit_date": frappe.utils.today(),
            "visit_type": "Initial Meeting",
            "reference_type": "CRM Lead",
            "reference_name": self.test_lead,
            "sales_person": "Administrator",
            "visit_purpose": "Test visit",
            "planned_start_time": "2025-06-14 10:00:00",
            "planned_end_time": "2025-06-14 09:00:00"  # End before start
        })
        
        with self.assertRaises(frappe.ValidationError):
            visit.insert()
    
    def test_follow_up_date_validation(self):
        """Test follow-up date validation"""
        visit = frappe.get_doc({
            "doctype": "CRM Site Visit",
            "visit_date": frappe.utils.today(),
            "visit_type": "Initial Meeting",
            "reference_type": "CRM Lead",
            "reference_name": self.test_lead,
            "sales_person": "Administrator",
            "visit_purpose": "Test visit",
            "follow_up_required": 1,
            "follow_up_date": frappe.utils.add_days(frappe.utils.today(), -1)  # Past date
        })
        
        with self.assertRaises(frappe.ValidationError):
            visit.insert()
    
    def test_duration_calculation(self):
        """Test duration calculation"""
        visit = frappe.get_doc({
            "doctype": "CRM Site Visit",
            "visit_date": frappe.utils.today(),
            "visit_type": "Initial Meeting",
            "reference_type": "CRM Lead",
            "reference_name": self.test_lead,
            "sales_person": "Administrator",
            "visit_purpose": "Test visit",
            "check_in_time": "2025-06-14 10:00:00",
            "check_out_time": "2025-06-14 11:30:00"
        })
        visit.insert()
        
        # Duration should be 90 minutes (5400 seconds)
        self.assertEqual(visit.total_duration, 5400)
        
        # Clean up
        visit.delete()
    
    def tearDown(self):
        """Clean up test data"""
        if frappe.db.exists("CRM Lead", self.test_lead):
            frappe.delete_doc("CRM Lead", self.test_lead)
