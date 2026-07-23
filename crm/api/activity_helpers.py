import frappe
from bs4 import BeautifulSoup
from frappe.translate import get_translated_doctypes


def get_communication_directions(communications: list) -> dict:
	names = [communication.name for communication in communications]
	if not names:
		return {}

	return {
		communication.name: communication.sent_or_received
		for communication in frappe.get_all(
			"Communication",
			filters={"name": ("in", names)},
			fields=["name", "sent_or_received"],
		)
	}


def parse_attachment_log(html: str, type: str):
	soup = BeautifulSoup(html, "html.parser")
	a_tag = soup.find("a")
	type = "added" if type == "Attachment" else "removed"
	if not a_tag:
		return {
			"type": type,
			"file_name": html.replace("Removed ", ""),
			"file_url": "",
			"is_private": False,
		}

	is_private = False
	if "private/files" in a_tag["href"]:
		is_private = True

	return {
		"type": type,
		"file_name": a_tag.text,
		"file_url": a_tag["href"],
		"is_private": is_private,
	}


def is_translatable(doctype: str) -> bool:
	return doctype in get_translated_doctypes()
