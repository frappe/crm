import frappe
from frappe.model.document import Document


class CRMPreQualifiedFacility(Document):
    def after_insert(self):
        if self.flags.get("skip_invitation"):
            return
        _send_facility_invitation(self)


def _send_facility_invitation(doc):
    """Send one invitation email per network membership on the facility.

    The network and contact live on the CRM Facility Membership child rows (a
    facility can belong to up to two networks) — NOT on the parent facility, which
    only carries mfl_code / facility_name / keph_level. Each Active membership with
    a contact email gets its own branded, per-network invitation.
    """
    for mem in (doc.memberships or []):
        if not mem.network or not mem.contact_email:
            continue
        if (mem.status or "Active") != "Active":
            continue
        try:
            network = frappe.get_doc("CRM Opt-In Network", mem.network)
            # The opt-in portal keys on the network slug (verify_prequalified /
            # get_settings filter by `slug`), not the Link docname.
            slug = network.slug or mem.network
            optin_url = "{}/opt-in?network={}".format(frappe.utils.get_url(), slug)
            frappe.sendmail(
                recipients=[mem.contact_email],
                subject="You've been pre-qualified: {} — CareverseHIMS".format(network.display_name),
                message=_invite_html(mem.contact_name, network.display_name, doc.facility_name, optin_url),
                now=True,
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "CRMPreQualifiedFacility: invitation email failed")


def _invite_html(contact_name, network_name, facility_name, optin_url):
    return """
<p>Dear {contact_name},</p>

<p>You have been pre-qualified to join the <strong>{network_name}</strong> network on
CareverseHIMS — Tiberbu's health information management platform.</p>

<p>Your facility, <strong>{facility_name}</strong>, is ready to be enrolled. The process
takes about 5 minutes:</p>

<ol>
  <li>Verify your email with a one-time code.</li>
  <li>Confirm your facility details and review pricing.</li>
  <li>Accept the subscription agreement.</li>
</ol>

<p style="margin: 24px 0;">
  <a href="{optin_url}"
     style="background:#b91c1c;color:#fff;padding:12px 24px;border-radius:6px;
            text-decoration:none;font-weight:600;">
    Start Opt-In &rarr;
  </a>
</p>

<p>If the button doesn't work, paste this link in your browser:<br/>
<a href="{optin_url}">{optin_url}</a></p>

<p>If you have questions, reply to this email or contact us at
<a href="mailto:hello@tiberbu.com">hello@tiberbu.com</a>.</p>

<p>Best regards,<br/>The Tiberbu Team</p>
""".format(
        contact_name=contact_name,
        network_name=network_name,
        facility_name=facility_name,
        optin_url=optin_url,
    )
