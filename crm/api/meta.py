import frappe
import hmac, hashlib
import json
from typing import Any, Dict, List, Optional
from frappe.utils.password import get_decrypted_password

try:
    import requests  # whitelisted RPCs can import stdlib + installed deps
except Exception:
    requests = None

# ---------- Config helpers ----------
def _conf(key: str, default: str = "") -> str:
    # Prefer site_config; fallback to Single doctype if present
    val = (frappe.conf.get(key) or "").strip()
    if val:
        return val
    try:
        return (frappe.db.get_single_value("Meta Integration Settings", key) or default).strip()
    except Exception:
        return default

def _verify_token() -> str:         return _conf("meta_verify_token")
def _app_id() -> str:               return _conf("meta_app_id")
def _app_secret() -> str:           
    # Prefer doctype over site_config for app_secret verification
    try:
        doctype_val = get_decrypted_password("Meta Integration Settings", "Meta Integration Settings", "meta_app_secret", raise_exception=False)
        if doctype_val:
            return doctype_val.strip()
    except Exception:
        pass
    # Fallback to site_config if doctype value not available
    return (frappe.conf.get("meta_app_secret") or "").strip()
def _graph_ver() -> str:            return _conf("meta_graph_api_version", "v20.0")
def _access_token() -> str:         return _conf("meta_access_token")

def _norm(x):
    if x is None: return ""
    return x.strip() if isinstance(x, str) else str(x)

def _get(d, key):
    if not isinstance(d, dict): return ""
    try:
        for k in (key, key.lower(), key.upper()):
            if k in d: return _norm(d.get(k))
    except (AttributeError, TypeError):
        pass
    return ""

# ---------- Security: verify X-Hub-Signature-256 ----------
def _signature_ok(raw: bytes) -> bool:
    secret = _app_secret()
    if not secret:
        # If no app secret configured, skip signature check (not recommended for prod)
        return True
    header = (
        frappe.request.headers.get("X-Hub-Signature-256") or
        frappe.request.headers.get("X-Hub-Signature")
    )
    if not header:
        return False
    # header format: "sha256=hex"
    try:
        algo, received = header.split("=", 1)
    except ValueError:
        return False
    if algo.lower() != "sha256":
        return False
    expected = hmac.new(secret.encode(), raw or b"", hashlib.sha256).hexdigest()
    # constant-time compare
    return hmac.compare_digest(received, expected)

# ---------- Optional Graph helpers ----------
GRAPH_BASE = "https://graph.facebook.com"

