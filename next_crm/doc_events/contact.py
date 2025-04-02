from next_crm.api.contact import set_primary_email, set_primary_mobile_no


def validate(doc, method=None):
    set_primary_email(doc)
    set_primary_mobile_no(doc)
    doc.set_primary_email()
    doc.set_primary("mobile_no")
