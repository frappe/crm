import frappe
import json
import requests
from datetime import datetime
from frappe import _
from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
from frappe.utils.password import get_decrypted_password


def validate(doc, method):
    if doc.type == "Incoming" and doc.get("from"):
        name, doctype = get_lead_or_deal_from_number(doc.get("from"))
        doc.reference_doctype = doctype
        doc.reference_name = name


def on_update(doc, method):
    frappe.publish_realtime(
        "avito_message",
        {
            "reference_doctype": doc.reference_doctype,
            "reference_name": doc.reference_name,
        },
    )

    notify_agent(doc)

def on_trash_lead(crm_lead, method):
    """ Delete cascade avito messages on lead delete """
    avito_mesage_docs = frappe.get_all('Avito Message', filters={'reference_name': crm_lead.name})
    
    for avito_mesage_doc in avito_mesage_docs:
        try:
            # Delete or cancel the linked document
            avito_mesage_doc_doc = frappe.get_doc('Avito Message', avito_mesage_doc.name)
            
            # Check if the document can be cancelled or deleted
            if avito_mesage_doc_doc.docstatus == 1:
                avito_mesage_doc_doc.cancel()
            else:
                avito_mesage_doc_doc.delete()
        except Exception as e:
            frappe.log_error(f"Failed to delete/cancel linked document {avito_mesage_doc.name} due to {str(e)}", "Linked Document Deletion Error")


def notify_agent(doc):
    if doc.type == "Incoming":
        doctype = doc.reference_doctype
        if doctype.startswith("CRM "):
            doctype = doctype[4:].lower()
        notification_text = f"""
            <div class="mb-2 leading-5 text-gray-600">
                <span class="font-medium text-gray-900">{ _('You') }</span>
                <span>{ _('received a avito message in {0}').format(doctype) }</span>
                <span class="font-medium text-gray-900">{ doc.reference_name }</span>
            </div>
        """
        assigned_users = get_assigned_users(doc.reference_doctype, doc.reference_name)
        for user in assigned_users:
            notify_user({
                "owner": doc.owner,
                "assigned_to": user,
                "notification_type": "Avito",
                "message": doc.message,
                "notification_text": notification_text,
                "reference_doctype": "Avito Message",
                "reference_docname": doc.name,
                "redirect_to_doctype": doc.reference_doctype,
                "redirect_to_docname": doc.reference_name,
            })


def get_lead_or_deal_from_number(number):
    """Get lead/deal from the given number."""

    def find_record(doctype, mobile_no, where=""):
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
        doc = find_record(doctype, number, "AND converted is not True")
        if not doc:
            doc = find_record(doctype, number)

    return doc, doctype


def parse_mobile_no(mobile_no: str):
    """Parse mobile number to remove spaces, brackets, etc.
    >>> parse_mobile_no('+91 (766) 667 6666')
    ... '+917666676666'
    """
    return "".join([c for c in mobile_no if c.isdigit() or c == "+"])


@frappe.whitelist()
def is_avito_enabled():
    if not frappe.db.exists("DocType", "Avito Settings"):
        return False
    return frappe.get_cached_value("Avito Settings", "Avito Settings", "enabled")

@frappe.whitelist()
def is_avito_installed():
    if not frappe.db.exists("DocType", "Avito Settings"):
        return False
    return True


@frappe.whitelist()
def get_avito_messages(reference_doctype, reference_name):
    if not frappe.db.exists("DocType", "Avito Message"):
        return []
    messages = []

    if reference_doctype == 'CRM Deal':
        lead = frappe.db.get_value(reference_doctype, reference_name, 'lead')
        if lead:
            messages = frappe.get_all(
                "Avito Message",
                filters={
                    "reference_doctype": "CRM Lead",
                    "reference_name": lead,
                },
                fields=[
                    "name",
                    "type",
                    "to",
                    "from",
                    "content_type",
                    "message_type",
                    "attach",
                    "template",
                    "use_template",
                    "message_id",
                    "is_reply",
                    "reply_to_message_id",
                    "creation",
                    "message",
                    "status",
                    "reference_doctype",
                    "reference_name",
                    "template_parameters",
                    "template_header_parameters",
                ],
            )

    messages += frappe.get_all(
        "Avito Message",
        filters={
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
        },
        fields=[
            "name",
            "type",
            "chat_id",
            "from",
            "content_type",
            "message_type",
            "attach",
            "template",
            "use_template",
            "message_id",
            "is_reply",
            "reply_to_message_id",
            "creation",
            "message",
            "status",
            "reference_doctype",
            "reference_name",
            "template_parameters",
            "template_header_parameters",
        ],
    )

    # Filter messages to get only Template messages
    template_messages = [
        message for message in messages if message["message_type"] == "Template"
    ]

    # Iterate through template messages
    for template_message in template_messages:
        # Find the template that this message is using
        template = frappe.get_doc("Avito Templates", template_message["template"])

        # If the template is found, add the template details to the template message
        if template:
            template_message["template_name"] = template.template_name
            if template_message["template_parameters"]:
                parameters = json.loads(template_message["template_parameters"])
                template.template = parse_template_parameters(
                    template.template, parameters
                )

            template_message["template"] = template.template
            if template_message["template_header_parameters"]:
                header_parameters = json.loads(
                    template_message["template_header_parameters"]
                )
                template.header = parse_template_parameters(
                    template.header, header_parameters
                )
            template_message["header"] = template.header
            template_message["footer"] = template.footer

    # Filter messages to get only reaction messages
    reaction_messages = [
        message for message in messages if message["content_type"] == "reaction"
    ]

    # Iterate through reaction messages
    for reaction_message in reaction_messages:
        # Find the message that this reaction is reacting to
        reacted_message = next(
            (
                m
                for m in messages
                if m["message_id"] == reaction_message["reply_to_message_id"]
            ),
            None,
        )

        # If the reacted message is found, add the reaction to it
        if reacted_message:
            reacted_message["reaction"] = reaction_message["message"]

    for message in messages:
        from_name = get_from_name(message) if message["from"] else _("You")
        message["from_name"] = from_name
    # Filter messages to get only replies
    reply_messages = [message for message in messages if message["is_reply"]]

    # Iterate through reply messages
    for reply_message in reply_messages:
        # Find the message that this message is replying to
        replied_message = next(
            (
                m
                for m in messages
                if m["message_id"] == reply_message["reply_to_message_id"]
            ),
            None,
        )

        # If the replied message is found, add the reply details to the reply message
        from_name = (
            get_from_name(reply_message) if replied_message["from"] else _("You")
        )
        if replied_message:
            message = replied_message["message"]
            if replied_message["message_type"] == "Template":
                message = replied_message["template"]
            reply_message["reply_message"] = message
            reply_message["header"] = replied_message.get("header") or ""
            reply_message["footer"] = replied_message.get("footer") or ""
            reply_message["reply_to"] = replied_message["name"]
            reply_message["reply_to_type"] = replied_message["type"]
            reply_message["reply_to_from"] = from_name

    return [message for message in messages if message["content_type"] != "reaction"]


