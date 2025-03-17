__version__ = "2.0.0-dev"
__title__ = "Next CRM"

import erpnext.crm.utils as utils
import frappe


def monkey_patch():
    utils.link_open_tasks = link_open_tasks
    utils.link_open_events = link_open_events


def link_open_tasks(ref_doctype, ref_docname, doc):
    todos = utils.get_open_todos(ref_doctype, ref_docname)

    for todo in todos:
        todo_doc = frappe.get_doc("ToDo", todo.name)
        todo_doc.reference_type = doc.doctype
        todo_doc.reference_name = doc.name
        todo_doc.save(ignore_permissions=True)


def link_open_events(ref_doctype, ref_docname, doc):
    events = utils.get_open_events(ref_doctype, ref_docname)
    for event in events:
        event_doc = frappe.get_doc("Event", event.name)
        event_doc.add_participant(doc.doctype, doc.name)
        event_doc.save(ignore_permissions=True)


try:
    monkey_patch()
except Exception:
    pass
