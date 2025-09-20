import base64
import json
import frappe
import requests
from frappe import _
from werkzeug.wrappers import Response
from frappe.utils import now_datetime, get_datetime, add_to_date
from crm.integrations.api import get_contact_by_phone_number
from .ringcentral_handler import IncomingCall, RingCentral, RingCentralCallDetails
from json import dumps
from frappe import db
from datetime import datetime
from zoneinfo import ZoneInfo
import time
@frappe.whitelist()
def is_enabled():
    """Check if RingCentral integration is enabled."""
    return frappe.db.get_single_value("CRM RingCentral Settings", "enabled")

@frappe.whitelist()
def get_record_calls():
    """Check if automatic call recording is enabled."""
    return frappe.db.get_single_value("CRM RingCentral Settings", "record_calls")

@frappe.whitelist()
def get_webphone_credentials():
    """Returns credentials for RingCentral WebPhone SDK."""
    try:
        ringcentral = RingCentral.connect()
        if not ringcentral:
            frappe.log_error("RingCentral integration not enabled", "RingCentral")
            return {"ok": False, "error": "integration_not_enabled"}
        
        # Check and refresh token if needed
        if ringcentral.settings.token_expiry and now_datetime() >= get_datetime(ringcentral.settings.token_expiry):
            frappe.log_error("Refreshing access token due to expiry", "RingCentral")
            ringcentral.refresh_access_token()
        
        # Validate and clean access token
        access_token = ringcentral.settings.access_token
        if not access_token:
            frappe.log_error("No access token found", "RingCentral")
            return {"ok": False, "error": "invalid_access_token", "detail": "No access token found"}
        
        access_token = access_token.strip() # Remove whitespace
        frappe.log_error("Access token cleaned", f"RingCentral: Cleaned access token: {access_token}")
        
        # Calculate expires_in
        expires_in = None
        if ringcentral.settings.token_expiry:
            expires_in = int((get_datetime(ringcentral.settings.token_expiry) - now_datetime()).total_seconds())
        
        from_number = db.get_value("CRM Telephony Agent", frappe.session.user, "ringcentral_number")
        if not from_number:
            frappe.log_error(f"No ringcentral_number for user {frappe.session.user}", "RingCentral")
            return {
                "ok": False,
                "error": "caller_phone_identity_missing",
                "detail": f"No ringcentral_number found for user {frappe.session.user}"
            }
        
        # Direct POST request with requests library
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        frappe.log_error("Sending SIP provision request", f"RingCentral: Headers: {dumps(headers, indent=2)}")
        response = requests.post(
            f"{ringcentral.server_url}/restapi/v1.0/client-info/sip-provision",
            json={"sipInfo": [{"transport": "WSS"}]},
            headers=headers
        )
        response.raise_for_status()
        sip_response = response.json()
        frappe.log_error("SIP response received", f"RingCentral: {dumps(sip_response, indent=2)}")
        sip_info = sip_response.get('sipInfo', [{}])[0]
        
        if not sip_info.get('username'):
            frappe.log_error("SIP info missing username", "RingCentral")
            return {
                "ok": False,
                "error": "sip_provision_failed",
                "detail": "Failed to retrieve SIP credentials"
            }
        
        return {
            "ok": True,
            "client_id": ringcentral.client_id,
            "client_secret": ringcentral.client_secret,
            "server_url": ringcentral.server_url,
            "token": access_token, # Use access_token as token
            "expires_in": expires_in, # Calculated from token_expiry
            "from_number": from_number,
            "sipInfo": {
                "username": sip_info.get("username"),
                "password": sip_info.get("password"),
                "authorizationId": sip_info.get("authorizationId"),
                "domain": sip_info.get("domain"),
                "outboundProxy": sip_info.get("outboundProxy"),
                "transport": sip_info.get("transport", "WSS")
            }
        }
    except Exception as e:
        frappe.log_error(f"WebPhone Credentials Error: {str(e)}", f"RingCentral: {frappe.get_traceback()}")
        return {"ok": False, "error": str(e), "detail": frappe.get_traceback()}

