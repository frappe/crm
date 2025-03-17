import json

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.form.load import get_docinfo


@frappe.whitelist()
def get_activities(name):
    if frappe.db.exists("Opportunity", name):
        return get_opportunity_activities(name)
    elif frappe.db.exists("Lead", name):
        return get_lead_activities(name)
    else:
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)


def get_opportunity_activities(name):
    get_docinfo("", "Opportunity", name)
    docinfo = frappe.response["docinfo"]
    opportunity_meta = frappe.get_meta("Opportunity")
    opportunity_fields = {
        field.fieldname: {"label": field.label, "options": field.options}
        for field in opportunity_meta.fields
    }
    avoid_fields = [
        "party_name",
        "lead",
        "response_by",
        "sla_creation",
        "sla",
        "first_response_time",
        "first_responded_on",
    ]

    doc = frappe.db.get_values(
        "Opportunity", name, ["creation", "owner", "opportunity_from", "party_name"]
    )[0]
    opportunity_from = doc[2]

    activities = []
    calls = []
    notes = []
    todos = []
    events = []
    attachments = []
    creation_text = "created this opportunity"

    if opportunity_from == "Lead":
        lead = doc[3]
        activities, calls, notes, todos, events, attachments = get_lead_activities(
            lead, False
        )
        creation_text = "converted the lead to this opportunity"

    activities.append(
        {
            "activity_type": "creation",
            "creation": doc[0],
            "owner": doc[1],
            "data": creation_text,
            "is_lead": False,
        }
    )

    docinfo.versions.reverse()

    for version in docinfo.versions:
        data = json.loads(version.data)
        if not data.get("changed"):
            continue

        if change := data.get("changed")[0]:
            field = opportunity_fields.get(change[0], None)

            if (
                not field
                or change[0] in avoid_fields
                or (not change[1] and not change[2])
            ):
                continue

            field_label = field.get("label") or change[0]
            field_option = field.get("options") or None

            activity_type = "changed"
            data = {
                "field": change[0],
                "field_label": field_label,
                "old_value": change[1],
                "value": change[2],
            }

            if not change[1] and change[2]:
                activity_type = "added"
                data = {
                    "field": change[0],
                    "field_label": field_label,
                    "value": change[2],
                }
            elif change[1] and not change[2]:
                activity_type = "removed"
                data = {
                    "field": change[0],
                    "field_label": field_label,
                    "value": change[1],
                }

        activity = {
            "activity_type": activity_type,
            "creation": version.creation,
            "owner": version.owner,
            "data": data,
            "is_lead": False,
            "options": field_option,
        }
        activities.append(activity)

    for comment in docinfo.comments:
        activity = {
            "name": comment.name,
            "activity_type": "comment",
            "creation": comment.creation,
            "owner": comment.owner,
            "content": comment.content,
            "attachments": get_attachments("Comment", comment.name),
            "is_lead": False,
        }
        activities.append(activity)

    for communication in docinfo.communications + docinfo.automated_messages:
        activity = {
            "activity_type": "communication",
            "communication_type": communication.communication_type,
            "creation": communication.creation,
            "data": {
                "subject": communication.subject,
                "content": communication.content,
                "sender_full_name": communication.sender_full_name,
                "sender": communication.sender,
                "recipients": communication.recipients,
                "cc": communication.cc,
                "bcc": communication.bcc,
                "attachments": get_attachments("Communication", communication.name),
                "read_by_recipient": communication.read_by_recipient,
                "delivery_status": communication.delivery_status,
            },
            "is_lead": False,
        }
        activities.append(activity)

    if "frappe_gmail_thread" in frappe.get_installed_apps():
        from frappe_gmail_thread.api.activity import get_linked_gmail_threads

        threads = get_linked_gmail_threads("Opportunity", name)

        for thread in threads:
            activity = {
                "activity_type": "communication",
                "communication_type": "Email",
                "creation": thread["template_data"]["doc"]["creation"],
                "data": {
                    "subject": thread["template_data"]["doc"]["subject"],
                    "content": thread["template_data"]["doc"]["content"],
                    "sender_full_name": thread["template_data"]["doc"][
                        "sender_full_name"
                    ],
                    "sender": thread["template_data"]["doc"]["sender"],
                    "recipients": thread["template_data"]["doc"]["recipients"],
                    "cc": thread["template_data"]["doc"]["cc"],
                    "bcc": thread["template_data"]["doc"]["bcc"],
                    "attachments": thread["template_data"]["doc"]["attachments"],
                    "read_by_recipient": thread["template_data"]["doc"][
                        "read_by_recipient"
                    ],
                    "delivery_status": thread["template_data"]["doc"][
                        "delivery_status"
                    ],
                },
                "is_lead": False,
            }
            activities.append(activity)

    for attachment_log in docinfo.attachment_logs:
        activity = {
            "name": attachment_log.name,
            "activity_type": "attachment_log",
            "creation": attachment_log.creation,
            "owner": attachment_log.owner,
            "data": parse_attachment_log(
                attachment_log.content, attachment_log.comment_type
            ),
            "is_lead": False,
        }
        activities.append(activity)

    calls = calls + get_linked_calls(name)
    notes = notes + get_linked_notes(name)
    todos = todos + get_linked_todos(name)
    events = events + get_linked_events(name)
    attachments = attachments + get_attachments("Opportunity", name)

    activities.sort(key=lambda x: x["creation"], reverse=True)
    activities = handle_multiple_versions(activities)

    return activities, calls, notes, todos, events, attachments


