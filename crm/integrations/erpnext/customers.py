"""Organization-owned ERPNext customer identities and reconciliation."""

import hashlib
import json
from urllib.parse import urlsplit, urlunsplit

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, get_url, now_datetime

ERP_API = "erpnext.crm.frappe_crm_api."
AUDIT = "CRM Customer Sync"
BATCH_SIZE = 100


def _mapping_write_allowed(doc):
	return id(doc) in (frappe.flags.get("erpnext_customer_identity_writes") or set())


def _save_mapping(doc):
	previous = frappe.flags.get("erpnext_customer_identity_writes")
	frappe.flags.erpnext_customer_identity_writes = (previous or set()) | {id(doc)}
	try:
		doc.save()
	finally:
		frappe.flags.erpnext_customer_identity_writes = previous


class CustomerMappingConflict(frappe.ValidationError):
	pass


def _conflict(message):
	raise CustomerMappingConflict(message)


def _site(url):
	try:
		value = (url or "").strip()
		parts = urlsplit(value)
		if (
			parts.scheme.lower() not in ("http", "https")
			or not parts.hostname
			or parts.username is not None
			or parts.password is not None
			or parts.query
			or parts.fragment
			or "\\" in value
			or any(character.isspace() for character in value)
		):
			raise ValueError
		host = parts.hostname.encode("idna").decode("ascii").lower()
		if ":" in host:
			host = f"[{host}]"
		port = parts.port
		if port and (parts.scheme.lower(), port) not in (("http", 80), ("https", 443)):
			host = f"{host}:{port}"
		result = urlunsplit((parts.scheme.lower(), host, parts.path.rstrip("/"), "", ""))
		if len(result) > 255:
			raise ValueError
		return result
	except (ValueError, UnicodeError):
		frappe.throw(_("Enter an HTTP or HTTPS site URL without credentials, query or fragment."))


def _crm_site():
	return _site(get_url(allow_header_override=False))


def _settings():
	settings = frappe.get_single("ERPNext CRM Settings")
	if not settings.enabled:
		frappe.throw(_("Enable the ERPNext integration first."))
	return settings


def _source_site(settings):
	return _site(settings.erpnext_site_url) if settings.is_erpnext_in_different_site else _crm_site()


def _erp(method, args=None, *, write=False, settings=None):
	settings = settings or _settings()
	args = args or {}
	if not settings.is_erpnext_in_different_site:
		return frappe.get_attr(ERP_API + method)(**args)
	from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_erpnext_site_client

	client = get_erpnext_site_client(settings)
	if write:
		if method == "create_customer":
			# FrappeClient form-encodes dictionaries. The existing Customer endpoint
			# accepts flat form fields; a JSON string cannot satisfy its typed dict argument.
			args = args["customer_data"]
		return client.post_api(ERP_API + method, args)
	return client.get_api(ERP_API + method, args)


def _can_manage():
	return frappe.has_permission("ERPNext CRM Settings", "write")


def _customer(name, settings, include_related=True):
	detail = _erp(
		"get_customer_for_crm", {"customer": name, "include_related": include_related}, settings=settings
	)
	return {
		**detail["customer"],
		"contacts": detail.get("contacts", []),
		"addresses": detail.get("addresses", []),
	}


def _require_manage():
	frappe.get_single("ERPNext CRM Settings").check_permission("write")
	frappe.has_permission("CRM Organization", "read", throw=True)


def _audit_name(customer, settings, source_site=None):
	return hashlib.sha256(f"{source_site or _source_site(settings)}\n{customer}".encode()).hexdigest()


def _audit(customer, settings):
	name = _audit_name(customer["name"], settings)
	if frappe.db.exists(AUDIT, name):
		return frappe.get_doc(AUDIT, name)
	# A source rename keeps the reciprocal Organization identity. Carry the audit
	# baseline and ignore policy only after the source proves the old ID is gone.
	if (
		customer.get("crm_organization")
		and customer.get("crm_site") == _crm_site()
		and frappe.db.exists("CRM Organization", customer["crm_organization"])
		and frappe.has_permission("CRM Organization", "write", customer["crm_organization"])
	):
		organization = frappe.get_doc("CRM Organization", customer["crm_organization"])
		previous_customer = organization.get("erpnext_customer")
		if (
			previous_customer
			and previous_customer != customer["name"]
			and organization.get("erpnext_site") == _source_site(settings)
			and frappe.db.exists(AUDIT, _audit_name(previous_customer, settings))
		):
			organization.check_permission("write")
			proof = _erp(
				"resolve_customer_for_crm",
				{"customer": previous_customer, "organization": organization.name, "crm_site": _crm_site()},
				settings=settings,
			)
			if (
				proof
				and proof.get("renamed_from") == previous_customer
				and proof["customer"]["name"] == customer["name"]
			):
				_backfill_deal_references(organization, customer["name"], previous_customer)
				organization.erpnext_customer = customer["name"]
				_save_mapping(organization)
				previous = frappe.get_doc(AUDIT, _audit_name(previous_customer, settings))
				return _rename_audit(previous, customer["name"], name)
	return frappe.get_doc(
		{
			"doctype": AUDIT,
			"sync_key": name,
			"customer": customer["name"],
			"erpnext_site": _source_site(settings),
			"status": "Pending",
			"direction": "ERPNext to CRM",
		}
	)


