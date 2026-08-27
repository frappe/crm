"""
crm/setup/optin.py — Opt-In portal bootstrap utilities.

Auto-called by after_migrate hook and as a lazy bootstrap in _get_signing_key.
"""
from __future__ import annotations

import secrets

import frappe

DEFAULT_TC_TITLE = "CareverseHIMS Opt-In Terms and Conditions"
OPTIN_LEAD_SOURCE = "Self Opt-In Portal"


def ensure_lead_source():
    """
    Ensure the "Self Opt-In Portal" CRM Lead Source exists, so the opt-in pipeline
    can stamp leads/deals with it. Idempotent; safe to call on every migrate.
    """
    try:
        if frappe.db.exists("CRM Lead Source", OPTIN_LEAD_SOURCE):
            return
        doc = frappe.new_doc("CRM Lead Source")
        doc.source_name = OPTIN_LEAD_SOURCE
        doc.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "ensure_lead_source: failed to seed opt-in lead source")


def ensure_signing_key():
    """
    Generate and persist optin_signing_key on CRM Opt-In Settings if absent.
    Idempotent: safe to call multiple times.
    """
    try:
        settings = frappe.get_single("CRM Opt-In Settings")
        existing = settings.get_password("optin_signing_key", raise_exception=False)
        if existing:
            return
        key = secrets.token_hex(32)
        settings.optin_signing_key = key
        settings.save(ignore_permissions=True)  # SYSTEM-INTERNAL
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "ensure_signing_key: failed to persist signing key")


TEST_NETWORK_SLUG = "chak-cbsl"
TEST_CONTACT = {
    "contact_name": "Jane Wanjiku",
    "contact_email": "dsmwaura@gmail.com",
    "contact_phone": "0722810063",
}
# A known, KEPH-varied set of pre-qualified facilities for manual portal testing.
# Levels are chosen to all resolve to priced items in "Negotiated Year 1".
TEST_FACILITIES = [
    {"mfl_code": "15001", "facility_name": "Kenyatta National Hospital", "keph_level": "Level 5"},
    {"mfl_code": "13086", "facility_name": "Moi Teaching & Referral Hospital", "keph_level": "Level 5"},
    {"mfl_code": "13232", "facility_name": "Coast General Teaching & Referral Hospital", "keph_level": "Level 5"},
    {"mfl_code": "15034", "facility_name": "Mbagathi County Referral Hospital", "keph_level": "Level 4"},
    {"mfl_code": "14934", "facility_name": "Mama Lucy Kibaki Hospital", "keph_level": "Level 4"},
    {"mfl_code": "13984", "facility_name": "Pumwani Maternity Hospital", "keph_level": "Level 4"},
    {"mfl_code": "18456", "facility_name": "Ruaraka Uhai Neema Hospital", "keph_level": "Level 3B"},
    {"mfl_code": "12907", "facility_name": "St. Mary's Mission Hospital, Langata", "keph_level": "Level 3A"},
]


# Private-hospital opt-in networks (associations and hospital groups). Each is
# upserted by slug. All facilities under them route the OTP to CONTACT below,
# which is why every seeded facility shares the same registered email/phone.
CONTACT = TEST_CONTACT
PRIVATE_NETWORKS = [
    {
        "slug": "aga-khan",
        "display_name": "Aga Khan Health Services, Kenya",
        "footer_legal_name": "Aga Khan Health Services, Kenya",
        "contact_email": CONTACT["contact_email"],
    },
    {
        "slug": "lifemed",
        "display_name": "LifeMed Health Network",
        "footer_legal_name": "LifeMed Health Network Limited",
        "contact_email": CONTACT["contact_email"],
    },
    {
        "slug": "kaph",
        "display_name": "Kenya Association of Private Hospitals (KAPH)",
        "footer_legal_name": "Kenya Association of Private Hospitals",
        "contact_email": CONTACT["contact_email"],
    },
    {
        "slug": "rupha",
        "display_name": "Rural & Urban Private Hospitals Association (RUPHA)",
        "footer_legal_name": "Rural & Urban Private Hospitals Association of Kenya",
        "contact_email": CONTACT["contact_email"],
    },
]

