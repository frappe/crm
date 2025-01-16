# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMCampaign(Document):
    def validate(self):
        for i in self.campaign_participants:
            if i.participant_source == "Contact":
                if  frappe.db.exists("Contact", i.reference_docname):
                    i.full_name = frappe.db.get_value("Contact", i.reference_docname,'first_name')
                    i.email = frappe.db.get_value("Contact", i.reference_docname, 'email_id')
            elif i.participant_source == "CRM Lead":
                if frappe.db.exists("CRM Lead", i.reference_docname):
                    i.full_name = frappe.db.get_value("CRM Lead", i.reference_docname,'first_name')
                    i.organization = frappe.db.get_value("CRM Lead", i.reference_docname,'organization')
                    i.email = frappe.db.get_value("CRM Lead", i.reference_docname,'email')

    
    @staticmethod
    def default_list_data():
        columns = [
            {
                'label': 'Campaign Name',
                'type': 'Data',
                'key': 'campaign_name',
                'width': '12rem',
            },
            {
                'label': 'Campaign Type',
                'type': 'Link',
                'key': 'campaign_type',
                'options':'CRM Campaign Type',
                'width': '12rem',
            },
            {
                'label': 'Status',
                'type': 'Select',
                'key': 'status',
                'width': '10rem',
            },
            {
                'label': 'Scheduled Send Time',
                'type': 'Datetime',
                'key': 'scheduled_send_time',
                'width': '11rem',
            }
        ]
        rows = [
            "name",
            "campaign_name",
            "campaign_type",
            "status",
            "scheduled_send_time"
        ]
        return {'columns': columns, 'rows': rows}




@frappe.whitelist()
def update_campaign_participants():
    campaign_name = frappe.form_dict.get("campaign_name")
    doctype = frappe.form_dict.get("doctype")
    campaign_participants = frappe.form_dict.get("campaign_participants")

    if not frappe.db.exists("CRM Campaign",  {"campaign_name": campaign_name}):
        campaign = frappe.new_doc("CRM Campaign")
        campaign.campaign_name = campaign_name
        campaign.insert(ignore_permissions=True)
        frappe.db.commit()
        
    campaign = frappe.get_doc("CRM Campaign", {"campaign_name": campaign_name})

    for participant in campaign_participants:
        reference_docname = participant.get("reference_docname")
        if not frappe.db.exists("CRM Campaign Participants", {"parent": campaign.name, "participant_source": doctype, "reference_docname": reference_docname}):
            campaign.append("campaign_participants", {
                "participant_source": doctype,
                "reference_docname": reference_docname,
            })

    # Save the campaign to apply changes
    campaign.save(ignore_permissions=True)
    frappe.db.commit()

    return {"campaign_name": campaign.name}

        

@frappe.whitelist()
def create_or_update_campaign(args):
    existing_campaign = frappe.db.exists("CRM Campaign", {"campaign_name": args.get('campaign_name')})
    if existing_campaign:
        #update campaign if any changes on existing record
        campaign = frappe.get_doc("CRM Campaign", args.get('campaign_name'))
        if args.get('campaign_type') != campaign.get('campaign_type'):
            campaign.update({"campaign_type": args.get('campaign_type')})
        if args.get('status') != campaign.get('status'):
            campaign.update({"status": args.get('status')})
        if args.get('scheduled_send_time') != campaign.get('scheduled_send_time'):
            campaign.update({"scheduled_send_time": args.get('scheduled_send_time')})
        if args.get('email_template') != campaign.get('email_template'):
            campaign.update({"email_template": args.get('email_template')})
        campaign.save(ignore_permissions=True)
        frappe.db.commit()
        return campaign.name
    else:
        #create a new campaign if not exist
        campaign = frappe.new_doc("CRM Campaign")
        campaign.update({
            "campaign_name": args.get('campaign_name'),
            "campaign_type": args.get('campaign_type'),
            "status": args.get('status'),
            "scheduled_send_time": args.get('scheduled_send_time'),
            "email_template": args.get('email_template')
        })
        campaign.insert(ignore_permissions=True)
        frappe.db.commit()
        return campaign.name

@frappe.whitelist()
def get_campaign():
    campaigns = frappe.db.sql(f"""SELECT cc.name
                                FROM `tabCRM Campaign` cc""", as_dict=True)
    result = [{"label": c['name'], "type": "Data", "value" : c['name']} for c in campaigns]
    return result
    
def send_email_for_campaign():
    crm_campaigns = frappe.get_all(
        "CRM Campaign", filters={"status": ("not in", ["On Hold", "Closed"])}
    )
    for camp in crm_campaigns:
        campaign = frappe.get_doc("CRM Campaign", camp.name)
        if getdate(campaign.scheduled_send_time) == getdate(today()) and (campaign.scheduled_send_time).hour == (today()).hour:
            for entry in campaign.get("campaign_participants"):
                campaign.status= "In Progress"
                comm = send_mail(campaign, entry)
                campaign.status= "Closed"
                campaign.save(ignore_permissions=True)



def send_mail(campaign, entry):
    if campaign.get("email_template"):
        email_template = frappe.get_doc("Email Template", campaign.get("email_template"))
        context = {"doc": frappe.get_doc(entry.get('participant_source'), entry.get('reference_docname'))}
        # send mail and link communication to document
        comm = make(
            doctype="CRM Campaign",
            name= campaign.name,
            subject=frappe.render_template(email_template.get("subject"), context),
            content=frappe.render_template(email_template.response_, context),
            recipients=entry.get('email'),
            communication_medium="Email",
            sent_or_received="Sent",
            send_email=True,
            email_template=email_template.name,
        )
        return comm
    else:
        return f"Please set Email template for {campaign.name}"

@frappe.whitelist()
def get_doc_view_campaign_data(campaign_name):
    doc = frappe.get_doc("CRM Campaign", campaign_name)
    converted_data = {
            "campaign_name": doc.get('campaign_name'),
            "campaign_type": doc.get('campaign_type'),
            "status": doc.get('status'),
            "scheduled_send_time": doc.get('scheduled_send_time'),
            "email_template": doc.get('email_template')
        }
    campaign_participants = []
    campaign_participants.append({"CRM Lead":get_campaign_participants("CRM Lead", campaign_name)})
    campaign_participants.append({'Contact':get_campaign_participants("Contact", campaign_name)})
    converted_data.update({"campaign_participants":campaign_participants})
    return converted_data
   
def get_campaign_participants(ref_doctype, campaign_name):
    fields=('name','organization', 'email', 'participant_source', 'reference_docname', 'full_name')
    filters={'parent':campaign_name , 'participant_source':ref_doctype}
    data = frappe.db.get_all("CRM Campaign Participants",filters=filters ,fields=fields)
    for row in data:
        row['name'] = frappe.db.get_value(row.participant_source, {'name':row.reference_docname}, 'name')
    return data if len(data)>0 else []

