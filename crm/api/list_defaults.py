from frappe.model import no_value_fields, table_fields

MAX_COLUMNS = 7
MIN_LIST_FIELDS = 3
TOP_UP_FIELDS = 4
MAX_CARD_FIELDS = 3
TOP_UP_SKIPPED_FIELDTYPES = ("Text Editor", "Small Text", "Long Text", "Text", "Attach Image", "Code")
WIDTHS = {
	"Check": "6rem",
	"Currency": "9rem",
	"Date": "8rem",
	"Datetime": "8rem",
	"Select": "8rem",
	"Link": "10rem",
	"Data": "10rem",
}

NAME_COLUMN = {"label": "Name", "type": "Data", "key": "name", "width": "16rem"}
MODIFIED_COLUMN = {"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"}
DOCSTATUS_COLUMN = {"label": "Status", "type": "Int", "key": "docstatus", "width": "8rem"}


class MetaListDefaults:
	"""List view defaults read from a doctype's meta, for doctypes CRM has no settings for."""

	def __init__(self, meta):
		self.meta = meta

	@property
	def columns(self):
		"""Title field, list fields, Status when submittable, then Last Modified; at most 7."""
		head = [self.get_column(self.title_field_meta, "12rem")] if self.title_field_meta else [NAME_COLUMN]
		tail = [*self.status_columns, MODIFIED_COLUMN]
		middle = [self.get_column(field) for field in self.list_fields]
		return [dict(column) for column in [*head, *middle[: MAX_COLUMNS - len(head) - len(tail)], *tail]]

	@property
	def rows(self):
		return ["name", self.meta.image_field] if self.meta.image_field else ["name"]

	@property
	def title_field(self):
		return self.title_field_meta.fieldname if self.title_field_meta else "name"

	@property
	def select_field(self):
		"""The Group by and Kanban field: a Select named status, else the first Select in the list view, else the first Select."""
		selects = [field for field in self.value_fields if field.fieldtype == "Select"]
		status = next((field for field in selects if field.fieldname == "status"), None)
		in_list_view = next((field for field in selects if field.in_list_view), None)
		first = status or in_list_view or (selects[0] if selects else None)
		return first.fieldname if first else None

	@property
	def order_by(self):
		return f"{self.meta.sort_field or 'modified'} {self.meta.sort_order or 'desc'}".lower()

	def get_card_fields(self, column_field=None):
		skipped = {"name", "modified", "docstatus", self.title_field, column_field}
		return [column["key"] for column in self.columns if column["key"] not in skipped][:MAX_CARD_FIELDS]

	@property
	def title_field_meta(self):
		field = self.meta.get_field(self.meta.title_field) if self.meta.title_field else None
		return field if field and not field.hidden else None

	@property
	def value_fields(self):
		skipped = (*no_value_fields, *table_fields)
		return [
			field
			for field in self.meta.fields
			if field.fieldtype not in skipped and not field.hidden and field.fieldname != "naming_series"
		]

	@property
	def list_fields(self):
		"""The in_list_view fields, topped up from standard filter and required fields when there are few."""
		title = self.meta.title_field
		fields = [f for f in self.value_fields if f.in_list_view and f.fieldname != title]
		if len(fields) >= MIN_LIST_FIELDS:
			return fields

		extra = [
			f
			for f in self.value_fields
			if f not in fields
			and f.fieldname != title
			and (f.in_standard_filter or f.reqd)
			and f.fieldtype not in TOP_UP_SKIPPED_FIELDTYPES
		]
		return [*fields, *extra][:TOP_UP_FIELDS]

	@property
	def status_columns(self):
		"""Submittable doctypes show their own status field, else the docstatus."""
		if not self.meta.is_submittable:
			return []
		if any(field.fieldname == "status" for field in self.list_fields):
			return []
		status = self.meta.get_field("status")
		return [self.get_column(status)] if status and not status.hidden else [DOCSTATUS_COLUMN]

	def get_column(self, field, width=None):
		column = {
			"label": field.label,
			"type": field.fieldtype,
			"key": field.fieldname,
			"width": width or WIDTHS.get(field.fieldtype, "11rem"),
		}
		if field.fieldtype in ("Link", "Dynamic Link"):
			column["options"] = field.options
		return column
