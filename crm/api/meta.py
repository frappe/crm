import frappe
import hmac, hashlib
import json
from typing import Any, Dict, Optional, Tuple
from frappe.utils.password import get_decrypted_password

try:
    import requests  # whitelisted RPCs can import stdlib + installed deps
except Exception:
    requests = None

# ---------- Config helpers ----------
def _conf(key: str, default: str = "") -> str:
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
    try:
        doctype_val = get_decrypted_password(
            "Meta Integration Settings",
            "Meta Integration Settings",
            "meta_app_secret",
            raise_exception=False,
        )
        if doctype_val:
            return doctype_val.strip()
    except Exception:
        pass
    return (frappe.conf.get("meta_app_secret") or "").strip()

def _graph_ver() -> str:            return _conf("meta_graph_api_version", "v23.0")
def _access_token() -> str:         return _conf("meta_access_token")

def _system_user_access_token() -> str:
    try:
        tok = get_decrypted_password(
            "Meta Integration Settings",
            "Meta Integration Settings",
            "meta_access_token",
            raise_exception=False,
        ) or ""
        return tok.strip()
    except Exception:
        return (_access_token() or "").strip()

def _norm(x):
    if x is None:
        return ""
    return x.strip() if isinstance(x, str) else str(x)

def _get(d, key):
    if not isinstance(d, dict):
        return ""
    try:
        for k in (key, key.lower(), key.upper()):
            if k in d:
                return _norm(d.get(k))
    except (AttributeError, TypeError):
        pass
    return ""

# ---------- Security: verify X-Hub-Signature-256 ----------
def _signature_ok(raw: bytes) -> bool:
    secret = _app_secret()
    if not secret:
        # Not recommended for prod, but don't block tests
        return True
    header = (
        frappe.request.headers.get("X-Hub-Signature-256")
        or frappe.request.headers.get("X-Hub-Signature")
    )
    if not header:
        return False
    try:
        algo, received = header.split("=", 1)
    except ValueError:
        return False
    if algo.lower() != "sha256":
        return False
    expected = hmac.new(secret.encode(), raw or b"", hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)

# ---------- Graph helpers ----------
GRAPH_BASE = "https://graph.facebook.com"

def _graph_get(path: str, params: Dict[str, Any]):
    if not requests:
        return {"error": {"message": "requests not available"}}

    path = path if path.startswith("/") else f"/{path}"
    url = f"https://graph.facebook.com/{_graph_ver()}{path}"

    tok = _system_user_access_token()
    if not tok:
        return {"error": {"message": "Missing system user access token"}}

    headers = {"Authorization": f"Bearer {tok}", "Accept": "application/json"}
    q = dict(params or {})

    try:
        r = requests.get(url, params=q, headers=headers, timeout=20)
        try:
            data = r.json() if r.content else {}
        except Exception:
            data = {"raw": r.text}

        if r.status_code != 200:
            frappe.log_error(
                f"Graph GET {r.status_code}: {data} | url={url} | params={q}",
                "Meta Integration Error"
            )
        return data
    except Exception as e:
        frappe.log_error(
            f"Graph GET exception: {e} | url={url} | params={q}",
            "Meta Integration Error"
        )
        return {"error": {"message": str(e)}}



def _fetch_form_meta(form_id: str) -> Tuple[str, str]:
    if not form_id:
        return "", ""
    info = _graph_get(f"/{form_id}", {"fields": "name,questions"})
    if not info or "error" in info:
        return "", ""
    form_name = _norm(info.get("name"))
    questions = info.get("questions") or []
    try:
        questions_json = frappe.as_json(questions, indent=0)
    except Exception:
        questions_json = json.dumps(questions, separators=(",", ":"))
    return form_name, questions_json

def _fetch_lead_info(leadgen_id: str):
    if not leadgen_id:
        return {"error": {"message": "empty leadgen_id"}}
    fields = "field_data,created_time,ad_id,adset_id,campaign_id,form_id"
    return _graph_get(f"/{leadgen_id}", {"fields": fields})


