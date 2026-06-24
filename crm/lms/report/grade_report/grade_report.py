import frappe


def execute(filters: dict | None = None):
    columns = [
        {"fieldname": "student", "label": "Student", "fieldtype": "Link", "options": "Student", "width": 150},
        {"fieldname": "student_name", "label": "Student Name", "fieldtype": "Data", "width": 180},
        {"fieldname": "lecture", "label": "Lecture", "fieldtype": "Link", "options": "Course Lecture", "width": 200},
        {"fieldname": "lecture_title", "label": "Lecture Title", "fieldtype": "Data", "width": 200},
        {"fieldname": "course", "label": "Course", "fieldtype": "Data", "width": 150},
        {"fieldname": "score", "label": "Score (0-100)", "fieldtype": "Int", "width": 100},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
        {"fieldname": "instructor", "label": "Instructor", "fieldtype": "Link", "options": "User", "width": 120},
        {"fieldname": "submitted_at", "label": "Submitted At", "fieldtype": "Datetime", "width": 160},
    ]

    conditions = []
    values = {}

    if filters:
        if filters.get("student"):
            conditions.append("sa.student = %(student)s")
            values["student"] = filters["student"]
        if filters.get("course"):
            conditions.append("sa.course = %(course)s")
            values["course"] = filters["course"]
        if filters.get("status"):
            conditions.append("sa.status = %(status)s")
            values["status"] = filters["status"]
        if filters.get("min_score"):
            conditions.append("sa.score >= %(min_score)s")
            values["min_score"] = int(filters["min_score"])
        if filters.get("max_score"):
            conditions.append("sa.score <= %(max_score)s")
            values["max_score"] = int(filters["max_score"])
        if filters.get("from_date"):
            conditions.append("sa.submitted_at >= %(from_date)s")
            values["from_date"] = filters["from_date"]
        if filters.get("to_date"):
            conditions.append("sa.submitted_at <= %(to_date)s")
            values["to_date"] = filters["to_date"]

    where = " AND ".join(conditions) if conditions else "1=1"

    data = frappe.db.sql(
        f"""
        SELECT
            sa.student,
            s.student_name,
            sa.lecture,
            cl.title AS lecture_title,
            sa.course,
            sa.score,
            sa.status,
            sa.instructor,
            sa.submitted_at
        FROM `tabStudent Assignment` sa
        LEFT JOIN `tabStudent` s ON s.name = sa.student
        LEFT JOIN `tabCourse Lecture` cl ON cl.name = sa.lecture
        WHERE {where}
        ORDER BY sa.modified DESC
        """,
        values,
        as_dict=1,
    )

    return columns, data
