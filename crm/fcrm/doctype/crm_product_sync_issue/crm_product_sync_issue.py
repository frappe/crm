# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMProductSyncIssue(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		detail: DF.SmallText | None
		detected_on: DF.Datetime | None
		dismissed: DF.Check
		kind: DF.Literal["unlinked_orphan"]
		name: DF.Int | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		product: DF.Link | None
	# end: auto-generated types

	pass
