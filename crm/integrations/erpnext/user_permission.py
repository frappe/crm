import frappe
from frappe.utils import cstr

from crm.integrations.erpnext.mirror_sync import MIRROR_FLAG, MirrorSync
from crm.integrations.erpnext.utils import should_sync


def _dedup_extra(doc) -> dict:
	return {
		"applicable_for": cstr(doc.applicable_for),
		"apply_to_all_doctypes": doc.apply_to_all_doctypes,
	}


def _sync(doc) -> MirrorSync:
	return MirrorSync(doc, "allow", "for_value", extra_dedup=_dedup_extra)


def before_validate(doc, method=None):
	sync = _sync(doc)
	old = doc.get_doc_before_save()
	if old and sync.has_data_updated(old) and sync.sync_active():
		sync.delete_mirror_for(old)


def after_insert(doc, method=None):
	sync = _sync(doc)
	if sync.should_mirror():
		sync.create_mirror()


def on_update(doc, method=None):
	sync = _sync(doc)
	if not sync.should_mirror():
		return
	old = doc.get_doc_before_save()
	if old and sync.has_data_updated(old):
		sync.create_mirror()
	else:
		sync.sync_state_to_mirror()


def on_trash(doc, method=None):
	sync = _sync(doc)
	if not sync.should_mirror():
		return
	mirror = sync.find_mirror()
	if not mirror:
		return
	sync.set_mirror_flags(mirror)
	mirror.delete(ignore_permissions=True)


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
