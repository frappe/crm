from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Any

import frappe
from frappe import _


SYNONYM_MAP = {
	"first_name": ["first name", "firstname", "first", "fname", "given name", "first_name"],
	"last_name": ["last name", "lastname", "last", "lname", "surname", "family name", "last_name"],
	"id": ["id", "lead id", "crm lead id", "lead_id", "record id"],
	"status": ["status", "lead status", "lead_status", "stage"],
	"email": ["email", "email address", "email_id", "email id", "mail", "e-mail"],
	"mobile_no": [
		"mobile number",
		"mobile",
		"mobile no",
		"mobile_no",
		"phone",
		"phone number",
		"phone no",
		"contact number",
		"cell",
		"tel",
	],
	"organization": [
		"organization name",
		"organization",
		"company name",
		"company",
		"org",
		"org name",
		"account",
		"business",
		"organization_name",
	],
	"website": ["website", "company website", "org website", "url", "web", "site", "domain"],
	"city": ["city", "town", "locality"],
	"state": ["state", "province", "region"],
	"country": ["country", "nation"],
}


def _clean_str(val: Any) -> str:
	if val is None:
		return ""
	s = str(val).strip()
	return "" if s.lower() in ("none", "null", "nan") else s


def _extract_file_bytes(
	file_url: str | None = None,
	file_content: str | None = None,
	file_name: str | None = None,
) -> tuple[bytes, str]:
	"""Extract file bytes and name from uploaded file, url, or base64 content."""
	# 1. From request.files if sent via multipart/form-data
	if hasattr(frappe, "request") and frappe.request and getattr(frappe.request, "files", None):
		uploaded = frappe.request.files.get("file")
		if uploaded:
			return uploaded.stream.read(), getattr(uploaded, "filename", file_name or "upload.csv")

	# 2. From file_url in Frappe files
	if file_url:
		file_url = file_url.strip()
		file_doc = frappe.db.get_value("File", {"file_url": file_url}, ["name", "file_name"], as_dict=True)
		fname = file_doc.file_name if file_doc else file_url.split("/")[-1]

		if file_url.startswith("/files/"):
			file_path = frappe.get_site_path("public", file_url.lstrip("/"))
		elif file_url.startswith("/private/files/"):
			file_path = frappe.get_site_path(file_url.lstrip("/"))
		else:
			file_path = frappe.get_site_path("public", "files", file_url.lstrip("/"))

		import os
		if os.path.exists(file_path):
			with open(file_path, "rb") as f:
				return f.read(), file_name or fname

		# Fallback to Frappe get_doc
		if file_doc:
			doc = frappe.get_doc("File", file_doc.name)
			return doc.get_content(), file_name or doc.file_name

	# 3. From base64 file_content
	if file_content:
		import base64
		if "," in file_content:
			file_content = file_content.split(",", 1)[1]
		return base64.b64decode(file_content), file_name or "upload.xlsx"

	frappe.throw(_("No file provided for import"))


def _parse_tabular_data(content: bytes, file_name: str) -> tuple[list[str], list[dict[str, str]]]:
	"""Parse CSV, XLSX, or XLS into headers and list of dict rows."""
	file_lower = (file_name or "").lower()

	if file_lower.endswith(".xlsx"):
		import openpyxl
		wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
		sheet = wb.active
		all_rows = list(sheet.iter_rows(values_only=True))
		if not all_rows:
			return [], []

		headers = [_clean_str(h) for h in all_rows[0]]
		# Filter out trailing empty header columns
		while headers and not headers[-1]:
			headers.pop()

		rows = []
		for r in all_rows[1:]:
			if not any(r):
				continue
			row_dict = {}
			has_val = False
			for idx, h in enumerate(headers):
				if not h:
					continue
				val = r[idx] if idx < len(r) else ""
				val_str = _clean_str(val)
				if val_str:
					has_val = True
				row_dict[h] = val_str
			if has_val:
				rows.append(row_dict)
		return headers, rows

	if file_lower.endswith(".xls"):
		import xlrd
		wb = xlrd.open_workbook(file_contents=content)
		sheet = wb.sheet_by_index(0)
		if sheet.nrows == 0:
			return [], []

		headers = [_clean_str(sheet.cell_value(0, col)) for col in range(sheet.ncols)]
		while headers and not headers[-1]:
			headers.pop()

		rows = []
		for row_idx in range(1, sheet.nrows):
			row_dict = {}
			has_val = False
			for col_idx, h in enumerate(headers):
				if not h:
					continue
				val = sheet.cell_value(row_idx, col_idx)
				val_str = _clean_str(val)
				if val_str:
					has_val = True
				row_dict[h] = val_str
			if has_val:
				rows.append(row_dict)
		return headers, rows

	# Default: CSV
	try:
		text = content.decode("utf-8-sig")
	except UnicodeDecodeError:
		try:
			text = content.decode("latin-1")
		except UnicodeDecodeError:
			text = content.decode("cp1252", errors="ignore")

	# Sniff delimiter
	first_lines = "\n".join(text.splitlines()[:5])
	try:
		sniffer = csv.Sniffer()
		dialect = sniffer.sniff(first_lines, delimiters=",\t;|")
		delimiter = dialect.delimiter
	except Exception:
		delimiter = ","

	reader = csv.reader(io.StringIO(text), delimiter=delimiter)
	all_rows = list(reader)
	if not all_rows:
		return [], []

	headers = [_clean_str(h) for h in all_rows[0]]
	while headers and not headers[-1]:
		headers.pop()

	rows = []
	for r in all_rows[1:]:
		if not any(r):
			continue
		row_dict = {}
		has_val = False
		for idx, h in enumerate(headers):
			if not h:
				continue
			val = r[idx] if idx < len(r) else ""
			val_str = _clean_str(val)
			if val_str:
				has_val = True
			row_dict[h] = val_str
		if has_val:
			rows.append(row_dict)

	return headers, rows


