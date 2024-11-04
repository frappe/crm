import frappe
import requests

def get_base_url():
    url = frappe.conf.get("saas_billing_base_url") or "https://frappecloud.com"
    if frappe.conf.developer_mode and frappe.conf.get("saas_billing_base_url"):
        url = frappe.conf.get("saas_billing_base_url")
    return url

def get_site_name():
    site_name = frappe.local.site
    if frappe.conf.developer_mode and frappe.conf.get("saas_billing_site_name"):
        site_name = frappe.conf.get("saas_billing_site_name")
    return site_name

def get_headers():
    # check if user is system manager
    if frappe.get_roles(frappe.session.user).count("System Manager") == 0:
        frappe.throw("You are not allowed to access this resource")

    # check if communication secret is set
    if not frappe.conf.get("fc_communication_secret"):
        frappe.throw("Communication secret not set")

    return {
        "X-Site-Token": frappe.conf.get("fc_communication_secret"),
        "X-Site": get_site_name()
    }

@frappe.whitelist()
def generate_access_token():
    request = requests.post(f"{get_base_url()}/api/method/press.saas.api.auth.generate_access_token", headers=get_headers())
    if request.status_code == 200:
        return request.json()["message"]
    else:
        frappe.throw("Failed to generate access token")

@frappe.whitelist()
def is_access_token_valid(token):
    headers={ 'Content-Type': 'application/json' }
    request = requests.post(f"{get_base_url()}/api/method/press.saas.api.auth.is_access_token_valid", headers, json={ token })
    return request.json()["message"]

@frappe.whitelist()
def current_site_info():
    request = requests.post(f"{get_base_url()}/api/method/press.saas.api.site.info", headers=get_headers())
    if request.status_code == 200:
        return request.json().get("message")
    else:
        frappe.throw("Failed to get site info")

@frappe.whitelist()
def saas_api(method, data={}):
    request = requests.post(f"{get_base_url()}/api/method/press.saas.api.{method}", headers=get_headers(), json=data)
    print(request.json())
    return request.json().get("message")