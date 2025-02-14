import frappe

def get_attachments(doctype, name):
    """Get attachments for a document"""
    return frappe.db.get_all(
        "File",
        filters={"attached_to_doctype": doctype, "attached_to_name": name},
        fields=["name", "file_name", "file_type", "file_url", "file_size", "is_private", "creation", "owner"],
    ) or []

def get_communication_medium(communication):
    """Get communication medium with fallback"""
    medium = getattr(communication, 'communication_medium', None)
    
    if not medium:
        if getattr(communication, 'phone_no', None):
            medium = 'Phone'
        elif getattr(communication, 'reference_doctype', None) == 'WhatsApp Message':
            medium = 'Chat'
            
    return medium

def prepare_communication_activity(communication, is_lead=True):
    """Prepare communication activity object with proper medium handling"""
    return {
        "activity_type": "communication",
        "communication_type": communication.communication_type,
        "communication_medium": get_communication_medium(communication),
        "creation": communication.creation,
        "data": {
            "subject": communication.subject,
            "content": communication.content,
            "sender_full_name": communication.sender_full_name,
            "sender": communication.sender,
            "recipients": communication.recipients,
            "cc": communication.cc,
            "bcc": communication.bcc,
            "attachments": get_attachments('Communication', communication.name),
            "read_by_recipient": communication.read_by_recipient,
            "delivery_status": communication.delivery_status
        },
        "is_lead": is_lead,
    } 