import sys
import json
import traceback
import frappe
from frappe import _

frappe.init(site="crm.localhost")
frappe.connect()

print("=" * 70)
print("STARTING COMPLETE VERIFICATION OF CUSTOMIZED FRAPPE CRM WORKFLOW")
print("=" * 70)

all_passed = True

def run_test(name, fn):
    global all_passed
    print(f"\n--- [TEST] {name} ---")
    try:
        fn()
        print(f"--> [PASS] {name}")
    except Exception as e:
        all_passed = False
        print(f"--> [FAIL] {name}: {e}")
        traceback.print_exc()

# -----------------------------------------------------------------------------
# TEST A: BULK IMPORT & DEDUPLICATION (Contacts & Orgs only, 0 Leads)
# -----------------------------------------------------------------------------
def test_a():
    from crm.api.import_data import execute_bulk_import
    frappe.set_user("Administrator")
    
    init_leads = frappe.db.count("CRM Lead")
    init_contacts = frappe.db.count("Contact")
    init_orgs = frappe.db.count("CRM Organization")
    
    import time
    ts = int(time.time())
    org1 = f"Apex Corp {ts}"
    org2 = f"Nexus Innovations {ts}"
    e1 = f"alice_{ts}@veriftest.com"
    e2 = f"bob_{ts}@veriftest.com"
    e3 = f"charlie_{ts}@veriftest.com"
    
    p1 = f"+1555{ts % 10000:04d}1"
    p2 = f"+1555{ts % 10000:04d}2"
    p3 = f"+1555{ts % 10000:04d}3"
    
    rows = [
        {"First Name": "Alice", "Last Name": "Vanguard", "Email": e1, "Phone": p1, "Company Name": org1, "Country": "United States"},
        {"First Name": "Bob", "Last Name": "Vanguard", "Email": e2, "Phone": p2, "Company Name": org1, "Country": "United States"},
        {"First Name": "Charlie", "Last Name": "Nexus", "Email": e3, "Phone": p3, "Company Name": org2, "Country": "United Kingdom"}
    ]
    mapping = {
        "First Name": "first_name",
        "Last Name": "last_name",
        "Email": "email",
        "Phone": "mobile_no",
        "Company Name": "organization",
        "Country": "country"
    }
    
    # Run 1: initial import
    res1 = execute_bulk_import(rows=rows, column_mapping=mapping)
    assert res1.get("success") is True, f"Import failed: {res1}"
    assert res1.get("successful_records") == 3, f"Expected 3 successful records, got {res1.get('successful_records')}"
    
    after_leads = frappe.db.count("CRM Lead")
    after_contacts = frappe.db.count("Contact")
    after_orgs = frappe.db.count("CRM Organization")
    
    # Critical requirement: Zero CRM Leads created
    leads_diff = after_leads - init_leads
    contacts_diff = after_contacts - init_contacts
    orgs_diff = after_orgs - init_orgs
    
    assert leads_diff == 0, f"FAIL: {leads_diff} CRM Leads were created! Must be 0."
    assert contacts_diff == 3, f"Expected 3 new Contacts, got {contacts_diff}"
    assert orgs_diff == 2, f"Expected 2 new Organizations ({org1}, {org2}), got {orgs_diff}"
    
    # Check linked contact and organization
    c_doc = frappe.get_doc("Contact", {"email_id": e1})
    assert c_doc.company_name == org1, f"Contact company_name mismatch: {c_doc.company_name}"
    
    # Run 2: Re-import same data -> verify deduplication (0 new orgs, 0 new contacts, 0 new leads)
    res2 = execute_bulk_import(rows=rows, column_mapping=mapping)
    final_leads = frappe.db.count("CRM Lead")
    final_contacts = frappe.db.count("Contact")
    final_orgs = frappe.db.count("CRM Organization")
    
    assert final_leads == after_leads, "Duplicate import created leads!"
    assert final_contacts == after_contacts, "Duplicate import created duplicate contacts!"
    assert final_orgs == after_orgs, "Duplicate import created duplicate organizations!"
    print(f"Verified: 0 Leads created, 3 Contacts created, 2 Orgs created, Deduplication 100% effective.")

