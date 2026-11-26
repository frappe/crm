import frappe
from frappe import _
from frappe.model.document import get_controller
from frappe.utils import make_filter_tuple

from crm.api.list_defaults import MODIFIED_COLUMN, NAME_COLUMN, MetaListDefaults
from crm.utils import is_frappe_version

COUNT_NAME = (
	{"COUNT": "name", "as": "total_count"}
	if is_frappe_version("16", above=True)
	else "count(name) as total_count"
)


class ListQuery:
	"""One page of a doctype's list or group by view, with the columns and fields it shows.

	Columns come from the client, then the user's standard CRM View Settings row,
	then the controller's default_list_data, then meta.
	"""

	def __init__(self, doctype, filters, order_by, page_length=20, view_type="list", group_by_field=None):
		self.doctype = doctype
		self.filters = filters
		self.order_by = order_by
		self.page_length = page_length
		self.view_type = view_type or "list"
		self.group_by_field = group_by_field
		self.controller = get_controller(doctype)
		self.meta = frappe.get_meta(doctype)
		self.is_default = True

	def run(self, columns=None, rows=None):
		"""Fetch the records; sets columns, rows, records and is_default."""
		columns, rows = self.get_columns_and_rows(columns, rows)
		self.columns = self.get_visible_columns(columns, rows)
		self.rows = rows
		self.add_extra_rows()
		records = frappe.get_list(
			self.doctype,
			fields=self.rows,
			filters=self.filters,
			order_by=self.order_by,
			page_length=self.page_length,
		)
		self.records = parse_list_data(records or [], self.doctype)
		return self

	@property
	def total(self):
		return get_count(self.doctype, self.filters)

	def get_columns_and_rows(self, columns, rows):
		if columns or rows:
			self.is_default = False
			return columns or [dict(NAME_COLUMN), dict(MODIFIED_COLUMN)], rows or ["name"]

		if settings := self.standard_view_settings:
			self.is_default = False
			return frappe.parse_json(settings.columns), frappe.parse_json(settings.rows)

		if default_list_data := self.default_list_data:
			return default_list_data.get("columns"), default_list_data.get("rows")

		defaults = MetaListDefaults(self.meta)
		return defaults.columns, defaults.rows

	@property
	def standard_view_settings(self):
		filters = {"dt": self.doctype, "type": self.view_type, "is_standard": 1, "user": frappe.session.user}
		if frappe.db.exists("CRM View Settings", filters):
			return frappe.get_doc("CRM View Settings", filters)

	@property
	def default_list_data(self):
		if hasattr(self.controller, "default_list_data"):
			return self.controller.default_list_data()

	def get_visible_columns(self, columns, rows):
		"""Drop hidden fields the controller did not choose, and fetch every column's field."""
		default_keys = [column.get("key") for column in (self.default_list_data or {}).get("columns", [])]
		visible = []
		for column in columns:
			key = column.get("key")
			field = self.meta.get_field(key)
			if field and field.get("hidden") and key not in default_keys:
				continue

			if key not in rows:
				rows.append(key)
			column["label"] = _(column.get("label"))
			if key == "_liked_by" and column.get("width") == "10rem":
				column["width"] = "50px"
			visible.append(column)
		return visible

	def add_extra_rows(self):
		if self.group_by_field and self.group_by_field not in self.rows:
			self.rows.append(self.group_by_field)
		if self.meta.track_seen and "_seen" not in self.rows:
			self.rows.append("_seen")
		add_task_all_day(self.doctype, self.rows)


class KanbanQuery:
	"""The columns of a doctype's kanban view, each with a page of records.

	The title and card fields come from the client, then the controller's
	default_kanban_settings, then meta.
	"""

	def __init__(self, doctype, filters, order_by, column_field=None):
		self.doctype = doctype
		self.filters = filters
		self.order_by = order_by
		self.column_field = column_field
		self.controller = get_controller(doctype)
		self.defaults = MetaListDefaults(frappe.get_meta(doctype))

	def run(self, kanban_columns=None, title_field=None, kanban_fields=None, rows=None):
		"""Fetch each column's records; sets kanban_columns, title_field, kanban_fields, rows and columns."""
		self.rows = rows or self.default_rows
		self.kanban_columns = kanban_columns or self.get_column_names()
		self.title_field = title_field or self.kanban_settings.get("title_field") or self.defaults.title_field
		self.kanban_fields = kanban_fields or self.default_kanban_fields
		for field in [self.title_field, *self.kanban_fields]:
			if field not in self.rows:
				self.rows.append(field)
		add_task_all_day(self.doctype, self.rows)
		self.columns = [self.get_column(kanban_column) for kanban_column in self.kanban_columns]
		return self

	@property
	def total(self):
		return get_count(self.doctype, self.filters)

	@property
	def kanban_settings(self):
		if hasattr(self.controller, "default_kanban_settings"):
			return self.controller.default_kanban_settings()
		return {}

	@property
	def default_column_field(self):
		return self.kanban_settings.get("column_field") or self.defaults.select_field

	@property
	def default_rows(self):
		if hasattr(self.controller, "default_list_data"):
			return self.controller.default_list_data().get("rows")
		return []

	@property
	def default_kanban_fields(self):
		if fields := self.kanban_settings.get("kanban_fields"):
			return frappe.parse_json(fields)
		if self.kanban_settings:
			return ["name"]
		return self.defaults.get_card_fields(self.column_field) or ["name"]

	def get_column_names(self):
		"""One column per Link record or Select option of the column field."""
		if not self.column_field:
			return []
		field = self.defaults.meta.get_field(self.column_field)
		if field.fieldtype == "Link":
			return frappe.get_all(field.options, fields=["name"], order_by="modified asc")
		if field.fieldtype == "Select":
			return [{"name": option} for option in field.options.split("\n")]
		return []

	def get_column(self, kanban_column):
		"""Fetch one column's records; adds count and all_count to the column."""
		filters = convert_filter_to_tuple(self.doctype, self.filters) if self.filters else []
		if self.column_field and kanban_column.get("name"):
			filters.append([self.doctype, self.column_field, "=", kanban_column.get("name")])

		order = kanban_column.get("order")
		records = [] if kanban_column.get("delete") else self.get_column_records(kanban_column, filters)
		if not kanban_column.get("delete"):
			kanban_column["all_count"] = get_count(self.doctype, filters)
			kanban_column["count"] = len(records)
			set_activity_counts(records, self.doctype)

		if order:
			records = sorted(
				records,
				key=lambda x: order.index(x.get("name")) if x.get("name") in order else len(order),
			)
		return {"column": kanban_column, "fields": self.kanban_fields, "data": records}

	def get_column_records(self, kanban_column, filters):
		page_length = kanban_column.get("page_length", 20)
		if order := kanban_column.get("order"):
			return get_records_based_on_order(self.doctype, self.rows, filters, page_length, order)
		return frappe.get_list(
			self.doctype,
			fields=self.rows,
			filters=filters,
			order_by=self.order_by,
			page_length=page_length,
		)