def _suggest_mappings(headers: list[str]) -> dict[str, str]:
	"""Map CRM destination fields to uploaded file headers automatically."""
	suggested = {}
	lower_headers = {h.lower().strip(): h for h in headers if h}

	for field, synonyms in SYNONYM_MAP.items():
		matched = None
		# 1. Exact match on synonym
		for syn in synonyms:
			if syn in lower_headers:
				matched = lower_headers[syn]
				break

		# 2. Substring match
		if not matched:
			for syn in synonyms:
				for h_lower, orig in lower_headers.items():
					if syn == h_lower or syn in h_lower:
						matched = orig
						break
				if matched:
					break

		if matched:
			suggested[field] = matched

	return suggested


@frappe.whitelist()
def parse_import_file(
	file_url: str | None = None,
	file_content: str | None = None,
	file_name: str | None = None,
) -> dict[str, Any]:
	"""Parse uploaded file and return headers, sample rows, and suggested mappings."""
	content, fname = _extract_file_bytes(file_url, file_content, file_name)
	if file_name:
		fname = file_name

	headers, rows = _parse_tabular_data(content, fname)
	if not headers:
		frappe.throw(_("The file appears to be empty or has no header row."))

	token = str(uuid.uuid4())
	# Cache parsed rows for 2 hours to avoid re-uploading large data
	frappe.cache().set_value(f"import_data_rows_{token}", rows, expires_in_sec=7200)

	suggested = _suggest_mappings(headers)

	return {
		"file_token": token,
		"file_name": fname,
		"total_rows": len(rows),
		"columns": headers,
		"sample_rows": rows[:5],
		"suggested_mapping": suggested,
	}


def _normalize_mapping(column_mapping: Any) -> dict[str, str]:
	"""Ensure column_mapping is a dict of { crm_field: file_column }."""
	if not column_mapping:
		return {}

	if isinstance(column_mapping, str):
		try:
			column_mapping = json.loads(column_mapping)
		except Exception:
			return {}

	if not isinstance(column_mapping, dict):
		return {}

	crm_fields = list(SYNONYM_MAP.keys())
	normalized = {}

	# Check if incoming is { crm_field: file_col } or { file_col: crm_field }
	is_target_keyed = any(k in crm_fields for k in column_mapping.keys())
	if is_target_keyed:
		for k, v in column_mapping.items():
			if v and str(v).strip().lower() not in ("none", "null", "skip"):
				normalized[k] = str(v).strip()
	else:
		for file_col, crm_target in column_mapping.items():
			if crm_target and str(crm_target).strip().lower() not in ("none", "null", "skip"):
				normalized[str(crm_target).strip()] = str(file_col).strip()

	return normalized


def _get_rows(file_token: str | None = None, rows: Any = None) -> list[dict[str, str]]:
	if file_token:
		cached = frappe.cache().get_value(f"import_data_rows_{file_token}")
		if cached:
			return cached
	if rows:
		if isinstance(rows, str):
			try:
				return json.loads(rows)
			except Exception:
				pass
		elif isinstance(rows, list):
			return rows
	frappe.throw(_("No import rows found. Please upload the file again."))