@frappe.whitelist(allow_guest=True)
def oauth_callback():
    """Handle OAuth callback from RingCentral"""
    code = frappe.form_dict.get('code')
    if not code:
        frappe.log_error("OAuth callback error: No code provided")
        return '<script>window.close();</script>'
    
    try:
        ringcentral = RingCentral.connect()
        if not ringcentral:
            frappe.log_error("OAuth callback error: RingCentral integration not enabled")
            return '<script>alert("RingCentral integration not enabled"); window.close();</script>'
        
        token_url = f"{ringcentral.server_url}/restapi/oauth/token"
        client_id = ringcentral.client_id
        client_secret = ringcentral.client_secret
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": ringcentral.redirect_uri,
        }
        res = requests.post(token_url, data=data, headers=headers)
        if res.status_code != 200:
            frappe.log_error(f"OAuth callback error: Failed to fetch token: {res.text}")
            frappe.throw(_("Failed to fetch token: ") + res.text)
        
        tokens = res.json()
        frappe.log_error(f"OAuth callback success: Token data={tokens}")
        ringcentral.settings.access_token = tokens["access_token"]
        ringcentral.settings.refresh_token = tokens["refresh_token"]
        ringcentral.settings.token_expiry = add_to_date(now_datetime(), seconds=tokens.get("expires_in", 3600))
        ringcentral.settings.save(ignore_permissions=True)
        frappe.db.commit()
        ringcentral.platform.auth().set_data({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens.get("expires_in", 3600)
        })
        return '<script>window.opener.postMessage("OAuth flow completed. You can close this window.", "*"); window.close();</script>'
    except Exception as e:
        frappe.log_error(f"OAuth callback error: {str(e)}")
        return f'<script>alert("Authorization failed: {str(e)}"); window.close();</script>'

@frappe.whitelist()
def get_authorize_url():
    """Get RingCentral authorization URL."""
    try:
        ringcentral = RingCentral.connect()
        if not ringcentral:
            frappe.log_error(title="RingCentral Authorize URL", message="RingCentral integration is not enabled")
            frappe.throw(_("RingCentral integration is not enabled"))
        
        auth_url = ringcentral.get_authorize_url()
        frappe.log_error(title="RingCentral Authorize URL", message=f"Generated URL: {auth_url}")
        return {"authorize_url": auth_url}
    except Exception as e:
        frappe.log_error(title="RingCentral Authorize URL Error", message=f"Failed to get authorize URL: {str(e)}\nStacktrace: {frappe.get_traceback()}")
        raise

@frappe.whitelist()
def check_auth_status():
    """Check the authorization status of RingCentral integration."""
    try:
        settings = frappe.get_doc("CRM RingCentral Settings", "CRM RingCentral Settings")
        if not settings.enabled:
            frappe.log_error(
                title="RingCentral Auth Check - Disabled",
                message="RingCentral integration is disabled in CRM RingCentral Settings"
            )
            return {"is_authorized": False}
        
        has_valid_token = settings.access_token and (
            not settings.token_expiry or now_datetime() < get_datetime(settings.token_expiry)
        )
        
        if not has_valid_token and settings.refresh_token:
            try:
                ringcentral = RingCentral.connect()
                frappe.log_error(
                    title="RingCentral Token Refresh - Attempting",
                    message="Attempting to refresh access token"
                )
                ringcentral.refresh_access_token()
                settings.reload()
                has_valid_token = settings.access_token and (
                    not settings.token_expiry or now_datetime() < get_datetime(settings.token_expiry)
                )
                frappe.log_error(
                    title="RingCentral Token Refresh - Result",
                    message=f"Token refresh successful. Has valid token: {has_valid_token}"
                )
            except Exception as e:
                frappe.log_error(
                    title="RingCentral Token Refresh - Failed",
                    message=f"Token refresh failed: {str(e)}\n\nTraceback: {frappe.get_traceback()}"
                )
        
        frappe.log_error(
            title="RingCentral Auth Status",
            message=f"Auth status check completed. Has valid token: {has_valid_token}, Access token exists: {bool(settings.access_token)}, Token expiry: {settings.token_expiry}"
        )
        return {"is_authorized": has_valid_token}
    
    except Exception as e:
        frappe.log_error(
            title="RingCentral Auth Check - Error",
            message=f"Unexpected error in auth check: {str(e)}\n\nTraceback: {frappe.get_traceback()}"
        )
        return {"is_authorized": False}