def _rename_audit(audit, customer, name):
	old_name = audit.name
	audit.customer = customer
	audit.sync_key = name
	audit.save(ignore_permissions=True)
	frappe.rename_doc(AUDIT, old_name, name, force=True, ignore_permissions=True)
	return frappe.get_doc(AUDIT, name)


def _save_audit(audit, customer, status, message="", rule=None, organization=None):
	audit.customer_name = customer.get("customer_name")
	audit.customer_type = customer.get("customer_type")
	audit.source_modified = customer.get("modified")
	audit.last_attempt = now_datetime()
	audit.status = status
	audit.message = message
	if rule:
		audit.match_rule = rule
	if organization:
		audit.organization = organization
	if status == "Synced":
		audit.last_success = audit.last_attempt
	audit.save(ignore_permissions=True)
	return audit


def _normalized_name(value):
	return " ".join((value or "").split()).casefold()


def _organization_names():
	names = {}
	start = 0
	while True:
		rows = frappe.get_list(
			"CRM Organization",
			fields=["name", "organization_name"],
			order_by="name asc",
			limit_start=start,
			limit_page_length=BATCH_SIZE,
		)
		for row in rows:
			names.setdefault(_normalized_name(row.organization_name), []).append(row.name)
		if len(rows) < BATCH_SIZE:
			return names
		start += BATCH_SIZE


def _organization_for(customer, settings, legacy=None, name_index=None):
	crm_site = _crm_site()
	if customer.get("crm_site") and _site(customer["crm_site"]) != crm_site:
		_conflict(_("This Customer is linked to another CRM site."))
	if legacy and legacy.get("conflict"):
		_conflict(legacy["conflict"])
	linked = frappe.get_list(
		"CRM Organization",
		filters={"erpnext_customer": customer["name"]},
		or_filters=[["erpnext_site", "=", _source_site(settings)], ["erpnext_site", "is", "not set"]],
		fields=["name", "erpnext_site"],
		limit_page_length=2,
	)
	if len(linked) > 1:
		_conflict(_("Several organizations reference this Customer."))
	references = {row.name for row in linked}
	if customer.get("crm_organization"):
		references.add(customer["crm_organization"])
	if legacy:
		references.update(legacy.get("organizations") or [])
	if len(references) > 1:
		_conflict(_("The existing Customer and Deal references identify different organizations."))
	if references:
		name = next(iter(references))
		if frappe.db.exists(
			AUDIT, {"organization": name, "erpnext_site": _source_site(settings), "status": "Unlinked"}
		):
			_conflict(_("Complete the pending Customer unlink before reconciling this organization."))
		if not frappe.db.exists("CRM Organization", name):
			_conflict(_("The linked CRM Organization no longer exists."))
		return frappe.get_doc("CRM Organization", name), "Legacy Deal" if legacy and legacy.get(
			"organizations"
		) else "Existing mapping"
	if customer.get("tax_id"):
		matches = frappe.get_list(
			"CRM Organization", filters={"tax_id": customer["tax_id"]}, fields=["name"], limit_page_length=2
		)
		if len(matches) > 1:
			_conflict(_("Several organizations have this Tax ID. Choose an organization explicitly."))
		if matches:
			return frappe.get_doc("CRM Organization", matches[0].name), "Tax ID"
	# Name matching is a one-time reconciliation hint; the persisted IDs own all subsequent resolution.
	name_index = name_index if name_index is not None else _organization_names()
	matches = name_index.get(_normalized_name(customer.get("customer_name")), [])
	if len(matches) > 1:
		_conflict(_("Several organizations have this name. Choose an organization explicitly."))
	return (
		(frappe.get_doc("CRM Organization", matches[0]), "Exact name")
		if matches
		else (None, "Created organization")
	)


def _shared_values(customer):
	values = {"organization_name": customer["customer_name"]}
	for field in ("website", "tax_id"):
		if field in customer:
			values[field] = customer[field] or ""
	for source, target, doctype in (
		("industry", "industry", "CRM Industry"),
		("territory", "territory", "CRM Territory"),
		("default_currency", "currency", "Currency"),
	):
		value = customer.get(source)
		if source in customer and not value:
			values[target] = None
		if value and frappe.db.exists(doctype, value):
			values[target] = value
	return values


