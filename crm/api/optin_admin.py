"""
crm/api/optin_admin.py — Internal admin API for Opt-In Network and Facility management.

RBAC:
  - System Manager / Sales Manager: full access to all networks and facilities.
  - Network Coordinator: read/write only for networks where they appear in the
    coordinators child table. Determined by _get_coordinator_networks(user).
"""
from __future__ import annotations

import csv
import io
import json

import frappe
from frappe import _


def _is_admin(user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    return "System Manager" in roles or "Sales Manager" in roles or user == "Administrator"


def _get_coordinator_networks(user=None):
    """Return list of network slugs where user is a coordinator. Empty = no access."""
    user = user or frappe.session.user
    rows = frappe.get_list(
        "CRM Network Coordinator",
        filters={"user": user, "parenttype": "CRM Opt-In Network"},
        fields=["parent"],
        ignore_permissions=True,  # SYSTEM-INTERNAL
    )
    return [r.parent for r in rows]


def _assert_network_access(network_slug):
    """Raise PermissionError if current user has no access to this network."""
    if _is_admin():
        return
    allowed = _get_coordinator_networks()
    if network_slug not in allowed:
        frappe.throw(_("Not permitted"), frappe.PermissionError)


# ---------------------------------------------------------------------------
# Network CRUD
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_networks(page=0, page_size=20):
    page = int(page or 0)
    page_size = int(page_size or 20)

    if _is_admin():
        filters = {}
    else:
        allowed = _get_coordinator_networks()
        if not allowed:
            return {"rows": [], "total": 0}
        filters = {"name": ["in", allowed]}

    rows = frappe.get_list(
        "CRM Opt-In Network",
        filters=filters,
        fields=["name", "slug", "display_name", "enabled", "contact_email", "footer_legal_name", "logo_url", "primary_colour", "price_list_override"],
        order_by="display_name asc",
        limit_start=page * page_size,
        limit_page_length=page_size,
    )
    total = len(frappe.get_list("CRM Opt-In Network", filters=filters, fields=["name"], limit_page_length=0))
    return {"rows": rows, "total": total}


@frappe.whitelist()
def save_network(data):
    """Create or update a CRM Opt-In Network. data is a JSON-serialisable dict."""
    if not _is_admin():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if isinstance(data, str):
        data = json.loads(data)

    name = data.get("name")
    if name and frappe.db.exists("CRM Opt-In Network", name):
        doc = frappe.get_doc("CRM Opt-In Network", name)
    else:
        doc = frappe.new_doc("CRM Opt-In Network")

    for field in ("slug", "display_name", "enabled", "contact_email", "footer_legal_name",
                  "logo_url", "primary_colour", "price_list_override", "custom_header_copy"):
        if field in data:
            setattr(doc, field, data[field])

    doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()
    return {"name": doc.name}


@frappe.whitelist()
def delete_network(name):
    if not _is_admin():
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    name = frappe.utils.cstr(name)
    # Check no facilities reference this network
    count = len(frappe.get_list(
        "CRM Facility Membership",
        filters={"network": name, "parenttype": "CRM Pre-Qualified Facility"},
        fields=["name"],
        limit_page_length=1,
        ignore_permissions=True,  # SYSTEM-INTERNAL
    ))
    if count:
        frappe.throw(_("Cannot delete network: facilities are assigned to it. Remove all memberships first."))
    frappe.delete_doc("CRM Opt-In Network", name, ignore_permissions=True)
    frappe.db.commit()
    return {"deleted": name}


# ---------------------------------------------------------------------------
# Facility CRUD
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_facilities(network=None, status=None, page=0, page_size=20):
    page = int(page or 0)
    page_size = int(page_size or 20)

    if not _is_admin():
        allowed_networks = _get_coordinator_networks()
        if not allowed_networks:
            return {"rows": [], "total": 0}
        # If network filter is set, check it's in allowed list
        if network and network not in allowed_networks:
            return {"rows": [], "total": 0}
        target_networks = [network] if network else allowed_networks
    else:
        target_networks = [network] if network else None

    # Get facility names that have memberships in target networks
    mem_filters = {"parenttype": "CRM Pre-Qualified Facility"}
    if target_networks:
        mem_filters["network"] = ["in", target_networks]
    if status:
        mem_filters["status"] = status

    mem_rows = frappe.get_list(
        "CRM Facility Membership",
        filters=mem_filters,
        fields=["parent", "network", "status", "contact_name", "contact_email", "contact_phone"],
        ignore_permissions=True,  # SYSTEM-INTERNAL
        limit_page_length=0,
    )

    if not mem_rows:
        return {"rows": [], "total": 0}

    # Group memberships by parent facility
    from collections import defaultdict
    mem_by_parent = defaultdict(list)
    for m in mem_rows:
        mem_by_parent[m.parent].append(m)

    parent_names = list(mem_by_parent.keys())

    fac_rows = frappe.get_list(
        "CRM Pre-Qualified Facility",
        filters={"name": ["in", parent_names]},
        fields=["name", "mfl_code", "facility_name", "keph_level"],
        order_by="facility_name asc",
        limit_start=page * page_size,
        limit_page_length=page_size,
        ignore_permissions=True,  # SYSTEM-INTERNAL
    )

    result = []
    for fac in fac_rows:
        result.append({
            "name": fac.name,
            "mfl_code": fac.mfl_code,
            "facility_name": fac.facility_name,
            "keph_level": fac.keph_level,
            "memberships": [
                {
                    "network": m.network,
                    "status": m.status,
                    "contact_name": m.contact_name,
                    "contact_email": m.contact_email,
                    "contact_phone": m.contact_phone,
                }
                for m in mem_by_parent[fac.name]
            ],
        })

    return {"rows": result, "total": len(parent_names)}


@frappe.whitelist()
def save_facility(data):
    """
    Create or update a CRM Pre-Qualified Facility with its memberships.
    data shape: {
      name?: str,  # existing doc name (for update)
      mfl_code: str,
      facility_name: str,
      keph_level: str,
      memberships: [{network, status, contact_name, contact_email, contact_phone}]
    }
    Max 2 memberships enforced.
    """
    if isinstance(data, str):
        data = json.loads(data)

    # RBAC: coordinators can only save facilities in their networks
    mem_networks = [m.get("network") for m in (data.get("memberships") or [])]
    if not _is_admin():
        allowed = _get_coordinator_networks()
        for net in mem_networks:
            if net and net not in allowed:
                frappe.throw(_("Not permitted for network %s") % net, frappe.PermissionError)

    memberships = data.get("memberships") or []
    if len(memberships) > 2:
        frappe.throw(_("A facility may belong to at most 2 networks."))

    name = data.get("name")
    mfl_code = frappe.utils.cstr(data.get("mfl_code") or "").strip()

    if name and frappe.db.exists("CRM Pre-Qualified Facility", name):
        doc = frappe.get_doc("CRM Pre-Qualified Facility", name)
    elif mfl_code:
        # Check for existing by mfl_code
        existing = frappe.get_all(
            "CRM Pre-Qualified Facility",
            filters={"mfl_code": mfl_code},
            pluck="name",
            limit=1,
        )
        doc = frappe.get_doc("CRM Pre-Qualified Facility", existing[0]) if existing else frappe.new_doc("CRM Pre-Qualified Facility")
    else:
        doc = frappe.new_doc("CRM Pre-Qualified Facility")

    doc.mfl_code = mfl_code or doc.mfl_code
    doc.facility_name = frappe.utils.cstr(data.get("facility_name") or doc.facility_name or "")
    doc.keph_level = frappe.utils.cstr(data.get("keph_level") or doc.keph_level or "")

    # Rebuild memberships: keep existing rows not in the new set (other network), update/add for this set
    new_network_set = {m.get("network") for m in memberships if m.get("network")}
    # Remove membership rows for networks being replaced
    doc.memberships = [m for m in (doc.memberships or []) if m.network not in new_network_set]
    for mem_data in memberships:
        net = frappe.utils.cstr(mem_data.get("network") or "").strip()
        if not net:
            continue
        doc.append("memberships", {
            "network": net,
            "status": mem_data.get("status") or "Active",
            "contact_name": frappe.utils.cstr(mem_data.get("contact_name") or ""),
            "contact_email": frappe.utils.cstr(mem_data.get("contact_email") or "").lower(),
            "contact_phone": frappe.utils.cstr(mem_data.get("contact_phone") or ""),
        })

    doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()
    return {"name": doc.name}


@frappe.whitelist()
def delete_facility(name):
    name = frappe.utils.cstr(name)
    if not _is_admin():
        # Check coordinator has access to this facility's networks
        fac = frappe.get_doc("CRM Pre-Qualified Facility", name)
        allowed = _get_coordinator_networks()
        fac_networks = [m.network for m in (fac.memberships or [])]
        if not any(n in allowed for n in fac_networks):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
    frappe.delete_doc("CRM Pre-Qualified Facility", name, ignore_permissions=True)
    frappe.db.commit()
    return {"deleted": name}


# ---------------------------------------------------------------------------
# HFR Lookup
# ---------------------------------------------------------------------------


@frappe.whitelist()
def lookup_hfr(mfl_code):
    """
    Look up a facility in the Health Facility Registry by MFL code.
    Delegates to crm.api.hfr.search_facility which reads CRM HFR Settings
    (hfr_url, hfr_fetch_path, JWT credentials). Returns {mfl_code, facility_name, keph_level}.
    """
    mfl_code = frappe.utils.cstr(mfl_code).strip()
    if not mfl_code:
        frappe.throw(_("MFL code is required"))

    from crm.api.hfr import search_facility

    results = search_facility(mfl_code, search_by="mfl_code")
    if not results:
        frappe.throw(_("Facility MFL %s not found in HFR") % mfl_code)

    hit = results[0]
    keph_level_raw = frappe.utils.cstr(hit.get("level") or "").strip()
    if keph_level_raw and not keph_level_raw.lower().startswith("level"):
        keph_level = "Level %s" % keph_level_raw
    else:
        keph_level = keph_level_raw

    return {
        "mfl_code": hit.get("mfl_code") or mfl_code,
        "facility_name": hit.get("name") or "",
        "keph_level": keph_level,
    }


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------


@frappe.whitelist()
def import_facilities_csv(csv_data, network_slug, dry_run=0):
    """
    Parse and import a CSV of pre-qualified facilities for a network.

    Expected CSV columns (order flexible, matched by header name):
      mfl_code, facility_name (optional — auto-filled from HFR if blank),
      keph_level (optional — auto-filled from HFR if blank),
      contact_name, contact_email, contact_phone

    Returns:
      {
        imported: int,
        errors: [{row: int, mfl_code: str, message: str}],
        dry_run: bool
      }
    """
    _assert_network_access(network_slug)

    dry_run = bool(int(dry_run or 0))

    if isinstance(csv_data, str):
        raw = csv_data
    else:
        raw = frappe.utils.cstr(csv_data)

    reader = csv.DictReader(io.StringIO(raw))

    # Normalise header names (strip, lowercase)
    def _norm(row):
        return {k.strip().lower().replace(" ", "_"): frappe.utils.cstr(v or "").strip() for k, v in row.items()}

    rows = [_norm(r) for r in reader]

    errors = []
    imported = 0

    for idx, row in enumerate(rows, start=2):  # row 1 is header
        mfl_code = row.get("mfl_code") or row.get("mfl code") or ""
        if not mfl_code:
            errors.append({"row": idx, "mfl_code": "", "message": "mfl_code is required"})
            continue

        contact_name = row.get("contact_name") or ""
        contact_email = (row.get("contact_email") or "").lower()
        contact_phone = row.get("contact_phone") or ""

        if not contact_email:
            errors.append({"row": idx, "mfl_code": mfl_code, "message": "contact_email is required"})
            continue

        facility_name = row.get("facility_name") or ""
        keph_level = row.get("keph_level") or row.get("keph level") or ""

        # HFR enrichment if fields missing
        if not facility_name or not keph_level:
            try:
                hfr = lookup_hfr(mfl_code)
                facility_name = facility_name or hfr.get("facility_name") or ""
                keph_level = keph_level or hfr.get("keph_level") or ""
            except Exception:
                pass  # HFR lookup failure is non-fatal; row will save with whatever we have

        if not facility_name:
            errors.append({"row": idx, "mfl_code": mfl_code, "message": "facility_name could not be resolved (not in CSV and HFR lookup failed)"})
            continue

        if not dry_run:
            try:
                save_facility({
                    "mfl_code": mfl_code,
                    "facility_name": facility_name,
                    "keph_level": keph_level or "Level 3",
                    "memberships": [{
                        "network": network_slug,
                        "status": "Active",
                        "contact_name": contact_name,
                        "contact_email": contact_email,
                        "contact_phone": contact_phone,
                    }],
                })
                imported += 1
            except Exception as exc:
                errors.append({"row": idx, "mfl_code": mfl_code, "message": frappe.utils.cstr(exc)})
        else:
            imported += 1  # count as "would import" in dry run

    return {"imported": imported, "errors": errors, "dry_run": dry_run}


@frappe.whitelist()
def csv_template():
    """Return the CSV template as a string for download."""
    return "mfl_code,facility_name,keph_level,contact_name,contact_email,contact_phone\n22999,Example Hospital,Level 4,Jane Wanjiku,jane@hospital.co.ke,0722000000\n"