# Realistic private Kenyan facilities per network. KEPH levels are all drawn from
# the priced set (Level 2/3/3A/3B/4/4B/5) so each resolves to a Negotiated Year 1
# item price. contact_name is a role, not a person, since all rows share CONTACT.
PRIVATE_FACILITIES = {
    "aga-khan": [
        {"mfl_code": "13097", "facility_name": "Aga Khan University Hospital, Nairobi", "keph_level": "Level 5"},
        {"mfl_code": "11928", "facility_name": "Aga Khan Hospital, Mombasa", "keph_level": "Level 5"},
        {"mfl_code": "16741", "facility_name": "Aga Khan Hospital, Kisumu", "keph_level": "Level 4"},
        {"mfl_code": "17255", "facility_name": "Aga Khan Medical Centre, Nyali", "keph_level": "Level 3B"},
        {"mfl_code": "19003", "facility_name": "Aga Khan Medical Centre, Kisii", "keph_level": "Level 3"},
    ],
    "lifemed": [
        {"mfl_code": "20114", "facility_name": "Lifecare Hospital, Eldoret", "keph_level": "Level 4"},
        {"mfl_code": "20115", "facility_name": "Lifecare Hospital, Bungoma", "keph_level": "Level 4"},
        {"mfl_code": "20116", "facility_name": "Lifecare Hospital, Migori", "keph_level": "Level 3B"},
        {"mfl_code": "20117", "facility_name": "Lifecare Hospital, Meru", "keph_level": "Level 3B"},
        {"mfl_code": "20118", "facility_name": "Lifecare Hospital, Kitale", "keph_level": "Level 3A"},
    ],
    "kaph": [
        {"mfl_code": "13089", "facility_name": "The Nairobi Hospital", "keph_level": "Level 5"},
        {"mfl_code": "12987", "facility_name": "MP Shah Hospital", "keph_level": "Level 5"},
        {"mfl_code": "13090", "facility_name": "The Mater Misericordiae Hospital", "keph_level": "Level 5"},
        {"mfl_code": "14012", "facility_name": "Gertrude's Children's Hospital", "keph_level": "Level 4"},
        {"mfl_code": "13760", "facility_name": "Nairobi West Hospital", "keph_level": "Level 4"},
        {"mfl_code": "15588", "facility_name": "Avenue Healthcare, Parklands", "keph_level": "Level 4"},
    ],
    "rupha": [
        {"mfl_code": "16233", "facility_name": "Metropolitan Hospital, Nairobi", "keph_level": "Level 4"},
        {"mfl_code": "17890", "facility_name": "Jumuia Hospital, Kakamega", "keph_level": "Level 4"},
        {"mfl_code": "18122", "facility_name": "Coptic Hospital, Nairobi", "keph_level": "Level 4"},
        {"mfl_code": "18455", "facility_name": "Nairobi Adventist Hospital", "keph_level": "Level 3B"},
        {"mfl_code": "19677", "facility_name": "Melchizedek Hospital, Nairobi", "keph_level": "Level 3B"},
        {"mfl_code": "21001", "facility_name": "Ladnan Hospital, Nairobi", "keph_level": "Level 3A"},
    ],
}


def _upsert_facility(network_slug, fac, contact):
    """Insert or update one CRM Pre-Qualified Facility + its membership for network_slug."""
    existing = frappe.get_all(
        "CRM Pre-Qualified Facility",
        filters={"mfl_code": fac["mfl_code"]},
        pluck="name",
        limit=1,
    )
    if existing:
        doc = frappe.get_doc("CRM Pre-Qualified Facility", existing[0])
    else:
        doc = frappe.new_doc("CRM Pre-Qualified Facility")
        doc.mfl_code = fac["mfl_code"]

    doc.facility_name = fac["facility_name"]
    doc.keph_level = fac["keph_level"]

    # Find or create the membership for this network
    mem = next(
        (m for m in (doc.memberships or []) if m.network == network_slug),
        None,
    )
    if mem is None:
        doc.append("memberships", {
            "network": network_slug,
            "status": "Active",
            "contact_name": contact["contact_name"],
            "contact_email": contact["contact_email"],
            "contact_phone": contact["contact_phone"],
        })
    else:
        mem.contact_name = contact["contact_name"]
        mem.contact_email = contact["contact_email"]
        mem.contact_phone = contact["contact_phone"]
        mem.status = "Active"

    doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
    return doc.name


