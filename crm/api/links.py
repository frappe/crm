import base64
import hashlib
import hmac
import json

import frappe
from frappe.rate_limiter import rate_limit


def _secret() -> bytes:
	return (frappe.local.conf.get("encryption_key") or frappe.local.site).encode()


def _sign(slug: str, token: str) -> str:
	return hmac.new(_secret(), f"{slug}|{token}".encode(), hashlib.sha256).hexdigest()[:16]


def personal_link_url(slug: str, reference_doctype: str, reference_name: str) -> str:
	"""Personalized tracked-link URL: the token carries who clicked, HMAC-signed."""
	payload = json.dumps({"d": reference_doctype, "n": reference_name})
	token = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
	return frappe.utils.get_url(f"/api/method/crm.api.links.r?l={slug}&t={token}&s={_sign(slug, token)}")


def _verify(slug: str, token: str, sig: str) -> dict | None:
	if not hmac.compare_digest(sig, _sign(slug, token)):
		return None
	try:
		padded = token + "=" * (-len(token) % 4)
		return json.loads(base64.urlsafe_b64decode(padded))
	except Exception:
		return None


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=600, seconds=60 * 60)
def r(l: str, t: str | None = None, s: str | None = None):
	"""Tracked-link redirect: count the click, fire automation events, redirect."""
	link = frappe.db.get_value("CRM Tracked Link", l, ["name", "target_url", "click_count"], as_dict=True)
	if not link:
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/"
		return

	frappe.db.set_value(
		"CRM Tracked Link", link.name, "click_count", (link.click_count or 0) + 1, update_modified=False
	)

	payload = _verify(l, t, s) if (t and s) else None
	if (
		payload
		and payload.get("d") in ("CRM Lead", "CRM Deal")
		and frappe.db.exists(payload["d"], payload["n"])
	):
		try:
			ref = frappe.get_doc(payload["d"], payload["n"])
			ref.add_comment(
				"Comment", frappe._("Clicked tracked link {0}").format(frappe.utils.escape_html(l))
			)
			from crm.automation.engine import process_event

			frappe.local.form_dict["_tracked_link"] = l
			process_event("link_clicked", ref)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "CRM Tracked Link: event failed")

	frappe.db.commit()
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = link.target_url