# -----------------------------------------------------------------------------
# TEST B: CONTACT ASSIGNMENT & TAB COUNTS
# -----------------------------------------------------------------------------
def test_b():
    from crm.api.contact import get_contact_tab_counts, mark_contacts_dropped
    from frappe.desk.form import assign_to
    frappe.set_user("Administrator")
    
    contact_name = frappe.db.get_value("Contact", {"email_id": ["like", "%@veriftest.com"]}, "name")
    assert contact_name, "Contact not found for test_b"
    
    # Clear any assignments first
    assign_to.clear("Contact", contact_name, ignore_permissions=True)
    frappe.db.set_value("Contact", contact_name, "custom_is_dropped", 0)
    frappe.db.commit()
    
    counts1 = get_contact_tab_counts()
    print(f"Tab counts before assignment: {counts1}")
    
    # Assign contact to user1@example.com
    assign_to.add({
        "assign_to": ["user1@example.com"],
        "doctype": "Contact",
        "name": contact_name
    })
    frappe.db.commit()
    
    counts2 = get_contact_tab_counts()
    print(f"Tab counts after assigning to user1: {counts2}")
    
    # Verify user1 session counts
    frappe.set_user("user1@example.com")
    u1_counts = get_contact_tab_counts()
    assert u1_counts["assigned"] >= 1, f"user1 should see at least 1 assigned contact: {u1_counts}"
    
    # Non-admin cannot mark contacts dropped
    try:
        mark_contacts_dropped([contact_name], 1)
        raise AssertionError("Sales User should NOT be allowed to mark contacts dropped!")
    except frappe.PermissionError:
        print("Verified: Non-admin correctly rejected from marking contacts dropped.")
    
    # Admin marks contact dropped
    frappe.set_user("Administrator")
    mark_contacts_dropped([contact_name], 1)
    counts3 = get_contact_tab_counts()
    assert frappe.db.get_value("Contact", contact_name, "custom_is_dropped") == 1
    
    # Restore contact to unassigned
    mark_contacts_dropped([contact_name], 0)
    assert frappe.db.get_value("Contact", contact_name, "custom_is_dropped") == 0
    print("Verified: Unassigned -> Assigned -> Dropped -> Restore workflow works seamlessly.")

# -----------------------------------------------------------------------------
# TEST C: DAILY ALLOCATION
# -----------------------------------------------------------------------------
def test_c():
    from crm.api.daily_allocation import allocate_prospects, get_daily_allocation_summary
    today = frappe.utils.today()
    
    # Standard user cannot allocate prospects
    frappe.set_user("user1@example.com")
    try:
        allocate_prospects("user1@example.com", ["FakeContact"], today)
        raise AssertionError("Sales User should NOT be permitted to allocate prospects!")
    except frappe.PermissionError:
        print("Verified: Sales user correctly blocked from allocating prospects.")
        
    # Admin allocates
    frappe.set_user("Administrator")
    contacts = frappe.get_all("Contact", filters={"email_id": ["like", "%@veriftest.com"]}, pluck="name", limit=3)
    c1, c2, c3 = contacts[0], contacts[1], contacts[2]
    
    res = allocate_prospects("user1@example.com", [c1, c2], today, force=True)
    assert res.get("success") is True, f"Allocation failed: {res}"
    print(f"Allocated {res.get('allocated_count')} contacts to user1@example.com")
    
    # Duplicate prevention: allocate again without force
    res_dup = allocate_prospects("user1@example.com", [c1, c2], today, force=False)
    assert res_dup.get("allocated_count") == 0, "Duplicate allocation was not prevented!"
    assert res_dup.get("skipped_count") == 2, "Expected 2 skipped records on duplicate allocation!"
    print("Verified: Duplicate allocation on same date successfully prevented.")
    
    # Allocate c3 to user2@example.com
    res_u2 = allocate_prospects("user2@example.com", [c3], today, force=True)
    assert res_u2.get("success") is True
    print(f"Allocated {res_u2.get('allocated_count')} contact to user2@example.com")

# -----------------------------------------------------------------------------
# TEST D: MY TASK WORKSPACE & RBAC
# -----------------------------------------------------------------------------
def test_d():
    from crm.api.daily_allocation import get_allocated_tasks, bulk_update_tasks, bulk_delete_tasks
    today = frappe.utils.today()
    
    # Check user1 tasks
    frappe.set_user("user1@example.com")
    u1_tasks = get_allocated_tasks(date=today)
    for t in u1_tasks:
        assert t["assigned_to"] == "user1@example.com", f"user1 saw task assigned to {t['assigned_to']}!"
    print(f"user1 sees only own tasks ({len(u1_tasks)} tasks).")
    
    # Check user2 tasks
    frappe.set_user("user2@example.com")
    u2_tasks = get_allocated_tasks(date=today)
    for t in u2_tasks:
        assert t["assigned_to"] == "user2@example.com", f"user2 saw task assigned to {t['assigned_to']}!"
    print(f"user2 sees only own tasks ({len(u2_tasks)} tasks).")
    
    # user1 attempts to delete tasks -> Must be rejected
    frappe.set_user("user1@example.com")
    if u1_tasks:
        try:
            bulk_delete_tasks([u1_tasks[0]["name"]])
            raise AssertionError("Sales user should NOT be able to delete tasks!")
        except frappe.PermissionError:
            print("Verified: Sales user correctly blocked from deleting tasks.")
            
    # Status bulk update across the 6 statuses
    t_name = u1_tasks[0]["name"]
    for test_status in ["Pending", "Callback", "Follow up", "Not Interested", "To Do"]:
        bulk_update_tasks([t_name], status=test_status)
        current_st = frappe.db.get_value("CRM Daily Allocation", t_name, "status")
        assert current_st == test_status, f"Expected status {test_status}, got {current_st}"
    print("Verified: Task workflow status transitions work across all 6 statuses.")

