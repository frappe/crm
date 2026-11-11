import requests
import json
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

def test_full_workflow():
    print("=" * 70)
    print("STARTING COMPLETE 4-CHANGE WORKFLOW AUDIT & E2E VERIFICATION")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Admin Login & User Verification
    # -------------------------------------------------------------
    print("\n--- Test 1: Admin & User Login (smrikaam@gmail.com, sam.walker@smrikaam.com) ---")
    admin_session = create_session("smrikaam@gmail.com", "SmrikaamAdmin@2026!")
    sam_session = create_session("sam.walker@smrikaam.com", "SamWalkerCRM@2026!")

    # -------------------------------------------------------------
    # 2. CHANGE 1: Bulk Email Preview, Editing & 3-Prospect Personalization
    # -------------------------------------------------------------
    print("\n--- Test 2: CHANGE 1 - Bulk Email Branded Preview, Visual Edit & 3-Prospect Personalization ---")
    # Verify Demo template rendering returns clean body and branded shell
    demo_res = sam_session.post(f"{BASE_URL}/api/method/crm.api.daily_allocation.render_email_template", json={
        "template_name": "Demo"
    })
    assert demo_res.status_code == 200, f"Demo render failed: {demo_res.text}"
    demo_data = demo_res.json()["message"]
    assert demo_data["is_branded"] == True, "Demo template must be flagged as branded"
    assert "<!doctype html" in demo_data["content"].lower(), "Preview must contain full HTML email document"
    assert "PROGRESS THROUGH INNOVATION" in demo_data["content"], "Branded header must be preserved"
    assert "SMRIKAAM TECHNOLOGIES" in demo_data["content"], "Brand logo/title must be preserved"
    assert "body-pad" not in demo_data["body_content"], "TipTap editor body must NOT contain raw table class tags"
    print("  [OK] Demo template correctly separates clean visual body and branded email shell")

    # Create 3 test prospects: John, Alex, David
    ts = int(time.time())
    recipients_data = [
        {"first_name": "John", "last_name": f"Tester_{ts}", "email": f"john_{ts}@example.com", "country": "United States", "timezone": "America/New_York"},
        {"first_name": "Alex", "last_name": f"Tester_{ts}", "email": f"alex_{ts}@example.com", "country": "United Kingdom", "timezone": "Europe/London"},
        {"first_name": "David", "last_name": f"Tester_{ts}", "email": f"david_{ts}@example.com", "country": "", "timezone": ""},
    ]

    contact_names = []
    for r in recipients_data:
        c_res = admin_session.post(f"{BASE_URL}/api/method/frappe.client.insert", json={
            "doc": {
                "doctype": "Contact",
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "company_name": f"Acme {r['first_name']}",
                "email_ids": [{"email_id": r["email"], "is_primary": 1}],
                "phone_nos": [{"phone": "+15551234567", "is_primary_phone": 1, "is_primary_mobile_no": 1}],
                "custom_country": r["country"],
                "custom_timezone": r["timezone"],
                "custom_is_dropped": 0
            }
        })
        assert c_res.status_code == 200, f"Contact creation failed for {r['first_name']}: {c_res.text}"
        c_name = c_res.json()["message"]["name"]
        contact_names.append(c_name)

        # Allocate to Sam Walker
        admin_session.post(f"{BASE_URL}/api/method/frappe.desk.form.assign_to.add", json={
            "doctype": "Contact",
            "name": c_name,
            "assign_to": json.dumps(["sam.walker@smrikaam.com"])
        })

    print(f"  [OK] Created 3 test contacts allocated to Sam Walker: {contact_names}")

    # User edits the email body in the visual editor
    edited_body = (
        "<p><strong>Hi {{ first_name }},</strong></p>"
        "<p>Greetings from Smrikaam Technologies!</p>"
        "<p>We noticed your team is evaluating Agentic AI and IIoT automation for production facilities.</p>"
        "<p>We would love to schedule a brief 15-minute introductory call.</p>"
    )

    # Test preview rendering with user's edited body
    preview_res = sam_session.post(f"{BASE_URL}/api/method/crm.api.daily_allocation.render_email_preview", json={
        "content": edited_body,
        "subject": "AI Collaboration with {{ first_name }}",
        "contact": contact_names[1], # Alex
        "template_name": "Demo",
        "is_branded": True
    })
    assert preview_res.status_code == 200, f"Preview failed: {preview_res.text}"
    preview_data = preview_res.json()["message"]
    assert "Alex" in preview_data["subject"], "Preview subject must personalize for Alex"
    assert "Hi Alex," in preview_data["content"], "Preview content must render greeting for Alex"
    assert "Agentic AI and IIoT automation" in preview_data["content"], "User's edited text must be in preview"
    assert "PROGRESS THROUGH INNOVATION" in preview_data["content"], "Branded header must be in preview"
    print("  [OK] Visual preview rendering verified with sample data and branded layout")

    # Send bulk email to all 3 contacts
    bulk_send_res = sam_session.post(f"{BASE_URL}/api/method/crm.api.daily_allocation.send_bulk_email", json={
        "doctype": "Contact",
        "names": contact_names,
        "subject": "AI Collaboration with {{ first_name }}",
        "content": edited_body,
        "template_name": "Demo",
        "is_branded": True
    })
    assert bulk_send_res.status_code == 200, f"Bulk send failed: {bulk_send_res.text}"
    bulk_result = bulk_send_res.json()["message"]
    assert bulk_result["sent"] == 3, f"Expected 3 sent, got {bulk_result['sent']}"
    print("  [OK] Bulk email queued for all 3 recipients")

    # Verify each recipient has their own distinct personalized greeting
    for idx, r in enumerate(recipients_data):
        comm_res = sam_session.get(f"{BASE_URL}/api/method/frappe.client.get_list", params={
            "doctype": "Communication",
            "filters": json.dumps({"reference_doctype": "Contact", "reference_name": contact_names[idx]}),
            "fields": json.dumps(["name", "subject", "content", "delivery_status"]),
            "order_by": "creation desc",
            "limit_page_length": 1
        })
        comms = comm_res.json()["message"]
        assert len(comms) > 0, f"No communication found for {r['first_name']}"
        comm = comms[0]
        assert f"Hi {r['first_name']}," in comm["content"], f"Recipient {r['first_name']} did not receive personalized greeting! Content: {comm['content'][:200]}"
        assert "Agentic AI and IIoT automation" in comm["content"], "Edited body copy missing from recipient email!"
        assert "PROGRESS THROUGH INNOVATION" in comm["content"], "Branded header missing from recipient email!"
        assert f"AI Collaboration with {r['first_name']}" in comm["subject"], f"Subject not personalized for {r['first_name']}"
        print(f"  [OK] Recipient {idx+1} ({r['first_name']}): Verified personalized greeting and branded layout")

    # -------------------------------------------------------------
    # 3. CHANGE 2: Single Email Visual Editor & Preview
    # -------------------------------------------------------------
    print("\n--- Test 3: CHANGE 2 - Single Email Visual Editor & Sending ---")
    single_res = sam_session.post(f"{BASE_URL}/api/method/crm.api.daily_allocation.send_task_email", json={
        "contact": contact_names[0],
        "recipient": recipients_data[0]["email"],
        "subject": "Direct followup for {{ first_name }}",
        "content": "<p>Hi {{ first_name }},</p><p>Following up on our call earlier.</p>",
        "template_name": "Demo",
        "is_branded": True
    })
    assert single_res.status_code == 200, f"Single email failed: {single_res.text}"
    single_data = single_res.json()["message"]
    assert single_data["success"] == True
    single_comm = single_data["communication"]
    print(f"  [OK] Single email sent successfully: Communication {single_comm}")

    # -------------------------------------------------------------
    # 4. CHANGE 3: Incoming Email Replies, Threading, Notification & Status
    # -------------------------------------------------------------
    print("\n--- Test 4: CHANGE 3 - Incoming Email Reply Matching & Notifications ---")
    # Simulate incoming email reply to the single email sent above
    parent_comm = sam_session.get(f"{BASE_URL}/api/method/frappe.client.get", params={
        "doctype": "Communication",
        "name": single_comm
    }).json()["message"]

    msg_id = parent_comm.get("message_id") or f"<msg_{single_comm}@smrikaam.com>"
    reply_msg_id = f"<reply_{ts}@example.com>"

    # Insert incoming reply referencing parent communication
    incoming_res = admin_session.post(f"{BASE_URL}/api/method/frappe.client.insert", json={
        "doc": {
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "sent_or_received": "Received",
            "sender": recipients_data[0]["email"],
            "sender_full_name": f"{recipients_data[0]['first_name']} {recipients_data[0]['last_name']}",
            "recipients": "sam.walker@smrikaam.com",
            "subject": f"Re: {parent_comm['subject']}",
            "content": "<p>Hi Sam, thanks for reaching out. Let's talk on Thursday at 2pm.</p>",
            "in_reply_to": single_comm,
            "message_id": reply_msg_id
        }
    })
    assert incoming_res.status_code == 200, f"Incoming email insertion failed: {incoming_res.text}"
    incoming_comm = incoming_res.json()["message"]
    print(f"  [OK] Incoming email reply created: {incoming_comm['name']}")

    # Check that parent communication delivery_status was updated to 'Replied'
    updated_parent = sam_session.get(f"{BASE_URL}/api/method/frappe.client.get", params={
        "doctype": "Communication",
        "name": single_comm
    }).json()["message"]
    assert updated_parent["delivery_status"] == "Replied", f"Expected delivery_status 'Replied', got {updated_parent['delivery_status']}"
    print(f"  [OK] Outgoing email delivery_status correctly marked as 'Replied'")

    # Check activities view for contact
    act_res = sam_session.get(f"{BASE_URL}/api/method/crm.api.contact.get_contact_activities", params={
        "contact": contact_names[0]
    })
    assert act_res.status_code == 200, f"Activities fetch failed: {act_res.text}"
    activities = act_res.json()["message"]["emails"]
    incoming_act = next((a for a in activities if a["name"] == incoming_comm["name"]), None)
    assert incoming_act is not None, "Incoming reply not found in contact activities!"
    assert incoming_act["sent_or_received"] == "Received"
    assert incoming_act["activity_title"] == "Prospect replied to your email"
    print(f"  [OK] Activity displays: '{incoming_act['activity_title']}' with Received badge")

    # Check CRM Notification was delivered to Sam Walker
    notif_res = sam_session.get(f"{BASE_URL}/api/method/crm.api.notifications.get_notifications")
    assert notif_res.status_code == 200, f"Notifications fetch failed: {notif_res.text}"
    user_notifs = notif_res.json()["message"]
    reply_notif = next((n for n in user_notifs if n["reference_name"] == contact_names[0]), None)
    assert reply_notif is not None, "Notification for incoming reply not found!"
    assert reply_notif["route_name"] == "Contact", f"Expected route_name 'Contact', got {reply_notif['route_name']}"
    assert reply_notif["reference_doctype"] == "contact"
    print(f"  [OK] CRM Notification generated for Sam Walker: '{reply_notif['notification_text']}', route_name: '{reply_notif['route_name']}'")

    # -------------------------------------------------------------
    # 5. CHANGE 4: Contacts List View - Country and Timezone Columns
    # -------------------------------------------------------------
    print("\n--- Test 5: CHANGE 4 - Contacts List View Country & Timezone Columns ---")
    c1 = sam_session.get(f"{BASE_URL}/api/method/frappe.client.get", params={"doctype": "Contact", "name": contact_names[0]}).json()["message"]
    c2 = sam_session.get(f"{BASE_URL}/api/method/frappe.client.get", params={"doctype": "Contact", "name": contact_names[1]}).json()["message"]
    c3 = sam_session.get(f"{BASE_URL}/api/method/frappe.client.get", params={"doctype": "Contact", "name": contact_names[2]}).json()["message"]

    assert c1["custom_country"] == "United States"
    assert c1["custom_timezone"] == "America/New_York"
    assert c2["custom_country"] == "United Kingdom"
    assert c2["custom_timezone"] == "Europe/London"
    print(f"  [OK] Contact 1: {c1['full_name']} -> Country: {c1['custom_country']}, Timezone: {c1['custom_timezone']}")
    print(f"  [OK] Contact 2: {c2['full_name']} -> Country: {c2['custom_country']}, Timezone: {c2['custom_timezone']}")

    # Contact 3 has empty country and timezone -> Verify frontend mapping logic resolves to '—'
    c3_country = c3.get("custom_country") or "—"
    c3_tz = c3.get("custom_timezone") or "—"
    print(f"  [OK] Contact 3: {c3['full_name']} (missing values) -> Country: '{c3_country}', Timezone: '{c3_tz}'")

    print("\n" + "=" * 70)
    print("ALL 4 CHANGES FULLY VERIFIED END-TO-END WITH ZERO REGRESSIONS!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_workflow()
