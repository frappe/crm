import frappe
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def add_attachments_on_note(note, attachments):
    if note and not isinstance(note, dict):
        note = note.as_dict()
    if attachments:  
        attachments= {r['file_name']: r for r in attachments}.values()

    if frappe.db.exists("FCRM Note", note.get('name')):
        doc = frappe.get_doc("FCRM Note", note.get('name'))
        if note.get('title') != doc.get('title'):
            doc.update({"title": note.get('title')})
        if note.get('content') != doc.get('content'):
            doc.update({"content": note.get('content')})

        if len(attachments) > 0:
            #check file attach is exist in doc if not then add
            for attach in attachments:
                if 'name' in attach and attach.get('file_url') not in [row.get('file_url') for row in doc.attachments]:
                    row = doc.append("attachments", {})
                    row.file_url = attach.get('file_url')
        elif len(attachments) == 0:
            frappe.db.sql(f"""DELETE FROM `tabCRM Note Attachments` 
                             WHERE parent = "{note.get('name')}"  """)
            frappe.db.commit()
           
        #delete file from doctype if deleted from frontend
        for doc_att in doc.attachments:
            if doc_att.get('file_url') not in [current_att['file_name'] for current_att in attachments]:
                frappe.db.sql(f"""DELETE FROM `tabCRM Note Attachments` 
                         WHERE name = "{doc_att.get('name')}"  """)
                frappe.db.commit()

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
        
    else:
        doc = frappe.new_doc("FCRM Note")
        doc.update({
            "title": note.get('title'),
            "content": note.get('content')
        })
        if len(attachments) > 0:
            for attach in attachments:
                row = doc.append("attachments", {})
                row.file_url = attach.get('file_name')
        
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name


@frappe.whitelist()
def get_attachments_from_note(note_name):
    # Query the database to fetch name and file_url
    attachments = frappe.db.get_all(
        "CRM Note Attachments", 
        filters={'parent': note_name},
        fields=['name', 'file_url'],
        order_by='creation DESC',
        limit=10
    )
    seen_file_urls = set()
    # Transform the result to use `file_name` instead of `name`
    formatted_attachments = [{'file_url': att['name'], 'file_name': att['file_url']} 
                               for att in attachments 
                               if att['file_url'] not in seen_file_urls 
                               and not seen_file_urls.add(att['file_url'])]
    
    # Return the formatted list or an empty list if none found
    return formatted_attachments if formatted_attachments else []