@frappe.whitelist(allow_guest=True)
def ringcentral_call_handler(**kwargs):
    """Webhook for RingCentral incoming and outgoing call events."""
    try:
        args = frappe._dict(kwargs)
        frappe.log_error(
            title="RingCentral Webhook Received",
            message=f"Webhook payload: {frappe.as_json(args)}"
        )
        call_details = RingCentralCallDetails(args)
        
        # Create call log - only once
        create_call_log(call_details)
        
        if call_details.get_direction() == "Incoming":
            resp = IncomingCall(args.get("fromNumber"), args.get("toNumber")).process()
            frappe.log_error(
                title="RingCentral Incoming Call Processed",
                message=f"Incoming call response: {frappe.as_json(resp)}"
            )
            if isinstance(resp, dict) and resp.get("status") == "error":
                return Response(json.dumps(resp), mimetype="application/json")
            return Response(json.dumps(resp), mimetype="application/json")
        else:
            # For outgoing calls, update the call log with initial details
            update_call_log(call_sid=call_details.call_sid, status=args.get("callStatus"))
            frappe.log_error(
                title="RingCentral Outgoing Call Processed",
                message=f"Updated call log for call_sid: {call_details.call_sid}, status: {args.get('callStatus')}"
            )
            return Response(json.dumps({"status": "ok"}), mimetype="application/json")
    except Exception as e:
        frappe.log_error(
            title="RingCentral Webhook Error",
            message=f"Failed to process webhook: {str(e)}\n{frappe.get_traceback()}"
        )
        return Response(json.dumps({"status": "error", "message": str(e)}), mimetype="application/json")
    
    
@frappe.whitelist()
def create_call_log(call_details):
    """Create placeholder CRM Call Log at call start. Full sync happens at end."""
    try:
        call_details = frappe._dict(call_details)
        frappe.log_error(
            title="Create Call Log Attempt",
            message=f"Attempting to create call log with details: {frappe.as_json(call_details)}"
        )
        if not call_details.get("id"):
            frappe.log_error(title="Create Call Log Error", message="Missing call_sid in call_details")
            return {"ok": False, "error": "Missing call_sid"}
        
        existing_log = frappe.db.get_value("CRM Call Log", {"id": call_details.get("id")}, "name")
        if existing_log:
            frappe.log_error(
                title="Create Call Log Error",
                message=f"Call log already exists for call_sid: {call_details.get('id')}"
            )
            return {"ok": True, "call_sid": existing_log}
        
        # Get datetime object and format it properly
        start_time_obj = get_datetime_from_timestamp(call_details.get("startTime")) if call_details.get("startTime") else None
        start_time = start_time_obj.strftime("%Y-%m-%d %H:%M:%S") if start_time_obj else None
        
        call_log = frappe.get_doc({
            "doctype": "CRM Call Log",
            "id": call_details.get("id"),  
            "custom_telephony_session_id": call_details.get("custom_telephony_session_id"),  # New field
            "from": call_details.get("from"),
            "to": call_details.get("to"),
            "type": call_details.get("type", "Outgoing"),
            "status": "Initiated",  # Placeholder
            "telephony_medium": "RingCentral",
            "start_time": start_time,
        })
        
        if call_details.get("type") == "Incoming":
            call_log.receiver = call_details.get("receiver", "")
            contact_number = call_details.get("from")
        else:
            call_log.caller = call_details.get("caller", frappe.session.user)
            contact_number = call_details.get("from") if call_details.get("type") == "Incoming" else call_details.get("to")
        
        if contact_number:
            link(contact_number, call_log)
        
        call_log.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.log_error(
            title="Create Call Log Success",
            message=f"Created call log: {call_log.name} for call_sid: {call_details.get('id')}"
        )
        return {"ok": True, "call_sid": call_log.name}
    except Exception as e:
        frappe.log_error(title="Create Call Log Error", message=str(e))
        return {"ok": False, "error": str(e)}
    
def link(contact_number, call_log):
    contact = get_contact_by_phone_number(contact_number)
    if contact.get("name"):
        doctype = "Contact"
        docname = contact.get("name")
        if contact.get("lead"):
            doctype = "CRM Lead"
            docname = contact.get("lead")
        elif contact.get("deal"):
            doctype = "CRM Deal"
            docname = contact.get("deal")
        call_log.link_with_reference_doc(doctype, docname)
   
  
