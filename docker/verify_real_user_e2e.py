import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"
HEADERS = {"Host": "crm.localhost"}

def create_session(usr, pwd):
    s = requests.Session()
    s.headers.update(HEADERS)
    res = s.post(f"{BASE_URL}/api/method/login", data={"usr": usr, "pwd": pwd})
    if res.status_code != 200:
        raise Exception(f"Failed to login as {usr}: {res.status_code} {res.text}")
    print(f"  [OK] Logged in as {usr}")
    return s

def run_tests():
    print("=" * 70)
    print("RUNNING REAL USER HTTP SESSION E2E TESTS (Admin, User 1, User 2)")
    print("=" * 70)

    # 1. Admin login
    print("\n--- Step 1: Admin Login ---")
    admin_session = create_session("Administrator", "admin")

    # Create a fresh controlled test contact
    ts = int(time.time())
    test_email = f"e2e_prospect_{ts}@example.com"
    test_first = f"E2E_First_{ts}"
    test_last = f"E2E_Last_{ts}"
    test_phone = f"+1555{ts % 10000:04d}9"
    test_company = f"E2E Corp {ts}"

    # First create organization
    org_res = admin_session.post(f"{BASE_URL}/api/method/frappe.client.insert", json={
        "doc": {
            "doctype": "CRM Organization",
            "organization_name": test_company
        }
    })
    assert org_res.status_code == 200, f"Failed to create test org: {org_res.text}"
    org_name = org_res.json()["message"]["name"]
    print(f"  Created test org: {org_name}")

    # Create unassigned contact
    contact_res = admin_session.post(f"{BASE_URL}/api/method/frappe.client.insert", json={
        "doc": {
            "doctype": "Contact",
            "first_name": test_first,
            "last_name": test_last,
            "company_name": test_company,
            "custom_organization": org_name,
            "email_ids": [{"email_id": test_email, "is_primary": 1}],
            "phone_nos": [{"phone": test_phone, "is_primary_phone": 1, "is_primary_mobile_no": 1}],
            "custom_is_dropped": 0
        }
    })
    assert contact_res.status_code == 200, f"Failed to create test contact: {contact_res.text}"
    contact_name = contact_res.json()["message"]["name"]
    print(f"  Created test contact: {contact_name} ({test_first} {test_last})")

    # Create linked address with Country = United States
    addr_res = admin_session.post(f"{BASE_URL}/api/method/frappe.client.insert", json={
        "doc": {
            "doctype": "Address",
            "address_title": test_company,
            "address_type": "Office",
            "address_line1": "100 Broadway",
            "city": "New York",
            "state": "NY",
            "country": "United States",
            "links": [
                {"link_doctype": "Contact", "link_name": contact_name},
                {"link_doctype": "CRM Organization", "link_name": org_name}
            ]
        }
    })
    assert addr_res.status_code == 200, f"Failed to create test address: {addr_res.text}"
    addr_name = addr_res.json()["message"]["name"]
    print(f"  Created test address: {addr_name} (United States)")

    # Step 2: Verify contact is in Unassigned
    counts_res = admin_session.get(f"{BASE_URL}/api/method/crm.api.contact.get_contact_tab_counts")
    assert counts_res.status_code == 200
    print(f"  Admin contact tab counts: {counts_res.json()['message']}")

    # Step 3: Admin assigns contact to User 2 (via bulk add_multiple)
    print("\n--- Step 3: Admin Assigns Contact to User 2 (bulk add_multiple) ---")
    assign_res = admin_session.post(f"{BASE_URL}/api/method/frappe.desk.form.assign_to.add_multiple", json={
        "doctype": "Contact",
        "name": json.dumps([contact_name]),
        "assign_to": json.dumps(["user2@example.com"]),
        "bulk_assign": True,
        "re_assign": True
    })
    assert assign_res.status_code == 200, f"Assignment failed: {assign_res.text}"
    print(f"  Assignment response: {assign_res.json()}")

    # Also test single assignment endpoint: frappe.desk.form.assign_to.add
    print("\n--- Test Single Assign Endpoint: frappe.desk.form.assign_to.add ---")
    single_ts = ts + 2
    single_email = f"single_{single_ts}@example.com"
    single_c_res = admin_session.post(f"{BASE_URL}/api/method/frappe.client.insert", json={
        "doc": {
            "doctype": "Contact",
            "first_name": f"Single_First_{single_ts}",
            "last_name": f"Single_Last_{single_ts}",
            "company_name": test_company,
            "custom_organization": org_name,
            "email_ids": [{"email_id": single_email, "is_primary": 1}],
            "phone_nos": [{"phone": f"+1555{single_ts % 10000:04d}0", "is_primary_phone": 1, "is_primary_mobile_no": 1}],
            "custom_is_dropped": 0
        }
    })
    single_c_name = single_c_res.json()["message"]["name"]
    single_assign_res = admin_session.post(f"{BASE_URL}/api/method/frappe.desk.form.assign_to.add", json={
        "doctype": "Contact",
        "name": single_c_name,
        "assign_to": json.dumps(["user2@example.com"])
    })
    assert single_assign_res.status_code == 200, f"Single assign failed: {single_assign_res.text}"
    print(f"  Single assign response: {single_assign_res.json()}")

    # Step 4: Verify contact appears under Contacts -> Assigned
    print("\n--- Step 4: Verify Contact in Contacts -> Assigned ---")
    contact_check = admin_session.get(f"{BASE_URL}/api/method/frappe.client.get_value", params={
        "doctype": "Contact",
        "filters": json.dumps({"name": contact_name}),
        "fieldname": json.dumps(["_assign", "custom_is_dropped"])
    })
    assert contact_check.status_code == 200
    contact_data = contact_check.json()["message"]
    print(f"  Contact _assign: {contact_data.get('_assign')}")
    assert "user2@example.com" in (contact_data.get("_assign") or ""), "user2@example.com not in Contact._assign!"
    assert contact_data.get("custom_is_dropped") == 0, "Contact should not be dropped!"

    # Also verify via Contacts -> Assigned tab query
    tab_counts = admin_session.get(f"{BASE_URL}/api/method/crm.api.contact.get_contact_tab_counts").json()["message"]
    print(f"  Tab counts after assignment: {tab_counts}")
    assert tab_counts["assigned"] >= 1, "Assigned tab count should be at least 1"

    # Step 5: Verify Assigned To displays User 2
    assigned_users = json.loads(contact_data.get("_assign") or "[]")
    assert "user2@example.com" in assigned_users
    print(f"  [OK] Contact {contact_name} is Assigned to: {assigned_users}")

    # Logout Admin
    admin_session.post(f"{BASE_URL}/api/method/logout")

    # Step 6: Log in as User 2
    print("\n--- Step 6: User 2 Login ---")
    u2_session = create_session("user2@example.com", "user2password")

    # Step 7 & 8: Open My Tasks -> To Do
    print("\n--- Step 7 & 8: Open User 2 My Tasks -> To Do ---")
    tasks_res = u2_session.get(f"{BASE_URL}/api/method/crm.api.daily_allocation.get_allocated_tasks", params={
        "status": "To Do"
    })
    assert tasks_res.status_code == 200, f"Failed to get tasks: {tasks_res.text}"
    u2_tasks = tasks_res.json()["message"]
    print(f"  User 2 has {len(u2_tasks)} 'To Do' tasks.")

    matching_tasks = [t for t in u2_tasks if t["contact"] == contact_name]
    assert len(matching_tasks) == 1, f"Expected exactly 1 task for {contact_name}, found: {len(matching_tasks)}"
    u2_task = matching_tasks[0]
    print(f"  Found assigned task (bulk): {u2_task['name']}")

    matching_single = [t for t in u2_tasks if t["contact"] == single_c_name]
    assert len(matching_single) == 1, f"Expected exactly 1 task for single assign {single_c_name}, found: {len(matching_single)}"
    print(f"  [OK] Single assign contact also appeared in User 2 My Tasks -> To Do: {matching_single[0]['name']}")

    # Step 9: Open the task and verify prospect name, organization, email, phone, allocation date
    print("\n--- Step 9: Verify Task Details ---")
    print(f"  Task details:")
    print(f"    Name: {u2_task.get('prospect_name')}")
    print(f"    Organization: {u2_task.get('organization')}")
    print(f"    Email: {u2_task.get('email')}")
    print(f"    Phone: {u2_task.get('mobile_no')}")
    print(f"    Allocation Date: {u2_task.get('allocation_date')}")
    print(f"    Status: {u2_task.get('status')}")
    print(f"    Assigned To: {u2_task.get('assigned_to')}")

    assert u2_task.get("assigned_to") == "user2@example.com", "assigned_to mismatch"
    assert u2_task.get("status") == "To Do", "status should be 'To Do'"
    assert f"{test_first} {test_last}" in u2_task.get("prospect_name", ""), "prospect_name mismatch"
    assert u2_task.get("organization") == test_company, "organization mismatch"
    assert u2_task.get("email") == test_email, "email mismatch"
    assert u2_task.get("mobile_no") == test_phone, "mobile_no mismatch"
    assert u2_task.get("country") == "United States", f"country mismatch: {u2_task.get('country')}"
    assert "America/New_York" in str(u2_task.get("timezone")) or "GMT" in str(u2_task.get("timezone")) or u2_task.get("raw_timezone") == "America/New_York", f"timezone mismatch: {u2_task.get('timezone')}"

    # Step 10: Verify email and call actions work from the task
    print("\n--- Step 10: Verify Email & Call Outreach Actions from Task ---")
    # 10a: Send Task Email
    email_send_res = u2_session.post(f"{BASE_URL}/api/method/crm.api.daily_allocation.send_task_email", json={
        "task_name": u2_task["name"],
        "recipient": test_email,
        "subject": "E2E Outreach Test",
        "content": "<p>Hello from User 2</p>"
    })
    assert email_send_res.status_code == 200, f"send_task_email failed: {email_send_res.text}"
    assert email_send_res.json()["message"]["success"] is True

    # Verify task status advanced to 'In Progress'
    task_after_email = u2_session.get(f"{BASE_URL}/api/method/frappe.client.get", params={
        "doctype": "CRM Daily Allocation",
        "name": u2_task["name"]
    })
    assert task_after_email.status_code == 200
    assert task_after_email.json()["message"]["status"] == "In Progress", f"Status expected 'In Progress', got {task_after_email.json()['message']['status']}"
    print(f"  [OK] Email sent and task status auto-advanced to 'In Progress'")

    # Reset back to 'To Do' for call test
    admin_session = create_session("Administrator", "admin")
    admin_session.post(f"{BASE_URL}/api/method/frappe.client.set_value", json={
        "doctype": "CRM Daily Allocation",
        "name": u2_task["name"],
        "fieldname": "status",
        "value": "To Do"
    })
    admin_session.post(f"{BASE_URL}/api/method/logout")

    # 10b: Log Task Call (Completed)
    call_log_res = u2_session.post(f"{BASE_URL}/api/method/crm.api.daily_allocation.log_task_call", json={
        "task_name": u2_task["name"],
        "call_type": "Outgoing",
        "phone": test_phone,
        "duration": 65,
        "status": "Completed",
        "note": "Connected with prospect; interested in demo."
    })
    assert call_log_res.status_code == 200, f"log_task_call failed: {call_log_res.text}"
    assert call_log_res.json()["message"]["success"] is True

    task_after_call = u2_session.get(f"{BASE_URL}/api/method/frappe.client.get", params={
        "doctype": "CRM Daily Allocation",
        "name": u2_task["name"]
    })
    assert task_after_call.status_code == 200
    assert task_after_call.json()["message"]["status"] == "In Progress"
    print(f"  [OK] Call logged and task status auto-advanced to 'In Progress'")

    # Step 11 & 12: User Isolation (User 1 vs User 2)
    print("\n--- Step 11 & 12: User Isolation Tests ---")
    admin_session = create_session("Administrator", "admin")
    
    # Create contact for User 1
    ts1 = ts + 1
    test1_email = f"u1_prospect_{ts1}@example.com"
    c1_res = admin_session.post(f"{BASE_URL}/api/method/frappe.client.insert", json={
        "doc": {
            "doctype": "Contact",
            "first_name": f"User1_Prospect_{ts1}",
            "last_name": "Test",
            "company_name": test_company,
            "custom_organization": org_name,
            "email_ids": [{"email_id": test1_email, "is_primary": 1}],
            "custom_is_dropped": 0
        }
    })
    c1_name = c1_res.json()["message"]["name"]
    # Assign to User 1
    admin_session.post(f"{BASE_URL}/api/method/frappe.desk.form.assign_to.add_multiple", json={
        "doctype": "Contact",
        "name": json.dumps([c1_name]),
        "assign_to": json.dumps(["user1@example.com"]),
        "bulk_assign": True,
        "re_assign": True
    })
    admin_session.post(f"{BASE_URL}/api/method/logout")

    # Login as User 1
    u1_session = create_session("user1@example.com", "user1password")
    u1_tasks = u1_session.get(f"{BASE_URL}/api/method/crm.api.daily_allocation.get_allocated_tasks").json()["message"]
    u1_contact_names = [t["contact"] for t in u1_tasks]
    assert c1_name in u1_contact_names, f"User 1 should see {c1_name}"
    assert contact_name not in u1_contact_names, f"User 1 should NOT see User 2's contact {contact_name}"
    print(f"  [OK] User 1 sees {c1_name} and NOT {contact_name}")

    # Verify User 2 cannot see User 1's task
    u2_tasks_all = u2_session.get(f"{BASE_URL}/api/method/crm.api.daily_allocation.get_allocated_tasks").json()["message"]
    u2_contact_names = [t["contact"] for t in u2_tasks_all]
    assert c1_name not in u2_contact_names, f"User 2 should NOT see User 1's contact {c1_name}"
    print(f"  [OK] User 2 cannot see User 1's task {c1_name}")

    # Verify User 2 cannot access or update User 1's allocation directly
    u1_task_record = [t for t in u1_tasks if t["contact"] == c1_name][0]
    u2_hack_attempt = u2_session.post(f"{BASE_URL}/api/method/crm.api.daily_allocation.update_task_status", json={
        "task_name": u1_task_record["name"],
        "status": "Completed"
    })
    assert u2_hack_attempt.status_code == 403 or "PermissionError" in u2_hack_attempt.text
    print(f"  [OK] User 2 direct update on User 1 task was BLOCKED with 403 / PermissionError")

    # Step 13: Reassignment & No Duplicate Tasks
    print("\n--- Step 13: Reassignment & No Duplicate Tasks Test ---")
    admin_session = create_session("Administrator", "admin")
    # Reassign contact_name from User 2 to User 1
    reassign_res = admin_session.post(f"{BASE_URL}/api/method/frappe.desk.form.assign_to.add_multiple", json={
        "doctype": "Contact",
        "name": json.dumps([contact_name]),
        "assign_to": json.dumps(["user1@example.com"]),
        "bulk_assign": True,
        "re_assign": True
    })
    assert reassign_res.status_code == 200

    # Query CRM Daily Allocation count for contact_name
    alloc_count_res = admin_session.get(f"{BASE_URL}/api/method/frappe.client.get_list", params={
        "doctype": "CRM Daily Allocation",
        "filters": json.dumps({"contact": contact_name}),
        "fields": json.dumps(["name", "assigned_to", "status"])
    })
    alloc_list = alloc_count_res.json()["message"]
    assert len(alloc_list) == 1, f"Expected exactly 1 allocation record for {contact_name}, found {len(alloc_list)}: {alloc_list}"
    assert alloc_list[0]["assigned_to"] == "user1@example.com", f"Expected assigned_to user1@example.com, got {alloc_list[0]['assigned_to']}"
    print(f"  [OK] Single allocation preserved: {alloc_list[0]['name']} now assigned to {alloc_list[0]['assigned_to']}")

    # Check User 2 no longer sees contact_name
    u2_tasks_after = u2_session.get(f"{BASE_URL}/api/method/crm.api.daily_allocation.get_allocated_tasks").json()["message"]
    assert contact_name not in [t["contact"] for t in u2_tasks_after], f"User 2 should no longer see {contact_name}"
    print(f"  [OK] Contact {contact_name} removed from User 2 My Tasks")

    # Check User 1 now sees contact_name
    u1_tasks_after = u1_session.get(f"{BASE_URL}/api/method/crm.api.daily_allocation.get_allocated_tasks").json()["message"]
    assert contact_name in [t["contact"] for t in u1_tasks_after], f"User 1 should now see {contact_name}"
    print(f"  [OK] Contact {contact_name} now visible in User 1 My Tasks")

    # Clean up test records
    print("\n--- Cleaning up test records ---")
    admin_session.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "Address", "name": addr_name})
    admin_session.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "Contact", "name": contact_name})
    admin_session.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "Contact", "name": c1_name})
    admin_session.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "Contact", "name": single_c_name})
    admin_session.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "CRM Organization", "name": org_name})
    for a in alloc_list:
        admin_session.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "CRM Daily Allocation", "name": a["name"]})
    admin_session.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "CRM Daily Allocation", "name": u1_task_record["name"]})
    if matching_single:
        admin_session.post(f"{BASE_URL}/api/method/frappe.client.delete", json={"doctype": "CRM Daily Allocation", "name": matching_single[0]["name"]})
    print("  [OK] Test records cleaned up successfully.")

    print("\n" + "=" * 70)
    print("ALL REAL USER HTTP SESSION E2E TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
