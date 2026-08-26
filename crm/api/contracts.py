"""
crm/api/contracts.py — CRM Contract Signing State Machine

Story:  cs-s1-2
BRD:    BRD_Contract_Signing.docx
ADR:    ADR_Contract_Signing.docx

Security model:
- generate / download_pdf / resend_invitation require Sales Manager or System Manager.
- Public endpoints (request_otp, verify_otp, get_contract, sign) are guest-accessible.
- Identity chain: random invitation token (stored on the signatory row) → 6-digit OTP
  → random signing-session token (stored on the row). All tokens are opaque, high-entropy
  secrets generated with frappe.generate_hash(); none are derived from the request, so a
  token can be regenerated at will and rotating the signing key never invalidates them.
- hmac.compare_digest() is used for ALL token/OTP comparisons — never ==.

Rules enforced:
- frappe.get_list() for every SELECT — no frappe.db.sql() SELECTs, no frappe.get_all().
- ignore_permissions=True only on system/scheduler paths — marked # SYSTEM-INTERNAL.
- No f-strings in log/error messages — % formatting only.
- All transactional email renders through crm.api._email.branded_email_html.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time

import frappe
from frappe import _

from crm.api._email import branded_email_html, otp_code_block
from crm.api._timeline import log_deal_event

_OTP_EXPIRY_SECONDS = 600    # 10 minutes
_SIGN_EXPIRY_SECONDS = 7200  # 2 hours
_INVITE_EXPIRY_SECONDS = 604800  # 7 days
_MAX_OTP_ATTEMPTS = 3
_TOKEN_LENGTH = 48


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_signing_key():
    """Return the optin_signing_key; auto-generates if absent. Used only for OTP hashing."""
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


def _gen_token():
    """Return an opaque, high-entropy, URL-safe token."""
    return frappe.generate_hash(length=_TOKEN_LENGTH)


def _network_for_contract(contract_doc):
    """Resolve the branded-email network dict for a contract, or None. Never raises."""
    slug = frappe.utils.cstr(getattr(contract_doc, "network_slug", "") or "").strip()
    if not slug:
        return None
    try:
        from crm.api.optin import _get_network_doc
        return _get_network_doc(slug)
    except Exception:
        return None


def _resolve_network_slug(deal):
    """Best-effort: find the opt-in network slug for a deal via its submission. Never raises."""
    try:
        rows = frappe.get_list(
            "CRM Opt-In Submission",
            filters={"deal": deal},
            fields=["network_slug"],
            order_by="creation desc",
            limit=1,
            ignore_permissions=True,  # SYSTEM-INTERNAL
        )
        if rows:
            return frappe.utils.cstr(rows[0].get("network_slug") or "").strip()
    except Exception:
        pass
    return ""


def _check_contract_rate_limit(limit=10, window=60):
    """IP-based rate limit for guest contract signing endpoints (10 req/min/IP)."""
    request = getattr(frappe.local, "request", None)
    ip = request.environ.get("REMOTE_ADDR", "unknown") if request else "cli"
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


def _get_signatory_row(contract_doc, role):
    """Return the first signatory child row matching role, or None."""
    for row in (contract_doc.signatories or []):
        if row.signatory_role == role:
            return row
    return None


def _load_signatory(contract, role):
    """Load the contract doc and the signatory row for role. Raise if either is missing."""
    contract_doc = frappe.get_doc("CRM Contract", contract)
    signatory_row = _get_signatory_row(contract_doc, role)
    if not signatory_row:
        frappe.throw(_("Signatory role not found in this contract."), frappe.DoesNotExistError)
    return contract_doc, signatory_row


def _validate_invite(signatory_row, token):
    """Raise AuthenticationError unless token matches the stored, unexpired invite token."""
    stored = frappe.utils.cstr(signatory_row.invite_token or "")
    if (
        not stored
        or not signatory_row.invite_expiry
        or frappe.utils.now_datetime() > signatory_row.invite_expiry
    ):
        frappe.throw(_("This signing link has expired."), frappe.AuthenticationError)
    if not hmac.compare_digest(stored, frappe.utils.cstr(token)):
        frappe.throw(_("Invalid signing link."), frappe.AuthenticationError)


def _validate_signing(signatory_row, token):
    """Raise AuthenticationError unless token matches the stored, unexpired signing token."""
    stored = frappe.utils.cstr(signatory_row.signing_token or "")
    if (
        not stored
        or not signatory_row.signing_expiry
        or frappe.utils.now_datetime() > signatory_row.signing_expiry
    ):
        frappe.throw(_("Session expired. Please request a new code."), frappe.AuthenticationError)
    if not hmac.compare_digest(stored, frappe.utils.cstr(token)):
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)


def _attempts_cache_key(contract, role):
    return "contract_otp_attempts:%s:%s" % (contract, role)


def _signing_link(contract_name, role, token):
    """Build the guest signing-portal URL for an invitation token."""
    return frappe.utils.get_url(
        "/sign-contract?contract=%s&role=%s&token=%s"
        % (contract_name, role.replace(" ", "+"), token)
    )


def _issue_and_send_invitation(contract_doc, signatory_row, now=True):
    """
    Mint a fresh invitation token on the signatory row, persist it, and email the
    signatory a branded invitation with a Sign CTA. The caller is responsible for
    having a saved contract_doc; this saves + commits its own token write.

    now=False queues the email (email queue) instead of sending synchronously — use it
    on guest request paths so the guest isn't blocked on third-party SMTP delivery.
    """
    token = _gen_token()
    signatory_row.invite_token = token
    signatory_row.invite_expiry = frappe.utils.add_to_date(
        frappe.utils.now_datetime(), seconds=_INVITE_EXPIRY_SECONDS
    )
    contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()

    role = frappe.utils.cstr(signatory_row.signatory_role)
    link = _signing_link(contract_doc.name, role, token)
    network = _network_for_contract(contract_doc)
    name = frappe.utils.escape_html(frappe.utils.cstr(signatory_row.signatory_name))

    try:
        frappe.sendmail(
            recipients=[signatory_row.signatory_email],
            subject="Action Required: Sign Your CareverseHIMS Contract",
            message=branded_email_html(
                network,
                heading="Contract ready for your signature",
                intro_html=(
                    "<p style='margin:0 0 6px'>Dear %s,</p>"
                    "<p style='margin:0'>You have been asked to review and sign a "
                    "CareverseHIMS contract. Use the button below to open the secure "
                    "signing portal — you'll confirm your identity with a one-time code.</p>"
                    % name
                ),
                cta_label="Review & Sign Contract",
                cta_url=link,
                note_html=(
                    "This link expires in 7 days and is unique to you — please don't share it."
                ),
            ),
            now=now,
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "contracts._issue_and_send_invitation: email failed for %s / %s" % (
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
            # now=False: don't block the guest's sign request on witness-invite SMTP
            _issue_and_send_invitation(contract, witness_row, now=False)

    elif signed_count >= 2:
        # Both external parties have signed
        contract.workflow_state = "Awaiting Internal Approval"
        # status stays "Awaiting Signatures" (the only valid Select option for this state)
        contract.save(ignore_permissions=True)  # SYSTEM-INTERNAL
        frappe.db.commit()
        # Enqueue: this notifies the INTERNAL approvers, not the guest who just
        # signed. Running it inline (now=True) would block the guest's sign
        # request on third-party SMTP delivery. The worker still sends promptly
        # (now=True inside _notify_internal_approvers) so delivery isn't queued.
        frappe.enqueue(
            "crm.api.contracts._notify_internal_approvers",
            contract_name=contract_name,
            deal_name=contract.deal,
            queue="short",
            timeout=120,
        )
        log_deal_event(
            contract.deal,
            "Both facility parties signed contract %s — awaiting internal approval"
            % contract.name,
        )


def _notify_internal_approvers(contract_name, deal_name):
    """
    Fetch network_approver_1, network_approver_2, tiberbu_approver from the
    CRM Onboarding Request linked to the deal. If no ONB record exists, logs a
    warning and returns early — these fields do not exist on tabCRM Deal.
    Send a branded approval-request email to each approver found.
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

    # NOTE: approver fields live only on CRM Onboarding Request, not on CRM Deal.
    # If no onboarding request was found, log a warning and return — do NOT attempt
    # to query tabCRM Deal for columns that don't exist there (OperationalError).
    if not approver_names:
        frappe.log_error(
            "No CRM Onboarding Request linked to deal %s; cannot notify internal approvers "
            "for contract %s." % (deal_name, contract_name),
            "contracts._notify_internal_approvers: no onboarding request",
        )
        return

    network = None
    try:
        contract_doc = frappe.get_doc("CRM Contract", contract_name)
        network = _network_for_contract(contract_doc)
    except Exception:
        pass

    crm_url = frappe.utils.get_url("/crm/deals/%s" % deal_name) if deal_name else frappe.utils.get_url()

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
                message=branded_email_html(
                    network,
                    heading="Contract awaiting your approval",
                    intro_html=(
                        "<p style='margin:0 0 6px'>Hello,</p>"
                        "<p style='margin:0'>Both facility signatories have signed contract "
                        "<strong>%s</strong>. It now requires your internal approval before it "
                        "can be executed.</p>" % frappe.utils.escape_html(contract_name)
                    ),
                    cta_label="Open in CRM",
                    cta_url=crm_url,
                ),
                now=True,
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
    add two signatory rows, and send the invitation to the Facility Signatory.

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
    contract.network_slug = _resolve_network_slug(deal)

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

    # Send invitation to the Facility Signatory immediately
    signatory_row = _get_signatory_row(contract, "Facility Signatory")
    if signatory_row:
        _issue_and_send_invitation(contract, signatory_row)

    log_deal_event(
        deal,
        "Contract %s generated — signing invitation sent to %s"
        % (contract.name, facility_signatory_email),
    )
    return {"contract": contract.name}