def fetch_ad_account_id(leadgen_id: str):
    
    if not requests:
        return {"error": {"message": "requests not available"}}
    
    if not leadgen_id:
        return {"error": {"message": "leadgen_id is required"}}
    
    try:
        # Step 1: Get lead info to extract ad_id
        lead_info = _fetch_lead_info(leadgen_id)
        
        if not lead_info or "error" in lead_info:
            error_msg = lead_info.get("error", {}).get("message", "Unknown error") if lead_info else "No data returned"
            return {"error": {"message": f"Failed to fetch lead info: {error_msg}"}}
        
        ad_id = lead_info.get("ad_id")
        if not ad_id:
            return {"error": {"message": f"No ad_id found in lead {leadgen_id}"}}
        
        # Step 2: Get ad account info using ad_id
        ad_info = _graph_get(f"/{ad_id}", {"fields": "account_id,name"})
        
        if not ad_info or "error" in ad_info:
            error_msg = ad_info.get("error", {}).get("message", "Unknown error") if ad_info else "No data returned"
            return {"error": {"message": f"Failed to fetch ad info for ad_id {ad_id}: {error_msg}"}}
        
        # Step 3: Extract account_id from response
        account_id = ad_info.get("account_id")
        ad_name = ad_info.get("name")
        
        if not account_id:
            return {"error": {"message": f"No account_id found in ad {ad_id}"}}
        
        return {
            "success": True,
            "leadgen_id": leadgen_id,
            "ad_id": ad_id,
            "ad_name": ad_name,
            "ad_account_id": account_id
        }
        
    except Exception as e:
        frappe.log_error(
            f"fetch_ad_account_id failed for leadgen_id {leadgen_id}: {str(e)}",
            "Meta Integration Error"
        )
        return {"error": {"message": f"Processing failed: {str(e)}"}}



def fetch_meta_accounts():
    if not requests:
        return {"error": {"message": "requests not available"}}
    
    # Get user access token (not system user token)
    user_token = _system_user_access_token()
    if not user_token:
        return {"error": {"message": "Missing user access token in Meta Integration Settings. Please set meta_user_access_token field."}}
    
    url = f"https://graph.facebook.com/{_graph_ver()}/me/accounts"
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Accept": "application/json"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=20)
        try:
            data = r.json() if r.content else {}
        except Exception:
            data = {"raw": r.text}
        
        if r.status_code != 200:
            frappe.log_error(
                f"Meta Accounts GET {r.status_code}: {data} | url={url}",
                "Meta Integration Error"
            )
            return {"error": {"message": f"HTTP {r.status_code}", "details": data}}
        
        return data
        
    except Exception as e:
        frappe.log_error(
            f"Meta Accounts GET exception: {e} | url={url}",
            "Meta Integration Error"
        )
        return {"error": {"message": str(e)}}


def fetch_page_leadgen_forms(page_id: str, page_access_token: str):
    if not requests:
        return {"error": {"message": "requests not available"}}
    
    if not page_id:
        return {"error": {"message": "page_id is required"}}
    
    if not page_access_token:
        return {"error": {"message": "page_access_token is required"}}
    
    url = f"https://graph.facebook.com/{_graph_ver()}/{page_id}/leadgen_forms"
    headers = {
        "Authorization": f"Bearer {page_access_token}",
        "Accept": "application/json"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=20)
        try:
            data = r.json() if r.content else {}
        except Exception:
            data = {"raw": r.text}
        
        if r.status_code != 200:
            frappe.log_error(
                f"Meta Leadgen Forms GET {r.status_code}: {data} | url={url}",
                "Meta Integration Error"
            )
            return {"error": {"message": f"HTTP {r.status_code}", "details": data}}
        
        return data
        
    except Exception as e:
        frappe.log_error(
            f"Meta Leadgen Forms GET exception: {e} | url={url}",
            "Meta Integration Error"
        )
        return {"error": {"message": str(e)}}


