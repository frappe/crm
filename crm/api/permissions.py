import frappe

# Role yang boleh melihat SEMUA transaksi (bypass filter assignment).
BYPASS_ROLES = {"System Manager", "Sales Manager"}


def _can_see_all(user):
    if user == "Administrator":
        return True
    return bool(BYPASS_ROLES & set(frappe.get_roles(user)))


def _assigned_or_owned(user, table):
    """SQL condition: user hanya lihat dokumen yang dia buat (owner) atau di-assign ke dia."""
    if _can_see_all(user):
        return ""
    esc_user = frappe.db.escape(user)
    like_user = frappe.db.escape("%" + user + "%")
    return f"(`{table}`.owner = {esc_user} OR `{table}`._assign LIKE {like_user})"


def _doc_has_permission(doc, user):
    if _can_see_all(user):
        return True
    if doc.get("owner") == user:
        return True
    assignees = frappe.parse_json(doc.get("_assign") or "[]") or []
    return user in assignees


# --- get_permission_query_conditions (filter LIST view) ---
def quotation_query_conditions(user=None):
    return _assigned_or_owned(user or frappe.session.user, "tabCRM Quotation")


def estimation_query_conditions(user=None):
    return _assigned_or_owned(user or frappe.session.user, "tabCRM Estimation")


# --- has_permission (akses buka 1 dokumen langsung) ---
def quotation_has_permission(doc, ptype=None, user=None, **kwargs):
    return _doc_has_permission(doc, user or frappe.session.user)


def estimation_has_permission(doc, ptype=None, user=None, **kwargs):
    return _doc_has_permission(doc, user or frappe.session.user)