@frappe.whitelist()
def resend_invitation(contract, role):
    """
    Regenerate the invitation link for a still-pending signatory and re-send the
    branded invitation email. Requires: Sales Manager or System Manager role.

    Returns: {status: "sent", email: <signatory_email>}
    """
    _check_crm_role()

    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()

    contract_doc, signatory_row = _load_signatory(contract, role)

    if signatory_row.status != "Pending":
        frappe.throw(
            _("This signatory has already completed signing — nothing to resend."),
            frappe.ValidationError,
        )

    # A witness is only invited after the principal signs; block premature resend.
    if role == "Facility Witness":
        principal = _get_signatory_row(contract_doc, "Facility Signatory")
        if principal and principal.status != "Signed":
            frappe.throw(
                _("The witness is invited automatically once the facility signatory has signed."),
                frappe.ValidationError,
            )

    _issue_and_send_invitation(contract_doc, signatory_row)

    log_deal_event(
        contract_doc.deal,
        "Signing invitation for %s re-sent to %s (contract %s)"
        % (role, signatory_row.signatory_email, contract),
    )
    return {"status": "sent", "email": signatory_row.signatory_email}


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
def request_otp(contract, role, token):
    """
    Validate the invitation token, generate a 6-digit OTP, store its HMAC on the
    signatory row, and email it to the signatory.

    Returns: {status: "sent"}
    """
    _check_contract_rate_limit()
    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()

    contract_doc, signatory_row = _load_signatory(contract, role)
    _validate_invite(signatory_row, token)

    if signatory_row.status != "Pending":
        frappe.throw(
            _("This signing slot has already been completed."),
            frappe.ValidationError,
        )

    # Generate 6-digit OTP with a cryptographically-secure RNG (this is an auth factor)
    otp = str(secrets.randbelow(900000) + 100000)
    key = _get_signing_key()
    signatory_row.otp_hash = _hmac_hex(key, otp)
    signatory_row.otp_expiry = frappe.utils.add_to_date(
        frappe.utils.now_datetime(), seconds=_OTP_EXPIRY_SECONDS
    )
    signatory_row.otp_used = 0
    contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()

    # Reset attempt counter in Redis
    frappe.cache().set_value(
        _attempts_cache_key(contract, role),
        0,
        expires_in_sec=_OTP_EXPIRY_SECONDS + 120,
    )

    # Send branded OTP email
    network = _network_for_contract(contract_doc)
    try:
        frappe.sendmail(
            recipients=[signatory_row.signatory_email],
            subject="Your CareverseHIMS Contract Signing Code",
            message=branded_email_html(
                network,
                heading="Verify your identity",
                intro_html=(
                    "<p style='margin:0 0 6px'>Dear %s,</p>"
                    "<p style='margin:0'>Use the code below to sign your CareverseHIMS "
                    "contract.</p>"
                    % frappe.utils.escape_html(frappe.utils.cstr(signatory_row.signatory_name))
                ),
                highlight_html=otp_code_block(otp, network),
                note_html=(
                    "This code expires in 10 minutes. Do not share it with anyone."
                ),
            ),
            now=True,
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "contracts.request_otp: OTP email failed for %s / %s" % (contract, role),
        )

    return {"status": "sent"}