def get_lead_activities(name, get_events=True):
    get_docinfo("", "Lead", name)
    docinfo = frappe.response["docinfo"]
    lead_meta = frappe.get_meta("Lead")
    lead_fields = {
        field.fieldname: {"label": field.label, "options": field.options}
        for field in lead_meta.fields
    }
    avoid_fields = [
        "converted",
        "response_by",
        "sla_creation",
        "sla",
        "first_response_time",
        "first_responded_on",
    ]

    doc = frappe.db.get_values("Lead", name, ["creation", "owner"])[0]
    activities = [
        {
            "activity_type": "creation",
            "creation": doc[0],
            "owner": doc[1],
            "data": "created this lead",
            "is_lead": True,
        }
    ]

    docinfo.versions.reverse()

    for version in docinfo.versions:
        data = json.loads(version.data)
        if not data.get("changed"):
            continue

        if change := data.get("changed")[0]:
            field = lead_fields.get(change[0], None)

            if (
                not field
                or change[0] in avoid_fields
                or (not change[1] and not change[2])
            ):
                continue

            field_label = field.get("label") or change[0]
            field_option = field.get("options") or None

            activity_type = "changed"
            data = {
                "field": change[0],
                "field_label": field_label,
                "old_value": change[1],
                "value": change[2],
            }

            if not change[1] and change[2]:
                activity_type = "added"
                data = {
                    "field": change[0],
                    "field_label": field_label,
                    "value": change[2],
                }
            elif change[1] and not change[2]:
                activity_type = "removed"
                data = {
                    "field": change[0],
                    "field_label": field_label,
                    "value": change[1],
                }

        activity = {
            "activity_type": activity_type,
            "creation": version.creation,
            "owner": version.owner,
            "data": data,
            "is_lead": True,
            "options": field_option,
        }
        activities.append(activity)

    for comment in docinfo.comments:
        activity = {
            "name": comment.name,
            "activity_type": "comment",
            "creation": comment.creation,
            "owner": comment.owner,
            "content": comment.content,
            "attachments": get_attachments("Comment", comment.name),
            "is_lead": True,
        }
        activities.append(activity)

    for communication in docinfo.communications + docinfo.automated_messages:
        if communication.get("communication_medium") == "Event" and not get_events:
            continue
        activity = {
            "activity_type": "communication",
            "communication_type": communication.communication_type,
            "creation": communication.creation,
            "data": {
                "subject": communication.subject,
                "content": communication.content,
                "sender_full_name": communication.sender_full_name,
                "sender": communication.sender,
                "recipients": communication.recipients,
                "cc": communication.cc,
                "bcc": communication.bcc,
                "attachments": get_attachments("Communication", communication.name),
                "read_by_recipient": communication.read_by_recipient,
                "delivery_status": communication.delivery_status,
            },
            "is_lead": True,
        }
        activities.append(activity)

    if "frappe_gmail_thread" in frappe.get_installed_apps():
        from frappe_gmail_thread.api.activity import get_linked_gmail_threads

        threads = get_linked_gmail_threads("Lead", name)

        for thread in threads:
            activity = {
                "activity_type": "communication",
                "communication_type": "Email",
                "creation": thread["template_data"]["doc"]["creation"],
                "data": {
                    "subject": thread["template_data"]["doc"]["subject"],
                    "content": thread["template_data"]["doc"]["content"],
                    "sender_full_name": thread["template_data"]["doc"][
                        "sender_full_name"
                    ],
                    "sender": thread["template_data"]["doc"]["sender"],
                    "recipients": thread["template_data"]["doc"]["recipients"],
                    "cc": thread["template_data"]["doc"]["cc"],
                    "bcc": thread["template_data"]["doc"]["bcc"],
                    "attachments": thread["template_data"]["doc"]["attachments"],
                    "read_by_recipient": thread["template_data"]["doc"][
                        "read_by_recipient"
                    ],
                    "delivery_status": thread["template_data"]["doc"][
                        "delivery_status"
                    ],
                },
                "is_lead": True,
            }
            activities.append(activity)

    for attachment_log in docinfo.attachment_logs:
        activity = {
            "name": attachment_log.name,
            "activity_type": "attachment_log",
            "creation": attachment_log.creation,
            "owner": attachment_log.owner,
            "data": parse_attachment_log(
                attachment_log.content, attachment_log.comment_type
            ),
            "is_lead": True,
        }
        activities.append(activity)

    calls = get_linked_calls(name)
    notes = get_linked_notes(name)
    todos = get_linked_todos(name)
    events = get_linked_events(name)
    attachments = get_attachments("Lead", name)

    activities.sort(key=lambda x: x["creation"], reverse=True)
    activities = handle_multiple_versions(activities)

    return activities, calls, notes, todos, events, attachments