def _prepare_organization(customer, organization, audit, settings, force=False):
	values = _shared_values(customer)
	renamed_from = None
	if organization:
		organization.check_permission("write")
		if organization.get("erpnext_customer") and organization.erpnext_customer != customer["name"]:
			proof = _erp(
				"resolve_customer_for_crm",
				{
					"customer": organization.erpnext_customer,
					"organization": organization.name,
					"crm_site": _crm_site(),
				},
				settings=settings,
			)
			if (
				not proof
				or proof.get("renamed_from") != organization.erpnext_customer
				or proof["customer"]["name"] != customer["name"]
			):
				_conflict(_("This organization is linked to another ERPNext Customer."))
			renamed_from = organization.erpnext_customer
		if organization.get("erpnext_site") and _site(organization.erpnext_site) != _source_site(settings):
			_conflict(_("This organization is linked to another ERPNext site."))
		previous = json.loads(audit.last_synced_values or "{}")
		for field, value in values.items():
			current = organization.get(field) or ""
			baseline = previous.get(field) or ""
			if (
				not force
				and (field in previous or current)
				and current != (value or "")
				and current != baseline
			):
				_conflict(
					_("The CRM value for {0} differs from ERPNext. Review before synchronizing.").format(
						frappe.get_meta("CRM Organization").get_label(field)
					)
				)
	else:
		frappe.has_permission("CRM Organization", "create", throw=True)
		organization = frappe.new_doc("CRM Organization")
	organization.update(values)
	organization.erpnext_customer = customer["name"]
	organization.erpnext_site = _source_site(settings)
	return organization, values, renamed_from


def _link_organization(doc, organization):
	if not any(
		row.link_doctype == "CRM Organization" and row.link_name == organization.name for row in doc.links
	):
		doc.append("links", {"link_doctype": "CRM Organization", "link_name": organization.name})


def _related_values(doc, remote, fields, force):
	values = {field: remote.get(field) or "" for field in fields if field in remote}
	children = {
		"email_ids": ("email_id", "is_primary"),
		"phone_nos": ("phone", "is_primary_phone", "is_primary_mobile_no"),
	}
	if doc.doctype == "Contact":
		for field, keys in children.items():
			if field in remote:
				values[field] = [{key: item.get(key) for key in keys} for item in remote[field] or []]
	previous = json.loads(doc.get("erpnext_synced_values") or "{}")
	for field, value in values.items():
		current = doc.get(field) or ""
		if field in children:
			current = [{key: row.get(key) for key in children[field]} for row in doc.get(field) or []]
		baseline = previous.get(field) or ([] if field in children else "")
		if (
			not force
			and not doc.is_new()
			and (field in previous or current)
			and current != value
			and current != baseline
		):
			_conflict(
				_("The local {0} value for {1} has changed. Review before synchronizing.").format(
					doc.doctype, field
				)
			)
		doc.set(field, value)
	doc.erpnext_synced_values = frappe.as_json(values)


def _primary_address(customer):
	addresses = [row for row in customer.get("addresses") or [] if not row.get("disabled")]
	for row in addresses:
		if row["name"] == customer.get("customer_primary_address"):
			return row["name"]
	return next(
		(row["name"] for row in addresses if row.get("is_primary_address")),
		addresses[0]["name"] if addresses else None,
	)


def _set_primary_address(organization, target, audit, force):
	if not target:
		return
	previous = json.loads(audit.last_synced_values or "{}")
	current = organization.address or None
	if (
		("address" in previous or current)
		and current != target
		and current != (previous.get("address") or None)
		and not force
	):
		_conflict(_("The organization's address differs from ERPNext. Review before synchronizing."))
	organization.address = target
	_save_mapping(organization)


