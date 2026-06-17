# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMWebsiteIntelligence(Document):
    """Child table row holding one Website Intelligence enrichment run.

    Populated by `crm.api.website_intelligence.run_enrichment`. All fields are
    read-only in the UI; they are filled programmatically from the standalone
    enrichment pipeline so every value remains traceable via `raw_json`.
    """

    pass
