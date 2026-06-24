import frappe


def execute(filters: dict | None = None):
    columns = [
        {"fieldname": "student", "label": "Student", "fieldtype": "Link", "options": "Student", "width": 150},
        {"fieldname": "student_name", "label": "Student Name", "fieldtype": "Data", "width": 180},
        {"fieldname": "group", "label": "Group", "fieldtype": "Data", "width": 120},
        {"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
        {"fieldname": "course", "label": "Course", "fieldtype": "Data", "width": 150},
    ]

    conditions = []
    values = {}

    if filters:
        if filters.get("student"):
            conditions.append("sa.student = %(student)s")
            values["student"] = filters["student"]
        if filters.get("group"):
            conditions.append("sa.group = %(group)s")
            values["group"] = filters["group"]
        if filters.get("from_date"):
            conditions.append("sa.date >= %(from_date)s")
            values["from_date"] = filters["from_date"]
        if filters.get("to_date"):
            conditions.append("sa.date <= %(to_date)s")
            values["to_date"] = filters["to_date"]
        if filters.get("status"):
            conditions.append("sa.status = %(status)s")
            values["status"] = filters["status"]

    where = " AND ".join(conditions) if conditions else "1=1"

    data = frappe.db.sql(
        """
        SELECT
            sa.student,
            s.student_name,
            sa.group,
            sa.date,
            sa.status,
            sa.course
        FROM `tabStudent Attendance` sa
        LEFT JOIN `tabStudent` s ON s.name = sa.student
        WHERE {where}
        ORDER BY sa.date DESC, sa.student ASC
        """.format(where=where),
        values,
        as_dict=1,
    )

    return columns, data