def _sync_related(customer, organization, settings, audit, force=False):
	primary = _primary_address(customer)
	if not settings.is_erpnext_in_different_site:
		# Contacts and Addresses are the same records on a shared site. Never copy or reparent people.
		for doctype, key in (("Contact", "contacts"), ("Address", "addresses")):
			for record in customer.get(key) or []:
				doc = frappe.get_doc(doctype, record["name"])
				doc.check_permission("write")
				_link_organization(doc, organization)
				_save_mapping(doc)
		_set_primary_address(organization, primary, audit, force)
		return
	for kind, source_field, fields in (
		("Contact", "contacts", ("first_name", "middle_name", "last_name", "gender")),
		(
			"Address",
			"addresses",
			(
				"address_title",
				"address_type",
				"address_line1",
				"address_line2",
				"city",
				"county",
				"state",
				"pincode",
				"country",
				"email_id",
				"phone",
				"disabled",
				"is_primary_address",
				"is_shipping_address",
			),
		),
	):
		for remote in customer.get(source_field) or []:
			matches = frappe.get_list(
				kind,
				filters={"erpnext_site": _source_site(settings), "erpnext_record": remote["name"]},
				fields=["name"],
				limit_page_length=2,
			)
			if len(matches) > 1:
				_conflict(_("Several local {0} records have the same ERPNext reference.").format(kind))
			if (
				remote.get("crm_record")
				and remote.get("crm_site")
				and _site(remote["crm_site"]) == _crm_site()
			):
				if not frappe.db.exists(kind, remote["crm_record"]):
					_conflict(_("The source {0} referenced by ERPNext no longer exists.").format(kind))
				if matches and matches[0].name != remote["crm_record"]:
					_conflict(_("The {0} records have conflicting reciprocal mappings.").format(kind))
				matches = [frappe._dict(name=remote["crm_record"])]
			doc = frappe.get_doc(kind, matches[0].name) if matches else frappe.new_doc(kind)
			doc.check_permission("write" if matches else "create")
			if doc.get("erpnext_record") and (
				doc.erpnext_record != remote["name"] or doc.get("erpnext_site") != _source_site(settings)
			):
				_conflict(_("This {0} is linked to another ERPNext record.").format(kind))
			# Only mapped records may be updated. Display names, email and phone never claim an existing identity.
			_related_values(doc, remote, fields, force)
			doc.erpnext_site = _source_site(settings)
			doc.erpnext_record = remote["name"]
			if kind == "Contact" and not matches:
				doc.company_name = (
					organization.name
					if remote.get("company_name") in (customer["name"], customer.get("customer_name"))
					else remote.get("company_name")
				)
			_link_organization(doc, organization)
			_save_mapping(doc)
			if kind == "Address" and remote["name"] == primary:
				_set_primary_address(organization, doc.name, audit, force)


def _backfill_deal_references(organization, customer, renamed_from=None):
	accepted = (None, "", customer, renamed_from)
	if renamed_from:
		filters = {"organization": organization.name, "erpnext_customer": renamed_from}
		readable = frappe.get_list("CRM Deal", filters=filters, fields=["count(name) as count"])[0]["count"]
		if readable != frappe.db.count("CRM Deal", filters):
			frappe.throw(
				_("Read access to all affected Deals is required to rename this Customer identity."),
				frappe.PermissionError,
			)
	start = 0
	while True:
		rows = frappe.get_list(
			"CRM Deal",
			filters={"organization": organization.name},
			fields=["name", "erpnext_customer"],
			order_by="name asc",
			limit_start=start,
			limit_page_length=BATCH_SIZE,
		)
		for row in rows:
			can_write = frappe.has_permission("CRM Deal", "write", row.name)
			if renamed_from and row.erpnext_customer == renamed_from and not can_write:
				frappe.throw(
					_(
						"Write permission is required to update the renamed Customer reference on Deal {0}."
					).format(row.name),
					frappe.PermissionError,
				)
			if row.erpnext_customer in accepted and can_write:
				# Derived navigation data must not replay Deal status hooks or overwrite a conflicting account.
				current = frappe.db.get_value("CRM Deal", row.name, "erpnext_customer", for_update=True)
				if current in accepted:
					frappe.db.set_value(
						"CRM Deal", row.name, "erpnext_customer", customer, update_modified=False
					)
		if len(rows) < BATCH_SIZE:
			return
		start += BATCH_SIZE


def reconcile_customer(
	customer, *, settings=None, legacy=None, organization=None, force=False, create=False, name_index=None
):
	settings = settings or _settings()
	audit = _audit(customer, settings)
	if audit.status in ("Ignored", "Unlinked") and not force:
		return audit
	prepared_remotely = False
	savepoint = "crm_customer_reconciliation"
	frappe.db.savepoint(savepoint)
	try:
		if customer.get("customer_type") != "Company":
			_conflict(_("Only Company Customers can be linked to CRM Organizations."))
		if create:
			organization, rule = None, "Created organization"
		elif organization:
			organization = frappe.get_doc("CRM Organization", organization)
			rule = "Manual link"
		else:
			organization, rule = _organization_for(customer, settings, legacy, name_index)
		if customer.get("crm_site") and _site(customer["crm_site"]) != _crm_site():
			_conflict(_("This Customer belongs to another CRM site."))
		if customer.get("crm_organization") and (
			not organization or customer["crm_organization"] != organization.name
		):
			_conflict(
				_("This Customer references another organization. Unlink that identity before replacing it.")
			)
		organization, values, renamed_from = _prepare_organization(
			customer, organization, audit, settings, force
		)
		_save_mapping(organization)
		if renamed_from:
			_backfill_deal_references(organization, customer["name"], renamed_from)
		if settings.is_erpnext_in_different_site:
			# The remote acknowledgement may be lost after its transaction commits. Keep the
			# local identity so retries can finish the same pair instead of inserting again.
			_save_audit(audit, customer, "Pending", rule=rule, organization=organization.name)
			frappe.db.commit()
			prepared_remotely = True
			frappe.db.savepoint(savepoint)
		result = _erp(
			"link_customer_to_organization",
			{
				"customer": customer["name"],
				"organization": organization.name,
				"crm_site": _crm_site(),
				"modified": customer.get("modified"),
			},
			write=True,
			settings=settings,
		)
		if _shared_values(result) != _shared_values(customer):
			_conflict(
				_("The ERPNext Customer changed during synchronization. Review its latest values and retry.")
			)
		_sync_related(customer, organization, settings, audit, force)
		_backfill_deal_references(organization, customer["name"])
		values["address"] = organization.address
		audit.last_synced_values = frappe.as_json(values)
		if name_index is not None:
			candidates = name_index.setdefault(_normalized_name(organization.organization_name), [])
			if organization.name not in candidates:
				candidates.append(organization.name)
		customer = {**customer, "modified": result.get("modified", customer.get("modified"))}
		return _save_audit(audit, customer, "Synced", rule=rule, organization=organization.name)
	except Exception as error:
		frappe.db.rollback(save_point=savepoint)
		if prepared_remotely:
			audit = frappe.get_doc(AUDIT, audit.name)
		status = (
			"Review"
			if isinstance(
				error, CustomerMappingConflict | frappe.DuplicateEntryError | frappe.TimestampMismatchError
			)
			else "Failed"
		)
		log = frappe.log_error(title="ERPNext Customer Reconciliation", message=frappe.get_traceback())
		audit.error_log = log.name if log else None
		return _save_audit(audit, customer, status, str(error))


