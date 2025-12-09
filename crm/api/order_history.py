# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: AGPLv3. See LICENSE

import frappe
from frappe import _


@frappe.whitelist()
def fetch_lead_order_history(lead_name, customer_name):
	"""
	Fetch order history for CRM Lead from Sales Orders
	
	Args:
		lead_name: CRM Lead document name
		customer_name: Customer name for matching
	"""
	try:
		if not lead_name:
			return {
				'success': False,
				'message': 'Lead name is required'
			}

		# Find customer(s) matching this lead name (case-insensitive)
		customers = frappe.db.sql("""
			SELECT name, customer_name
			FROM `tabCustomer`
			WHERE LOWER(customer_name) LIKE LOWER(%s)
			OR lead_name = %s
		""", (f"%{customer_name}%", lead_name), as_dict=True)

		if not customers:
			return {
				'success': False,
				'message': f'No customers found matching "{customer_name}"'
			}

		# Process each customer separately
		all_sales_orders = []

		for customer in customers:
			sales_orders = frappe.db.sql("""
				SELECT name, customer, transaction_date, delivery_status, 
					   delivery_date, status, net_total,
					   shopify_order_number
				FROM `tabSales Order`
				WHERE customer = %s
				AND docstatus != 2
				ORDER BY transaction_date DESC
			""", customer.name, as_dict=True)

			all_sales_orders.extend(sales_orders)

		if not all_sales_orders:
			return {
				'success': False,
				'message': 'No sales orders found for this customer'
			}

		# Get the Lead document
		lead_doc = frappe.get_doc("CRM Lead", lead_name)

		# Process each Sales Order
		total_items_added = 0

		for so in all_sales_orders:
			# Get items for this Sales Order (include name field for Sales Order Item)
			so_items = frappe.db.sql("""
				SELECT name, item_code, item_name, qty, rate
				FROM `tabSales Order Item`
				WHERE parent = %s
			""", so.name, as_dict=True)

			for item in so_items:
				# Check if this item already exists
				existing_items = [row for row in lead_doc.custom_order_history 
								if row.sales_order == so.name and row.item_name == item.item_name]

				# Get Work Order statuses via correct connection path
				ops_status, mat_status, pro_status, qa_status = _get_work_order_statuses(
					so.name, 
					item.item_code,
					item.get('name')  # Sales Order Item name
				)
				
				# Ensure mat_status is always set to a valid value (not None or empty)
				if not mat_status or not str(mat_status).strip():
					mat_status = "NO_RECIPE"
				
				if existing_items:
					# UPDATE existing item with current statuses
					existing_item = existing_items[0]
					existing_item.ops_status = ops_status
					existing_item.mat_status = mat_status
					existing_item.pro_status = pro_status
					existing_item.qa_status = qa_status
					existing_item.order_status = so.status
					existing_item.delivery_status = so.delivery_status or "Not Delivered"
					existing_item.delivery_date = so.delivery_date
					
					total_items_added += 1
				else:
					# ADD new item
					lead_doc.append("custom_order_history", {
						"sales_order": so.name,
						"order_date": so.transaction_date,
						"item_code": item.item_code,
						"item_name": item.item_name,
						"qty": item.qty,
						"rate": item.rate,
						"amount": so.net_total,
						"delivery_status": so.delivery_status or "Not Delivered",
						"delivery_date": so.delivery_date,
						"order_status": so.status,
						"ops_status": ops_status,
						"mat_status": mat_status,
						"pro_status": pro_status,
						"qa_status": qa_status
					})

					total_items_added += 1

		# Save the lead document
		if total_items_added > 0:
			lead_doc.save()
			frappe.db.commit()
			lead_doc.reload()

		return {
			'success': True,
			'message': f'Successfully synced {total_items_added} items from {len(all_sales_orders)} orders'
		}

	except Exception as e:
		frappe.log_error(f"Error fetching lead order history: {str(e)}", "Fetch Lead Order History Error")
		return {
			'success': False,
			'message': f'Error: {str(e)}'
		}