@frappe.whitelist(allow_guest=True)
def get_message_from_avito(
    *args, **kwargs
):
    frappe.enqueue(process_avito_message, queue='short', timeout=5, *args, **kwargs)
    # process_avito_message(*args, **kwargs)

def process_avito_message(
    *args, **kwargs
):
    author_id = kwargs['payload']['value']['author_id']
    user_id = kwargs['payload']['value']['user_id']
    if author_id == user_id: return

    message = kwargs['payload']['value']['content']['text']
    chat_id = kwargs['payload']['value']['chat_id']
    attach = ''

    settings = frappe.get_doc("Avito Settings")
    if settings.token_expires_in == None or \
       settings.token == None or \
       datetime.strptime(settings.token_expires_in, '%Y-%m-%d %H:%M:%S.%f') < datetime.now():
        settings.update_auth_token()
    
    try:
        avito_lead = frappe.get_last_doc(doctype="Avito Lead", filters={"avito_chat_id": chat_id})
    except frappe.DoesNotExistError:
        token = get_decrypted_password('Avito Settings', 'Avito Settings', 'token')
        crm_lead = frappe.new_doc("CRM Lead")
        res = requests.get(
            f"https://api.avito.ru/messenger/v2/accounts/{user_id}/chats/{chat_id}", 
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            })
        content = json.loads(res.text)
        user = content['users'][0]
        if user['id'] == user_id: user = content['users'][1]
        crm_lead.first_name = user['name']
        crm_lead.insert(ignore_permissions=True)
        # avito lead - subDocType
        avito_lead = frappe.new_doc("Avito Lead")
        avito_lead.avito_chat_id = chat_id
        avito_lead.fcrm_lead = crm_lead
        avito_lead.insert(ignore_permissions=True)

    create_avito_message("CRM Lead", avito_lead.fcrm_lead, message, '', None, chat_id=chat_id, _type="Incoming")


@frappe.whitelist()
def create_avito_message(
    reference_doctype,
    reference_name,
    message,
    attach,
    reply_to,
    chat_id=None,
    content_type="text",
    _type="Outgoing",
):
    doc = frappe.new_doc("Avito Message")

    token = get_decrypted_password('Avito Settings', 'Avito Settings', 'token')

    if reply_to:
        reply_doc = frappe.get_doc("Avito Message", reply_to)
        doc.update(
            {
                "is_reply": True,
                "reply_to_message_id": reply_doc.message_id,
            }
        )
    
    if chat_id is None:
        avito_lead = frappe.get_last_doc("Avito Lead", filters={"fcrm_lead": reference_name})
        chat_id = avito_lead.avito_chat_id

    doc.update(
        {
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "message": message or attach,
            "chat_id": chat_id, # chat_id to,
            "attach": attach,
            "content_type": content_type,
            "type": _type,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def send_avito_template(reference_doctype, reference_name, template, to):
    doc = frappe.new_doc("Avito Message")
    doc.update(
        {
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "message_type": "Template",
            "message": "Template message",
            "content_type": "text",
            "use_template": True,
            "template": template,
            "to": to,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def react_on_avito_message(emoji, reply_to_name):
    reply_to_doc = frappe.get_doc("Avito Message", reply_to_name)
    to = reply_to_doc.type == "Incoming" and reply_to_doc.get("from") or reply_to_doc.to
    doc = frappe.new_doc("Avito Message")
    doc.update(
        {
            "reference_doctype": reply_to_doc.reference_doctype,
            "reference_name": reply_to_doc.reference_name,
            "message": emoji,
            "to": to,
            "reply_to_message_id": reply_to_doc.message_id,
            "content_type": "reaction",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def parse_template_parameters(string, parameters):
    for i, parameter in enumerate(parameters, start=1):
        placeholder = "{{" + str(i) + "}}"
        string = string.replace(placeholder, parameter)

    return string


def get_from_name(message):
    doc = frappe.get_doc(message["reference_doctype"], message["reference_name"])
    from_name = ""
    if message["reference_doctype"] == "CRM Deal":
        if doc.get("contacts"):
            for c in doc.get("contacts"):
                if c.is_primary:
                    from_name = c.full_name or c.mobile_no
                    break
        else:
            from_name = doc.get("lead_name")
    else:
        from_name = doc.get("first_name") + " " + doc.get("last_name")
    return from_name
