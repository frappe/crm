import frappe
from frappe import _
from frappe.utils import get_url


INTERNAL_EMAIL_DOMAINS = ["cozycornerpatios.com", "zipcushions.com"]


def extract_customer_email(sender, recipients):
	"""Extract customer email excluding internal domains"""
	all_emails = []
	
	if sender:
		all_emails.append(sender)
	
	if recipients:
		# Recipients can be a string or list
		if isinstance(recipients, str):
			recipient_list = [r.strip() for r in recipients.split(",")]
		else:
			recipient_list = recipients
		all_emails.extend(recipient_list)
	
	# Extract email addresses and filter out internal domains
	customer_emails = []
	for email_str in all_emails:
		# Extract email from format like "Name <email@domain.com>" or just "email@domain.com"
		email = email_str
		if "<" in email_str and ">" in email_str:
			email = email_str.split("<")[1].split(">")[0].strip()
		else:
			email = email_str.strip()
		
		# Check if email domain is internal
		domain = email.split("@")[-1] if "@" in email else ""
		if domain and domain.lower() not in INTERNAL_EMAIL_DOMAINS:
			customer_emails.append(email)
	
	return customer_emails[0] if customer_emails else None


def parse_name_into_first_last(full_name):
	"""Split name into first_name and last_name"""
	if not full_name:
		return "", ""
	
	parts = full_name.strip().split()
	if len(parts) == 0:
		return "", ""
	elif len(parts) == 1:
		return parts[0], ""
	else:
		return parts[0], " ".join(parts[1:])


def create_transfer_notes(source_doc, selected_emails, all_emails):
	"""Generate detailed transfer notes"""
	notes = []
	
	# Source document info
	if source_doc.doctype == "CRM Lead":
		notes.append(f"Transferred from CRM Lead: {source_doc.name}")
		if source_doc.get("first_name") or source_doc.get("last_name"):
			first = source_doc.get('first_name') or ''
			last = source_doc.get('last_name') or ''
			name = f"{first} {last}".strip()
			if name:
				notes.append(f"Lead Name: {name}")
	else:
		notes.append(f"Transferred from HD Ticket: {source_doc.name}")
		if source_doc.get("subject"):
			notes.append(f"Ticket Subject: {source_doc.subject}")
	
	# Email summaries
	if selected_emails:
		notes.append(f"\nTransferred {len(selected_emails)} email(s):")
		for email in selected_emails:
			subject = email.get("subject", "No Subject")
			date = email.get("creation", "")
			notes.append(f"  - {subject} ({date})")
	
	return "\n".join(notes)


