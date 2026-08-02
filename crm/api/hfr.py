from __future__ import annotations

import json
import time

import frappe
import requests
from frappe import _

try:
	import jwt as pyjwt
except ImportError:
	pyjwt = None

_DOCTYPE = "CRM HFR Settings"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_settings():
	s = frappe.get_single(_DOCTYPE)
	if not s.hfr_enabled:
		frappe.throw(_("HFR integration is not enabled."), frappe.PermissionError)
	return s


def _generate_jwt(s):
	if pyjwt is None:
		frappe.throw(_("PyJWT is not installed. Run: pip install PyJWT"))
	password = s.get_password("hfr_password") or ""
	expiry = int(s.hfr_jwt_expiry or 20000)
	payload = {"key": s.hfr_username, "exp": int(time.time()) + expiry}
	return pyjwt.encode(payload, password, algorithm="HS256")


def _hfr_request(url, params):
	s = _get_settings()
	token = _generate_jwt(s)
	try:
		resp = requests.get(
			url,
			json=params,
			headers={
				"Authorization": "Bearer %s" % token,
				"Content-Type": "application/json",
			},
			timeout=30,
		)
		resp.raise_for_status()
	except requests.exceptions.Timeout:
		frappe.throw(_("HFR request timed out. Please try again."))
	except requests.exceptions.RequestException as exc:
		frappe.throw(_("HFR request failed: %s") % str(exc))
	return resp.json()


def _build_hfr_url(s):
	return "%s%s" % (s.hfr_url.rstrip("/"), s.hfr_fetch_path)


def _normalise_facility_list(data):
	"""Extract a list of facility dicts from varied HFR response shapes."""
	msg = data.get("message") or data.get("data") or []
	if isinstance(msg, dict):
		# Some endpoints wrap in {facilities: [...]}
		msg = msg.get("facilities") or msg.get("data") or [msg]
	if not isinstance(msg, list):
		msg = []
	return msg


def _map_facility_to_org_fields(f):
	"""Map a raw HFR facility dict to CRM Organization fieldnames."""
	county = f.get("county") or ""
	territory = None
	if county:
		territory = frappe.db.exists("CRM Territory", {"territory_name": county})

	return {
		"organization_name": f.get("facility_name"),
		"hfr_facility_id": f.get("facility_fid") or f.get("hie_id"),
		"mfl_code": f.get("facility_mfl") or f.get("facility_code"),
		"facility_type": f.get("facility_type"),
		"facility_category": f.get("category"),
		"facility_level": f.get("kephl_level"),
		"facility_owner": f.get("facility_owner"),
		"facility_owner_type": f.get("facility_owner_type"),
		"regulatory_body": f.get("regulatory_body"),
		"registration_number": f.get("registration_number"),
		"board_registration_number": f.get("board_registration_number"),
		"operational_status": f.get("operational_status"),
		"kra_pin": f.get("kra_pin"),
		"hfr_county": county,
		"hfr_sub_county": f.get("sub_county"),
		"hfr_constituency": f.get("constituency"),
		"hfr_ward": f.get("ward"),
		"latitude": f.get("latitude"),
		"longitude": f.get("longitude"),
		"license_number": f.get("license_number"),
		"license_type": f.get("license_type"),
		"license_expiry": f.get("license_expiry"),
		"facility_standing": f.get("standing"),
		"open_whole_day": int(bool(f.get("open_whole_day", 0))),
		"open_weekends": int(bool(f.get("open_weekends", 0))),
		"open_public_holidays": int(bool(f.get("open_public_holiday", 0))),
		"open_late_night": int(bool(f.get("open_late_night", 0))),
		"number_of_beds": f.get("number_of_beds"),
		"number_of_cots": f.get("number_of_cots"),
		"territory": territory,
		"hfr_sync_status": "HFR Verified",
	}


# ---------------------------------------------------------------------------
# Public whitelisted API
# ---------------------------------------------------------------------------


