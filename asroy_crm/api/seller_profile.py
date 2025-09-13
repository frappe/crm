import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def create_seller_profile(data):
    """
    Create a new Asroy Seller Profile KYC document from Google Form data.
    """
    try:
        # Parse the incoming JSON data
        data = frappe.parse_json(data)

        # Create a new document
        doc = frappe.get_doc({
            "doctype": "Asroy Seller Profile KYC",
            "salutation": data.get("salutation"),
            "name1": data.get("name1"),
            "mobile": data.get("mobile"),
            "mailing_address": data.get("mailing_address"),
            "permanent_address": data.get("permanent_address"),
            "email": data.get("email"),
            "date_of_birth": data.get("date_of_birth"),
            "marital_status": data.get("marital_status"),
            "nationality": data.get("nationality"),
            "nid_or_passport_number": data.get("nid_or_passport_number"),
            "no_of_household_family_members": data.get("no_of_household_family_members"),
            "number_of_adult_family_members": data.get("number_of_adult_family_members"),
            "number_of_children_family_members": data.get("number_of_children_family_members"),
            "residency_status": data.get("residency_status"),
            "secondary_contact_person_name": data.get("secondary_contact_person_name"),
            "secondary_contact_person_mobile": data.get("secondary_contact_person_mobile"),
            "secondary_contact_person_relationship": data.get("secondary_contact_person_relationship"),
            "type_of_profession": data.get("type_of_profession"),
            "name_of_organization": data.get("name_of_organization"),
            "designation": data.get("designation"),
            "addresses_of_organization": data.get("addresses_of_organization"),
            "project_name": data.get("project_name"),
            "project_address": data.get("project_address"),
            "project_type": data.get("project_type"),
            "location": data.get("location"),
            "total_floors": data.get("total_floors"),
            "total_units": data.get("total_units"),
            "land_size_katha": data.get("land_size_katha"),
            "road_size_feet": data.get("road_size_feet"),
            "developer_name": data.get("developer_name"),
            "handover_year": data.get("handover_year"),
            "building_type": data.get("building_type"),
            "holding_type": data.get("holding_type"),
            "total_parkings": data.get("total_parkings"),
            "finishing_status": data.get("finishing_status"),
            "building_facing": data.get("building_facing"),
            "fair_facing": data.get("fair_facing"),
            "gps_coordinate": data.get("gps_coordinate"),
            "cctv": data.get("cctv"),
            "security_guard": data.get("security_guard"),
            "fire_extinguisher": data.get("fire_extinguisher"),
            "fire_hydrant": data.get("fire_hydrant"),
            "water_sprinkler": data.get("water_sprinkler"),
            "reception_lobby": data.get("reception_lobby"),
            "electricity_backup": data.get("electricity_backup"),
            "cleaning_staff": data.get("cleaning_staff"),
            "garbage_disposal": data.get("garbage_disposal"),
            "prayer_room": data.get("prayer_room"),
            "green_zone": data.get("green_zone"),
            "jogging_area": data.get("jogging_area"),
            "gymnasium": data.get("gymnasium"),
            "wheelchair_access": data.get("wheelchair_access"),
            "game_or_sports_zone": data.get("game_or_sports_zone"),
            "community_space": data.get("community_space"),
            "floor_no": data.get("floor_no"),
            "unit_no": data.get("unit_no"),
            "occupancy_status": data.get("occupancy_status"),
            "gross_area_square_feet": data.get("gross_area_square_feet"),
            "gross_area_specific": data.get("gross_area_specific"),
            "no_of_parking": data.get("no_of_parking"),
            "net_area_square_feet": data.get("net_area_square_feet"),
            "property_facing": data.get("property_facing"),
            "no_of_beds": data.get("no_of_beds"),
            "no_of_baths": data.get("no_of_baths"),
            "no_of_livings": data.get("no_of_livings"),
            "no_of_balconies": data.get("no_of_balconies"),
            "maid_quarters": data.get("maid_quarters"),
            "store_room": data.get("store_room"),
            "flooring": data.get("flooring"),
            "floor_titles_size": data.get("floor_titles_size"),
            "fittings_brand": data.get("fittings_brand"),
            "asking_price_bdt": data.get("asking_price_bdt"),
            "bottom_price_bdt": data.get("bottom_price_bdt"),
            "pricing_specific": data.get("pricing_specific"),
            "bastuana_service_charge_bdt": data.get("bastuana_service_charge_bdt"),
            "bastuana_service_charge_specific": data.get("bastuana_service_charge_specific"),
            "property_monthly_rent_bdt": data.get("property_monthly_rent_bdt"),
            "property_monthly_service_charge_bdt": data.get("property_monthly_service_charge_bdt"),
            "viewing_contact_name": data.get("viewing_contact_name"),
            "viewing_contact_mobile": data.get("viewing_contact_mobile"),
            "viewing_access": data.get("viewing_access"),
            "no_of_owners_of_the_property": data.get("no_of_owners_of_the_property"),
            "registration_status": data.get("registration_status"),
            "mutation": data.get("mutation"),
            "holding_tax": data.get("holding_tax"),
            "mortgage_against_property": data.get("mortgage_against_property"),
            "mortgage_details": data.get("mortgage_details")
        })

        # Insert the document
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Seller Profile KYC created successfully!"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Google Form Submission Error")
        return {
            "status": "error",
            "message": str(e)
        }