def copy_communication(comm_name, target_doctype, target_name):
	"""Duplicate communication with new reference"""
	try:
		original_comm = frappe.get_doc("Communication", comm_name)
		
		# Create new communication and explicitly copy all fields
		# This ensures content and all other fields are properly copied
		new_comm = frappe.new_doc("Communication")
		
		# Copy all important fields explicitly
		new_comm.communication_type = original_comm.communication_type or "Communication"
		new_comm.communication_medium = original_comm.communication_medium or "Email"
		new_comm.subject = original_comm.subject
		new_comm.content = original_comm.content  # CRITICAL: Copy content
		new_comm.text_content = original_comm.text_content  # CRITICAL: Copy text_content
		new_comm.sender = original_comm.sender
		new_comm.sender_full_name = original_comm.sender_full_name
		new_comm.recipients = original_comm.recipients
		new_comm.cc = original_comm.cc or ""
		new_comm.bcc = original_comm.bcc or ""
		new_comm.sent_or_received = original_comm.sent_or_received or "Received"
		new_comm.delivery_status = original_comm.delivery_status
		new_comm.email_status = original_comm.email_status
		new_comm.message_id = original_comm.message_id
		new_comm.in_reply_to = original_comm.in_reply_to
		new_comm.email_account = original_comm.email_account
		new_comm.communication_date = original_comm.communication_date or original_comm.creation
		new_comm.uid = original_comm.uid
		new_comm.user = original_comm.user or frappe.session.user
		
		# Set reference to new ticket - MUST be set before insert
		new_comm.reference_doctype = target_doctype
		new_comm.reference_name = str(target_name)  # Ensure it's a string
		new_comm.status = "Linked"
		
		# Clear any timeline_links that might have been set from original
		new_comm.timeline_links = []
		
		# Set flags and insert
		new_comm.flags.ignore_permissions = True
		new_comm.flags.ignore_mandatory = True
		new_comm.insert(ignore_permissions=True)
		
		# Reload to get actual saved values
		new_comm.reload()
		
		# Double-check reference was saved correctly
		if new_comm.reference_doctype != target_doctype or str(new_comm.reference_name) != str(target_name):
			# Force update if reference is wrong
			frappe.db.set_value(
				"Communication",
				new_comm.name,
				{
					"reference_doctype": target_doctype,
					"reference_name": str(target_name),
					"status": "Linked"
				},
				update_modified=False
			)
			frappe.db.commit()
			new_comm.reload()
		
		# Verify content was copied
		if not (new_comm.content or new_comm.text_content):
			frappe.log_error(
				f"WARNING: Copied comm {new_comm.name} has no content! Original {comm_name} had content={bool(original_comm.content)}",
				"Communication Content Warning"
			)
		
		# Log the actual saved reference for debugging
		frappe.log_error(
			f"Created comm {new_comm.name}: ref_doctype={new_comm.reference_doctype}, ref_name={new_comm.reference_name}, target was {target_doctype}/{target_name}",
			"Communication Reference Debug"
		)
		
		return new_comm.name
	except Exception as e:
		error_msg = f"Error copying communication {comm_name}: {str(e)}\n{frappe.get_traceback()}"
		frappe.log_error(error_msg, "Communication Copy Error")
		raise


@frappe.whitelist()
def get_communications_for_transfer(doctype, name):
	"""Get list of Communication records for transfer"""
	if not frappe.has_permission(doctype, "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	
	communications = frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": doctype,
			"reference_name": name,
			"communication_medium": "Email",
		},
		fields=["name", "subject", "sender", "recipients", "creation", "content"],
		order_by="creation asc",
	)
	
	return communications