def _customers(settings):
	rows = []
	start = 0
	while True:
		page = _erp("get_customers_for_crm", {"start": start, "page_length": BATCH_SIZE}, settings=settings)
		rows.extend(page["customers"])
		if not page.get("has_more"):
			return rows
		start = page["next_start"]


def _set_run_status(status, message=""):
	frappe.db.set_single_value("ERPNext CRM Settings", "customer_sync_status", status)
	frappe.db.set_single_value("ERPNext CRM Settings", "customer_sync_message", message)
	if status == "Running":
		frappe.db.set_single_value("ERPNext CRM Settings", "customer_sync_last_attempt", now_datetime())
	if status == "Completed":
		frappe.db.set_single_value("ERPNext CRM Settings", "customer_sync_last_success", now_datetime())


def run_reconciliation(legacy_only=False):
	try:
		settings = _settings()
		_set_run_status("Running", _("Customer reconciliation is running."))
		frappe.db.commit()
		summary = _run_reconciliation(settings, legacy_only)
		_set_run_status(
			"Completed", _("Reconciliation completed. Review each Customer's synchronization status.")
		)
		frappe.db.commit()
		return summary
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="ERPNext Customer Reconciliation", message=frappe.get_traceback())
		_set_run_status(
			"Failed",
			_(
				"Customer reconciliation could not complete. Check the ERPNext connection, integration permissions and Error Log, then retry."
			),
		)
		frappe.db.commit()
		raise
	finally:
		frappe.publish_realtime("crm_customer_sync_complete", user=frappe.session.user)


def _run_reconciliation(settings, legacy_only=False):
	from crm.integrations.erpnext.customer_migration import legacy_links

	customers = _customers(settings)
	legacy = legacy_links(customers, crm_site=_crm_site(), erpnext_site=_source_site(settings))
	name_index = _organization_names()
	summary = {"Synced": 0, "Review": 0, "Failed": 0, "Ignored": 0}
	for row in customers:
		references = legacy.get(row["name"])
		if legacy_only and not (
			references and (references.get("organizations") or references.get("conflict"))
		):
			continue
		try:
			existing_audit = _audit(row, settings)
			if existing_audit.status in ("Ignored", "Unlinked"):
				summary[existing_audit.status] = summary.get(existing_audit.status, 0) + 1
				continue
			customer = _customer(row["name"], settings)
			audit = reconcile_customer(customer, settings=settings, legacy=references, name_index=name_index)
			summary[audit.status] = summary.get(audit.status, 0) + 1
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			audit = _audit(row, settings)
			_save_audit(
				audit, row, "Failed", _("Customer could not be read. Review the Error Log and retry.")
			)
			frappe.log_error(title="ERPNext Customer Reconciliation", message=frappe.get_traceback())
			frappe.db.commit()
			summary["Failed"] += 1
	return summary


def enqueue_reconciliation():
	settings = frappe.get_single("ERPNext CRM Settings")
	if settings.enabled and settings.get("sync_customers"):
		frappe.enqueue(
			"crm.integrations.erpnext.customers.run_reconciliation",
			queue="long",
			timeout=3600,
			job_id="crm_customer_reconciliation",
			deduplicate=True,
			enqueue_after_commit=True,
		)


def on_customer_update(doc, method=None):
	settings = frappe.get_single("ERPNext CRM Settings")
	if (
		doc.customer_type == "Company"
		and settings.enabled
		and settings.get("sync_customers")
		and not settings.is_erpnext_in_different_site
	):
		enqueue_reconciliation()


