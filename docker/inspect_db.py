import frappe
import json

frappe.init("crm.localhost")
frappe.connect()

print("=" * 60)
print("DATABASE INSPECTION")
print("=" * 60)

print("CRM Lead count:", frappe.db.count("CRM Lead"))
print("CRM Organization count:", frappe.db.count("CRM Organization"))
print("Contact count:", frappe.db.count("Contact"))

print("\n--- tabContact columns ---")
cols = frappe.db.get_table_columns("Contact")
print([c for c in cols if "custom" in c or "drop" in c or "assign" in c or "org" in c or "company" in c])

print("\n--- CRM Organizations ---")
orgs = frappe.db.sql("select name, organization_name, creation, owner from `tabCRM Organization` order by creation desc limit 10", as_dict=True)
print(json.dumps(orgs, indent=2, default=str))

print("\n--- Contacts in DB ---")
contacts = frappe.db.sql("select name, first_name, last_name, company_name, email_id, mobile_no, creation, owner, _assign from `tabContact` order by creation desc limit 10", as_dict=True)
print(json.dumps(contacts, indent=2, default=str))

print("\n--- Dynamic Links for Contacts ---")
links = frappe.db.sql("select parent, link_doctype, link_name from `tabDynamic Link` where parenttype='Contact' or link_doctype='CRM Organization' limit 20", as_dict=True)
print(json.dumps(links, indent=2, default=str))

print("\n--- Error Log ---")
errors = frappe.db.sql("select name, method, error, creation from `tabError Log` order by creation desc limit 5", as_dict=True)
print(json.dumps(errors, indent=2, default=str))

print("\n--- Custom Fields for Contact ---")
cf = frappe.db.sql("select name, dt, fieldname, label, fieldtype from `tabCustom Field` where dt='Contact'", as_dict=True)
print(json.dumps(cf, indent=2, default=str))