def seed_test_facilities(network_slug=TEST_NETWORK_SLUG, contact=None):
    """
    Seed a known set of Active pre-qualified facilities for manual opt-in testing.
    Idempotent: upserts each facility by (network + mfl_code). Not wired into
    after_migrate — this is test data, run it explicitly on a dev site:

        bench --site <site> execute crm.setup.optin.seed_test_facilities
    """
    contact = contact or TEST_CONTACT
    if not frappe.db.exists("CRM Opt-In Network", {"slug": network_slug}):
        frappe.log_error(
            "seed_test_facilities: network '%s' not found" % network_slug,
            "seed_test_facilities",
        )
        return []

    seeded = [_upsert_facility(network_slug, fac, contact) for fac in TEST_FACILITIES]
    frappe.db.commit()
    return seeded


def ensure_optin_networks(networks=None):
    """
    Upsert the private-hospital opt-in networks (Aga Khan, LifeMed, KAPH, RUPHA)
    by slug. Idempotent: safe to re-run. Returns the list of slugs touched.
    """
    networks = networks or PRIVATE_NETWORKS
    touched = []
    for net in networks:
        if frappe.db.exists("CRM Opt-In Network", {"slug": net["slug"]}):
            doc = frappe.get_doc("CRM Opt-In Network", {"slug": net["slug"]})
        else:
            doc = frappe.new_doc("CRM Opt-In Network")
            doc.slug = net["slug"]

        doc.display_name = net["display_name"]
        doc.enabled = 1
        doc.contact_email = net.get("contact_email")
        doc.footer_legal_name = net.get("footer_legal_name")
        doc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
        touched.append(doc.name)

    frappe.db.commit()
    return touched


def seed_private_facilities(contact=None):
    """
    Create the private-hospital networks then upsert their Kenyan facilities,
    all registered against CONTACT (dsmwaura@gmail.com / 0722810063) so the OTP
    flow can be exercised on any of them. Idempotent; run explicitly on a dev site:

        bench --site <site> execute crm.setup.optin.seed_private_facilities

    Returns a {slug: [facility names]} map.
    """
    contact = contact or CONTACT
    ensure_optin_networks()

    seeded = {}
    for slug, facilities in PRIVATE_FACILITIES.items():
        fac_contact = dict(contact)
        # A role contact per network — every facility shares the tester's email/phone.
        fac_contact["contact_name"] = "%s Facilities Administrator" % _network_short_name(slug)
        seeded[slug] = [_upsert_facility(slug, fac, fac_contact) for fac in facilities]

    frappe.db.commit()
    return seeded


def _network_short_name(slug):
    """Human label for a network slug, used only for the seeded contact name."""
    return {
        "aga-khan": "Aga Khan",
        "lifemed": "LifeMed",
        "kaph": "KAPH",
        "rupha": "RUPHA",
    }.get(slug, slug)


# ---------------------------------------------------------------------------
# Demo networks — 5 contacts, each with a named private-hospital portfolio.
# MFL codes are in the 22001-22030 range (no overlap with existing seeds).
# ---------------------------------------------------------------------------
DEMO_NETWORKS = [
    {
        "slug": "primrose-health",
        "display_name": "Primrose Health Network",
        "footer_legal_name": "Primrose Health Network Limited",
        "contact_email": "thomas@tiberbu.com",
        "_contact": {"contact_name": "Thomas Mwogi", "contact_email": "thomas@tiberbu.com", "contact_phone": "0700000001"},
    },
    {
        "slug": "covenant-health",
        "display_name": "Covenant Health Network",
        "footer_legal_name": "Covenant Health Network (CHAK Affiliate)",
        "contact_email": "mmokua@chak.or.ke",
        "_contact": {"contact_name": "Moses Mokua", "contact_email": "mmokua@chak.or.ke", "contact_phone": "0700000002"},
    },
    {
        "slug": "apex-medical",
        "display_name": "Apex Medical Network",
        "footer_legal_name": "Apex Medical Network Limited",
        "contact_email": "salim@tiberbu.com",
        "_contact": {"contact_name": "Salim Mwaura", "contact_email": "salim@tiberbu.com", "contact_phone": "0700000003"},
    },
    {
        "slug": "crescent-health",
        "display_name": "Crescent Health Network",
        "footer_legal_name": "Crescent Health Network Limited",
        "contact_email": "abdul@kns.co.ke",
        "_contact": {"contact_name": "Abdullahi Sheikh", "contact_email": "abdul@kns.co.ke", "contact_phone": "0700000004"},
    },
    {
        "slug": "pinnacle-care",
        "display_name": "Pinnacle Care Network",
        "footer_legal_name": "Pinnacle Care Network Limited",
        "contact_email": "irungu@kns.co.ke",
        "_contact": {"contact_name": "Abubakr Irungu", "contact_email": "irungu@kns.co.ke", "contact_phone": "0700000005"},
    },
    {
        "slug": "bahari-health",
        "display_name": "Bahari Health Network",
        "footer_legal_name": "Bahari Health Network Limited",
        "contact_email": "abdul.as@gmail.com",
        "_contact": {"contact_name": "Abdullahi Sheikh", "contact_email": "abdul.as@gmail.com", "contact_phone": "0700000006"},
    },
    {
        "slug": "highlands-health",
        "display_name": "Highlands Health Network",
        "footer_legal_name": "Highlands Health Network Limited",
        "contact_email": "salim@tiberbu.com",
        "_contact": {"contact_name": "Salim Mwaura", "contact_email": "salim@tiberbu.com", "contact_phone": "0700000007"},
    },
]

