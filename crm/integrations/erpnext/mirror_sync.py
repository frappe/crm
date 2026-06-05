import frappe

from crm.integrations.erpnext.utils import ALLOWED_DOCTYPES, find_target_for, should_sync

MIRROR_FLAG = "ignore_erpnext_sync"
_SKIP_PAYLOAD_FIELDS = {
	"name",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"idx",
	"docstatus",
	"parent",
	"parentfield",
	"parenttype",
	"doctype",
}


class MirrorSync:
	"""Generic mirror sync for lifecycle-bound docs (User Permission, DocShare)
	between Item and CRM Product. Wraps a document and is driven by doc_events
	handlers. Configure the link fields via doctype_field + value_field.

	extra_dedup: optional callable(doc) -> dict, merged into the dedup filter.
	extra_mirror_flags: optional dict of flags set on every mirror document.
	"""

	def __init__(self, doc, doctype_field, value_field, extra_dedup=None, extra_mirror_flags=None):
		self.doc = doc
		self.DOCTYPE_FIELD = doctype_field
		self.VALUE_FIELD = value_field
		self._extra_dedup = extra_dedup
		self._extra_mirror_flags = extra_mirror_flags or {}

	def sync_active(self) -> bool:
		return should_sync()

	def should_mirror(self) -> bool:
		if self.doc.flags.get(MIRROR_FLAG):
			return False
		if not self.sync_active():
			return False
		return self.doc.get(self.DOCTYPE_FIELD) in ALLOWED_DOCTYPES

	def has_data_updated(self, old) -> bool:
		return self.doc.get(self.DOCTYPE_FIELD) != old.get(self.DOCTYPE_FIELD) or self.doc.get(
			self.VALUE_FIELD
		) != old.get(self.VALUE_FIELD)

	def _target(self):
		return find_target_for(self.doc.get(self.DOCTYPE_FIELD), self.doc.get(self.VALUE_FIELD))

	def dedup_filter(self, target_doctype: str, target_value: str) -> dict:
		filters = {
			self.DOCTYPE_FIELD: target_doctype,
			self.VALUE_FIELD: target_value,
			"user": self.doc.user,
		}
		if self._extra_dedup:
			filters.update(self._extra_dedup(self.doc))
		return filters

	def find_mirror(self):
		target = self._target()
		if not target:
			return None
		target_doctype, target_value = target
		filters = self.dedup_filter(target_doctype, target_value)
		name = frappe.db.get_value(self.doc.doctype, filters, "name") 
		return frappe.get_doc(self.doc.doctype, name) if name else None

	def set_mirror_flags(self, mirror):
		mirror.flags[MIRROR_FLAG] = True
		for flag, value in self._extra_mirror_flags.items():
			mirror.flags[flag] = value

	def _mirror_payload(self, target_doctype, target_value):
		data = self.doc.as_dict()
		for k in _SKIP_PAYLOAD_FIELDS:
			data.pop(k, None)
		data[self.DOCTYPE_FIELD] = target_doctype
		data[self.VALUE_FIELD] = target_value
		data["doctype"] = self.doc.doctype
		return data

	def create_mirror(self):
		target = self._target()
		if not target:
			return
		target_doctype, target_value = target
		if frappe.db.exists(self.doc.doctype, self.dedup_filter(target_doctype, target_value)):
			return
		mirror = frappe.get_doc(self._mirror_payload(target_doctype, target_value))
		self.set_mirror_flags(mirror)
		mirror.insert(ignore_permissions=True)

	def sync_state_to_mirror(self):
		mirror = self.find_mirror()
		if not mirror:
			return
		changed = False
		for field, value in self.doc.as_dict().items():
			if field in _SKIP_PAYLOAD_FIELDS or field in (self.DOCTYPE_FIELD, self.VALUE_FIELD):
				continue
			if mirror.get(field) != value:
				mirror.set(field, value)
				changed = True
		if not changed:
			return
		self.set_mirror_flags(mirror)
		mirror.save(ignore_permissions=True)

	def delete_mirror_for(self, old):
		old_target = find_target_for(old.get(self.DOCTYPE_FIELD), old.get(self.VALUE_FIELD))
		if not old_target:
			return
		target_doctype, target_value = old_target
		filters = self.dedup_filter(target_doctype, target_value)
		name = frappe.db.get_value(self.doc.doctype, filters, "name")
		if not name:
			return
		mirror = frappe.get_doc(self.doc.doctype, name)
		self.set_mirror_flags(mirror)
		mirror.delete(ignore_permissions=True)