@frappe.whitelist()
def fetch_deal_order_history(deal_name, customer_name):
	"""
	Fetch order history for CRM Deal from Sales Orders
	
	Args:
		deal_name: CRM Deal document name
		customer_name: Customer name for matching (from Lead's lead_name)
	"""
	try:
		if not deal_name:
			return {
				'success': False,
				'message': 'Deal name is required'
			}

		# Find customer(s) matching this customer name (case-insensitive)
		customers = frappe.db.sql("""
			SELECT name, customer_name
			FROM `tabCustomer`
			WHERE LOWER(customer_name) LIKE LOWER(%s)
		""", f"%{customer_name}%", as_dict=True)

		if not customers:
			return {
				'success': False,
				'message': f'No customers found matching "{customer_name}"'
			}

		# Process each customer separately
		all_sales_orders = []

		for customer in customers:
			sales_orders = frappe.db.sql("""
				SELECT name, customer, transaction_date, delivery_status, 
					   delivery_date, status, net_total,
					   shopify_order_number
				FROM `tabSales Order`
				WHERE customer = %s
				AND docstatus != 2
				ORDER BY transaction_date DESC
			""", customer.name, as_dict=True)

			all_sales_orders.extend(sales_orders)

		if not all_sales_orders:
			return {
				'success': False,
				'message': 'No sales orders found for this customer'
			}

		# Get the Deal document
		deal_doc = frappe.get_doc("CRM Deal", deal_name)

		# Process each Sales Order
		total_items_added = 0

		for so in all_sales_orders:
			# Get items for this Sales Order
			so_items = frappe.db.sql("""
				SELECT name, item_code, item_name, qty, rate
				FROM `tabSales Order Item`
				WHERE parent = %s
			""", so.name, as_dict=True)

			for item in so_items:
				# Check if this item already exists
				existing_items = [row for row in deal_doc.custom_order_history 
								if row.sales_order == so.name and row.item_name == item.item_name]

				# Get Work Order statuses
				ops_status, mat_status, pro_status, qa_status = _get_work_order_statuses(
					so.name, 
					item.item_code,
					item.get('name')
				)
				
				# Ensure mat_status is always set to a valid value (not None or empty)
				if not mat_status or not str(mat_status).strip():
					mat_status = "NO_RECIPE"

				if existing_items:
					# UPDATE existing item
					existing_item = existing_items[0]
					existing_item.ops_status = ops_status
					existing_item.mat_status = mat_status
					existing_item.pro_status = pro_status
					existing_item.qa_status = qa_status
					existing_item.order_status = so.status
					existing_item.delivery_status = so.delivery_status or "Not Delivered"
					existing_item.delivery_date = so.delivery_date
					total_items_added += 1
				else:
					# ADD new item
					deal_doc.append("custom_order_history", {
						"sales_order": so.name,
						"order_date": so.transaction_date,
						"item_code": item.item_code,
						"item_name": item.item_name,
						"qty": item.qty,
						"rate": item.rate,
						"amount": so.net_total,
						"delivery_status": so.delivery_status or "Not Delivered",
						"delivery_date": so.delivery_date,
						"order_status": so.status,
						"ops_status": ops_status,
						"mat_status": mat_status,
						"pro_status": pro_status,
						"qa_status": qa_status
					})

					total_items_added += 1

		# Save the deal document
		if total_items_added > 0:
			deal_doc.save()
			frappe.db.commit()

		return {
			'success': True,
			'message': f'Successfully synced {total_items_added} items from {len(all_sales_orders)} orders'
		}

	except Exception as e:
		frappe.log_error(f"Error fetching deal order history: {str(e)}", "Fetch Deal Order History Error")
		return {
			'success': False,
			'message': f'Error: {str(e)}'
		}