DEMO_FACILITIES = {
    "primrose-health": [
        {"mfl_code": "22001", "facility_name": "Karen Hospital, Nairobi", "keph_level": "Level 4B"},
        {"mfl_code": "22002", "facility_name": "Kijabe Mission Hospital, Kiambu", "keph_level": "Level 4"},
        {"mfl_code": "22003", "facility_name": "Tenwek Hospital, Bomet", "keph_level": "Level 4"},
        {"mfl_code": "22004", "facility_name": "Kikuyu Mission Hospital, Kiambu", "keph_level": "Level 3B"},
        {"mfl_code": "22005", "facility_name": "St. Mary's Hospital, Mumias", "keph_level": "Level 3A"},
    ],
    "covenant-health": [
        {"mfl_code": "22006", "facility_name": "Chogoria Hospital, Tharaka-Nithi", "keph_level": "Level 4"},
        {"mfl_code": "22007", "facility_name": "AIC Litein Mission Hospital, Kericho", "keph_level": "Level 3B"},
        {"mfl_code": "22008", "facility_name": "Kapsowar Mission Hospital, Elgeyo-Marakwet", "keph_level": "Level 3"},
        {"mfl_code": "22009", "facility_name": "Siloam Mission Hospital, Trans Nzoia", "keph_level": "Level 3"},
        {"mfl_code": "22010", "facility_name": "Nyang'ori Mission Hospital, Vihiga", "keph_level": "Level 2"},
    ],
    "apex-medical": [
        {"mfl_code": "22011", "facility_name": "Primus International Medical Centre, Westlands", "keph_level": "Level 4"},
        {"mfl_code": "22012", "facility_name": "Meridian Medical Centre, Upper Hill", "keph_level": "Level 3B"},
        {"mfl_code": "22013", "facility_name": "HealthCare International, Westlands", "keph_level": "Level 3B"},
        {"mfl_code": "22014", "facility_name": "St. Luke's Orthopaedics & Trauma Hospital, Nairobi", "keph_level": "Level 4"},
        {"mfl_code": "22015", "facility_name": "Resolution Health Centre, Upper Hill", "keph_level": "Level 3A"},
    ],
    "crescent-health": [
        {"mfl_code": "22016", "facility_name": "Premier Hospital, Mombasa", "keph_level": "Level 4"},
        {"mfl_code": "22017", "facility_name": "Pandya Memorial Hospital, Mombasa", "keph_level": "Level 4"},
        {"mfl_code": "22018", "facility_name": "Coast Medical Centre, Mombasa", "keph_level": "Level 3B"},
        {"mfl_code": "22019", "facility_name": "Khadijah Hospital, Mombasa", "keph_level": "Level 3"},
        {"mfl_code": "22020", "facility_name": "Islamic Centre Clinic, Mombasa", "keph_level": "Level 2"},
    ],
    "pinnacle-care": [
        {"mfl_code": "22021", "facility_name": "Nairobi South Hospital, South B", "keph_level": "Level 4"},
        {"mfl_code": "22022", "facility_name": "Athi River Medical Centre, Machakos", "keph_level": "Level 3B"},
        {"mfl_code": "22023", "facility_name": "Upper Hill Medical Centre, Nairobi", "keph_level": "Level 3"},
        {"mfl_code": "22024", "facility_name": "Langata Hospital, Nairobi", "keph_level": "Level 3A"},
        {"mfl_code": "22025", "facility_name": "Kitengela Medical Centre, Kajiado", "keph_level": "Level 2"},
    ],
    "bahari-health": [
        {"mfl_code": "22026", "facility_name": "Mombasa Medical Centre, Mombasa", "keph_level": "Level 4"},
        {"mfl_code": "22027", "facility_name": "Serene Hospital, Mombasa", "keph_level": "Level 3B"},
        {"mfl_code": "22028", "facility_name": "Harbour View Medical Centre, Mombasa", "keph_level": "Level 3"},
        {"mfl_code": "22029", "facility_name": "Tudor Medical Centre, Mombasa", "keph_level": "Level 3A"},
        {"mfl_code": "22030", "facility_name": "Mishomoroni Medical Centre, Mombasa", "keph_level": "Level 2"},
    ],
    "highlands-health": [
        {"mfl_code": "22031", "facility_name": "Nakuru Highlands Hospital, Nakuru", "keph_level": "Level 4"},
        {"mfl_code": "22032", "facility_name": "Rift Valley Medical Centre, Nakuru", "keph_level": "Level 3B"},
        {"mfl_code": "22033", "facility_name": "Eldoret Highlands Medical Centre, Uasin Gishu", "keph_level": "Level 3"},
        {"mfl_code": "22034", "facility_name": "Nyahururu Medical Centre, Laikipia", "keph_level": "Level 3A"},
        {"mfl_code": "22035", "facility_name": "Molo Cottage Medical Centre, Nakuru", "keph_level": "Level 2"},
    ],
}