def customer_for_organization(organization, settings=None):
	"""Read an established Company identity without creating or linking records."""
	settings = settings or _settings()
	doc = frappe.get_doc("CRM Organization", organization)
	doc.check_permission("read")
	if doc.get("erpnext_site") and _site(doc.erpnext_site) != _source_site(settings):
		_conflict(_("This organization is linked to another ERPNext site."))
	if frappe.db.exists(
		AUDIT, {"organization": doc.name, "erpnext_site": _source_site(settings), "status": "Unlinked"}
	):
		_conflict(_("Complete the pending Customer unlink before creating another opportunity customer."))
	detail = _erp(
		"resolve_customer_for_crm",
		{"customer": doc.get("erpnext_customer"), "organization": doc.name, "crm_site": _crm_site()},
		settings=settings,
	)
	return detail["customer"]["name"] if detail else None


def create_company_customer_from_deal(deal, settings):
	"""Make the Organization the durable Company identity for every new Deal."""
	from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
		get_contacts,
		get_organization_address,
	)

	organization = frappe.get_doc("CRM Organization", deal.organization)
	organization.check_permission("write")
	existing = customer_for_organization(organization.name, settings)
	if existing and organization.get("erpnext_customer") and existing != organization.erpnext_customer:
		# Resolution has already proved that the reciprocal identity survived a rename.
		_audit(_customer(existing, settings, include_related=False), settings)
		_backfill_deal_references(organization, existing, organization.erpnext_customer)
		organization.reload()
	contacts = get_contacts(deal)
	for row in contacts:
		contact = frappe.get_doc("Contact", row["contact"])
		contact.check_permission("read")
		contact.apply_fieldlevel_read_permissions()
		row["crm_record"] = contact.name
		row["erpnext_record"] = contact.get("erpnext_record")
		row["erpnext_site"] = contact.get("erpnext_site")
	address = get_organization_address(organization.name)
	if address:
		doc = frappe.get_doc("Address", address["name"])
		doc.check_permission("read")
		doc.apply_fieldlevel_read_permissions()
		address.update(
			crm_record=doc.name,
			erpnext_record=doc.get("erpnext_record"),
			erpnext_site=doc.get("erpnext_site"),
		)
	data = {
		"customer": existing,
		"customer_name": organization.organization_name,
		"customer_type": "Company",
		"crm_organization": organization.name,
		"crm_site": _crm_site(),
		"tax_id": organization.get("tax_id"),
		"territory": organization.territory or deal.territory,
		"industry": organization.industry or deal.industry,
		"website": organization.website,
		"default_currency": organization.currency or deal.currency,
		"contacts": json.dumps(contacts),
		"address": json.dumps(address),
	}
	if not settings.is_erpnext_in_different_site:
		for field, doctype in (("territory", "Territory"), ("industry", "Industry Type")):
			if data[field] and not frappe.db.exists(doctype, data[field]):
				data[field] = None
	customer_name = _erp("create_customer", {"customer_data": data}, write=True, settings=settings)
	if not customer_name:
		frappe.throw(
			_("The ERPNext Customer could not be confirmed. Reconcile the organization before retrying.")
		)
	organization.erpnext_customer = customer_name
	organization.erpnext_site = _source_site(settings)
	_save_mapping(organization)
	# This is a navigation/cache value only; subsequent Deals resolve through Organization.
	frappe.db.set_value("CRM Deal", deal.name, "erpnext_customer", customer_name)
	return customer_name


def validate_organization_mapping(doc, method=None):
	if not doc.meta.has_field("erpnext_customer"):
		return
	pair = (doc.get("erpnext_site") or None, doc.get("erpnext_customer") or None)
	old = (
		frappe.db.get_value(
			doc.doctype, doc.name, ["erpnext_site", "erpnext_customer"], as_dict=True, for_update=True
		)
		if doc.name and not doc.is_new()
		else None
	)
	previous = (old.get("erpnext_site") or None, old.get("erpnext_customer") or None) if old else (None, None)
	if bool(pair[0]) != bool(pair[1]):
		frappe.throw(_("ERPNext Site and Customer must be set together."))
	if pair != previous and not _mapping_write_allowed(doc):
		frappe.throw(
			_("Use ERPNext customer reconciliation to change this organization's customer identity.")
		)


def validate_deal_customer(doc, method=None):
	if not doc.organization or not doc.meta.has_field("erpnext_customer"):
		return
	if not doc.is_new() and not doc.has_value_changed("organization"):
		return
	organization = frappe.get_doc("CRM Organization", doc.organization)
	organization.check_permission("read")
	settings = frappe.get_single("ERPNext CRM Settings")
	if organization.get("erpnext_customer") and organization.get("erpnext_site") == _source_site(settings):
		doc.erpnext_customer = organization.erpnext_customer