@frappe.whitelist()
def preview_import(
	file_token: str | None = None,
	rows: Any = None,
	column_mapping: Any = None,
) -> dict[str, Any]:
	"""Validate mappings, calculate summary metrics and preview mapped rows."""
	rows_data = _get_rows(file_token, rows)
	mapping = _normalize_mapping(column_mapping)

	total_rows = len(rows_data)
	valid_rows = []
	missing_values_count = 0
	unique_orgs = set()

	for r in rows_data:
		first_name = _clean_str(r.get(mapping.get("first_name", "")))
		last_name = _clean_str(r.get(mapping.get("last_name", "")))
		email = _clean_str(r.get(mapping.get("email", "")))
		mobile_no = _clean_str(r.get(mapping.get("mobile_no", "")))
		org_val = _clean_str(r.get(mapping.get("organization", "")))
		website = _clean_str(r.get(mapping.get("website", "")))
		city = _clean_str(r.get(mapping.get("city", "")))
		state = _clean_str(r.get(mapping.get("state", "")))
		country = _clean_str(r.get(mapping.get("country", "")))
		id_val = _clean_str(r.get(mapping.get("id", "")))

		# Row validity: must have at least a person's name, email, mobile, or org
		if not (first_name or email or mobile_no or org_val):
			continue

		valid_rows.append(r)

		if org_val:
			unique_orgs.add(org_val)

		# Check if optional fields are missing
		optional_fields = [last_name, website, city, state, country, id_val]
		if any(not f for f in optional_fields):
			missing_values_count += 1

	# Check which organizations already exist in the database (case-insensitive)
	existing_orgs = set()
	orgs_to_create = set()

	for org in unique_orgs:
		norm = org.lower().strip()
		found = frappe.db.sql(
			"SELECT name FROM `tabCRM Organization` WHERE LOWER(organization_name) = %s OR LOWER(name) = %s LIMIT 1",
			(norm, norm),
			as_dict=True,
		)
		if found:
			existing_orgs.add(found[0].name)
		else:
			orgs_to_create.add(org)

	# Build mapped preview for the first 5 valid rows
	sample_preview = []
	for r in valid_rows[:5]:
		status_candidate = _clean_str(r.get(mapping.get("status", "")))
		status_final = status_candidate or "New"

		sample_preview.append({
			"first_name": _clean_str(r.get(mapping.get("first_name", ""))),
			"last_name": _clean_str(r.get(mapping.get("last_name", ""))),
			"id": _clean_str(r.get(mapping.get("id", ""))),
			"status": status_final,
			"email": _clean_str(r.get(mapping.get("email", ""))),
			"mobile_no": _clean_str(r.get(mapping.get("mobile_no", ""))),
			"organization": _clean_str(r.get(mapping.get("organization", ""))),
			"website": _clean_str(r.get(mapping.get("website", ""))),
			"city": _clean_str(r.get(mapping.get("city", ""))),
			"state": _clean_str(r.get(mapping.get("state", ""))),
			"country": _clean_str(r.get(mapping.get("country", ""))),
		})

	return {
		"total_rows": total_rows,
		"valid_rows": len(valid_rows),
		"missing_values_count": missing_values_count,
		"orgs_to_create_count": len(orgs_to_create),
		"existing_orgs_count": len(existing_orgs),
		"orgs_to_create": sorted(list(orgs_to_create)),
		"existing_orgs": sorted(list(existing_orgs)),
		"sample_preview": sample_preview,
		"status_default_applied": "status" not in mapping or not mapping["status"],
	}


def _get_or_create_org(org_name: str | None, website: str | None = None, org_cache: dict[str, str] | None = None) -> str | None:
	"""Find existing Organization (case-insensitive) or create new one. Caches in-memory."""
	if not org_name:
		return None

	org_name_clean = org_name.strip()
	if not org_name_clean:
		return None

	key = org_name_clean.lower()

	if org_cache is not None and key in org_cache:
		matched = org_cache[key]
		if website:
			curr_site = frappe.db.get_value("CRM Organization", matched, "website")
			if not curr_site:
				frappe.db.set_value("CRM Organization", matched, "website", website)
		return matched

	# Database lookup (case-insensitive)
	existing = frappe.db.sql(
		"SELECT name, website FROM `tabCRM Organization` WHERE LOWER(organization_name) = %s OR LOWER(name) = %s LIMIT 1",
		(key, key),
		as_dict=True,
	)

	if existing:
		matched_name = existing[0].name
		if website and not existing[0].website:
			frappe.db.set_value("CRM Organization", matched_name, "website", website)
		if org_cache is not None:
			org_cache[key] = matched_name
			org_cache[matched_name.lower()] = matched_name
		return matched_name

	# Create new CRM Organization
	new_org = frappe.new_doc("CRM Organization")
	new_org.owner = frappe.session.user
	new_org.organization_name = org_name_clean
	new_org.status = "Active"
	if website:
		new_org.website = website
	new_org.flags.ignore_permissions = True
	new_org.insert()

	matched_name = new_org.name
	if org_cache is not None:
		org_cache[key] = matched_name
		org_cache[matched_name.lower()] = matched_name
	return matched_name