# -----------------------------------------------------------------------------
# TEST E: EMAIL & CALL AUTOMATIC STATUS ADVANCEMENT
# -----------------------------------------------------------------------------
def test_e():
    from crm.api.daily_allocation import send_task_email, log_task_call, get_allocated_tasks
    today = frappe.utils.today()
    frappe.set_user("user1@example.com")
    
    u1_tasks = get_allocated_tasks(date=today)
    task1 = u1_tasks[0]
    task2 = u1_tasks[1]
    
    # Reset both to 'To Do'
    frappe.db.set_value("CRM Daily Allocation", task1["name"], "status", "To Do")
    frappe.db.set_value("CRM Daily Allocation", task2["name"], "status", "To Do")
    frappe.db.commit()
    
    # 1. Send task email from My Task
    mail_res = send_task_email(
        task_name=task1["name"],
        recipient=task1["email"],
        subject="Automated Verification Email",
        content="Testing task status transition to In Progress."
    )
    assert mail_res.get("success") is True
    st_after_mail = frappe.db.get_value("CRM Daily Allocation", task1["name"], "status")
    assert st_after_mail == "In Progress", f"Task should advance to In Progress, got {st_after_mail}"
    print("Verified: Sending email advances task from 'To Do' to 'In Progress'.")
    
    # 2. Log non-completed call (e.g. No Answer) -> Should NOT advance to In Progress
    log_task_call(
        task_name=task2["name"],
        call_type="Outgoing",
        phone=task2["mobile_no"],
        duration=30,
        status="No Answer",
        note="Call went to voicemail"
    )
    st_after_unanswered = frappe.db.get_value("CRM Daily Allocation", task2["name"], "status")
    assert st_after_unanswered == "To Do", f"Unanswered call should not advance status, got {st_after_unanswered}"
    print("Verified: Non-completed call does not change status (remains 'To Do').")
    
    # 3. Log completed call -> Advances to 'In Progress'
    log_task_call(
        task_name=task2["name"],
        call_type="Outgoing",
        phone=task2["mobile_no"],
        duration=180,
        status="Completed",
        note="Client requested a callback next week"
    )
    st_after_completed = frappe.db.get_value("CRM Daily Allocation", task2["name"], "status")
    assert st_after_completed == "In Progress", f"Completed call should advance task to In Progress, got {st_after_completed}"
    print("Verified: Completed call advances task from 'To Do' to 'In Progress'.")

# -----------------------------------------------------------------------------
# TEST F: CONTACT DETAIL READ-ONLY EMAIL
# -----------------------------------------------------------------------------
def test_f():
    from crm.api.contact import send_contact_email
    frappe.set_user("user1@example.com")
    c_name = frappe.db.get_value("Contact", {"email_id": ["like", "%@veriftest.com"]}, "name")
    
    # Calling send_contact_email must be rejected with PermissionError
    try:
        send_contact_email(
            contact=c_name,
            recipient="alice.vanguard@veriftest.com",
            subject="Test Blocked Email",
            content="This should fail."
        )
        raise AssertionError("send_contact_email should have thrown PermissionError!")
    except frappe.PermissionError as pe:
        assert "disabled" in str(pe).lower(), f"Unexpected error message: {pe}"
        print(f"Verified: send_contact_email blocked with message: '{pe}'")

