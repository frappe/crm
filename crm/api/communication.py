import frappe
from frappe import _
import re
import email.header

def clean_display_name(address):
    """Extract and decode display name from MIME-encoded string"""
    if not address:
        return ""
        
    # If in format "Name <email@domain.com>", extract name part
    name_match = re.match(r'([^<]*)<[^>]+>', address)
    if name_match:
        name = name_match.group(1).strip()
        if name.startswith('=?'):
            try:
                decoded_parts = email.header.decode_header(name)
                decoded_name = ""
                for part, charset in decoded_parts:
                    if isinstance(part, bytes):
                        decoded_name += part.decode(charset or 'utf-8')
                    else:
                        decoded_name += part
                return decoded_name.strip()
            except:
                return name
        return name
        
    # If MIME-encoded without email
    if address.startswith('=?'):
        try:
            decoded_parts = email.header.decode_header(address)
            decoded_name = ""
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    decoded_name += part.decode(charset or 'utf-8')
                else:
                    decoded_name += part
            return decoded_name.strip()
        except:
            return address
            
    return address

def clean_email_address(address):
    """Extract clean email address from MIME-encoded string"""
    if not address:
        return ""
        
    try:
        # First try to decode if it's MIME encoded
        if "=?" in address:
            decoded_parts = email.header.decode_header(address)
            decoded_text = ""
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    decoded_text += part.decode(charset or 'utf-8')
                else:
                    decoded_text += part
            address = decoded_text
            
        # Extract email from "Name <email@domain.com>" format
        email_match = re.search(r'<([^>]+)>', address)
        if email_match:
            return email_match.group(1).lower()
            
        # If no angle brackets, try to extract email directly
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', address)
        if email_match:
            return email_match.group(0).lower()
            
        return ""
        
    except Exception as e:
        frappe.logger().error(f"Error cleaning email address '{address}': {str(e)}")
        # If decoding fails, try to extract email directly
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', address)
        if email_match:
            return email_match.group(0).lower()
        return ""

def init_for_execute():
    """Initialize session for bench execute"""
    if not frappe.db:
        frappe.connect()
    if not frappe.session:
        frappe.set_user("Administrator")

def column_exists(doctype, column):
    """Check if column exists in table"""
    return frappe.db.sql(
        """SELECT COUNT(*)
        FROM information_schema.COLUMNS 
        WHERE TABLE_NAME = 'tab{doctype}'
        AND COLUMN_NAME = '{column}'""".format(
            doctype=doctype,
            column=column
        )
    )[0][0] > 0

def create_indices():
    """Create necessary indices for better query performance"""
    indices = [
        {
            "doctype": "Communication",
            "fields": ["communication_medium", "communication_type", "reference_doctype", "reference_name", "sender", "recipients"]
        },
        {
            "doctype": "CRM Lead",
            "fields": ["email"]
        },
        {
            "doctype": "CRM Deal",
            "fields": ["email"]
        }
    ]
    
    for index in indices:
        doctype = index["doctype"]
        for field in index["fields"]:
            # Check if column exists
            if not column_exists(doctype, field):
                frappe.logger().warning(f"Column {field} does not exist in {doctype}, skipping index creation")
                continue
                
            # Get existing indices
            existing_indices = frappe.db.sql(
                """SHOW INDEX FROM `tab{doctype}`
                WHERE Column_name='{field}'""".format(
                    doctype=doctype,
                    field=field
                ), as_dict=1
            )
            
            if not existing_indices:
                # Create index if it doesn't exist
                frappe.db.sql(
                    """ALTER TABLE `tab{doctype}`
                    ADD INDEX `idx_{field}` (`{field}`)""".format(
                        doctype=doctype,
                        field=field
                    )
                )
                frappe.db.commit()
                frappe.logger().info(f"Created index on {doctype}.{field}")

@frappe.whitelist()
def track_communication():
    """Create a communication record for phone/whatsapp tracking, ignoring standard permissions"""
    try:
        doc = frappe.get_doc(frappe.parse_json(frappe.form_dict.get("doc")))
        doc.insert(ignore_permissions=True)
        return doc
    except Exception as e:
        frappe.log_error("Error in track_communication", str(e))
        frappe.throw(_("Could not track communication: {0}").format(str(e)))