@frappe.whitelist(allow_guest=True)
def verify_otp(contract, role, token, otp):
    """
    Validate the 6-digit OTP against the stored HMAC.
    On success: clear otp_hash, issue a short-lived signing-session token.

    Returns: {signing_token, expiry, signatory_name, signatory_role}
    The contract HTML is fetched separately via get_contract once the session token
    is issued, so it is intentionally not returned here.

    All failures raise frappe.AuthenticationError with a generic message.
    """
    _check_contract_rate_limit()
    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()
    otp = frappe.utils.cstr(otp).strip()

    contract_doc, signatory_row = _load_signatory(contract, role)
    _validate_invite(signatory_row, token)

    if signatory_row.status != "Pending":
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    # Check OTP expiry / reuse. otp_used blocks a consumed code even if a stale
    # otp_hash lingers; a fresh request_otp resets it to 0.
    if (
        not signatory_row.otp_hash
        or frappe.utils.cint(signatory_row.otp_used)
        or not signatory_row.otp_expiry
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
    key = _get_signing_key()
    stored_hash = frappe.utils.cstr(signatory_row.otp_hash or "")
    expected_hash = _hmac_hex(key, otp)

    if not hmac.compare_digest(stored_hash, expected_hash):
        frappe.throw(_("Verification failed."), frappe.AuthenticationError)

    # OTP valid — clear it, reset attempts, and issue a signing-session token
    signing_token = _gen_token()
    signatory_row.otp_hash = ""
    signatory_row.otp_used = 1
    signatory_row.signing_token = signing_token
    signatory_row.signing_expiry = frappe.utils.add_to_date(
        frappe.utils.now_datetime(), seconds=_SIGN_EXPIRY_SECONDS
    )
    contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()
    frappe.cache().set_value(attempts_key, 0, expires_in_sec=60)

    return {
        "signing_token": signing_token,
        "expiry": int(time.time()) + _SIGN_EXPIRY_SECONDS,
        "signatory_name": frappe.utils.cstr(signatory_row.signatory_name or ""),
        "signatory_role": frappe.utils.cstr(signatory_row.signatory_role or ""),
    }


@frappe.whitelist(allow_guest=True)
def get_contract(signing_token, contract, role):
    """
    Return contract HTML and signatory metadata for the signing portal.
    Validates the signing-session token before returning any data.

    Returns: {contract_html, signatory_name, signatory_role, contract_date}
    """
    _check_contract_rate_limit()
    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()

    contract_doc, signatory_row = _load_signatory(contract, role)
    _validate_signing(signatory_row, signing_token)

    return {
        "contract_html": frappe.utils.cstr(contract_doc.contract_html or ""),
        "signatory_name": frappe.utils.cstr(signatory_row.signatory_name or ""),
        "signatory_role": role,
        "contract_date": frappe.utils.cstr(contract_doc.contract_date or ""),
    }


@frappe.whitelist(allow_guest=True)
def sign(signing_token, contract, role, signature_b64):
    """
    Record the signature on the signatory row and advance the workflow via _transition().

    Returns: {status: "signed"}
    """
    _check_contract_rate_limit()
    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()

    contract_doc, signatory_row = _load_signatory(contract, role)
    _validate_signing(signatory_row, signing_token)

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
    # Consume the signing-session token so it can't be replayed
    signatory_row.signing_token = ""

    contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()

    # Advance the contract workflow
    _transition(contract)

    return {"status": "signed"}