def seed_demo_networks():
    """
    Upsert 5 demo opt-in networks with private Kenyan facilities, each assigned to
    a named contact. Sends ONE summary invitation email per contact listing all their
    facilities and the opt-in link. Idempotent; run explicitly:

        bench --site cr-dev.tiberbu.app execute crm.setup.optin.seed_demo_networks
    """
    nets = {n["slug"]: n for n in DEMO_NETWORKS}

    # Upsert networks (strip internal _contact key before save)
    public_nets = [{k: v for k, v in n.items() if not k.startswith("_")} for n in DEMO_NETWORKS]
    ensure_optin_networks(public_nets)

    site_url = frappe.utils.get_url()

    for slug, facilities in DEMO_FACILITIES.items():
        net_meta = nets[slug]
        contact = net_meta["_contact"]
        for fac in facilities:
            _upsert_facility(slug, fac, contact)

        frappe.db.commit()
        _send_demo_invitation(slug, nets[slug], site_url)

    # Summary email to salim
    _send_seed_summary(nets, site_url)

    return {slug: len(facs) for slug, facs in DEMO_FACILITIES.items()}


def seed_single_demo_network(slug):
    """
    Seed one demo network by slug (must exist in DEMO_NETWORKS/DEMO_FACILITIES),
    upsert its facilities, and send the invitation email. Idempotent.

        bench --site cr-dev.tiberbu.app execute crm.setup.optin.seed_single_demo_network --kwargs '{"slug": "bahari-health"}'
    """
    nets = {n["slug"]: n for n in DEMO_NETWORKS}
    if slug not in nets:
        raise ValueError("Unknown demo network slug: {}".format(slug))
    if slug not in DEMO_FACILITIES:
        raise ValueError("No facilities defined for slug: {}".format(slug))

    net_meta = nets[slug]
    public_net = {k: v for k, v in net_meta.items() if not k.startswith("_")}
    ensure_optin_networks([public_net])

    contact = net_meta["_contact"]
    for fac in DEMO_FACILITIES[slug]:
        _upsert_facility(slug, fac, contact)

    frappe.db.commit()
    site_url = frappe.utils.get_url()
    _send_demo_invitation(slug, net_meta, site_url)
    return {"network": slug, "facilities": len(DEMO_FACILITIES[slug])}


