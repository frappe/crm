"""
crm/api/contracts.py — CRM Contract Signing State Machine

Story:  cs-s1-2
BRD:    BRD_Contract_Signing.docx
ADR:    ADR_Contract_Signing.docx

Security model:
- generate / download_pdf require Sales Manager or System Manager role.
- Public endpoints (request_otp, verify_otp, get_contract, sign) are guest-accessible.
- Identity is proven by: HMAC invitation token → 6-digit OTP → HMAC signing token.
- hmac.compare_digest() used for ALL token comparisons — never ==.

Rules enforced:
- frappe.get_list() for every SELECT — no frappe.db.sql() SELECTs, no frappe.get_all().
- ignore_permissions=True only on system/scheduler paths — marked # SYSTEM-INTERNAL.
- No f-strings in log/error messages — % formatting only.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import random
import time

import frappe
from frappe import _

_OTP_EXPIRY_SECONDS = 600    # 10 minutes
_SIGN_EXPIRY_SECONDS = 7200  # 2 hours
_INVITE_EXPIRY_SECONDS = 604800  # 7 days
_MAX_OTP_ATTEMPTS = 3


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_signing_key():
    """Return the optin_signing_key; auto-generates if absent."""
    settings = frappe.get_single("CRM Opt-In Settings")
    key = settings.get_password("optin_signing_key", raise_exception=False)
    if not key:
        from crm.setup.optin import ensure_signing_key
        ensure_signing_key()
        settings = frappe.get_single("CRM Opt-In Settings")
        key = settings.get_password("optin_signing_key", raise_exception=False)
    if not key:
        frappe.throw("Contract signing key not configured.", frappe.ConfigurationError)
    return key


def _hmac_hex(secret, message):
    """Return HMAC-SHA256 hex digest of message under secret (both str)."""
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def _check_contract_rate_limit(limit=10, window=60):
    """IP-based rate limit for guest contract signing endpoints (10 req/min/IP)."""
    ip = frappe.local.request.environ.get("REMOTE_ADDR", "unknown") if frappe.local.request else "cli"
    cache_key = "contract_rl:%s" % ip
    count = frappe.cache().get_value(cache_key) or 0
    if int(count) >= limit:
        frappe.throw(_("Too many requests. Please wait before trying again."), frappe.PermissionError)
    frappe.cache().set_value(cache_key, int(count) + 1, expires_in_sec=window)


def _check_crm_role():
    """Raise PermissionError if the current user lacks Sales Manager or System Manager."""
    user = frappe.session.user
    roles = frappe.get_roles(user)
    if (
        "Sales Manager" not in roles
        and "System Manager" not in roles
        and user != "Administrator"
    ):
        frappe.throw(_("Not permitted."), frappe.PermissionError)


def _validate_invite_token(contract, role, exp, tok):
    """
    Raise AuthenticationError if the HMAC invitation token is invalid or expired.
    Token message: "{contract}:{role}:{exp}"
    """
    try:
        exp_int = int(exp)
    except (TypeError, ValueError):
        frappe.throw(_("Invalid invitation link."), frappe.AuthenticationError)

    if time.time() > exp_int:
        frappe.throw(_("Invitation link has expired."), frappe.AuthenticationError)

    key = _get_signing_key()
    msg = "%s:%s:%s" % (contract, role, exp)
    expected = _hmac_hex(key, msg)

    if not hmac.compare_digest(expected, frappe.utils.cstr(tok)):
        frappe.throw(_("Invalid invitation link."), frappe.AuthenticationError)


def _validate_signing_token(signing_token, contract, role, expiry):
    """
    Raise AuthenticationError if the signing token is invalid or expired.
    Token message: "{contract}:{role}:{expiry}"
    """
    try:
        exp_int = int(expiry)
    except (TypeError, ValueError):
        frappe.throw(_("Invalid session token."), frappe.AuthenticationError)

    if time.time() > exp_int:
        frappe.throw(_("Session expired. Please request a new OTP."), frappe.AuthenticationError)

    key = _get_signing_key()
    msg = "%s:%s:%s" % (contract, role, expiry)
    expected = _hmac_hex(key, msg)

    if not hmac.compare_digest(expected, frappe.utils.cstr(signing_token)):
        frappe.throw(_("Invalid session token."), frappe.AuthenticationError)


def _get_signatory_row(contract_doc, role):
    """Return the first signatory child row matching role, or None."""
    for row in (contract_doc.signatories or []):
        if row.signatory_role == role:
            return row
    return None


def _attempts_cache_key(contract, role):
    return "contract_otp_attempts:%s:%s" % (contract, role)


def _session_cache_key(session_token):
    return "contract_session:%s" % session_token


def _send_signing_invitation(contract_doc, signatory_row):
    """
    Build an HMAC-signed invitation link and email it to the signatory.
    Link: /sign-contract?contract={name}&role={role}&exp={expiry}&tok={token}
    """
    key = _get_signing_key()
    expiry = int(time.time()) + _INVITE_EXPIRY_SECONDS
    role = frappe.utils.cstr(signatory_row.signatory_role)
    tok = _hmac_hex(key, "%s:%s:%s" % (contract_doc.name, role, expiry))
    link = "/sign-contract?contract=%s&role=%s&exp=%s&tok=%s" % (
        contract_doc.name,
        role.replace(" ", "+"),
        expiry,
        tok,
    )

    try:
        frappe.sendmail(
            recipients=[signatory_row.signatory_email],
            subject="Action Required: Sign Your CareverseHIMS Contract",
            message=(
                "<p>Dear %s,</p>"
                "<p>You have been asked to sign a CareverseHIMS contract. "
                "Please click the link below to review and sign:</p>"
                "<p><a href='%s'>Sign Contract</a></p>"
                "<p>This link expires in 7 days. "
                "Do not share it with anyone.</p>"
            ) % (frappe.utils.cstr(signatory_row.signatory_name), link),
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "contracts._send_signing_invitation: email failed for %s / %s" % (
                contract_doc.name, role
            ),
        )


# ---------------------------------------------------------------------------
# State machine — private, not whitelisted
# ---------------------------------------------------------------------------


def _transition(contract_name):
    """
    Advance the contract workflow after a signatory signs.

    State machine (based on count of Signed rows in signatories):
      1 signed  → Facility Signatory just signed; send Facility Witness invitation.
      2 signed  → Both external parties signed; set workflow_state =
                  "Awaiting Internal Approval"; notify 3 internal approvers.
    """
    contract = frappe.get_doc("CRM Contract", contract_name)
    signed_count = sum(1 for s in (contract.signatories or []) if s.status == "Signed")

    if signed_count == 1:
        # Facility Signatory just signed — invite Facility Witness next
        witness_row = _get_signatory_row(contract, "Facility Witness")
        if witness_row and witness_row.status == "Pending":
            _send_signing_invitation(contract, witness_row)

    elif signed_count >= 2:
        # Both external parties have signed
        contract.workflow_state = "Awaiting Internal Approval"
        # status stays "Awaiting Signatures" (the only valid Select option for this state)
        contract.save(ignore_permissions=True)  # SYSTEM-INTERNAL
        frappe.db.commit()
        _notify_internal_approvers(contract_name, contract.deal)


def _notify_internal_approvers(contract_name, deal_name):
    """
    Fetch network_approver_1, network_approver_2, tiberbu_approver from the
    CRM Onboarding Request linked to the deal (fallback: CRM Deal custom fields).
    Send an approval-request email to each.
    """
    approver_fields = ["network_approver_1", "network_approver_2", "tiberbu_approver"]
    approver_names = []

    if deal_name:
        onboarding_rows = frappe.get_list(
            "CRM Onboarding Request",
            filters={"deal": deal_name},
            fields=approver_fields,
            limit=1,
            ignore_permissions=True,  # SYSTEM-INTERNAL
        )
        if onboarding_rows:
            row = onboarding_rows[0]
            for f in approver_fields:
                v = row.get(f)
                if v:
                    approver_names.append(v)

    # Fallback: CRM Deal custom fields
    if not approver_names and deal_name:
        deal_rows = frappe.get_list(
            "CRM Deal",
            filters={"name": deal_name},
            fields=approver_fields,
            limit=1,
            ignore_permissions=True,  # SYSTEM-INTERNAL
        )
        if deal_rows:
            row = deal_rows[0]
            for f in approver_fields:
                v = row.get(f)
                if v:
                    approver_names.append(v)

    for approver_user in approver_names:
        approver_user = frappe.utils.cstr(approver_user).strip()
        if not approver_user:
            continue
        try:
            approver_email = frappe.db.get_value("User", approver_user, "email")
            if not approver_email:
                continue
            frappe.sendmail(
                recipients=[approver_email],
                subject="Approval Required: CareverseHIMS Contract %s" % contract_name,
                message=(
                    "<p>Dear %s,</p>"
                    "<p>A CareverseHIMS contract requires your internal approval.</p>"
                    "<p>Contract Reference: <strong>%s</strong></p>"
                    "<p>Both facility signatories have signed. "
                    "Please log in to the CRM to review and approve.</p>"
                ) % (approver_user, contract_name),
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "contracts._notify_internal_approvers: failed for approver %s on %s" % (
                    approver_user, contract_name
                ),
            )


# ---------------------------------------------------------------------------
# Whitelisted API — CRM users only
# ---------------------------------------------------------------------------


@frappe.whitelist()
def generate(
    deal,
    quote,
    facility_signatory_name,
    facility_signatory_email,
    facility_witness_name,
    facility_witness_email,
    network_approver_1="",
    network_approver_2="",
    tiberbu_approver="",
):
    """
    Create a CRM Contract for a deal, render contract HTML from active T&C,
    add two signatory rows, and send the HMAC invitation to the Facility Signatory.

    Requires: Sales Manager or System Manager role.
    Returns: {contract: <name>}
    """
    _check_crm_role()

    deal = frappe.utils.cstr(deal).strip()
    quote = frappe.utils.cstr(quote).strip()
    facility_signatory_name = frappe.utils.cstr(facility_signatory_name).strip()
    facility_signatory_email = frappe.utils.cstr(facility_signatory_email).strip().lower()
    facility_witness_name = frappe.utils.cstr(facility_witness_name).strip()
    facility_witness_email = frappe.utils.cstr(facility_witness_email).strip().lower()

    if not deal:
        frappe.throw(_("Deal is required to generate a contract."))
    if not facility_signatory_email or not facility_witness_email:
        frappe.throw(_("Signatory and witness email addresses are required."))

    # Render contract HTML from active T&C template
    contract_html = ""
    tc_document = ""
    tc_document_hash = ""

    try:
        settings = frappe.get_single("CRM Opt-In Settings")
        tc_name = settings.active_tc_document
        if tc_name:
            tc_doc = frappe.get_doc("Terms and Conditions", tc_name)
            context = {
                "deal": deal,
                "quote": quote,
                "facility_signatory_name": facility_signatory_name,
                "date": frappe.utils.format_date(frappe.utils.today()),
            }
            contract_html = frappe.render_template(tc_doc.terms or "", context)
            tc_document = tc_name
            tc_document_hash = hashlib.sha256(contract_html.encode()).hexdigest()
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "contracts.generate: T&C render failed for deal %s" % deal,
        )

    # Create the CRM Contract document
    contract = frappe.new_doc("CRM Contract")
    contract.naming_series = "CONT-"
    contract.deal = deal
    contract.quote = quote or None
    contract.contract_date = frappe.utils.today()
    contract.status = "Awaiting Signatures"
    contract.workflow_state = "Awaiting Facility Signature"
    contract.contract_html = contract_html
    contract.tc_document = tc_document
    contract.tc_document_hash = tc_document_hash

    # Signatory row 1: Facility Signatory
    contract.append("signatories", {
        "signatory_name": facility_signatory_name,
        "signatory_email": facility_signatory_email,
        "signatory_role": "Facility Signatory",
        "status": "Pending",
        "is_witness": 0,
    })

    # Signatory row 2: Facility Witness
    contract.append("signatories", {
        "signatory_name": facility_witness_name,
        "signatory_email": facility_witness_email,
        "signatory_role": "Facility Witness",
        "status": "Pending",
        "is_witness": 1,
        "witnessing_for": facility_signatory_name,
    })

    contract.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()

    # Send HMAC invitation to the Facility Signatory immediately
    signatory_row = _get_signatory_row(contract, "Facility Signatory")
    if signatory_row:
        _send_signing_invitation(contract, signatory_row)

    return {"contract": contract.name}


@frappe.whitelist()
def download_pdf(contract):
    """
    Return base64-encoded PDF of the contract HTML.
    Requires: Sales Manager or System Manager role.
    Returns: {pdf_b64: <base64 string>}
    """
    _check_crm_role()

    contract = frappe.utils.cstr(contract).strip()

    contract_rows = frappe.get_list(
        "CRM Contract",
        filters={"name": contract},
        fields=["name", "contract_html"],
        limit=1,
        ignore_permissions=True,  # SYSTEM-INTERNAL
    )
    if not contract_rows:
        frappe.throw(_("Contract not found."), frappe.DoesNotExistError)

    html = frappe.utils.cstr(contract_rows[0].get("contract_html") or "")

    try:
        from frappe.utils.pdf import get_pdf
        pdf_bytes = get_pdf(html)
        return {"pdf_b64": base64.b64encode(pdf_bytes).decode("utf-8")}
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "contracts.download_pdf: PDF generation failed for %s" % contract,
        )
        frappe.throw(_("PDF generation failed."))


# ---------------------------------------------------------------------------
# Whitelisted API — guest-accessible (signing portal)
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def request_otp(contract, role, exp, tok):
    """
    Validate HMAC invitation token, generate a 6-digit OTP, store its HMAC on the
    signatory row, and email it to the signatory.

    Returns: {session_token}
    session_token = HMAC(secret, "{contract}:{role}:{otp_expiry_ts}")
    It is also stored in Redis so verify_otp can validate it without datetime arithmetic.
    """
    _check_contract_rate_limit()
    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()

    _validate_invite_token(contract, role, exp, tok)

    contract_doc = frappe.get_doc("CRM Contract", contract)
    signatory_row = _get_signatory_row(contract_doc, role)

    if not signatory_row:
        frappe.throw(_("Signatory role not found in this contract."), frappe.DoesNotExistError)

    if signatory_row.status != "Pending":
        frappe.throw(
            _("This signing slot has already been completed."),
            frappe.ValidationError,
        )

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    key = _get_signing_key()
    otp_hash = _hmac_hex(key, otp)
    otp_expiry_ts = int(time.time()) + _OTP_EXPIRY_SECONDS
    otp_expiry_dt = frappe.utils.add_to_date(
        frappe.utils.now_datetime(), seconds=_OTP_EXPIRY_SECONDS
    )

    # Persist OTP hash on the signatory row (Data field — stored as plain HMAC hex)
    signatory_row.otp_hash = otp_hash
    signatory_row.otp_expiry = otp_expiry_dt
    signatory_row.otp_used = 0
    contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()

    # Reset attempt counter in Redis
    frappe.cache().set_value(
        _attempts_cache_key(contract, role),
        0,
        expires_in_sec=_OTP_EXPIRY_SECONDS + 120,
    )

    # Build session token and cache session context for verify_otp
    session_token = _hmac_hex(key, "%s:%s:%s" % (contract, role, otp_expiry_ts))
    frappe.cache().set_value(
        _session_cache_key(session_token),
        json.dumps({"contract": contract, "role": role, "expiry": otp_expiry_ts}),
        expires_in_sec=_OTP_EXPIRY_SECONDS + 120,
    )

    # Send OTP email
    try:
        frappe.sendmail(
            recipients=[signatory_row.signatory_email],
            subject="Your CareverseHIMS Contract Signing Code",
            message=(
                "<p>Dear %s,</p>"
                "<p>Your contract verification code is: <strong>%s</strong></p>"
                "<p>This code expires in 10 minutes. "
                "Do not share it with anyone.</p>"
            ) % (frappe.utils.cstr(signatory_row.signatory_name), otp),
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "contracts.request_otp: OTP email failed for %s / %s" % (contract, role),
        )

    return {"session_token": session_token}


@frappe.whitelist(allow_guest=True)
def verify_otp(session_token, contract, role, otp):
    """
    Validate the 6-digit OTP against the stored HMAC.
    On success: clear otp_hash, issue a short-lived signing_token.

    Returns: {signing_token, expiry, contract_html, signatory_name, signatory_role}

    All failures raise frappe.AuthenticationError("Verification failed.") — same message always.
    """
    _check_contract_rate_limit()
    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()
    otp = frappe.utils.cstr(otp).strip()
    session_token = frappe.utils.cstr(session_token).strip()

    # Validate session token via Redis cache (avoids datetime-to-timestamp conversion)
    key = _get_signing_key()
    session_raw = frappe.cache().get_value(_session_cache_key(session_token))
    if not session_raw:
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    try:
        session_data = json.loads(session_raw)
    except Exception:
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    # Verify contract and role match what was cached at request_otp time
    if (
        session_data.get("contract") != contract
        or session_data.get("role") != role
    ):
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    # Cryptographically re-verify the session token (constant-time)
    otp_expiry_ts = session_data.get("expiry", 0)
    expected_session = _hmac_hex(key, "%s:%s:%s" % (contract, role, otp_expiry_ts))
    if not hmac.compare_digest(expected_session, session_token):
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    contract_doc = frappe.get_doc("CRM Contract", contract)
    signatory_row = _get_signatory_row(contract_doc, role)

    if not signatory_row:
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    # Check OTP expiry (DB-side guard in addition to Redis expiry)
    if (
        not signatory_row.otp_expiry
        or frappe.utils.now_datetime() > signatory_row.otp_expiry
    ):
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    # Check attempt count from Redis
    attempts_key = _attempts_cache_key(contract, role)
    attempts = int(frappe.cache().get_value(attempts_key) or 0)
    if attempts >= _MAX_OTP_ATTEMPTS:
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    # Increment attempts before validating (prevents brute-force via timing)
    frappe.cache().set_value(
        attempts_key,
        attempts + 1,
        expires_in_sec=_OTP_EXPIRY_SECONDS + 120,
    )

    # Validate OTP HMAC — constant-time comparison
    # otp_hash is a Data field; read directly (not get_password)
    stored_hash = frappe.utils.cstr(signatory_row.otp_hash or "")
    expected_hash = _hmac_hex(key, otp)

    if not hmac.compare_digest(stored_hash, expected_hash):
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    # OTP valid — clear hash and reset attempt counter
    signatory_row.otp_hash = ""
    signatory_row.otp_used = 1
    contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()
    frappe.cache().set_value(attempts_key, 0, expires_in_sec=60)
    # Invalidate the consumed session token
    frappe.cache().delete_value(_session_cache_key(session_token))

    # Issue signing token valid for 2 hours
    signing_expiry = int(time.time()) + _SIGN_EXPIRY_SECONDS
    signing_token = _hmac_hex(key, "%s:%s:%s" % (contract, role, signing_expiry))

    return {
        "signing_token": signing_token,
        "expiry": signing_expiry,
        "contract_html": frappe.utils.cstr(contract_doc.contract_html or ""),
        "signatory_name": frappe.utils.cstr(signatory_row.signatory_name or ""),
        "signatory_role": frappe.utils.cstr(signatory_row.signatory_role or ""),
    }


@frappe.whitelist(allow_guest=True)
def get_contract(signing_token, contract, role, expiry):
    """
    Return contract HTML and signatory metadata for the signing portal.
    Validates signing_token before returning any data.

    Returns: {contract_html, signatory_name, signatory_role, contract_date}
    """
    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()

    _validate_signing_token(signing_token, contract, role, expiry)

    contract_rows = frappe.get_list(
        "CRM Contract",
        filters={"name": contract},
        fields=["name", "contract_html", "contract_date"],
        limit=1,
        ignore_permissions=True,  # SYSTEM-INTERNAL
    )
    if not contract_rows:
        frappe.throw(_("Contract not found."), frappe.DoesNotExistError)

    contract_row = contract_rows[0]

    sig_rows = frappe.get_list(
        "CRM Contract Signatory",
        filters={"parent": contract, "signatory_role": role},
        fields=["signatory_name", "signatory_role", "status"],
        limit=1,
        ignore_permissions=True,  # SYSTEM-INTERNAL
    )
    signatory_name = sig_rows[0].get("signatory_name", "") if sig_rows else ""

    return {
        "contract_html": frappe.utils.cstr(contract_row.get("contract_html") or ""),
        "signatory_name": frappe.utils.cstr(signatory_name),
        "signatory_role": role,
        "contract_date": frappe.utils.cstr(contract_row.get("contract_date") or ""),
    }


@frappe.whitelist(allow_guest=True)
def sign(signing_token, contract, role, expiry, signature_b64):
    """
    Record the signature on the signatory row and advance the workflow via _transition().

    Returns: {status: "signed"}
    """
    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()

    _validate_signing_token(signing_token, contract, role, expiry)

    contract_doc = frappe.get_doc("CRM Contract", contract)
    signatory_row = _get_signatory_row(contract_doc, role)

    if not signatory_row:
        frappe.throw(_("Signatory role not found in this contract."), frappe.DoesNotExistError)

    if signatory_row.status != "Pending":
        frappe.throw(
            _("This signing slot has already been completed."),
            frappe.ValidationError,
        )

    # Capture client IP
    remote_addr = ""
    try:
        remote_addr = frappe.local.request.environ.get("REMOTE_ADDR", "")
    except AttributeError:
        pass

    # Record signature
    signatory_row.signature_data = frappe.utils.cstr(signature_b64)
    signatory_row.signed_at = frappe.utils.now_datetime()
    signatory_row.signature_ip = remote_addr
    signatory_row.status = "Signed"

    contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()

    # Advance the contract workflow
    _transition(contract)

    return {"status": "signed"}
