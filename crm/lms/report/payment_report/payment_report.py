import frappe


def execute(filters: dict | None = None):
    columns = [
        {"fieldname": "student", "label": "Student", "fieldtype": "Link", "options": "Student", "width": 150},
        {"fieldname": "student_name", "label": "Student Name", "fieldtype": "Data", "width": 180},
        {"fieldname": "amount", "label": "Amount", "fieldtype": "Currency", "width": 100},
        {"fieldname": "payment_method", "label": "Method", "fieldtype": "Data", "width": 100},
        {"fieldname": "payment_date", "label": "Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "student_abonement", "label": "Abonement", "fieldtype": "Link", "options": "Student Abonement", "width": 120},
        {"fieldname": "abonement_type", "label": "Abonement Type", "fieldtype": "Data", "width": 120},
    ]

    conditions = []
    values = {}

    if filters:
        if filters.get("student"):
            conditions.append("p.student = %(student)s")
            values["student"] = filters["student"]
        if filters.get("payment_method"):
            conditions.append("p.payment_method = %(payment_method)s")
            values["payment_method"] = filters["payment_method"]
        if filters.get("from_date"):
            conditions.append("p.payment_date >= %(from_date)s")
            values["from_date"] = filters["from_date"]
        if filters.get("to_date"):
            conditions.append("p.payment_date <= %(to_date)s")
            values["to_date"] = filters["to_date"]

    where = " AND ".join(conditions) if conditions else "1=1"

    data = frappe.db.sql(
        f"""
        SELECT
            p.student,
            s.student_name,
            p.amount,
            p.payment_method,
            p.payment_date,
            p.student_abonement,
            sat.abonement_name AS abonement_type
        FROM `tabPayment` p
        LEFT JOIN `tabStudent` s ON s.name = p.student
        LEFT JOIN `tabStudent Abonement` sa ON sa.name = p.student_abonement
        LEFT JOIN `tabAbonement Type` sat ON sat.name = sa.abonement_type
        WHERE {where}
        ORDER BY p.payment_date DESC
        """,
        values,
        as_dict=1,
    )

    return columns, data
