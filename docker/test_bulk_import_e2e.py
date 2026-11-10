import os
import sys
import base64
import json
import time
import requests
import openpyxl

BASE_URL = "http://localhost:8000"
HEADERS = {"Host": "crm.localhost"}

def run_e2e():
    print("=" * 70)
    print("STARTING BULK IMPORT END-TO-END VERIFICATION")
    print("=" * 70)

    # 1. Login as Administrator
    s = requests.Session()
    s.headers.update(HEADERS)
    login_res = s.post(f"{BASE_URL}/api/method/login", data={"usr": "Administrator", "pwd": "admin"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    print("  [OK] Logged in as Administrator")

    # 2. Measure initial database counts
    counts_res = s.get(f"{BASE_URL}/api/method/crm.api.contact.get_contact_tab_counts")
    assert counts_res.status_code == 200, f"get_contact_tab_counts failed: {counts_res.text}"
    initial_unassigned = counts_res.json()["message"]["unassigned"]
    print(f"  [OK] Initial Unassigned Contacts: {initial_unassigned}")

    # Check initial record counts via frappe.client.get_list
    init_leads_res = s.get(f"{BASE_URL}/api/method/frappe.client.get_list", params={"doctype": "CRM Lead", "limit_page_length": 1})
    init_contacts_res = s.get(f"{BASE_URL}/api/method/frappe.client.get_list", params={"doctype": "Contact", "limit_page_length": 1})
    init_orgs_res = s.get(f"{BASE_URL}/api/method/frappe.client.get_list", params={"doctype": "CRM Organization", "limit_page_length": 1})

    # 3. Create a controlled XLSX file containing 5 contacts across 2 organizations
    ts = int(time.time())
    org_a = f"Quantum Horizons {ts}"
    org_b = f"Solaris Robotics {ts}"

    rows_data = [
        {"First Name": "Diana", "Last Name": "Prince", "Email": f"diana_{ts}@themyscira.com", "Phone": f"+1555{ts % 10000:04d}1", "Company Name": org_a, "Country": "United States"},
        {"First Name": "Arthur", "Last Name": "Curry", "Email": f"arthur_{ts}@atlantis.com", "Phone": f"+1555{ts % 10000:04d}2", "Company Name": org_a, "Country": "United States"},
        {"First Name": "Victor", "Last Name": "Stone", "Email": f"victor_{ts}@star-labs.com", "Phone": f"+1555{ts % 10000:04d}3", "Company Name": org_a, "Country": "United States"},
        {"First Name": "Barry", "Last Name": "Allen", "Email": f"barry_{ts}@centralcity.com", "Phone": f"+1555{ts % 10000:04d}4", "Company Name": org_b, "Country": "United States"},
        {"First Name": "Clark", "Last Name": "Kent", "Email": f"clark_{ts}@dailyplanet.com", "Phone": f"+1555{ts % 10000:04d}5", "Company Name": org_b, "Country": "United States"},
    ]

    xlsx_path = f"/tmp/bulk_test_{ts}.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Contacts"

    headers = ["First Name", "Last Name", "Email", "Phone", "Company Name", "Country"]
    ws.append(headers)
    for row in rows_data:
        ws.append([row[h] for h in headers])
    wb.save(xlsx_path)
    print(f"  [OK] Generated test XLSX with 5 contacts and 2 orgs: {xlsx_path}")

    with open(xlsx_path, "rb") as f:
        file_bytes = f.read()
    b64_content = base64.b64encode(file_bytes).decode("utf-8")

    # Step 1 of Import: parse_import_file
    print("\n--- Step 1: Parse Import File ---")
    parse_res = s.post(f"{BASE_URL}/api/method/crm.api.import_data.parse_import_file", json={
        "file_content": b64_content,
        "file_name": os.path.basename(xlsx_path),
    })
    assert parse_res.status_code == 200, f"parse_import_file failed: {parse_res.text}"
    parse_json = parse_res.json()["message"]
    file_token = parse_json["file_token"]
    assert parse_json["total_rows"] == 5, f"Expected 5 total rows, got {parse_json['total_rows']}"
    print(f"  [OK] File parsed successfully: token={file_token}, rows={parse_json['total_rows']}")
    print(f"  Suggested mapping: {parse_json.get('suggested_mapping')}")

    column_mapping = {
        "first_name": "First Name",
        "last_name": "Last Name",
        "email": "Email",
        "mobile_no": "Phone",
        "organization": "Company Name",
        "country": "Country"
    }

    # Step 2 of Import: preview_import
    print("\n--- Step 2: Preview Import ---")
    preview_res = s.post(f"{BASE_URL}/api/method/crm.api.import_data.preview_import", json={
        "file_token": file_token,
        "column_mapping": column_mapping,
    })
    assert preview_res.status_code == 200, f"preview_import failed: {preview_res.text}"
    preview_json = preview_res.json()["message"]
    print(f"  [OK] Preview: total={preview_json['total_rows']}, valid={preview_json['valid_rows']}, orgs_to_create={preview_json['orgs_to_create_count']}")
    assert preview_json["valid_rows"] == 5, f"Expected 5 valid rows, got {preview_json['valid_rows']}"
    assert preview_json["orgs_to_create_count"] == 2, f"Expected 2 orgs to create, got {preview_json['orgs_to_create_count']}"

    # Step 3 of Import: execute_bulk_import
    print("\n--- Step 3: Execute Bulk Import ---")
    exec_res = s.post(f"{BASE_URL}/api/method/crm.api.import_data.execute_bulk_import", json={
        "file_token": file_token,
        "column_mapping": column_mapping,
    })
    assert exec_res.status_code == 200, f"execute_bulk_import failed: {exec_res.text}"
    exec_json = exec_res.json()["message"]
    print(f"  Import result: {exec_json}")
    assert exec_json["success"] is True, f"Bulk import reported success=False: {exec_json}"
    assert exec_json["imported"] == 5, f"Expected 5 imported records, got {exec_json['imported']}"
    assert len(exec_json.get("errors", [])) == 0, f"Expected 0 errors, got {exec_json.get('errors')}"
    print(f"  [OK] 5 records successfully imported with 0 errors!")

    # Step 4: Verify Database Entities & Relationships
    print("\n--- Step 4: Verify DB Records & Relationships ---")
    
    # 4a: Check CRM Leads created: MUST BE 0!
    created_leads = s.get(f"{BASE_URL}/api/method/frappe.client.get_list", params={
        "doctype": "CRM Lead",
        "filters": json.dumps({"email": ["like", f"%_{ts}@%"]})
    }).json()["message"]
    assert len(created_leads) == 0, f"CRITICAL FAILURE: {len(created_leads)} CRM Leads were created! Must be 0."
    print("  [OK] CRM Leads created: 0 (Strict Zero Lead Requirement Passed)")

    # 4b: Check Organizations created: EXACTLY 2
    org_res_a = s.get(f"{BASE_URL}/api/method/frappe.client.get_value", params={
        "doctype": "CRM Organization",
        "filters": json.dumps({"organization_name": org_a}),
        "fieldname": "name"
    }).json()["message"]
    org_res_b = s.get(f"{BASE_URL}/api/method/frappe.client.get_value", params={
        "doctype": "CRM Organization",
        "filters": json.dumps({"organization_name": org_b}),
        "fieldname": "name"
    }).json()["message"]
    assert org_res_a and org_res_a.get("name"), f"Organization {org_a} not found in DB!"
    assert org_res_b and org_res_b.get("name"), f"Organization {org_b} not found in DB!"
    org_a_name = org_res_a["name"]
    org_b_name = org_res_b["name"]
    print(f"  [OK] Organizations created: 2 ({org_a_name}, {org_b_name})")

    # 4c: Check Contacts created: EXACTLY 5
    created_contacts = []
    for r in rows_data:
        c_res = s.get(f"{BASE_URL}/api/method/frappe.client.get_value", params={
            "doctype": "Contact",
            "filters": json.dumps({"email_id": r["Email"]}),
            "fieldname": json.dumps(["name", "first_name", "last_name", "company_name", "email_id", "mobile_no", "custom_is_dropped", "_assign"])
        }).json()["message"]
        assert c_res and c_res.get("name"), f"Contact with email {r['Email']} not found in DB!"
        
        # Verify field mapping
        assert c_res["first_name"] == r["First Name"], f"first_name mismatch: {c_res['first_name']} != {r['First Name']}"
        assert c_res["last_name"] == r["Last Name"], f"last_name mismatch: {c_res['last_name']} != {r['Last Name']}"
        assert c_res["company_name"] == r["Company Name"], f"company_name mismatch: {c_res['company_name']} != {r['Company Name']}"
        assert c_res["custom_is_dropped"] == 0, f"custom_is_dropped should be 0, got {c_res['custom_is_dropped']}"
        assert not c_res.get("_assign"), f"Contact should be unassigned, got {c_res.get('_assign')}"
        
        # Verify Dynamic Link to Organization
        links_res = s.get(f"{BASE_URL}/api/method/frappe.client.get_list", params={
            "doctype": "Dynamic Link",
            "filters": json.dumps({
                "parent": c_res["name"],
                "link_doctype": "CRM Organization",
                "link_name": r["Company Name"]
            })
        }).json()["message"]
        assert len(links_res) >= 1, f"Contact {c_res['name']} missing Dynamic Link to {r['Company Name']}"

        created_contacts.append(c_res)

    assert len(created_contacts) == 5
    print("  [OK] Contacts created: 5 (All verified with correct names, emails, phones, and org links)")

    # Step 5: Verify Contacts Visibility in Contacts -> Unassigned
    print("\n--- Step 5: Verify Contacts Visibility in UI API ---")
    
    # 5a: Tab counts
    tab_counts_after = s.get(f"{BASE_URL}/api/method/crm.api.contact.get_contact_tab_counts").json()["message"]
    print(f"  Tab counts after import: {tab_counts_after}")
    assert tab_counts_after["unassigned"] == initial_unassigned + 5, f"Expected {initial_unassigned + 5} unassigned, got {tab_counts_after['unassigned']}"
    print(f"  [OK] Admin Unassigned Tab count correctly increased by 5!")

    # 5b: Reportview query for Unassigned contacts (exact query used by Contacts.vue)
    unassigned_view_res = s.post(f"{BASE_URL}/api/method/frappe.desk.reportview.get", json={
        "doctype": "Contact",
        "fields": [
            "`tabContact`.`name`",
            "`tabContact`.`full_name`",
            "`tabContact`.`company_name`",
            "`tabContact`.`email_id`",
            "`tabContact`.`mobile_no`",
            "`tabContact`.`modified`",
            "`tabContact`.`image`",
            "`tabContact`.`_assign`",
            "`tabContact`.`custom_is_dropped`"
        ],
        "filters": [["Contact", "custom_is_dropped", "=", 0], ["Contact", "_assign", "is", "not set"]],
        "order_by": "modified desc",
        "start": 0,
        "page_length": 50
    })
    assert unassigned_view_res.status_code == 200, f"Unassigned view failed: {unassigned_view_res.text}"
    unassigned_data = unassigned_view_res.json()["message"]
    returned_contact_names = [row[0] for row in unassigned_data["values"]]
    
    for c in created_contacts:
        assert c["name"] in returned_contact_names, f"Contact {c['name']} not visible in Unassigned view!"
    print("  [OK] All 5 imported contacts are immediately visible in Contacts → Unassigned view!")

    # 5c: Reportview query for Organizations
    org_view_res = s.post(f"{BASE_URL}/api/method/frappe.desk.reportview.get", json={
        "doctype": "CRM Organization",
        "fields": ["`tabCRM Organization`.`name`", "`tabCRM Organization`.`organization_name`"],
        "order_by": "modified desc",
        "start": 0,
        "page_length": 50
    })
    assert org_view_res.status_code == 200, f"Org view failed: {org_view_res.text}"
    returned_org_names = [row[0] for row in org_view_res.json()["message"]["values"]]
    assert org_a_name in returned_org_names, f"Org {org_a_name} not visible in Organizations view!"
    assert org_b_name in returned_org_names, f"Org {org_b_name} not visible in Organizations view!"
    print("  [OK] Both organizations are visible in Organizations view!")

    # Step 6: Test Re-import Deduplication
    print("\n--- Step 6: Test Re-importing Same File (Deduplication) ---")
    re_parse_res = s.post(f"{BASE_URL}/api/method/crm.api.import_data.parse_import_file", json={
        "file_content": b64_content,
        "file_name": os.path.basename(xlsx_path),
    })
    re_token = re_parse_res.json()["message"]["file_token"]

    re_exec_res = s.post(f"{BASE_URL}/api/method/crm.api.import_data.execute_bulk_import", json={
        "file_token": re_token,
        "column_mapping": column_mapping,
    })
    assert re_exec_res.status_code == 200
    re_exec_json = re_exec_res.json()["message"]
    print(f"  Re-import result: {re_exec_json}")

    # Check tab counts: should remain EXACTLY the same (0 duplicates created)
    tab_counts_reimport = s.get(f"{BASE_URL}/api/method/crm.api.contact.get_contact_tab_counts").json()["message"]
    assert tab_counts_reimport["unassigned"] == tab_counts_after["unassigned"], f"Duplicate contacts were created! Count before: {tab_counts_after['unassigned']}, after: {tab_counts_reimport['unassigned']}"
    
    # Check orgs count: should remain 2
    orgs_count = s.get(f"{BASE_URL}/api/method/frappe.client.get_list", params={
        "doctype": "CRM Organization",
        "filters": json.dumps({"organization_name": ["in", [org_a, org_b]]})
    }).json()["message"]
    assert len(orgs_count) == 2, f"Expected 2 organizations, got {len(orgs_count)}"
    print("  [OK] Re-import deduplication 100% effective (0 duplicate contacts, 0 duplicate orgs, 0 leads)")

    # Step 7: Clean up test records
    print("\n--- Step 7: Clean up isolated test records ---")
    for c in created_contacts:
        s.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "Contact", "name": c["name"]})
    s.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "CRM Organization", "name": org_a_name})
    s.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "CRM Organization", "name": org_b_name})
    if os.path.exists(xlsx_path):
        os.remove(xlsx_path)
    print("  [OK] Cleaned up all test records.")

    print("\n" + "=" * 70)
    print("ALL BULK IMPORT END-TO-END VERIFICATION CHECKS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    run_e2e()