def fetch_all_page_leadgen_forms():
    try:
        # Step 1: Get all Meta accounts/pages
        accounts_result = fetch_meta_accounts()
        
        if "error" in accounts_result:
            return {"success": False, "error": f"Failed to fetch accounts: {accounts_result['error']['message']}"}
        
        pages_data = accounts_result.get("data", [])
        if not pages_data:
            return {"success": False, "error": "No pages found in your Meta account"}
        
        # Step 2: For each page, fetch its leadgen forms
        all_forms = {}
        errors = []
        
        for page in pages_data:
            page_id = page.get("id")
            page_name = page.get("name")
            page_access_token = page.get("access_token")
            
            if not page_id or not page_access_token:
                errors.append(f"Missing data for page: {page_name}")
                continue
            
            # Fetch leadgen forms for this page
            forms_result = fetch_page_leadgen_forms(page_id, page_access_token)
            
            if "error" in forms_result:
                errors.append(f"Failed to fetch forms for page '{page_name}' ({page_id}): {forms_result['error']['message']}")
                all_forms[page_id] = {
                    "page_name": page_name,
                    "page_id": page_id,
                    "error": forms_result["error"]["message"],
                    "forms": []
                }
            else:
                forms_data = forms_result.get("data", [])
                all_forms[page_id] = {
                    "page_name": page_name,
                    "page_id": page_id,
                    "forms_count": len(forms_data),
                    "forms": forms_data
                }
        
        # Step 3: Return comprehensive result
        result = {
            "success": True,
            "total_pages": len(pages_data),
            "pages_with_forms": len([p for p in all_forms.values() if not p.get("error")]),
            "total_forms": sum(p.get("forms_count", 0) for p in all_forms.values()),
            "pages": all_forms
        }
        
        if errors:
            result["errors"] = errors
        
        return result
        
    except Exception as e:
        frappe.log_error(f"fetch_all_page_leadgen_forms failed: {str(e)}", "Meta Integration Error")
        return {"success": False, "error": f"Processing failed: {str(e)}"}


def fetch_form_leads(form_id: str, page_access_token: str):
    
    if not requests:
        return {"error": {"message": "requests not available"}}
    
    if not form_id:
        return {"error": {"message": "form_id is required"}}
    
    if not page_access_token:
        return {"error": {"message": "page_access_token is required"}}
    
    all_leads = []
    next_url = f"https://graph.facebook.com/{_graph_ver()}/{form_id}/leads"
    headers = {
        "Authorization": f"Bearer {page_access_token}",
        "Accept": "application/json"
    }
    
    try:
        while next_url:
            r = requests.get(next_url, headers=headers, timeout=20)
            try:
                data = r.json() if r.content else {}
            except Exception:
                data = {"raw": r.text}
            
            if r.status_code != 200:
                frappe.log_error(
                    f"Meta Form Leads GET {r.status_code}: {data} | url={next_url}",
                    "Meta Integration Error"
                )
                return {"error": {"message": f"HTTP {r.status_code}", "details": data}}
            
            # Add current page leads to the collection
            current_leads = data.get("data", [])
            all_leads.extend(current_leads)
            
            # Check for next page
            paging = data.get("paging", {})
            next_url = paging.get("next")
            
            # Safety break to prevent infinite loops (optional)
            if len(all_leads) > 10000:  # Adjust limit as needed
                frappe.log_error(
                    f"Form {form_id} has more than 10000 leads, stopping pagination to prevent issues",
                    "Meta Integration Warning"
                )
                break
        
        # Return data in the same format as the original API
        return {
            "data": all_leads,
            "total_count": len(all_leads),
            "paginated": True
        }
        
    except Exception as e:
        frappe.log_error(
            f"Meta Form Leads GET exception: {e} | url={next_url}",
            "Meta Integration Error"
        )
        return {"error": {"message": str(e)}}


