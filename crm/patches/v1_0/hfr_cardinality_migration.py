import frappe


def execute():
	_migrate_org_facilities()
	_migrate_lead_facilities()


def _migrate_org_facilities():
	if not frappe.db.has_column("CRM Organization", "hfr_facility_id"):
		return

	orgs = frappe.db.sql(
		"SELECT name, hfr_facility_id, mfl_code, facility_type, facility_category,"
		" facility_level, facility_owner, facility_owner_type, regulatory_body,"
		" registration_number, operational_status, hfr_county, hfr_sub_county,"
		" hfr_ward, latitude, longitude, license_number, license_expiry,"
		" facility_standing, number_of_beds, hfr_sync_status, hfr_last_synced"
		" FROM `tabCRM Organization`"
		" WHERE hfr_facility_id IS NOT NULL AND hfr_facility_id != ''",
		as_dict=True,
	)
	for org in orgs:
		if frappe.db.exists(
			"CRM Org Facility",
			{"parent": org.name, "hfr_facility_id": org.hfr_facility_id},
		):
			continue
		frappe.get_doc(
			{
				"doctype": "CRM Org Facility",
				"parent": org.name,
				"parenttype": "CRM Organization",
				"parentfield": "facilities",
				"hfr_facility_id": org.hfr_facility_id,
				"facility_name": org.name,
				"mfl_code": org.mfl_code,
				"facility_type": org.facility_type,
				"facility_category": org.facility_category,
				"facility_level": org.facility_level,
				"facility_owner": org.facility_owner,
				"facility_owner_type": org.facility_owner_type,
				"regulatory_body": org.regulatory_body,
				"registration_number": org.registration_number,
				"operational_status": org.operational_status,
				"hfr_county": org.hfr_county,
				"hfr_sub_county": org.hfr_sub_county,
				"hfr_ward": org.hfr_ward,
				"latitude": org.latitude,
				"longitude": org.longitude,
				"license_number": org.license_number,
				"license_expiry": org.license_expiry,
				"facility_standing": org.facility_standing,
				"number_of_beds": org.number_of_beds,
				"hfr_sync_status": org.hfr_sync_status or "HFR Verified",
				"hfr_last_synced": org.hfr_last_synced,
			}
		).insert(ignore_permissions=True)  # SYSTEM-INTERNAL

	frappe.db.commit()


def _migrate_lead_facilities():
	if not frappe.db.has_column("CRM Lead", "hfr_facility_id"):
		return

	leads = frappe.db.sql(
		"SELECT name, hfr_facility_id, mfl_code, facility_level,"
		" facility_owner_type, hfr_sync_status"
		" FROM `tabCRM Lead`"
		" WHERE hfr_facility_id IS NOT NULL AND hfr_facility_id != ''",
		as_dict=True,
	)
	for lead in leads:
		if frappe.db.exists(
			"CRM Lead Facility",
			{"parent": lead.name, "hfr_facility_id": lead.hfr_facility_id},
		):
			continue
		frappe.get_doc(
			{
				"doctype": "CRM Lead Facility",
				"parent": lead.name,
				"parenttype": "CRM Lead",
				"parentfield": "facilities",
				"hfr_facility_id": lead.hfr_facility_id,
				"facility_name": lead.hfr_facility_id,
				"mfl_code": lead.mfl_code,
				"facility_level": lead.facility_level,
				"facility_owner_type": lead.facility_owner_type,
				"hfr_sync_status": lead.hfr_sync_status or "HFR Verified",
			}
		).insert(ignore_permissions=True)  # SYSTEM-INTERNAL

	frappe.db.commit()
