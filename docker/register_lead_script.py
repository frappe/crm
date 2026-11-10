import os
import frappe

def register():
    script_path = '/workspace/docker/lead_list_script.js'
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
    except Exception as e:
        print(f"Could not read {script_path}: {e}")
        return

    script_name = 'CRM Lead List Customizations'
    if not frappe.db.exists('CRM Form Script', script_name):
        doc = frappe.get_doc({
            'doctype': 'CRM Form Script',
            'name': script_name,
            'dt': 'CRM Lead',
            'view': 'List',
            'enabled': 1,
            'script': script_content
        })
        doc.insert()
        frappe.db.commit()
        print(f"SUCCESS: {script_name} inserted.")
    else:
        doc = frappe.get_doc('CRM Form Script', script_name)
        doc.script = script_content
        doc.save()
        frappe.db.commit()
        print(f"SUCCESS: {script_name} updated.")

if __name__ == '__main__':
    sites_dir = '/home/frappe/frappe-bench/sites'
    os.chdir(sites_dir)
    os.makedirs(os.path.join(sites_dir, 'crm.localhost', 'logs'), exist_ok=True)
    frappe.init('crm.localhost', sites_path=sites_dir)
    frappe.connect()
    register()
    print("Site apps:", frappe.get_installed_apps())
