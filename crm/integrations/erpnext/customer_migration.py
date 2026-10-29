"""Read-only legacy evidence for Organization/Customer reconciliation.

The caller supplies the complete Company Customer snapshot from the configured
ERPNext site and owns authorization, connection identity and all later writes.
No Deal, Organization or mapping is created by this module.
"""

from collections import defaultdict
from urllib.parse import urlsplit, urlunsplit

import frappe
from frappe import _
from frappe.utils import get_url

PAGE_SIZE = 500


def _site_identity(value):
	if not isinstance(value, str):
		return ""
	value = value.strip()
	try:
		parsed = urlsplit(value)
		if (
			parsed.scheme.lower() not in ("http", "https")
			or not parsed.hostname
			or parsed.username is not None
			or parsed.password is not None
			or parsed.query
			or parsed.fragment
			or "\\" in value
			or any(character.isspace() for character in value)
		):
			raise ValueError
		host = parsed.hostname.encode("idna").decode("ascii").lower()
		if ":" in host:
			host = f"[{host}]"
		port = parsed.port
		if port and (parsed.scheme.lower(), port) not in (("http", 80), ("https", 443)):
			host = f"{host}:{port}"
		result = urlunsplit((parsed.scheme.lower(), host, parsed.path.rstrip("/"), "", ""))
		if len(result) > 255:
			raise ValueError
		return result
	except (ValueError, UnicodeError):
		# Invalid historical namespaces remain distinct and require review.
		return value


def _read_all(doctype, fields):
	"""Do not infer an empty graph from records hidden by user permissions."""
	if not frappe.has_permission(doctype, ptype="read"):
		frappe.throw(
			_("You cannot read all records required for legacy customer reconciliation."),
			exc=frappe.PermissionError,
		)
	rows = []
	for start in range(0, frappe.db.count(doctype) + PAGE_SIZE, PAGE_SIZE):
		page = frappe.get_list(
			doctype,
			fields=fields,
			order_by="name asc",
			limit_start=start,
			limit_page_length=PAGE_SIZE,
		)
		if any(any(field not in row for field in fields) for row in page):
			frappe.throw(
				_("Some legacy customer relationship fields are not readable."),
				exc=frappe.PermissionError,
			)
		rows.extend(page)
		if len(page) < PAGE_SIZE:
			break
	if len(rows) != frappe.db.count(doctype):
		frappe.throw(
			_(
				"Legacy reconciliation requires read access to all CRM Deals and Organizations. "
				"Retry with a user who can read the complete relationship history."
			),
			exc=frappe.PermissionError,
		)
	return rows