def _send_demo_invitation(slug, net_meta, site_url):
    """Email the contact for one demo network with their facility list and opt-in link."""
    contact = net_meta["_contact"]
    facilities = DEMO_FACILITIES[slug]
    network_name = net_meta["display_name"]
    optin_url = "{}/opt-in?network={}".format(site_url, slug)

    fac_rows = "".join(
        "<li>{} (KEPH {})</li>".format(f["facility_name"], f["keph_level"])
        for f in facilities
    )

    body = """
<p>Dear {contact_name},</p>

<p>You have been pre-qualified to join <strong>{network_name}</strong> on CareverseHIMS
— Tiberbu's health information management platform.</p>

<p>The following facilities under your account are ready for enrolment:</p>
<ul>{fac_rows}</ul>

<p>The opt-in process takes about 5 minutes per facility — verify your email, confirm
details, review pricing, and accept the agreement.</p>

<p style="margin: 24px 0;">
  <a href="{optin_url}"
     style="background:#b91c1c;color:#fff;padding:12px 24px;border-radius:6px;
            text-decoration:none;font-weight:600;">
    Start Opt-In &rarr;
  </a>
</p>

<p>Opt-in link: <a href="{optin_url}">{optin_url}</a></p>

<p>Questions? Contact us at <a href="mailto:hello@tiberbu.com">hello@tiberbu.com</a>.</p>

<p>Best regards,<br/>The Tiberbu Team</p>
""".format(
        contact_name=contact["contact_name"],
        network_name=network_name,
        fac_rows=fac_rows,
        optin_url=optin_url,
    )

    try:
        frappe.sendmail(
            recipients=[contact["contact_email"]],
            subject="You've been pre-qualified: {} — CareverseHIMS".format(network_name),
            message=body,
            now=True,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "seed_demo_networks: invitation email failed for {}".format(slug))


def _send_seed_summary(nets, site_url):
    """Send a summary of all 5 demo networks to salim@tiberbu.com."""
    rows = ""
    for slug, net_meta in nets.items():
        contact = net_meta["_contact"]
        url = "{}/opt-in?network={}".format(site_url, slug)
        rows += (
            "<tr>"
            "<td style='padding:6px 12px;border:1px solid #e5e7eb;'>{}</td>"
            "<td style='padding:6px 12px;border:1px solid #e5e7eb;'>{}</td>"
            "<td style='padding:6px 12px;border:1px solid #e5e7eb;'>{}</td>"
            "<td style='padding:6px 12px;border:1px solid #e5e7eb;'>"
            "<a href='{}'>{}</a></td>"
            "</tr>"
        ).format(
            net_meta["display_name"],
            contact["contact_name"],
            contact["contact_email"],
            url,
            url,
        )

    body = """
<h2>Demo Networks Seeded</h2>
<p>5 opt-in networks have been created and invitations dispatched.</p>
<table style='border-collapse:collapse;width:100%;'>
  <thead>
    <tr style='background:#f3f4f6;'>
      <th style='padding:6px 12px;border:1px solid #e5e7eb;text-align:left;'>Network</th>
      <th style='padding:6px 12px;border:1px solid #e5e7eb;text-align:left;'>Contact</th>
      <th style='padding:6px 12px;border:1px solid #e5e7eb;text-align:left;'>Email</th>
      <th style='padding:6px 12px;border:1px solid #e5e7eb;text-align:left;'>Opt-In URL</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
""".format(rows=rows)

    try:
        frappe.sendmail(
            recipients=["salim@tiberbu.com"],
            subject="[CRM Seed] 5 Demo Networks Ready",
            message=body,
            now=True,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "seed_demo_networks: summary email failed")