def _graph_get(path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # --- START: Temporary Simulation Logic ---
    if frappe.conf.get("simulate_meta_api"):
        # Never let logging kill the simulation
        try:
            frappe.logger("meta_sim").info(f"Simulating API call for path: {path}")
        except Exception:
            pass

        # Simulated lead fetch
        if "fake_lead_789" in str(path):
            return {
                "field_data": [
                    {"name": "first_name", "values": ["John"]},
                    {"name": "email", "values": ["john.doe.test@example.com"]},
                    {"name": "phone_number", "values": ["+1234567890"]},
                    {"name": "custom_question_1", "values": ["Answer to question 1"]},
                ],
                "created_time": 1756212794,
                "ad_id": "fake_ad_id_from_api",
                "form_id": "fake_form_456",
            }

        # Simulated form fetch
        if "fake_form_456" in str(path):
            return {
                "name": "My Test Lead Form",
                "questions": [
                    {"key": "first_name", "label": "What is your first name?"},
                    {"key": "email", "label": "What is your email?"},
                    {"key": "phone_number", "label": "What is your phone number?"},
                    {"key": "custom_question_1", "label": "This is my custom question"},
                ],
            }

        # Return empty dict (not None) so callers don't think it failed
        return {}
    # --- END: Temporary Simulation Logic ---
    if not requests:
        return None
    url = f"{GRAPH_BASE}/{_graph_ver()}{path}"
    q = dict(params or {})
    tok = _access_token()
    if not tok:
        return None
    q["access_token"] = tok
    try:
        r = requests.get(url, params=q, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def _fetch_form_meta(form_id: str) -> tuple[str, str]:
    
    if not form_id:
        return "", ""
    info = _graph_get(f"/{form_id}", {"fields": "name,questions"})
    if not info:
        return "", ""
    form_name = _norm(info.get("name"))
    questions = info.get("questions") or []
    try:
        questions_json = frappe.as_json(questions, indent=0)
    except Exception:
        questions_json = json.dumps(questions, separators=(",", ":"))
    return form_name, questions_json

def _fetch_lead_info(leadgen_id: str) -> Optional[Dict[str, Any]]:
    """Fetches the complete lead object from the Graph API using its ID."""
    if not leadgen_id:
        return None
    # This call is handled by the real API in production and our mock in testing
    return _graph_get(f"/{leadgen_id}", {"fields": "field_data,created_time,ad_id,form_id"})

# ---------- Insert into staging ----------
def _insert_staging(rec: Dict[str, Any]) -> str:
    # Map into CRM Meta Ads Lead
    doc = frappe.get_doc({
        "doctype": "CRM Meta Ads Lead",
        "first_name":      _get(rec, "first_name"),
        "mobile_no":       _get(rec, "mobile_no"),
        "ad_account_id":   _get(rec, "ad_account_id"),
        "email":           _get(rec, "email"),
        "campaign_name":   _get(rec, "campaign_name"),
        "adset_name":      _get(rec, "adset_name"),
        "ad_name":         _get(rec, "ad_name"),
        "page_id":         _get(rec, "page_id"),
        "leadgen_id":      _get(rec, "leadgen_id"),
        "form_id":         _get(rec, "form_id"),
        "form_name":       _get(rec, "form_name"),
        "form_questions":  rec.get("form_questions") or "",
        "field_data":      rec.get("field_data") or "",
        "ad_id":           _get(rec, "ad_id"),
        "adgroup_id":      _get(rec, "adgroup_id"),
        "adset_id":        _get(rec, "adset_id"),
        "campaign_id":     _get(rec, "campaign_id"),
        "created_time":    rec.get("created_time") or None,
        "raw_payload":     rec.get("raw_payload") or "",
        "source_ip":       frappe.request.headers.get("X-Forwarded-For") or frappe.request.remote_addr,
        "processed":       rec.get("processed", 0),  # Default to 0 (False)
        "processed_on":    rec.get("processed_on") or None,
        "target_lead":     _get(rec, "target_lead"),  # Link to CRM Lead
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name

# ---------- Webhook entrypoint ----------
@frappe.whitelist(allow_guest=True)
def meta_leads_webhook():
    """
    GET: verification
    POST: accepts webhook, fetches full lead details from Graph API, and saves to staging.
    """
    if frappe.request.method == "GET":
        # Your existing GET request logic for verification is correct and remains unchanged.
        args = frappe.form_dict or {}
        mode      = _get(args, "hub.mode").lower()
        token     = _get(args, "hub.verify_token")
        challenge = _get(args, "hub.challenge")
        dbg       = _get(args, "debug") == "1"

        if mode == "subscribe" and token == _verify_token() and challenge:
            fr = frappe.response
            fr["type"]     = "txt"
            fr["result"]   = challenge
            fr["filename"] = "meta_webhook.txt"
            fr["doctype"]  = "MetaWebhook"
            return

        frappe.response["type"] = "json"
        if dbg:
            frappe.response["message"] = {
                "ok": False, "error": "Verification failed",
                "why": {"mode": mode, "has_challenge": bool(challenge), "token_match": (token == _verify_token())}
            }
        else:
            frappe.response["message"] = {"ok": False, "error": "Verification failed"}
        return

    # POST processing starts here
    raw = frappe.request.data or b""
    if not _signature_ok(raw):
        frappe.local.response["http_status_code"] = 403
        frappe.response["type"] = "json"
        frappe.response["message"] = {"ok": False, "error": "Invalid signature"}
        return

    payload = frappe.request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        payload = {}

    inserted = []

    # --- CHANGE 1: This entire `save_record` function is new and improved ---
    # It now fetches, parses, and consolidates all data before saving.
    def save_record(rec: Dict[str, Any], raw_json: str):
        try:
            # 1. Fetch Form Info using form_id
            if not rec.get("form_name") and rec.get("form_id"):
                form_name, questions_json = _fetch_form_meta(rec["form_id"])
                if form_name: rec["form_name"] = form_name
                if questions_json: rec["form_questions"] = questions_json

            # 2. Fetch full Lead Info using leadgen_id
            lead_info = _fetch_lead_info(rec.get("leadgen_id")) if rec.get("leadgen_id") else None

            # 3. Parse and consolidate data from the API call
            if lead_info:
                rec["created_time"] = lead_info.get("created_time") or rec.get("created_time")
                rec["ad_id"] = lead_info.get("ad_id") or rec.get("ad_id")
                
                field_data = lead_info.get("field_data")
                if field_data and isinstance(field_data, list):
                    try:
                        rec["field_data"] = frappe.as_json(field_data)
                        # Parse field_data to populate main fields
                        for field in field_data:
                            name = field.get("name", "").lower()
                            value = (field.get("values") or [""])[0]
                            if not value: continue

                            if name == "first_name": rec["first_name"] = value
                            elif name in ("phone_number", "mobile_no"): rec["mobile_no"] = value
                            elif name in ("email", "e-mail"): rec["email"] = value
                    except Exception as e:
                        frappe.log_error(f"Meta field_data parsing failed: {e}", "Meta Integration Error")

            # 4. Save the final, complete record
            rec["raw_payload"] = raw_json
            inserted.append(_insert_staging(rec))
        except Exception as e:
            frappe.log_error(f"Meta save_record failed: {str(e)}, Record: {rec}", "Meta Integration Error")
            raise

    raw_json_str = frappe.as_json(payload)

    try:
        # --- CHANGE 2: The payload handling is now cleaner ---
        if "entry" in payload:
            for entry in (payload.get("entry") or []):
                for change in (entry.get("changes") or []):
                    if _get(change, "field") != "leadgen": continue
                    val = change.get("value") or {}
                    # Create a minimal record from the webhook payload
                    rec = {k: _get(val, k) for k in ["leadgen_id", "form_id", "ad_id", "adset_id", "campaign_id", "created_time"]}
                    rec["page_id"] = _get(entry, "id")
                    save_record(rec, raw_json_str)
        else:
            # Handle simple test payloads
            rec = {k: _get(payload, k) for k in ["first_name", "mobile_no", "email", "campaign_name", "adset_name", "ad_name", "page_id", "leadgen_id", "form_id", "ad_id", "adset_id", "campaign_id", "created_time"]}
            save_record(rec, raw_json_str)

        frappe.response["type"] = "json"
        frappe.response["message"] = {"ok": True, "inserted": inserted, "count": len(inserted)}

    except Exception as e:
        frappe.log_error(f"Meta webhook processing failed: {str(e)}, Payload: {payload}", "Meta Integration Error")
        frappe.response["type"] = "json"
        frappe.response["message"] = {"ok": False, "error": f"Processing failed: {str(e)}"}
        return
