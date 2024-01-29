import frappe
from bs4 import BeautifulSoup

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
    for mention in mentions:
        values = frappe._dict(
            doctype="CRM Notification",
            from_user=doc.owner,
            to_user=mention.email,
            type="Mention",
            message=doc.content,
            comment=doc.name,
            reference_doctype=doc.reference_doctype,
            reference_name=doc.reference_name,
        )

        if frappe.db.exists("CRM Notification", values):
            return
        frappe.get_doc(values).insert()


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