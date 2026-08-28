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


def _resolve_user_identity(user, fallback_name="", fallback_email=""):
    """Resolve a User link to {full_name, email}, preferring live User values but
    falling back to any stored/label values. Email is lower-cased. Never raises."""
    name = frappe.utils.cstr(fallback_name or "").strip()
    email = frappe.utils.cstr(fallback_email or "").strip().lower()
    user = frappe.utils.cstr(user or "").strip()
    if user:
        try:
            u = frappe.db.get_value("User", user, ["full_name", "email"], as_dict=True)
            if u:
                name = frappe.utils.cstr(u.full_name or name).strip()
                email = frappe.utils.cstr(u.email or email).strip().lower()
        except Exception:
            pass
    return {"full_name": name, "email": email}


def _network_signers(network_slug):
    """Configured co-signatories for a network → [{full_name, email}]. Network
    signers are external people keyed by email (name + email, no Frappe User). A
    network's name IS its slug (autoname field:slug)."""
    network_slug = frappe.utils.cstr(network_slug or "").strip()
    if not network_slug or not frappe.db.exists("CRM Opt-In Network", network_slug):
        return []
    rows = frappe.get_list(
        "CRM Network Signer",
        filters={
            "parent": network_slug,
            "parenttype": "CRM Opt-In Network",
            "parentfield": "network_signers",
        },
        fields=["full_name", "email"],
        order_by="idx asc",
        ignore_permissions=True,  # SYSTEM-INTERNAL
    )
    signers = []
    for r in rows:
        email = frappe.utils.cstr(r.get("email") or "").strip()
        if email:
            signers.append({
                "full_name": frappe.utils.cstr(r.get("full_name") or "").strip() or email,
                "email": email,
            })
    return signers


def _tiberbu_signer():
    """Global Tiberbu co-signatory from CRM Opt-In Settings → {full_name, email} or None."""
    user = ""
    # A Single always "exists" by name; read the field directly.
    try:
        user = frappe.utils.cstr(
            frappe.db.get_single_value("CRM Opt-In Settings", "tiberbu_signatory") or ""
        ).strip()
    except Exception:
        user = ""
    if not user:
        return None
    ident = _resolve_user_identity(user)
    return ident if ident["email"] else None


def _facility_witness_from_deal(deal):
    """Facility witness captured on the deal's latest opt-in submission → {name, email}."""
    deal = frappe.utils.cstr(deal or "").strip()
    if not deal:
        return {"name": "", "email": ""}
    rows = frappe.get_list(
        "CRM Opt-In Submission",
        filters={"deal": deal},
        fields=["facility_witness_name", "facility_witness_email"],
        order_by="creation desc",
        limit=1,
        ignore_permissions=True,  # SYSTEM-INTERNAL
    )
    if rows:
        return {
            "name": frappe.utils.cstr(rows[0].get("facility_witness_name") or "").strip(),
            "email": frappe.utils.cstr(rows[0].get("facility_witness_email") or "").strip().lower(),
        }
    return {"name": "", "email": ""}


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


def _get_signatory_row(contract_doc, role, row_name=None):
    """Return the signatory child row for role, or None.

    A role can legitimately repeat on one contract — a network with several
    configured signers yields several "Network Signatory" rows. When row_name
    (the child docname) is given, the exact row is returned so operations never
    hit the wrong person; without it, the first row for the role is returned
    (correct for the singular roles: facility signatory/witness, Tiberbu).
    """
    rows = [r for r in (contract_doc.signatories or []) if r.signatory_role == role]
    if row_name:
        for r in rows:
            if r.name == row_name:
                return r
        return None
    return rows[0] if rows else None


def _load_signatory(contract, role, row_name=None):
    """Load the contract doc and the signatory row for role. Raise if either is missing."""
    contract_doc = frappe.get_doc("CRM Contract", contract)
    signatory_row = _get_signatory_row(contract_doc, role, row_name)
    if not signatory_row:
        frappe.throw(_("Signatory role not found in this contract."), frappe.DoesNotExistError)
    return contract_doc, signatory_row


def _load_signatory_by_token(contract, role, token, token_field):
    """Resolve a signatory row for the guest signing flow by matching its token.

    Roles that repeat (multiple Network Signatory rows) each carry a unique
    invite/signing token, so the token — not the role — identifies the person.
    Falls back to the first role row when no token matches, so the downstream
    token validator raises the usual "invalid/expired link" error unchanged.
    """
    contract_doc = frappe.get_doc("CRM Contract", contract)
    rows = [r for r in (contract_doc.signatories or []) if r.signatory_role == role]
    if not rows:
        frappe.throw(_("Signatory role not found in this contract."), frappe.DoesNotExistError)
    token = frappe.utils.cstr(token or "")
    if token:
        for r in rows:
            stored = frappe.utils.cstr(r.get(token_field) or "")
            if stored and hmac.compare_digest(stored, token):
                return contract_doc, r
    return contract_doc, rows[0]


