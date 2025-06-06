import frappe
import email
from email import policy
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def create_communication_from_eml(file_url: str, reference_name: str, reference_doctype: str) -> dict:
    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_content = file_doc.get_content()
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')

        msg = email.message_from_bytes(file_content, policy=policy.default)
        comm = frappe.new_doc("Communication")
        email_body = _extract_email_body(msg)
        
        comm.update({
            "subject": msg["subject"] or "No Subject",
            "communication_medium": "Email",
            "content": email_body,
            "sender": msg["from"] or "",
            "recipients": msg["to"] or "",
            "communication_date": email.utils.parsedate_to_datetime(msg["date"]).replace(tzinfo=None) if msg["date"] else frappe.utils.now_datetime(),
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "timeline_links": [{
                "link_doctype": reference_doctype,
                "link_name": reference_name
            }]
        })
        comm.insert(ignore_permissions=True)

        _save_attachments(msg, comm.name)
        return {"success": True, "communication": comm.name}
    except Exception as e:
        frappe.log_error(f"Failed to create communication from EML: {str(e)}")
        return {"success": False, "error": str(e)}

def _extract_email_body(msg):
    if body_part := msg.get_body(preferencelist=("html", "plain")):
        try:
            return body_part.get_content()
        except:
            pass
    
    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type in ["text/plain", "text/html"]:
            try:
                return part.get_payload(decode=True).decode('utf-8', errors='replace')
            except:
                continue
    return ""

def _save_attachments(msg, comm_name):
    for part in msg.iter_attachments():
        if file_name := part.get_filename():
            try:
                attachment_data = part.get_payload(decode=True)
                if isinstance(attachment_data, str):
                    attachment_data = attachment_data.encode('utf-8')
                save_file(
                    file_name,
                    attachment_data,
                    "Communication",
                    comm_name,
                    "Home/Attachments"
                )
            except Exception as e:
                frappe.log_error(f"Failed to save attachment {file_name}: {str(e)}")