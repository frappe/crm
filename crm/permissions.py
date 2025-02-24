import frappe

def get_permission_query_conditions_for_assignable_doc(doctype, user=None, owner_field="owner"):
    """Universal permission query conditions for assignable documents"""
    if not user:
        user = frappe.session.user
        
    if "System Manager" in frappe.get_roles(user) or any(role in frappe.get_roles(user) for role in ["Sales Manager", "Support Manager"]):
        return ""

    # User can see documents they own
    conditions = [f"`tab{doctype}`.{owner_field} = '{user}'"]
    
    # User can see documents shared with them (via DocShare from ToDo assignments)
    shared_docs = frappe.db.sql("""
        SELECT share_name
        FROM `tabDocShare`
        WHERE
            share_doctype=%s
            AND user=%s
            AND `read`=1
    """, (doctype, user), as_dict=1)
    
    if shared_docs:
        doc_names = ["'" + d.share_name + "'" for d in shared_docs]
        conditions.append(f"`tab{doctype}`.name in ({','.join(doc_names)})")
    
    return "(" + " OR ".join(conditions) + ")"

def get_permission_query_conditions_for_crm_deal(user=None):
    """Permission query conditions for CRM Deal"""
    return get_permission_query_conditions_for_assignable_doc("CRM Deal", user, owner_field="deal_owner")

def get_permission_query_conditions_for_crm_lead(user=None):
    """Permission query conditions for CRM Lead"""
    return get_permission_query_conditions_for_assignable_doc("CRM Lead", user, owner_field="lead_owner")

def get_permission_query_conditions_for_crm_task(user=None):
    """Permission query conditions for CRM Task"""
    return get_permission_query_conditions_for_assignable_doc("CRM Task", user) 