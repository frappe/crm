import requests
import json

s = requests.Session()
s.headers.update({"Host": "crm.localhost"})
res = s.post("http://localhost:8000/api/method/login", data={"usr": "Administrator", "pwd": "admin"})
print("Login status:", res.status_code)

# 1. Test get_contact_tab_counts
tab_counts_res = s.get("http://localhost:8000/api/method/crm.api.contact.get_contact_tab_counts")
print("tab_counts status:", tab_counts_res.status_code)
print("tab_counts response:", tab_counts_res.text[:500])

# 2. Test frappe.desk.reportview.get for Contact (Unassigned tab)
view_res = s.post("http://localhost:8000/api/method/frappe.desk.reportview.get", json={
    "doctype": "Contact",
    "fields": ["`tabContact`.`name`", "`tabContact`.`full_name`", "`tabContact`.`company_name`", "`tabContact`.`email_id`", "`tabContact`.`mobile_no`", "`tabContact`.`modified`", "`tabContact`.`image`", "`tabContact`.`_assign`", "`tabContact`.`custom_is_dropped`"],
    "filters": [["Contact", "custom_is_dropped", "=", 0], ["Contact", "_assign", "is", "not set"]],
    "order_by": "modified desc",
    "start": 0,
    "page_length": 20
})
print("reportview.get status:", view_res.status_code)
print("reportview.get response:", view_res.text[:500])

# 3. Test frappe.desk.reportview.get for CRM Organization
org_res = s.post("http://localhost:8000/api/method/frappe.desk.reportview.get", json={
    "doctype": "CRM Organization",
    "fields": ["`tabCRM Organization`.`name`", "`tabCRM Organization`.`organization_name`", "`tabCRM Organization`.`website`"],
    "order_by": "modified desc",
    "start": 0,
    "page_length": 20
})
print("Organizations query status:", org_res.status_code)
print("Organizations query response:", org_res.text[:500])
