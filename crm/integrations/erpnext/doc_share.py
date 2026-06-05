import frappe

from crm.integrations.erpnext.mirror_sync import MIRROR_FLAG, MirrorSync
from crm.integrations.erpnext.utils import should_sync


def _sync(doc) -> MirrorSync:
	return MirrorSync(
		doc,
		"share_doctype",
		"share_name",
		extra_mirror_flags={"ignore_share_permission": True},
	)


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
