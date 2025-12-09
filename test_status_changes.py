"""
Script to test and verify CRM status changes
Run this with: bench --site [your-site] console
Then execute: exec(open('apps/crm/test_status_changes.py').read())
"""

import frappe

def check_lead_statuses():
	"""Check current lead statuses"""
	print("\n=== LEAD STATUSES ===")
	lead_statuses = frappe.get_all(
		"CRM Lead Status",
		fields=["name", "color", "position"],
		order_by="position asc"
	)
	
	expected = ["New", "Qualified", "Unqualified", "Junk"]
	
	for status in lead_statuses:
		marker = "✓" if status.name in expected else "✗"
		print(f"{marker} {status.name:15} | Color: {status.color:10} | Position: {status.position}")
	
	print(f"\nTotal: {len(lead_statuses)} statuses")
	print(f"Expected: {len(expected)} statuses")
	
	missing = set(expected) - {s.name for s in lead_statuses}
	if missing:
		print(f"⚠ Missing statuses: {missing}")
	
	extra = {s.name for s in lead_statuses} - set(expected)
	if extra:
		print(f"⚠ Extra statuses: {extra}")


def check_deal_statuses():
	"""Check current deal statuses"""
	print("\n=== DEAL STATUSES ===")
	deal_statuses = frappe.get_all(
		"CRM Deal Status",
		fields=["name", "color", "type", "probability", "position"],
		order_by="position asc"
	)
	
	expected = ["Qualification", "Quotation", "Followup", "Ready to Close", "Won", "Lost", "Hold"]
	
	for status in deal_statuses:
		marker = "✓" if status.name in expected else "✗"
		print(f"{marker} {status.name:20} | Color: {status.color:10} | Type: {status.type:10} | Prob: {status.probability:3}% | Pos: {status.position}")
	
	print(f"\nTotal: {len(deal_statuses)} statuses")
	print(f"Expected: {len(expected)} statuses")
	
	missing = set(expected) - {s.name for s in deal_statuses}
	if missing:
		print(f"⚠ Missing statuses: {missing}")
	
	extra = {s.name for s in deal_statuses} - set(expected)
	if extra:
		print(f"⚠ Extra statuses: {extra}")


def check_leads_with_old_statuses():
	"""Check if any leads are using old statuses"""
	print("\n=== LEADS WITH OLD STATUSES ===")
	old_statuses = ["Contacted", "Nurture"]
	
	for old_status in old_statuses:
		count = frappe.db.count("CRM Lead", {"status": old_status})
		if count > 0:
			print(f"⚠ {count} leads still using '{old_status}' status")
		else:
			print(f"✓ No leads using '{old_status}' status")


def check_deals_with_old_statuses():
	"""Check if any deals are using old statuses"""
	print("\n=== DEALS WITH OLD STATUSES ===")
	old_statuses = ["Demo/Making", "Negotiation", "Proposal/Quotation"]
	
	for old_status in old_statuses:
		count = frappe.db.count("CRM Deal", {"status": old_status})
		if count > 0:
			print(f"⚠ {count} deals still using '{old_status}' status")
		else:
			print(f"✓ No deals using '{old_status}' status")


if __name__ == "__main__" or __name__ == "__builtin__":
	check_lead_statuses()
	check_deal_statuses()
	check_leads_with_old_statuses()
	check_deals_with_old_statuses()
	print("\n✅ Status check complete!")