@frappe.whitelist()
def update_recording_url(call_sid=None, custom_recording_id=None, recording_url=None, custom_telephony_session_id=None):
    """Update CRM Call Log with custom_recording_id, recording_url, and custom_telephony_session_id by call_sid or custom_telephony_session_id."""
    try:
        call_log_name = None
        if call_sid:
            call_log_name = frappe.db.get_value("CRM Call Log", {"id": call_sid}, "name")
        
        if not call_log_name and custom_telephony_session_id:
            call_log_name = frappe.db.get_value("CRM Call Log", {"custom_telephony_session_id": custom_telephony_session_id}, "name")
        
        if not call_log_name:
            error_message = f"Call log not found for call_sid: {call_sid or 'None'}, custom_telephony_session_id: {custom_telephony_session_id or 'None'}"
            frappe.log_error(error_message, "Update Recording URL")
            return {"ok": False, "error": "Call log not found"}

        # Prepare update data
        update_data = {}
        
        if custom_recording_id:
            update_data["custom_recording_id"] = custom_recording_id
            # Generate the recording URL if not provided
            if not recording_url:
                update_data["recording_url"] = f"/api/method/crm.integrations.ringcentral.api.get_recording_audio?custom_recording_id={custom_recording_id}"
            else:
                update_data["recording_url"] = recording_url
        
        if recording_url and not custom_recording_id:
            # If we have URL but no ID, try to extract ID from URL
            update_data["recording_url"] = recording_url
            if "recording/" in recording_url:
                import re
                match = re.search(r'recording/([^/]+)/content', recording_url)
                if match:
                    update_data["custom_recording_id"] = match.group(1)
        
        if custom_telephony_session_id:
            update_data["custom_telephony_session_id"] = custom_telephony_session_id
        
        # Update the call log
        frappe.db.set_value("CRM Call Log", call_log_name, update_data)
        frappe.db.commit()
        
        frappe.log_error(
            title="RingCentral Recording URL Updated",
            message=f"Updated recording for call log {call_log_name} (call_sid: {call_sid or 'None'}, custom_telephony_session_id: {custom_telephony_session_id}) with custom_recording_id: {custom_recording_id}"
        )
        
        return {"ok": True, "message": "Recording URL updated"}
        
    except Exception as e:
        frappe.log_error(f"Failed to update recording URL: {str(e)}\n{frappe.get_traceback()}", "Update Recording URL Error")
        return {"ok": False, "error": str(e)}
  