def _get_work_order_statuses(sales_order_name, item_code, sales_order_item_name=None):
	"""
	Get Work Order statuses - Simply copy whatever is in the Work Order
	Workflow: Sales Order → Purchase Order → Inter Company SO → Work Order
	
	Args:
		sales_order_name: Sales Order document name
		item_code: Item code from Sales Order Item
		sales_order_item_name: Optional Sales Order Item name
	
	Returns:
		tuple: (ops_status, mat_status, pro_status, qa_status)
	"""
	# Default values
	ops_status = "Not Started"
	mat_status = "NO_RECIPE"
	pro_status = "NEW"
	qa_status = "AWAITING"

	try:
		# Step 1: Find Purchase Orders linked to this Sales Order
		purchase_orders = frappe.db.sql("""
			SELECT DISTINCT poi.parent
			FROM `tabPurchase Order Item` poi
			WHERE poi.sales_order = %s
			AND poi.item_code = %s
		""", (sales_order_name, item_code), as_dict=True)

		# Step 2: Get Inter Company Order Reference from Purchase Order
		for po_result in purchase_orders:
			try:
				po = frappe.get_doc("Purchase Order", po_result.parent)
				inter_company_so = po.get("inter_company_order_reference")

				if inter_company_so:
					# Step 3: Find Work Order - Get the document directly to access ALL fields
					wo_names = frappe.db.sql("""
						SELECT name
						FROM `tabWork Order`
						WHERE sales_order = %s
						AND production_item = %s
						AND docstatus != 2
						LIMIT 1
					""", (inter_company_so, item_code), as_dict=True)

					if wo_names:
						# Get Work Order document to access ALL fields
						wo_doc = frappe.get_doc("Work Order", wo_names[0].name)
						
						# Get ALL fields as dictionary (includes custom fields)
						wo_dict = wo_doc.as_dict()
						
						# Simply copy whatever status fields exist - try all possible field names
						# OPS Status
						ops_status_raw = (wo_dict.get("work_order_status") or 
										  wo_dict.get("custom_ops_status") or 
										  wo_dict.get("ops_status") or 
										  "Not Started")
						ops_status = str(ops_status_raw).strip() if ops_status_raw else "Not Started"
						
						# Production Status
						pro_status_raw = (wo_dict.get("production_status") or 
										 wo_dict.get("custom_production_status") or 
										 "NEW")
						pro_status = str(pro_status_raw).strip() if pro_status_raw else "NEW"
						
						# QA Status
						qa_status_raw = (wo_dict.get("qa_status") or 
										 wo_dict.get("custom_qa_status") or 
										 "AWAITING")
						qa_status = str(qa_status_raw).strip() if qa_status_raw else "AWAITING"
						
						# Ingredient Status - prioritize custom_ingredients_status field from Work Order
						# Try both dictionary access and direct attribute access to ensure we get the custom field
						ingredients_status_raw = (wo_dict.get("custom_ingredients_status") or 
												   getattr(wo_doc, "custom_ingredients_status", None))
						
						if ingredients_status_raw and str(ingredients_status_raw).strip():
							# Use the custom_ingredients_status value directly
							mat_status = str(ingredients_status_raw).strip()
						else:
							# Fallback to other field names if custom_ingredients_status doesn't exist
							ingredients_status_raw = (wo_dict.get("ingredient_status") or 
													 wo_dict.get("custom_ingredient_status") or 
													 wo_dict.get("ingredients_status"))
							ingredients_status = str(ingredients_status_raw).strip() if ingredients_status_raw else None
							
							material_reservation_raw = (wo_dict.get("material_reservation_status") or 
													   wo_dict.get("custom_material_reservation_status"))
							material_reservation = str(material_reservation_raw).strip() if material_reservation_raw else None
							material_transferred = wo_dict.get("material_transferred_for_manufacturing") or 0
							
							# Material status logic (fallback)
							if material_transferred and material_transferred > 0:
								mat_status = "READY"
							elif ingredients_status and ingredients_status == "IN_STOCK":
								mat_status = "READY"
							elif material_reservation and material_reservation == "Fully Reserved":
								mat_status = "READY"
							elif ingredients_status:
								mat_status = ingredients_status
							else:
								mat_status = "NO_RECIPE"
						
						return (ops_status, mat_status, pro_status, qa_status)
			except Exception as e:
				pass

		# Fallback: Try direct lookup from Sales Order to Work Order
		wo_names = frappe.db.sql("""
			SELECT name
			FROM `tabWork Order`
			WHERE sales_order = %s
			AND production_item = %s
			AND docstatus != 2
			LIMIT 1
		""", (sales_order_name, item_code), as_dict=True)

		if wo_names:
			wo_doc = frappe.get_doc("Work Order", wo_names[0].name)
			wo_dict = wo_doc.as_dict()
			
			# Simply copy whatever status fields exist
			ops_status_raw = (wo_dict.get("work_order_status") or 
							  wo_dict.get("custom_ops_status") or 
							  wo_dict.get("ops_status") or 
							  "Not Started")
			ops_status = str(ops_status_raw).strip() if ops_status_raw else "Not Started"
			
			pro_status_raw = (wo_dict.get("production_status") or 
							 wo_dict.get("custom_production_status") or 
							 "NEW")
			pro_status = str(pro_status_raw).strip() if pro_status_raw else "NEW"
			
			qa_status_raw = (wo_dict.get("qa_status") or 
							 wo_dict.get("custom_qa_status") or 
							 "AWAITING")
			qa_status = str(qa_status_raw).strip() if qa_status_raw else "AWAITING"
			
			# Ingredient Status - prioritize custom_ingredients_status field from Work Order
			# Try both dictionary access and direct attribute access to ensure we get the custom field
			ingredients_status_raw = (wo_dict.get("custom_ingredients_status") or 
									   getattr(wo_doc, "custom_ingredients_status", None))
			
			if ingredients_status_raw and str(ingredients_status_raw).strip():
				# Use the custom_ingredients_status value directly
				mat_status = str(ingredients_status_raw).strip()
			else:
				# Fallback to other field names if custom_ingredients_status doesn't exist
				ingredients_status_raw = (wo_dict.get("ingredient_status") or 
										   wo_dict.get("custom_ingredient_status") or 
										   wo_dict.get("ingredients_status"))
				ingredients_status = str(ingredients_status_raw).strip() if ingredients_status_raw else None
				
				material_reservation_raw = (wo_dict.get("material_reservation_status") or 
										   wo_dict.get("custom_material_reservation_status"))
				material_reservation = str(material_reservation_raw).strip() if material_reservation_raw else None
				material_transferred = wo_dict.get("material_transferred_for_manufacturing") or 0
				
				# Material status logic (fallback)
				if material_transferred and material_transferred > 0:
					mat_status = "READY"
				elif ingredients_status and ingredients_status == "IN_STOCK":
					mat_status = "READY"
				elif material_reservation and material_reservation == "Fully Reserved":
					mat_status = "READY"
				elif ingredients_status:
					mat_status = ingredients_status
				else:
					mat_status = "NO_RECIPE"
			
			return (ops_status, mat_status, pro_status, qa_status)
			
	except Exception as e:
		pass

	# Return defaults if no Work Order found
	return (ops_status, mat_status, pro_status, qa_status)