def _get_or_create_contact(
	first_name: str,
	last_name: str,
	email: str,
	mobile_no: str,
	org_name: str | None,
	status: str | None = None,
	contact_cache: dict[str, str] | None = None,
) -> str:
	"""Find existing Contact by email/mobile or create new Contact linked to Organization."""
	contact_name = None
	email_clean = email.strip() if email else ""
	mobile_clean = mobile_no.strip() if mobile_no else ""

	# 1. In-memory cache lookup
	if contact_cache is not None:
		if email_clean and email_clean.lower() in contact_cache:
			contact_name = contact_cache[email_clean.lower()]
		elif mobile_clean and mobile_clean in contact_cache:
			contact_name = contact_cache[mobile_clean]

	# 2. Database lookup
	if not contact_name and email_clean:
		contact_name = frappe.db.get_value("Contact Email", {"email_id": email_clean}, "parent")
		if not contact_name:
			contact_name = frappe.db.get_value("Contact", {"email_id": email_clean}, "name")

	if not contact_name and mobile_clean:
		contact_name = frappe.db.get_value("Contact Phone", {"phone": mobile_clean}, "parent")
		if not contact_name:
			contact_name = frappe.db.get_value("Contact", {"mobile_no": mobile_clean}, "name")
			if not contact_name:
				contact_name = frappe.db.get_value("Contact", {"phone": mobile_clean}, "name")

	if not contact_name and not email_clean and not mobile_clean and first_name:
		filters = {"first_name": first_name}
		if last_name:
			filters["last_name"] = last_name
		if org_name:
			filters["company_name"] = org_name
		contact_name = frappe.db.get_value("Contact", filters, "name")

	if contact_name:
		# Update existing contact
		contact_doc = frappe.get_doc("Contact", contact_name)
		changed = False
		if not contact_doc.first_name and first_name:
			contact_doc.first_name = first_name
			changed = True
		if not contact_doc.last_name and last_name:
			contact_doc.last_name = last_name
			changed = True
		if org_name and contact_doc.company_name != org_name:
			contact_doc.company_name = org_name
			changed = True

		if org_name:
			has_link = any(
				l.link_doctype == "CRM Organization" and l.link_name == org_name
				for l in contact_doc.links
			)
			if not has_link:
				contact_doc.append("links", {"link_doctype": "CRM Organization", "link_name": org_name})
				changed = True

		if email_clean:
			has_email = any(e.email_id.lower() == email_clean.lower() for e in contact_doc.email_ids)
			if not has_email:
				contact_doc.append("email_ids", {"email_id": email_clean, "is_primary": 1 if not contact_doc.email_ids else 0})
				changed = True
			if not contact_doc.email_id:
				contact_doc.email_id = email_clean
				changed = True

		if mobile_clean:
			has_phone = any(p.phone == mobile_clean for p in contact_doc.phone_nos)
			if not has_phone:
				contact_doc.append("phone_nos", {"phone": mobile_clean, "is_primary_mobile_no": 1 if not contact_doc.phone_nos else 0})
				changed = True
			if not contact_doc.mobile_no:
				contact_doc.mobile_no = mobile_clean
				contact_doc.phone = mobile_clean
				changed = True

		if changed:
			contact_doc.flags.ignore_permissions = True
			contact_doc.save()

		if contact_cache is not None:
			if email_clean:
				contact_cache[email_clean.lower()] = contact_name
			if mobile_clean:
				contact_cache[mobile_clean] = contact_name

		return contact_name

	# Create new contact
	contact_doc = frappe.new_doc("Contact")
	contact_doc.owner = frappe.session.user
	contact_doc.first_name = first_name or (email_clean.split("@")[0] if email_clean else (org_name or "Contact"))
	contact_doc.last_name = last_name or ""
	contact_doc.custom_is_dropped = 0
	if org_name:
		contact_doc.company_name = org_name
		contact_doc.append("links", {"link_doctype": "CRM Organization", "link_name": org_name})

	if email_clean:
		contact_doc.email_id = email_clean
		contact_doc.append("email_ids", {"email_id": email_clean, "is_primary": 1})
	if mobile_clean:
		contact_doc.mobile_no = mobile_clean
		contact_doc.phone = mobile_clean
		contact_doc.append("phone_nos", {"phone": mobile_clean, "is_primary_mobile_no": 1})

	if status and status in ("Passive", "Open", "Replied"):
		contact_doc.status = status

	contact_doc.flags.ignore_permissions = True
	contact_doc.insert()

	contact_name = contact_doc.name
	if contact_cache is not None:
		if email_clean:
			contact_cache[email_clean.lower()] = contact_name
		if mobile_clean:
			contact_cache[mobile_clean] = contact_name

	return contact_name