def validate_related_mapping(doc, method=None):
	if not doc.meta.has_field("erpnext_record"):
		return
	pair = (doc.get("erpnext_site") or None, doc.get("erpnext_record") or None)
	old = (
		frappe.db.get_value(
			doc.doctype, doc.name, ["erpnext_site", "erpnext_record"], as_dict=True, for_update=True
		)
		if doc.name and not doc.is_new()
		else None
	)
	previous = (old.get("erpnext_site") or None, old.get("erpnext_record") or None) if old else (None, None)
	if bool(pair[0]) != bool(pair[1]):
		frappe.throw(_("ERPNext Site and Record must be set together."))
	if pair != previous and not _mapping_write_allowed(doc):
		frappe.throw(_("Use customer reconciliation to change this record's ERPNext identity."))


def _require_no_pending_unlink(organization):
	if frappe.db.exists(AUDIT, {"organization": organization, "status": "Unlinked"}):
		frappe.throw(
			_("Complete the pending Customer unlink before renaming, merging or deleting this organization.")
		)


def before_organization_rename(doc, method, olddn, newdn, merge=False):
	_require_no_pending_unlink(olddn)
	if merge:
		_require_no_pending_unlink(newdn)
	if merge and (
		doc.get("erpnext_customer") or frappe.db.get_value("CRM Organization", newdn, "erpnext_customer")
	):
		frappe.throw(_("Unlink ERPNext Customers before merging CRM Organizations."))


def after_organization_rename(doc, method, olddn, newdn, merge=False):
	if not doc.get("erpnext_customer"):
		return
	settings = _settings()
	if doc.erpnext_site != _source_site(settings):
		frappe.throw(_("This organization belongs to another ERPNext connection. Unlink it before renaming."))
	customer = _customer(doc.erpnext_customer, settings, include_related=False)
	_erp(
		"link_customer_to_organization",
		{
			"customer": customer["name"],
			"organization": newdn,
			"previous_organization": olddn,
			"crm_site": _crm_site(),
			"modified": customer["modified"],
		},
		write=True,
		settings=settings,
	)


def before_organization_delete(doc, method=None):
	_require_no_pending_unlink(doc.name)
	if doc.get("erpnext_customer"):
		frappe.throw(_("Unlink the ERPNext Customer before deleting this organization."))


def after_customer_rename(doc, method, olddn, newdn, merge=False):
	if not doc.get("crm_organization") or doc.get("crm_site") != _crm_site():
		return
	organization = frappe.get_doc("CRM Organization", doc.crm_organization)
	organization.check_permission("write")
	if organization.get("erpnext_customer") != olddn or organization.get("erpnext_site") != _crm_site():
		frappe.throw(_("The CRM Organization identity conflicts with this Customer rename."))
	organization.erpnext_customer = newdn
	_backfill_deal_references(organization, newdn, olddn)
	_save_mapping(organization)
	settings = frappe.get_single("ERPNext CRM Settings")
	old_key = _audit_name(olddn, settings, source_site=_crm_site())
	if frappe.db.exists(AUDIT, old_key):
		audit = frappe.get_doc(AUDIT, old_key)
		new_key = _audit_name(newdn, settings, source_site=_crm_site())
		_rename_audit(audit, newdn, new_key)


@frappe.whitelist(methods=["POST"])
def run_customer_sync() -> dict:
	_require_manage()
	_settings()
	_set_run_status("Queued", _("Customer reconciliation is queued."))
	frappe.enqueue(
		"crm.integrations.erpnext.customers.run_reconciliation",
		queue="long",
		timeout=3600,
		job_id="crm_customer_reconciliation",
		deduplicate=True,
		enqueue_after_commit=True,
	)
	return {"queued": True}


_AUDIT_FIELDS = [
	"name",
	"customer",
	"customer_name",
	"customer_type",
	"organization",
	"status",
	"match_rule",
	"last_attempt",
	"last_success",
	"message",
	"modified",
]


@frappe.whitelist()
def get_customer_sync_status(
	start: int = 0, page_length: int = 20, search: str = "", status: str = ""
) -> dict:
	_require_manage()
	settings = _settings()
	start, page_length = max(0, cint(start)), min(100, max(1, cint(page_length)))
	filters = {"erpnext_site": _source_site(settings)}
	if status:
		if status not in ("Pending", "Synced", "Review", "Failed", "Ignored", "Unlinked"):
			frappe.throw(_("Choose a valid synchronization status."))
		filters["status"] = status
	or_filters = (
		[
			[AUDIT, field, "like", f"%{str(search)[:200]}%"]
			for field in ("customer", "customer_name", "organization")
		]
		if search
		else None
	)
	rows = frappe.get_list(
		AUDIT,
		filters=filters,
		or_filters=or_filters,
		fields=_AUDIT_FIELDS,
		order_by="modified desc, name asc",
		limit_start=start,
		limit_page_length=page_length + 1,
	)
	total = frappe.get_list(AUDIT, filters=filters, or_filters=or_filters, fields=["count(name) as total"])[
		0
	].total
	return {
		"rows": rows[:page_length],
		"total": total,
		"has_more": len(rows) > page_length,
		"can_manage": _can_manage(),
		"run": {
			"status": settings.get("customer_sync_status"),
			"message": settings.get("customer_sync_message"),
			"last_attempt": settings.get("customer_sync_last_attempt"),
			"last_success": settings.get("customer_sync_last_success"),
		},
	}


