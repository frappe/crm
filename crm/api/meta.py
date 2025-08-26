import frappe
import hmac, hashlib
import json
from typing import Any, Dict, List, Optional

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
def _app_secret() -> str:           return _conf("meta_app_secret")
def _graph_ver() -> str:            return _conf("meta_graph_api_version", "v20.0")
def _access_token() -> str:         return _conf("meta_access_token")

def _norm(x):
    if x is None: return ""
    return x.strip() if isinstance(x, str) else str(x)

def _get(d, key):
    if not isinstance(d, dict): return ""
    for k in (key, key.lower(), key.upper()):
        if k in d: return _norm(d.get(k))
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

def _fetch_form_meta(form_id: str) -> (str, str):
    """
    Return (form_name, questions_json) or ("","") if not available.
    """
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

def _fetch_lead_field_data(leadgen_id: str) -> str:
    """
    Return field_data JSON (user answers) or "".
    """
    if not leadgen_id:
        return ""
    info = _graph_get(f"/{leadgen_id}", {"fields": "field_data,created_time,ad_id,form_id"})
    if not info:
        return ""
    field_data = info.get("field_data") or []
    try:
        return frappe.as_json(field_data, indent=0)
    except Exception:
        return json.dumps(field_data, separators=(",", ":"))

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
        "adset_id":        _get(rec, "adset_id"),
        "campaign_id":     _get(rec, "campaign_id"),
        "created_time":    rec.get("created_time") or None,
        "raw_payload":     rec.get("raw_payload") or "",
        "source_ip":       frappe.request.headers.get("X-Forwarded-For") or frappe.request.remote_addr,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name

# ---------- Webhook entrypoint ----------
@frappe.whitelist(allow_guest=True)
def meta_leads_webhook():
    """
    GET: verification (echoes hub.challenge as plain text)
    POST: accepts either Meta's standard webhook structure OR simple JSON,
          verifies signature (if app secret set), then writes each lead to
          'CRM Meta Ads Lead' and returns an ack.
    """
    if frappe.request.method == "GET":
        args = frappe.form_dict or {}
        mode      = _get(args, "hub.mode").lower()
        token     = _get(args, "hub.verify_token")
        challenge = _get(args, "hub.challenge")
        dbg       = _get(args, "debug") == "1"

        if mode == "subscribe" and token == _verify_token() and challenge:
            fr = frappe.response
            # Your stack wants 'txt' plus a 'result' (and often filename)
            fr["type"]     = "txt"
            fr["result"]   = challenge
            fr["filename"] = "meta_webhook.txt"
            fr["doctype"]  = "MetaWebhook"
            return

        frappe.response["type"] = "json"
        if dbg:
            frappe.response["message"] = {
                "ok": False,
                "error": "Verification failed",
                "why": {"mode": mode, "has_challenge": bool(challenge), "token_match": (token == _verify_token())}
            }
        else:
            frappe.response["message"] = {"ok": False, "error": "Verification failed"}
        return

    # POST
    raw = frappe.request.data or b""
    # Signature (optional but recommended in prod)
    if not _signature_ok(raw):
        frappe.local.response["http_status_code"] = 403
        frappe.response["type"] = "json"
        frappe.response["message"] = {"ok": False, "error": "Invalid signature"}
        return

    payload = frappe.request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        payload = {}

    inserted = []

    def save_record(rec: Dict[str, Any], raw_json: str):
        # Fill form_name/questions if possible
        if not rec.get("form_name") and rec.get("form_id"):
            form_name, questions_json = _fetch_form_meta(rec["form_id"])
            if form_name:
                rec["form_name"] = form_name
            if questions_json:
                rec["form_questions"] = questions_json
        # Optionally fetch answers (field_data) from Graph
        if rec.get("leadgen_id") and not rec.get("field_data"):
            fd = _fetch_lead_field_data(rec["leadgen_id"])
            if fd:
                rec["field_data"] = fd
        rec["raw_payload"] = raw_json
        inserted.append(_insert_staging(rec))

    raw_json_str = ""
    try:
        raw_json_str = frappe.as_json(payload, indent=0)
    except Exception:
        try:
            raw_json_str = json.dumps(payload, separators=(",", ":"))
        except Exception:
            raw_json_str = "{}"

    # Case 1: Meta’s official webhook structure (entries/changes)
    if "entry" in payload:
        for entry in (payload.get("entry") or []):
            page_id = _get(entry, "id")
            for change in (entry.get("changes") or []):
                if _get(change, "field") != "leadgen":
                    continue
                val = change.get("value") or {}
                rec = {
                    "first_name":    _get(val, "first_name"),   # may be empty in webhook
                    "mobile_no":     _get(val, "phone_number"),  # may be empty in webhook
                    "ad_account_id": _get(val, "ad_account_id"), # may be empty in webhook
                    "email":         _get(val, "email"),
                    "campaign_name": "",                         # unknown here; optional
                    "adset_name":    "",
                    "ad_name":       "",
                    "page_id":       page_id or _get(val, "page_id"),
                    "leadgen_id":    _get(val, "leadgen_id"),
                    "form_id":       _get(val, "form_id"),
                    "ad_id":         _get(val, "ad_id"),
                    "adset_id":      _get(val, "adset_id"),
                    "campaign_id":   _get(val, "campaign_id"),
                    "created_time":  _get(val, "created_time"),
                }
                save_record(rec, raw_json_str)

    # Case 2: Your simpler JSON (used in Postman/tests)
    else:
        rec = {
            "first_name":    _get(payload, "first_name"),
            "mobile_no":     _get(payload, "mobile_no"),
            "ad_account_id": _get(payload, "ad_account_id"),
            "email":         _get(payload, "email"),
            "campaign_name": _get(payload, "campaign_name") or _get(payload, "campaign"),
            "adset_name":    _get(payload, "adset_name"),
            "ad_name":       _get(payload, "ad_name"),
            "page_id":       _get(payload, "page_id"),
            "leadgen_id":    _get(payload, "lead_id") or _get(payload, "leadgen_id"),
            "form_id":       _get(payload, "form_id"),
            "ad_id":         _get(payload, "ad_id"),
            "adset_id":      _get(payload, "adset_id"),
            "campaign_id":   _get(payload, "campaign_id"),
            "created_time":  _get(payload, "created_time"),
        }
        save_record(rec, raw_json_str)

    frappe.response["type"] = "json"
    frappe.response["message"] = {"ok": True, "inserted": inserted, "count": len(inserted)}
