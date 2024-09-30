from collections.abc import Iterable

import frappe
from frappe import _
from bs4 import BeautifulSoup
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user

def on_update(self, method):
    notify_mentions(self)


def notify_mentions(doc):
    """
    Extract mentions from `content`, and notify.
    `content` must have `HTML` content.
    """
    content = getattr(doc, "content", None)
    if not content:
        return
    mentions = extract_mentions(content)
    reference_doc = frappe.get_doc(doc.reference_doctype, doc.reference_name)
    for mention in mentions:
        owner = frappe.get_cached_value("User", doc.owner, "full_name")
        doctype = doc.reference_doctype
        if doctype.startswith("CRM "):
            doctype = doctype[4:].lower()
        name = reference_doc.lead_name or name if doctype == "lead" else reference_doc.organization or reference_doc.lead_name or name
        notification_text = f"""
            <div class="mb-2 leading-5 text-gray-600">
                <span class="font-medium text-gray-900">{ owner }</span>
                <span>{ _('mentioned you in {0}').format(doctype) }</span>
                <span class="font-medium text-gray-900">{ name }</span>
            </div>
        """
        notify_user({
            "owner": doc.owner,
            "assigned_to": mention.email,
            "notification_type": "Mention",
            "message": doc.content,
            "notification_text": notification_text,
            "reference_doctype": "Comment",
            "reference_docname": doc.name,
            "redirect_to_doctype": doc.reference_doctype,
            "redirect_to_docname": doc.reference_name,
        })


def extract_mentions(html):
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    mentions = []
    for d in soup.find_all("span", attrs={"data-type": "mention"}):
        mentions.append(
            frappe._dict(full_name=d.get("data-label"), email=d.get("data-id"))
        )
    return mentions

@frappe.whitelist()
def add_attachments(name: str, attachments: Iterable[str | dict]) -> None:
	"""Add attachments to the given Comment

	:param name: Comment name
	:param attachments: File names or dicts with keys "fname" and "fcontent"
	"""
	# loop through attachments
	for a in attachments:
		if isinstance(a, str):
			attach = frappe.db.get_value("File", {"name": a}, ["file_url", "is_private"], as_dict=1)
			file_args = {
				"file_url": attach.file_url,
				"is_private": attach.is_private,
			}
		elif isinstance(a, dict) and "fcontent" in a and "fname" in a:
			# dict returned by frappe.attach_print()
			file_args = {
				"file_name": a["fname"],
				"content": a["fcontent"],
				"is_private": 1,
			}
		else:
			continue

		file_args.update(
			{
				"attached_to_doctype": "Comment",
				"attached_to_name": name,
				"folder": "Home/Attachments",
			}
		)

		_file = frappe.new_doc("File")
		_file.update(file_args)
		_file.save(ignore_permissions=True)