@frappe.whitelist()
def transfer_to_helpdesk(lead_name, communication_ids=None, delete_source=True):
	"""Transfer CRM Lead to HD Ticket with selected communications"""
	if not frappe.has_permission("CRM Lead", "read", lead_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	
	try:
		# Fetch CRM Lead
		lead = frappe.get_doc("CRM Lead", lead_name)
		
		# Extract customer information with field fallbacks
		customer_name = ""
		if lead.get("first_name") or lead.get("last_name"):
			first = lead.get('first_name') or ''
			last = lead.get('last_name') or ''
			customer_name = f"{first} {last}".strip()
		if not customer_name:
			customer_name = lead_name
		
		# Email fallback: email -> email_id -> email_account
		customer_email = None
		if lead.get("email"):
			customer_email = lead.email
		elif lead.get("email_id"):
			customer_email = lead.email_id
		elif lead.get("email_account"):
			customer_email = lead.email_account
		
		# Phone fallback: mobile_no -> phone
		customer_phone = None
		if lead.get("mobile_no"):
			customer_phone = lead.mobile_no
		elif lead.get("phone"):
			customer_phone = lead.phone
		
		# Get all communications to extract email if missing
		all_communications = get_communications_for_transfer("CRM Lead", lead_name)
		if not customer_email and all_communications:
			# Try to extract from first communication
			first_comm = all_communications[0]
			customer_email = extract_customer_email(first_comm.get("sender"), first_comm.get("recipients"))
		
		# If still no email, generate a placeholder
		if not customer_email:
			customer_email = f"transferred-{lead_name}@example.com"
		
		# Create or update Contact
		contact_name = None
		try:
			# Check if contact exists with this email
			contact_email = frappe.db.get_value("Contact Email", {"email_id": customer_email}, "parent")
			
			if contact_email:
				contact = frappe.get_doc("Contact", contact_email)
				# Always update name to match Lead's first_name and last_name exactly
				lead_first_name = lead.get('first_name') or ''
				lead_last_name = lead.get('last_name') or ''
				
				# Update Contact to match Lead exactly - clear any existing values first
				contact.first_name = lead_first_name
				contact.last_name = lead_last_name
				contact.middle_name = ''  # Clear middle name to avoid conflicts
				
				contact.save(ignore_permissions=True)
				contact.reload()  # Reload to ensure full_name is updated correctly
				
				# Use contact.name as-is (no renaming - let Frappe handle name generation)
				contact_name = contact.name
			else:
				# Create new contact - use Lead's first_name and last_name directly
				contact = frappe.new_doc("Contact")
				
				# Get Lead's original first and last names
				lead_first_name = lead.get('first_name') or ''
				lead_last_name = lead.get('last_name') or ''
				
				# Set Contact name exactly as Lead has it
				contact.first_name = lead_first_name
				contact.last_name = lead_last_name
				contact.middle_name = ''  # Ensure no middle name
				
				if customer_email:
					contact.append("email_ids", {"email_id": customer_email, "is_primary": 1})
				if customer_phone:
					contact.append("phone_nos", {"phone": customer_phone, "is_primary_mobile_no": 1})
				contact.insert(ignore_permissions=True)
				contact.reload()  # Reload to ensure full_name is set correctly
				contact_name = contact.name
		except Exception as e:
			frappe.log_error(f"Error creating/updating contact: {str(e)}")
			# Continue without contact link
		
		# Get selected communications
		selected_communications = []
		if communication_ids:
			selected_communications = [
				comm for comm in all_communications if comm["name"] in communication_ids
			]
		else:
			selected_communications = all_communications
		
		# Log for debugging (shortened to fit Error Log title limit)
		frappe.log_error(
			f"Transfer: {lead_name}, Found: {len(all_communications)}, Selected: {len(selected_communications)}",
			"Transfer Debug"
		)
		
		# Get latest email subject for ticket subject
		ticket_subject = "Transferred from CRM Lead"
		if selected_communications:
			latest_comm = selected_communications[-1]
			if latest_comm.get("subject"):
				ticket_subject = latest_comm["subject"]
		
		# Create transfer notes
		transfer_notes = create_transfer_notes(lead, selected_communications, all_communications)
		
		# Create HD Ticket
		ticket = frappe.new_doc("HD Ticket")
		ticket.subject = ticket_subject
		ticket.description = transfer_notes
		ticket.raised_by = customer_email
		if contact_name:
			ticket.contact = contact_name
		if customer_phone:
			ticket.contact_number = customer_phone
		ticket.status = "Open"
		ticket.priority = "Medium"
		
		# Copy custom_reply_email_alias if it exists on the Lead
		if lead.get("custom_reply_email_alias"):
			ticket.custom_reply_email_alias = lead.custom_reply_email_alias
		
		ticket.insert(ignore_permissions=True)
		frappe.db.commit()  # Ensure ticket is saved before copying communications
		
		# Copy selected communications
		transferred_count = 0
		if not selected_communications:
			frappe.log_error(f"No communications to transfer from Lead {lead_name}. All comms: {len(all_communications)}", "Transfer Warning")
		else:
			# Store ticket name as string to match query format (HD Ticket names are integers)
			ticket_name_str = str(ticket.name)
			frappe.log_error(f"Copying {len(selected_communications)} comms to ticket {ticket_name_str}", "Transfer Start")
			
			created_comm_names = []  # Track all created communication names
			
			for idx, comm in enumerate(selected_communications, 1):
				try:
					copied_comm_name = copy_communication(comm["name"], "HD Ticket", ticket_name_str)
					transferred_count += 1
					created_comm_names.append(copied_comm_name)
					
					# Commit after each communication to ensure it's saved
					frappe.db.commit()
					
					# Immediately verify it exists in database with correct reference
					# Use get_doc to reload and get actual saved values
					try:
						verify_comm_doc = frappe.get_doc("Communication", copied_comm_name)
						has_content = bool(verify_comm_doc.content or verify_comm_doc.text_content)
						ref_matches = (verify_comm_doc.reference_doctype == "HD Ticket" and 
									   str(verify_comm_doc.reference_name) == ticket_name_str)
						
						if ref_matches:
							frappe.log_error(
								f"Copied {idx}/{len(selected_communications)}: {copied_comm_name[:10]}... ref={verify_comm_doc.reference_name} (CORRECT), has_content={has_content}",
								"Communication Copy Success"
							)
						else:
							frappe.log_error(
								f"ERROR: {copied_comm_name[:10]}... has WRONG ref! Expected HD Ticket/{ticket_name_str}, got {verify_comm_doc.reference_doctype}/{verify_comm_doc.reference_name}",
								"Communication Reference Error"
							)
							# Try to fix it
							frappe.db.set_value(
								"Communication",
								copied_comm_name,
								{
									"reference_doctype": "HD Ticket",
									"reference_name": ticket_name_str,
									"status": "Linked"
								},
								update_modified=False
							)
							frappe.db.commit()
					except Exception as verify_error:
						frappe.log_error(
							f"ERROR verifying {copied_comm_name[:10]}...: {str(verify_error)}",
							"Communication Verification Error"
						)
				except Exception as e:
					error_details = f"Error copying communication {comm['name']} to HD Ticket {ticket.name}: {str(e)}\n{frappe.get_traceback()}"
					frappe.log_error(error_details, "Communication Copy Error")
					# Continue with other emails even if one fails
			
			# Log summary of all created communications
			frappe.log_error(
				f"Created {len(created_comm_names)} communications: {', '.join([c[:10] + '...' for c in created_comm_names[:5]])}{'...' if len(created_comm_names) > 5 else ''}",
				"Transfer Summary"
			)
		
		# Final commit to ensure everything is saved
		frappe.db.commit()
		
		# Reload ticket to ensure all data is fresh
		ticket.reload()
		
		# Verify communications were created by querying directly using QB (same as get_communications)
		QBCommunication = frappe.qb.DocType("Communication")
		ticket_name_str = str(ticket.name)
		created_comms_qb = (
			frappe.qb.from_(QBCommunication)
			.select(
				QBCommunication.name,
				QBCommunication.subject,
				QBCommunication.content,
				QBCommunication.text_content,
				QBCommunication.reference_name
			)
			.where(QBCommunication.reference_doctype == "HD Ticket")
			.where(QBCommunication.reference_name == ticket_name_str)
			.limit(20)
		).run(as_dict=True)
		
		# Also try with frappe.get_all for comparison
		created_comms_get_all = frappe.get_all(
			"Communication",
			filters={
				"reference_doctype": "HD Ticket",
				"reference_name": ticket_name_str
			},
			fields=["name", "subject", "content", "text_content", "reference_name"],
			limit=20
		)
		
		# Log details about each communication (shortened)
		comms_with_content_qb = sum(1 for c in created_comms_qb if (c.get("content") or c.get("text_content")))
		comms_with_content_get_all = sum(1 for c in created_comms_get_all if (c.get("content") or c.get("text_content")))
		
		frappe.log_error(
			f"After transfer: QB found {len(created_comms_qb)} comms ({comms_with_content_qb} with content), "
			f"get_all found {len(created_comms_get_all)} comms ({comms_with_content_get_all} with content) for ticket {ticket_name_str}",
			"Transfer Verification"
		)
		
		# Delete source Lead if requested
		if delete_source:
			try:
				frappe.delete_doc("CRM Lead", lead_name, ignore_permissions=True, force=True)
			except Exception as e:
				frappe.log_error(f"Error deleting source lead {lead_name}: {str(e)}")
		
		# Return success response
		ticket_url = get_url(f"/app/hd-ticket/{ticket.name}")
		
		return {
			"success": True,
			"ticket_name": ticket.name,
			"ticket_url": ticket_url,
			"transferred_count": transferred_count,
			"message": _("Successfully transferred {0} email(s) to HD Ticket {1}").format(
				transferred_count, ticket.name
			),
		}
		
	except Exception as e:
		frappe.log_error(f"Error in transfer_to_helpdesk: {str(e)}")
		frappe.throw(_("Error transferring to helpdesk: {0}").format(str(e)))

