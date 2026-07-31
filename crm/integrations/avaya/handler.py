import frappe
from frappe import _

# E5/E6 GATED — this module is a placeholder. The real webhook handler and
# make_a_call implementation are blocked on Tiberbu confirming the live Avaya
# edition (AXP or Aura/AES) and providing credentials + payload contracts.
# See docs/tiberbu-crm-avaya-connect-status.md and BRD §6.2.1 Risk R1.
#
# Reference implementation to mirror when unblocked: crm/integrations/exotel/handler.py
#   handle_request  → validate webhook token → publish_realtime → create/update CRM Call Log
#   make_a_call     → call Avaya originate API → return call-id dict the UI reads
#
# The module exists now so that:
#   - `crm.integrations.avaya.handler.make_a_call` resolves (no ImportError)
#   - the frontend receives a clear "not yet connected" error, not a cryptic 404
#   - E5 only needs to fill in the real logic, not create the module path from scratch


@frappe.whitelist(allow_guest=True)
def handle_request(**kwargs):
    """Inbound Avaya webhook — not yet implemented (E5/E6 gated)."""
    frappe.throw(
        _("Avaya inbound webhook is not yet configured. Complete E5 setup once credentials are provided."),
        title=_("Avaya Not Connected"),
    )


@frappe.whitelist()
def make_a_call(to_number: str):
    """Outbound click-to-dial — not yet implemented (E5/E6 gated)."""
    frappe.throw(
        _("Avaya calling is not yet connected. Configure CRM Avaya Settings once credentials are provided."),
        title=_("Avaya Not Connected"),
    )
