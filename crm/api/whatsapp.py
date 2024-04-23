import frappe

def validate(doc, method):
	if doc.type == "Incoming" and doc.get("from"):
		name, doctype = get_lead_or_deal_from_number(doc.get("from"))
		doc.reference_doctype = doctype
		doc.reference_name = name

def get_lead_or_deal_from_number(number):
	"""Get lead/deal from the given number.
	"""

	def find_record(doctype, mobile_no, where=''):
		mobile_no = parse_mobile_no(mobile_no)
		
		query = f"""
			SELECT name, mobile_no
			FROM `tab{doctype}`
			WHERE CONCAT('+', REGEXP_REPLACE(mobile_no, '[^0-9]', '')) = {mobile_no}
		"""

		data = frappe.db.sql(query + where, as_dict=True)
		return data[0].name if data else None

	doctype = "CRM Deal"

	doc = find_record(doctype, number) or None
	if not doc:
		doctype = "CRM Lead"
		doc = find_record(doctype, number, 'AND converted is not True')
		if not doc:
			doc = find_record(doctype, number)

	return doc, doctype

def parse_mobile_no(mobile_no: str):
	"""Parse mobile number to remove spaces, brackets, etc.
	>>> parse_mobile_no('+91 (766) 667 6666')
	... '+917666676666'
	"""
	return ''.join([c for c in mobile_no if c.isdigit() or c == '+'])

@frappe.whitelist()
def get_whatsapp_messages(reference_doctype, reference_name):
	messages = frappe.get_all(
		"WhatsApp Message",
		filters={
			"reference_doctype": reference_doctype,
			"reference_name": reference_name
		},
		fields=[
			'name',
			'type',
			'to',
			'from',
			'content_type',
			'message_type',
			'attach',
			'template',
			'use_template',
			'message_id',
			'is_reply',
			'reply_to_message_id',
			'creation',
			'message',
			'status',
			'reference_doctype',
			'reference_name',
		],
	)

	# Filter messages to get only Template messages
	template_messages = [message for message in messages if message['message_type'] == 'Template']

	# Iterate through template messages
	for template_message in template_messages:
		# Find the template that this message is using
		template = frappe.get_doc("WhatsApp Templates", template_message['template'])
		
		# If the template is found, add the template details to the template message
		if template:
			template_message['template_name'] = template.template_name
			template_message['template'] = template.template
			template_message['header'] = template.header
			template_message['footer'] = template.footer

	# Filter messages to get only reaction messages
	reaction_messages = [message for message in messages if message['content_type'] == 'reaction']

	# Iterate through reaction messages
	for reaction_message in reaction_messages:
		# Find the message that this reaction is reacting to
		reacted_message = next((m for m in messages if m['message_id'] == reaction_message['reply_to_message_id']), None)
		
		# If the reacted message is found, add the reaction to it
		if reacted_message:
			reacted_message['reaction'] = reaction_message['message']

	# Filter messages to get only replies
	reply_messages = [message for message in messages if message['is_reply']]

	# Iterate through reply messages
	for reply_message in reply_messages:
		# Find the message that this message is replying to
		replied_message = next((m for m in messages if m['message_id'] == reply_message['reply_to_message_id']), None)
		
		# If the replied message is found, add the reply details to the reply message
		doc = frappe.get_doc(reply_message['reference_doctype'], reply_message['reference_name'])
		from_name = replied_message['from']
		for c in doc.contacts:
			if c.is_primary:
				from_name = c.full_name or c.mobile_no
		if replied_message:
			reply_message['reply_message'] = replied_message['template'] if replied_message['message_type'] == 'Template' else replied_message['message']
			reply_message['header'] = replied_message.get('header') or ''
			reply_message['footer'] = replied_message.get('footer') or ''
			reply_message['reply_to'] = replied_message['name']
			reply_message['reply_to_type'] = replied_message['type']
			reply_message['reply_to_from'] = from_name

	return [message for message in messages if message['content_type'] != 'reaction']

@frappe.whitelist()
def create_whatsapp_message(reference_doctype, reference_name, message, to, attach, reply_to, content_type="text"):
	doc = frappe.new_doc("WhatsApp Message")

	if reply_to:
		reply_doc = frappe.get_doc("WhatsApp Message", reply_to)
		doc.update({
			"is_reply": True,
			"reply_to_message_id": reply_doc.message_id,
		})

	doc.update({
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"message": message or attach,
		"to": to,
		"attach": attach,
		"content_type": content_type,
	})
	doc.insert(ignore_permissions=True)
	return doc.name

@frappe.whitelist()
def send_whatsapp_template(reference_doctype, reference_name, template, to):
	doc = frappe.new_doc("WhatsApp Message")
	doc.update({
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"message_type": "Template",
		"message": "Template message",
		"content_type": "text",
		"use_template": True,
		"template": template,
		"to": to,
	})
	doc.insert(ignore_permissions=True)
	return doc.name

@frappe.whitelist()
def react_on_whatsapp_message(emoji, reply_to_name):
	reply_to_doc = frappe.get_doc("WhatsApp Message", reply_to_name)
	to = reply_to_doc.type == "Incoming" and reply_to_doc.get("from") or reply_to_doc.to
	doc = frappe.new_doc("WhatsApp Message")
	doc.update({
		"reference_doctype": reply_to_doc.reference_doctype,
		"reference_name": reply_to_doc.reference_name,
		"message": emoji,
		"to": to,
		"reply_to_message_id": reply_to_doc.message_id,
		"content_type": "reaction",
	})
	doc.insert(ignore_permissions=True)
	return doc.name