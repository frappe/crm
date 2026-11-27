# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMSidebarItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		added: DF.Check
		anchors: DF.SmallText | None
		collapsible: DF.Check
		hidden: DF.Check
		icon: DF.Data | None
		keep_closed: DF.Check
		key: DF.Data
		label: DF.Data | None
		link_to: DF.Data | None
		link_type: DF.Literal["", "Built-in", "DocType"]
		overrides: DF.SmallText | None
		parent: DF.Data
		parent_key: DF.Data | None
		parentfield: DF.Data
		parenttype: DF.Data
		type: DF.Literal["Link", "Section"]
	# end: auto-generated types

	pass