@frappe.whitelist()
def search_facility(query, search_by="mfl_code"):
	"""Return a list of HFR facility candidates matching query.

	The UAT HIE endpoint supports lookup by: mfl_code, registration_number,
	license_number, facility_fid. Free-text name search is not supported.
	"""
	param_map = {
		"mfl_code": "facility-code",
		"registration_number": "registration-number",
		"license_number": "license-number",
		"facility_fid": "facility-fid",
	}
	if search_by not in param_map:
		frappe.throw(_("Invalid search_by value."))

	s = _get_settings()
	url = _build_hfr_url(s)
	data = _hfr_request(url, {param_map[search_by]: query})
	facilities = _normalise_facility_list(data)

	return [
		{
			"fid": f.get("facility_fid") or f.get("hie_id"),
			"name": f.get("facility_name"),
			"mfl_code": f.get("facility_mfl") or f.get("facility_code"),
			"level": f.get("kephl_level"),
			"category": f.get("category"),
			"county": f.get("county"),
			"owner_type": f.get("facility_owner_type"),
			"operational_status": f.get("operational_status"),
		}
		for f in facilities
		if f.get("facility_fid") or f.get("hie_id")
	]


@frappe.whitelist()
def get_facility_detail(fid):
	"""Return HFR fields keyed to CRM Organization fieldnames for a given FID."""
	s = _get_settings()
	url = _build_hfr_url(s)
	data = _hfr_request(url, {"facility-fid": fid})
	facilities = _normalise_facility_list(data)
	f = facilities[0] if facilities else {}
	return _map_facility_to_org_fields(f)


@frappe.whitelist()
def resync_facility_row(doctype, docname, row_name):
	"""Fetch latest HFR data for a facility child row and overwrite all HFR-managed fields."""
	_allowed = ("CRM Organization", "CRM Lead", "CRM Deal")
	if doctype not in _allowed:
		frappe.throw(_("Invalid doctype."))

	parent = frappe.get_doc(doctype, docname)
	row = next((r for r in (parent.facilities or []) if r.name == row_name), None)
	if not row:
		frappe.throw(_("Facility row not found."))
	if not row.hfr_facility_id:
		frappe.throw(_("This facility row has no HFR Facility ID."))

	hfr_data = get_facility_detail(row.hfr_facility_id)

	_field_map = {
		"facility_name": "organization_name",
		"mfl_code": "mfl_code",
		"facility_type": "facility_type",
		"facility_category": "facility_category",
		"facility_level": "facility_level",
		"facility_owner": "facility_owner",
		"facility_owner_type": "facility_owner_type",
		"regulatory_body": "regulatory_body",
		"registration_number": "registration_number",
		"operational_status": "operational_status",
		"hfr_county": "hfr_county",
		"hfr_sub_county": "hfr_sub_county",
		"hfr_ward": "hfr_ward",
		"latitude": "latitude",
		"longitude": "longitude",
		"license_number": "license_number",
		"license_expiry": "license_expiry",
		"facility_standing": "facility_standing",
		"number_of_beds": "number_of_beds",
	}
	for row_field, data_field in _field_map.items():
		val = hfr_data.get(data_field)
		if val is not None:
			row.set(row_field, val)

	row.hfr_sync_status = "HFR Verified"
	row.hfr_last_synced = frappe.utils.now_datetime()
	parent.save()

	return {"updated_row": row_name, "hfr_facility_id": row.hfr_facility_id}


@frappe.whitelist()
def get_hfr_settings():
	"""Return non-sensitive HFR settings for the frontend."""
	s = frappe.get_single(_DOCTYPE)
	return {
		"hfr_enabled": s.hfr_enabled,
		"hfr_url": s.hfr_url,
		"hfr_fetch_path": s.hfr_fetch_path,
		"hfr_username": s.hfr_username,
		"hfr_jwt_expiry": s.hfr_jwt_expiry,
	}


@frappe.whitelist(methods=["POST"])
def update_hfr_settings(settings):
	"""Persist HFR settings. Password only updated when provided."""
	if isinstance(settings, str):
		settings = json.loads(settings)

	s = frappe.get_single(_DOCTYPE)
	s.hfr_enabled = settings.get("hfr_enabled", 0)
	s.hfr_url = settings.get("hfr_url") or ""
	s.hfr_fetch_path = settings.get("hfr_fetch_path") or "/v1/hfr/facilities"
	s.hfr_username = settings.get("hfr_username") or ""
	s.hfr_jwt_expiry = int(settings.get("hfr_jwt_expiry") or 20000)
	if settings.get("hfr_password"):
		s.hfr_password = settings["hfr_password"]
	s.save()
	return {"success": True}