def fetch_all_leads():
    
    try:
        # Step 1: Get all forms from all pages
        forms_result = fetch_all_page_leadgen_forms()
        
        if not forms_result.get("success"):
            return {"success": False, "error": f"Failed to fetch forms: {forms_result.get('error', 'Unknown error')}"}
        
        pages_data = forms_result.get("pages", {})
        if not pages_data:
            return {"success": False, "error": "No pages with forms found"}
        
        # Step 2: For each page and form, fetch leads
        all_leads = {}
        errors = []
        total_leads_count = 0
        
        for page_id, page_info in pages_data.items():
            page_name = page_info.get("page_name")
            forms = page_info.get("forms", [])
            
            if page_info.get("error"):
                errors.append(f"Page '{page_name}' had form fetch error: {page_info['error']}")
                continue
            
            # Get page access token from accounts (we need to call fetch_meta_accounts again)
            accounts_result = fetch_meta_accounts()
            if "error" in accounts_result:
                errors.append(f"Could not get access token for page '{page_name}': {accounts_result['error']['message']}")
                continue
            
            # Find the page access token
            page_access_token = None
            for account in accounts_result.get("data", []):
                if account.get("id") == page_id:
                    page_access_token = account.get("access_token")
                    break
            
            if not page_access_token:
                errors.append(f"Could not find access token for page '{page_name}' ({page_id})")
                continue
            
            page_leads = {}
            
            for form in forms:
                form_id = form.get("id")
                form_name = form.get("name", f"Form {form_id}")
                
                if not form_id:
                    errors.append(f"Form missing ID in page '{page_name}'")
                    continue
                
                # Fetch leads for this form
                leads_result = fetch_form_leads(form_id, page_access_token)
                
                if "error" in leads_result:
                    errors.append(f"Failed to fetch leads for form '{form_name}' ({form_id}): {leads_result['error']['message']}")
                    page_leads[form_id] = {
                        "form_name": form_name,
                        "form_id": form_id,
                        "error": leads_result["error"]["message"],
                        "leads": [],
                        "leads_count": 0
                    }
                else:
                    leads_data = leads_result.get("data", [])
                    leads_count = len(leads_data)
                    total_leads_count += leads_count
                    
                    page_leads[form_id] = {
                        "form_name": form_name,
                        "form_id": form_id,
                        "leads_count": leads_count,
                        "leads": leads_data
                    }
            
            all_leads[page_id] = {
                "page_name": page_name,
                "page_id": page_id,
                "forms_count": len(forms),
                "total_leads_in_page": sum(form_data.get("leads_count", 0) for form_data in page_leads.values()),
                "forms": page_leads
            }
        
        # Step 3: Return comprehensive result
        result = {
            "success": True,
            "total_pages": len(pages_data),
            "total_forms": sum(page_data.get("forms_count", 0) for page_data in all_leads.values()),
            "total_leads": total_leads_count,
            "pages": all_leads
        }
        
        if errors:
            result["errors"] = errors
        
        return result
        
    except Exception as e:
        frappe.log_error(f"fetch_all_leads failed: {str(e)}", "Meta Integration Error")
        return {"success": False, "error": f"Processing failed: {str(e)}"}