def update_email_references():
    """Find emails without references and link them to leads/deals based on email addresses"""
    try:
        # Get all emails without references
        emails_without_refs = frappe.get_all(
            "Communication",
            filters={
                "communication_medium": "Email",
                "communication_type": "Communication",
                "reference_doctype": ["in", ["", None]],
                "reference_name": ["in", ["", None]]
            },
            fields=["name", "sender", "recipients", "cc", "bcc", "sender_full_name"]
        )

        processed = 0
        linked = 0
        not_found = 0
        cleaning_errors = 0

        for email in emails_without_refs:
            processed += 1
            # Collect all email addresses from the communication
            email_addresses = set()
            updates = {}
            
            if email.sender:
                clean_sender = clean_email_address(email.sender)
                if clean_sender:
                    email_addresses.add(clean_sender)
                    # Update sender name if it's MIME-encoded
                    if "=?" in email.sender:
                        display_name = clean_display_name(email.sender)
                        if display_name:
                            updates["sender_full_name"] = display_name
                        updates["sender"] = clean_sender

            if email.recipients:
                clean_recipients = []
                for recipient in email.recipients.split(","):
                    recipient = recipient.strip()
                    try:
                        clean_recipient = clean_email_address(recipient)
                        if clean_recipient:
                            email_addresses.add(clean_recipient)
                            if "=?" in recipient:
                                display_name = clean_display_name(recipient)
                                if display_name:
                                    clean_recipients.append(f"{display_name} <{clean_recipient}>")
                                else:
                                    clean_recipients.append(clean_recipient)
                            else:
                                clean_recipients.append(recipient)
                    except Exception as e:
                        cleaning_errors += 1
                        frappe.logger().error(f"Error cleaning recipient '{recipient}' in email {email.name}: {str(e)}")
                        # Keep original if cleaning fails
                        clean_recipients.append(recipient)
                        
                if clean_recipients:
                    updates["recipients"] = ", ".join(clean_recipients)

            if email.cc:
                clean_ccs = []
                for cc in email.cc.split(","):
                    cc = cc.strip()
                    clean_cc = clean_email_address(cc)
                    if clean_cc:
                        email_addresses.add(clean_cc)
                        if "=?" in cc:
                            display_name = clean_display_name(cc)
                            if display_name:
                                clean_ccs.append(f"{display_name} <{clean_cc}>")
                            else:
                                clean_ccs.append(clean_cc)
                        else:
                            clean_ccs.append(cc)
                if clean_ccs:
                    updates["cc"] = ", ".join(clean_ccs)

            if email.bcc:
                clean_bccs = []
                for bcc in email.bcc.split(","):
                    bcc = bcc.strip()
                    clean_bcc = clean_email_address(bcc)
                    if clean_bcc:
                        email_addresses.add(clean_bcc)
                        if "=?" in bcc:
                            display_name = clean_display_name(bcc)
                            if display_name:
                                clean_bccs.append(f"{display_name} <{clean_bcc}>")
                            else:
                                clean_bccs.append(clean_bcc)
                        else:
                            clean_bccs.append(bcc)
                if clean_bccs:
                    updates["bcc"] = ", ".join(clean_bccs)

            if not email_addresses:
                continue

            # Update communication fields if needed
            if updates:
                frappe.db.set_value("Communication", email.name, updates, update_modified=False)

            # Search for leads with matching emails
            leads = frappe.get_all(
                "CRM Lead",
                filters={"email": ["in", list(email_addresses)]},
                fields=["name", "email"]
            )

            # Search for deals with matching emails
            deals = frappe.get_all(
                "CRM Deal",
                filters={"email": ["in", list(email_addresses)]},
                fields=["name", "email"]
            )

            # Priority given to deals over leads if both found
            if deals:
                deal = deals[0]
                frappe.db.set_value(
                    "Communication",
                    email.name,
                    {
                        "reference_doctype": "CRM Deal",
                        "reference_name": deal.name
                    },
                    update_modified=False
                )
                linked += 1
            elif leads:
                lead = leads[0]
                frappe.db.set_value(
                    "Communication",
                    email.name,
                    {
                        "reference_doctype": "CRM Lead",
                        "reference_name": lead.name
                    },
                    update_modified=False
                )
                linked += 1
            else:
                not_found += 1

        # Log summary with more details
        frappe.logger().info(
            f"Email reference update completed:\n"
            f"- Processed: {processed}\n"
            f"- Linked: {linked}\n"
            f"- Not found: {not_found}\n"
            f"- Cleaning errors: {cleaning_errors}"
        )

    except Exception as e:
        frappe.logger().error(f"Error in update_email_references: {str(e)}")
        raise

@frappe.whitelist()
def fix_email_references():
    """Endpoint to manually trigger email reference update"""
    try:
        # Initialize session only if needed (for bench execute)
        if not frappe.session or not frappe.session.user:
            init_for_execute()
        
        # Check permissions
        if not frappe.has_permission("Communication", "write"):
            frappe.throw(_("Not permitted to update email references"), frappe.PermissionError)
        
        # Ensure indices exist
        create_indices()
        
        # Run update directly
        update_email_references()
        
        frappe.msgprint(_("Email references update completed successfully"))
        return "Email reference update completed"
    except Exception as e:
        frappe.log_error("Error in fix_email_references", str(e))
        frappe.throw(_("Failed to update email references: {0}").format(str(e))) 