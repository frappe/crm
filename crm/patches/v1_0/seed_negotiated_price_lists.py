import frappe


ITEMS = {
	"CV-HIMS-KEPH-2":  "CareverseHIMS -- Level 2",
	"CV-HIMS-KEPH-3":  "CareverseHIMS -- Level 3",
	"CV-HIMS-KEPH-3A": "CareverseHIMS -- Level 3A",
	"CV-HIMS-KEPH-3B": "CareverseHIMS -- Level 3B",
	"CV-HIMS-KEPH-4":  "CareverseHIMS -- Level 4",
	"CV-HIMS-KEPH-4B": "CareverseHIMS -- Level 4B",
	"CV-HIMS-KEPH-5":  "CareverseHIMS -- Level 5",
}

PRICE_LISTS = {
	"Negotiated Year 1": {
		"CV-HIMS-KEPH-2": 28425.93, "CV-HIMS-KEPH-3": 28425.93,
		"CV-HIMS-KEPH-3A": 101161.82, "CV-HIMS-KEPH-3B": 28425.93,
		"CV-HIMS-KEPH-4": 101161.82, "CV-HIMS-KEPH-4B": 101161.82,
		"CV-HIMS-KEPH-5": 335412.65,
	},
	"Negotiated Year 2": {
		"CV-HIMS-KEPH-2": 28425.93, "CV-HIMS-KEPH-3": 28425.93,
		"CV-HIMS-KEPH-3A": 101161.82, "CV-HIMS-KEPH-3B": 28425.93,
		"CV-HIMS-KEPH-4": 101161.82, "CV-HIMS-KEPH-4B": 101161.82,
		"CV-HIMS-KEPH-5": 335412.65,
	},
	"Negotiated Year 3": {
		"CV-HIMS-KEPH-2": 22239.23, "CV-HIMS-KEPH-3": 22239.23,
		"CV-HIMS-KEPH-3A": 83668.26, "CV-HIMS-KEPH-3B": 22239.23,
		"CV-HIMS-KEPH-4": 83668.26, "CV-HIMS-KEPH-4B": 83668.26,
		"CV-HIMS-KEPH-5": 277682.26,
	},
	"Negotiated Year 4": {
		"CV-HIMS-KEPH-2": 23351.19, "CV-HIMS-KEPH-3": 23351.19,
		"CV-HIMS-KEPH-3A": 87851.67, "CV-HIMS-KEPH-3B": 23351.19,
		"CV-HIMS-KEPH-4": 87851.67, "CV-HIMS-KEPH-4B": 87851.67,
		"CV-HIMS-KEPH-5": 291566.38,
	},
	"Negotiated Year 5": {
		"CV-HIMS-KEPH-2": 24518.75, "CV-HIMS-KEPH-3": 24518.75,
		"CV-HIMS-KEPH-3A": 92244.25, "CV-HIMS-KEPH-3B": 24518.75,
		"CV-HIMS-KEPH-4": 92244.25, "CV-HIMS-KEPH-4B": 92244.25,
		"CV-HIMS-KEPH-5": 306144.69,
	},
}


def execute():
	_seed_items()
	_seed_price_lists()
	frappe.db.commit()


def _seed_items():
	for item_code, item_name in ITEMS.items():
		if frappe.db.exists("Item", item_code):
			continue
		frappe.get_doc({
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_name,
			"item_group": "Services",
			"stock_uom": "Nos",
			"is_sales_item": 1,
			"is_stock_item": 0,
		}).insert(ignore_permissions=True)  # SYSTEM-INTERNAL


def _seed_price_lists():
	for pl_name, prices in PRICE_LISTS.items():
		if not frappe.db.exists("Price List", pl_name):
			frappe.get_doc({
				"doctype": "Price List",
				"price_list_name": pl_name,
				"currency": "KES",
				"selling": 1,
				"buying": 0,
				"enabled": 1,
			}).insert(ignore_permissions=True)  # SYSTEM-INTERNAL
		for item_code, rate in prices.items():
			if frappe.db.exists("Item Price", {"price_list": pl_name, "item_code": item_code}):
				continue
			frappe.get_doc({
				"doctype": "Item Price",
				"price_list": pl_name,
				"item_code": item_code,
				"price_list_rate": rate,
				"currency": "KES",
				"uom": "Nos",
			}).insert(ignore_permissions=True)  # SYSTEM-INTERNAL