def ensure_default_terms():
    """
    Ensure a Terms and Conditions document exists and is wired to
    CRM Opt-In Settings.active_tc_document, so the opt-in portal's terms step
    can always render.

    Idempotent, with admin-override respected:
      - If an admin has pointed active_tc_document at their OWN document (any title
        other than the system default), leave everything alone.
      - Otherwise keep the system-owned default document in sync with the current
        template (so template fixes ship on migrate) and point active at it.
    """
    try:
        settings = frappe.get_single("CRM Opt-In Settings")

        # Admin has a custom active doc — never touch it.
        active = settings.active_tc_document
        if (
            active
            and active != DEFAULT_TC_TITLE
            and frappe.db.exists("Terms and Conditions", active)
        ):
            return

        template = _default_terms_template()

        if frappe.db.exists("Terms and Conditions", DEFAULT_TC_TITLE):
            tc = frappe.get_doc("Terms and Conditions", DEFAULT_TC_TITLE)
            if (tc.terms or "") != template:
                tc.terms = template
                tc.save(ignore_permissions=True)  # SYSTEM-INTERNAL
        else:
            tc = frappe.new_doc("Terms and Conditions")
            tc.title = DEFAULT_TC_TITLE
            tc.selling = 1
            tc.terms = template
            tc.insert(ignore_permissions=True)  # SYSTEM-INTERNAL

        if active != tc.name:
            settings.active_tc_document = tc.name
            settings.save(ignore_permissions=True)  # SYSTEM-INTERNAL
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "ensure_default_terms: failed to seed T&C document")


def _default_terms_template():
    """
    Jinja source for the default opt-in T&C. Rendered by crm.api.optin.get_terms_text.

    IMPORTANT: the "Terms and Conditions" doctype stores this in a Text Editor field,
    whose HTML sanitiser strips Jinja *block* tags ({% ... %}) on save while leaving
    *expression* tags ({{ ... }}) intact. So this template must never use {% for %}
    loops — the per-facility pricing table is pre-rendered server-side and injected via
    the {{ pricing_table }} expression (autoescape is off in Frappe's Jinja env).

    Render context (all supplied by crm.api.optin.get_terms_text):
      network.display_name, date, contact.email,
      pricing_table (safe HTML <table>), grand_total_monthly_display,
      grand_total_annual_display (preformatted strings).
    """
    return """
<h3>{{ network.display_name }} — CareverseHIMS Subscription Agreement</h3>
<p><em>Effective date of acceptance: {{ date }}</em></p>

<p>This Agreement is entered into between Tiberbu Healthnet Solutions
("<strong>Provider</strong>") and the facility contact identified below
("<strong>Customer</strong>", {{ contact.email }}), for the provision of the
CareverseHIMS health information management service.</p>

<h4>1. Facilities and Fees</h4>
<p>The Customer subscribes the following facilities. Fees are computed from each
facility's KEPH level and are exclusive of VAT (16%), which is applied at
checkout.</p>
<div>{{ pricing_table }}</div>
<p><strong>Total monthly commitment (incl. VAT): KES
{{ grand_total_monthly_display }}</strong><br/>
<strong>Total annual commitment (incl. VAT): KES
{{ grand_total_annual_display }}</strong></p>

<h4>2. Subscription Term and Price Lock</h4>
<p>The subscription runs for an initial term of twelve (12) months from the
activation date and renews for successive twelve (12) month terms unless either
party gives thirty (30) days' written notice. The rates shown above are locked
for the initial term.</p>

<h4>3. Payment</h4>
<p>Fees are invoiced in Kenya Shillings (KES). Invoices are payable within thirty
(30) days of the invoice date. Late payments may attract suspension of service
after a fourteen (14) day cure period.</p>

<h4>4. Data Protection and Privacy</h4>
<p>The Provider processes personal and health data in accordance with the Kenya
Data Protection Act, 2019. The Customer remains the data controller for patient
records; the Provider acts as data processor and implements appropriate technical
and organisational safeguards.</p>

<h4>5. Service Availability</h4>
<p>The Provider targets 99.5% monthly service availability, excluding scheduled
maintenance notified in advance and events beyond reasonable control.</p>

<h4>6. Confidentiality</h4>
<p>Each party shall keep confidential all non-public information disclosed by the
other party and use it solely to perform this Agreement.</p>

<h4>7. Termination</h4>
<p>Either party may terminate for material breach that remains uncured thirty (30)
days after written notice. On termination, the Provider shall make the Customer's
data available for export for a period of sixty (60) days.</p>

<h4>8. Governing Law</h4>
<p>This Agreement is governed by the laws of the Republic of Kenya, and the courts
of Kenya shall have exclusive jurisdiction.</p>

<h4>9. Acceptance</h4>
<p>By ticking the acceptance box and submitting the opt-in, the Customer confirms
they are authorised to bind the named facilities and agree to these Terms and
Conditions as displayed, including the specific fees shown above.</p>
"""