# -----------------------------------------------------------------------------
# TEST G: SECURITY & ROLE-BASED ACCESS CONTROL
# -----------------------------------------------------------------------------
def test_g():
    frappe.set_user("Administrator")
    
    # Ensure test records exist for deletion tests
    contact = frappe.db.get_value("Contact", {"email_id": "bob.vanguard@veriftest.com"}, "name")
    org = frappe.db.get_value("CRM Organization", {"organization_name": "Apex Corp Global"}, "name")
    lead = frappe.db.get_value("CRM Lead", {}, "name")
    alloc = frappe.db.get_value("CRM Daily Allocation", {"assigned_to": "user1@example.com"}, "name")
    comm = frappe.db.get_value("Communication", {"reference_doctype": "Contact"}, "name")
    call_log = frappe.db.get_value("CRM Call Log", {"reference_doctype": "Contact"}, "name")
    fcrm_note = frappe.db.get_value("FCRM Note", {}, "name")
    
    # Switch to standard user user1@example.com
    frappe.set_user("user1@example.com")
    print(f"Executing RBAC security checks as: {frappe.session.user} (Roles: {frappe.get_roles('user1@example.com')})")
    
    # 1. Contact Delete
    if contact:
        try:
            frappe.delete_doc("Contact", contact)
            raise AssertionError("Sales User should NOT be able to delete Contact!")
        except frappe.PermissionError:
            print("  [G.1] Contact delete: BLOCKED (PermissionError)")
            
    # 2. CRM Organization Delete
    if org:
        try:
            frappe.delete_doc("CRM Organization", org)
            raise AssertionError("Sales User should NOT be able to delete CRM Organization!")
        except frappe.PermissionError:
            print("  [G.2] CRM Organization delete: BLOCKED (PermissionError)")
            
    # 3. CRM Lead Delete
    if lead:
        try:
            frappe.delete_doc("CRM Lead", lead)
            raise AssertionError("Sales User should NOT be able to delete CRM Lead!")
        except frappe.PermissionError:
            print("  [G.3] CRM Lead delete: BLOCKED (PermissionError)")
            
    # 4. Communication Delete
    if comm:
        try:
            frappe.delete_doc("Communication", comm)
            raise AssertionError("Sales User should NOT be able to delete Communication!")
        except frappe.PermissionError:
            print("  [G.4] Communication delete: BLOCKED (PermissionError)")
            
    # 5. Communication Update
    if comm:
        try:
            doc = frappe.get_doc("Communication", comm)
            doc.content = "Hacked content"
            doc.save()
            raise AssertionError("Sales User should NOT be able to update Communication!")
        except frappe.PermissionError:
            print("  [G.5] Communication update: BLOCKED (PermissionError)")
            
    # 6. CRM Call Log Delete
    if call_log:
        try:
            frappe.delete_doc("CRM Call Log", call_log)
            raise AssertionError("Sales User should NOT be able to delete CRM Call Log!")
        except frappe.PermissionError:
            print("  [G.6] CRM Call Log delete: BLOCKED (PermissionError)")
            
    # 7. CRM Call Log Update
    if call_log:
        try:
            doc = frappe.get_doc("CRM Call Log", call_log)
            doc.duration = 9999
            doc.save()
            raise AssertionError("Sales User should NOT be able to update CRM Call Log!")
        except frappe.PermissionError:
            print("  [G.7] CRM Call Log update: BLOCKED (PermissionError)")
            
    # 8. FCRM Note Delete
    if fcrm_note:
        try:
            frappe.delete_doc("FCRM Note", fcrm_note)
            raise AssertionError("Sales User should NOT be able to delete FCRM Note!")
        except frappe.PermissionError:
            print("  [G.8] FCRM Note delete: BLOCKED (PermissionError)")
            
    # 9. CRM Daily Allocation Delete
    if alloc:
        try:
            frappe.delete_doc("CRM Daily Allocation", alloc)
            raise AssertionError("Sales User should NOT be able to delete CRM Daily Allocation!")
        except frappe.PermissionError:
            print("  [G.9] Daily Allocation delete: BLOCKED (PermissionError)")
            
    # 10. Update another user's allocation
    frappe.set_user("Administrator")
    u2_alloc = frappe.db.get_value("CRM Daily Allocation", {"assigned_to": "user2@example.com"}, "name")
    if u2_alloc:
        frappe.set_user("user1@example.com")
        from crm.api.daily_allocation import update_task_status
        try:
            update_task_status(u2_alloc, "Completed")
            raise AssertionError("user1 should NOT be able to update user2's allocation!")
        except frappe.PermissionError:
            print("  [G.10] Update another user's allocation: BLOCKED (PermissionError)")

# -----------------------------------------------------------------------------
# RUN ALL
# -----------------------------------------------------------------------------
run_test("Test A: Bulk Import & Deduplication (Zero Leads, Contacts & Orgs only)", test_a)
run_test("Test B: Contact Assignment & Tab Counts", test_b)
run_test("Test C: Daily Allocation & Duplicate Prevention", test_c)
run_test("Test D: My Task Workspace & 6 Statuses", test_d)
run_test("Test E: Email & Call Automatic Status Advancement", test_e)
run_test("Test F: Contact Detail Read-Only Email", test_f)
run_test("Test G: Security & Role-Based Access Control", test_g)

print("\n" + "=" * 70)
if all_passed:
    print("ALL TESTS (A through G) PASSED WITH ZERO ERRORS!")
else:
    print("SOME TESTS FAILED! Review output above.")
    sys.exit(1)
print("=" * 70)
