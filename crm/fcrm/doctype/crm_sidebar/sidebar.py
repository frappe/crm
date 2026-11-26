import frappe
from frappe import _
from frappe.permissions import get_doctypes_with_read

from crm.fcrm.doctype.crm_sidebar.crm_sidebar import can_edit_site_sidebar
from crm.fcrm.doctype.crm_sidebar.layers import as_item, resolve
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

		layer = self.get_layer_name(scope)
		return {
			"scope": scope,
			"items": items,
			"below": below,
			"modified": str(frappe.db.get_value("CRM Sidebar", layer, "modified")) if layer else None,
			"can_edit_site": can_edit_site_sidebar(self.user),
			"built_in_doctypes": {
				item["opens_doctype"]: item["label"]
				for item in self.standard_items
				if item.get("opens_doctype")
			},
		}

	def save_layer(self, scope: str, items: list[dict], modified: str | None) -> dict:
		"""Store `items` as the smallest layer that makes them; fail if the layer changed since `modified`."""
		self.check_scope(scope)
		doc = self.get_locked_layer(scope)
		if (None if doc.is_new() else str(doc.modified)) != (modified or None):
			frappe.throw(
				_(
					"Someone else saved this sidebar after you opened it. Reload to get their changes, then make yours again."
				),
				frappe.TimestampMismatchError,
				title=_("Sidebar Changed"),
			)

		below = self.resolve("site" if scope == "user" else None)
		rows = reduce_layer(below, items, scope)
		self.check_added_rows(rows, doc, [as_item(item) for item in items])
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
			doc.save()
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

	def check_added_rows(self, rows: list[dict], doc, items: list[dict]):
		"""A row this layer adds is a section or a DocType; a new or changed DocType is checked again."""
		stored = {row.key: row.link_to for row in doc.get("items", []) if row.added}
		for row in rows:
			if not row.get("added"):
				continue
			if row["type"] == "Section":
				if not (row.get("label") or "").strip():
					frappe.throw(_("Give the section a label."))
				row.update(link_type=None, link_to=None, icon=None)
				continue
			if row.get("link_type") != "DocType" or not row.get("link_to"):
				frappe.throw(_("A row you add opens a DocType."))
			if stored.get(row["key"]) != row["link_to"]:
				self.check_doctype(row, items)
			row["label"] = row.get("label") or row["link_to"]

	def check_doctype(self, row: dict, items: list[dict]):
		doctype = row["link_to"]
		if not frappe.db.exists("DocType", doctype):
			frappe.throw(_("DocType {0} does not exist.").format(frappe.bold(doctype)))
		meta = frappe.get_meta(doctype)
		if meta.istable or meta.issingle or meta.is_virtual:
			frappe.throw(
				_("{0} cannot be in the sidebar: it has no list of records.").format(frappe.bold(doctype))
			)
		built_in = next((item for item in self.standard_items if item.get("opens_doctype") == doctype), None)
		if built_in:
			frappe.throw(_("{0} already opens {1}.").format(_(built_in["label"]), doctype))
		other = next(
			(
				i
				for i in items
				if i["key"] != row["key"] and i["link_type"] == "DocType" and i["link_to"] == doctype
			),
			None,
		)
		if other:
			frappe.throw(
				_("{0} is already in the sidebar, as {1}.").format(doctype, other["label"] or doctype)
			)
		if not self.can_read(doctype):
			frappe.throw(_("You cannot read {0}.").format(doctype), frappe.PermissionError)

	def has_no_access(self, item: dict) -> bool:
		return item["link_type"] == "DocType" and not self.can_read(item["link_to"])

	def can_read(self, doctype: str) -> bool:
		if doctype not in self.readable:
			readable = False
			if doctype and frappe.db.exists("DocType", doctype):
				readable = frappe.has_permission(doctype, "read", user=self.user)
			self.readable[doctype] = readable
		return self.readable[doctype]
