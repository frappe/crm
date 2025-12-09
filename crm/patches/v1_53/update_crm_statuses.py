import frappe


def execute():
	"""
	Update CRM Lead and Deal statuses to match the new custom status structure.
	This patch:
	1. Updates existing lead status colors and positions
	2. Creates missing lead statuses (if any)
	3. Updates existing deal statuses (renames, updates colors, positions)
	4. Creates missing deal statuses
	5. Handles migration of old status names to new ones
	6. Deletes old status definitions that are no longer needed
	"""
	
	# Update Lead Statuses
	update_lead_statuses()
	
	# Update Deal Statuses
	update_deal_statuses()
	
	frappe.db.commit()


def update_lead_statuses():
	"""Update lead statuses to: New, Qualified, Unqualified, Junk"""
	
	lead_statuses_config = {
		"New": {
			"color": "gray",
			"position": 1,
		},
		"Qualified": {
			"color": "gray",
			"position": 2,
		},
		"Unqualified": {
			"color": "gray",
			"position": 3,
		},
		"Junk": {
			"color": "purple",
			"position": 4,
		},
	}
	
	# Update or create lead statuses
	for status_name, config in lead_statuses_config.items():
		if frappe.db.exists("CRM Lead Status", status_name):
			# Update existing status
			doc = frappe.get_doc("CRM Lead Status", status_name)
			doc.color = config["color"]
			doc.position = config["position"]
			doc.save()
		else:
			# Create new status
			doc = frappe.new_doc("CRM Lead Status")
			doc.lead_status = status_name
			doc.color = config["color"]
			doc.position = config["position"]
			doc.insert()
	
	# Migrate old statuses to new ones if they exist
	old_to_new_mapping = {
		"Contacted": "Qualified",  # Map Contacted to Qualified
		"Nurture": "Qualified",    # Map Nurture to Qualified
		"OPEN": "New",             # Map OPEN to New (if it exists)
	}
	
	for old_status, new_status in old_to_new_mapping.items():
		if frappe.db.exists("CRM Lead Status", old_status):
			# Migrate leads using old status to new status
			leads_with_old_status = frappe.get_all(
				"CRM Lead",
				filters={"status": old_status},
				fields=["name"]
			)
			
			for lead in leads_with_old_status:
				frappe.db.set_value("CRM Lead", lead.name, "status", new_status)
	
	# Delete old status definitions that are no longer in use
	all_lead_statuses = frappe.get_all("CRM Lead Status", fields=["name"])
	valid_statuses = set(lead_statuses_config.keys())
	
	for status_doc in all_lead_statuses:
		status_name = status_doc.name
		if status_name not in valid_statuses:
			# Check if any leads are still using this status
			leads_count = frappe.db.count("CRM Lead", {"status": status_name})
			if leads_count == 0:
				try:
					frappe.delete_doc("CRM Lead Status", status_name, force=True)
					frappe.log_error(f"Deleted old lead status: {status_name}", "Status Cleanup")
				except Exception as e:
					frappe.log_error(f"Error deleting status {status_name}: {str(e)}", "Status Cleanup Error")


def update_deal_statuses():
	"""Update deal statuses to: Qualification, Quotation, Followup, Ready to Close, Won, Lost, Hold"""
	
	deal_statuses_config = {
		"Qualification": {
			"color": "gray",
			"type": "Open",
			"probability": 10,
			"position": 1,
		},
		"Quotation": {
			"color": "blue",
			"type": "Ongoing",
			"probability": 50,
			"position": 2,
		},
		"Followup": {
			"color": "gray",
			"type": "Ongoing",
			"probability": 40,
			"position": 3,
		},
		"Ready to Close": {
			"color": "purple",
			"type": "Ongoing",
			"probability": 90,
			"position": 4,
		},
		"Won": {
			"color": "green",
			"type": "Won",
			"probability": 100,
			"position": 5,
		},
		"Lost": {
			"color": "red",
			"type": "Lost",
			"probability": 0,
			"position": 6,
		},
		"Hold": {
			"color": "purple",
			"type": "On Hold",
			"probability": 30,
			"position": 7,
		},
	}
	
	# Handle renaming of "Proposal/Quotation" to "Quotation"
	if frappe.db.exists("CRM Deal Status", "Proposal/Quotation"):
		if not frappe.db.exists("CRM Deal Status", "Quotation"):
			# Rename the status
			frappe.rename_doc("CRM Deal Status", "Proposal/Quotation", "Quotation", force=True)
		else:
			# If Quotation already exists, migrate deals and delete old status
			deals_with_old_status = frappe.get_all(
				"CRM Deal",
				filters={"status": "Proposal/Quotation"},
				fields=["name"]
			)
			
			for deal in deals_with_old_status:
				frappe.db.set_value("CRM Deal", deal.name, "status", "Quotation")
			
			# Delete old status after migration
			try:
				frappe.delete_doc("CRM Deal Status", "Proposal/Quotation", force=True)
				frappe.log_error("Deleted old deal status: Proposal/Quotation", "Status Cleanup")
			except Exception as e:
				frappe.log_error(f"Error deleting Proposal/Quotation: {str(e)}", "Status Cleanup Error")
	
	# Update or create deal statuses
	for status_name, config in deal_statuses_config.items():
		if frappe.db.exists("CRM Deal Status", status_name):
			# Update existing status
			doc = frappe.get_doc("CRM Deal Status", status_name)
			doc.color = config["color"]
			doc.type = config["type"]
			doc.probability = config["probability"]
			doc.position = config["position"]
			doc.save()
		else:
			# Create new status
			doc = frappe.new_doc("CRM Deal Status")
			doc.deal_status = status_name
			doc.color = config["color"]
			doc.type = config["type"]
			doc.probability = config["probability"]
			doc.position = config["position"]
			doc.insert()
	
	# Migrate old statuses to new ones if they exist
	old_to_new_mapping = {
		"Demo/Making": "Followup",      # Map Demo/Making to Followup
		"Negotiation": "Ready to Close", # Map Negotiation to Ready to Close
	}
	
	for old_status, new_status in old_to_new_mapping.items():
		if frappe.db.exists("CRM Deal Status", old_status):
			# Migrate deals using old status to new status
			deals_with_old_status = frappe.get_all(
				"CRM Deal",
				filters={"status": old_status},
				fields=["name"]
			)
			
			for deal in deals_with_old_status:
				frappe.db.set_value("CRM Deal", deal.name, "status", new_status)
	
	# Delete old status definitions that are no longer in use
	all_deal_statuses = frappe.get_all("CRM Deal Status", fields=["name"])
	valid_statuses = set(deal_statuses_config.keys())
	
	for status_doc in all_deal_statuses:
		status_name = status_doc.name
		if status_name not in valid_statuses:
			# Check if any deals are still using this status
			deals_count = frappe.db.count("CRM Deal", {"status": status_name})
			if deals_count == 0:
				try:
					frappe.delete_doc("CRM Deal Status", status_name, force=True)
					frappe.log_error(f"Deleted old deal status: {status_name}", "Status Cleanup")
				except Exception as e:
					frappe.log_error(f"Error deleting status {status_name}: {str(e)}", "Status Cleanup Error")