def _invalidate_signature(row):
    """Void a captured signature and its signing artefacts.

    Used when an edit means the signature no longer belongs to the current
    person/terms, so the audit trail never shows a signature for a signing event
    that no longer holds. Clears the signature image, IP, timestamp, the consumed
    OTP and any live signing session. Invite handling is left to the caller.
    """
    row.signature_data = None
    row.signature_ip = None
    row.signed_at = None
    row.otp_hash = None
    row.otp_expiry = None
    row.otp_used = 0
    row.signing_token = None
    row.signing_expiry = None


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


def _attempts_cache_key(contract, role, row_name=""):
    # row_name disambiguates repeated roles (multiple Network Signatory rows) so
    # each signatory has its own brute-force counter rather than a shared one.
    return "contract_otp_attempts:%s:%s:%s" % (contract, role, row_name or "")


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


_COUNTERPARTY_ROLES = ("Network Signatory", "Tiberbu Signatory")


def _transition(contract_name):
    """
    Advance the contract workflow after a signatory signs. Ordered, idempotent —
    safe to call after every signature; each stage guards on invite_token so a
    party is invited exactly once.

    Stages:
      A. Facility Signatory signs        → invite Facility Witness.
      B. Facility side complete (both     → invite EVERY Network Signatory and the
         facility parties signed)           Tiberbu Signatory IN PARALLEL, each with
                                            a 7-day link; they sign whenever they like
                                            within the window (same OTP + pad portal).
      C. All signatories signed          → status/workflow_state = "Fully Executed".
    """
    contract = frappe.get_doc("CRM Contract", contract_name)
    sigs = list(contract.signatories or [])
    if not sigs:
        return

    fac_sig = _get_signatory_row(contract, "Facility Signatory")
    fac_wit = _get_signatory_row(contract, "Facility Witness")
    fac_sig_signed = bool(fac_sig) and fac_sig.status == "Signed"
    # A missing witness row (defensive) counts as "not blocking".
    fac_wit_signed = (fac_wit is None) or (fac_wit.status == "Signed")
    facility_complete = fac_sig_signed and fac_wit_signed

    # Stage A → B: facility witness is invited only once the facility signatory signs.
    # now=True: send synchronously so the invitation is delivered via SES rather than
    # left sitting in the Email Queue awaiting a scheduled flush.
    if fac_sig_signed and fac_wit and fac_wit.status == "Pending" and not fac_wit.invite_token:
        _issue_and_send_invitation(contract, fac_wit, now=True)

    # Stage B → C: once both facility parties have signed, invite the network +
    # tiberbu co-signatories in parallel. Guarded on invite_token so re-entry is safe.
    if facility_complete:
        invited_any = False
        for row in sigs:
            if (
                row.signatory_role in _COUNTERPARTY_ROLES
                and row.status == "Pending"
                and not row.invite_token
            ):
                _issue_and_send_invitation(contract, row, now=True)
                invited_any = True
        if invited_any:
            _set_contract_state(contract, "Awaiting Counterparty Signatures")
            log_deal_event(
                contract.deal,
                "Both facility parties signed contract %s — network & Tiberbu "
                "co-signatories invited (7-day link)" % contract.name,
            )

    # Done: every signatory has signed.
    if sigs and all(s.status == "Signed" for s in sigs):
        _set_contract_state(contract, "Fully Executed", status="Fully Executed")
        log_deal_event(
            contract.deal,
            "All parties signed contract %s — fully executed" % contract.name,
        )