@frappe.whitelist()
def push_to_stagging():
    
    try:
        # Step 1: Get all leads from all forms
        all_leads_result = fetch_all_leads()
        
        if not all_leads_result.get("success"):
            return {"success": False, "error": f"Failed to fetch leads: {all_leads_result.get('error', 'Unknown error')}"}
        
        pages_data = all_leads_result.get("pages", {})
        if not pages_data:
            return {"success": False, "error": "No pages with leads found"}
        
        # Step 2: Collect all unique leadgen_ids
        all_leadgen_ids = set()
        total_leads_found = 0
        
        for page_id, page_info in pages_data.items():
            forms_data = page_info.get("forms", {})
            for form_id, form_info in forms_data.items():
                if form_info.get("error"):
                    continue
                leads = form_info.get("leads", [])
                for lead in leads:
                    leadgen_id = lead.get("id")
                    if leadgen_id:
                        all_leadgen_ids.add(leadgen_id)
                        total_leads_found += 1
        
        if not all_leadgen_ids:
            return {"success": False, "error": "No leads with valid leadgen_id found"}
        
        # Step 3: Check for existing records to avoid duplicates
        existing_leadgen_ids = set()
        try:
            existing_records = frappe.db.get_all(
                "CRM Meta Lead Stagging",
                fields=["leadgen_id"],
                filters={"leadgen_id": ["in", list(all_leadgen_ids)]}
            )
            existing_leadgen_ids = {record["leadgen_id"] for record in existing_records}
        except Exception as e:
            frappe.log_error(f"Error checking existing records: {str(e)}", "Meta Integration Warning")
            # Continue without duplicate check if DB query fails
        
        # Step 4: Filter out duplicates
        new_leadgen_ids = all_leadgen_ids - existing_leadgen_ids
        
        if not new_leadgen_ids:
            return {
                "success": True,
                "message": "All leads already exist in staging table",
                "total_leads_found": total_leads_found,
                "duplicates_skipped": len(existing_leadgen_ids),
                "new_leads_processed": 0,
                "inserted": [],
                "errors": []
            }
        
        # Step 5: Process each new lead
        inserted = []
        errors = []
        processed_count = 0
        
        for leadgen_id in new_leadgen_ids:
            processed_count += 1
            
            try:
                # Fetch detailed lead info
                lead_info = _fetch_lead_info(leadgen_id)
                
                if not lead_info or "error" in lead_info:
                    error_msg = lead_info.get("error", {}).get("message", "Unknown error") if lead_info else "No data returned"
                    errors.append(f"Failed to fetch details for lead {leadgen_id}: {error_msg}")
                    continue
                
                # Prepare record for insertion
                rec = {
                    "leadgen_id": leadgen_id,
                    "created_time": frappe.utils.now(),  # Use current timestamp
                    "ad_id": lead_info.get("ad_id"),
                    "adset_id": lead_info.get("adset_id"),
                    "campaign_id": lead_info.get("campaign_id"),
                    "form_id": lead_info.get("form_id"),
                }
                
                # Fetch ad account ID using the leadgen_id
                try:
                    ad_account_result = fetch_ad_account_id(leadgen_id)
                    if ad_account_result.get("success") and ad_account_result.get("ad_account_id"):
                        rec["ad_account_id"] = ad_account_result["ad_account_id"]
                        # Also update ad_name if available
                        if ad_account_result.get("ad_name"):
                            rec["ad_name"] = ad_account_result["ad_name"]
                except Exception as e:
                    frappe.log_error(f"Failed to fetch ad_account_id for lead {leadgen_id}: {str(e)}", "Meta Integration Warning")
                    # Continue without ad_account_id if fetch fails
                
                # Fetch form metadata if form_id is available
                if rec.get("form_id"):
                    form_name, questions_json = _fetch_form_meta(rec["form_id"])
                    if form_name:
                        rec["form_name"] = form_name
                    if questions_json:
                        rec["form_questions"] = questions_json
                
                # Parse field_data to extract core fields
                field_data = lead_info.get("field_data")
                if field_data and isinstance(field_data, list):
                    try:
                        rec["field_data"] = frappe.as_json(field_data)
                        for field in field_data:
                            name = (field.get("name") or "").lower()
                            value = (field.get("values") or [""])[0]
                            if not value:
                                continue
                            if name in ("full_name", "first_name", "name"):
                                rec["first_name"] = rec.get("first_name") or value
                            elif name in ("phone_number", "mobile_no", "phone"):
                                rec["mobile_no"] = rec.get("mobile_no") or value
                            elif name in ("email", "e-mail"):
                                rec["email"] = rec.get("email") or value
                    except Exception as e:
                        frappe.log_error(f"Meta field_data parsing failed for {leadgen_id}: {e}", "Meta Integration Error")
                
                # Add raw payload for debugging
                rec["raw_payload"] = frappe.as_json(lead_info)
                
                # Insert into staging table
                doc_name = _insert_staging_stg(rec)
                inserted.append({
                    "leadgen_id": leadgen_id,
                    "doc_name": doc_name
                })
                
            except Exception as e:
                error_msg = f"Failed to process lead {leadgen_id}: {str(e)}"
                errors.append(error_msg)
                frappe.log_error(error_msg, "Meta Integration Error")
                continue
        
        # Step 6: Return comprehensive result
        result = {
            "success": True,
            "total_leads_found": total_leads_found,
            "unique_leads_found": len(all_leadgen_ids),
            "duplicates_skipped": len(existing_leadgen_ids),
            "new_leads_processed": len(new_leadgen_ids),
            "successfully_inserted": len(inserted),
            "failed_insertions": len(errors),
            # "inserted": inserted
        }
        
        if errors:
            result["errors"] = errors
        
        # Add summary message
        if len(inserted) > 0:
            result["message"] = f"Successfully processed {len(inserted)} new leads into staging table"
        else:
            result["message"] = "No new leads were processed"
        
        return result
        
    except Exception as e:
        frappe.log_error(f"push_to_stagging failed: {str(e)}", "Meta Integration Error")
        return {"success": False, "error": f"Processing failed: {str(e)}"}