def _get_or_create_address(
	org_name: str | None,
	contact_name: str | None,
	first_name: str,
	last_name: str,
	city: str,
	state: str,
	country: str,
) -> str | None:
	"""Create Address linked to Organization and Contact if city/state/country provided."""
	if not (city or state or country):
		return None

	# Avoid duplicate addresses for same org/contact
	if org_name:
		existing = frappe.db.sql("""
			SELECT dl.parent FROM `tabDynamic Link` dl
			JOIN `tabAddress` a ON a.name = dl.parent
			WHERE dl.link_doctype = 'CRM Organization' AND dl.link_name = %s
			AND dl.parenttype = 'Address' AND IFNULL(a.city, '') = %s
			LIMIT 1
		""", (org_name, city or ""))
		if existing:
			return existing[0][0]

	title = org_name or f"{first_name or ''} {last_name or ''}".strip() or "Office"
	address_doc = frappe.new_doc("Address")
	address_doc.address_title = title
	address_doc.address_type = "Office"
	address_doc.address_line1 = city or state or (f"{country} Office" if country else "Office Address")
	address_doc.city = city or state or (country.split()[0] if country else "City") or "City"
	address_doc.state = state or ""

	# Check valid Country
	if country and frappe.db.exists("Country", country):
		address_doc.country = country
	else:
		address_doc.country = frappe.db.get_default("country") or "United States"

	if org_name:
		address_doc.append("links", {"link_doctype": "CRM Organization", "link_name": org_name})
	if contact_name:
		address_doc.append("links", {"link_doctype": "Contact", "link_name": contact_name})

	address_doc.flags.ignore_permissions = True
	address_doc.insert()
	return address_doc.name


