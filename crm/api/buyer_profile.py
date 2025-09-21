import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def create_buyer_profile(data):
    """
    Create a new Asroy Buyer Profile KYC document from Google Form data.
    """
    try:
        # Parse the incoming JSON data
        data = frappe.parse_json(data)

        # Create a new document
        doc = frappe.get_doc({
            "doctype": "Asroy Buyer Profile KYC",
            "salutation": data.get("salutation"),
            "name1": data.get("name1"),
            "email": data.get("email"),
            "mobile": data.get("mobile"),
            "date_of_birth": data.get("date_of_birth"),
            "designation": data.get("designation"),
            "nationality": data.get("nationality"),
            "nid_no": data.get("nid_no"),
            "mailing_address": data.get("mailing_address"),
            "permanent_address": data.get("permanent_address"),
            "type_of_profession": data.get("type_of_profession"),
            "marital_status": data.get("marital_status"),
            "relation_with_secondary_contact_person": data.get("relation_with_secondary_contact_person"),
            "secondary_contact_person_mobile": data.get("secondary_contact_person_mobile"),
            "secondary_contact_person_name": data.get("secondary_contact_person_name"),
            "residency_status": data.get("residency_status"),
            "no_of_children_family_members": data.get("no_of_children_family_members"),
            "no_of_adult_family_members": data.get("no_of_adult_family_members"),
            "no_of_household_family_members": data.get("no_of_household_family_members"),
            "name_of_organization": data.get("name_of_organization"),
            "address_of_organization": data.get("address_of_organization"),
            "location": data.get("location"),
            "location_comments": data.get("location_comments"),
            "property_type": data.get("property_type"),
            "property_size_squar_feet": data.get("property_size_squar_feet"),
            "property_condition": data.get("property_condition"),
            "property_size_katha": data.get("property_size_katha"),
            "no_of_beds": data.get("no_of_beds"),
            "no_of_baths": data.get("no_of_baths"),
            "no_of_balconies": data.get("no_of_balconies"),
            "no_of_car_parking": data.get("no_of_car_parking"),
            "budget_bdt": data.get("budget_bdt"),
            "financial_mode": data.get("financial_mode")
        })

        # Insert the document
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Buyer Profile KYC created successfully!"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Google Form Submission Error")
        return {
            "status": "error",
            "message": str(e)
        }