def prepare_filters(doctype, filters, default_filters=None):
	"""Copy the filters with @me set to the session user, page filters added, and Comments matched."""
	filters = frappe._dict(filters or {})
	for key in filters:
		value = filters[key]
		if isinstance(value, list):
			if "@me" in value:
				value[value.index("@me")] = frappe.session.user
			elif "%@me%" in value:
				for i in [i for i, v in enumerate(value) if v == "%@me%"]:
					value[i] = "%" + frappe.session.user + "%"
		elif value == "@me":
			filters[key] = frappe.session.user

	if default_filters:
		filters.update(frappe.parse_json(default_filters))

	apply_comments_filter(doctype, filters)
	return filters


def apply_comments_filter(doctype, filters):
	"""Match the Comments filter against the Comment doctype instead of `_comments`.

	`_comments` is a cache Frappe keeps on the parent doc and it only stores the
	first ~100 characters of each comment, so `like` on it misses later text.
	"""
	value = filters.get("_comments")
	if not isinstance(value, list | tuple) or len(value) != 2:
		return

	operator, text = str(value[0]).lower(), value[1]
	if operator not in ("like", "not like"):
		return

	commented = frappe.get_all(
		"Comment",
		filters={"reference_doctype": doctype, "comment_type": "Comment", "content": ["like", text]},
		pluck="reference_name",
		distinct=True,
		limit_page_length=0,
	)
	filters.pop("_comments")

	if "name" not in filters:
		filters["name"] = ["in" if operator == "like" else "not in", commented]
		return

	# a "name" filter is already set, keep it and combine both
	scoped = set(
		frappe.get_all(doctype, filters={"name": filters["name"]}, pluck="name", limit_page_length=0)
	)
	names = scoped & set(commented) if operator == "like" else scoped - set(commented)
	filters["name"] = ["in", list(names)]


def get_count(doctype, filters):
	return frappe.get_list(doctype, filters=filters, fields=[COUNT_NAME])[0].total_count


def add_task_all_day(doctype, rows):
	if doctype == "CRM Task" and "due_date" in rows and "all_day" not in rows:
		rows.append("all_day")


def parse_list_data(data, doctype):
	controller = get_controller(doctype)
	if hasattr(controller, "parse_list_data"):
		data = controller.parse_list_data(data)
	return data


def convert_filter_to_tuple(doctype, filters):
	if isinstance(filters, dict):
		return [make_filter_tuple(doctype, key, value) for key, value in filters.items()]
	return filters


def get_records_based_on_order(doctype, rows, filters, page_length, order):
	filters = convert_filter_to_tuple(doctype, filters)
	in_filters = [*filters, [doctype, "name", "in", order[:page_length]]]
	records = frappe.get_list(
		doctype,
		fields=rows,
		filters=in_filters,
		order_by="creation desc",
		page_length=page_length,
	)

	if len(records) < page_length:
		not_in_filters = [*filters, [doctype, "name", "not in", order]]
		records.extend(
			frappe.get_list(
				doctype,
				fields=rows,
				filters=not_in_filters,
				order_by="creation desc",
				page_length=page_length - len(records),
			)
		)
	return records


def set_activity_counts(rows, doctype):
	# one grouped query per activity type instead of one query per card
	names = [d.get("name") for d in rows]
	if not names:
		return rows

	def count_by(activity_doctype, link_field, filters=None):
		result = frappe.get_all(
			activity_doctype,
			filters={"reference_doctype": doctype, link_field: ["in", names], **(filters or {})},
			fields=[link_field, COUNT_NAME],
			group_by=link_field,
		)
		return {r.get(link_field): r.total_count for r in result}

	email_counts = count_by(
		"Communication",
		"reference_name",
		{"communication_type": ["in", ["Communication", "Automated Message"]]},
	)
	comment_counts = count_by("Comment", "reference_name", {"comment_type": "Comment"})
	task_counts = count_by("CRM Task", "reference_docname")
	note_counts = count_by("FCRM Note", "reference_docname")

	for d in rows:
		name = d.get("name")
		d["_email_count"] = email_counts.get(name, 0)
		d["_comment_count"] = comment_counts.get(name, 0)
		d["_task_count"] = task_counts.get(name, 0)
		d["_note_count"] = note_counts.get(name, 0)
	return rows