@frappe.whitelist(allow_guest=True)
def update_call_log(call_sid=None, status=None, duration=None, end_time=None, custom_telephony_session_id=None):
    """Update call log status and details with duration validation."""
    try:
        if not call_sid:
            frappe.log_error(
                title="RingCentral Update Call Log",
                message="No call_sid provided for update_call_log"
            )
            return {"status": "error", "message": "No call_sid provided"}
       
        call_log_name = frappe.db.get_value("CRM Call Log", {"id": call_sid}, "name")
        if not call_log_name:
            frappe.log_error(
                title="RingCentral Update Call Log",
                message=f"Call log not found for call_sid (id): {call_sid}"
            )
            return {"status": "error", "message": f"Call log not found for call_sid: {call_sid}"}
       
        call_log = frappe.get_doc("CRM Call Log", call_log_name)
        call_log.status = RingCentralCallDetails.get_call_status(status)
        
        # Get datetime object for end_time
        end_time_obj = get_datetime_from_timestamp(end_time) if end_time else None
        call_log.end_time = end_time_obj.strftime("%Y-%m-%d %H:%M:%S") if end_time_obj else frappe.utils.now()
        
        # Calculate duration from start_time and end_time if available
        # calculated_duration = None
        # if call_log.start_time and call_log.end_time:
        #     start_dt = get_datetime(call_log.start_time)
        #     end_dt = get_datetime(call_log.end_time)
        #     calculated_duration = (end_dt - start_dt).total_seconds()
        #     frappe.log_error(
        #         title="RingCentral Duration Debug",
        #         message=f"Frontend duration: {duration}, Calculated duration: {calculated_duration}"
        #     )
        
        # Use provided duration if valid, else fallback to calculated duration
        # call_log.duration = int(float(duration)) if duration is not None and float(duration) > 0 else calculated_duration or 0
        # call_log.duration = int(calculated_duration) if calculated_duration is not None else (int(float(duration)) if duration is not None and float(duration) > 0 else 0)
        # Calculate duration from start_time and end_time
        if call_log.start_time and call_log.end_time:
            start_dt = get_datetime(call_log.start_time)
            end_dt = get_datetime(call_log.end_time)
            calculated_duration = (end_dt - start_dt).total_seconds()
            call_log.duration = int(calculated_duration) if calculated_duration >= 0 else 0
            frappe.log_error(
                title="RingCentral Duration Debug",
                message=f"Calculated duration: {call_log.duration} seconds for call_sid: {call_sid}"
            )
        else:
            call_log.duration = 0
            frappe.log_error(
                title="RingCentral Duration Debug",
                message=f"Missing start_time or end_time for call_sid: {call_sid}, setting duration to 0"
            )
        
        
        if custom_telephony_session_id:
            call_log.custom_telephony_session_id = custom_telephony_session_id
        call_log.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.log_error(
            title="RingCentral Call Log Updated",
            message=f"Updated call log: {call_log.name}, call_sid: {call_sid}, status: {call_log.status}, duration: {call_log.duration}"
        )
        return {
            "status": "ok",
            "message": "Call log updated",
            "call_log": {
                "name": call_log.name,
                "id": call_log.id,
                "status": call_log.status,
                "duration": call_log.duration,
                "end_time": call_log.end_time
            }
        }
    except Exception as e:
        frappe.log_error(
            title="RingCentral Update Call Log Error",
            message=f"Failed to update call log for call_sid: {call_sid}: {str(e)}\n{frappe.get_traceback()}"
        )
        frappe.db.commit()
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def get_recording_audio(custom_recording_id):
    """Proxy endpoint to serve RingCentral audio with authentication"""
    try:
        # Simple debug log
        frappe.log_error(f"Audio proxy called for recording: {custom_recording_id}", "RingCentral Audio")
        
        ringcentral = RingCentral.connect()
        if not ringcentral:
            frappe.throw("RingCentral integration not enabled")
        
        # Refresh token if needed
        if ringcentral.settings.token_expiry and now_datetime() >= get_datetime(ringcentral.settings.token_expiry):
            ringcentral.refresh_access_token()
        
        access_token = ringcentral.settings.access_token.strip()
        if not access_token:
            frappe.throw("No valid access token available")
        
        # Construct the media URL
        media_url = f"https://media.ringcentral.com/restapi/v1.0/account/~/recording/{custom_recording_id}/content"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "audio/mpeg, audio/wav"
        }
        
        # Get the audio response
        response = requests.get(media_url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Log success (without verbose headers)
        frappe.log_error(
            f"Audio stream successful: {response.status_code}, Content-Type: {response.headers.get('content-type')}",
            "RingCentral Audio"
        )
        
        # Set response as audio stream
        frappe.local.response = Response(
            response.iter_content(chunk_size=8192),
            content_type=response.headers.get('content-type', 'audio/mpeg'),
            status=200
        )
        
        return frappe.local.response
        
    except Exception as e:
        error_msg = f"Failed to fetch recording {custom_recording_id}: {str(e)}"
        frappe.log_error(title="RingCentral Audio Error", message=error_msg)
        frappe.throw("Failed to fetch recording")
        
        
@frappe.whitelist()
def sync_call_logs():
    try:
        ringcentral = RingCentral.connect()
        if not ringcentral:
            frappe.log_error("RingCentral integration not enabled", "RingCentral")
            return {"ok": False, "error": "integration_not_enabled"}

        # Get the last sync time (manual set required)
        last_sync_str = frappe.db.get_single_value("CRM RingCentral Settings", "last_sync_time")
        if not last_sync_str:
            frappe.log_error("Last sync time not set in CRM RingCentral Settings", "RingCentral")
            return {"ok": False, "error": "last_sync_time_not_set"}

        # Convert last_sync to ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
        last_sync_dt = get_datetime(last_sync_str)
        last_sync = last_sync_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Current time in ISO 8601
        current_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%SZ")

        frappe.log_error(f"Sync range: dateFrom={last_sync}, dateTo={current_time}", "RingCentral Sync Debug")

        headers = {
            "Authorization": f"Bearer {ringcentral.settings.access_token.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.get(
            f"{ringcentral.server_url}/restapi/v1.0/account/~/extension/~/call-log",
            params={
                "dateFrom": last_sync,
                "dateTo": current_time,
                "withRecording": "true",
                "view": "Detailed",
                "perPage": 100
            },
            headers=headers
        )
        response.raise_for_status()
        call_data = response.json()
        records = call_data.get("records", [])

        for record in records:
            custom_telephony_session_id = record.get("telephonySessionId")
            start_time = record.get("startTime")
            from_number = record.get("from", {}).get("phoneNumber")
            to_number = record.get("to", {}).get("phoneNumber")
            recording = record.get("recording")

            if custom_telephony_session_id and recording and recording.get("id"):
                custom_recording_id = recording.get("id")
                # Convert start_time to Frappe-compatible format
                start_time_frappe = get_datetime(start_time).strftime("%Y-%m-%d %H:%M:%S")
                end_time_frappe = add_to_date(get_datetime(start_time), seconds=record.get("duration") or 0).strftime("%Y-%m-%d %H:%M:%S")

                # Check if this call exists in CRM Call Log
                call_log_name = frappe.db.get_value(
                    "CRM Call Log",
                    {
                        "custom_telephony_session_id": custom_telephony_session_id,
                        "start_time": start_time_frappe,
                        "from": from_number,
                        "to": to_number
                    },
                    "name"
                )
                if not call_log_name:
                    # Create new call log if not exists
                    call_log = frappe.get_doc({
                        "doctype": "CRM Call Log",
                        "id": frappe.generate_hash(length=32),  # Generate a unique ID
                        "custom_telephony_session_id": custom_telephony_session_id,
                        "from": from_number,
                        "to": to_number,
                        "type": "Outgoing" if record.get("direction") == "Outbound" else "Incoming",
                        "status": "Completed",
                        "telephony_medium": "RingCentral",
                        "start_time": start_time_frappe,
                        "duration": record.get("duration"),
                        "end_time": end_time_frappe,
                        "custom_recording_id": custom_recording_id,  # Store recording ID
                        "recording_url": f"/api/method/crm.integrations.ringcentral.api.get_recording_audio?custom_recording_id={custom_recording_id}"
                        # "recording_url": recording["contentUri"]
                    })
                    call_log.insert(ignore_permissions=True)
                    frappe.db.commit()
                    frappe.log_error(
                        title="RingCentral Call Log Created",
                        message=f"Created call log {call_log.name} with telephonySessionId: {custom_telephony_session_id}"
                    )
                else:
                    # Update existing call log with recording URL
                    frappe.db.set_value(
                        "CRM Call Log",
                        call_log_name,
                        {
                            "custom_recording_id": custom_recording_id,
                            "recording_url": f"/api/method/crm.integrations.ringcentral.api.get_recording_audio?custom_recording_id={custom_recording_id}"
                        }
                    )
                    frappe.db.commit()
                    frappe.log_error(
                        title="RingCentral Recording Updated",
                        message=f"Updated call log {call_log_name} with recording URL"
                    )

        # Update last sync time to current time
        frappe.db.set_value("CRM RingCentral Settings", None, "last_sync_time", now_datetime())
        frappe.db.commit()
        return {"ok": True, "message": f"Synced {len(records)} call logs"}
    except Exception as e:
        frappe.log_error(
            title="RingCentral Sync Error",
            message=f"Failed to sync call logs: {str(e)}\n{frappe.get_traceback()}"
        )
        return {"ok": False, "error": str(e)}

def get_datetime_from_timestamp(timestamp):
    """Convert timestamp to system timezone datetime."""
    if not timestamp:
        return None
    datetime_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    system_timezone = frappe.utils.get_system_timezone()
    converted_datetime = datetime_utc.astimezone(ZoneInfo(system_timezone))
    return converted_datetime  # Return datetime object, not formatted string