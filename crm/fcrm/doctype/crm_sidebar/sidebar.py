import frappe
from frappe import _
from frappe.permissions import get_doctypes_with_read

from crm.fcrm.doctype.crm_sidebar.crm_sidebar import can_edit_site_sidebar, get_built_in_doctypes
from crm.fcrm.doctype.crm_sidebar.layers import resolve
from crm.fcrm.doctype.crm_sidebar.reduction import reduce_layer

SCOPES = ("user", "site")
ROW_FIELDS = (
	"key",
	"type",
	"label",
	"icon",
	"link_type",
	"link_to",
	"parent_key",
	"collapsible",
	"keep_closed",
	"hidden",
	"added",
	"overrides",
	"anchors",
)


class Sidebar:
	"""The CRM sidebar one user sees, and the layers they can edit."""

	def __init__(self, user: str | None = None):
		self.user = user or frappe.session.user
		self.readable: dict[str, bool] = {}

	@property
	def standard_items(self) -> list[dict]:
		return frappe.get_hooks("standard_sidebar_items")

	def get_items(self) -> list[dict]:
		"""The items to draw: not hidden, not in a hidden section, and readable."""
		items = self.resolve("user")
		hidden = {item["key"] for item in items if item["hidden"] or self.has_no_access(item)}
		return [
			{field: value for field, value in item.items() if field != "hidden"}
			for item in items
			if item["key"] not in hidden and item["parent_key"] not in hidden
		]

	def get_layer(self, scope: str) -> dict:
		"""What the dialog edits: this layer's sidebar with markers, and the one below it."""
		self.check_scope(scope)
		below = self.resolve("site" if scope == "user" else None)
		hidden_below = {item["key"] for item in below if item["hidden"]}
		items = self.resolve(scope)
		for item in items:
			if self.has_no_access(item):
				item["no_access"] = 1
			if scope == "user" and item["hidden"] and item["key"] in hidden_below:
				item["hidden_by"] = "site"

		return {
			"scope": scope,
			"items": items,
			"below": below,
			"modified": self.get_modified(scope),
			"site_modified": self.get_modified("site") if scope == "user" else None,
			"can_edit_site": can_edit_site_sidebar(self.user),
			"built_in_doctypes": get_built_in_doctypes(),
		}

	def save_layer(
		self, scope: str, items: list[dict], modified: str | None, site_modified: str | None = None
	) -> dict:
		"""Store `items` as the smallest layer that makes them.

		Fails if this layer changed since `modified`, or, for a user's layer, if the site layer
		changed since `site_modified`: the items were arranged over a site layer that is gone.
		"""
		self.check_scope(scope)
		doc = self.get_locked_layer(scope)
		self.check_unchanged(None if doc.is_new() else str(doc.modified), modified)
		if scope == "user":
			self.check_unchanged(self.get_modified("site"), site_modified)

		below_rows = [self.get_layer_rows("site")] if scope == "user" else []
		rows = reduce_layer(resolve(self.standard_items, below_rows), items, scope)
		self.check_duplicate_doctypes(rows, doc, resolve(self.standard_items, [*below_rows, rows]))
		self.write(doc, rows)
		return {**self.get_layer(scope), "sidebar": self.get_items()}

	def search_doctypes(self, txt: str, limit: int = 20) -> list[str]:
		readable = set(get_doctypes_with_read(self.user))
		names = frappe.get_all(
			"DocType",
			filters={"istable": 0, "issingle": 0, "is_virtual": 0, "name": ["like", f"%{txt}%"]},
			pluck="name",
			order_by="name asc",
		)
		return [name for name in names if name in readable][:limit]

	def resolve(self, scope: str | None) -> list[dict]:
		"""The sidebar up to and including `scope`'s layer; None is the standard items alone."""
		layers = []
		if scope:
			layers.append(self.get_layer_rows("site"))
		if scope == "user":
			layers.append(self.get_layer_rows("user"))
		return resolve(self.standard_items, layers)

	def get_modified(self, scope: str) -> str | None:
		layer = self.get_layer_name(scope)
		return str(frappe.db.get_value("CRM Sidebar", layer, "modified")) if layer else None

	def check_unchanged(self, current: str | None, opened: str | None):
		if current != (opened or None):
			raise_sidebar_changed()

	def get_layer_name(self, scope: str) -> str | None:
		user = self.user if scope == "user" else ("is", "not set")
		return frappe.db.get_value("CRM Sidebar", {"user": user})

	def get_layer_rows(self, scope: str) -> list[dict]:
		name = self.get_layer_name(scope)
		if not name:
			return []
		return frappe.get_all(
			"CRM Sidebar Item",
			filters={"parent": name, "parenttype": "CRM Sidebar", "parentfield": "items"},
			fields=list(ROW_FIELDS),
			order_by="idx asc",
		)

	def get_locked_layer(self, scope: str):
		name = self.get_layer_name(scope)
		if name:
			return frappe.get_doc("CRM Sidebar", name, for_update=True)
		return frappe.new_doc("CRM Sidebar", user=self.user if scope == "user" else None)

	def write(self, doc, rows: list[dict]):
		"""An empty layer is no layer, so it is deleted rather than kept empty."""
		if rows:
			doc.set("items", rows)
			try:
				doc.save()
			except frappe.DuplicateEntryError:
				# Another first save of this layer won the insert.
				raise_sidebar_changed()
		elif not doc.is_new():
			frappe.delete_doc("CRM Sidebar", doc.name, delete_permanently=True)

	def check_scope(self, scope: str):
		if scope not in SCOPES:
			frappe.throw(_("Scope must be user or site."))
		if scope == "site" and not can_edit_site_sidebar(self.user):
			frappe.throw(
				_("Only a Sales Manager or System Manager can change the sidebar for everyone."),
				frappe.PermissionError,
			)

	def check_duplicate_doctypes(self, rows: list[dict], doc, resolved: list[dict]):
		"""A DocType opens from one row only: refuse a row this save adds or points at another DocType."""
		stored = {row.key: row.link_to for row in doc.get("items", []) if row.added}
		for row in rows:
			if not row.get("added") or not row.get("link_to") or stored.get(row["key"]) == row["link_to"]:
				continue
			other = next(
				(
					item
					for item in resolved
					if item["key"] != row["key"]
					and item["link_type"] == "DocType"
					and item["link_to"] == row["link_to"]
				),
				None,
			)
			if other:
				frappe.throw(
					_("{0} is already in the sidebar, as {1}.").format(
						row["link_to"], other["label"] or row["link_to"]
					)
				)

	def has_no_access(self, item: dict) -> bool:
		return item["link_type"] == "DocType" and not self.can_read(item["link_to"])

	def can_read(self, doctype: str) -> bool:
		if doctype not in self.readable:
			readable = False
			if doctype and frappe.db.exists("DocType", doctype):
				readable = frappe.has_permission(doctype, "read", user=self.user)
			self.readable[doctype] = readable
		return self.readable[doctype]


def raise_sidebar_changed():
	frappe.throw(
		_(
			"Someone else saved the sidebar after you opened it. Reload to get their changes, then make yours again."
		),
		frappe.TimestampMismatchError,
		title=_("Sidebar Changed"),
	)
