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


class MirrorSyncMixin:
	"""Generic mirror sync for lifecycle-bound docs (UserPermission, DocShare)
	between Item and CRM Product. Subclasses set DOCTYPE_FIELD + VALUE_FIELD.
	"""

	DOCTYPE_FIELD = ""
	VALUE_FIELD = ""

	def sync_active(self) -> bool:
		return should_sync()

	def should_mirror(self) -> bool:
		if self.flags.get(MIRROR_FLAG):
			return False
		if not self.sync_active():
			return False
		return self.get(self.DOCTYPE_FIELD) in ALLOWED_DOCTYPES

	def has_data_updated(self, old) -> bool:
		return self.get(self.DOCTYPE_FIELD) != old.get(self.DOCTYPE_FIELD) or self.get(
			self.VALUE_FIELD
		) != old.get(self.VALUE_FIELD)

	def _target(self):
		return find_target_for(self.get(self.DOCTYPE_FIELD), self.get(self.VALUE_FIELD))

	def dedup_filter(self, target_doctype: str, target_value: str) -> dict:
		return {
			self.DOCTYPE_FIELD: target_doctype,
			self.VALUE_FIELD: target_value,
			"user": self.user,
		}

	def find_mirror(self):
		target = self._target()
		if not target:
			return None
		target_doctype, target_value = target
		filters = self.dedup_filter(target_doctype, target_value)
		name = frappe.db.get_value(self.doctype, filters, "name")
		return frappe.get_doc(self.doctype, name) if name else None

	def set_mirror_flags(self, mirror):
		mirror.flags[MIRROR_FLAG] = True

	def _mirror_payload(self, target_doctype, target_value):
		data = self.as_dict()
		for k in _SKIP_PAYLOAD_FIELDS:
			data.pop(k, None)
		data[self.DOCTYPE_FIELD] = target_doctype
		data[self.VALUE_FIELD] = target_value
		data["doctype"] = self.doctype
		return data

	def create_mirror(self):
		target = self._target()
		if not target:
			return
		target_doctype, target_value = target
		if frappe.db.exists(self.doctype, self.dedup_filter(target_doctype, target_value)):
			return
		mirror = frappe.get_doc(self._mirror_payload(target_doctype, target_value))
		self.set_mirror_flags(mirror)
		mirror.insert(ignore_permissions=True)

	def sync_state_to_mirror(self):
		mirror = self.find_mirror()
		if not mirror:
			return
		changed = False
		for field, value in self.as_dict().items():
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
		name = frappe.db.get_value(self.doctype, filters, "name")
		if not name:
			return
		mirror = frappe.get_doc(self.doctype, name)
		self.set_mirror_flags(mirror)
		mirror.delete(ignore_permissions=True)
