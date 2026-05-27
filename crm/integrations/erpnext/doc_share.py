import frappe
from frappe.core.doctype.docshare.docshare import DocShare

from crm.integrations.erpnext.mirror_sync import MIRROR_FLAG, MirrorSyncMixin
from crm.integrations.erpnext.utils import should_sync


class CustomDocShare(MirrorSyncMixin, DocShare):
	DOCTYPE_FIELD = "share_doctype"
	VALUE_FIELD = "share_name"

	def before_validate(self):
		old = self.get_doc_before_save()
		if old and self.has_data_updated(old) and self.sync_active():
			self.delete_mirror_for(old)

	def after_insert(self):
		super().after_insert()
		if self.should_mirror():
			self.create_mirror()

	def on_update(self):
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

	def set_mirror_flags(self, mirror):
		super().set_mirror_flags(mirror)
		mirror.flags.ignore_share_permission = True


def sync_shared_docs():
	if not should_sync():
		return
	product_shares = frappe.get_list("DocShare", filters={"share_doctype": "CRM Product"}, fields=["*"])
	item_shares = frappe.get_list("DocShare", filters={"share_doctype": "Item"}, fields=["*"])
	existing_product = {(s.user, s.share_name) for s in product_shares}
	existing_item = {(s.user, s.share_name) for s in item_shares}

	for share in item_shares:
		product = frappe.db.get_value("Item", share.share_name, "crm_product_code")
		if not product or (share.user, product) in existing_product:
			continue
		_mirror_share(share, "CRM Product", product)
		existing_product.add((share.user, product))

	for share in product_shares:
		item = frappe.db.get_value("CRM Product", share.share_name, "erpnext_item_code")
		if not item or (share.user, item) in existing_item:
			continue
		_mirror_share(share, "Item", item)
		existing_item.add((share.user, item))


def _mirror_share(src, target_doctype, target_value):
	data = dict(src)
	for k in ("name", "owner", "creation", "modified", "modified_by", "idx"):
		data.pop(k, None)
	data.update({"doctype": "DocShare", "share_doctype": target_doctype, "share_name": target_value})
	doc = frappe.get_doc(data)
	doc.flags[MIRROR_FLAG] = True
	doc.flags.ignore_share_permission = True
	doc.insert(ignore_permissions=True)