def legacy_links(customers, crm_site=None, erpnext_site=None):
	"""Return ``{organizations, conflict, previous_customer}`` per Customer name.

	``customers`` must contain the full source Company Customer set, including
	``name`` and any ``crm_deal``, ``crm_organization`` and ``crm_site`` values.
	All readable forward Deal links and existing Organization links participate
	in the graph, even when they point to a Customer outside the supplied set.
	Only a conflict-free single edge is suitable for automatic migration.
	``previous_customer`` is unverified rename evidence: the caller must prove
	the old Customer is absent and the new Customer retains the exact reciprocal
	Organization identity before changing an existing Organization mapping.
	"""
	if not isinstance(customers, list | tuple):
		frappe.throw(_("Legacy reconciliation requires a complete Customer list."))
	by_customer = {}
	for customer in customers:
		if (
			not isinstance(customer, dict)
			or not isinstance(customer.get("name"), str)
			or not customer["name"]
		):
			frappe.throw(_("Every legacy Customer must have a native record identity."))
		for field in ("crm_deal", "crm_organization", "crm_site"):
			if customer.get(field) is not None and not isinstance(customer[field], str):
				frappe.throw(_("Legacy Customer relationships must contain native record identities."))
		if customer["name"] in by_customer:
			frappe.throw(_("The legacy Customer snapshot contains duplicate identities."))
		by_customer[customer["name"]] = customer
	if not by_customer:
		return {}

	deal_fields = ["name", "organization"]
	if frappe.get_meta("CRM Deal").has_field("erpnext_customer"):
		deal_fields.append("erpnext_customer")
	organization_fields = ["name"]
	organization_meta = frappe.get_meta("CRM Organization")
	if organization_meta.has_field("erpnext_customer"):
		organization_fields.append("erpnext_customer")
	if organization_meta.has_field("erpnext_site"):
		organization_fields.append("erpnext_site")
	deals = {row["name"]: row for row in _read_all("CRM Deal", deal_fields)}
	organizations = {row["name"]: row for row in _read_all("CRM Organization", organization_fields)}
	edges = defaultdict(set)
	problems = defaultdict(set)
	current_site = _site_identity(crm_site or get_url(allow_header_override=False))
	current_erpnext_site = _site_identity(erpnext_site or get_url(allow_header_override=False))

	def current_connection(organization_name):
		organization = organizations.get(organization_name)
		return (
			not organization
			or not organization.get("erpnext_site")
			or (_site_identity(organization["erpnext_site"]) == current_erpnext_site)
		)

	# A remote Customer rename preserves its reciprocal Organization identity.
	# Defer its stale forward IDs to the caller's authoritative ERP rename proof;
	# absence from this permission-filtered Company snapshot is not that proof.
	reciprocal_customers = defaultdict(set)
	for customer_name, customer in by_customer.items():
		if (
			customer.get("crm_organization")
			and customer.get("crm_site")
			and _site_identity(customer["crm_site"]) == current_site
		):
			reciprocal_customers[customer["crm_organization"]].add(customer_name)
	deferred_renames = {}
	previous_customers = {}
	for organization_name, organization in organizations.items():
		previous_customer = organization.get("erpnext_customer")
		current_customers = reciprocal_customers[organization_name]
		if (
			previous_customer
			and previous_customer not in by_customer
			and len(current_customers) == 1
			and current_connection(organization_name)
		):
			current_customer = next(iter(current_customers))
			deferred_renames[previous_customer, organization_name] = current_customer
			previous_customers[current_customer] = previous_customer

	def add_edge(customer_name, organization_name, evidence):
		if not organization_name:
			problems[customer_name].add(f"{evidence} has no CRM Organization.")
			return
		if not current_connection(organization_name):
			problems[customer_name].add(
				f"CRM Organization {organization_name} belongs to another ERPNext connection ({evidence})."
			)
			return
		customer_name = deferred_renames.get((customer_name, organization_name), customer_name)
		edges[customer_name].add(organization_name)
		if organization_name not in organizations:
			problems[customer_name].add(
				f"CRM Organization {organization_name} is missing or unreadable ({evidence})."
			)

	for deal in deals.values():
		if customer_name := deal.get("erpnext_customer"):
			if not deal.get("organization") and customer_name not in by_customer:
				continue
			if not current_connection(deal.get("organization")):
				continue
			add_edge(customer_name, deal.get("organization"), f"Legacy Deal {deal['name']}")
	for organization in organizations.values():
		if customer_name := organization.get("erpnext_customer"):
			if current_connection(organization["name"]):
				add_edge(customer_name, organization["name"], "Existing Organization mapping")
	for customer_name, customer in by_customer.items():
		if customer.get("crm_site") and _site_identity(customer["crm_site"]) != current_site:
			problems[customer_name].add(
				"Customer belongs to a different CRM site; its relationship cannot be reassigned automatically."
			)
			# An Organization/Deal name from another CRM site is not a local identity.
			continue
		if organization_name := customer.get("crm_organization"):
			add_edge(customer_name, organization_name, "Existing Customer mapping")
		if legacy_deal := customer.get("crm_deal"):
			deal = deals.get(legacy_deal)
			if not deal:
				problems[customer_name].add(f"Legacy Deal {legacy_deal} is missing or unreadable.")
			else:
				add_edge(customer_name, deal.get("organization"), f"Legacy Customer.crm_deal {legacy_deal}")

	customers_by_organization = defaultdict(set)
	for customer_name, linked_organizations in edges.items():
		for organization_name in linked_organizations:
			customers_by_organization[organization_name].add(customer_name)
		if len(linked_organizations) > 1:
			problems[customer_name].add("Customer is associated with more than one CRM Organization.")
	for organization_name, linked_customers in customers_by_organization.items():
		if len(linked_customers) > 1:
			for customer_name in linked_customers:
				problems[customer_name].add(
					f"CRM Organization {organization_name} is associated with more than one ERPNext Customer."
				)
	for customer_name, linked_organizations in edges.items():
		for organization_name in linked_organizations:
			organization = organizations.get(organization_name)
			if (
				organization
				and organization.get("erpnext_customer") not in (None, "", customer_name)
				and deferred_renames.get((organization.get("erpnext_customer"), organization_name))
				!= customer_name
			):
				problems[customer_name].add(
					f"CRM Organization {organization_name} already maps to a different ERPNext Customer."
				)
	return {
		customer_name: {
			"organizations": sorted(edges[customer_name]),
			"conflict": " ".join(sorted(problems[customer_name])) or None,
			"previous_customer": previous_customers.get(customer_name),
		}
		for customer_name in by_customer
	}
