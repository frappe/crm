import frappe
from frappe.core.doctype.user_permission.user_permission import UserPermission
from frappe.utils import cstr

from crm.integrations.erpnext.mirror_sync import MIRROR_FLAG, MirrorSyncMixin
from crm.integrations.erpnext.utils import should_sync


class CustomUserPermission(MirrorSyncMixin, UserPermission):
	"""Mirror User Permissions between Item and CRM Product."""

	DOCTYPE_FIELD = "allow"
	VALUE_FIELD = "for_value"

	def before_validate(self):
		old = self.get_doc_before_save()
		if old and self.has_data_updated(old) and self.sync_active():
			self.delete_mirror_for(old)

	def after_insert(self):
		if self.should_mirror():
			self.create_mirror()

	def on_update(self):
		super().on_update()
		if not self.should_mirror():
			return
		old = self.get_doc_before_save()
		if old and self.has_data_updated(old):
			self.create_mirror()
		else:
			self.sync_state_to_mirror()

	def on_trash(self):
		super().on_trash()
		if not self.should_mirror():
			return
		mirror = self.find_mirror()
		if not mirror:
			return
		self.set_mirror_flags(mirror)
		mirror.delete(ignore_permissions=True)

	def dedup_filter(self, target_doctype: str, target_value: str) -> dict:
		# Match Frappe's 5-key dup check in validate_user_permission()
		return {
			**super().dedup_filter(target_doctype, target_value),
			"applicable_for": cstr(self.applicable_for),
			"apply_to_all_doctypes": self.apply_to_all_doctypes,
		}


def sync_user_permissions():
	"""Bulk-sync User Permissions between Item and CRM Product. Idempotent."""
	if not should_sync():
		return

	product_perms = frappe.get_list("User Permission", filters={"allow": "CRM Product"}, fields=["*"])
	item_perms = frappe.get_list("User Permission", filters={"allow": "Item"}, fields=["*"])
	existing_product = {(p.user, p.for_value) for p in product_perms}
	existing_item = {(p.user, p.for_value) for p in item_perms}

	for perm in item_perms:
		product = frappe.db.get_value("Item", perm.for_value, "crm_product_code")
		if not product or (perm.user, product) in existing_product:
			continue
		_mirror_permission(perm, "CRM Product", product)
		existing_product.add((perm.user, product))

	for perm in product_perms:
		item = frappe.db.get_value("CRM Product", perm.for_value, "erpnext_item_code")
		if not item or (perm.user, item) in existing_item:
			continue
		_mirror_permission(perm, "Item", item)
		existing_item.add((perm.user, item))


def _mirror_permission(src, target_doctype, target_value):
	data = dict(src)
	for k in ("name", "owner", "creation", "modified", "modified_by", "idx"):
		data.pop(k, None)
	data.update({"doctype": "User Permission", "allow": target_doctype, "for_value": target_value})
	doc = frappe.get_doc(data)
	doc.flags[MIRROR_FLAG] = True
	doc.insert(ignore_permissions=True)