def _set_contract_state(contract, workflow_state, status=None):
    """Persist workflow_state (and optionally status) on a contract. SYSTEM-INTERNAL."""
    contract.workflow_state = workflow_state
    if status:
        contract.status = status
    contract.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()


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
def get_network_signatories(deal="", network_slug=""):
    """
    Resolve the co-signatories that will be seeded onto a contract: every
    Network Signatory configured on the deal's network plus the global Tiberbu
    Signatory. Powers the auto-populate on the Quote/Contracting page.

    Requires: Sales Manager or System Manager role.
    Returns: {network_slug, signers: [{full_name, email, signer_role}]}
    """
    _check_crm_role()

    deal = frappe.utils.cstr(deal).strip()
    network_slug = frappe.utils.cstr(network_slug).strip()
    if not network_slug and deal:
        network_slug = _resolve_network_slug(deal) or ""

    signers = [dict(s, signer_role="Network Signatory") for s in _network_signers(network_slug)]
    tb = _tiberbu_signer()
    if tb:
        signers.append(dict(tb, signer_role="Tiberbu Signatory"))

    return {"network_slug": network_slug, "signers": signers}


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
    Create a CRM Contract for a deal, render contract HTML from active T&C, and
    seed all signatory rows: Facility Signatory, Facility Witness, every configured
    Network Signatory, and the global Tiberbu Signatory. Only the Facility Signatory
    is invited immediately; the rest are invited by the state machine in order
    (see _transition). network_approver_* params are legacy no-ops — the network /
    tiberbu co-signatories now come from configuration.

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

    # Witness falls back to what the facility captured on their opt-in submission,
    # so the exec need not re-key it.
    if not facility_witness_email or not facility_witness_name:
        ois_witness = _facility_witness_from_deal(deal)
        facility_witness_name = facility_witness_name or ois_witness["name"]
        facility_witness_email = facility_witness_email or ois_witness["email"]

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
            # The T&C template needs the full network/contact/pricing context the
            # customer accepted; a minimal {deal, date} context raises UndefinedError
            # ('network' is undefined) and leaves contract_html empty.
            from crm.api.optin import build_tc_context_for_deal

            context = build_tc_context_for_deal(deal) or {}
            context.setdefault("deal", deal)
            context.setdefault("quote", quote)
            context.setdefault("facility_signatory_name", facility_signatory_name)
            context.setdefault("date", frappe.utils.format_date(frappe.utils.today()))
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
    network_slug = _resolve_network_slug(deal)
    contract.network_slug = network_slug

    # Row 1: Facility Signatory (invited immediately below).
    contract.append("signatories", {
        "signatory_name": facility_signatory_name,
        "signatory_email": facility_signatory_email,
        "signatory_role": "Facility Signatory",
        "status": "Pending",
        "is_witness": 0,
    })

    # Row 2: Facility Witness (invited once the facility signatory signs).
    contract.append("signatories", {
        "signatory_name": facility_witness_name,
        "signatory_email": facility_witness_email,
        "signatory_role": "Facility Witness",
        "status": "Pending",
        "is_witness": 1,
        "witnessing_for": facility_signatory_name,
    })

    # Rows 3..N: network co-signatories from the network configuration, invited in
    # parallel with the Tiberbu signatory once the facility side completes.
    for signer in _network_signers(network_slug):
        contract.append("signatories", {
            "signatory_name": signer["full_name"] or signer["email"],
            "signatory_email": signer["email"],
            "signatory_role": "Network Signatory",
            "status": "Pending",
            "is_witness": 0,
        })

    # Row N+1: the global Tiberbu co-signatory.
    tb = _tiberbu_signer()
    if tb:
        contract.append("signatories", {
            "signatory_name": tb["full_name"] or tb["email"],
            "signatory_email": tb["email"],
            "signatory_role": "Tiberbu Signatory",
            "status": "Pending",
            "is_witness": 0,
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
def resend_invitation(contract, role, row_name=None):
    """
    Regenerate the invitation link for a still-pending signatory and re-send the
    branded invitation email. Requires: Sales Manager or System Manager role.

    row_name (the signatory child docname) targets the exact row when a role
    repeats (multiple Network Signatory rows); omit it for the singular roles.

    Returns: {status: "sent", email: <signatory_email>}
    """
    _check_crm_role()

    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()
    row_name = frappe.utils.cstr(row_name).strip() or None

    contract_doc, signatory_row = _load_signatory(contract, role, row_name)

    if signatory_row.status != "Pending":
        frappe.throw(
            _("This signatory has already completed signing — nothing to resend."),
            frappe.ValidationError,
        )

    # Signatories are invited in order (facility signatory → witness → network +
    # tiberbu in parallel). A row with no invite_token hasn't reached its turn yet,
    # so there is nothing to resend — block the premature resend for every role.
    if not signatory_row.invite_token:
        frappe.throw(
            _("This signatory hasn't been invited yet — they are invited "
              "automatically once it is their turn to sign."),
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
def update_signatory(contract, role, name, email, row_name=None):
    """
    Update the name/email of a signatory. Requires: Sales Manager or System
    Manager role.

    row_name (the signatory child docname) targets the exact row when a role
    repeats (multiple Network Signatory rows) — without it a repeated role would
    resolve to the first row and could invalidate the wrong person's signature.
    Omit it for the singular roles (facility signatory/witness, Tiberbu).

    Any row is editable — Pending, Declined, or already Signed. Editing a SIGNED
    signatory invalidates the captured signature: the signature image, IP,
    timestamp and any consumed OTP are cleared and the row is reset to Pending so
    the (possibly new) person signs afresh. If the row had an outstanding invite
    OR was signed, a fresh signing link is issued and emailed to the current
    address (invalidating the old one); otherwise the exec can Resend.

    Returns: {status: "updated", email, resent: bool}
    """
    _check_crm_role()

    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()
    name = frappe.utils.cstr(name).strip()
    email = frappe.utils.cstr(email).strip().lower()
    row_name = frappe.utils.cstr(row_name).strip() or None

    if not name or not email:
        frappe.throw(_("Signatory name and email are required."))

    contract_doc, signatory_row = _load_signatory(contract, role, row_name)

    was_signed = signatory_row.status == "Signed"
    email_changed = (
        frappe.utils.cstr(signatory_row.signatory_email or "").strip().lower() != email
    )

    signatory_row.signatory_name = name
    signatory_row.signatory_email = email

    # Editing a signed row means the old signature no longer belongs to this
    # (possibly new) person — clear it and the consumed OTP so the audit trail
    # never shows a signature for someone who did not sign the current terms.
    if was_signed:
        _invalidate_signature(signatory_row)

    # A corrected non-Pending row (Declined, or a just-invalidated Signed one)
    # returns to Pending so it re-enters the signing flow.
    if signatory_row.status != "Pending":
        signatory_row.status = "Pending"
    # The facility witness attests to the facility signatory's signing event.
    if role == "Facility Signatory":
        witness = _get_signatory_row(contract_doc, "Facility Witness")
        if witness:
            # Keep the "witnessing_for" label in sync when the principal is renamed.
            witness.witnessing_for = name
            # If the principal's signature was just invalidated, the witness's
            # attestation is now void — it witnessed an event that no longer
            # exists. Reset it so it is re-invited (after the principal re-signs)
            # and re-witnesses the fresh signature.
            if was_signed and witness.status == "Signed":
                _invalidate_signature(witness)
                witness.status = "Pending"
                witness.invite_token = None
                witness.invite_expiry = None

    # A re-opened signed row means the contract is no longer fully executed —
    # walk the contract-level state back to the awaiting stage for this party so
    # the UI never shows "Fully Executed" alongside a Pending signatory.
    if was_signed:
        contract_doc.status = "Awaiting Signatures"
        contract_doc.workflow_state = (
            "Awaiting Counterparty Signatures"
            if role in _COUNTERPARTY_ROLES
            else "Awaiting Facility Signature"
        )

    # Re-issue a fresh link when the address changed on an already-invited row,
    # or whenever a signed row was edited (they must sign again). Re-issuing mints
    # a new token (invalidating the stale link), emails it, and saves + commits.
    already_invited = bool(signatory_row.invite_token)
    resent = False
    if was_signed or (email_changed and already_invited):
        _issue_and_send_invitation(contract_doc, signatory_row)
        resent = True
    else:
        contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
        frappe.db.commit()

    log_deal_event(
        contract_doc.deal,
        "Signatory %s updated on contract %s%s"
        % (role, contract, (" — new invitation sent to %s" % email) if resent else ""),
    )
    return {"status": "updated", "email": email, "resent": resent}


@frappe.whitelist()
def add_signatory(contract, role, name, email):
    """
    Add a Network/Tiberbu co-signatory row to a contract that is missing it —
    e.g. a contract generated before co-signatories were wired, or where the
    network/Tiberbu configuration changed after generation.
    Requires: Sales Manager or System Manager role.

    The new row is Pending and un-invited: it is invited automatically once the
    facility side has signed (see _transition), or the exec can Resend. A
    Tiberbu Signatory is unique per contract; a Network Signatory is deduped on
    email so the same person is not added twice.

    Returns: {status: "added", role, email}
    """
    _check_crm_role()

    contract = frappe.utils.cstr(contract).strip()
    role = frappe.utils.cstr(role).strip()
    name = frappe.utils.cstr(name).strip()
    email = frappe.utils.cstr(email).strip().lower()

    if role not in _COUNTERPARTY_ROLES:
        frappe.throw(_("Only Network and Tiberbu co-signatories can be added here."))
    if not name or not email:
        frappe.throw(_("Signatory name and email are required."))

    contract_doc = frappe.get_doc("CRM Contract", contract)

    for row in (contract_doc.signatories or []):
        if row.signatory_role != role:
            continue
        # Tiberbu is singular; a Network signer is unique by email.
        if role == "Tiberbu Signatory" or (
            frappe.utils.cstr(row.signatory_email or "").strip().lower() == email
        ):
            frappe.throw(_("This co-signatory is already on the contract."))

    contract_doc.append(
        "signatories",
        {
            "signatory_name": name,
            "signatory_email": email,
            "signatory_role": role,
            "status": "Pending",
            "is_witness": 0,
        },
    )
    contract_doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()

    log_deal_event(
        contract_doc.deal,
        "Co-signatory %s (%s) added to contract %s" % (role, email, contract),
    )

    # If the facility side has already signed (the common legacy case — the
    # contract predates co-signing), the new counterparty would otherwise sit
    # Pending and un-invited forever, because invitations are only issued from
    # _transition on a signature event. _transition is ordered + idempotent
    # (guards on invite_token) so it safely invites the new row now if it is due.
    _transition(contract)

    return {"status": "added", "role": role, "email": email}


def _sync_network_signer_on_contract(contract, name, email, original_email):
    """Reflect a network-config signer change onto a live contract's Network
    Signatory row. Reuses the whitelisted row operations so the Signed-row
    invalidation + re-invite semantics (see update_signatory) are identical:
    edit the matching row (found by its original email, or by the new email when
    the row was already renamed) or add a new Pending row when the contract has
    none for that person yet.

    The new email is matched as a fallback so a rename to an address already on
    the contract updates that row rather than making add_signatory throw
    "already on the contract" (which would strand the just-committed config change).
    """
    contract_doc = frappe.get_doc("CRM Contract", contract)
    old_match = frappe.utils.cstr(original_email or email).strip().lower()
    new_match = frappe.utils.cstr(email).strip().lower()
    net_rows = [
        r for r in (contract_doc.signatories or [])
        if r.signatory_role == "Network Signatory"
    ]
    row = next(
        (r for r in net_rows
         if frappe.utils.cstr(r.signatory_email or "").strip().lower() == old_match),
        None,
    ) or next(
        (r for r in net_rows
         if frappe.utils.cstr(r.signatory_email or "").strip().lower() == new_match),
        None,
    )
    if row:
        update_signatory(
            contract=contract, role="Network Signatory",
            name=name, email=email, row_name=row.name,
        )
        return "updated"
    add_signatory(contract=contract, role="Network Signatory", name=name, email=email)
    return "added"


@frappe.whitelist()
def save_network_signer(network_slug, name, email, original_email="", contract=""):
    """
    Add, edit, or replace a Network Signatory in the NETWORK CONFIGURATION —
    the source of truth (CRM Opt-In Network.network_signers), so the change
    persists for every future contract for that network. Network signers are
    external people keyed by name + email (no Frappe User). When `contract` is
    given the change is also synced onto that live contract (see
    _sync_network_signer_on_contract). Requires: Sales Manager or System Manager.

    - original_email set → the matching config row is updated/replaced.
    - original_email blank → a new signer is appended (deduped by email).

    This is the Network counterpart to the per-contract add_signatory. The
    Tiberbu Signatory is deliberately NOT handled here — it is a global singleton
    in CRM Opt-In Settings and must never be overwritten from a single deal, so
    Tiberbu add/edit stays per-contract via add_signatory / update_signatory.

    Returns: {status, network_slug, email, contract_synced}
    """
    _check_crm_role()

    network_slug = frappe.utils.cstr(network_slug).strip()
    name = frappe.utils.cstr(name).strip()
    email = frappe.utils.cstr(email).strip().lower()
    original_email = frappe.utils.cstr(original_email).strip().lower()
    contract = frappe.utils.cstr(contract).strip()

    if not network_slug or not frappe.db.exists("CRM Opt-In Network", network_slug):
        frappe.throw(_("Unknown opt-in network for this deal — cannot save a network signer."))
    if not name or not email:
        frappe.throw(_("Signer name and email are required."))

    net = frappe.get_doc("CRM Opt-In Network", network_slug)
    rows = net.network_signers or []

    # When editing, match the config row by its original email. If the signer
    # isn't in the config yet (e.g. it lives only on the contract), we append it —
    # the whole point is to write it back — rather than error out.
    target = None
    if original_email:
        target = next(
            (r for r in rows
             if frappe.utils.cstr(r.email or "").strip().lower() == original_email),
            None,
        )

    # The new email must not collide with a DIFFERENT existing signer row.
    for r in rows:
        if r is target:
            continue
        if frappe.utils.cstr(r.email or "").strip().lower() == email:
            frappe.throw(_("A network signer with this email already exists."))

    if target:
        target.full_name = name
        target.email = email
    else:
        net.append("network_signers", {"full_name": name, "email": email})

    net.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    frappe.db.commit()

    contract_synced = ""
    if contract and frappe.db.exists("CRM Contract", contract):
        contract_synced = _sync_network_signer_on_contract(contract, name, email, original_email)
        log_deal_event(
            frappe.get_value("CRM Contract", contract, "deal"),
            "Network signer %s saved to network %s config and %s on contract %s"
            % (email, network_slug, contract_synced, contract),
        )

    return {
        "status": "saved",
        "network_slug": network_slug,
        "email": email,
        "contract_synced": contract_synced,
    }


@frappe.whitelist()
def download_pdf(contract):
    """
    Return a base64-encoded PDF of the FULL executed contract:
      1. The signed Terms & Conditions body.
      2. A signature block — each signatory's name, role, rendered signature
         image, timestamp and IP (or a wet-ink line where unsigned/printing).
      3. An appended "Certificate of Completion" audit page (parties, per-signatory
         timestamps/IPs, T&C integrity hash, execution status).

    Requires: Sales Manager or System Manager role.
    Returns: {pdf_b64: <base64 string>}
    """
    _check_crm_role()

    contract = frappe.utils.cstr(contract).strip()
    if not frappe.db.exists("CRM Contract", contract):
        frappe.throw(_("Contract not found."), frappe.DoesNotExistError)

    contract_doc = frappe.get_doc("CRM Contract", contract)
    html = _build_contract_document_html(contract_doc)

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


def _build_contract_document_html(contract_doc):
    """Assemble the full print-ready executed-contract HTML (terms + signatures
    + certificate). Kept side-effect-free so it is safe to call for preview/PDF."""
    brand = _network_branding(contract_doc)
    accent = brand["accent"]

    # 1. Contract body. Prefer the stored (signed) HTML; regenerate from the linked
    #    T&C for legacy contracts whose contract_html was never populated.
    body = frappe.utils.cstr(contract_doc.contract_html or "").strip()
    if not body:
        body = _regenerate_contract_body(contract_doc)
    if not body:
        body = (
            "<p style='color:#991b1b'>The terms for this contract are unavailable. "
            "Please contact the issuer for the executed copy.</p>"
        )

    date_str = frappe.utils.format_date(contract_doc.contract_date) if contract_doc.contract_date else ""
    signatures = _render_signature_block(contract_doc, accent)
    certificate = _render_certificate_page(contract_doc, accent, date_str, brand)

    # Centered, branded masthead: network logo (falls back to a wordmark), the
    # network name, the agreement title, reference/date, and the issuer contact.
    logo_html = (
        "<img class='doc-logo' src='%s' alt='%s'/>"
        % (frappe.utils.escape_html(brand["logo"]), frappe.utils.escape_html(brand["display_name"]))
        if brand["logo"]
        else ""
    )
    contact_html = (
        "<div class='doc-contact'>%s</div>" % frappe.utils.escape_html(brand["contact_email"])
        if brand["contact_email"]
        else ""
    )
    footer_html = (
        "<div class='doc-footer'>%s</div>" % frappe.utils.escape_html(brand["footer_legal_name"])
        if brand["footer_legal_name"]
        else ""
    )

    return """<!doctype html>
<html><head><meta charset="utf-8"><style>
  @page {{ margin: 22mm 18mm; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #1f2937; font-size: 12px; line-height: 1.55; }}
  h1, h2, h3 {{ color: #111827; }}
  .doc-header {{ text-align: center; border-bottom: 3px solid {accent};
          padding-bottom: 16px; margin-bottom: 24px; }}
  .doc-logo {{ max-height: 64px; max-width: 220px; margin: 0 auto 12px; display: block; }}
  .doc-header .brand {{ font-size: 12px; letter-spacing: .12em; text-transform: uppercase;
          color: {accent}; font-weight: 700; }}
  .doc-header h1 {{ margin: 6px 0 4px; font-size: 22px; }}
  .doc-meta {{ color: #6b7280; font-size: 11px; }}
  .doc-contact {{ color: {accent}; font-size: 11px; margin-top: 5px; font-weight: 600; }}
  .doc-footer {{ margin-top: 30px; padding-top: 12px; border-top: 1px solid #e5e7eb;
          text-align: center; color: #9ca3af; font-size: 10px; }}
  .contract-body {{ margin-bottom: 8px; text-align: justify; }}
  .sig-section {{ margin-top: 28px; padding-top: 14px; border-top: 1px solid #e5e7eb; }}
  .sig-section h2 {{ font-size: 14px; margin-bottom: 12px; text-align: center; }}
  .sig-card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 14px;
          margin-bottom: 12px; page-break-inside: avoid; text-align: center; }}
  .sig-role {{ font-size: 10px; text-transform: uppercase; letter-spacing: .06em;
          color: {accent}; font-weight: 700; }}
  .sig-name {{ font-size: 14px; font-weight: 600; margin: 2px 0; }}
  .sig-img {{ height: 64px; margin: 6px auto; display: block; }}
  .sig-line {{ border-bottom: 1px solid #9ca3af; width: 260px; height: 40px; margin: 6px auto; }}
  .sig-meta {{ color: #6b7280; font-size: 10px; }}
  .cert-page {{ page-break-before: always; padding-top: 6px; }}
  .cert-title {{ text-align: center; margin-bottom: 4px; }}
  .cert-title .brand {{ color: {accent}; font-weight: 700; letter-spacing: .12em;
          text-transform: uppercase; font-size: 11px; }}
  .cert-title h2 {{ font-size: 18px; margin: 4px 0; }}
  table.cert {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  table.cert th, table.cert td {{ text-align: left; padding: 7px 8px; font-size: 11px;
          border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
  table.cert th {{ color: #6b7280; text-transform: uppercase; font-size: 9px; letter-spacing: .05em; }}
  .cert-kv {{ margin: 3px 0; font-size: 11px; }}
  .cert-kv b {{ display: inline-block; min-width: 130px; color: #6b7280; font-weight: 600; }}
  .hash {{ font-family: monospace; font-size: 10px; word-break: break-all; color: #374151; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 10px;
          font-weight: 700; background: {accent}; color: #fff; }}
</style></head><body>
  <div class="doc-header">
    {logo}
    <div class="brand">{network}</div>
    <h1>CareverseHIMS Subscription Agreement</h1>
    <div class="doc-meta">{ref}{date_bit}</div>
    {contact}
  </div>
  <div class="contract-body">{body}</div>
  {signatures}
  {footer}
  {certificate}
</body></html>""".format(
        accent=accent,
        logo=logo_html,
        network=frappe.utils.escape_html(brand["display_name"]),
        ref=frappe.utils.escape_html(contract_doc.name),
        date_bit=(" &middot; " + frappe.utils.escape_html(date_str)) if date_str else "",
        contact=contact_html,
        footer=footer_html,
        body=body,
        signatures=signatures,
        certificate=certificate,
    )


def _regenerate_contract_body(contract_doc):
    """Re-render the T&C body for legacy contracts with an empty contract_html."""
    tc_name = contract_doc.tc_document
    if not tc_name and frappe.db.exists("CRM Opt-In Settings", "CRM Opt-In Settings"):
        tc_name = frappe.get_single("CRM Opt-In Settings").active_tc_document
    if not tc_name or not frappe.db.exists("Terms and Conditions", tc_name):
        return ""
    try:
        tc_doc = frappe.get_doc("Terms and Conditions", tc_name)
        signatory = _get_signatory_row(contract_doc, "Facility Signatory")
        # Reuse the accepted network/contact/pricing context (see build_tc_context_for_deal);
        # without it the template raises 'network is undefined' and yields empty terms.
        from crm.api.optin import build_tc_context_for_deal

        context = build_tc_context_for_deal(contract_doc.deal) or {}
        context.setdefault("deal", contract_doc.deal)
        context.setdefault("quote", contract_doc.quote)
        context.setdefault("facility_signatory_name", signatory.signatory_name if signatory else "")
        context.setdefault(
            "date", frappe.utils.format_date(contract_doc.contract_date or frappe.utils.today())
        )
        return frappe.render_template(tc_doc.terms or "", context)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "contracts.download_pdf: legacy T&C re-render failed for %s" % contract_doc.name,
        )
        return ""


def _render_signature_block(contract_doc, accent):
    """One card per signatory: rendered signature image + audit line, or a wet-ink
    line for signatories still pending (so a printed copy can be hand-signed)."""
    cards = []
    for s in contract_doc.signatories or []:
        role = frappe.utils.escape_html(s.signatory_role or "")
        name = frappe.utils.escape_html(s.signatory_name or "")
        if s.status == "Signed" and s.signature_data:
            mark = "<img class='sig-img' src='%s' alt='signature'/>" % frappe.utils.cstr(s.signature_data)
            when = frappe.utils.format_datetime(s.signed_at) if s.signed_at else ""
            meta = "Signed electronically"
            if when:
                meta += " on %s" % frappe.utils.escape_html(when)
            if s.signature_ip:
                meta += " &middot; IP %s" % frappe.utils.escape_html(frappe.utils.cstr(s.signature_ip))
        else:
            mark = "<div class='sig-line'></div>"
            meta = "Awaiting signature"
        cards.append(
            "<div class='sig-card'><div class='sig-role'>%s</div>"
            "<div class='sig-name'>%s</div>%s<div class='sig-meta'>%s</div></div>"
            % (role, name, mark, meta)
        )
    return "<div class='sig-section'><h2>Signatures</h2>%s</div>" % "".join(cards)


def _render_certificate_page(contract_doc, accent, date_str, brand=None):
    """DocuSign-style Certificate of Completion appended as a separate page."""
    brand = brand or _network_branding(contract_doc)
    rows = []
    for s in contract_doc.signatories or []:
        when = frappe.utils.format_datetime(s.signed_at) if s.signed_at else "—"
        ip = frappe.utils.escape_html(frappe.utils.cstr(s.signature_ip or "—"))
        rows.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (
                frappe.utils.escape_html(s.signatory_name or ""),
                frappe.utils.escape_html(s.signatory_role or ""),
                frappe.utils.escape_html(s.status or ""),
                frappe.utils.escape_html(when),
                ip,
            )
        )
    executed = all((s.status == "Signed") for s in (contract_doc.signatories or [])) and bool(
        contract_doc.signatories
    )
    status_label = "Fully Executed" if executed else frappe.utils.cstr(
        contract_doc.workflow_state or contract_doc.status or "In Progress"
    )
    tc_hash = frappe.utils.escape_html(frappe.utils.cstr(contract_doc.tc_document_hash or "—"))

    contact_line = (
        "<div class='cert-kv'><b>Issuer Contact</b> %s</div>"
        % frappe.utils.escape_html(brand["contact_email"])
        if brand.get("contact_email")
        else ""
    )

    return """<div class="cert-page">
    <div class="cert-title"><div class="brand">{network}</div>
      <h2>Certificate of Completion</h2></div>
    <div class="cert-kv"><b>Contract</b> {ref}</div>
    <div class="cert-kv"><b>Contract Date</b> {date}</div>
    <div class="cert-kv"><b>Deal</b> {deal}</div>
    {contact}
    <div class="cert-kv"><b>Status</b> <span class="badge">{status}</span></div>
    <table class="cert"><thead><tr>
      <th>Signatory</th><th>Role</th><th>Status</th><th>Signed At</th><th>IP Address</th>
    </tr></thead><tbody>{rows}</tbody></table>
    <div class="cert-kv" style="margin-top:18px"><b>T&amp;C Integrity</b></div>
    <div class="hash">{hash}</div>
  </div>""".format(
        network=frappe.utils.escape_html(brand["display_name"]),
        ref=frappe.utils.escape_html(contract_doc.name),
        date=frappe.utils.escape_html(date_str or "—"),
        deal=frappe.utils.escape_html(frappe.utils.cstr(contract_doc.deal or "—")),
        contact=contact_line,
        status=frappe.utils.escape_html(status_label),
        rows="".join(rows) or "<tr><td colspan='5'>No signatories.</td></tr>",
        hash=tc_hash,
    )


def _network_branding(contract_doc):
    """Resolve the network masthead for a contract: accent colour, display name,
    logo URL, issuer contact e-mail and legal footer. Falls back through the deal's
    latest opt-in submission for legacy contracts with no network_slug, and to the
    Tiberbu wordmark/red when nothing is configured."""
    import re

    from crm.api.optin import _get_network_doc

    slug = frappe.utils.cstr(contract_doc.network_slug or "").strip()
    if not slug and contract_doc.deal:
        subs = frappe.get_list(
            "CRM Opt-In Submission",
            filters={"deal": contract_doc.deal},
            fields=["network_slug"],
            order_by="creation desc",
            limit=1,
            ignore_permissions=True,  # SYSTEM-INTERNAL
        )
        if subs:
            slug = frappe.utils.cstr(subs[0].network_slug or "").strip()

    doc = _get_network_doc(slug) if slug else None

    accent = frappe.utils.cstr((doc.get("primary_colour") if doc else "") or "").strip()
    if not re.match(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", accent):
        accent = "#bc1823"

    display = frappe.utils.cstr((doc.get("display_name") if doc else "") or "").strip() or "CareverseHIMS"

    logo = frappe.utils.cstr((doc.get("logo_url") if doc else "") or "").strip()
    if logo and not logo.startswith("http"):
        logo = frappe.utils.get_url(logo)

    return {
        "accent": accent,
        "display_name": display,
        "logo": logo,
        "contact_email": frappe.utils.cstr((doc.get("contact_email") if doc else "") or "").strip(),
        "footer_legal_name": frappe.utils.cstr((doc.get("footer_legal_name") if doc else "") or "").strip(),
    }


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

    contract_doc, signatory_row = _load_signatory_by_token(contract, role, token, "invite_token")
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

    # Reset attempt counter in Redis (keyed per-row so co-signatories sharing a
    # role each get their own counter)
    frappe.cache().set_value(
        _attempts_cache_key(contract, role, signatory_row.name),
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

    contract_doc, signatory_row = _load_signatory_by_token(contract, role, token, "invite_token")
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

    # Check attempt count from Redis (per-row so shared-role co-signatories don't
    # share a brute-force counter)
    attempts_key = _attempts_cache_key(contract, role, signatory_row.name)
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

    contract_doc, signatory_row = _load_signatory_by_token(
        contract, role, signing_token, "signing_token"
    )
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

    contract_doc, signatory_row = _load_signatory_by_token(
        contract, role, signing_token, "signing_token"
    )
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