def get_attachments(doctype, name):
    return (
        frappe.db.get_all(
            "File",
            filters={"attached_to_doctype": doctype, "attached_to_name": name},
            fields=[
                "name",
                "file_name",
                "file_type",
                "file_url",
                "file_size",
                "is_private",
                "creation",
                "owner",
            ],
        )
        or []
    )


def handle_multiple_versions(versions):
    activities = []
    grouped_versions = []
    old_version = None
    for version in versions:
        is_version = version["activity_type"] in ["changed", "added", "removed"]
        if not is_version:
            activities.append(version)
        if not old_version:
            old_version = version
            if is_version:
                grouped_versions.append(version)
            continue
        if (
            is_version
            and old_version.get("owner")
            and version["owner"] == old_version["owner"]
        ):
            grouped_versions.append(version)
        else:
            if grouped_versions:
                activities.append(parse_grouped_versions(grouped_versions))
            grouped_versions = []
            if is_version:
                grouped_versions.append(version)
        old_version = version
        if version == versions[-1] and grouped_versions:
            activities.append(parse_grouped_versions(grouped_versions))

    return activities


def parse_grouped_versions(versions):
    version = versions[0]
    if len(versions) == 1:
        return version
    other_versions = versions[1:]
    version["other_versions"] = other_versions
    return version


def get_linked_calls(name):
    calls = frappe.db.get_all(
        "CRM Call Log",
        filters={"reference_docname": name},
        fields=[
            "name",
            "caller",
            "receiver",
            "from",
            "to",
            "duration",
            "start_time",
            "end_time",
            "status",
            "type",
            "recording_url",
            "creation",
            "note",
        ],
    )
    return calls or []


def get_linked_notes(name):
    notes = frappe.db.get_all(
        "CRM Note",
        filters={"parent": name},
        fields=["name", "custom_title", "note", "owner", "modified"],
    )
    return notes or []


def get_linked_todos(name):
    todos = frappe.db.get_list(
        "ToDo",
        filters={"reference_name": name},
        fields=[
            "name",
            "custom_title",
            "description",
            "allocated_to",
            "date",
            "priority",
            "status",
            "modified",
        ],
    )
    return todos or []


def get_linked_events(name):
    events = frappe.db.get_list(
        "Event",
        filters=[["Event Participants", "reference_docname", "=", name]],
        fields=[
            "name",
            "subject",
            "description",
            "_assign",
            "starts_on",
            "ends_on",
            "event_category",
            "status",
            "event_type",
            "modified",
        ],
    )

    return events or []


def parse_attachment_log(html, type):
    soup = BeautifulSoup(html, "html.parser")
    a_tag = soup.find("a")
    type = "added" if type == "Attachment" else "removed"
    if not a_tag:
        return {
            "type": type,
            "file_name": html.replace("Removed ", ""),
            "file_url": "",
            "is_private": False,
        }

    is_private = False
    if "private/files" in a_tag["href"]:
        is_private = True

    return {
        "type": type,
        "file_name": a_tag.text,
        "file_url": a_tag["href"],
        "is_private": is_private,
    }