@frappe.whitelist(methods=["POST"])
def resolve_customer(
	name: str, action: str, organization: str | None = None, modified: str | None = None
) -> dict:
	_require_manage()
	settings = _settings()
	audit = frappe.get_doc(AUDIT, name, for_update=True)
	audit.check_permission("read")
	if audit.erpnext_site != _source_site(settings):
		frappe.throw(_("This reconciliation belongs to another ERPNext connection."))
	if not modified or get_datetime(audit.modified) != get_datetime(modified):
		frappe.throw(
			_("The synchronization record changed. Refresh and review it again."),
			frappe.TimestampMismatchError,
		)
	if action not in ("link", "create", "resync", "ignore", "unlink"):
		frappe.throw(_("Choose a valid reconciliation action."))
	pending_unlink = audit.status == "Unlinked" and audit.organization
	if pending_unlink and action != "unlink":
		frappe.throw(_("Complete the pending unlink before starting another reconciliation."))
	if action == "ignore":
		audit.status = "Ignored"
		audit.last_attempt = now_datetime()
		audit.message = _("Ignored by {0}").format(frappe.session.user)
		audit.save(ignore_permissions=True)
		return {field: audit.get(field) for field in _AUDIT_FIELDS}
	if pending_unlink:
		detail = _erp(
			"resolve_customer_for_crm",
			{"customer": audit.customer, "organization": audit.organization, "crm_site": _crm_site()},
			settings=settings,
		)
		customer = detail["customer"]
	else:
		customer = _customer(audit.customer, settings, include_related=action != "unlink")
	if (
		audit.source_modified
		and get_datetime(customer["modified"]) != get_datetime(audit.source_modified)
		and not pending_unlink
		and not (action == "resync" and audit.status in ("Ignored", "Unlinked"))
	):
		frappe.throw(
			_("The ERPNext Customer changed. Synchronize and review the latest values first."),
			frappe.TimestampMismatchError,
		)
	if action == "unlink":
		if not audit.organization:
			frappe.throw(_("There is no organization link to remove."))
		doc = frappe.get_doc("CRM Organization", audit.organization)
		doc.check_permission("write")
		pending_unlink = (
			audit.status == "Unlinked" and not doc.get("erpnext_customer") and not doc.get("erpnext_site")
		)
		if not pending_unlink and (
			doc.get("erpnext_customer") != audit.customer or doc.get("erpnext_site") != audit.erpnext_site
		):
			frappe.throw(_("The organization link has changed. Refresh before unlinking."))
		if settings.is_erpnext_in_different_site:
			doc.erpnext_customer = None
			doc.erpnext_site = None
			_save_mapping(doc)
			# Retain the reviewed Organization until the remote acknowledgement is confirmed.
			# Automatic jobs skip this durable intent instead of recreating the removed link.
			_save_audit(
				audit, customer, "Unlinked", _("Local unlink recorded; ERPNext confirmation is pending.")
			)
			frappe.db.commit()
		_erp(
			"unlink_customer_from_organization",
			{
				"customer": customer["name"],
				"organization": doc.name,
				"crm_site": _crm_site(),
				"modified": customer["modified"],
			},
			write=True,
			settings=settings,
		)
		doc.erpnext_customer = None
		doc.erpnext_site = None
		_save_mapping(doc)
		audit.organization = None
		audit.last_synced_values = None
		_save_audit(audit, customer, "Unlinked", _("Unlinked by {0}").format(frappe.session.user))
		if customer["name"] != audit.customer:
			current = _audit(customer, settings)
			current.organization = None
			_save_audit(current, customer, "Unlinked", _("Unlinked after the ERPNext Customer was renamed."))
	else:
		if audit.status == "Unlinked" and audit.organization:
			frappe.throw(_("Complete the pending unlink before starting another reconciliation."))
		if action == "link" and not organization:
			frappe.throw(_("Choose an organization to link."))
		if action == "create":
			if customer.get("crm_organization") or frappe.db.exists(
				"CRM Organization", {"erpnext_customer": customer["name"]}
			):
				frappe.throw(_("This Customer already has an organization. Review its existing link."))
		audit = reconcile_customer(
			customer,
			settings=settings,
			organization=organization or audit.organization,
			force=True,
			create=action == "create",
		)
	return {field: audit.get(field) for field in _AUDIT_FIELDS}
