import frappe
from frappe import _
import requests
from ringcentral import SDK
from crm.integrations.ringcentral.utils import get_public_url, merge_dicts
from frappe.utils.password import get_decrypted_password
from frappe.utils import now_datetime, add_to_date, get_datetime
import base64


@frappe.whitelist(allow_guest=True)
def oauth_callback(code=None, state=None):
    if not code:
        frappe.throw(_("Missing authorization code."))

    settings = frappe.get_single("CRM RingCentral Settings")
    token_url = f"{settings.server_url}/restapi/oauth/token"
    client_id = settings.client_id
    client_secret = settings.get_password("client_secret")

    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri,
    }

    res = requests.post(token_url, data=data, headers=headers)
    if res.status_code != 200:
        frappe.throw(_("Failed to fetch token: ") + res.text)

    tokens = res.json()
    frappe.log_error(
        title="RingCentral Tokens Debug",
        message=res.text
    )

    settings.access_token = tokens["access_token"]
    settings.refresh_token = tokens["refresh_token"]
    settings.token_expiry = add_to_date(now_datetime(), seconds=tokens.get("expires_in", 3600))
    settings.save(ignore_permissions=True)
    frappe.db.commit()

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/crm"


class RingCentral:
    """RingCentral connector over RingCentral SDK."""

    def __init__(self, settings):
        """
        :param settings: `CRM RingCentral Settings` doctype
        """
        self.settings = settings
        self.client_id = settings.client_id
        self.client_secret = settings.get_password("client_secret")
        self.server_url = settings.server_url
        self.redirect_uri = settings.redirect_uri
        self.rcsdk = self.get_ringcentral_client()
        self.platform = self.rcsdk.platform()  # Expose platform attribute

    def get_authorize_url(self):
        """Generate RingCentral OAuth URL (for frontend button)."""
        return (
            f"{self.server_url}/restapi/oauth/authorize"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
        )

    def refresh_access_token(self):
        """Refresh expired token."""
        if not self.settings.refresh_token:
            frappe.log_error("Missing refresh token in CRM RingCentral Settings", title="RingCentral Token Refresh Error")
            frappe.throw(_("Missing refresh token."))

        token_url = f"{self.server_url}/restapi/oauth/token"
        client_id = self.settings.client_id
        client_secret = self.settings.get_password("client_secret")

        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.settings.get_password("refresh_token")
        }

        res = requests.post(token_url, headers=headers, data=data)
        if res.status_code != 200:
            frappe.log_error(message=res.text, title="RingCentral Token Refresh Failed")
            frappe.throw(_("Failed to refresh token: ") + res.text)

        tokens = res.json()
        frappe.log_error(
            message=frappe.as_json({
                "access_token": tokens["access_token"][:50] + "...",
                "refresh_token": tokens["refresh_token"][:50] + "...",
                "expires_in": tokens.get("expires_in", 3600),
                "scope": tokens.get("scope")
            }),
            title="RingCentral Token Refreshed"
        )

        self.settings.access_token = tokens["access_token"]
        self.settings.refresh_token = tokens["refresh_token"]
        self.settings.token_expiry = add_to_date(now_datetime(), seconds=tokens.get("expires_in", 3600))
        self.settings.save(ignore_permissions=True)
        frappe.db.commit()

        self.platform.auth().set_data({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens.get("expires_in", 3600)
        })
        return self.settings.access_token
    def fetch_call_log_by_session(self, custom_telephony_session_id, view='Detailed', account_level=False):
        """Fetch call log from RC API by telephonySessionId."""
        try:
            endpoint = '/restapi/v1.0/account/~/call-log' if account_level else '/restapi/v1.0/account/~/extension/~/call-log'
            params = {
                'telephonySessionId': custom_telephony_session_id,
                'view': view,
                'perPage': 1 # Since we filter by unique ID, expect 1 result
                            }
            response = self.platform.get(endpoint, params=params)
            data = response.json()
            if not data.get('records'):
                frappe.log_error(f"No call log found for telephonySessionId: {custom_telephony_session_id}", "RingCentral Fetch Call Log")
            return None
        except Exception as e:
            frappe.log_error(f"Failed to fetch call log: {str(e)}", "RingCentral Fetch Call Log")
        return None

    @classmethod
    def connect(cls):
        """Make a RingCentral connection."""
        settings = frappe.get_doc("CRM RingCentral Settings")
        if not (settings and settings.enabled):
            frappe.log_error("RingCentral integration is not enabled")
            return None
        return cls(settings=settings)

    def get_phone_numbers(self):
        """Get account's RingCentral phone numbers."""
        try:
            url = f"{self.server_url}/restapi/v1.0/account/~/phone-number"
            headers = {
                "Authorization": f"Bearer {self.settings.access_token.strip()}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                frappe.log_error(title="Failed to fetch phone numbers", message=response.text)
                frappe.throw(_("Failed to fetch phone numbers: ") + response.text)
            numbers = response.json().get("records", [])
            return [n["phoneNumber"] for n in numbers if n.get("usageType") == "DirectNumber"]
        except Exception as e:
            frappe.log_error(title="Failed to fetch phone numbers", message=str(e))
            frappe.throw(_("Failed to fetch phone numbers: ") + str(e))

    def generate_access_token(self, identity: str, ttl=3600):
        """Generates a token for WebRTC authentication."""
        try:
            if not self.platform.auth().access_token_valid():
                if self.settings.token_expiry and now_datetime() >= get_datetime(self.settings.token_expiry):
                    frappe.log_error("Access token expired, refreshing...")
                    self.refresh_access_token()
            token_data = self.platform.auth().data()
            frappe.log_error(f"Generated token data: {token_data}")
            return {
                'token': token_data.get('access_token'),
                'expires_in': token_data.get('expires_in', 3600)
            }
        except Exception as e:
            frappe.log_error(
                title="Generated RingCentral Token",
                message=frappe.as_json(token_data)  # pretty prints JSON into message field
            )
            return {}

    @classmethod
    def safe_identity(cls, identity: str):
        """Create a safe identity by replacing unsupported characters."""
        return identity.replace("@", "(at)")

    @classmethod
    def emailid_from_identity(cls, identity: str):
        """Convert safe identity string into emailID."""
        return identity.replace("(at)", "@")

    def generate_ringcentral_dial_response(self, from_number: str, to_number: str):
        """Generates call instructions to forward the call to agent's phone."""
        try:
            url = f"{self.server_url}/restapi/v1.0/account/~/extension/~/ring-out"
            headers = {
                "Authorization": f"Bearer {self.settings.access_token.strip()}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            data = {
                "from": {"phoneNumber": from_number},
                "to": {"phoneNumber": to_number},
                "playPrompt": True
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 200:
                frappe.log_error(title="Failed to generate RingCentral dial response", message=response.text)
                frappe.throw(_("Failed to generate dial response: ") + response.text)
            return response.json()
        except Exception as e:
            frappe.log_error(title="Failed to generate RingCentral dial response", message=str(e))
            return {}

    def get_call_info(self, call_sid):
        """Fetch call details by call ID."""
        try:
            response = self.platform.get(f'/restapi/v1.0/account/~/telephony/sessions/{call_sid}')
            return response.json()
        except Exception as e:
            frappe.log_error(title="Failed to fetch RingCentral call info", message=str(e))
            return {}

    def get_ringcentral_client(self):
        """Initialize RingCentral SDK client."""
        if not self.settings.enabled:
            frappe.throw(_("Please enable RingCentral settings before making a call."))

        if self.settings.token_expiry:
            token_expiry = get_datetime(self.settings.token_expiry)
            if now_datetime() >= token_expiry:
                frappe.log_error("Access token expired, refreshing in get_ringcentral_client...")
                self.refresh_access_token()

        rcsdk = SDK(self.client_id, self.client_secret, self.server_url)
        if self.settings.access_token:
            clean_access_token = self.settings.access_token.strip()
            rcsdk.platform().auth().set_data({
                'access_token': clean_access_token,
                'refresh_token': self.settings.get_password("refresh_token"),
                'expires_in': 3600
            })
        return rcsdk


class IncomingCall:
    def __init__(self, from_number, to_number, meta=None):
        self.from_number = from_number
        self.to_number = to_number
        self.meta = meta

    def process(self):
        """Process the incoming call."""
        ringcentral = RingCentral.connect()
        if not ringcentral:
            return {"status": "error", "message": _("RingCentral not enabled")}

        owners = get_ringcentral_number_owners(self.to_number)
        attender = get_the_call_attender(owners, self.from_number)

        if not attender:
            return {"status": "error", "message": _("Agent is unavailable to take the call, please call after some time.")}

        if attender["call_receiving_device"] == "Phone":
            return ringcentral.generate_ringcentral_dial_response(self.from_number, attender["mobile_no"])
        else:
            return {
                "status": "client",
                "identity": ringcentral.safe_identity(attender["name"])
            }


def get_ringcentral_number_owners(phone_number):
    """Get list of users who are using the phone_number."""
    phone_number = "".join([c for c in phone_number if c.isdigit() or c == "+"])
    user_voice_settings = frappe.get_all(
        "CRM Telephony Agent",
        filters={"ringcentral_number": phone_number},
        fields=["name", "call_receiving_device"],
    )
    user_wise_voice_settings = {user["name"]: user for user in user_voice_settings}

    user_general_settings = frappe.get_all(
        "User", filters=[["name", "IN", user_wise_voice_settings.keys()]], fields=["name", "mobile_no"]
    )
    user_wise_general_settings = {user["name"]: user for user in user_general_settings}

    return merge_dicts(user_wise_general_settings, user_wise_voice_settings)


def get_active_loggedin_users(users):
    """Filter the current logged-in users from the given users list."""
    rows = frappe.db.sql(
        """
        SELECT `user`
        FROM `tabSessions`
        WHERE `user` IN %(users)s
        """,
        {"users": users},
    )
    return [row[0] for row in set(rows)]


def get_the_call_attender(owners, caller=None):
    """Get attender details from list of owners."""
    if not owners:
        return

    current_loggedin_users = get_active_loggedin_users(list(owners.keys()))

    if len(current_loggedin_users) > 1 and caller:
        deal_owner = frappe.db.get_value("CRM Deal", {"mobile_no": caller}, "deal_owner")
        if not deal_owner:
            deal_owner = frappe.db.get_value(
                "CRM Lead", {"mobile_no": caller, "converted": False}, "lead_owner"
            )

        for user in current_loggedin_users:
            if user == deal_owner:
                current_loggedin_users = [user]

    for name, details in owners.items():
        if (details["call_receiving_device"] == "Phone" and details["mobile_no"]) or (
            details["call_receiving_device"] == "Computer" and name in current_loggedin_users
        ):
            return details


class RingCentralCallDetails:
    def __init__(self, call_info, call_from=None, call_to=None):
        self.call_info = call_info
        self.call_sid = call_info.get("id")
        self.call_status = self.get_call_status(call_info.get("status", {}).get("callStatus"))
        self._call_from = call_from or call_info.get("from", {}).get("phoneNumber")
        self._call_to = call_to or call_info.get("to", {}).get("phoneNumber")

    def get_direction(self):
        if self.call_info.get("direction") == "Outbound":
            return "Outgoing"
        return "Incoming"

    def get_from_number(self):
        return self._call_from or self.call_info.get("from", {}).get("phoneNumber")

    def get_to_number(self):
        return self._call_to or self.call_info.get("to", {}).get("phoneNumber")

    @classmethod
    def get_call_status(cls, ringcentral_status):
        """Convert RingCentral given status into system status."""
        ringcentral_status = ringcentral_status or ""
        if not ringcentral_status:
            return "Unknown"
        return " ".join(ringcentral_status.replace("-", " ").split()).title()

    def to_dict(self):
        """Convert call details into dict."""
        direction = self.get_direction()
        from_number = self.get_from_number()
        to_number = self.get_to_number()
        caller = ""
        receiver = ""

        if direction == "Outgoing":
            caller = self.call_info.get("from", {}).get("name", "")
            identity = RingCentral.safe_identity(caller)
            caller = RingCentral.emailid_from_identity(identity) if identity else ""
        else:
            owners = get_ringcentral_number_owners(to_number)
            attender = get_the_call_attender(owners, from_number)
            receiver = attender["name"] if attender else ""

        return {
            "type": direction,
            "status": self.call_status,
            "id": self.call_sid,
            "from": from_number,
            "to": to_number,
            "receiver": receiver,
            "caller": caller,
        }