@frappe.whitelist()
def execute_bulk_import(
	file_token: str | None = None,
	rows: Any = None,
	column_mapping: Any = None,
) -> dict[str, Any]:
	"""Execute row-by-row import creating Contacts and Organizations (NO Leads) with deduplication."""
	rows_data = _get_rows(file_token, rows)
	mapping = _normalize_mapping(column_mapping)

	# Ensure custom fields exist on Contact
	try:
		from crm.api.contact import ensure_contact_custom_fields
		ensure_contact_custom_fields()
	except Exception:
		pass

	imported = 0
	skipped = 0
	errors = []
	results = []
	org_cache = {}
	contact_cache = {}

	# Valid Contact Statuses in CRM
	valid_statuses = {"Passive", "Open", "Replied"}

	# Preload existing organizations into org_cache for faster resolution
	existing_orgs = frappe.db.sql("SELECT name, organization_name FROM `tabCRM Organization`", as_dict=True)
	for o in existing_orgs:
		org_cache[o.name.lower()] = o.name
		if o.organization_name:
			org_cache[o.organization_name.lower()] = o.name

	for row_idx, r in enumerate(rows_data, start=1):
		first_name = _clean_str(r.get(mapping.get("first_name", "")))
		last_name = _clean_str(r.get(mapping.get("last_name", "")))
		email = _clean_str(r.get(mapping.get("email", "")))
		mobile_no = _clean_str(r.get(mapping.get("mobile_no", "")))
		org_val = _clean_str(r.get(mapping.get("organization", "")))
		website = _clean_str(r.get(mapping.get("website", "")))
		city = _clean_str(r.get(mapping.get("city", "")))
		state = _clean_str(r.get(mapping.get("state", "")))
		country = _clean_str(r.get(mapping.get("country", "")))
		raw_status = _clean_str(r.get(mapping.get("status", "")))
		status_val = raw_status if raw_status in valid_statuses else None

		# Blank row check: skip row if completely empty
		if not (first_name or last_name or email or mobile_no or org_val):
			skipped += 1
			continue

		savepoint = f"import_row_{row_idx}"
		try:
			frappe.db.savepoint(savepoint)

			# 1. Organization: create or link existing without duplicate
			org_name = _get_or_create_org(org_val, website=website, org_cache=org_cache)

			# 2. Contact: individual/person record created as CRM Contact and linked to Organization
			contact_name = None
			if first_name or last_name or email or mobile_no or not org_name:
				contact_name = _get_or_create_contact(
					first_name=first_name,
					last_name=last_name,
					email=email,
					mobile_no=mobile_no,
					org_name=org_name,
					status=status_val,
					contact_cache=contact_cache,
				)

			# Ensure contact was created if person info was provided
			if (first_name or last_name or email or mobile_no) and not contact_name:
				display_name = f"{first_name} {last_name}".strip() or org_val or email or f"Row {row_idx}"
				raise ValueError(f"Failed to create Contact for {display_name}")

			# 3. Address (optional): linked to Organization and Contact
			_get_or_create_address(
				org_name=org_name,
				contact_name=contact_name,
				first_name=first_name,
				last_name=last_name,
				city=city,
				state=state,
				country=country,
			)

			# DO NOT CREATE ANY CRM LEAD RECORDS DURING BULK IMPORT
			display_name = f"{first_name} {last_name}".strip() or org_val or email or f"Row {row_idx}"
			results.append({
				"row": row_idx,
				"name": display_name,
				"organization": org_name or org_val or "",
				"email": email or "",
				"contact": contact_name,
			})

			imported += 1

		except Exception as e:
			frappe.db.rollback(save_point=savepoint)
			frappe.log_error(title=f"Bulk Import Error Row {row_idx}", message=frappe.get_traceback())
			errors.append({
				"row": row_idx,
				"name": f"{first_name} {last_name}".strip() or org_val or email or f"Row {row_idx}",
				"message": str(e),
			})

	frappe.db.commit()

	# Emit realtime update so open frontend tabs (Contacts, My Tasks, Orgs) refresh immediately
	try:
		frappe.publish_realtime("crm_tasks_updated", {"imported": imported}, after_commit=True)
	except Exception:
		pass

	return {
		"success": len(errors) == 0,
		"successful_records": imported,
		"total": len(rows_data),
		"imported": imported,
		"skipped": skipped,
		"errors": errors,
		"results": results,
	}


@frappe.whitelist()
def execute_single_import(data: Any) -> dict[str, Any]:
	"""Create a single record, linking or creating Organization, Contact, Lead, and Address."""
	if not data:
		frappe.throw(_("No data provided."))

	if isinstance(data, str):
		try:
			data = json.loads(data)
		except Exception:
			frappe.throw(_("Invalid data payload."))

	first_name = _clean_str(data.get("first_name"))
	last_name = _clean_str(data.get("last_name"))
	email = _clean_str(data.get("email"))
	mobile_no = _clean_str(data.get("mobile_no"))
	org_val = _clean_str(data.get("organization"))
	website = _clean_str(data.get("website"))
	city = _clean_str(data.get("city"))
	state = _clean_str(data.get("state"))
	country = _clean_str(data.get("country"))

	valid_statuses = set(frappe.get_all("CRM Lead Status", pluck="name"))
	if not valid_statuses:
		valid_statuses = {"New", "Contacted", "Qualified", "Nurture", "Unqualified", "Junk"}

	raw_status = _clean_str(data.get("status"))
	status_val = raw_status if raw_status in valid_statuses else "New"

	if not (first_name or org_val or email):
		frappe.throw(_("At least a First Name, Organization Name, or Email is required."))

	try:
		# 1. Organization
		org_name = _get_or_create_org(org_val, website=website)

		# 2. Contact
		contact_name = _get_or_create_contact(
			first_name=first_name,
			last_name=last_name,
			email=email,
			mobile_no=mobile_no,
			org_name=org_name,
		)

		# 3. Address (optional) - NO CRM Leads are created during import
		_get_or_create_address(
			org_name=org_name,
			contact_name=contact_name,
			first_name=first_name,
			last_name=last_name,
			city=city,
			state=state,
			country=country,
		)

		frappe.db.commit()

		return {
			"success": True,
			"contact": contact_name,
			"organization": org_name,
		}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(title="Single Import Error", message=frappe.get_traceback())
		frappe.throw(str(e))