# ---------- Insert into CRM Meta Lead ----------
def _insert_staging(rec: Dict[str, Any]) -> str:
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
        "processed":       rec.get("processed", 0),
        "processed_on":    rec.get("processed_on") or None,
        "target_lead":     _get(rec, "target_lead"),
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name

# ---------- Insert into CRM stg ----------
def _insert_staging_stg(rec: Dict[str, Any]) -> str:
    """Insert record into CRM Meta Ads Lead Stg doctype"""
    
    # Safely get source IP - handle cases where frappe.request is not available
    source_ip = ""
    try:
        if hasattr(frappe, 'request') and frappe.request:
            source_ip = frappe.request.headers.get("X-Forwarded-For") or frappe.request.remote_addr or ""
    except Exception:
        source_ip = ""
    
    doc = frappe.get_doc({
        "doctype": "CRM Meta Lead Stagging",
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
        "source_ip":       source_ip,
        "processed":       rec.get("processed", 0),
        "processed_on":    rec.get("processed_on") or None,
        "target_lead":     _get(rec, "target_lead"),
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name


def fetch_and_insert_to_staging(leadgen_id: str, **kwargs) -> Dict[str, Any]:

    if not leadgen_id:
        return {"success": False, "error": "leadgen_id is required"}
    
    try:
        # 1) Fetch lead info from Meta Graph API
        lead_info = _fetch_lead_info(leadgen_id)
        
        if not lead_info or "error" in lead_info:
            error_msg = lead_info.get("error", {}).get("message", "Unknown error") if lead_info else "No data returned"
            return {"success": False, "error": f"Failed to fetch lead info: {error_msg}"}
        
        # 2) Prepare record for insertion
        rec = {
            "leadgen_id": leadgen_id,
            "created_time": frappe.utils.now(),  # Use current timestamp instead of Meta's created_time
            "ad_id": lead_info.get("ad_id"),
            "adset_id": lead_info.get("adset_id"),
            "campaign_id": lead_info.get("campaign_id"),
            "form_id": lead_info.get("form_id"),
        }
        
        # 3) Add any additional fields passed as kwargs
        for key, value in kwargs.items():
            if key not in rec:  # Don't override Graph API data
                rec[key] = value
        
        # 4) Fetch form metadata if form_id is available
        if rec.get("form_id"):
            form_name, questions_json = _fetch_form_meta(rec["form_id"])
            if form_name:
                rec["form_name"] = form_name
            if questions_json:
                rec["form_questions"] = questions_json
        
        # 5) Parse field_data to extract core fields
        field_data = lead_info.get("field_data")
        if field_data and isinstance(field_data, list):
            try:
                rec["field_data"] = frappe.as_json(field_data)
                for field in field_data:
                    name = (field.get("name") or "").lower()
                    value = (field.get("values") or [""])[0]
                    if not value:
                        continue
                    if name in ("full_name", "first_name", "name"):
                        rec["first_name"] = rec.get("first_name") or value
                    elif name in ("phone_number", "mobile_no", "phone"):
                        rec["mobile_no"] = rec.get("mobile_no") or value
                    elif name in ("email", "e-mail"):
                        rec["email"] = rec.get("email") or value
            except Exception as e:
                frappe.log_error(f"Meta field_data parsing failed: {e}", "Meta Integration Error")
        
        # 6) Add raw payload for debugging
        rec["raw_payload"] = frappe.as_json(lead_info)
        
        # 7) Insert into staging table
        doc_name = _insert_staging_stg(rec)
        
        return {
            "success": True, 
            "doc_name": doc_name,
            "leadgen_id": leadgen_id,
            "message": f"Lead {leadgen_id} successfully inserted into staging table"
        }
        
    except Exception as e:
        frappe.log_error(f"fetch_and_insert_lead_to_staging failed: {str(e)}, leadgen_id: {leadgen_id}", "Meta Integration Error")
        return {"success": False, "error": f"Processing failed: {str(e)}"}

# ---------- Webhook entrypoint ----------
@frappe.whitelist(allow_guest=True)
def meta_leads_webhook():
    
    if frappe.request.method == "GET":
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

    # POST
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

    def save_record(rec: Dict[str, Any], raw_json: str):
        try:
            # 1) Form meta
            if not rec.get("form_name") and rec.get("form_id"):
                form_name, questions_json = _fetch_form_meta(rec["form_id"])
                if form_name:
                    rec["form_name"] = form_name
                if questions_json:
                    rec["form_questions"] = questions_json

            # 2) Lead details (mirror Postman)
            lead_info = _fetch_lead_info(rec.get("leadgen_id")) if rec.get("leadgen_id") else None

            # 3) Merge fields
            if lead_info and "error" not in lead_info:
                rec["created_time"] = lead_info.get("created_time") or rec.get("created_time")
                # Prefer Graph values
                for k in ("ad_id", "adset_id", "campaign_id", "form_id"):
                    if lead_info.get(k):
                        rec[k] = lead_info.get(k)

                # Fetch ad account ID using the leadgen_id
                try:
                    if rec.get("leadgen_id"):
                        ad_account_result = fetch_ad_account_id(rec["leadgen_id"])
                        if ad_account_result.get("success") and ad_account_result.get("ad_account_id"):
                            rec["ad_account_id"] = ad_account_result["ad_account_id"]
                            # Also update ad_name if available
                            if ad_account_result.get("ad_name"):
                                rec["ad_name"] = ad_account_result["ad_name"]
                except Exception as e:
                    frappe.log_error(f"Webhook: Failed to fetch ad_account_id for lead {rec.get('leadgen_id')}: {str(e)}", "Meta Integration Warning")
                    # Continue without ad_account_id if fetch fails

                # Field data -> parse core fields
                field_data = lead_info.get("field_data")
                if field_data and isinstance(field_data, list):
                    try:
                        rec["field_data"] = frappe.as_json(field_data)
                        for field in field_data:
                            name = (field.get("name") or "").lower()
                            value = (field.get("values") or [""])[0]
                            if not value:
                                continue
                            if name in ("full_name", "first_name", "name"):
                                rec["first_name"] = rec.get("first_name") or value
                            elif name in ("phone_number", "mobile_no", "phone"):
                                rec["mobile_no"] = rec.get("mobile_no") or value
                            elif name in ("email", "e-mail"):
                                rec["email"] = rec.get("email") or value
                    except Exception as e:
                        frappe.log_error(f"Meta field_data parsing failed: {e}", "Meta Integration Error")
            else:
                if lead_info and "error" in lead_info:
                    frappe.log_error(f"Lead fetch error for {rec.get('leadgen_id')}: {lead_info}", "Meta Integration Error")

            # 4) Save to both staging tables
            rec["raw_payload"] = raw_json
            
            # Insert into CRM Meta Ads Lead (original staging)
            main_doc_name = _insert_staging(rec)
            inserted.append(main_doc_name)
            
            # insert into Meta Lead Stg
            try:
                stg_rec = rec.copy()
                stg_rec["created_time"] = frappe.utils.now()  # Use current time for staging
                stg_doc_name = _insert_staging_stg(stg_rec)
                frappe.log_error(f"Lead {rec.get('leadgen_id')} also inserted into staging table: {stg_doc_name}", "Meta Integration Success")
            except Exception as stg_error:
                # Log error but don't fail the main process
                frappe.log_error(f"Failed to insert into staging table: {str(stg_error)}, Record: {rec}", "Meta Integration Warning")
                
        except Exception as e:
            frappe.log_error(f"Meta save_record failed: {str(e)}, Record: {rec}", "Meta Integration Error")
            raise

    raw_json_str = frappe.as_json(payload)

    def sync_missing_leads():
        
        try:
            # Get all leadgen_ids from CRM Meta Ads Lead
            main_leads = frappe.db.get_all(
                "CRM Meta Ads Lead",
                fields=["leadgen_id"],
                filters={"leadgen_id": ["!=", ""]}
            )
            main_leadgen_ids = {record["leadgen_id"] for record in main_leads if record.get("leadgen_id")}
            
            if not main_leadgen_ids:
                return {"status": "no_leads", "message": "No leads found in CRM Meta Ads Lead"}
            
            # Get all leadgen_ids from CRM Meta Lead Stagging
            staging_leads = frappe.db.get_all(
                "CRM Meta Lead Stagging",
                fields=["leadgen_id"],
                filters={"leadgen_id": ["in", list(main_leadgen_ids)]}
            )
            staging_leadgen_ids = {record["leadgen_id"] for record in staging_leads if record.get("leadgen_id")}
            
            # Find missing leads
            missing_leadgen_ids = main_leadgen_ids - staging_leadgen_ids
            
            if not missing_leadgen_ids:
                return {
                    "status": "synchronized", 
                    "message": f"All {len(main_leadgen_ids)} leads are already synchronized",
                    "main_count": len(main_leadgen_ids),
                    "staging_count": len(staging_leadgen_ids),
                    "missing_count": 0
                }
            
            # Log the sync operation
            frappe.log_error(
                f"Found {len(missing_leadgen_ids)} leads in CRM Meta Ads Lead that are missing from CRM Meta Lead Stagging. Running sync...",
                "Meta Integration Sync"
            )
            
            sync_result = push_to_stagging()
            
            return {
                "status": "sync_attempted",
                "message": f"Attempted to sync {len(missing_leadgen_ids)} missing leads",
                "main_count": len(main_leadgen_ids),
                "staging_count": len(staging_leadgen_ids),
                "missing_count": len(missing_leadgen_ids),
                "sync_result": sync_result
            }
            
        except Exception as e:
            frappe.log_error(f"sync_missing_leads failed: {str(e)}", "Meta Integration Error")
            return {
                "status": "error",
                "message": f"Sync check failed: {str(e)}"
            }

    try:
        processed_any = False

        if "entry" in payload:
            for entry in (payload.get("entry") or []):
                page_id = _get(entry, "id")
                for change in (entry.get("changes") or []):
                    if _get(change, "field") != "leadgen":
                        continue
                    val = change.get("value") or {}
                    rec = {
                        "first_name":    _get(val, "first_name"),
                        "mobile_no":     _get(val, "phone_number"),
                        "ad_account_id": _get(val, "ad_account_id"),
                        "email":         _get(val, "email"),
                        "campaign_name": "",
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
                    processed_any = True

        elif _get(payload, "field") == "leadgen" and isinstance(payload.get("value"), dict):
            # 2) Meta test tool payload: {"field":"leadgen","value":{...}}
            val = payload.get("value") or {}
            rec = {
                k: _get(val, k)
                for k in ["leadgen_id", "form_id", "ad_id", "adset_id", "campaign_id", "created_time"]
            }
            rec["page_id"] = _get(val, "page_id") or _get(payload, "page_id")
            if not rec.get("leadgen_id"):
                frappe.response["type"] = "json"
                frappe.response["message"] = {"ok": False, "error": "Meta Lead ID (leadgen_id) missing in value{}"}
                return
            save_record(rec, raw_json_str)
            processed_any = True

        else:
            # 3) Simple/manual payload with top-level fields (Postman)
            rec = {
                k: _get(payload, k)
                for k in [
                    "first_name",
                    "mobile_no",
                    "email",
                    "campaign_name",
                    "adset_name",
                    "ad_name",
                    "page_id",
                    "leadgen_id",
                    "form_id",
                    "ad_id",
                    "adset_id",
                    "campaign_id",
                    "created_time",
                ]
            }
            if rec.get("leadgen_id"):
                save_record(rec, raw_json_str)
                processed_any = True

        if not processed_any:
            # Explicit, actionable response for unknown shapes
            frappe.response["type"] = "json"
            frappe.response["message"] = {
                "ok": False,
                "error": "Unsupported payload shape",
                "hint": "Expected: {entry:[{changes:[{field:'leadgen', value:{...}}]}]} OR {field:'leadgen', value:{...}} OR top-level leadgen_id.",
                "received_keys": list(payload.keys()),
            }
            return

        # After processing webhook data, check for missing leads and sync if needed
        sync_results = sync_missing_leads()

        frappe.response["type"] = "json"
        frappe.response["message"] = {
            "ok": True,
            "inserted": inserted,
            "count": len(inserted),
            "sync_check": sync_results,
        }

    except Exception as e:
        frappe.log_error(f"Meta webhook processing failed: {str(e)}, Payload: {payload}", "Meta Integration Error")
        frappe.response["type"] = "json"
        frappe.response["message"] = {"ok": False, "error": f"Processing failed: {str(e)}"}
        return
